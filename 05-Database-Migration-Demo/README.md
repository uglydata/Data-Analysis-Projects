# Database Migration Demo

## About this project

These two scripts generalize a database migration pattern (schema
discovery, type mapping, batched transfer, verification) that I built
and used in a real professional engagement. Table names, schema
details, server addresses, and all identifying specifics have been
replaced with dynamic discovery or removed entirely - nothing here
reflects any real client's actual data or schema. The technique and
code structure are real; the specifics are not.

**Why this was necessary:** the real source system was an old SQL
Server 2008 instance with no drivers available for standard Oracle
migration tooling (e.g. SQL Developer's migration wizard) to connect
to it directly. Without a compatible driver, the only fallback was
fully manual: exporting each table from SQL Server's admin tools to
CSV, then importing into Oracle by hand - an approach I estimated
would have taken weeks, possibly a month, across an entire schema.
Connecting directly via a generic ODBC driver (rather than
tool-specific connectors) sidestepped that limitation entirely, and
the resulting script completed the same migration in roughly 30
minutes.

## Problem

Moving a relational schema from one engine to another (MySQL/MariaDB
or SQL Server, in this case) to Oracle isn't just a data copy - the
two engines disagree on types, length limits, reserved words, and
what a "safe" batch size looks like. A one-off `INSERT INTO ... SELECT
*` script breaks the moment a `VARCHAR` exceeds Oracle's 4000-byte
limit, a table name collides with a reserved word, or the source
table has more rows than fit comfortably in one transaction.

## Approach

Both scripts follow the same shape:

1. **Discover** tables and columns from the source database's
   `INFORMATION_SCHEMA` rather than maintaining a hardcoded table
   list - the script adapts to whatever schema it's pointed at.
2. **Map types** from the source engine to the closest Oracle
   equivalent (`VARCHAR` length limits, `DECIMAL` precision/scale,
   `DATETIME`/`TIMESTAMP`, binary/BLOB types, reserved-word table
   names).
3. **Create** the target table if it doesn't already exist - reruns
   are idempotent; a table that's already been migrated is skipped.
4. **Transfer data in batches** (default 5000 rows) rather than
   loading an entire table into memory or committing one giant
   transaction.
5. **Verify** row counts between source and target per table, and
   isolate failures so one bad table doesn't abort the whole run.

`migrate_mysql_to_oracle.py` and `migrate_mssql_to_oracle.py` differ
mainly in how each source engine exposes schema metadata
(`SHOW FULL COLUMNS` vs `INFORMATION_SCHEMA.COLUMNS` with explicit
length/precision/scale columns) and in their type-mapping tables.

## Setup

Both scripts read every credential and connection detail from
environment variables - nothing is hardcoded.

**`migrate_mysql_to_oracle.py`:**
```
MIGRATION_SOURCE_USER
MIGRATION_SOURCE_PASSWORD
MIGRATION_SOURCE_HOST
MIGRATION_SOURCE_PORT      (optional, defaults to 3306)
MIGRATION_SOURCE_DATABASE
MIGRATION_TARGET_DSN
MIGRATION_TARGET_USER
MIGRATION_TARGET_PASSWORD
```

**`migrate_mssql_to_oracle.py`:**
```
MIGRATION_SOURCE_SERVER
MIGRATION_SOURCE_DATABASE
MIGRATION_SOURCE_UID
MIGRATION_SOURCE_PWD
MIGRATION_TARGET_DSN
MIGRATION_TARGET_UID
MIGRATION_TARGET_PWD
```

To try `migrate_mysql_to_oracle.py` against a real (public, freely
downloadable) dataset, point `MIGRATION_SOURCE_DATABASE` at a MySQL
install of [Sakila](https://dev.mysql.com/doc/sakila/en/) - no code
changes needed, since tables are discovered automatically.

## Limitations / what I'd do differently at scale

- This is a full-reload pattern - it re-copies whatever isn't already
  present, but it doesn't handle ongoing sync. A production migration
  with a live source would need change-data-capture (e.g. Debezium)
  or a cutover window, not a batch reload.
- Table order isn't foreign-key-aware. For a schema with FK
  constraints on the target, tables need to be created in dependency
  order, or constraints added after all data is loaded.
- Row-count verification catches *missing* rows, not *corrupted*
  ones (e.g. a truncated string that still counts as "migrated"). A
  stricter check would hash a sample of rows on both sides.
- Both scripts process one table at a time; large migrations would
  benefit from migrating independent tables in parallel.
