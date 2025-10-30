from __future__ import annotations

import dataclasses
import datetime
import json
import pathlib
import typing

import pydantic
import pytest

import specmaker_core._dependencies.utils.serialization as serialization


class ExampleModel(pydantic.BaseModel):
    value: int
    label: str
    timestamp: datetime.datetime


@dataclasses.dataclass
class ExampleDataclass:
    value: int
    flag: bool


def _round_trip(data: typing.Any) -> typing.Any:
    """Serialize data with to_json and deserialize using json.loads."""
    serialized = serialization.to_json(data)
    return json.loads(serialized)


def test_to_json_handles_supported_types() -> None:
    expected_timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
    model = ExampleModel(value=1, label="sample", timestamp=expected_timestamp)
    dataclass_instance = ExampleDataclass(value=2, flag=True)
    sample_path = pathlib.Path("/tmp/specmaker")

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
        serialization.to_json({"value": complex(1, 2)})
