"""Durable execution helpers shared across SpecMaker workflows."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterable
from typing import Any, Final

from pydantic_ai import AgentStreamEvent, RunContext
from pydantic_ai.durable_exec.dbos import DBOSAgent, StepConfig

from specmaker_core.agents.reviewer import REVIEWER_NAME, get_reviewer

LOGGER = logging.getLogger(__name__)

MODEL_STEP_CONFIG: Final[StepConfig] = StepConfig(max_attempts=3)
MCP_STEP_CONFIG: Final[StepConfig] = StepConfig(max_attempts=1)

_dbos_reviewer_instance: DBOSAgent[None, Any] | None = None


def get_dbos_reviewer() -> DBOSAgent[None, Any]:
    """Lazily instantiate and return the durable reviewer agent."""
    global _dbos_reviewer_instance
    if _dbos_reviewer_instance is None:
        _dbos_reviewer_instance = DBOSAgent(
            get_reviewer(),
            model_step_config=MODEL_STEP_CONFIG,
            mcp_step_config=MCP_STEP_CONFIG,
        )
    return _dbos_reviewer_instance


async def event_stream_handler(
    ctx: RunContext[Any],
    stream: AsyncIterable[AgentStreamEvent],
) -> None:
    """Log streaming events for visibility during durable runs."""
    agent_name = getattr(ctx, "agent_name", REVIEWER_NAME)
    async for event in stream:
        LOGGER.info("[%s] %s", agent_name, event)
