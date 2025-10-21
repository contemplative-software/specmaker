"""Domain-specific exceptions for SpecMaker Core (validation, policy, and runtime errors)."""

from __future__ import annotations


class SpecMakerError(Exception):
    """Base exception for all SpecMaker-specific errors."""


class ValidationError(SpecMakerError):
    """Raised when incoming data fails validation rules."""


__all__ = ["SpecMakerError", "ValidationError"]
