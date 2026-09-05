"""
SQL Server -> Oracle schema + data migration.

Discovers tables and columns directly from INFORMATION_SCHEMA (no
hardcoded table list to maintain), builds Oracle column types from
SQL Server's type/length/precision metadata, creates target tables
if they don't already exist, and streams data across in batches with
per-table error isolation and row-count verification.

Config is entirely environment-variable driven - see README.md.
"""

import os
import sys
import logging
from datetime import datetime

import pyodbc

# ============================================================
# Config - set via environment variables, never hardcode credentials.
# ============================================================
SOURCE_SERVER = os.environ.get("MIGRATION_SOURCE_SERVER")
SOURCE_DATABASE = os.environ.get("MIGRATION_SOURCE_DATABASE")
SOURCE_UID = os.environ.get("MIGRATION_SOURCE_UID")
SOURCE_PWD = os.environ.get("MIGRATION_SOURCE_PWD")
TARGET_DSN = os.environ.get("MIGRATION_TARGET_DSN")
TARGET_UID = os.environ.get("MIGRATION_TARGET_UID")
TARGET_PWD = os.environ.get("MIGRATION_TARGET_PWD")

if not all([SOURCE_SERVER, SOURCE_DATABASE, SOURCE_UID, SOURCE_PWD, TARGET_DSN, TARGET_UID, TARGET_PWD]):
    sys.exit(
        "Set MIGRATION_SOURCE_SERVER, MIGRATION_SOURCE_DATABASE, MIGRATION_SOURCE_UID, "
        "MIGRATION_SOURCE_PWD, MIGRATION_TARGET_DSN, MIGRATION_TARGET_UID, MIGRATION_TARGET_PWD "
        "environment variables before running."
    )

# Optionally restrict to specific tables; leave empty to migrate every
# base table in the source database (auto-discovered).
TABLE_ALLOWLIST = []

BATCH_SIZE = 5000

# ============================================================
# Logging
# ============================================================
logfile = f"mssql_to_oracle_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(logfile, mode="w", encoding="utf-8"), logging.StreamHandler()]
)

# ============================================================
# Type mapping: SQL Server -> Oracle
# ============================================================
TYPE_MAPPING = {
    "int": "NUMBER(10)",
    "bigint": "NUMBER(19)",
    "smallint": "NUMBER(5)",
    "tinyint": "NUMBER(3)",
    "bit": "NUMBER(1)",
    "decimal": "NUMBER",
    "numeric": "NUMBER",
    "float": "FLOAT",
    "real": "FLOAT",
    "money": "NUMBER(19,4)",
    "smallmoney": "NUMBER(10,4)",
    "char": "VARCHAR2",
    "varchar": "VARCHAR2",
    "nvarchar": "VARCHAR2",
    "text": "CLOB",
    "ntext": "CLOB",
    "date": "DATE",
    "datetime": "DATE",
    "smalldatetime": "DATE",
    "datetime2": "TIMESTAMP",
    "uniqueidentifier": "RAW(16)",
    "image": "BLOB",
    "varbinary": "BLOB",
    "binary": "BLOB",
}


def safe_truncate(value, maxlen):
    """Truncate a string safely to fit an Oracle VARCHAR2 limit."""
    if isinstance(value, str) and len(value) > maxlen:
        return value[:maxlen]
    return value


def build_column_type(coltype, collen, prec, scale):
    """Decide the Oracle column type for one SQL Server column."""
    coltype_lower = coltype.lower()

    if coltype_lower in ("decimal", "numeric") and prec:
        return f"NUMBER({prec},{scale})" if scale else f"NUMBER({prec})"

    if coltype_lower in ("varchar", "nvarchar", "char"):
        length = collen if collen and collen >= 50 else 50
        if length > 4000:
            return "CLOB"
        return f"VARCHAR2({min(int(length * 1.5), 4000)})"

    if coltype_lower in ("image", "varbinary", "binary"):
        return "BLOB"

    return TYPE_MAPPING.get(coltype_lower, "VARCHAR2(4000)")


def discover_tables(source_cursor):
    """List base tables in the source database, honoring TABLE_ALLOWLIST if set."""
    source_cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    all_tables = [row[0] for row in source_cursor.fetchall()]
    if TABLE_ALLOWLIST:
        return [t for t in all_tables if t in TABLE_ALLOWLIST]
    return all_tables


def migrate_table(table, source_cursor, target_cursor, target_cnx):
    logging.info(f"=== Processing {table} ===")

    source_cursor.execute(
        """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """,
        (table,),
    )
    columns = source_cursor.fetchall()
    if not columns:
        logging.warning(f"No columns found for table {table}")
        return

    source_cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    source_rowcount = source_cursor.fetchone()[0]
    logging.info(f"Source {table}: {len(columns)} columns, {source_rowcount} rows")

    target_table = table.upper()

    # Skip if the target table already exists - makes re-runs idempotent.
    target_cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = ?", (target_table,))
    if target_cursor.fetchone()[0]:
        logging.info(f"[SKIP] Oracle table already exists: {target_table}")
        return

    col_defs = [
        f'"{colname}" {build_column_type(coltype, collen, prec, scale)}'
        for colname, coltype, collen, prec, scale in columns
    ]
    create_sql = f"CREATE TABLE {target_table} ({', '.join(col_defs)})"
    try:
        target_cursor.execute(create_sql)
        target_cnx.commit()
        logging.info(f"[CREATE] {target_table}")
    except Exception as e:
        logging.error(f"[ERROR] Creating table {target_table}: {e}")
        target_cnx.rollback()
        return

    # Stream rows across in batches rather than loading the whole table into memory.
    source_cursor.execute(f"SELECT * FROM [{table}]")
    col_list = ", ".join([f'"{c[0]}"' for c in columns])
    placeholders = ", ".join([f":{i + 1}" for i in range(len(columns))])
    insert_sql = f"INSERT INTO {target_table} ({col_list}) VALUES ({placeholders})"

    total_inserted = 0
    while True:
        rows = source_cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break

        prepared_rows = []
        for row in rows:
            converted = []
            for idx, val in enumerate(row):
                dtype = columns[idx][1].lower()
                collen = columns[idx][2]
                if val is None:
                    converted.append(None)
                elif dtype in ("varchar", "nvarchar", "char") and collen and collen <= 4000:
                    converted.append(safe_truncate(val, int(collen * 1.2)))
                elif dtype in ("image", "varbinary", "binary"):
                    converted.append(bytes(val) if val is not None and not isinstance(val, bytes) else val)
                else:
                    converted.append(val)
            prepared_rows.append(tuple(converted))

        target_cursor.executemany(insert_sql, prepared_rows)
        target_cnx.commit()
        total_inserted += len(prepared_rows)
        logging.info(f"[INSERT] {table}: {total_inserted}/{source_rowcount} rows")

    target_cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
    target_rowcount = target_cursor.fetchone()[0]
    status = "OK" if target_rowcount == source_rowcount else "MISMATCH"
    logging.info(f"[VERIFY] {target_table}: source={source_rowcount} target={target_rowcount} [{status}]")


def main():
    source_cnx = pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={SOURCE_SERVER};"
        f"Database={SOURCE_DATABASE};"
        f"Uid={SOURCE_UID};"
        f"Pwd={SOURCE_PWD};"
        "TrustServerCertificate=yes;"
    )
    target_cnx = pyodbc.connect(f"DSN={TARGET_DSN};Uid={TARGET_UID};Pwd={TARGET_PWD};", autocommit=False)

    source_cursor = source_cnx.cursor()
    target_cursor = target_cnx.cursor()

    tables = discover_tables(source_cursor)
    logging.info(f"Discovered {len(tables)} table(s) to migrate")

    for table in tables:
        try:
            migrate_table(table, source_cursor, target_cursor, target_cnx)
        except Exception as e:
            logging.error(f"[FAIL] {table}: {e}")
            target_cnx.rollback()

    source_cnx.close()
    target_cnx.close()
    logging.info("Migration completed.")


if __name__ == "__main__":
    main()
