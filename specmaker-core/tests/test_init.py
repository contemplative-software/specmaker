from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from specmaker_core import ProjectContext, init


@pytest.fixture()
def project_context(tmp_path: Path) -> ProjectContext:
    return ProjectContext(
        project_name="Sample Project",
        repository_root=tmp_path,
        description="A sample project description.",
        audience=["engineers"],
        constraints=["No external network calls"],
        style_rules="google",
        created_by="test-user",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
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
