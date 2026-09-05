"""
Redmine Issue History Export (JSON)

The other scripts in this folder export a flat CSV snapshot of
issues - current status, current assignee, current everything. That's
enough for a status report, but it can't answer "how long did this
sit in review?" or "what's our average lead time this quarter?",
because a snapshot has no history. Answering those needs every status
transition, with a timestamp, which only Redmine's journal/history
data provides.

This script exports full issue + journal history to daily JSON files,
suitable for downstream analysis of lead time, cycle time, and time
spent in each status. It's designed to run daily/incrementally
(skips days that are already fully exported) rather than re-pulling
the whole tracker's history every time.

Config: redmine_export_config.ini (api_key, base_url, date range,
root_projects)
"""

import requests
import configparser
import logging
import json
from datetime import datetime, timedelta, date
import sys
from pathlib import Path
import pytz

# ====== setup ======
script_dir = Path(__file__).resolve().parent
log_file = script_dir / "redmine_export.log"
logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def log_and_print(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} - {msg}")
    logging.info(msg)


def format_dt(value: str):
    """Convert a Redmine UTC datetime string to a local-timezone string."""
    try:
        if value.endswith("Z"):
            dt_utc = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
        else:
            dt_utc = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
        dt_local = dt_utc.astimezone(pytz.timezone(LOCAL_TIMEZONE))
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return value


def convert_datetimes_to_local(obj):
    """Walk a nested dict/list; convert any '*_on' string field to local time."""
    if isinstance(obj, dict):
        return {
            k: convert_datetimes_to_local(
                format_dt(v) if k.endswith("_on") and isinstance(v, str) else v
            )
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_datetimes_to_local(i) for i in obj]
    return obj


log_and_print("===== Redmine Issue History Export Started =====")

# ====== config ======
config_file = script_dir / "redmine_export_config.ini"
if not config_file.exists():
    log_and_print(f"Config file '{config_file}' not found.")
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file)

try:
    api_key = config["redmine"]["api_key"]
    base_url = config["redmine"]["base_url"]
    max_records = int(config["redmine"]["max_records"])
    created_on = config["redmine"]["created_on"]  # "YYYY-MM-DD,YYYY-MM-DD"
    root_project_identifiers = set(x.strip() for x in config["redmine"].get("root_projects", "").split(",") if x.strip())
    LOCAL_TIMEZONE = config["redmine"].get("local_timezone", "UTC")
except KeyError as e:
    log_and_print(f"Missing config key: {e}")
    sys.exit(1)

headers = {"X-Redmine-API-Key": api_key}
output_folder = Path(config["redmine"].get("output_folder", script_dir / "output"))
output_folder.mkdir(parents=True, exist_ok=True)


# ====== helpers ======
def get_user_mapping():
    """GET /users.json -> {'123': 'Some Name'} for readable journal authors."""
    user_map = {}
    offset = 0
    while True:
        url = f"{base_url}/users.json?limit=100&offset={offset}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            log_and_print(f"Failed to fetch users: {resp.status_code}")
            break
        users = resp.json().get("users", [])
        for u in users:
            user_map[str(u["id"])] = u.get("name", f"User {u['id']}")
        if len(users) < 100:
            break
        offset += 100
    return user_map


def get_status_mapping():
    """GET /issue_statuses.json -> {'1': 'New', '2': 'In Progress', ...}

    Fetched live rather than hardcoded, so this script works against
    any Redmine instance's actual workflow without editing the code.
    """
    status_map = {}
    resp = requests.get(f"{base_url}/issue_statuses.json", headers=headers)
    if resp.status_code == 200:
        for s in resp.json().get("issue_statuses", []):
            status_map[str(s["id"])] = s.get("name", f"Status {s['id']}")
    else:
        log_and_print(f"Failed to fetch issue statuses: {resp.status_code}")
    return status_map


def get_target_project_ids():
    """Resolve configured root project identifiers to project IDs, including subprojects."""
    all_projects = []
    offset = 0
    while True:
        url = f"{base_url}/projects.json?limit=100&offset={offset}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            log_and_print("Failed to fetch project list.")
            break
        projects = resp.json().get("projects", [])
        all_projects.extend(projects)
        if len(projects) < 100:
            break
        offset += 100
    root_ids = {p["id"] for p in all_projects if p["identifier"] in root_project_identifiers}
    child_ids = {p["id"] for p in all_projects if p.get("parent", {}).get("id") in root_ids}
    return list(root_ids | child_ids)


def enrich_issue_journals(issue, user_map, status_map):
    """Attach readable author names and status labels to each journal entry."""
    for journal in issue.get("journals", []):
        j_user = journal.get("user")
        if isinstance(j_user, dict):
            j_id = j_user.get("id")
            if j_id is not None and str(j_id) in user_map:
                journal["user"]["name"] = user_map[str(j_id)]

        for detail in journal.get("details", []):
            if detail.get("property") == "attr" and detail.get("name") == "status_id":
                for key in ("old_value", "new_value"):
                    v = detail.get(key)
                    if v is not None:
                        detail[key] = status_map.get(str(v), v)
    return issue


# ====== export ======
user_mapping = get_user_mapping()
status_mapping = get_status_mapping()
project_ids = get_target_project_ids()
log_and_print(f"Selected project IDs: {project_ids}")

start_date, end_date = [datetime.strptime(d.strip(), "%Y-%m-%d") for d in created_on.split(",")]
current_date = start_date
counter = 1

while current_date <= min(end_date, datetime.today()):
    date_str = current_date.strftime("%Y-%m-%d")
    history_file = output_folder / f"issue_history_{date_str}.json"

    # Re-export only the last few days; older completed days don't change.
    if history_file.exists() and current_date.date() < (date.today() - timedelta(days=4)):
        log_and_print(f"Skipping {date_str}, already exported.")
        current_date += timedelta(days=1)
        continue

    issues_with_history = []
    seen_ids = set()

    for project_id in project_ids:
        for date_field in ["created_on", "updated_on"]:
            offset = 0
            while offset < max_records:
                url = (
                    f"{base_url}/issues.json?limit=100&offset={offset}"
                    f"&status_id=*&project_id={project_id}"
                    f"&{date_field}=><{date_str}|{date_str}"
                )
                resp = requests.get(url, headers=headers)
                if resp.status_code != 200:
                    break
                batch = resp.json().get("issues", [])
                if not batch:
                    break
                for issue_summary in batch:
                    issue_id = issue_summary["id"]
                    if issue_id in seen_ids:
                        continue
                    seen_ids.add(issue_id)

                    detail_url = f"{base_url}/issues/{issue_id}.json?include=custom_fields,journals"
                    detail_resp = requests.get(detail_url, headers=headers)
                    if detail_resp.status_code != 200:
                        continue
                    issue = detail_resp.json().get("issue")
                    issue = enrich_issue_journals(issue, user_mapping, status_mapping)
                    issues_with_history.append(issue)
                offset += 100

    issues_with_history = convert_datetimes_to_local(issues_with_history)

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(issues_with_history, f, ensure_ascii=False, indent=2)

    log_and_print(f"{counter}. Exported {len(issues_with_history)} issue(s) with history for {date_str}")
    counter += 1
    current_date += timedelta(days=1)

log_and_print("===== Redmine Issue History Export Completed =====")
