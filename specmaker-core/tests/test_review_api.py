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
from specmaker_core.agents import reviewer as _reviewer
from specmaker_core.persistence import metadata as _metadata
from specmaker_core.persistence import storage as _storage
from specmaker_core.persistence.storage import open_db
from specmaker_core.review import Completed, Deferred, list_agents, resume, review
from specmaker_core.toolsets import persistence_tools as _persistence_tools

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


@pytest.mark.asyncio
async def test_extract_run_id_from_metadata_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _extract_run_id when run_id is in result.metadata dict."""
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    @dataclass
    class MetadataRunResult:
        output: Any
        _messages: list[Any]
        _timestamp: datetime.datetime
        metadata: dict[str, str]

        def all_messages(self) -> list[Any]:
            return list(self._messages)

        def timestamp(self) -> datetime.datetime:
            return self._timestamp

    timestamp = datetime.datetime.now(datetime.UTC)
    stub_result = MetadataRunResult(
        report,
        [],
        timestamp,
        {"run_id": "run-from-metadata"},
    )

    async def fake_start_review(arg: _documents.Manuscript) -> MetadataRunResult:
        await asyncio.sleep(0)
        return stub_result

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)

    outcome = await review(context, manuscript)
    assert isinstance(outcome, Completed)
    assert outcome.run_id == "run-from-metadata"


@pytest.mark.asyncio
async def test_review_propagates_start_review_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()

    class CustomError(Exception):
        pass

    async def fake_start_review_raises(arg: _documents.Manuscript) -> StubRunResult:
        await asyncio.sleep(0)
        raise CustomError("Start review failed")

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review_raises)

    with pytest.raises(CustomError, match="Start review failed"):
        await review(context, manuscript)


@pytest.mark.asyncio
async def test_resume_propagates_resume_review_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()

    token = review_module.RunToken(
        run_id="test-run",
        project_context=context,
        manuscript=manuscript,
        message_history=[],
        approvals_requested=0,
        approvals_granted=0,
    )

    class CustomError(Exception):
        pass

    async def fake_resume_review_raises(
        message_history: list[Any],
        results: DeferredToolResults,
    ) -> StubRunResult:
        await asyncio.sleep(0)
        raise CustomError("Resume review failed")

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_resume_review", fake_resume_review_raises)

    results = DeferredToolResults()
    with pytest.raises(CustomError, match="Resume review failed"):
        await resume(token, results)


@pytest.mark.asyncio
async def test_review_completed_handles_persistence_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    timestamp = datetime.datetime.now(datetime.UTC)
    stub_result = StubRunResult(report, "run-persist-fail", [], timestamp)

    async def fake_start_review(arg: _documents.Manuscript) -> StubRunResult:
        await asyncio.sleep(0)
        return stub_result

    def fake_save_review_record(connection: Any, metadata: Any) -> None:
        raise RuntimeError("Database write failed")

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)
    monkeypatch.setattr(review_module, "save_review_record", fake_save_review_record)

    with pytest.raises(RuntimeError, match="Database write failed"):
        await review(context, manuscript)


@pytest.mark.asyncio
async def test_result_to_outcome_generates_fallback_run_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    # StubRunResult without workflow_run_id attribute
    @dataclass
    class MinimalRunResult:
        output: Any
        _messages: list[Any]
        _timestamp: datetime.datetime

        def all_messages(self) -> list[Any]:
            return list(self._messages)

        def timestamp(self) -> datetime.datetime:
            return self._timestamp

    timestamp = datetime.datetime.now(datetime.UTC)
    stub_result = MinimalRunResult(report, [], timestamp)

    async def fake_start_review(arg: _documents.Manuscript) -> MinimalRunResult:
        await asyncio.sleep(0)
        return stub_result

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)

    outcome = await review(context, manuscript)
    assert isinstance(outcome, Completed)
    # Should have a run_id (uuid) even though result had none
    assert outcome.run_id is not None
    assert len(outcome.run_id) > 0


@pytest.mark.asyncio
async def test_result_to_outcome_generates_fallback_timestamp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    # StubRunResult without working timestamp method
    @dataclass
    class NoTimestampResult:
        output: Any
        workflow_run_id: str
        _messages: list[Any]

        def all_messages(self) -> list[Any]:
            return list(self._messages)

        def timestamp(self) -> None:
            return None

    stub_result = NoTimestampResult(report, "run-no-timestamp", [])

    async def fake_start_review(arg: _documents.Manuscript) -> NoTimestampResult:
        await asyncio.sleep(0)
        return stub_result

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)

    outcome = await review(context, manuscript)
    assert isinstance(outcome, Completed)
    # Should have a timestamp (current time) even though result had none
    assert outcome.timestamp is not None
    assert outcome.timestamp.tzinfo is not None


@pytest.mark.asyncio
async def test_persistence_distinct_runs_same_second_no_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two runs in the same second with different run_id should create two rows."""
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    # Same timestamp, different run IDs
    timestamp = datetime.datetime.now(datetime.UTC)
    stub_result_1 = StubRunResult(report, "run-first", [], timestamp)
    stub_result_2 = StubRunResult(report, "run-second", [], timestamp)

    call_count = 0

    async def fake_start_review(arg: _documents.Manuscript) -> StubRunResult:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)
        return stub_result_1 if call_count == 1 else stub_result_2

    monkeypatch.setattr(review_module, "launch_dbos", lambda: None)
    monkeypatch.setattr(review_module, "_start_review", fake_start_review)

    # First review
    outcome1 = await review(context, manuscript)
    assert isinstance(outcome1, Completed)
    assert outcome1.run_id == "run-first"

    # Second review with same timestamp
    outcome2 = await review(context, manuscript)
    assert isinstance(outcome2, Completed)
    assert outcome2.run_id == "run-second"

    # Verify both rows exist
    connection = open_db()
    try:
        cursor = connection.execute("SELECT COUNT(*) FROM review_records")
        count = cursor.fetchone()[0]
        cursor_runs = connection.execute("SELECT run_id FROM review_records ORDER BY run_id")
        run_ids = [row[0] for row in cursor_runs.fetchall()]
    finally:
        connection.close()

    assert count == 2
    assert run_ids == ["run-first", "run-second"]


def test_persistence_same_run_upsert_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-saving the same (project, version, run_id) should update, not duplicate."""
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    timestamp = datetime.datetime.now(datetime.UTC)
    version = _storage.version_stamp(timestamp)
    run_id = "run-upsert"

    # First save
    metadata1 = _metadata.ReviewMetadata(
        record_id="rec-1",
        project_context=context,
        manuscript=manuscript,
        review_report=report,
        run_id=run_id,
        agent_name="reviewer",
        version=version,
        created_at=timestamp,
        approvals_requested=2,
        approvals_granted=1,
    )

    connection = open_db()
    try:
        _persistence_tools.save_review_record(connection, metadata1)

        # Verify single row
        cursor = connection.execute("SELECT COUNT(*) FROM review_records")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor = connection.execute(
            "SELECT approvals_granted FROM review_records WHERE run_id=?", (run_id,)
        )
        initial_granted = cursor.fetchone()[0]
        assert initial_granted == 1

        # Second save with different approvals_granted
        metadata2 = _metadata.ReviewMetadata(
            record_id="rec-2",
            project_context=context,
            manuscript=manuscript,
            review_report=report,
            run_id=run_id,
            agent_name="reviewer",
            version=version,
            created_at=timestamp,
            approvals_requested=2,
            approvals_granted=2,
        )
        _persistence_tools.save_review_record(connection, metadata2)

        # Verify still single row with updated value
        cursor = connection.execute("SELECT COUNT(*) FROM review_records")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor = connection.execute(
            "SELECT approvals_granted FROM review_records WHERE run_id=?", (run_id,)
        )
        updated_granted = cursor.fetchone()[0]
        assert updated_granted == 2
    finally:
        connection.close()


def test_load_review_records_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test loading records from an empty database."""
    monkeypatch.chdir(tmp_path)
    connection = open_db()
    try:
        records = _persistence_tools.load_review_records(connection)
        assert records == []
    finally:
        connection.close()


def test_load_review_records_with_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test loading persisted review records."""
    monkeypatch.chdir(tmp_path)
    context = _project_context(tmp_path)
    manuscript = _manuscript()
    report = _report()

    timestamp = datetime.datetime.now(datetime.UTC)
    version = _storage.version_stamp(timestamp)
    run_id = "run-load-test"

    metadata = _metadata.ReviewMetadata(
        record_id="rec-load",
        project_context=context,
        manuscript=manuscript,
        review_report=report,
        run_id=run_id,
        agent_name="reviewer",
        version=version,
        created_at=timestamp,
        approvals_requested=0,
        approvals_granted=0,
    )

    connection = open_db()
    try:
        _persistence_tools.save_review_record(connection, metadata)

        # Load all records
        records = _persistence_tools.load_review_records(connection)
        assert len(records) == 1
        assert records[0].run_id == run_id
        assert records[0].project_context.project_name == context.project_name

        # Load filtered by project name
        records_filtered = _persistence_tools.load_review_records(
            connection, project_name=context.project_name
        )
        assert len(records_filtered) == 1
        assert records_filtered[0].run_id == run_id
    finally:
        connection.close()


def test_create_trivial_review() -> None:
    """Test the deterministic placeholder review generator."""
    manuscript = _manuscript()
    review_report = _reviewer.create_trivial_review(manuscript)

    assert review_report.status == "pass"
    assert manuscript.title in review_report.summary
    assert review_report.issues == []
    assert review_report.style_rules == manuscript.style_rules
    assert review_report.confidence_percent == 75.0


def test_request_approvals_when_approved() -> None:
    """Test request_approvals tool when ctx.tool_call_approved is True."""
    from unittest.mock import Mock

    from pydantic_ai import RunContext

    mock_ctx = Mock(spec=RunContext)
    mock_ctx.tool_call_approved = True

    result = _reviewer.request_approvals(mock_ctx, ["item1", "item2"])
    assert result == "Approved: item1, item2"

    # Test with empty list
    result_empty = _reviewer.request_approvals(mock_ctx, [])
    assert result_empty == "Approved: no specific items"


def test_request_approvals_when_not_approved() -> None:
    """Test request_approvals tool raises ApprovalRequired when not approved."""
    from unittest.mock import Mock

    from pydantic_ai import ApprovalRequired, RunContext

    mock_ctx = Mock(spec=RunContext)
    mock_ctx.tool_call_approved = False

    with pytest.raises(ApprovalRequired):
        _reviewer.request_approvals(mock_ctx, ["item1"])


def test_get_reviewer_lazy_initialization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_reviewer() returns an Agent and registers tools."""
    # Mock OpenAI API key to avoid requiring real credentials
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-testing")

    agent = _reviewer.get_reviewer()

    # Should return an Agent instance
    assert agent is not None
    assert agent.name == "reviewer"
    assert agent._instructions is not None

    # Calling again should return same instance
    agent2 = _reviewer.get_reviewer()
    assert agent is agent2
