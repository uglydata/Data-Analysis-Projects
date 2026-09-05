"""
MySQL/MariaDB -> Oracle schema + data migration.

Discovers tables and columns directly from the source database's
INFORMATION_SCHEMA (no hardcoded table list to maintain), maps MySQL
column types to their closest Oracle equivalent, creates the target
tables if they don't already exist, and copies the data across in
batches with per-table error isolation and row-count verification.

Config is entirely environment-variable driven - see README.md for
the full list and how to run this against a local Sakila install.
"""

import os
import sys
import re
import logging
from datetime import datetime

import mysql.connector
import pyodbc

# ============================================================
# Config - set via environment variables, never hardcode credentials.
# ============================================================
SOURCE_CONFIG = {
    'user': os.environ.get('MIGRATION_SOURCE_USER'),
    'password': os.environ.get('MIGRATION_SOURCE_PASSWORD'),
    'host': os.environ.get('MIGRATION_SOURCE_HOST'),
    'port': int(os.environ.get('MIGRATION_SOURCE_PORT', 3306)),
    'database': os.environ.get('MIGRATION_SOURCE_DATABASE'),
}

TARGET_CONFIG = {
    'dsn': os.environ.get('MIGRATION_TARGET_DSN'),
    'user': os.environ.get('MIGRATION_TARGET_USER'),
    'password': os.environ.get('MIGRATION_TARGET_PASSWORD'),
}

if not all(SOURCE_CONFIG.values()) or not all(TARGET_CONFIG.values()):
    sys.exit(
        "Set MIGRATION_SOURCE_USER, MIGRATION_SOURCE_PASSWORD, MIGRATION_SOURCE_HOST, "
        "MIGRATION_SOURCE_DATABASE, MIGRATION_TARGET_DSN, MIGRATION_TARGET_USER, "
        "MIGRATION_TARGET_PASSWORD environment variables before running."
    )

# Optionally restrict to specific tables; leave empty to migrate every
# table in the source schema (auto-discovered via INFORMATION_SCHEMA).
TABLE_ALLOWLIST = []

BATCH_SIZE = 5000

# ============================================================
# Logging
# ============================================================
logfile = f"mysql_to_oracle_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(logfile, mode='w', encoding='utf-8'), logging.StreamHandler()]
)

# ============================================================
# Type mapping: MySQL -> Oracle
# ============================================================
TYPE_MAPPING = {
    'int': 'NUMBER',
    'bigint': 'NUMBER',
    'smallint': 'NUMBER',
    'tinyint': 'NUMBER',
    'varchar': 'VARCHAR2(4000)',
    'char': 'CHAR(1)',
    'text': 'CLOB',
    'longtext': 'CLOB',
    'mediumtext': 'CLOB',
    'datetime': 'DATE',
    'timestamp': 'DATE',
    'date': 'DATE',
    'decimal': 'NUMBER',
    'float': 'FLOAT',
    'double': 'FLOAT',
    'enum': 'VARCHAR2(255)',
    'blob': 'BLOB',
}


def map_type(mysql_type):
    """Map a MySQL column type string to its closest Oracle equivalent."""
    mysql_type = mysql_type.lower()
    if 'varchar' in mysql_type:
        m = re.search(r'varchar\((\d+)\)', mysql_type)
        if m and int(m.group(1)) > 4000:
            return 'CLOB'
        return f'VARCHAR2({min(int(m.group(1)), 4000)})'
    for prefix, oracle_type in TYPE_MAPPING.items():
        if mysql_type.startswith(prefix):
            return oracle_type
    return 'VARCHAR2(4000)'


def safe_table_name(name):
    """Quote/rename tables that collide with Oracle reserved words."""
    if name.upper() in ('USER', 'GROUP', 'ORDER', 'LEVEL', 'COMMENT'):
        return f'"{name.upper()}_"'
    return name.upper()


def discover_tables(source_cursor):
    """List tables in the source schema, honoring TABLE_ALLOWLIST if set."""
    source_cursor.execute("SHOW TABLES")
    all_tables = [row[0] for row in source_cursor.fetchall()]
    if TABLE_ALLOWLIST:
        return [t for t in all_tables if t in TABLE_ALLOWLIST]
    return all_tables


def migrate_table(table, target_cursor, target_cnx, source_cnx):
    target_table = safe_table_name(table)
    source_cursor = source_cnx.cursor(dictionary=True)

    logging.info(f"=== Processing {table} -> {target_table} ===")

    # Skip if the target table already exists - makes re-runs idempotent.
    target_cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = ?", (target_table.strip('"'),))
    if target_cursor.fetchone()[0]:
        logging.info(f"[SKIP] Oracle table already exists: {target_table}")
        source_cursor.close()
        return

    # Discover columns and types from the source.
    source_cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")
    columns = source_cursor.fetchall()
    col_names = [col['Field'] for col in columns]
    col_defs = [f'"{col["Field"].upper()}" {map_type(col["Type"])}' for col in columns]

    create_sql = f"CREATE TABLE {target_table} ({', '.join(col_defs)})"
    try:
        target_cursor.execute(create_sql)
        target_cnx.commit()
        logging.info(f"[CREATE] {target_table}")
    except Exception as e:
        logging.error(f"[ERROR] Creating table {target_table}: {e}")
        target_cnx.rollback()
        source_cursor.close()
        return

    # Copy data in batches.
    source_cursor.execute(f"SELECT * FROM `{table}`")
    rows = source_cursor.fetchall()
    logging.info(f"[FETCH] {len(rows)} rows from {table}")

    if rows:
        placeholders = ", ".join([f":{i + 1}" for i in range(len(col_names))])
        column_list = ", ".join([f'"{c.upper()}"' for c in col_names])
        insert_sql = f"INSERT INTO {target_table} ({column_list}) VALUES ({placeholders})"

        try:
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i:i + BATCH_SIZE]
                target_cursor.executemany(insert_sql, [[row[col] for col in col_names] for row in batch])
                target_cnx.commit()
                logging.info(f"[INSERT] Batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
        except Exception as e:
            logging.error(f"[ERROR] Insert failed for {target_table}: {e}")
            target_cnx.rollback()

    # Verify row counts match between source and target.
    try:
        target_cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        target_count = target_cursor.fetchone()[0]
        source_count = len(rows)
        status = "OK" if target_count == source_count else "MISMATCH"
        logging.info(f"[VERIFY] {target_table}: source={source_count} target={target_count} [{status}]")
    except Exception as e:
        logging.warning(f"[WARN] Row count verification failed for {target_table}: {e}")

    source_cursor.close()


def main():
    source_cnx = mysql.connector.connect(**SOURCE_CONFIG)
    target_cnx = pyodbc.connect(
        f"DSN={TARGET_CONFIG['dsn']};Uid={TARGET_CONFIG['user']};Pwd={TARGET_CONFIG['password']};",
        autocommit=False,
    )
    target_cursor = target_cnx.cursor()

    discovery_cursor = source_cnx.cursor()
    tables = discover_tables(discovery_cursor)
    discovery_cursor.close()
    logging.info(f"Discovered {len(tables)} table(s) to migrate")

    for table in tables:
        try:
            migrate_table(table, target_cursor, target_cnx, source_cnx)
        except Exception as e:
            logging.error(f"[FAIL] {table}: {e}")

    target_cursor.close()
    target_cnx.close()
    source_cnx.close()


if __name__ == "__main__":
    main()
