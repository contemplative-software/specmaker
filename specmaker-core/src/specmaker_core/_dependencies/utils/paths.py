"""Path utilities including SQLite path builders and temporary directories (pure logic)."""

from __future__ import annotations

from pathlib import Path

SPECMAKER_DIR_NAME = Path(".specmaker")
PROJECT_CONTEXT_FILENAME = Path("project_context.json")
README_FILENAME = Path("README.md")
MANIFEST_FILENAME = Path("manifest.json")


def ensure_repository_root(path: Path) -> Path:
    """Return the repository root as an absolute, resolved path."""
    if not path.exists():
        msg = f"Repository root does not exist: {path}"
        raise FileNotFoundError(msg)
    return path.resolve()


def specmaker_root(root: Path) -> Path:
    """Path to the project-local `.specmaker/` directory."""
    return ensure_repository_root(root) / SPECMAKER_DIR_NAME


def project_context_path(root: Path) -> Path:
    """Path to the `project_context.json` file inside `.specmaker/`."""
    return specmaker_root(root) / PROJECT_CONTEXT_FILENAME


def readme_path(root: Path) -> Path:
    """Path to the `.specmaker/README.md` file."""
    return specmaker_root(root) / README_FILENAME


def manifest_path(root: Path) -> Path:
    """Path to the `.specmaker/manifest.json` file."""
    return specmaker_root(root) / MANIFEST_FILENAME
