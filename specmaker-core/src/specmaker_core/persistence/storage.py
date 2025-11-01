"""SQLite storage helpers for durable review persistence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

DEFAULT_DB_PATH: Final[Path] = Path(".specmaker/specmaker.db")


def ensure_parent(path: Path) -> Path:
    """Ensure parent directory exists and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def open_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with WAL enabled."""
    path = ensure_parent(db_path)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    return connection


def version_stamp(timestamp: datetime | None = None) -> str:
    """Return a UTC timestamp string suitable for versioning records."""
    moment = timestamp or datetime.now(tz=UTC)
    return moment.strftime("%Y%m%d%H%M%S")
