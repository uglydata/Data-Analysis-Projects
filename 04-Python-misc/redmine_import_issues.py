"""
Redmine Issue Importer from LUIS Core CSV

Description:
------------
This script imports or updates issues in Redmine using data from a CSV export from LUIS Core.
It matches issues using the unique 'Xid' field and ensures proper field, status, and assignee mapping.

Algorithm:
----------
1. Initialize logging and load API/config settings.
2. Load CSV file from Downloads directory.
3. Fetch metadata from Redmine:
   - Issue statuses and their Redmine IDs.
4. For each row in the CSV:
   - Skip if Xid starts with 'R' (issue originates in Redmine).
   - Map the CSV status to a Redmine status.
     - Skip if Redmine status not found.
   - Map the assignee code to Redmine user ID.
     - Use default user if unknown or empty.
   - Determine if the issue already exists in Redmine by checking for Xid in the description.
   - Build the issue payload with subject, status, assignee, and other fields.
   - If the issue exists:
     - Update it via Redmine API.
     - Add a private comment noting the update.
   - If it does not exist:
     - Create it as a new issue in the Redmine project.
5. Log each step and outcome (created, updated, skipped, failed).
6. Output final summary:
   - Total rows processed
   - Created/updated issues
   - Skipped rows (invalid status, Redmine-originated)
   - Recognized assignees
   - Errors

Field Mapping:
--------------
| CSV Column      | Redmine Field         |
|-----------------|------------------------|
| Xid             | Description (embedded) |
| Txt             | Subject                |
| Izveidots       | Start date             |
| K.Termiņš       | Due date               |
| nov(h)          | Estimated hours        |
| Tips Statuss    | Mapped to status_id    |
| Izpilda         | Assigned to (user_id)  |

Status Mapping:
---------------
| CSV Status           | Redmine Status             |
|----------------------|----------------------------|
| Pabeigts             | Izpilde: Izpildīts         |
| Slēgts               | Slēgts                     |
| RindaUzIzpildi       | Atlikts                    |
| Izskatīšana          | Reģistrēts                 |
| Atlikts              | Atlikts                    |
| Noraidīts            | Slēgts                     |
| Testēšana            | Izpilde: Testēšanā         |
| Izpilde              | Izpilde: Izpildē           |
| Piešķirts            | Piešķirts                  |
| Pieteikts            | Reģistrēts                 |
| Pazudis              | Reģistrēts                 |
| Daļējs risinājums    | Precizēšana                |

Other Notes:
------------
- Skips updates if no data has changed.
- Skips Issues which Xid starts with R - Redmine issues, no need to import
- Logs all activities to `redmine_import.log`.
- Adds a private Redmine comment on every update to track import actions.
- Default tracker: Pieteikums (ID 1)
- Default priority: Normāla (ID 2)
- Default assignee: 7037 (Janis Zvirgzds)
    - assignee is recognized from dictionary, if not found- assign default
"""

import configparser
import logging
import sys
from pathlib import Path
import requests
import pandas as pd
from datetime import datetime

# Initialize counters
success_count = 0
recognized_user_count = 0
error_count = 0
skipped_count = 0

script_dir = Path(__file__).resolve().parent
log_file = script_dir / "redmine_import.log"

logging.basicConfig(
    filename=log_file,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def log_and_print(msg):
    print(msg)
    logging.info(msg)

log_and_print("===== Redmine Issue Import Started =====")

# Load config
config_file = script_dir / "redmine_import_config.ini"

if not config_file.exists():
    log_and_print(f"Config file '{config_file}' not found.")
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file)

try:
    redmine_config = config["redmine"]
    api_key = redmine_config["api_key"]
    base_url = redmine_config["base_url"]
    project_identifier = "luis-importetie"
except KeyError as e:
    log_and_print(f"Missing config key: {e}")
    sys.exit(1)

headers = {"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
max_rows = int(redmine_config.get("max_rows", 0))

# Status mapping
status_mapping = {
    "Pabeigts": "Izpilde: Izpildīts",
    "Slēgts": "Slēgts",
    "RindaUzIzpildi": "Atlikts",
    "Izskatīšana": "Reģistrēts",
    "Atlikts": "Atlikts",
    "Noraidīts": "Slēgts",
    "Testēšana": "Izpilde: Testēšanā",
    "Izpilde": "Izpilde: Izpildē",
    "Piešķirts": "Piešķirts",
    "Pieteikts": "Reģistrēts",
    "Pazudis": "Reģistrēts",
    "Daļējs risinājums": "Precizēšana"
}

# Assignee mapping
assignee_mapping = {
    "IBRIM": 24,   # Ivars Brikmanis
    "EPOCS": 312   # Edgars Počs
}
default_assignee = 7037  # Janis Zvirgzds

csv_path = Path.home() / "Downloads" / "uzdevumi.csv"
if not csv_path.exists():
    log_and_print(f"CSV file not found: {csv_path}")
    sys.exit(1)

df = pd.read_csv(csv_path, sep=";", encoding="windows-1257")

# Rename columns if needed
column_fixes = {
    "K.Termiņš": ["K.Termiņš", "K.Termiņð", "K.Termiòð", "K.Termins"],
    "Plānotā izpilde": ["Plānotā izpilde", "Plânotâ izpilde"],
    "Aprēķinātā izpilde": ["Aprēķinātā izpilde", "Aprçíinâtâ izpilde"]
}
for correct, variants in column_fixes.items():
    for col in df.columns:
        if col in variants and col != correct:
            df.rename(columns={col: correct}, inplace=True)
            log_and_print(f"Renamed column '{col}' → '{correct}'")

def fetch_status_name_id_map():
    resp = requests.get(f"{base_url}/issue_statuses.json", headers=headers)
    return {s["name"]: s["id"] for s in resp.json().get("issue_statuses", [])} if resp.ok else {}

status_name_to_id = fetch_status_name_id_map()

missing_statuses = set(status_mapping.values()) - set(status_name_to_id.keys())
if missing_statuses:
    log_and_print(f"Warning: The following mapped statuses are not found in Redmine: {missing_statuses}")

def find_issue_by_xid(xid):
    url = f"{base_url}/issues.json?project_id={project_identifier}&status_id=*&limit=100"
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        return None
    for issue in resp.json().get("issues", []):
        if xid in issue.get("description", ""):
            return issue
    return None

def add_internal_comment(issue_id, comment):
    url = f"{base_url}/issues/{issue_id}.json"
    data = {"issue": {"notes": comment, "private_notes": True}}
    return requests.put(url, headers=headers, json=data).ok

def create_or_update_issue(row):
    global success_count, recognized_user_count, error_count, skipped_count
    xid = str(row["Xid"]).strip()

    if xid.upper().startswith("R"):
        log_and_print(f"Xid {xid}: Skipped because it originates from Redmine.")
        skipped_count += 1
        return

    existing = find_issue_by_xid(xid)

    original_status = row["Tips Statuss"]
    mapped_status = status_mapping.get(original_status, "Reģistrēts")
    status_id = status_name_to_id.get(mapped_status)

    if not status_id:
        log_and_print(f"Xid {xid}: Skipped - Redmine status not found for '{original_status}' → '{mapped_status}'")
        skipped_count += 1
        return

    assignee_code_raw = row.get("Izpilda", "")
    assignee_code = str(assignee_code_raw).strip().upper()

    if not assignee_code or assignee_code == "NAN":
        assignee_id = default_assignee
        log_and_print(f"Xid {xid}: No assignee provided. Defaulting to API user ID {default_assignee}")
    else:
        assignee_id = assignee_mapping.get(assignee_code, default_assignee)
        if assignee_id == default_assignee:
            log_and_print(f"Xid {xid}: Unrecognized assignee code '{assignee_code}', using default user ID {default_assignee}")
        else:
            log_and_print(f"Xid {xid}: Assigned to Redmine user ID {assignee_id} for code '{assignee_code}'")
            recognized_user_count += 1

    issue_data = {
        "project_id": project_identifier,
        "subject": str(row["Txt"]),
        "description": f"Xid: {xid}\nLUIS: https://luis.lu.lv/pls/lu/uzdrab.uzdevums?uzid1={xid[1:]}",
        "tracker_id": 1,
        "priority_id": 2,
        "status_id": status_id
    }

    if assignee_code in assignee_mapping:
        issue_data["assigned_to_id"] = assignee_id

    # Start date
    if pd.notna(row["Izveidots"]):
        try:
            issue_data["start_date"] = datetime.strptime(str(row["Izveidots"]), "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            log_and_print(f"Xid {xid}: Invalid start date format: {row['Izveidots']}")
    # Due date
    if pd.notna(row.get("K.Termiņš", "")):
        try:
            issue_data["due_date"] = datetime.strptime(str(row["K.Termiņš"]), "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            log_and_print(f"Xid {xid}: Invalid due date format: {row['K.Termiņš']}")
    # Estimation
    if pd.notna(row.get("nov(h)", "")):
        issue_data["estimated_hours"] = float(row["nov(h)"])

    try:
        if existing:
            issue_id = existing["id"]
            url = f"{base_url}/issues/{issue_id}.json"
            resp = requests.put(url, headers=headers, json={"issue": issue_data})
            if resp.status_code == 200:
                log_and_print(f"Issue {xid} updated (ID: {issue_id})")
                add_internal_comment(issue_id, f"Issue updated via import process for Xid {xid}")
                success_count += 1
            elif resp.status_code == 204:
                log_and_print(f"Issue {xid} update skipped (ID: {issue_id}) - no changes")
            else:
                log_and_print(f"Failed to update issue {xid}: {resp.status_code}")
                error_count += 1
        else:
            resp = requests.post(f"{base_url}/issues.json", headers=headers, json={"issue": issue_data})
            if resp.status_code == 201:
                log_and_print(f"Issue {xid} created.")
                success_count += 1
            else:
                log_and_print(f"Failed to create issue {xid}: {resp.status_code} - {resp.text}")
                error_count += 1
    except Exception as e:
        log_and_print(f"Error for Xid {xid}: {e}")
        error_count += 1

# Run import
rows_to_process = df.head(max_rows) if max_rows > 0 else df
for _, row in rows_to_process.iterrows():
    create_or_update_issue(row)

# Log summary
log_and_print(f"Total rows processed: {len(rows_to_process)}")
log_and_print(f"Successfully created or updated: {success_count}")
log_and_print(f"Recognized assignee users: {recognized_user_count}")
log_and_print(f"Skipped rows: {skipped_count}")
log_and_print(f"Errors: {error_count}")
log_and_print("===== Redmine Issue Import Finished =====")
