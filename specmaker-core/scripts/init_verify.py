"""Verification script for the SpecMaker init command."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core.init import init


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the init verification script."""
    parser = argparse.ArgumentParser(description="Initialize SpecMaker project structure")
    parser.add_argument(
        "--root-dir",
        dest="root_dir",
        help="Path to the repository root. Defaults to current directory.",
        default=None,
    )
    parser.add_argument(
        "--project-name",
        dest="project_name",
        help="Name of the project. Defaults to directory name.",
        default=None,
    )
    parser.add_argument(
        "--description",
        dest="description",
        help="Project description.",
        default="Verification run for specmaker init",
    )
    parser.add_argument(
        "--audience",
        dest="audience",
        help="Comma-separated list of audience members.",
        default="engineers",
    )
    parser.add_argument(
        "--style-rules",
        dest="style_rules",
        help="Style rules to apply.",
        default="google",
    )
    parser.add_argument(
        "--created-by",
        dest="created_by",
        help="Name of creator.",
        default="init-verify-script",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Entrypoint for the init verification script."""
    args = parse_args(argv)

    root = Path(args.root_dir).resolve() if args.root_dir else Path.cwd()
    project_name = args.project_name if args.project_name else root.name
    audience = [a.strip() for a in args.audience.split(",")]

    context = ProjectContext(
        project_name=project_name,
        repository_root=root,
        description=args.description,
        audience=audience,
        constraints=[],
        style_rules=args.style_rules,
        created_by=args.created_by,
        created_at=datetime.now(UTC),
    )
    init(context)


if __name__ == "__main__":  # pragma: no cover
    main()
