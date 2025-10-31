"""Persistence helpers for deterministic SQLite review storage."""

from __future__ import annotations

import datetime
import sqlite3
from collections.abc import Sequence
from typing import cast

from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core.contracts.documents import Manuscript, ReviewReport
from specmaker_core.persistence.metadata import ReviewMetadata, metadata_to_json

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS review_records (
    record_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    approvals_requested INTEGER NOT NULL,
    approvals_granted INTEGER NOT NULL,
    project_context_json TEXT NOT NULL,
    manuscript_json TEXT NOT NULL,
    review_report_json TEXT NOT NULL,
    UNIQUE(project_name, version)
);
"""

CREATE_PROJECT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_review_records_project
    ON review_records(project_name, created_at DESC);
"""

INSERT_SQL = """
INSERT OR REPLACE INTO review_records (
    record_id,
    project_name,
    version,
    run_id,
    agent_name,
    created_at,
    approvals_requested,
    approvals_granted,
    project_context_json,
    manuscript_json,
    review_report_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SELECT_ALL_SQL = """
SELECT
    record_id,
    project_name,
    version,
    run_id,
    agent_name,
    created_at,
    approvals_requested,
    approvals_granted,
    project_context_json,
    manuscript_json,
    review_report_json
FROM review_records
WHERE (? IS NULL OR project_name = ?)
ORDER BY created_at DESC;
"""


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Ensure the SQLite schema required for review persistence exists."""
    connection.execute(CREATE_TABLE_SQL)
    connection.execute(CREATE_PROJECT_INDEX_SQL)


def save_review_record(connection: sqlite3.Connection, metadata: ReviewMetadata) -> None:
    """Persist a review record deterministically."""
    ensure_schema(connection)
    json_payload = metadata_to_json(metadata)
    created_at = metadata.created_at.astimezone(datetime.UTC).isoformat()

    connection.execute(
        INSERT_SQL,
        (
            metadata.record_id,
            metadata.project_context.project_name,
            metadata.version,
            metadata.run_id,
            metadata.agent_name,
            created_at,
            metadata.approvals_requested,
            metadata.approvals_granted,
            json_payload["project_context"],
            json_payload["manuscript"],
            json_payload["review_report"],
        ),
    )
    connection.commit()


def load_review_records(
    connection: sqlite3.Connection,
    *,
    project_name: str | None = None,
) -> list[ReviewMetadata]:
    """Load persisted review metadata records in reverse chronological order."""
    ensure_schema(connection)
    cursor = connection.execute(SELECT_ALL_SQL, (project_name, project_name))
    rows = cursor.fetchall()
    return [_row_to_metadata(row) for row in rows]


def _row_to_metadata(row: Sequence[object]) -> ReviewMetadata:
    (
        record_id,
        _project_name,
        version,
        run_id,
        agent_name,
        created_at,
        approvals_requested,
        approvals_granted,
        project_context_json,
        manuscript_json,
        review_report_json,
    ) = row

    created_at_dt = datetime.datetime.fromisoformat(str(created_at))
    project_context = ProjectContext.model_validate_json(str(project_context_json))
    manuscript = Manuscript.model_validate_json(str(manuscript_json))
    review_report = ReviewReport.model_validate_json(str(review_report_json))

    return ReviewMetadata(
        record_id=str(record_id),
        project_context=project_context,
        manuscript=manuscript,
        review_report=review_report,
        run_id=str(run_id),
        agent_name=str(agent_name),
        version=str(version),
        created_at=created_at_dt,
        approvals_requested=cast(int, approvals_requested),
        approvals_granted=cast(int, approvals_granted),
    )


__all__ = ["ensure_schema", "load_review_records", "save_review_record"]
