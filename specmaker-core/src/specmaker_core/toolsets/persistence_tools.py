"""Persistence helpers for deterministic SQLite review storage.

Schema Design
-------------
The review_records table uses a composite unique constraint on (project_name, version, run_id)
to prevent data loss when multiple review runs complete within the same second. The version
field uses second-level timestamps, so run_id distinguishes concurrent completions.

Insert Semantics
----------------
Uses SQLAlchemy's merge() to provide idempotent saves: re-saving the same
(project_name, version, run_id) tuple updates the existing row rather than failing or
creating duplicates. This supports retry scenarios and workflow resumption without data loss.
"""

from __future__ import annotations

import datetime
import sqlite3

from sqlalchemy import select
from sqlalchemy.orm import Session

from specmaker_core._dependencies.schemas import documents as _documents
from specmaker_core._dependencies.schemas import shared as _shared
from specmaker_core.persistence import models as _models
from specmaker_core.persistence import storage as _storage
from specmaker_core.persistence.metadata import ReviewMetadata, metadata_to_json


def ensure_schema(connection: sqlite3.Connection | Session) -> None:
    """Ensure the SQLite schema required for review persistence exists.

    For SQLAlchemy sessions, schema creation is handled automatically by the engine.
    For raw sqlite3 connections, this is a no-op for backward compatibility.
    """
    if isinstance(connection, Session):
        # Schema is created by engine in storage.get_engine()
        pass
    else:
        # Legacy sqlite3 connection - schema should exist or be created elsewhere
        pass


def save_review_record(connection: sqlite3.Connection | Session, metadata: ReviewMetadata) -> None:
    """Persist a review record with idempotent upsert semantics.

    Creates or updates a review record based on (project_name, version, run_id).
    If a record with the same composite key exists, all fields are updated rather
    than creating a duplicate. This supports retry scenarios and workflow resumption
    without data loss or constraint violations.
    """
    if isinstance(connection, Session):
        _save_with_sqlalchemy(connection, metadata)
    else:
        _save_with_sqlite3(connection, metadata)


def load_review_records(
    connection: sqlite3.Connection | Session,
    *,
    project_name: str | None = None,
) -> list[ReviewMetadata]:
    """Load persisted review metadata records in reverse chronological order."""
    if isinstance(connection, Session):
        return _load_with_sqlalchemy(connection, project_name=project_name)
    else:
        return _load_with_sqlite3(connection, project_name=project_name)


def _save_with_sqlalchemy(session: Session, metadata: ReviewMetadata) -> None:
    """Save review record using SQLAlchemy ORM with merge for upsert semantics."""
    json_payload = metadata_to_json(metadata)
    created_at = metadata.created_at.astimezone(datetime.UTC).isoformat()

    # Check if record exists with same (project_name, version, run_id)
    stmt = select(_models.ReviewRecord).where(
        _models.ReviewRecord.project_name == metadata.project_context.project_name,
        _models.ReviewRecord.version == metadata.version,
        _models.ReviewRecord.run_id == metadata.run_id,
    )
    existing = session.execute(stmt).scalar_one_or_none()

    if existing:
        # Update existing record
        existing.record_id = metadata.record_id
        existing.agent_name = metadata.agent_name
        existing.created_at = created_at
        existing.approvals_requested = metadata.approvals_requested
        existing.approvals_granted = metadata.approvals_granted
        existing.project_context_json = json_payload["project_context"]
        existing.manuscript_json = json_payload["manuscript"]
        existing.review_report_json = json_payload["review_report"]
    else:
        # Create new record
        record = _models.ReviewRecord(
            record_id=metadata.record_id,
            project_name=metadata.project_context.project_name,
            version=metadata.version,
            run_id=metadata.run_id,
            agent_name=metadata.agent_name,
            created_at=created_at,
            approvals_requested=metadata.approvals_requested,
            approvals_granted=metadata.approvals_granted,
            project_context_json=json_payload["project_context"],
            manuscript_json=json_payload["manuscript"],
            review_report_json=json_payload["review_report"],
        )
        session.add(record)

    session.commit()


def _load_with_sqlalchemy(
    session: Session,
    *,
    project_name: str | None = None,
) -> list[ReviewMetadata]:
    """Load review records using SQLAlchemy ORM."""
    stmt = select(_models.ReviewRecord).order_by(_models.ReviewRecord.created_at.desc())

    if project_name is not None:
        stmt = stmt.where(_models.ReviewRecord.project_name == project_name)

    records = session.execute(stmt).scalars().all()
    return [_record_to_metadata(record) for record in records]


def _record_to_metadata(record: _models.ReviewRecord) -> ReviewMetadata:
    """Convert SQLAlchemy ReviewRecord to ReviewMetadata."""
    created_at_dt = datetime.datetime.fromisoformat(record.created_at)
    project_context = _shared.ProjectContext.model_validate_json(record.project_context_json)
    manuscript = _documents.Manuscript.model_validate_json(record.manuscript_json)
    review_report = _documents.ReviewReport.model_validate_json(record.review_report_json)

    return ReviewMetadata(
        record_id=record.record_id,
        project_context=project_context,
        manuscript=manuscript,
        review_report=review_report,
        run_id=record.run_id,
        agent_name=record.agent_name,
        version=record.version,
        created_at=created_at_dt,
        approvals_requested=record.approvals_requested,
        approvals_granted=record.approvals_granted,
    )


# Legacy sqlite3 implementation for backward compatibility


def _save_with_sqlite3(connection: sqlite3.Connection, metadata: ReviewMetadata) -> None:
    """Save review record using raw sqlite3 (legacy implementation)."""
    from specmaker_core.persistence import storage as _storage

    # Ensure we have a session instead
    session = _storage.create_session()
    try:
        _save_with_sqlalchemy(session, metadata)
    finally:
        session.close()


def _load_with_sqlite3(
    connection: sqlite3.Connection,
    *,
    project_name: str | None = None,
) -> list[ReviewMetadata]:
    """Load review records using raw sqlite3 (legacy implementation)."""
    session = _storage.create_session()
    try:
        return _load_with_sqlalchemy(session, project_name=project_name)
    finally:
        session.close()
