# init: allow  # init: no-check
"""
Public API for the Go gherkin parser backend.

Provides parse() function that mirrors gherkin.parser.Parser().parse() output.

Responsibility:
    Public API for the Go gherkin parser backend. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._gherkin_go` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - _get_parser: owns nested behavior below this boundary
    - _check_go_available: owns nested behavior below this boundary
    - should_use_go_backend: owns nested behavior below this boundary
    - is_strict_go_mode: owns nested behavior below this boundary
    - _log_version: owns nested behavior below this boundary
    - parse: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `_gherkin_go`

State and side effects:
    mutates _go_version_logged, backend, logger, _GO_INSTALL_HINT, msg; depends on __future__.annotations, json,
    logging, os, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd._gherkin_go` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Failure semantics:
    Raises or re-raises GherkinGoNotAvailable, GherkinParseError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, cast

from pytest_bdd._gherkin_go._bridge import gherkin_go_available as gherkin_go_available
from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError
from pytest_bdd.mimetype import Mimetype

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

_go_version_logged = False

_GO_INSTALL_HINT = (
    "PYTEST_BDD_GHERKIN_BACKEND=go but go-parser not installed. Install with: pip install pytest-bdd-ng[go-parser]"
)


def _get_parser() -> Callable[[str, str], dict[str, object]]:
    """
    Return parse() callable — Go or Python fallback.

    Resolves the parser backend based on PYTEST_BDD_GHERKIN_BACKEND env var:
    - ``go``: Go parser required; raises ImportError if unavailable
    - ``python``: Python gherkin.parser.Parser fallback
    - ``auto`` (default): Go parser if available, Python fallback otherwise

    Returns a callable with signature ``(text: str, uri: str = "<string>") -> dict``.

    Responsibility:
        Return parse() callable — Go or Python fallback. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._get_parser` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _python_parse_auto: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `_get_parser`

    State and side effects:
        mutates backend; depends on pytest_bdd._gherkin_go.parse, gherkin.parser.Parser,
        pytest_bdd._gherkin_go._bridge.gherkin_go_available, pytest_bdd._gherkin_go.parse, gherkin.parser.Parser.

    Invariants:
        - `pytest_bdd._gherkin_go._get_parser` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()

    if backend == "go":
        _check_go_available()  # noqa: PLC0415
        from pytest_bdd._gherkin_go import parse as go_parse  # noqa: PLC0415

        return go_parse

    if backend == "python":
        from gherkin.parser import Parser as GherkinParser  # noqa: PLC0415

        logger.debug("Using Python gherkin parser (PYTEST_BDD_GHERKIN_BACKEND=python)")

        def _python_parse_backend(text: str, uri: str = "<string>") -> dict[str, object]:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd._gherkin_go._get_parser._python_parse` owns documented
                function behavior. It directly owns the observable contract, local decisions, and maintenance boundary
                for this function.

            Reason for existence:
                This entity is the information expert for `pytest_bdd._gherkin_go._get_parser._python_parse_backend`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - cast: collaborator call used by this boundary
                - GherkinParser.parse: collaborator call used by this boundary
                - GherkinParser: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/collector_batch.py: imports or references `_python_parse_backend`

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
            # noqa: ARG001
            return cast("dict[str, object]", GherkinParser().parse(text))

        return _python_parse_backend

    # auto or unknown value
    if backend != "auto":
        logger.warning("Unknown PYTEST_BDD_GHERKIN_BACKEND value '%s', treating as 'auto'", backend)

    try:
        from pytest_bdd._gherkin_go._bridge import gherkin_go_available  # noqa: PLC0415

        if gherkin_go_available():
            from pytest_bdd._gherkin_go import parse as go_parse  # noqa: PLC0415

            logger.info("Using Go gherkin parser backend")
            return go_parse
    except ImportError:
        pass

    logger.debug("Go gherkin parser unavailable, using Python fallback")
    from gherkin.parser import Parser as GherkinParser  # noqa: PLC0415

    def _python_parse_auto(text: str, uri: str = "<string>") -> dict[str, object]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._get_parser._python_parse` owns documented function
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._get_parser._python_parse_auto` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - GherkinParser.parse: collaborator call used by this boundary
            - GherkinParser: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `_python_parse_auto`

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
        return cast("dict[str, object]", GherkinParser().parse(text))

    return _python_parse_auto


def _check_go_available() -> None:
    """
    Check Go parser availability.

    Raises:
        GherkinGoNotAvailable: When Go shared library is not found, with an install hint.

    Responsibility:
        Check Go parser availability. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._check_go_available` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - gherkin_go_available: collaborator call used by this boundary
        - GherkinGoNotAvailable: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `_check_go_available`

    State and side effects:
        depends on pytest_bdd._gherkin_go._bridge.gherkin_go_available.

    Failure semantics:
        Raises or re-raises GherkinGoNotAvailable; callers must treat these as boundary failures.

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
    from pytest_bdd._gherkin_go._bridge import gherkin_go_available  # noqa: PLC0415

    if not gherkin_go_available():
        raise GherkinGoNotAvailable(_GO_INSTALL_HINT)


def should_use_go_backend() -> bool:
    """
    Check if Go backend should be attempted based on env var (single source of truth).

    Responsibility:
        Check if Go backend should be attempted based on env var (single source of truth). It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go.should_use_go_backend` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - os.environ.get.lower: collaborator call used by this boundary
        - os.environ.get: collaborator call used by this boundary
        - logger.warning: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `should_use_go_backend`

    State and side effects:
        mutates backend.

    Invariants:
        - `pytest_bdd._gherkin_go.should_use_go_backend` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()
    if backend == "python":
        return False
    if backend not in {"auto", "go"}:
        logger.warning("Unknown PYTEST_BDD_GHERKIN_BACKEND value '%s', treating as 'auto'", backend)
    return True


def is_strict_go_mode() -> bool:
    """
    Check if Go backend is forced — no fallback to Python.

    Responsibility:
        Check if Go backend is forced — no fallback to Python. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go.is_strict_go_mode` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - os.environ.get.lower: collaborator call used by this boundary
        - os.environ.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `is_strict_go_mode`

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
    return os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower() == "go"


def _log_version() -> None:
    """
    Log the Go parser version on first successful use.

    Responsibility:
        Log the Go parser version on first successful use. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._log_version` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - logger.info: collaborator call used by this boundary
        - gherkin_go_version: collaborator call used by this boundary
        - logger.debug: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `_log_version`

    State and side effects:
        mutates _go_version_logged; depends on pytest_bdd._gherkin_go._bridge.gherkin_go_version.

    Invariants:
        - `pytest_bdd._gherkin_go._log_version` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    global _go_version_logged
    if _go_version_logged:
        return
    _go_version_logged = True
    try:
        from pytest_bdd._gherkin_go._bridge import gherkin_go_version  # noqa: PLC0415

        logger.info("Using Go gherkin parser %s", gherkin_go_version())
    except Exception:  # noqa: BLE001
        logger.debug("Failed to retrieve Go parser version", exc_info=True)


def parse(text: str, uri: str = "<string>") -> dict[str, object]:
    """
    Parse Gherkin text using Go parser, returning dict identical to Python Parser().parse().

    Args:
        text: Gherkin (or Markdown+Gherkin) feature content.
        uri: Source URI; suffix ``.md`` or ``.feature.md`` selects markdown mode.

    Returns:
        Dict with ``'type': 'GherkinDocument'`` and ``'feature'`` key.

    Raises:
        GherkinParseError: On invalid Gherkin syntax.
        GherkinGoNotAvailable: When Go parser is unavailable.

    Responsibility:
        Parse Gherkin text using Go parser, returning dict identical to Python Parser().parse(). It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go.parse` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - gherkin_go_available: collaborator call used by this boundary
        - logger.warning: collaborator call used by this boundary
        - GherkinGoNotAvailable: collaborator call used by this boundary
        - uri.endswith: collaborator call used by this boundary
        - parse_gherkin_markdown: collaborator call used by this boundary
        - parse_gherkin_document: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
        - src/pytest_bdd/collector_batch.py: imports or references `parse`
        - src/pytest_bdd/hook.py: imports or references `parse`
        - src/pytest_bdd/parser.py: imports or references `parse`
        - src/pytest_bdd/parsers/__init__.py: imports or references `parse`

    State and side effects:
        mutates msg, json_str, result; depends on pytest_bdd._gherkin_go._bridge.gherkin_go_available,
        pytest_bdd._gherkin_go._bridge.parse_gherkin_document, pytest_bdd._gherkin_go._bridge.parse_gherkin_markdown.

    Invariants:
        - `pytest_bdd._gherkin_go.parse` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Failure semantics:
        Raises or re-raises GherkinGoNotAvailable, GherkinParseError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    from pytest_bdd._gherkin_go._bridge import gherkin_go_available, parse_gherkin_document, parse_gherkin_markdown

    if not gherkin_go_available():
        msg = "Go shared library not found in package data"
        logger.warning("Go gherkin parser unavailable (%s)", msg)
        raise GherkinGoNotAvailable(msg)

    json_str = parse_gherkin_markdown(text) if uri.endswith(".md") else parse_gherkin_document(text)

    result = json.loads(json_str)
    if not isinstance(result, dict):
        raise GherkinParseError(result)

    _log_version()
    return result
