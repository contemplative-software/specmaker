from __future__ import annotations

import asyncio
import datetime
import io
import json
from pathlib import Path

import pytest
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart

from specmaker_core import Completed, Deferred, Manuscript, ProjectContext, ReviewReport, RunToken
from specmaker_core.scripts import review_validation


def _write_context(tmp_path: Path) -> ProjectContext:
    context = ProjectContext(
        project_name="spec",
        repository_root=tmp_path,
        description="Test context",
        audience=["engineers"],
        constraints=[],
        style_rules="google",
        created_by="pytest",
        created_at=datetime.datetime.now(datetime.UTC),
    )
    spec_dir = tmp_path / ".specmaker"
    spec_dir.mkdir(parents=True, exist_ok=True)
    context_json = context.model_dump_json(indent=2)
    (spec_dir / "project_context.json").write_text(context_json, encoding="utf-8")
    return context


def _completed(report: ReviewReport) -> Completed[ReviewReport]:
    return Completed(
        value=report,
        run_id="run-script",
        message_history=[],
        timestamp=datetime.datetime.now(datetime.UTC),
        approvals_requested=0,
        approvals_granted=0,
    )


@pytest.mark.asyncio
async def test_run_uses_path_when_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_context(tmp_path)

    manuscript_path = tmp_path / "doc.md"
    manuscript_path.write_text("# Path Content", encoding="utf-8")

    report = ReviewReport(
        status="pass",
        summary="Looks good",
        issues=[],
        style_rules="google",
        confidence_percent=95.0,
    )

    async def fake_review(
        context: ProjectContext,
        manuscript: Manuscript,
    ) -> Completed[ReviewReport]:
        assert isinstance(manuscript, Manuscript)
        assert manuscript.content_markdown == "# Path Content"
        await asyncio.sleep(0)
        return _completed(report)

    monkeypatch.setattr(review_validation, "review", fake_review)
    args = review_validation.parse_args(["--path", str(manuscript_path)])
    await review_validation.run(args)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == json.loads(report.model_dump_json())


@pytest.mark.asyncio
async def test_run_falls_back_to_stdin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_context(tmp_path)

    stdin_content = "# From STDIN"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_content))

    report = ReviewReport(
        status="pass",
        summary="From stdin",
        issues=[],
        style_rules="google",
        confidence_percent=80.0,
    )

    async def fake_review(
        context: ProjectContext,
        manuscript: Manuscript,
    ) -> Completed[ReviewReport]:
        assert manuscript.content_markdown == stdin_content
        await asyncio.sleep(0)
        return _completed(report)

    monkeypatch.setattr(review_validation, "review", fake_review)
    args = review_validation.parse_args([])
    await review_validation.run(args)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == json.loads(report.model_dump_json())


@pytest.mark.asyncio
async def test_run_handles_deferred_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    context = _write_context(tmp_path)

    report = ReviewReport(
        status="pass",
        summary="Deferred",
        issues=[],
        style_rules="google",
        confidence_percent=75.0,
    )

    requests = DeferredToolRequests(
        calls=[],
        approvals=[
            ToolCallPart(
                tool_name="request_approvals",
                args={},
                tool_call_id="approval-1",
            )
        ],
    )

    token = RunToken(
        run_id="run-deferred",
        project_context=context,
        manuscript=Manuscript(
            title="Manual Input",
            content_markdown="# deferred",
            style_rules="google",
        ),
        message_history=[],
        approvals_requested=len(requests.approvals),
    )

    async def fake_review(
        context_arg: ProjectContext,
        manuscript: Manuscript,
    ) -> Deferred[ReviewReport]:
        await asyncio.sleep(0)
        return Deferred(requests=requests, token=token)

    async def fake_resume(
        resume_token: RunToken,
        results: DeferredToolResults,
    ) -> Completed[ReviewReport]:
        assert resume_token is token
        assert results.approvals["approval-1"] is True
        await asyncio.sleep(0)
        return _completed(report)

    def fake_collect(reqs: DeferredToolRequests) -> DeferredToolResults:
        assert reqs is requests
        aggregated = DeferredToolResults()
        aggregated.approvals["approval-1"] = True
        return aggregated

    monkeypatch.setattr(review_validation, "review", fake_review)
    monkeypatch.setattr(review_validation, "resume", fake_resume)
    monkeypatch.setattr(review_validation, "collect_single_batch_approvals", fake_collect)

    args = review_validation.parse_args([])
    monkeypatch.setattr("sys.stdin", io.StringIO("# deferred"))
    await review_validation.run(args)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == json.loads(report.model_dump_json())
