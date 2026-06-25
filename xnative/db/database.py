from __future__ import annotations

import sqlite3
from pathlib import Path

from xnative.core.config import settings
from xnative.db.migration_runner import run_migrations


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={settings.db_busy_timeout_ms}")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    settings.ensure_dirs()
    db_path = Path(path) if path is not None and str(path) != ":memory:" else path
    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path or settings.database_path)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    return conn


def init_db(path: str | Path | None = None) -> sqlite3.Connection:
    conn = connect(path)
    run_migrations(conn)
    return conn
