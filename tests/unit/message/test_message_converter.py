from __future__ import annotations

import pytest

import messages
from pytest_bdd.model.background import Background
from pytest_bdd.model.doc_string import DocString
from pytest_bdd.model.feature import Feature
from pytest_bdd.model.message_converter import (
    feature_to_envelope,
    feature_to_gherkin_document,
    validate_envelope_shape,
)
from pytest_bdd.model.rule import Rule
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.step import Step
from pytest_bdd.model.table import DataTable, TableCell, TableRow
from pytest_bdd.model.tag import Tag


def test_feature_to_gherkin_document_conversion() -> None:
    step1 = Step(name="an item exists", keyword="Given ", line=5)
    doc_str = DocString(content="hello world", media_type="text/plain", line=8)
    table = DataTable(rows=(TableRow(cells=(TableCell(value="v1", line=10),), line=10),), line=10)
    step2 = Step(name="details are provided", keyword="When ", line=7, doc_string=doc_str, data_table=table)

    bg = Background(name="Setup", keyword="Background", line=4, steps=(step1,))
    sc = Scenario(name="Scenario 1", keyword="Scenario", line=6, steps=(step2,), tags=(Tag(name="@unit", line=6),))
    rule = Rule(name="Rule 1", keyword="Rule", line=12, scenarios=(sc,))

    feature = Feature(
        name="Cart Feature",
        description="Handles user carts",
        uri="features/cart.feature",
        line=1,
        tags=(Tag(name="@feature_tag", line=1),),
        background=bg,
        scenarios=(sc,),
        rules=(rule,),
    )

    doc = feature_to_gherkin_document(feature)
    assert doc.uri == "features/cart.feature"
    assert doc.feature is not None
    assert doc.feature.name == "Cart Feature"
    assert len(doc.feature.tags) == 1
    assert doc.feature.tags[0].name == "@feature_tag"
    assert len(doc.feature.children) == 3  # bg, sc, rule

    env = feature_to_envelope(feature)
    assert env.gherkin_document is not None
    assert env.gherkin_document.feature is not None
    assert env.gherkin_document.feature.name == "Cart Feature"
    validate_envelope_shape(env)


def test_validate_envelope_shape_error() -> None:
    empty_env = messages.Envelope()
    with pytest.raises(TypeError, match="exactly one payload"):
        validate_envelope_shape(empty_env)
