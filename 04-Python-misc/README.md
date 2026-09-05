# Redmine Import/Export Scripts

Automation scripts for working with a Redmine issue tracker via its REST API: importing issues from another system, and exporting them in three different shapes depending on what question you're trying to answer.

## 1. redmine_import_issues.py

Imports or updates issues in Redmine based on a CSV export from another system.

### Features:
- Detects existing issues via unique `Xid` embedded in Redmine descriptions
- Maps status and assignee fields from the source system to Redmine
- Skips issues already created in Redmine
- Logs all activity to `redmine_import.log`
- Adds a private Redmine comment on updates
- Customizable via `redmine_import_config.ini`

## 2. export_redmine_issues.py

Exports issues to CSV - a current-state snapshot: one row per issue, its current status, assignee, custom fields, etc. Good for "what does the backlog look like right now." Also has a `journal` mode that exports status-change history to CSV, but flattened into rows - workable for a spreadsheet, but not a great shape for time-series analysis (see script 3 below for that).

### Modes:
- `full`: issue data + custom fields + last journal note
- `journal`: status-change history (old/new value per status transition)

## 3. export_issue_history_json.py

**Problem this solves:** a CSV snapshot only shows the *current* status - it can't answer "how long did this sit in review?" or "what's our average lead time this quarter?", because a snapshot has no history. Answering those needs every status transition with a timestamp, which only Redmine's journal data provides, and JSON is a far better fit for that nested, variable-length data than a flat CSV row.

Exports full issue + journal history to daily JSON files. Designed to run incrementally (skips days that are already fully exported) rather than re-pulling the whole tracker's history on every run. Status labels are fetched live from `/issue_statuses.json` rather than hardcoded, so it works against any Redmine instance's actual workflow without editing the code.

## 4. export_project_full.py

**Problem this solves:** reconstructing what actually happened on a specific project - who implemented a given feature, and when - normally means someone manually digging through a project's issue history. This exports every issue in one project with its full journal history, relations, and attachments (downloaded locally) into a single JSON file, structured well enough to be handed to an LLM to draft a project retrospective/summary directly from the raw tracker data, instead of doing that reconstruction by hand.

Edit the `PROJECTS` list at the top of the script to point at your own project identifier(s).

## 5. analyze_lead_cycle_time.py

Reads the JSON files produced by `export_issue_history_json.py` and demonstrates the actual payoff of exporting history instead of a snapshot: it reconstructs each issue's status timeline and computes lead time (creation to close) plus time spent in each status along the way. Outputs `lead_time_per_issue.csv`, `time_in_status.csv`, and prints an aggregate - average time spent per status across all issues, which is usually the more actionable number, since it points at where work is actually getting stuck.

```bash
python analyze_lead_cycle_time.py [path/to/output/folder]
```

## Setup

1. Create config files:
   - `redmine_import_config.ini`
   - `redmine_export_config.ini` (used by all three export scripts; `export_issue_history_json.py` additionally reads `created_on`, `root_projects`, `output_folder`, and `local_timezone` from the same file)

2. Install requirements:
   ```bash
   pip install -r ../requirements.txt
   ```
