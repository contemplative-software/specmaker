"""SQLAlchemy ORM models for review persistence."""

from __future__ import annotations

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ReviewRecord(Base):
    """ORM model for persisting manuscript review records.

    Schema Design
    -------------
    The composite unique constraint on (project_name, version, run_id) prevents data
    loss when multiple review runs complete within the same second. The version field
    uses second-level timestamps, so run_id distinguishes concurrent completions.
    """

    __tablename__ = "review_records"

    record_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    approvals_requested: Mapped[int] = mapped_column(nullable=False)
    approvals_granted: Mapped[int] = mapped_column(nullable=False)
    project_context_json: Mapped[str] = mapped_column(String, nullable=False)
    manuscript_json: Mapped[str] = mapped_column(String, nullable=False)
    review_report_json: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_name", "version", "run_id", name="uq_project_version_run"),
        Index("idx_review_records_project", "project_name", "created_at"),
    )
