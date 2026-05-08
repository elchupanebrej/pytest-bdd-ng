"""Provide library steps helpers."""

import re
from collections.abc import Iterator
from typing import Literal

from cucumber_messages import DataTable, TestStep  # type:ignore[attr-defined]

from pytest_bdd import given, then, when

try:
    from tutorial.src.catalog import Book, Catalog
except ModuleNotFoundError:  # pragma: no cover - repository-local tutorial layout
    from docs.tutorial.src.catalog import Book, Catalog


def get_books_from_data_table(data_table: DataTable) -> list[Book]:
    # Gherkin data-tables have no title row by default, but we could define them if we want.
    """Return books from data table."""
    title_row, *book_rows = data_table.rows

    step_data_table_titles = [cell.value for cell in title_row.cells]

    assert step_data_table_titles == ["Author", "Title"]

    return [Book(row.cells[0].value, row.cells[1].value) for row in book_rows]


# Steps to be used in scenarios are defined with special decorators
@given(
    "these books in the catalog",
    # Steps are allowed to inject new fixtures or overwrite existing ones
    target_fixture="catalog",
)
def these_books_in_the_catalog(
    # `step` fixture is injected by pytest dependency injection mechanism into scope of step by default;
    # So it could be used without extra effort
    step: TestStep,
) -> Iterator[Catalog]:
    """
    Handle these books in the catalog.

    Yields:
        Generated values.

    """
    books = get_books_from_data_table(step.argument.data_table)

    catalog = Catalog()
    catalog.add_books_to_catalog(books)

    yield catalog


@when(
    # Step definitions could have parameters. Here could be raw stings, cucumber expressions or regular expressions
    re.compile(r"a (?P<search_type>name|title) search is performed for (?P<search_term>.+)"),
    target_fixture="search_results",
)
def a_search_type_is_performed_for_search_term(
    # `search_results` is a usual pytest fixture defined somewhere else (at conftest.py, plugin or module)
    # and injected by pytest dependency injection mechanism.
    # In this case it will be provided by conftest.py
    search_results: list[Book],
    # `search_type` and `search_term` are parameters of this step and are injected by step definition
    search_type: Literal["name", "title"],
    search_term: str,
    # `catalog` is a fixture injected by another step
    catalog: Catalog,
) -> Iterator[list[Book]]:
    """
    Handle a search type is performed for search term.

    Yields:
        Generated values.

    Raises:
        AssertionError: If the operation cannot be completed.

    """
    if search_type == "title":
        search = catalog.search_by_title
    elif search_type == "name":
        search = catalog.search_by_author
    else:
        msg = "Unknown"
        raise AssertionError(msg)

    found_books = search(search_term)
    search_results.extend(found_books)
    yield search_results


@then("only these books will be returned")
def only_these_books_will_be_returned(
    # Fixtures persist during step execution, so usual `context` common for behave users is not required,
    # so if you define fixture dependencies debugging becomes much easier.
    search_results: list[Book],
    step: TestStep,
) -> None:
    """Handle only these books will be returned."""
    expected_books = get_books_from_data_table(step.argument.data_table)
    non_expected_books = [book for book in search_results if book not in expected_books]
    assert not non_expected_books, f"Books {non_expected_books} are not expected"
