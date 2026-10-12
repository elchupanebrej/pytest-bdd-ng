from __future__ import annotations

import argparse
import ast
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pytest_cuke.generation import (
    STEP_TYPE_TO_STEP_METHOD_NAME,
    STEP_TYPE_TO_STEP_PREFIX,
    add_options,
    check_existense,
    cmdline_main,
    make_python_docstring,
    make_string_literal,
)
from pytest_cuke.model import StepType


def test_generation_helpers() -> None:
    assert ast.literal_eval(make_python_docstring("simple")) == "simple."
    assert ast.literal_eval(make_python_docstring('with """ quotes')) == 'with """ quotes.'
    assert ast.literal_eval(make_python_docstring("line one\nline two")) == "line one\nline two."
    assert ast.literal_eval(make_string_literal("hello")) == "hello"
    assert ast.literal_eval(make_string_literal("it's fine\\and café\nnext")) == "it's fine\\and café\nnext"

    assert STEP_TYPE_TO_STEP_PREFIX[StepType.context] == "Given"
    assert STEP_TYPE_TO_STEP_PREFIX[StepType.action] == "When"
    assert STEP_TYPE_TO_STEP_PREFIX[StepType.outcome] == "Then"
    assert STEP_TYPE_TO_STEP_METHOD_NAME[StepType.context] == "given"


def test_check_existense(tmp_path: Path) -> None:
    f = tmp_path / "feat.feature"
    f.touch()
    assert check_existense(str(f)) == f

    with pytest.raises(argparse.ArgumentTypeError, match="is an invalid file or directory name"):
        check_existense(str(tmp_path / "non_existent.feature"))


def test_generation_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    add_options(parser)
    parser.getgroup.assert_called_once_with("cuke", "Generation")
    assert group._addoption.call_count == 3


def test_cmdline_main_none() -> None:
    config = MagicMock()
    config.option.cuke_generate_missing = False
    config.option.cuke_generate = False

    assert cmdline_main(config) is None
