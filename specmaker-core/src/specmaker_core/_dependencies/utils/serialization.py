"""Serialization helpers for JSON/MsgPack and canonical content hashing (no I/O)."""

from __future__ import annotations

import dataclasses
import datetime
import json
import pathlib
import typing

import pydantic


def _default_serializer(value: typing.Any) -> typing.Any:
    """Convert unsupported types into JSON-friendly representations."""
    if isinstance(value, pydantic.BaseModel):
        return value.model_dump(mode="python")
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)  # type: ignore[arg-type]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    msg = f"Cannot serialize value of type {type(value)}"
    raise TypeError(msg)


def to_json(data: typing.Any, *, indent: int = 2) -> str:
    """Serialize data to JSON with deterministic formatting."""
    return json.dumps(data, indent=indent, sort_keys=True, default=_default_serializer)
