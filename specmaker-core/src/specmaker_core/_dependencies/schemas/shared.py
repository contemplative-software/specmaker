"""Shared schemas such as ProjectContext, enums, identifiers, and common types."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectContext(BaseModel):
    """Project metadata captured by the `/init` command."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    project_name: str = Field(min_length=1)
    repository_root: Path
    description: str = Field(min_length=1)
    audience: list[str]
    constraints: list[str]
    style_rules: str = Field(default="google", min_length=1)
    created_by: str = Field(min_length=1)
    created_at: datetime

    @field_validator("audience", "constraints", mode="after")
    @classmethod
    def _strip_list_entries(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values]

    @model_validator(mode="after")
    def _normalize(self) -> ProjectContext:
        style_rules = self.style_rules or "google"
        object.__setattr__(self, "style_rules", style_rules)
        return self
