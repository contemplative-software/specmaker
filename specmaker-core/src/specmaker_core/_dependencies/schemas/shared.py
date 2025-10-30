"""Shared schemas such as ProjectContext, enums, identifiers, and common types."""

from __future__ import annotations

import datetime
import pathlib

import pydantic


class ProjectContext(pydantic.BaseModel):
    """Project metadata captured by the `/init` command."""

    model_config = pydantic.ConfigDict(frozen=True, str_strip_whitespace=True)

    project_name: str = pydantic.Field(min_length=1)
    repository_root: pathlib.Path
    description: str = pydantic.Field(min_length=1)
    audience: list[str]
    constraints: list[str]
    style_rules: str = pydantic.Field(default="google", min_length=1)
    created_by: str = pydantic.Field(min_length=1)
    created_at: datetime.datetime

    @pydantic.field_validator("audience", "constraints", mode="after")
    @classmethod
    def _strip_list_entries(cls, values: list[str]) -> list[str]:
        trimmed_values = [value.strip() for value in values]
        if any(not entry for entry in trimmed_values):
            raise ValueError("Audience and constraint entries must be non-empty strings.")
        return trimmed_values

    @pydantic.model_validator(mode="after")
    def _normalize(self) -> ProjectContext:
        style_rules = self.style_rules or "google"
        object.__setattr__(self, "style_rules", style_rules)
        return self
