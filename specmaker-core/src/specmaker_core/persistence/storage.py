"""SQLite storage helpers for durable review persistence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from specmaker_core.persistence import models as _models

DEFAULT_DB_PATH: Final[Path] = Path(".specmaker/specmaker.db")


def ensure_parent(path: Path) -> Path:
    """Ensure parent directory exists and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def open_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with WAL enabled.

    Note: This is maintained for backward compatibility. New code should use
    get_engine() and create_session() for SQLAlchemy-based access.
    """
    path = ensure_parent(db_path)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    return connection


def _set_sqlite_pragma(dbapi_conn: sqlite3.Connection, _connection_record: object) -> None:
    """Enable WAL mode and foreign keys for SQLite connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine(db_path: Path = DEFAULT_DB_PATH) -> Engine:
    """Create and configure a SQLAlchemy engine for the database."""
    path = ensure_parent(db_path)
    engine = create_engine(f"sqlite:///{path}", echo=False)

    # Enable WAL mode and foreign keys for SQLite
    event.listens_for(Engine, "connect")(_set_sqlite_pragma)

    # Create tables
    _models.Base.metadata.create_all(engine)

    return engine


def create_session(db_path: Path = DEFAULT_DB_PATH) -> Session:
    """Create a new SQLAlchemy session for database operations."""
    engine = get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def version_stamp(timestamp: datetime | None = None) -> str:
    """Return a UTC timestamp string suitable for versioning records."""
    moment = timestamp or datetime.now(tz=UTC)
    return moment.strftime("%Y%m%d%H%M%S")
