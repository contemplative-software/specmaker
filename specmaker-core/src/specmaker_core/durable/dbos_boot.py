"""DBOS bootstrap utilities for configuring durable execution.

This module centralizes the DBOS bootstrap logic so it can be reused by CLI
entrypoints, scripts, and tests. By default the bootstrap resolves
configuration via :class:`specmaker_core.config.settings.Settings` which keeps
the DB URL aligned with the application defaults (.specmaker/specmaker.db).
"""

from __future__ import annotations

import logging
from typing import Final

from dbos import DBOS, DBOSConfig

from specmaker_core.config.settings import Settings, get_settings

LOGGER = logging.getLogger(__name__)

DBOS_APP_NAME: Final[str] = "specmaker_core"


def build_dbos_config(settings: Settings) -> DBOSConfig:
    """Return the DBOS configuration derived from the provided settings."""
    return {
        "name": DBOS_APP_NAME,
        "system_database_url": settings.system_database_url,
    }


def launch_dbos(settings: Settings | None = None) -> None:
    """Initialise DBOS with the configured SQLite URL and launch it.

    Args:
        settings: Optional settings instance. When not provided the cached
            application settings are used via :func:`get_settings`.
    """
    effective_settings = settings or get_settings()
    config = build_dbos_config(effective_settings)

    # Extract values for logging to avoid TypedDict optional key access issues
    dbos_name = config.get("name", DBOS_APP_NAME)
    database_url = config.get("system_database_url", effective_settings.system_database_url)

    LOGGER.debug(
        "Launching DBOS",
        extra={"dbos_name": dbos_name, "database_url": database_url},
    )

    DBOS(config=config)
    DBOS.launch()
