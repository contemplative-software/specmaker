"""Reviewer agent configuration and helper utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import jinja2
from pydantic_ai import Agent, ApprovalRequired, DeferredToolRequests, RunContext

from specmaker_core._dependencies.schemas import documents as _documents

DEFAULT_REVIEWER_MODEL: Final[str] = "openai:gpt-5"
REVIEWER_NAME: Final[str] = "reviewer"


def _load_reviewer_instructions() -> str:
    """Load and render the reviewer agent instructions from the template."""
    template_dir = Path(__file__).parents[1] / "_dependencies" / "templates"
    template_path = template_dir / "reviewer.jinja2"
    template_content = template_path.read_text(encoding="utf-8")
    template = jinja2.Template(template_content)
    return template.render().strip()


_reviewer_instance: Agent[None, _documents.ReviewReport | DeferredToolRequests] | None = None


def get_reviewer() -> Agent[None, _documents.ReviewReport | DeferredToolRequests]:
    """Lazily instantiate and return the reviewer agent to avoid side effects on import."""
    global _reviewer_instance
    if _reviewer_instance is None:
        _reviewer_instance = Agent(
            DEFAULT_REVIEWER_MODEL,
            name=REVIEWER_NAME,
            instructions=_load_reviewer_instructions(),
            output_type=[_documents.ReviewReport, DeferredToolRequests],
        )
        _reviewer_instance.tool(request_approvals)
    return _reviewer_instance


def request_approvals(ctx: RunContext[None], items: list[str]) -> str:
    """Collect approval decisions in a single batch for deferred review flow."""
    if not ctx.tool_call_approved:
        raise ApprovalRequired
    approved = ", ".join(items) if items else "no specific items"
    return f"Approved: {approved}"


def create_trivial_review(manuscript: _documents.Manuscript) -> _documents.ReviewReport:
    """Return a deterministic placeholder review for environments without a model."""
    summary = (
        "Automated placeholder review for manuscript titled"
        f" '{manuscript.title}'. No issues were detected."
    )
    return _documents.ReviewReport(
        status="pass",
        summary=summary,
        issues=[],
        style_rules=manuscript.style_rules,
        confidence_percent=75.0,
    )
