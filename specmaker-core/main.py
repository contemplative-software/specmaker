"""Entry point for running SpecMaker Core init flow as a script."""

from __future__ import annotations

import datetime
import pathlib

from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core.init import init


def main() -> None:
    """Initialize the current repository with default context values."""
    context = ProjectContext(
        project_name=pathlib.Path.cwd().name,
        repository_root=pathlib.Path.cwd(),
        description="Initialized via specmaker_core.main",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="specmaker-core",
        created_at=datetime.datetime.now(datetime.UTC),
    )
    init(context)


if __name__ == "__main__":  # pragma: no cover
    main()
