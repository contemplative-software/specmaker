"""Manual validation script for the durable review workflow."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic_ai import DeferredToolRequests, DeferredToolResults

from specmaker_core import (
    Completed,
    Deferred,
    Manuscript,
    ProjectContext,
    ReviewReport,
    list_agents,
    resume,
    review,
)
from specmaker_core._dependencies.utils import paths

LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the review validation script."""
    parser = argparse.ArgumentParser(description="Run the reviewer agent manually")
    parser.add_argument(
        "--path",
        dest="path",
        help="Path to a manuscript markdown file. Falls back to STDIN when omitted.",
        default=None,
    )
    parser.add_argument(
        "--title",
        dest="title",
        help="Override manuscript title (defaults to filename or 'Manual Input').",
        default=None,
    )
    parser.add_argument(
        "--root",
        dest="root",
        help="Repository root directory. If omitted, auto-discovered from current directory.",
        default=None,
    )
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> None:
    """Execute the validation flow using parsed CLI arguments."""
    root = _resolve_project_root(args.root)
    context = _load_project_context(root)
    markdown = _read_input(args.path)
    title = _resolve_title(args.title, args.path)
    manuscript = Manuscript(title=title, content_markdown=markdown, style_rules=context.style_rules)

    LOGGER.info("Available agents: %s", ", ".join(list_agents()))
    outcome = await review(context, manuscript)
    completed = await _resolve_deferred(outcome, collect_single_batch_approvals)

    print(completed.value.model_dump_json(indent=2))


def main(argv: Sequence[str] | None = None) -> None:
    """Entrypoint for the review validation script."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args(argv)
    asyncio.run(run(args))


async def _resolve_deferred(
    outcome: Deferred[ReviewReport] | Completed[ReviewReport],
    collector: Callable[[DeferredToolRequests], DeferredToolResults],
) -> Completed[ReviewReport]:
    """Handle deferred review outcomes until completion."""
    current: Deferred[ReviewReport] | Completed[ReviewReport] = outcome
    while isinstance(current, Deferred):
        LOGGER.info("Review deferred awaiting %d approvals", len(current.requests.approvals))
        results = collector(current.requests)
        current = await resume(current.token, results)
    return current


def collect_single_batch_approvals(requests: DeferredToolRequests) -> DeferredToolResults:
    """Prompt the user once to approve or deny deferred tool calls."""
    results = DeferredToolResults()
    for approval in requests.approvals:
        args_json = json.dumps(approval.args, indent=2)
        prompt = (
            "Approve tool call\n"
            f"Tool: {approval.tool_name}\n"
            f"Args: {args_json}\n"
            "Respond with [y/N]: "
        )
        decision = input(prompt).strip().lower()
        results.approvals[approval.tool_call_id] = decision in {"y", "yes"}
    return results


def _read_input(path: str | None) -> str:
    """Read manuscript markdown from a file path or STDIN."""
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _resolve_title(override: str | None, path: str | None) -> str:
    """Derive the manuscript title from CLI inputs."""
    if override:
        return override
    if path:
        return Path(path).stem
    return "Manual Input"


def _discover_project_root() -> Path:
    """Walk upward from current directory to find project root with .specmaker directory."""
    current = Path.cwd().resolve()
    project_context_file = paths.SPECMAKER_DIR_NAME / paths.PROJECT_CONTEXT_FILENAME

    # Walk up the directory tree looking for .specmaker/project_context.json
    for directory in [current, *current.parents]:
        specmaker_dir = directory / paths.SPECMAKER_DIR_NAME
        context_file = directory / project_context_file
        if specmaker_dir.is_dir() and context_file.is_file():
            return directory

    msg = (
        "Could not locate project root. "
        "Please run this script from within a SpecMaker-initialized project directory, "
        "or use --root to specify the repository root directory. "
        "The script looks for a '.specmaker/project_context.json' file by walking up "
        "from the current directory."
    )
    raise FileNotFoundError(msg)


def _resolve_project_root(root_arg: str | None) -> Path:
    """Resolve project root from CLI argument or discovery."""
    if root_arg:
        root_path = Path(root_arg)
        return paths.ensure_repository_root(root_path)
    return _discover_project_root()


def _load_project_context(root: Path) -> ProjectContext:
    """Load the project context document from the `.specmaker` directory."""
    context_path = paths.project_context_path(root)
    raw = context_path.read_text(encoding="utf-8")
    return ProjectContext.model_validate_json(raw)


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
