'''
Modes
    limited: basic issue data (default)
    full: issue data + custom fields + last journal note
    journal: full issue data + all journal entries (for history/cycle time tracking)

Algorithm Summary
Setup
    Load config, logging, and API key
    Determine created_on filter and mode
Project Discovery
    Load all subprojects under "Project-Beast" and "Project-Alfa"
Issue Fetching
    For each project, fetch issues with pagination and filters
    Use include=custom_fields,journals for full and journal modes

Deduplication
    Deduplicate issues by ID

Export Logic
    If export_mode == journal:
        Write each journal entry to redmine_issues_history_export.csv
    Else:
        Write per-issue data to redmine_issues_export.csv   
        For full mode: include custom fields and last journal note

Logging
    Output progress and errors to a log file based on mode

''' 

import requests
import csv
import configparser
import logging
from datetime import datetime
import sys
from pathlib import Path

# Format Redmine datetime to match UI
def format_dt(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y %H:%M")
    except:
        return ''

def get_custom_field_enum_mapping():
    url = f"{base_url}/custom_fields.json"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        log_and_print("Failed to fetch custom fields.")
        return {}

    fields = resp.json().get('custom_fields', [])
    mapping = {}
    for field in fields:
        if field.get('name') == 'Pieteikuma tips' and 'possible_values' in field:
            mapping = {val['value']: val['label'] for val in field['possible_values']}
            break
    return mapping

# Setup
script_dir = Path(__file__).resolve().parent
log_file = script_dir / "redmine_export.log"
logging.basicConfig(filename=log_file, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def log_and_print(msg):
    print(msg)
    logging.info(msg)

log_and_print("===== Redmine Issue Export Started =====")

config_file = script_dir / 'redmine_export_config.ini'
if not config_file.exists():
    log_and_print(f"Config file '{config_file}' not found.")
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file)

try:
    api_key = config['redmine']['api_key']
    base_url = config['redmine']['base_url']
    max_records = int(config['redmine']['max_records'])
    export_modes = ['full', 'journal']
except KeyError as e:
    log_and_print(f"Missing config key: {e}")
    sys.exit(1)

created_on = config['redmine'].get('created_on', '')
headers = {'X-Redmine-API-Key': api_key}
pieteikuma_tips_mapping = get_custom_field_enum_mapping()

status_mapping = {
    '1': 'Reģistrēts',
    '19': 'Piešķirts',
    '37': 'Saskaņošanā',
    '35': 'Saskaņots',
    '32': 'Saskaņots finansējums',
    '36': 'Izskatīšanā',
    '34': 'Saskaņots struktūrvienībā',
    '33': 'Saskaņots ITS',
    '20': 'Precizēšana',
    '21': 'Izpilde: Izpildē',
    '27': 'Izpilde: Testēšanā',
    '28': 'Izpilde: Izpildīts',
    '5': 'Slēgts'
}

def get_target_project_ids():
    root_identifiers = {"pieteikumu-registrs", "isian-projekti"}
    all_projects = []
    offset = 0
    while True:
        url = f"{base_url}/projects.json?limit=100&offset={offset}&include=trackers"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            log_and_print("Failed to fetch project list.")
            break
        data = resp.json()
        projects = data.get("projects", [])
        all_projects.extend(projects)
        if len(projects) < 100:
            break
        offset += 100

    root_ids = {p["id"] for p in all_projects if p["identifier"] in root_identifiers}
    child_ids = {p["id"] for p in all_projects if p.get("parent", {}).get("id") in root_ids}
    return list(root_ids | child_ids)

project_ids = get_target_project_ids()
log_and_print(f"Selected project IDs: {project_ids}")

for export_mode in export_modes:
    limit = 100
    all_issues = []
    custom_field_names = set()

    log_and_print(f"Starting issue export for mode: {export_mode}")
    for project_id in project_ids:
        offset = 0
        while offset < max_records:
            params = f"limit={limit}&offset={offset}&status_id=*"
            params += f"&project_id={project_id}"
            if created_on:
                created_on_range = created_on.replace(',', '|')
                params += f"&created_on=><{created_on_range}"
            url = f"{base_url}/issues.json?{params}"
            log_and_print(f"Fetching project {project_id} offset {offset}")
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                log_and_print(f"Failed to fetch data: {resp.status_code}")
                break
            data = resp.json()
            issues = data.get('issues', [])
            if not issues:
                break
            for issue_summary in issues:
                issue_id = issue_summary['id']
                issue_url = f"{base_url}/issues/{issue_id}.json?include=custom_fields,journals"
                detail_resp = requests.get(issue_url, headers=headers)
                if detail_resp.status_code != 200:
                    continue
                full_issue = detail_resp.json().get('issue')
                if export_mode == "full":
                    for cf in full_issue.get('custom_fields', []):
                        custom_field_names.add(cf['name'])
                all_issues.append(full_issue)
                if len(all_issues) >= max_records:
                    break
            if len(all_issues) >= max_records:
                break
            offset += limit

    unique_issues = {issue['id']: issue for issue in all_issues}
    all_issues = list(unique_issues.values())
    log_and_print(f"Total unique issues: {len(all_issues)}")
    if all_issues:
        log_and_print(f"First issue payload: {all_issues[0]}")
    else:
        log_and_print("No issues found for the given filters.")

    if export_mode == "journal":
        csv_file = Path.home() / "Downloads" / "redmine_issues_history_export.csv"
        log_file = script_dir / "redmine_export_journal.log"
    else:
        csv_file = Path.home() / "Downloads" / "redmine_issues_export.csv"
        log_file = script_dir / "redmine_export_full.log"

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if export_mode == "journal":
            headers = ['Issue ID', 'Journal ID', 'Project', 'Subject', 'Author', 'Created On', 'Notes', 'Changed Field', 'Old Value', 'New Value']
            writer.writerow(headers)
            for issue in all_issues:
                issue_id = issue['id']
                project = issue.get('project', {}).get('name', '')
                subject = issue.get('subject', '')
                journals = issue.get('journals', [])
                for journal in journals:
                    journal_id = journal.get('id', '')
                    author = journal.get('user', {}).get('name', '')
                    created_on = format_dt(journal.get('created_on', ''))

                    notes = journal.get('notes') or ''
                    notes = notes.replace('\n', ' ').replace('\r', ' ')[:500]

                    details = journal.get('details', [])
                    if not details:
                        writer.writerow([issue_id, journal_id, project, subject, author, created_on, notes, '', '', ''])
                    else:
                        for detail in details:
                            if detail.get('property') == 'attr' and detail.get('name') == 'status_id':
                                field = "attr:status_id"
                                old = status_mapping.get(str(detail.get('old_value', '')), detail.get('old_value', ''))
                                new = status_mapping.get(str(detail.get('new_value', '')), detail.get('new_value', ''))
                                writer.writerow([issue_id, journal_id, project, subject, author, created_on, notes, field, old, new])
        else:
            csv_headers  = [
                '#', 'Projekts', 'Trakeris', 'Parent task', 'Parent task subject', 'Statuss',
                'Prioritāte', 'Temats', 'Autors', 'Piešķirts', 'Atjaunots', 'Kategorija',
                'Mērķa versija', 'Sākuma datums', 'Sagaidāmais datums', 'Paredzētais laiks',
                'Total estimated time', 'Pavadītais laiks', 'Overall spent time',
                '% padarīti', 'Izveidots', 'Closed', 'Last updated by', 'Saistītie uzdevumi',
                'Pielikumi', 'Checklist', 'Atrisinājums', 'LUIS komponente', 'Pieteikuma tips',
                'Private', 'Story points', 'Sprint', 'Apraksts', 'Last notes']
            writer.writerow(csv_headers)
            for issue in all_issues:
                cf_dict = {}
                for cf in issue.get('custom_fields', []):
                    value = cf.get('value', '')
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    cf_dict[cf['name']] = value
                journals = issue.get('journals', [])
                last_journal = journals[-1] if journals else {}
                last_updated_by = last_journal.get('user', {}).get('name', '')
                last_notes = last_journal.get('notes', '').replace('\n', ' ').replace('\r', ' ')[:500]
                row = [
                    issue['id'],
                    issue.get('project', {}).get('name') or 'IT pieteikumu reģistrs',
                    issue['tracker']['name'],
                    issue.get('parent', {}).get('id', ''),
                    '',
                    issue['status']['name'],
                    issue.get('priority', {}).get('name', ''),
                    issue['subject'],
                    issue.get('author', {}).get('name', ''),
                    issue.get('assigned_to', {}).get('name', ''),
                    format_dt(issue.get('updated_on', '')),
                    issue.get('category', {}).get('name', ''),
                    issue.get('fixed_version', {}).get('name', ''),
                    issue.get('start_date', ''),
                    issue.get('due_date', ''),
                    issue.get('estimated_hours', ''),
                    '',
                    issue.get('spent_hours', ''),
                    issue.get('spent_hours', ''),
                    issue.get('done_ratio', ''),
                    format_dt(issue.get('created_on', '')),
                    format_dt(issue.get('closed_on', '')),
                    last_updated_by,
                    '', '', '', '',
                    cf_dict.get('LUIS komponente', ''),
                    pieteikuma_tips_mapping.get(cf_dict.get('Pieteikuma tips', ''), cf_dict.get('Pieteikuma tips', '')),
                    cf_dict.get('Private', ''),
                    cf_dict.get('Story points', ''),
                    cf_dict.get('Sprint', ''),
                    issue.get('description', '').replace('\n', ' ').replace('\r', ' ')[:500],
                    last_notes
                ]
                writer.writerow(row)

    log_and_print(f"Finished export for mode: {export_mode} → {csv_file}")

log_and_print("===== Redmine Issue Export Completed =====")
