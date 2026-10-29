from pytest_cuke import given, then, when


@given("the catalog contains a book", target_fixture="book")
def catalog_contains_book() -> str:
    return "The Semantic Gherkin Guide"


@when("the reader searches for that book", target_fixture="search_result")
def reader_searches_for_book(book: str) -> str:
    return book


@then("the search returns the catalog book")
def search_returns_book(book: str, search_result: str) -> None:
    assert search_result == book
