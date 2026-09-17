from __future__ import annotations

from pytest_bdd.model.doc_string import DocString
from pytest_bdd.model.examples import Example, Examples
from pytest_bdd.model.table import DataTable, TableCell, TableRow
from pytest_bdd.model.tag import Tag

from pytest import mark

pytestmark = mark.unit



def test_leaf_models() -> None:
    t = Tag(name="@smoke", line=1, id="t1")
    assert t.clean_name == "smoke" and t.line == 1 and t.id == "t1"
    d = DocString(content="hi", media_type="text/plain", line=2)
    assert d.content == "hi" and d.media_type == "text/plain" and d.line == 2
    r1 = TableRow(cells=(TableCell(value="k"), TableCell(value="v")), line=3)
    r2 = TableRow(cells=(TableCell(value="a"), TableCell(value="1")), line=4)
    dt = DataTable(rows=(r1, r2), line=3)
    assert dt.raw == [["k", "v"], ["a", "1"]]
    assert dt.headings == ("k", "v")
    assert dt.as_dicts() == [{"k": "a", "v": "1"}]


def test_example_models() -> None:
    header = TableRow(cells=(TableCell("var1"), TableCell("var2")), line=10)
    r1 = TableRow(cells=(TableCell("val1"), TableCell("val2")), line=11)
    tag = Tag(name="@ex_tag", line=9)
    examples = Examples(header=header, rows=(r1,), tags=(tag,), name="Example set", line=9)

    assert examples.column_names == ("var1", "var2")
    assert examples.as_dicts() == [{"var1": "val1", "var2": "val2"}]
    assert examples.keyword == "Examples"

    ex = Example(values=("val1", "val2"), row=r1, line=11, tags=(tag,))
    assert ex.values == ("val1", "val2")
    assert ex.tags == (tag,)


def test_table_and_examples_without_data_rows() -> None:
    header_only = Examples(header=TableRow(cells=(TableCell("var1"),)))
    assert header_only.as_dicts() == []
    rows_only = Examples(rows=(TableRow(cells=(TableCell("val1"),)),))
    assert rows_only.column_names == ()
    assert rows_only.as_dicts() == []

    assert DataTable().headings == ()
    assert DataTable(rows=(TableRow(cells=(TableCell("only"),)),)).as_dicts() == []


def test_legacy_model_module_shims_reexport_canonical_objects() -> None:
    from pytest_bdd.model.document import GherkinDocument
    from pytest_bdd.model.gherkin_document import GherkinDocument as LegacyGherkinDocument
    from pytest_bdd.model.message_extension import ExpressionType, StepDefinitionPatternType
    from pytest_bdd.model.messages_extension import (
        ExpressionType as LegacyExpressionType,
        StepDefinitionPatternType as LegacyStepDefinitionPatternType,
    )

    assert LegacyGherkinDocument is GherkinDocument
    assert LegacyExpressionType is ExpressionType
    assert LegacyStepDefinitionPatternType is StepDefinitionPatternType
    assert LegacyStepDefinitionPatternType.pytest_bdd_string_expression.value == "PYTEST_BDD_STRING_EXPRESSION"
