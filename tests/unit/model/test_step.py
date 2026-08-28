from __future__ import annotations

from pytest_bdd.model.background import Background
from pytest_bdd.model.doc_string import DocString
from pytest_bdd.model.step import Step
from pytest_bdd.model.table import DataTable, TableCell, TableRow


def test_step_and_background() -> None:
    doc = DocString(content="payload", line=2)
    tbl = DataTable(rows=(TableRow(cells=(TableCell("x"),)),), line=3)
    step = Step(name="a step", keyword="Given ", line=1, doc_string=doc, data_table=tbl, type="Context", id="s1")
    assert step.name == "a step"
    assert step.prefix == "given"
    assert step.doc_string == doc
    assert step.data_table == tbl

    bg = Background(name="Setup", line=0, steps=(step,))
    assert bg.name == "Setup"
    assert bg.keyword == "Background"
    assert len(bg.steps) == 1
