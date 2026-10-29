from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from attrs.exceptions import FrozenInstanceError

from pytest_cuke import given

if TYPE_CHECKING:
    from pytest_cuke.model import Feature


@given("the legacy feature is adapted to a native model")
def legacy_feature_is_adapted(feature: Feature) -> None:
    assert feature.source_content is not None
    assert feature.filename is not None
    assert feature.uri
    log_path = Path(os.environ.get("PYTEST_CUKE_INVOCATION_LOG", "parser-invocations.json"))
    invocation = json.loads(log_path.read_text(encoding="utf-8"))[-1]
    assert feature.source_content == Path(feature.filename).read_text(encoding=invocation["encoding"])
    with pytest.raises(FrozenInstanceError):
        feature.name = "mutated"
