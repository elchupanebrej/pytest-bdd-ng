"""Keep the legacy argument view available to installed step consumers."""

import subprocess
import sys
from textwrap import dedent

import pytest

pytestmark = pytest.mark.integration


def test_step_argument_and_direct_data_fields(tmp_path):
    (tmp_path / "features").mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\ncuke_parser = python\n", encoding="utf-8")
    (tmp_path / "features" / "arguments.feature").write_text(
        dedent('''\
            Feature: Step argument compatibility
              Scenario: DocString
                Given a document
                  """text/plain
                  first line
                  café second line
                  """
              Scenario: DataTable
                Given a table
                  | name | value |
                  | café |       |
              Scenario: No argument
                Given no argument
        '''),
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text(
        dedent("""\
            from cucumber_messages import PickleStepArgument, PickleDocString, PickleTable
            from pytest_cuke import given

            @given("a document")
            def document(step):
                argument = step.argument
                assert isinstance(argument, PickleStepArgument)
                assert isinstance(argument.doc_string, PickleDocString)
                assert argument.data_table is None
                assert argument.doc_string.content == step.doc_string.content == "first line\\ncafé second line"
                assert argument.doc_string.media_type == step.doc_string.media_type == "text/plain"
                assert step.data_table is None

            @given("a table")
            def table(step):
                argument = step.argument
                assert isinstance(argument, PickleStepArgument)
                assert isinstance(argument.data_table, PickleTable)
                assert argument.doc_string is None
                rows = [[cell.value for cell in row.cells] for row in argument.data_table.rows]
                assert rows == step.data_table.raw == [["name", "value"], ["café", ""]]
                assert step.doc_string is None
                argument.data_table.rows[1].cells[0].value = "changed snapshot"
                assert step.data_table.raw[1][0] == "café"
                assert step.argument.data_table.rows[1].cells[0].value == "café"

            @given("no argument")
            def no_argument(step):
                assert step.argument is None
                assert step.doc_string is None
                assert step.data_table is None
        """),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "pytest.ini", "--confcutdir=.", "-q"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 passed" in result.stdout
