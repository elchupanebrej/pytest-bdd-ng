"""Simple `Application under test` catalog."""

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass  # Easy way to not write redundant __init__ https://docs.python.org/3/library/dataclasses.html
class Book:
    """Represent book state."""

    author: str
    title: str


@dataclass
class Catalog:
    """
    Represent catalog state.

    Yields:
        Generated values.

    """

    storage: list[Book] = field(default_factory=list)

    def add_books_to_catalog(self, books: Iterable[Book]) -> None:
        """Handle add books to catalog."""
        self.storage.extend(books)

    def search_by_author(self, term: str) -> Iterable[Book]:
        """
        Handle search by author.

        Yields:
            Generated values.

        """
        for book in self.storage:
            if term in book.author:
                yield book

    def search_by_title(self, term: str) -> Iterable[Book]:
        """
        Handle search by title.

        Yields:
            Generated values.

        """
        for book in self.storage:
            if term in book.title:
                yield book
