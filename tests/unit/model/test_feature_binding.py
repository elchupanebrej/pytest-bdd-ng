from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from pytest_cuke.model import feature_binding
from pytest_cuke.ide_bindings import source_identity
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.feature_binding import FeatureRuntimeBinding
from pytest_cuke.model.scenario import Scenario


def test_windows_drive_file_uri_keeps_source_identity_without_host_path_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature_uri = "file:///C:/workspace/features/checkout.feature"
    scenario = Scenario(name="Checkout", line=7, id="scenario-id")
    feature = Feature(name="Windows source", uri=feature_uri, scenarios=(scenario,))

    class HostPathAccessForbidden:
        def __init__(self, path: str) -> None:
            raise AssertionError(f"a Windows file URI must not be interpreted as a host path: {path}")

    monkeypatch.setattr(feature_binding, "Path", HostPathAccessForbidden)

    binding = FeatureRuntimeBinding.from_feature(feature)
    identity = source_identity(feature, scenario, binding)

    parsed_uri = urlsplit(binding.uri)
    assert parsed_uri.scheme == "file"
    assert parsed_uri.netloc == ""
    assert parsed_uri.path == "/C:/workspace/features/checkout.feature"
    assert identity["uri"] == feature_uri
    assert identity["scenarioUri"] == feature_uri
