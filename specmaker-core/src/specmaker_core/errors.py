"""Public error types re-exported for consumers (e.g., SpecMakerError)."""

from specmaker_core._dependencies.errors import SpecMakerError, ValidationError

__all__ = [
    "SpecMakerError",
    "ValidationError",
]
