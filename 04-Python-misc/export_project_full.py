"""
Redmine Full Project Export (issues + journals + attachments)

Answers a different question than the daily history export: not "how
long does work take across the whole tracker", but "what actually
happened on this one project, and who did it" - useful for a project
retrospective, an audit of who implemented a given feature, or as
structured input for an LLM to draft a project summary from raw
issue-tracker data instead of a person reconstructing it by hand.

Exports every issue in a project with its full journal history,
relations, children, and attachments (downloaded locally) into a
single JSON file per project.

Edit PROJECTS below to point at your own project identifier(s).
Config: redmine_export_config.ini (api_key, base_url)
"""

import configparser
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import pytz
import requests

# ===== PARAMETERS - edit these =====
PROJECTS = [
    "example-project",
]
ISSUE_LIMIT = None  # max issues per project, None = all

# ===== Setup =====
script_dir = Path(__file__).resolve().parent
log_file = script_dir / "export_full_issues.log"
logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} - {msg}")
    logging.info(msg)


def format_dt(value):
    """Convert a Redmine UTC datetime string to a local-timezone string."""
    try:
        if value.endswith("Z"):
            dt_utc = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
        else:
            dt_utc = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
        dt_local = dt_utc.astimezone(pytz.timezone("UTC"))
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return value


def convert_datetimes_to_local(obj):
    if isinstance(obj, dict):
        return {
            k: convert_datetimes_to_local(format_dt(v) if k.endswith("_on") and isinstance(v, str) else v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_datetimes_to_local(i) for i in obj]
    return obj


def load_config():
    config_file = script_dir / "redmine_export_config.ini"
    if not config_file.exists():
        log(f"Config file '{config_file}' not found.")
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        return config["redmine"]["api_key"], config["redmine"]["base_url"]
    except KeyError as e:
        log(f"Missing config key: {e}")
        sys.exit(1)


def fetch_issue_ids(base_url, headers, project, limit):
    """Fetch all issue IDs for a project, sorted by ID ascending."""
    issue_ids = []
    offset = 0
    while True:
        url = (
            f"{base_url}/issues.json?project_id={project}&status_id=*"
            f"&sort=id:asc&limit=100&offset={offset}"
        )
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            log(f"Error fetching issue list (offset={offset}): HTTP {resp.status_code}")
            break

        data = resp.json()
        issues = data.get("issues", [])
        if not issues:
            break
        issue_ids.extend(i["id"] for i in issues)

        if limit and len(issue_ids) >= limit:
            return issue_ids[:limit]

        total = data.get("total_count", 0)
        offset += 100
        if offset >= total:
            break
        time.sleep(0.2)

    return issue_ids


def fetch_issue_detail(base_url, headers, issue_id):
    """Fetch one issue with journals, attachments, custom fields, relations, children, watchers."""
    url = f"{base_url}/issues/{issue_id}.json?include=journals,attachments,custom_fields,relations,children,watchers"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    return resp.json().get("issue"), None


def download_attachment(url, save_path, headers):
    resp = requests.get(url, headers=headers, stream=True)
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True, None


def export_project(project, limit, base_url, headers):
    log(f"===== Exporting project: {project}, limit={limit} =====")

    output_dir = script_dir / "output" / project
    attachments_dir = output_dir / "attachments"
    output_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(parents=True, exist_ok=True)

    issue_ids = fetch_issue_ids(base_url, headers, project, limit)
    total = len(issue_ids)
    log(f"Found {total} issues to export")
    if total == 0:
        log("No issues found. Check the project identifier.")
        return

    all_issues = []
    attachments_ok, attachments_fail = 0, 0
    failed_attachments = []

    for idx, issue_id in enumerate(issue_ids, 1):
        issue, err = fetch_issue_detail(base_url, headers, issue_id)
        if issue is None:
            log(f"[{idx}/{total}] FAILED to fetch issue #{issue_id}: {err}")
            continue

        att_count = len(issue.get("attachments", []))
        log(f"[{idx}/{total}] Exporting issue #{issue_id}: {issue.get('subject', '')[:60]} ({att_count} attachments)")

        for att in issue.get("attachments", []):
            filename = att.get("filename", "unknown")
            local_name = f"{issue_id}_{filename}"
            save_path = attachments_dir / local_name

            if save_path.exists():
                att["local_file"] = local_name
                attachments_ok += 1
                continue

            content_url = att.get("content_url")
            if not content_url:
                attachments_fail += 1
                failed_attachments.append({"issue_id": issue_id, "filename": filename, "error": "no content_url"})
                continue

            ok, dl_err = download_attachment(content_url, save_path, headers)
            if ok:
                att["local_file"] = local_name
                attachments_ok += 1
            else:
                log(f"  FAILED to download {filename}: {dl_err}")
                attachments_fail += 1
                failed_attachments.append({"issue_id": issue_id, "filename": filename, "error": dl_err})
            time.sleep(0.1)

        all_issues.append(issue)
        time.sleep(0.2)

    log("Converting datetimes...")
    all_issues = convert_datetimes_to_local(all_issues)

    export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    issues_file = output_dir / "issues.json"
    with open(issues_file, "w", encoding="utf-8") as f:
        json.dump({"project": project, "export_date": export_date, "total_issues": len(all_issues), "issues": all_issues}, f, ensure_ascii=False, indent=2)
    log(f"Wrote {issues_file}")

    summary_file = output_dir / "export_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "project": project,
            "export_date": export_date,
            "total_issues": len(all_issues),
            "total_attachments_downloaded": attachments_ok,
            "total_attachments_failed": attachments_fail,
            "failed_attachments": failed_attachments,
        }, f, ensure_ascii=False, indent=2)
    log(f"Wrote {summary_file}")

    log(f"  Issues: {len(all_issues)}")
    log(f"  Attachments downloaded: {attachments_ok}, failed: {attachments_fail}")
    log(f"  Output: {output_dir}")


def main():
    api_key, base_url = load_config()
    headers = {"X-Redmine-API-Key": api_key}

    log("===== Redmine Full Project Export Started =====")
    log(f"Projects: {PROJECTS}")
    for project in PROJECTS:
        export_project(project, ISSUE_LIMIT, base_url, headers)
    log("===== All exports complete =====")


if __name__ == "__main__":
    main()
