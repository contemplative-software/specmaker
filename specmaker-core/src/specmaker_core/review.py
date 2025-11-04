"""Public review API exposing durable review and resume flows."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import uuid4

from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolApproved
from pydantic_ai.messages import ModelMessage
from pydantic_ai.run import AgentRunResult

from specmaker_core._dependencies.schemas import documents as _documents
from specmaker_core._dependencies.schemas import shared as _shared
from specmaker_core.agents.reviewer import REVIEWER_NAME
from specmaker_core.durable.dbos_boot import launch_dbos
from specmaker_core.durable.review_flow import resume_review as _resume_review
from specmaker_core.durable.review_flow import start_review as _start_review
from specmaker_core.persistence.metadata import build_review_metadata
from specmaker_core.persistence.storage import open_db, version_stamp
from specmaker_core.toolsets.persistence_tools import save_review_record

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RunToken:
    """Opaque token containing identifiers required to resume a deferred review."""

    run_id: str
    project_context: _shared.ProjectContext
    manuscript: _documents.Manuscript
    message_history: list[ModelMessage]
    approvals_requested: int = 0
    approvals_granted: int = 0


@dataclass(frozen=True)
class Completed(Generic[T]):  # noqa: UP046
    """Represents a completed durable review outcome with associated metadata."""

    value: T
    run_id: str
    message_history: list[ModelMessage]
    timestamp: datetime
    approvals_requested: int
    approvals_granted: int


@dataclass(frozen=True)
class Deferred(Generic[T]):  # noqa: UP046
    """Represents a review paused for external approvals or results."""

    requests: DeferredToolRequests
    token: RunToken


RunOutcome = Completed[T] | Deferred[T]


async def review(
    context: _shared.ProjectContext, manuscript: _documents.Manuscript
) -> RunOutcome[_documents.ReviewReport]:
    """Launch the reviewer agent and return a structured outcome."""
    launch_dbos()
    result = await _start_review(manuscript)
    return _result_to_outcome(
        context=context,
        manuscript=manuscript,
        result=result,
        prior_token=None,
        results=None,
    )


async def resume(
    token: RunToken, results: DeferredToolResults
) -> RunOutcome[_documents.ReviewReport]:
    """Resume a previously deferred review with collected results/approvals."""
    launch_dbos()
    result = await _resume_review(token.message_history, results)
    return _result_to_outcome(
        context=token.project_context,
        manuscript=token.manuscript,
        result=result,
        prior_token=token,
        results=results,
    )


def list_agents() -> list[str]:
    """Return the list of public agent identifiers exposed by SpecMaker Core."""
    return [REVIEWER_NAME]


def _result_to_outcome(
    *,
    context: _shared.ProjectContext,
    manuscript: _documents.Manuscript,
    result: AgentRunResult[_documents.ReviewReport | DeferredToolRequests],
    prior_token: RunToken | None,
    results: DeferredToolResults | None,
) -> RunOutcome[_documents.ReviewReport]:
    output = result.output
    messages = result.all_messages()
    approvals_requested = prior_token.approvals_requested if prior_token else 0
    approvals_granted = prior_token.approvals_granted if prior_token else 0
    if results is not None:
        approvals_granted += _count_approvals_granted(results)

    run_id = _extract_run_id(result) or (prior_token.run_id if prior_token else str(uuid4()))
    timestamp = _extract_timestamp(result)

    if isinstance(output, DeferredToolRequests):
        pending_approvals = len(output.approvals)
        updated_token = RunToken(
            run_id=run_id,
            project_context=context,
            manuscript=manuscript,
            message_history=messages,
            approvals_requested=approvals_requested + pending_approvals,
            approvals_granted=approvals_granted,
        )
        return Deferred(requests=output, token=updated_token)

    # Type narrowing ensures output is ReviewReport at this point
    completion = Completed(
        value=output,
        run_id=run_id,
        message_history=messages,
        timestamp=timestamp,
        approvals_requested=approvals_requested,
        approvals_granted=approvals_granted,
    )
    _persist_completion(context, manuscript, completion)
    return completion


def _extract_run_id(result: AgentRunResult[object]) -> str | None:
    candidates: Iterable[str | None] = (
        getattr(result, "workflow_run_id", None),
        getattr(result, "dbos_run_id", None),
        getattr(result, "run_id", None),
    )
    for value in candidates:
        if isinstance(value, str) and value:
            return value

    metadata = getattr(result, "metadata", None)
    if isinstance(metadata, dict):
        for key in ("workflow_run_id", "run_id", "dbos_run_id"):
            value = metadata.get(key)  # type: ignore[reportUnknownMemberType]
            if isinstance(value, str) and value:
                return value
    return None


def _extract_timestamp(result: AgentRunResult[object]) -> datetime:
    timestamp_method = getattr(result, "timestamp", None)
    if callable(timestamp_method):
        try:
            timestamp = timestamp_method()
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.debug("Failed to extract timestamp from run result", exc_info=True)
        else:
            if isinstance(timestamp, datetime):
                return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=UTC)
    return datetime.now(tz=UTC)


def _count_approvals_granted(results: DeferredToolResults) -> int:
    granted = 0
    for decision in results.approvals.values():
        if decision is True or isinstance(decision, ToolApproved):
            granted += 1
    return granted


def _persist_completion(
    context: _shared.ProjectContext,
    manuscript: _documents.Manuscript,
    completion: Completed[_documents.ReviewReport],
) -> None:
    connection = open_db()
    try:
        metadata = build_review_metadata(
            project_context=context,
            manuscript=manuscript,
            review_report=completion.value,
            run_id=completion.run_id,
            agent_name=REVIEWER_NAME,
            version=version_stamp(completion.timestamp),
            created_at=completion.timestamp,
            approvals_requested=completion.approvals_requested,
            approvals_granted=completion.approvals_granted,
        )
        save_review_record(connection, metadata)
    finally:
        connection.close()
