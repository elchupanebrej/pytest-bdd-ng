"""
Rendering helpers for generated pytest-bdd code.

Responsibility:
    Rendering helpers for generated pytest-bdd code. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - get_code_generation_template: owns nested behavior below this boundary
    - _run_ruff_format: owns nested behavior below this boundary
    - _format_code: owns nested behavior below this boundary
    - generate_code: owns nested behavior below this boundary
    - render_legacy_stdout_code: owns nested behavior below this boundary
    - make_python_docstring: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates logger, STEP_TYPE_TO_STEP_PREFIX, STEP_TYPE_TO_STEP_METHOD_NAME, TEMPLATE_ENV, template_source; depends on
    __future__.annotations, logging, subprocess, sys, contextlib.suppress.

Invariants:
    - `pytest_bdd.plugin.code_generator.rendering` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import logging
import subprocess  # noqa: S404
import sys
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from cucumber_messages import (
    PickleStepType,  # upstream library missing type stubs
)
from jinja2 import Environment

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.util.other import format_as_simplified_python_identifier

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cucumber_messages import (  # upstream library missing type stubs
        Pickle,
        PickleStep,
    )
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

    Responsibility:
        Return code generation template. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.rendering.get_code_generation_template` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - files.joinpath.read_text: collaborator call used by this boundary
        - files.joinpath: collaborator call used by this boundary
        - files: collaborator call used by this boundary
        - TEMPLATE_ENV.from_string: collaborator call used by this boundary
        - lru_cache: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates template_source.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rendering.get_code_generation_template` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    template_source = files("pytest_bdd.template").joinpath("test.py.jinja2").read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


def _run_ruff_format(code: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.code_generator.rendering._run_ruff_format` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering._run_ruff_format` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - tempfile.NamedTemporaryFile: collaborator call used by this boundary
        - tmp.write: collaborator call used by this boundary
        - subprocess.run: collaborator call used by this boundary
        - Path.read_text: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates tmp_path; depends on tempfile.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rendering._run_ruff_format` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    import tempfile  # noqa: PLC0415

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        subprocess.run(  # noqa: S603
            [sys.executable, "-m", "ruff", "format", tmp_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return Path(tmp_path).read_text(encoding="utf-8")
    finally:
        with suppress(Exception):
            Path(tmp_path).unlink(missing_ok=True)


def _format_code(code: str) -> str:
    """
    Format generated Python code using ruff.

    Returns:
        Formatted Python code string.

    Responsibility:
        Format generated Python code using ruff. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering._format_code` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _run_ruff_format: collaborator call used by this boundary
        - logger.warning: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    try:
        return _run_ruff_format(code)
    except (ImportError, OSError, subprocess.SubprocessError):
        logger.warning("Code generation formatting failed", exc_info=True)
        return code


def generate_code(
    features: Sequence[FeatureRuntimeBinding],
    feature_pickles: Sequence[tuple[FeatureRuntimeBinding, Pickle]],
    feature_pickle_steps: Sequence[tuple[tuple[FeatureRuntimeBinding, Pickle], PickleStep]],
) -> str:
    """
    Generate test code for the given filenames.

    Returns:
        Generated Python code string.

    Responsibility:
        Generate test code for the given filenames. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering.generate_code` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - get_code_generation_template: collaborator call used by this boundary
        - template.render: collaborator call used by this boundary
        - _format_code: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `generate_code`

    State and side effects:
        mutates template, code.

    Invariants:
        - `pytest_bdd.plugin.code_generator.rendering.generate_code` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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


def render_legacy_stdout_code(code: str) -> str:
    """
    Render generated code in the legacy stdout shape expected by old callers.

    Responsibility:
        Render generated code in the legacy stdout shape expected by old callers. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering.render_legacy_stdout_code`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - code.replace: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `render_legacy_stdout_code`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    return code.replace(
        "from pytest_bdd import (\n    scenario,\n    given,\n    when,\n    then,\n    step,\n)\n",
        "from pytest_bdd import given, scenario, step, then, when\n",
    )


def make_python_docstring(string: str) -> str:
    """
    Make a python docstring literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python docstring literal.

    Responsibility:
        Make a python docstring literal out of a given string. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering.make_python_docstring`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - repr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return repr(string)


def make_string_literal(string: str) -> str:
    """
    Make python string literal out of a given string.

    Args:
        string: Input string.

    Returns:
        Python string literal.

    Responsibility:
        Make python string literal out of a given string. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.rendering.make_string_literal`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - repr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `make_string_literal`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return repr(string)


def render_missing_step_skeleton(*, decorator: str, text: str) -> str:
    """
    Render one inert missing-step skeleton.

    Args:
        decorator: Step decorator name.
        text: Step text.

    Returns:
        Python source for one missing-step skeleton.

    Responsibility:
        Render one inert missing-step skeleton. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.code_generator.rendering.render_missing_step_skeleton` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - make_string_literal: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `render_missing_step_skeleton`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return f"@not_implemented\n@{decorator}({make_string_literal(text)})\ndef _():\n    raise NotImplementedError\n"
