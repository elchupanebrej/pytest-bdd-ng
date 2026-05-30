"""Rendering helpers for generated pytest-bdd code."""

from __future__ import annotations

import logging
import subprocess  # noqa: S404
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from cucumber_messages import PickleStepType  # type:ignore[attr-defined, import-untyped]
from jinja2 import Environment

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.util.other import format_as_simplified_python_identifier

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cucumber_messages import Pickle, PickleStep  # type:ignore[attr-defined, import-untyped]
    from jinja2.environment import Template

    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding

logger = logging.getLogger(__name__)

STEP_TYPE_TO_STEP_PREFIX = {
    PickleStepType.unknown: "*",
    PickleStepType.outcome: "Then",
    PickleStepType.context: "Given",
    PickleStepType.action: "When",
}

STEP_TYPE_TO_STEP_METHOD_NAME = {
    PickleStepType.unknown: "step",
    PickleStepType.outcome: "then",
    PickleStepType.context: "given",
    PickleStepType.action: "when",
}

TEMPLATE_ENV = Environment(autoescape=False, keep_trailing_newline=True)  # noqa: S701


@lru_cache(maxsize=1)
def get_code_generation_template() -> Template:
    """
    Return code generation template.

    Returns:
        Jinja2 template for code generation.

    """
    template_source = files("pytest_bdd.template").joinpath("test.py.jinja2").read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


def _format_code(code: str) -> str:
    """
    Format generated Python code using ruff.

    Returns:
        Formatted Python code string.

    """
    formatted_code = code
    tmp_path = None

    try:
        import tempfile  # noqa: PLC0415

        from ruff import find_ruff_bin  # type: ignore[import-untyped]  # noqa: PLC0415

        ruff_bin = find_ruff_bin()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        subprocess.run(  # noqa: S603
            [ruff_bin, "format", tmp_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

        formatted_code = Path(tmp_path).read_text(encoding="utf-8")
    except (ImportError, OSError, subprocess.SubprocessError):
        logger.warning("Code generation formatting failed", exc_info=True)
    finally:
        if tmp_path is not None:
            with suppress(Exception):
                Path(tmp_path).unlink(missing_ok=True)

    return formatted_code


def generate_code(
    features: Sequence[FeatureRuntimeBinding],
    feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> str:
    """
    Generate test code for the given filenames.

    Returns:
        Generated Python code string.

    """
    template = get_code_generation_template()
    code = template.render(
        features=features,
        feature_pickles=feature_pickles,
        feature_pickle_steps=feature_pickle_steps,
        make_python_name=format_as_simplified_python_identifier,
        make_python_docstring=make_python_docstring,
        make_string_literal=make_string_literal,
        step_type_to_method_name=STEP_TYPE_TO_STEP_METHOD_NAME,
    )
    return _format_code(code)


def make_python_docstring(string: str) -> str:
    """
    Make a python docstring literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python docstring literal.

    """
    return repr(string)


def make_string_literal(string: str) -> str:
    """
    Make python string literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python string literal.

    """
    return repr(string)
