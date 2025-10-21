"""Verification script for the SpecMaker init command."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from specmaker_core import ProjectContext, init


def main() -> None:
    root = Path.cwd()
    context = ProjectContext(
        project_name=root.name,
        repository_root=root,
        description="Verification run for specmaker init",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="init-verify-script",
        created_at=datetime.utcnow(),
    )
    init(context)


if __name__ == "__main__":  # pragma: no cover
    main()

