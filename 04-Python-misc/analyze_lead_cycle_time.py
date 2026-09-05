"""
Lead time / cycle time / time-in-status analysis from exported issue history.

Reads the JSON files produced by export_issue_history_json.py and
reconstructs, per issue, the full sequence of status changes with
timestamps - something a flat CSV snapshot can't provide, since it
only ever shows the current status.

From that timeline it computes:
  - Lead time: issue creation to closed (or "still open" if not closed)
  - Time spent in each status along the way
  - An aggregate: average time spent per status across all issues,
    which is usually the more actionable number - "where is work
    actually getting stuck?"

Usage:
    python analyze_lead_cycle_time.py [path/to/output/folder]
    (defaults to ./output, where export_issue_history_json.py writes its files)

Outputs two CSVs in the same folder:
  - lead_time_per_issue.csv
  - time_in_status.csv (long format: one row per issue per status segment)
"""

import csv
import glob
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return None


def load_issues(output_folder):
    """Load every issue_history_*.json file, keeping the latest copy of each issue."""
    issues_by_id = {}
    files = sorted(glob.glob(str(Path(output_folder) / "issue_history_*.json")))
    if not files:
        sys.exit(f"No issue_history_*.json files found in {output_folder}")

    for path in files:
        with open(path, encoding="utf-8") as f:
            for issue in json.load(f):
                issues_by_id[issue["id"]] = issue  # later files overwrite with more complete history

    return list(issues_by_id.values())


def status_timeline(issue):
    """Reconstruct the (status, entered_at, exited_at) timeline for one issue."""
    created_at = parse_dt(issue.get("created_on"))
    closed_at = parse_dt(issue.get("closed_on"))
    current_status = issue.get("status", {}).get("name", "Unknown")

    status_changes = []  # (timestamp, old_status, new_status)
    for journal in issue.get("journals", []):
        ts = parse_dt(journal.get("created_on"))
        for detail in journal.get("details", []):
            if detail.get("property") == "attr" and detail.get("name") == "status_id" and ts:
                status_changes.append((ts, detail.get("old_value"), detail.get("new_value")))
    status_changes.sort(key=lambda x: x[0])

    if not created_at:
        return []

    # Status before the first recorded change is whatever the first change's "old_value" was;
    # if there were no changes at all, the issue has been in its current status the whole time.
    initial_status = status_changes[0][1] if status_changes else current_status

    timeline = []
    segment_start = created_at
    segment_status = initial_status
    for ts, _old, new in status_changes:
        timeline.append((segment_status, segment_start, ts))
        segment_start = ts
        segment_status = new

    end_of_last_segment = closed_at if closed_at else datetime.now()
    timeline.append((segment_status, segment_start, end_of_last_segment))
    return timeline


def main():
    output_folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "output"
    issues = load_issues(output_folder)
    print(f"Loaded {len(issues)} unique issue(s) from {output_folder}")

    lead_time_rows = []
    time_in_status_rows = []
    status_duration_totals = defaultdict(lambda: [0.0, 0])  # status -> [total_days, count]

    for issue in issues:
        created_at = parse_dt(issue.get("created_on"))
        closed_at = parse_dt(issue.get("closed_on"))
        if not created_at:
            continue

        is_open = closed_at is None
        lead_time_days = ((closed_at or datetime.now()) - created_at).total_seconds() / 86400

        lead_time_rows.append({
            "issue_id": issue["id"],
            "subject": issue.get("subject", ""),
            "created_on": issue.get("created_on"),
            "closed_on": issue.get("closed_on") or "",
            "is_open": is_open,
            "lead_time_days": round(lead_time_days, 2),
        })

        for status, entered_at, exited_at in status_timeline(issue):
            duration_days = (exited_at - entered_at).total_seconds() / 86400
            time_in_status_rows.append({
                "issue_id": issue["id"],
                "status": status,
                "entered_at": entered_at.strftime(DATETIME_FORMAT),
                "exited_at": exited_at.strftime(DATETIME_FORMAT),
                "duration_days": round(duration_days, 2),
            })
            status_duration_totals[status][0] += duration_days
            status_duration_totals[status][1] += 1

    lead_time_file = output_folder / "lead_time_per_issue.csv"
    with open(lead_time_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["issue_id", "subject", "created_on", "closed_on", "is_open", "lead_time_days"])
        writer.writeheader()
        writer.writerows(lead_time_rows)
    print(f"Wrote {lead_time_file} ({len(lead_time_rows)} issues)")

    time_in_status_file = output_folder / "time_in_status.csv"
    with open(time_in_status_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["issue_id", "status", "entered_at", "exited_at", "duration_days"])
        writer.writeheader()
        writer.writerows(time_in_status_rows)
    print(f"Wrote {time_in_status_file} ({len(time_in_status_rows)} status segments)")

    print("\nAverage time spent per status (across all issues, all visits):")
    for status, (total_days, count) in sorted(status_duration_totals.items(), key=lambda x: -x[1][0]):
        print(f"  {status:30s} avg {total_days / count:6.2f} days  (n={count})")


if __name__ == "__main__":
    main()
