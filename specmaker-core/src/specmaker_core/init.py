"""Implementation for the `init` command entrypoint."""

from __future__ import annotations

import importlib.resources
import logging
import pathlib

import jinja2

from ._dependencies import errors
from ._dependencies.schemas import shared
from ._dependencies.utils import paths, serialization

LOGGER = logging.getLogger(__name__)


class InitError(errors.SpecMakerError):
    """Raised when the init flow fails to write expected files."""


def init(context: shared.ProjectContext) -> shared.ProjectContext:
    """Create the `.specmaker/` bootstrapped project structure."""
    root_dir = pathlib.Path(context.repository_root)
    try:
        spec_dir = paths.specmaker_root(root_dir)
    except FileNotFoundError as exc:  # pragma: no cover - defensive branch
        msg = f"Repository root does not exist: {root_dir}"
        raise errors.ValidationError(msg) from exc

    spec_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Ensured SpecMaker directory at %s", spec_dir)

    _write_project_context(paths.project_context_path(root_dir), context)
    _write_manifest(paths.manifest_path(root_dir))
    _write_readme(paths.readme_path(root_dir), context)
    return context


def _write_project_context(path: pathlib.Path, context: shared.ProjectContext) -> None:
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
        "files": [str(paths.PROJECT_CONTEXT_FILENAME), str(paths.README_FILENAME)],
    }
    _safe_write(path, serialization.to_json(manifest))
    LOGGER.info("Wrote manifest to %s", path)


def _write_readme(path: pathlib.Path, context: shared.ProjectContext) -> None:
    """Write the README file for the project."""
    if path.exists():
        LOGGER.info("Skipped existing %s", path)
        return

    template_package = importlib.resources.files("specmaker_core._dependencies.templates")
    template_content = (template_package / "readme.jinja2").read_text(encoding="utf-8")
    template = jinja2.Template(template_content)

    rendered = template.render(context=context)
    _safe_write(path, rendered)
    LOGGER.info("Wrote README to %s", path)


def _safe_write(path: pathlib.Path, content: str) -> None:
    """Write content to a file, raising an error if the write fails."""
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:  # pragma: no cover - I/O failure
        msg = f"Failed to write {path}: {exc}"
        raise InitError(msg) from exc
