"""Entry point for running SpecMaker Core init flow as a script."""

from __future__ import annotations

import datetime
import pathlib

import specmaker_core._dependencies.schemas.shared as shared
import specmaker_core.init as init_module


def main() -> None:
    """Initialize the current repository with default context values."""
    context = shared.ProjectContext(
        project_name=pathlib.Path.cwd().name,
        repository_root=pathlib.Path.cwd(),
        description="Initialized via specmaker_core.main",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="specmaker-core",
        created_at=datetime.datetime.now(datetime.UTC),
    )
    init_module.init(context)


if __name__ == "__main__":  # pragma: no cover
    main()
