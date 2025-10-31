"""Metadata helpers for persisting manuscript reviews."""

from __future__ import annotations

import datetime
import uuid
from typing import Final

import pydantic

from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core.contracts.documents import Manuscript, ReviewReport


class ReviewMetadata(pydantic.BaseModel):
    """Normalized record persisted alongside manuscripts and review reports."""

    model_config = pydantic.ConfigDict(frozen=True)

    record_id: str
    project_context: ProjectContext
    manuscript: Manuscript
    review_report: ReviewReport
    run_id: str
    agent_name: str
    version: str
    created_at: datetime.datetime
    approvals_requested: int
    approvals_granted: int

    @pydantic.field_validator("record_id", mode="before")
    @classmethod
    def _default_record_id(cls, value: str | None) -> str:
        return value or str(uuid.uuid4())


def build_review_metadata(
    *,
    project_context: ProjectContext,
    manuscript: Manuscript,
    review_report: ReviewReport,
    run_id: str,
    agent_name: str,
    version: str,
    created_at: datetime.datetime,
    approvals_requested: int,
    approvals_granted: int,
) -> ReviewMetadata:
    """Construct a review metadata record with normalized values."""
    return ReviewMetadata(
        record_id=f"{project_context.project_name}:{version}:{run_id}",
        project_context=project_context,
        manuscript=manuscript,
        review_report=review_report,
        run_id=run_id,
        agent_name=agent_name,
        version=version,
        created_at=created_at,
        approvals_requested=approvals_requested,
        approvals_granted=approvals_granted,
    )


SERIALIZED_FIELDS: Final[tuple[str, ...]] = (
    "project_context",
    "manuscript",
    "review_report",
)


def metadata_to_json(metadata: ReviewMetadata) -> dict[str, str]:
    """Return JSON strings for nested models suitable for SQLite storage."""
    json_payload: dict[str, str] = {}
    for field in SERIALIZED_FIELDS:
        model = getattr(metadata, field)
        json_payload[field] = model.model_dump_json()
    return json_payload


__all__ = [
    "SERIALIZED_FIELDS",
    "ReviewMetadata",
    "build_review_metadata",
    "metadata_to_json",
]
