from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from specmaker_core._dependencies.utils.serialization import to_json


class ExampleModel(BaseModel):
    value: int
    label: str
    timestamp: datetime


@dataclass
class ExampleDataclass:
    value: int
    flag: bool


def _round_trip(data: Any) -> Any:
    """Serialize data with to_json and deserialize using json.loads."""
    serialized = to_json(data)
    return json.loads(serialized)


def test_to_json_handles_supported_types() -> None:
    expected_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    model = ExampleModel(value=1, label="sample", timestamp=expected_timestamp)
    dataclass_instance = ExampleDataclass(value=2, flag=True)
    sample_path = Path("/tmp/specmaker")

    data = {
        "model": model,
        "dataclass": dataclass_instance,
        "path": sample_path,
        "timestamp": expected_timestamp,
        "plain": {"nested": [1, 2, 3]},
    }

    round_tripped = _round_trip(data)

    assert round_tripped["model"] == {
        "value": 1,
        "label": "sample",
        "timestamp": expected_timestamp.isoformat(),
    }
    assert round_tripped["dataclass"] == {"value": 2, "flag": True}
    assert round_tripped["path"] == str(sample_path)
    assert round_tripped["timestamp"] == expected_timestamp.isoformat()
    assert round_tripped["plain"] == {"nested": [1, 2, 3]}


def test_to_json_raises_type_error_for_unknown_type() -> None:
    with pytest.raises(TypeError, match="Cannot serialize value of type <class 'complex'>"):
        to_json({"value": complex(1, 2)})
