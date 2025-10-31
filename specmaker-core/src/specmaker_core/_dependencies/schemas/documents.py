"""Document schemas shared across SpecMaker agents and persistence layers."""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

import pydantic


class DocumentDraft(pydantic.BaseModel):
    """Outline produced by the architect agent before full manuscript drafting."""

    model_config = pydantic.ConfigDict(frozen=True, str_strip_whitespace=True)

    title: str = pydantic.Field(min_length=1)
    summary: str = pydantic.Field(min_length=1)
    sections: list[str] = pydantic.Field(default_factory=list)
    style_rules: str = pydantic.Field(default="google", min_length=1)
    created_at: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.utcnow)


class Manuscript(pydantic.BaseModel):
    """Full prose document produced by the writer agent."""

    model_config = pydantic.ConfigDict(frozen=True, str_strip_whitespace=True)

    title: str = pydantic.Field(min_length=1)
    content_markdown: str = pydantic.Field(min_length=1)
    style_rules: str = pydantic.Field(default="google", min_length=1)
    created_at: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.utcnow)


class ReviewIssue(pydantic.BaseModel):
    """Single review finding with severity, category, and optional location."""

    model_config = pydantic.ConfigDict(frozen=True, str_strip_whitespace=True)

    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))
    category: Literal["clarity", "accuracy", "structure", "grammar", "style", "other"]
    severity: Literal["blocking", "major", "minor"]
    message: str = pydantic.Field(min_length=1)
    location: str | None = None


class ReviewReport(pydantic.BaseModel):
    """Aggregate review result summarizing status and issues for a manuscript."""

    model_config = pydantic.ConfigDict(frozen=True, str_strip_whitespace=True)

    status: Literal["pass", "changes_required", "blocked"]
    summary: str = pydantic.Field(min_length=1)
    issues: list[ReviewIssue] = pydantic.Field(default_factory=list)
    style_rules: str = pydantic.Field(default="google", min_length=1)
    confidence_percent: float = pydantic.Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.utcnow)
