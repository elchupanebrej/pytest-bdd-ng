from __future__ import annotations

from pytest_bdd.model.background import Background
from pytest_bdd.model.doc_string import DocString
from pytest_bdd.model.document import GherkinDocument
from pytest_bdd.model.examples import Examples
from pytest_bdd.model.feature import Feature
from pytest_bdd.model.rule import Rule
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.serialization import as_dict, from_dict, from_json, to_json
from pytest_bdd.model.step import Step, StepType
from pytest_bdd.model.table import DataTable, TableCell, TableRow
from pytest_bdd.model.tag import Tag


def test_leaf_serialization_roundtrip() -> None:
    tag = Tag(name="@smoke", line=1, id="t1")
    assert from_dict(Tag, as_dict(tag)) == tag
    assert from_json(Tag, to_json(tag)) == tag

    doc_str = DocString(content="body", media_type="application/json", line=2, id="d1")
    assert from_dict(DocString, as_dict(doc_str)) == doc_str
    assert from_json(DocString, to_json(doc_str)) == doc_str

    tbl = DataTable(
        rows=(TableRow(cells=(TableCell(value="k", line=3), TableCell(value="v", line=3)), line=3),),
        line=3,
        id="dt1",
    )
    assert from_dict(DataTable, as_dict(tbl)) == tbl
    assert from_json(DataTable, to_json(tbl)) == tbl

    ex = Examples(
        header=TableRow(cells=(TableCell("h1"),)),
        rows=(TableRow(cells=(TableCell("val"),)),),
        tags=(tag,),
        name="Ex1",
        line=4,
    )
    assert from_dict(Examples, as_dict(ex)) == ex
    assert from_json(Examples, to_json(ex)) == ex


def test_composite_tree_seam2_roundtrip_contract() -> None:
    tag = Tag(name="@unit", line=1)
    doc_str = DocString(content="text", media_type="text/plain", line=5)
    tbl = DataTable(rows=(TableRow(cells=(TableCell("col1"), TableCell("col2"))),))
    step1 = Step(name="step 1", keyword="Given ", line=2, type=StepType.context, id="s1")
    step2 = Step(name="step 2", keyword="When ", line=3, doc_string=doc_str, data_table=tbl, type=StepType.action)
    bg = Background(name="Setup", line=2, steps=(step1,))
    ex = Examples(
        header=TableRow(cells=(TableCell("x"),)),
        rows=(
            TableRow(
                cells=(TableCell("1")),
            ),
        ),
    )
    sc1 = Scenario(name="Scenario 1", line=4, tags=(tag,), background=bg, steps=(step2,), examples=(ex,), id="sc1")
    sc2 = Scenario(name="Rule scenario", line=12, steps=(step1,))
    rule = Rule(name="Rule 1", line=10, background=bg, scenarios=(sc2,), id="r1")
    feature = Feature(
        name="Seam 2 Feature",
        line=1,
        tags=(tag,),
        description="Feature contract test",
        background=bg,
        scenarios=(sc1,),
        rules=(rule,),
        uri="features/seam2.feature",
        id="feat-1",
    )
    document = GherkinDocument(uri="features/seam2.feature", feature=feature, comments=("# Contract doc",), id="doc-1")

    assert feature.tag_names == ("unit",)
    assert len(feature.all_scenarios) == 2
    assert sc1.tag_names == ("unit",)
    assert len(sc1.all_steps) == 2

    doc_dict = as_dict(document)
    restored_from_dict = from_dict(GherkinDocument, doc_dict)
    assert restored_from_dict == document

    doc_json = to_json(document)
    restored_from_json = from_json(GherkinDocument, doc_json)
    assert restored_from_json == document
