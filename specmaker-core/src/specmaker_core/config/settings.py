"""Typed runtime settings surface (DB paths, model keys, timeouts) consumed by runtime.

Using Pydantic Settings for centralized environment variable management.
All environment variables should be accessed through this module only.
"""

import functools

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    """Runtime configuration loaded from environment variables.

    This is the single source of truth for all environment-driven configuration
    across the SpecMaker system. All code accessing environment variables should
    use this Settings instance rather than directly accessing os.environ.
    """

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables not defined in model
    )

    system_database_url: str = pydantic.Field(
        default="sqlite:///specmaker.sqlite",
        description="SQLite database URL for DBOS durability",
    )
    model_provider: str = pydantic.Field(
        default="openai",
        description="LLM provider key",
    )
    model_name_fallback: str = pydantic.Field(
        default="gpt-5",
        description="Fallback model identifier used when not specified per agent",
    )
    reasoning_effort_fallback: str = pydantic.Field(
        default="medium",
        description="Fallback reasoning effort for thinking models when not specified per agent",
    )
    model_timeout: float = pydantic.Field(
        default=120.0,
        description="Model API call timeout in seconds",
    )
    step_timeout: float = pydantic.Field(
        default=300.0,
        description="DBOS step execution timeout in seconds",
    )
    durable_retries_enabled: bool = pydantic.Field(
        default=False,
        description="Enable DBOS-managed automatic step retries",
    )


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached global Settings instance.

    Returns:
        Configured Settings instance with environment variables loaded.
    """
    return Settings()
