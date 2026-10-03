from __future__ import annotations

from pathlib import Path

import pytest

from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.reporting import ScenarioReport


def test_scenario_report_uses_normalized_file_uri_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    tools = project / "tools"
    source = project / "selected-features" / "invocation.feature"
    tools.mkdir(parents=True)
    source.parent.mkdir()
    monkeypatch.chdir(tools)
    feature = Feature(name="Invocation", uri="file:invocation.feature", filename=str(source))

    report = ScenarioReport(feature=feature, scenario=Scenario(name="Selected root"))

    assert feature.rel_filename == source.as_posix()
    assert report.serialize()["feature"]["rel_filename"] == "invocation.feature"
