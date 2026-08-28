from __future__ import annotations

import attr
from pytest_bdd.types import (
    CollectorFailure,
    GenericFailure,
    Identifiable,
    LinkedAST,
    MultiLinkedAST,
    ParserFailure,
    StashFailure,
)


@attr.frozen(slots=True)
class DummyIdentifiable:
    id: str


@attr.frozen(slots=True)
class DummyAST:
    ast_node_id: str
    ast_node_ids: list[str]


def test_failure_reasons_values() -> None:
    assert StashFailure.NOT_FOUND == "not_found"
    assert CollectorFailure.PARSE_FAILED == "parse_failed"
    assert ParserFailure.SYNTAX_ERROR == "syntax_error"
    assert GenericFailure.UNEXPECTED_ERROR == "unexpected_error"


def test_runtime_protocols() -> None:
    obj = DummyIdentifiable(id="123")
    assert isinstance(obj, Identifiable)
    ast_obj = DummyAST(ast_node_id="n1", ast_node_ids=["n1", "n2"])
    assert isinstance(ast_obj, LinkedAST)
    assert isinstance(ast_obj, MultiLinkedAST)
