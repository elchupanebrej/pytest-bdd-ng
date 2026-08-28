from __future__ import annotations

from pytest_bdd.types import (
    CollectorFailure,
    GenericFailure,
    ParserFailure,
    StashFailure,
)


def test_failure_reasons_values() -> None:
    assert StashFailure.NOT_FOUND == "not_found"
    assert CollectorFailure.PARSE_FAILED == "parse_failed"
    assert ParserFailure.SYNTAX_ERROR == "syntax_error"
    assert GenericFailure.UNEXPECTED_ERROR == "unexpected_error"
