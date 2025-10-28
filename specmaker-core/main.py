"""Entry point for running SpecMaker Core init flow as a script."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from specmaker_core import ProjectContext, init


def main() -> None:
    """Initialize the current repository with default context values."""
    context = ProjectContext(
        project_name=Path.cwd().name,
        repository_root=Path.cwd(),
        description="Initialized via specmaker_core.main",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="specmaker-core",
        created_at=datetime.now(UTC),
    )
    init(context)


if __name__ == "__main__":  # pragma: no cover
    main()
