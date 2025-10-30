"""Implementation for the `init` command entrypoint."""

from __future__ import annotations

import collections.abc
import logging
import pathlib

from specmaker_core._dependencies.errors import SpecMakerError, ValidationError
from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core._dependencies.utils.paths import (
    PROJECT_CONTEXT_FILENAME,
    README_FILENAME,
    manifest_path,
    project_context_path,
    readme_path,
    specmaker_root,
)
from specmaker_core._dependencies.utils.serialization import to_json

LOGGER = logging.getLogger(__name__)


class InitError(SpecMakerError):
    """Raised when the init flow fails to write expected files."""


def init(context: ProjectContext) -> ProjectContext:
    """Create the `.specmaker/` bootstrapped project structure."""
    root_dir = pathlib.Path(context.repository_root)
    try:
        spec_dir = specmaker_root(root_dir)
    except FileNotFoundError as exc:  # pragma: no cover - defensive branch
        msg = f"Repository root does not exist: {root_dir}"
        raise ValidationError(msg) from exc

    spec_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Ensured SpecMaker directory at %s", spec_dir)

    _write_project_context(project_context_path(root_dir), context)
    _write_manifest(manifest_path(root_dir))
    _write_readme(readme_path(root_dir), context)
    return context


def _write_project_context(path: pathlib.Path, context: ProjectContext) -> None:
    """Write the project context file for the project."""
    if path.exists():
        LOGGER.info("Skipped existing %s", path)
        return

    _safe_write(path, context.model_dump_json(indent=2))
    LOGGER.info("Wrote project context to %s", path)


def _write_manifest(path: pathlib.Path) -> None:
    """Write the manifest file for the project."""
    if path.exists():
        LOGGER.info("Skipped existing %s", path)
        return

    manifest = {
        "schema": "specmaker.init-manifest",
        "version": 1,
        "files": [str(PROJECT_CONTEXT_FILENAME), str(README_FILENAME)],
    }
    _safe_write(path, to_json(manifest))
    LOGGER.info("Wrote manifest to %s", path)


def _write_readme(path: pathlib.Path, context: ProjectContext) -> None:
    """Write the README file for the project."""
    if path.exists():
        LOGGER.info("Skipped existing %s", path)
        return

    lines = [
        f"# SpecMaker Project: {context.project_name}",
        "",
        "## Description",
        context.description,
        "",
        "## Audience",
        *(_formatted_list(context.audience)),
        "",
        "## Constraints",
        *(_formatted_list(context.constraints)),
        "",
        "## Metadata",
        f"- Created by: {context.created_by}",
        f"- Created at: {context.created_at.isoformat()}",
        f"- Style rules: {context.style_rules}",
        "",
    ]
    _safe_write(path, "\n".join(lines))
    LOGGER.info("Wrote README to %s", path)


def _formatted_list(values: collections.abc.Iterable[str]) -> collections.abc.Iterable[str]:
    """Format a list of values as a bulleted list."""
    return [f"- {value}" for value in values] or ["- (none)"]


def _safe_write(path: pathlib.Path, content: str) -> None:
    """Write content to a file, raising an error if the write fails."""
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:  # pragma: no cover - I/O failure
        msg = f"Failed to write {path}: {exc}"
        raise InitError(msg) from exc
