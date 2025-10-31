"""Reviewer agent configuration and helper utilities."""

from __future__ import annotations

from typing import Final

from pydantic_ai import Agent, ApprovalRequired, DeferredToolRequests, RunContext

from specmaker_core.contracts.documents import Manuscript, ReviewReport

DEFAULT_REVIEWER_MODEL: Final[str] = "openai:gpt-5"
REVIEWER_NAME: Final[str] = "reviewer"

REVIEWER_INSTRUCTIONS: Final[str] = (
    "You are a meticulous technical reviewer."
    " Provide concise written feedback with clear findings,"
    " structured severity, and actionable recommendations."
)

_reviewer_instance: Agent[None, ReviewReport | DeferredToolRequests] | None = None


def get_reviewer() -> Agent[None, ReviewReport | DeferredToolRequests]:
    """Lazily instantiate and return the reviewer agent to avoid side effects on import."""
    global _reviewer_instance
    if _reviewer_instance is None:
        _reviewer_instance = Agent(
            DEFAULT_REVIEWER_MODEL,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
            output_type=[ReviewReport, DeferredToolRequests],
        )
        _reviewer_instance.tool(request_approvals)
    return _reviewer_instance


def request_approvals(ctx: RunContext[None], items: list[str]) -> str:
    """Collect approval decisions in a single batch for deferred review flow."""
    if not ctx.tool_call_approved:
        raise ApprovalRequired
    approved = ", ".join(items) if items else "no specific items"
    return f"Approved: {approved}"


def create_trivial_review(manuscript: Manuscript) -> ReviewReport:
    """Return a deterministic placeholder review for environments without a model."""
    summary = (
        "Automated placeholder review for manuscript titled"
        f" '{manuscript.title}'. No issues were detected."
    )
    return ReviewReport(
        status="pass",
        summary=summary,
        issues=[],
        style_rules=manuscript.style_rules,
        confidence_percent=75.0,
    )


__all__ = ["DEFAULT_REVIEWER_MODEL", "REVIEWER_NAME", "create_trivial_review", "get_reviewer"]
