"""Typed runtime settings surface (DB paths, model keys, timeouts) consumed by runtime.

Using Pydantic Settings for centralized environment variable management.
All environment variables should be accessed through this module only.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables.

    This is the single source of truth for all environment-driven configuration
    across the SpecMaker system. All code accessing environment variables should
    use this Settings instance rather than directly accessing os.environ.

    Attributes:
        system_database_url: SQLite path for DBOS state persistence
          (default: sqlite:///specmaker.sqlite).
        model_provider: LLM provider key (e.g., 'openai', 'anthropic').
        model_name: Default model identifier (e.g., 'gpt-4', 'claude-opus').
        reasoning_effort: Reasoning level for models supporting extended thinking
          (e.g., 'low', 'medium', 'high').
        model_timeout: Timeout in seconds for model API calls (default: 120.0).
        step_timeout: Timeout in seconds for DBOS step execution (default: 300.0).
        durable_retries_enabled: Whether DBOS-managed automatic retries are active
          (default: False; DBOS handles retries when enabled).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    system_database_url: str = Field(
        default="sqlite:///specmaker.sqlite",
        description="SQLite database URL for DBOS durability",
    )
    model_provider: str = Field(
        default="openai",
        description="LLM provider key",
    )
    model_name: str = Field(
        default="gpt-4o",
        description="Default model identifier",
    )
    reasoning_effort: str = Field(
        default="medium",
        description="Reasoning effort level for extended thinking models",
    )
    model_timeout: float = Field(
        default=120.0,
        description="Model API call timeout in seconds",
    )
    step_timeout: float = Field(
        default=300.0,
        description="DBOS step execution timeout in seconds",
    )
    durable_retries_enabled: bool = Field(
        default=False,
        description="Enable DBOS-managed automatic step retries",
    )


def get_settings() -> Settings:
    """Return the global Settings instance.

    Returns:
        Configured Settings instance with environment variables loaded.
    """
    return Settings()
