from collections.abc import Iterable
from pathlib import Path

import pytest
from cucumber_messages import GherkinDocument, Pickle, Source  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import Config, Mark


class ScenarioTestCollectorHookSpec:
    @pytest.hookspec(firstresult=True)
    def pytest_bdd_is_collectible(self, config: Config, path: Path):
        """Verifies if path could be collected by pytest_bdd"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_parser(self, config: Config, mimetype: str):
        """Get parser for specific file path"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_mimetype(self, config: Config, path: Path):
        """Get parser for specific file path"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_convert_tag_to_marks(self, gherkin_document: GherkinDocument, pickle: Pickle, tag) -> Iterable[Mark] | None:
        """Apply a tag (from a ``.feature`` file) to the given test item.

        The default implementation does the equivalent of
        ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
        return ``True`` to do more sophisticated handling of tags.
        """

    def pytest_bdd_source_read(self, config: Config, gherkin_document: GherkinDocument, source: Source) -> None:
        """Notify plugins that source payload for feature was read during collection."""

    def pytest_bdd_feature_read(self, config: Config, gherkin_document: GherkinDocument) -> None:
        """Notify plugins that gherkin document payload for feature was read during collection."""

    def pytest_bdd_pickle_read(self, config: Config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        """Notify plugins that pickle payload was materialized during collection."""
