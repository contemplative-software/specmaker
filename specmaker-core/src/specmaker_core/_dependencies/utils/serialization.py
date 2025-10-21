"""Serialization helpers for JSON/MsgPack and canonical content hashing (no I/O)."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _default_serializer(value: Any) -> Any:
    """Convert unsupported types into JSON-friendly representations."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if is_dataclass(value):
        return asdict(value)  # type: ignore[arg-type]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    msg = f"Cannot serialize value of type {type(value)}"
    raise TypeError(msg)


def to_json(data: Any, *, indent: int = 2) -> str:
    """Serialize data to JSON with deterministic formatting."""
    return json.dumps(data, indent=indent, sort_keys=True, default=_default_serializer)
