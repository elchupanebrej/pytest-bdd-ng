import pytest

from pytest_cuke.model.doc_string import DocString
from pytest_cuke.model.message_converter import step_to_pickle_step
from pytest_cuke.model.step import Step
from pytest_cuke.model.table import DataTable, TableCell, TableRow


@pytest.mark.parametrize("doc_line,table_line,expected", [(4, 9, (1, 2)), (9, 4, (2, 1))])
def test_combined_argument_views_and_wire_preserve_bodies_and_order(doc_line, table_line, expected):
    step = Step(
        name="combined",
        keyword="Given",
        doc_string=DocString("body", "text/plain", line=doc_line),
        data_table=DataTable((TableRow((TableCell("value"),)),), line=table_line),
    )
    for argument in [step.argument, step_to_pickle_step(step).argument]:
        assert argument.doc_string.content == "body"
        assert argument.data_table.rows[0].cells[0].value == "value"
        assert (argument.doc_string.argument_index, argument.data_table.argument_index) == expected


@pytest.mark.parametrize("doc_line,table_line", [(0, 0), (0, 4), (4, 0), (4, 4)])
def test_unknown_argument_order_is_not_invented(doc_line, table_line):
    step = Step(
        name="combined",
        keyword="Given",
        doc_string=DocString("body", line=doc_line),
        data_table=DataTable((TableRow((TableCell("value"),)),), line=table_line),
    )
    for argument in [step.argument, step_to_pickle_step(step).argument]:
        assert argument.doc_string.content == "body"
        assert argument.data_table.rows[0].cells[0].value == "value"
        assert argument.doc_string.argument_index is None
        assert argument.data_table.argument_index is None


@pytest.mark.parametrize("kind", ["doc", "table"])
def test_single_arguments_keep_their_existing_unindexed_representation(kind):
    step = Step(
        name="single",
        keyword="Given",
        doc_string=DocString("body") if kind == "doc" else None,
        data_table=DataTable() if kind == "table" else None,
    )
    argument = step_to_pickle_step(step).argument
    value = argument.doc_string if kind == "doc" else argument.data_table
    assert value.argument_index is None
