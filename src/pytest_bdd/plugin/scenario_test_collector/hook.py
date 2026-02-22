from collections.abc import Iterable
from pathlib import Path

import pytest

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
    def pytest_bdd_convert_tag_to_marks(self, feature, scenario, tag) -> Iterable[Mark] | None:
        """Apply a tag (from a ``.feature`` file) to the given test item.

        The default implementation does the equivalent of
        ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
        return ``True`` to do more sophisticated handling of tags.
        """
