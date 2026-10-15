"""
The tutorial features and tests are siblings, so their shared steps and fixtures
must be registered at the tutorial project root.

https://docs.pytest.org/en/latest/how-to/writing_plugins.html#conftest-py-local-per-directory-plugins
https://docs.pytest.org/en/latest/explanation/goodpractices.html#test-discovery
"""

from pytest import fixture

from .tests.steps.library_steps import (
    a_search_type_is_performed_for_search_term,
    only_these_books_will_be_returned,
    these_books_in_the_catalog,
)


@fixture
def search_results() -> list:
    return []
