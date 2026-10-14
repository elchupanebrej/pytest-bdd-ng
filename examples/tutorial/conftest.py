"""
conftest.py is local per-directory plugin of pytest.
Its mission is to define fixtures, steps, and hooks which will be used
by tests gathered by pytest from directory structure below

https://docs.pytest.org/en/latest/how-to/writing_plugins.html#conftest-py-local-per-directory-plugins
https://docs.pytest.org/en/latest/explanation/goodpractices.html#test-discovery
"""

import sys
from pathlib import Path

from pytest import fixture

# The tutorial's step module uses package-relative imports. Make the repository
# root importable so the module has the same package name from either cwd.
_repository_root = str(Path(__file__).resolve().parents[2])
if _repository_root not in sys.path:
    sys.path.insert(0, _repository_root)

from examples.tutorial.tests.steps.library_steps import (  # noqa: E402
    a_search_type_is_performed_for_search_term,
    only_these_books_will_be_returned,
    these_books_in_the_catalog,
)


@fixture
def search_results() -> list:
    return []
