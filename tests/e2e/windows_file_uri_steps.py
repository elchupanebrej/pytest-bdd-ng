"""BDD steps for Windows drive-rooted feature source identities."""

from __future__ import annotations

import re
from pytest_cuke import given, then, when

from pytest_cuke.ide_bindings import source_identity
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.feature_binding import FeatureRuntimeBinding
from pytest_cuke.model.scenario import Scenario


@given(
    re.compile(r'a Windows drive-rooted feature URI "(?P<uri>[^"]+)"'),
    target_fixture="windows_uri_feature",
)
def windows_drive_root_feature(uri: str) -> Feature:
    scenario = Scenario(name="Checkout", line=7, id="scenario-id")
    return Feature(name="Windows source", uri=uri, scenarios=(scenario,))


@when("the feature source is bound to a runtime", target_fixture="windows_uri_binding")
def bind_windows_drive_root_feature(windows_uri_feature: Feature) -> FeatureRuntimeBinding:
    return FeatureRuntimeBinding.from_feature(windows_uri_feature)


@then("its bound URI and editor identity preserve the drive root")
def windows_drive_root_identity_is_preserved(
    windows_uri_feature: Feature,
    windows_uri_binding: FeatureRuntimeBinding,
) -> None:
    scenario = windows_uri_feature.scenarios[0]
    identity = source_identity(windows_uri_feature, scenario, windows_uri_binding)

    expected_uri = "file:///C:/workspace/my%20features/checkout.feature"
    assert windows_uri_binding.uri == expected_uri
    assert identity["uri"] == expected_uri
    assert identity["scenarioUri"] == expected_uri
