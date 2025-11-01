from __future__ import annotations

import asyncio
import datetime
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart

from specmaker_core._dependencies.schemas import documents as _documents
from specmaker_core._dependencies.schemas import shared as _shared
from specmaker_core.persistence.storage import open_db
from specmaker_core.review import Completed, Deferred, list_agents, resume, review

review_module = importlib.import_module("specmaker_core.review")


@dataclass
class StubRunResult:
    output: Any
    workflow_run_id: str
    _messages: list[Any]
    _timestamp: datetime.datetime

    def all_messages(self) -> list[Any]:
        return list(self._messages)

    def timestamp(self) -> datetime.datetime:
        return self._timestamp


def _project_context(tmp_path: Path) -> _shared.ProjectContext:
    return _shared.ProjectContext(
        project_name="spec",
        repository_root=tmp_path,
        description="Test context",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="pytest",
        created_at=datetime.datetime.now(datetime.UTC),
    )


def _manuscript() -> _documents.Manuscript:
    return _documents.Manuscript(title="Sample", content_markdown="# Heading", style_rules="google")


def _report() -> _documents.ReviewReport:
    return _documents.ReviewReport(
        status="pass",
        summary="Looks good",
        issues=[],
        style_rules="google",
        confidence_percent=90.0,
    )


@pytest.mark.asyncio
async def test_review_completed_persists_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    timestamp = datetime.datetime.now(datetime.UTC)
    stub_result = StubRunResult(report, "run-completed", [], timestamp)

    async def fake_start_review(arg: _documents.Manuscript) -> StubRunResult:
        assert arg == manuscript
        await asyncio.sleep(0)
        return stub_result

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)

    outcome = await review(context, manuscript)
    assert isinstance(outcome, Completed)
    assert outcome.value == report

    connection = open_db()
    try:
        cursor = connection.execute("SELECT COUNT(*) FROM review_records")
        count = cursor.fetchone()[0]
    finally:
        connection.close()
    assert count == 1


@pytest.mark.asyncio
async def test_review_deferred_resume_roundtrip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()

    requests = DeferredToolRequests(
        calls=[],
        approvals=[
            ToolCallPart(
                tool_name="request_approvals",
                args={"items": ["a"]},
                tool_call_id="call-1",
            ),
            ToolCallPart(
                tool_name="request_approvals",
                args={"items": ["b"]},
                tool_call_id="call-2",
            ),
        ],
    )

    initial_result = StubRunResult(
        requests,
        "run-deferred",
        [],
        datetime.datetime.now(datetime.UTC),
    )
    final_report = _report()
    final_result = StubRunResult(
        final_report,
        "run-deferred",
        [],
        datetime.datetime.now(datetime.UTC),
    )

    async def fake_start_review(arg: _documents.Manuscript) -> StubRunResult:
        assert arg == manuscript
        await asyncio.sleep(0)
        return initial_result

    async def fake_resume_review(
        message_history: list[Any],
        results: DeferredToolResults,
    ) -> StubRunResult:
        assert results.approvals["call-1"] is True
        assert results.approvals["call-2"] is False
        assert message_history == []
        await asyncio.sleep(0)
        return final_result

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)
    monkeypatch.setattr(review_module, "_resume_review", fake_resume_review)

    outcome = await review(context, manuscript)
    assert isinstance(outcome, Deferred)
    assert outcome.token.approvals_requested == 2

    results = DeferredToolResults()
    results.approvals["call-1"] = True
    results.approvals["call-2"] = False

    completed = await resume(outcome.token, results)
    assert isinstance(completed, Completed)
    assert completed.approvals_requested == 2
    assert completed.approvals_granted == 1

    connection = open_db()
    try:
        cursor = connection.execute("SELECT COUNT(*) FROM review_records")
        count = cursor.fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_list_agents_includes_reviewer() -> None:
    agents = list_agents()
    assert "reviewer" in agents
