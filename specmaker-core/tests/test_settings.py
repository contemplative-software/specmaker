from __future__ import annotations

import os
from collections.abc import Generator

import pytest

from specmaker_core.config.settings import Settings, get_settings


@pytest.mark.usefixtures("clean_settings_env")
def test_settings_defaults(clean_settings_env: dict[str, str]) -> None:
    settings = Settings()

    assert settings.system_database_url == "sqlite:///specmaker.sqlite"
    assert settings.model_provider == "openai"
    assert settings.model_name == "gpt-4o"
    assert settings.reasoning_effort == "medium"
    assert settings.model_timeout == 120.0
    assert settings.step_timeout == 300.0
    assert settings.durable_retries_enabled is False


@pytest.mark.usefixtures("clean_settings_env")
def test_settings_environment_overrides(clean_settings_env: dict[str, str]) -> None:
    overrides = {
        "SYSTEM_DATABASE_URL": "postgresql://localhost/specmaker",
        "MODEL_PROVIDER": "anthropic",
        "MODEL_NAME": "claude-opus",
        "REASONING_EFFORT": "high",
        "MODEL_TIMEOUT": "240.5",
        "STEP_TIMEOUT": "600.0",
        "DURABLE_RETRIES_ENABLED": "true",
    }

    os.environ.update(overrides)

    settings = Settings()

    assert settings.system_database_url == overrides["SYSTEM_DATABASE_URL"]
    assert settings.model_provider == overrides["MODEL_PROVIDER"]
    assert settings.model_name == overrides["MODEL_NAME"]
    assert settings.reasoning_effort == overrides["REASONING_EFFORT"]
    assert settings.model_timeout == pytest.approx(float(overrides["MODEL_TIMEOUT"]))
    assert settings.step_timeout == pytest.approx(float(overrides["STEP_TIMEOUT"]))
    assert settings.durable_retries_enabled is True


@pytest.fixture()
def clean_settings_env(monkeypatch: pytest.MonkeyPatch) -> Generator[dict[str, str]]:
    initial_keys = {
        "SYSTEM_DATABASE_URL",
        "MODEL_PROVIDER",
        "MODEL_NAME",
        "REASONING_EFFORT",
        "MODEL_TIMEOUT",
        "STEP_TIMEOUT",
        "DURABLE_RETRIES_ENABLED",
    }

    removed: dict[str, str] = {}
    for key in initial_keys:
        if key in os.environ:
            removed[key] = os.environ.pop(key)

    yield removed

    for key, value in removed.items():
        os.environ[key] = value


def test_get_settings_returns_settings_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROVIDER", "openrouter")

    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.model_provider == "openrouter"
