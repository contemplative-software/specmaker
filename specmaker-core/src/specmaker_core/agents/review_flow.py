"""Review flow orchestration helpers using the reviewer DBOS agent."""

from __future__ import annotations

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ModelMessage
from pydantic_ai.run import AgentRunResult

from specmaker_core._dependencies.schemas import documents as _documents
from specmaker_core.durable import event_stream_handler, get_dbos_reviewer


async def start_review(
    manuscript: _documents.Manuscript,
) -> AgentRunResult[_documents.ReviewReport | DeferredToolRequests]:
    """Start a durable review for the provided manuscript."""
    return await get_dbos_reviewer().run(
        _review_prompt(manuscript),
        event_stream_handler=event_stream_handler,
    )


async def resume_review(
    message_history: list[ModelMessage],
    results: DeferredToolResults,
) -> AgentRunResult[_documents.ReviewReport | DeferredToolRequests]:
    """Resume a deferred review run with collected approvals/results."""
    return await get_dbos_reviewer().run(
        "Resume manuscript review",
        message_history=message_history,
        deferred_tool_results=results,
        event_stream_handler=event_stream_handler,
    )


def _review_prompt(manuscript: _documents.Manuscript) -> str:
    header = f"Review manuscript: {manuscript.title}\n"
    return f"{header}\n{manuscript.content_markdown}".strip()
