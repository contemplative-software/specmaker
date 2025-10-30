from __future__ import annotations

import datetime
import pathlib

import pytest

from specmaker_core._dependencies.errors import ValidationError
from specmaker_core._dependencies.schemas.shared import ProjectContext
from specmaker_core._dependencies.utils.paths import project_context_path
from specmaker_core.init import init


@pytest.fixture()
def project_context(tmp_path: pathlib.Path) -> ProjectContext:
    return ProjectContext(
        project_name="Sample Project",
        repository_root=tmp_path,
        description="A sample project description.",
        audience=["engineers"],
        constraints=["No external network calls"],
        style_rules="google",
        created_by="test-user",
        created_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
    )


def test_init_creates_specmaker_directory(project_context: ProjectContext) -> None:
    init(project_context)
    spec_dir = project_context.repository_root / ".specmaker"
    assert spec_dir.exists()


def test_init_creates_files(project_context: ProjectContext) -> None:
    init(project_context)
    spec_dir = project_context.repository_root / ".specmaker"
    assert (spec_dir / "project_context.json").exists()
    assert (spec_dir / "README.md").exists()
    assert (spec_dir / "manifest.json").exists()


def test_idempotent_init(project_context: ProjectContext) -> None:
    init(project_context)
    manifest_path = project_context.repository_root / ".specmaker" / "manifest.json"
    content = manifest_path.read_text(encoding="utf-8")
    init(project_context)
    assert manifest_path.read_text(encoding="utf-8") == content


def test_invalid_repository_root_raises_validation_error(tmp_path: pathlib.Path) -> None:
    non_existent = tmp_path / "missing-root"
    context = ProjectContext(
        project_name="X",
        repository_root=non_existent,
        description="d",
        audience=[],
        constraints=[],
        style_rules="google",
        created_by="u",
        created_at=datetime.datetime(2024, 1, 1, 0, 0, 0),
    )
    with pytest.raises(ValidationError):
        init(context)


def test_project_context_json_round_trip(project_context: ProjectContext) -> None:
    init(project_context)
    json_path = project_context_path(project_context.repository_root)
    data = json_path.read_text(encoding="utf-8")
    # Pydantic can parse from JSON directly via model_validate_json
    parsed = ProjectContext.model_validate_json(data)
    assert parsed == project_context


@pytest.mark.skip(reason="Read-only filesystem edge case not feasible in CI")
def test_read_only_path_edge_case(tmp_path: pathlib.Path) -> None:
    # Simulate read-only by pointing into a path we cannot create (skipped)
    read_only_root = pathlib.Path("/root/does-not-exist")
    context = ProjectContext(
        project_name="X",
        repository_root=read_only_root,
        description="d",
        audience=[],
        constraints=[],
        style_rules="google",
        created_by="u",
        created_at=datetime.datetime(2024, 1, 1, 0, 0, 0),
    )
    with pytest.raises(ValidationError):
        init(context)
