"""Unit tests for scenario locator helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from cucumber_messages import Feature as FeatureMessage
from cucumber_messages import GherkinDocument, Location, Pickle, Source

from pytest_bdd.compatibility.parser import ParsedFeature
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.run import Run
from pytest_bdd.scenario_locator import FileScenarioLocator, ScenarioLocatorFilterMixin, UrlScenarioLocator
from pytest_bdd.util.other import IdGenerator

pytestmark = [pytest.mark.unit]


class _Parser:
    """Parser test double that delegates to real GherkinParser for feature file content."""

    def __init__(self, *, id_generator: IdGenerator | None = None) -> None:
        self.id_generator = id_generator

    def parse(self, config: SimpleNamespace, path: Path, uri: str, **_kwargs: object) -> ParsedFeature:
        """Parse file content using the real GherkinParser for accurate scenario extraction."""
        from pytest_bdd.parser import GherkinParser

        real_parser = GherkinParser(id_generator=self.id_generator)
        return real_parser.parse(config, path, uri, **_kwargs)


def _document(*, uri: str = "file:feature.feature") -> GherkinDocument:
    """Create a minimal feature document."""
    return GherkinDocument(
        comments=[],
        feature=FeatureMessage(
            children=[],
            description="",
            keyword="Feature",
            language="en",
            location=Location(line=1, column=1),
            name="Feature",
            tags=[],
        ),
        uri=uri,
    )


def _config(stash: dict[str, object] | None = None) -> SimpleNamespace:
    """Build a locator config."""
    if stash is None:
        stash = {}
    IdGenerator().set_in_stash(stash)
    Run.initialize_for_session(stash=stash, session=SimpleNamespace(name="session"))

    def get_mimetype(**_kwargs: object) -> Mimetype:
        return Mimetype.gherkin_plain

    def get_parser(**_kwargs: object) -> type[_Parser]:
        return _Parser

    def getoption(_option: str) -> bool:
        return False

    hook = SimpleNamespace(pytest_bdd_get_mimetype=get_mimetype, pytest_bdd_get_parser=get_parser)
    return SimpleNamespace(stash=stash, hook=hook, getoption=getoption)


def test_file_locator_resolve_features_reads_feature_file(tmp_path: Path) -> None:
    """FileScenarioLocator resolves a feature file into parsed source."""
    feature = tmp_path / "sample.feature"
    feature.write_text("Feature: File\n", encoding="utf-8")
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=[feature.name])

    [(parsed, source)] = list(locator.resolve_features(_config()))

    assert parsed.filename == feature.as_posix()
    assert source.uri == "file:sample.feature"
    assert source.data == "Feature: File\n"


def test_file_locator_directory_expands_files(tmp_path: Path) -> None:
    """FileScenarioLocator expands directory paths into files."""
    feature_dir = tmp_path / "features"
    feature_dir.mkdir()
    (feature_dir / "one.feature").write_text("Feature: One\n", encoding="utf-8")
    (feature_dir / "two.feature").write_text("Feature: Two\n", encoding="utf-8")
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=[Path("features")])

    results = list(locator.resolve_features(_config()))

    assert [source.uri for _, source in results] == ["file:features/one.feature", "file:features/two.feature"]


def test_file_locator_filter_scenarios_excludes_all_pickles() -> None:
    """filter_scenarios honors a callback returning False."""

    def filter_(_config: object, _document: object, _pickle: object) -> bool:
        return False

    locator = FileScenarioLocator(features_base_dir=Path(), filter_=filter_)
    pickle = Pickle(
        id="pickle-1",
        uri="file:feature.feature",
        ast_node_ids=[],
        language="en",
        name="Scenario",
        steps=[],
        tags=[],
    )

    assert list(locator.filter_scenarios(_document(), [pickle], _config())) == []


def test_file_locator_missing_file_yields_no_features(tmp_path: Path) -> None:
    """FileScenarioLocator ignores a missing concrete file path."""
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["missing.feature"])

    assert list(locator.resolve_features(_config())) == []


def test_url_locator_builds_absolute_urls_from_base_url() -> None:
    """UrlScenarioLocator builds URLs for local paths when base URL is configured."""
    locator = UrlScenarioLocator(
        url_paths=["relative.feature", "https://example.test/direct.feature"],
        features_base_url="https://example.test/base",
    )

    assert locator._build_urls() == [
        "https://example.test/direct.feature",
        "https://example.test/base/relative.feature",
    ]


def test_url_locator_empty_url_list_yields_no_features() -> None:
    """UrlScenarioLocator returns no features when no URL can be built."""
    locator = UrlScenarioLocator(url_paths=["relative.feature"])

    assert list(locator.resolve_features(_config())) == []


def test_bind_feature_creates_pickles_in_run_stash() -> None:
    """ScenarioLocatorFilterMixin binds parsed feature data to the stashed run."""
    document = _document()
    parsed = ParsedFeature(gherkin_document=document, filename="feature.feature", raw_data="Feature: Feature\n")
    source = Source(uri="file:feature.feature", data=parsed.raw_data, media_type="text/x.cucumber.gherkin+plain")
    config = _config()

    binding = ScenarioLocatorFilterMixin._bind_feature(parsed, source, config)

    assert binding.uri == "file:feature.feature"
    assert binding.pickles == ()


def test_file_locator_resolve_yields_document_pickle_source(tmp_path: Path) -> None:
    """FileScenarioLocator.resolve yields (GherkinDocument, Pickle, Source) tuples."""
    feature = tmp_path / "sample.feature"
    feature.write_text("Feature: Resolve\n  Scenario: Test\n    Given step\n", encoding="utf-8")
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=[feature.name])

    results = list(locator.resolve(_config()))

    assert len(results) >= 1
    doc, _pickle, source = results[0]
    assert doc.feature.name == "Resolve"
    assert source.uri.startswith("file:")


def test_file_locator_filter_scenarios_passes_when_callback_none() -> None:
    """filter_scenarios with no filter yields all pickles."""
    locator = FileScenarioLocator(features_base_dir=Path())
    pickle = Pickle(
        id="p1",
        uri="file:f.feature",
        ast_node_ids=[],
        language="en",
        name="S",
        steps=[],
        tags=[],
    )

    results = list(locator.filter_scenarios(_document(), [pickle], _config()))
    assert len(results) == 1


def test_file_locator_filter_scenarios_passes_all_when_callback_true() -> None:
    """filter_scenarios with truthy callback yields all pickles."""

    def filter_(_c: object, _d: object, _p: object) -> bool:
        return True

    locator = FileScenarioLocator(features_base_dir=Path(), filter_=filter_)
    pickle = Pickle(id="p1", uri="file:f.feature", ast_node_ids=[], language="en", name="S", steps=[], tags=[])

    assert list(locator.filter_scenarios(_document(), [pickle], _config())) == [(_document(), pickle)]


def test_file_locator_defaults_provides_utf8_encoding() -> None:
    """FileScenarioLocatorDefaults.encoding returns utf-8."""
    from pytest_bdd.scenario_locator import FileScenarioLocatorDefaults

    assert FileScenarioLocatorDefaults.encoding() == "utf-8"


def test_file_locator_defaults_parse_args_returns_empty_args() -> None:
    """FileScenarioLocatorDefaults.parse_args returns empty Args."""
    from pytest_bdd.scenario_locator import FileScenarioLocatorDefaults

    result = FileScenarioLocatorDefaults.parse_args()
    assert result.args == ()
    assert result.kwargs == {}


def test_file_locator_with_glob_pattern(tmp_path: Path) -> None:
    """FileScenarioLocator resolves glob patterns into files."""
    features = tmp_path / "features"
    features.mkdir()
    (features / "a.feature").write_text("Feature: A\n", encoding="utf-8")
    (features / "b.feature").write_text("Feature: B\n", encoding="utf-8")
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["features/*.feature"])

    results = list(locator.resolve_features(_config()))
    assert len(results) == 2


def test_file_locator_duplicate_path_skipped(tmp_path: Path) -> None:
    """FileScenarioLocator skips duplicate resolved paths."""
    feature = tmp_path / "dup.feature"
    feature.write_text("Feature: Dup\n", encoding="utf-8")
    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=[feature.name, feature.name])

    results = list(locator.resolve_features(_config()))
    assert len(results) == 1


def test_url_locator_builds_only_remote_urls() -> None:
    """UrlScenarioLocator._build_urls returns only remote URLs when no base."""
    locator = UrlScenarioLocator(url_paths=["https://example.test/only.feature"])

    assert locator._build_urls() == ["https://example.test/only.feature"]


def test_filter_mixin_with_none_filter_passes_all() -> None:
    """ScenarioLocatorFilterMixin with no filter passes all pickles."""
    locator = ScenarioLocatorFilterMixin(filter_=None)
    pickle = Pickle(id="p1", uri="file:f.feature", ast_node_ids=[], language="en", name="S", steps=[], tags=[])

    results = list(locator.filter_scenarios(_document(), [pickle], _config()))
    assert len(results) == 1
