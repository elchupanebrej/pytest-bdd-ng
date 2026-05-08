"""Provide gherkin helpers."""

from gherkin.parser_types import GherkinDocument as BaseGherkinDocument


class GherkinDocument(BaseGherkinDocument):
    """Represent gherkin document state."""

    uri: str | None
    # TODO: remove all usages of this field
    _pytest_bdd_filename: str | None
