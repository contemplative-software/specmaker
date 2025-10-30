from __future__ import annotations

import pytest

import specmaker_core.config.settings as settings


def test_get_settings_returns_cached_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_settings() caches Settings and ignores env changes after first call."""
    # Ensure clean cache before test run
    if hasattr(settings.get_settings, "cache_clear"):
        settings.get_settings.cache_clear()  # type: ignore[attr-defined]

    # Set initial env and fetch settings
    monkeypatch.setenv("MODEL_PROVIDER", "testprovider")
    first = settings.get_settings()
    second = settings.get_settings()

    # Verify same instance returned (caching works)
    assert first is second
    assert isinstance(first, settings.Settings)
    assert first.model_provider == "testprovider"

    # Change env var; cached instance should remain unchanged (critical behavior)
    monkeypatch.setenv("MODEL_PROVIDER", "changedprovider")
    third = settings.get_settings()

    assert third is first
    assert third.model_provider == "testprovider"

    # Clean up cache to avoid cross-test interference
    if hasattr(settings.get_settings, "cache_clear"):
        settings.get_settings.cache_clear()  # type: ignore[attr-defined]
