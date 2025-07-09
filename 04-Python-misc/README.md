# Redmine Import/Export Scripts

This repository contains two Python scripts to automate Redmine issue import and export using the Redmine REST API and CSV files.

## 1. redmine_import.py

Imports or updates issues in Redmine based on a CSV export from another system.

### Features:
- Detects existing issues via unique `Xid` embedded in Redmine descriptions
- Maps status and assignee fields from Core system to Redmine
- Skips issues already created in Redmine
- Logs all activity to `redmine_import.log`
- Adds a private Redmine comment on updates
- Customizable via `redmine_import_config.ini`

## 2. redmine_export.py

Exports issues (with optional journal history) to CSV from one or more Redmine projects.

### Modes:
- `limited`: basic issue data
- `full`: includes custom fields + last journal note
- `journal`: exports all journal entries for each issue

### Features:
- Recursively fetches subprojects
- Deduplicates issues by ID
- Outputs `redmine_issues_export.csv` or `redmine_issues_history_export.csv`
- Logs to `redmine_export_full.log` or `redmine_export_journal.log`

## Setup

1. Create config files:
   - `redmine_import_config.ini`
   - `redmine_export_config.ini`

2. Install requirements:
   ```bash
   pip install requests pandas
