from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass(frozen=True)
class AppliedMigration:
    version: str
    checksum: str


def migration_checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version TEXT PRIMARY KEY,
          checksum TEXT NOT NULL,
          applied_at INTEGER NOT NULL
        )
        """
    )


def applied_migrations(conn: sqlite3.Connection) -> dict[str, AppliedMigration]:
    ensure_migration_table(conn)
    rows = conn.execute("SELECT version, checksum FROM schema_migrations").fetchall()
    return {
        str(row["version"]): AppliedMigration(str(row["version"]), str(row["checksum"]))
        for row in rows
    }


def run_migrations(conn: sqlite3.Connection) -> list[AppliedMigration]:
    ensure_migration_table(conn)
    applied = applied_migrations(conn)
    installed: list[AppliedMigration] = []
    for path in _migration_files():
        version = path.name.split("_", 1)[0]
        sql = path.read_text(encoding="utf-8")
        checksum = migration_checksum(sql)
        existing = applied.get(version)
        if existing:
            if existing.checksum != checksum:
                raise RuntimeError(
                    f"Migration checksum mismatch for {path.name}: "
                    f"{existing.checksum} != {checksum}"
                )
            continue
        conn.execute("BEGIN")
        try:
            conn.executescript(sql)
            conn.execute(
                """
                INSERT INTO schema_migrations(version, checksum, applied_at)
                VALUES (?, ?, CAST((julianday('now') - 2440587.5) * 86400000000 AS INTEGER))
                """,
                (version, checksum),
            )
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
            installed.append(AppliedMigration(version, checksum))
    return installed
