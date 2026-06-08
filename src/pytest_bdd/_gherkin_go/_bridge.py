"""
Low-level ctypes bridge to the Go gherkin parser shared library.

Responsibility:
    Low-level ctypes bridge to the Go gherkin parser shared library. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._gherkin_go._bridge` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - _load_library: owns nested behavior below this boundary
    - gherkin_go_available: owns nested behavior below this boundary
    - _call_and_free: owns nested behavior below this boundary
    - parse_gherkin_document: owns nested behavior below this boundary
    - parse_gherkin_markdown: owns nested behavior below this boundary
    - gherkin_go_version: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `_bridge`

State and side effects:
    mutates _lib_error, _lib, lib, result, logger; depends on __future__.annotations, ctypes, logging, sys,
    pathlib.Path.

Invariants:
    - `pytest_bdd._gherkin_go._bridge` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises OSError, RuntimeError, re-raise; callers must treat these as boundary failures.

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

import ctypes
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_lib: ctypes.CDLL | None = None
_lib_error: str | None = None

# Map sys.platform to shared library filename
_PLATFORM_LIB_MAP = {
    "linux": "libgherkin_go.so",
    "win32": "gherkin_go.dll",
    "darwin": "libgherkin_go.dylib",
}


def _load_library() -> ctypes.CDLL:
    """
    Load the Go shared library from package data.

    Returns:
        Loaded CDLL instance.

    Raises:
        OSError: If the library cannot be loaded.

    Responsibility:
        Load the Go shared library from package data. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge._load_library` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - OSError: collaborator call used by this boundary
        - _PLATFORM_LIB_MAP.get: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - lib_path.exists: collaborator call used by this boundary
        - ctypes.CDLL: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `_load_library`

    State and side effects:
        mutates _lib_error, lib_name, package_dir, lib_path, _lib.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge._load_library` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises OSError, re-raise; callers must treat these as boundary failures.

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
    global _lib, _lib_error  # noqa: PLW0603

    if _lib is not None:
        return _lib
    if _lib_error is not None:
        raise OSError(_lib_error)

    lib_name = _PLATFORM_LIB_MAP.get(sys.platform)
    if lib_name is None:
        _lib_error = f"Unsupported platform: {sys.platform}"
        raise OSError(_lib_error)

    # Search in the package directory
    package_dir = Path(__file__).parent
    lib_path = package_dir / lib_name

    if not lib_path.exists():
        _lib_error = f"Shared library not found: {lib_path}"
        raise OSError(_lib_error)

    try:
        _lib = ctypes.CDLL(str(lib_path))
    except OSError as exc:
        _lib_error = f"Failed to load {lib_path}: {exc}"
        raise

    # Configure function signatures
    _lib.ParseGherkinDocument.argtypes = [ctypes.c_char_p]
    _lib.ParseGherkinDocument.restype = ctypes.c_void_p

    _lib.ParseGherkinMarkdown.argtypes = [ctypes.c_char_p]
    _lib.ParseGherkinMarkdown.restype = ctypes.c_void_p

    _lib.FreeCString.argtypes = [ctypes.c_void_p]
    _lib.FreeCString.restype = None

    _lib.Version.argtypes = []
    _lib.Version.restype = ctypes.c_void_p

    return _lib


def gherkin_go_available() -> bool:
    """
    Check if the Go shared library is loadable.

    Responsibility:
        Check if the Go shared library is loadable. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge.gherkin_go_available` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_library: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `gherkin_go_available`

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
    try:
        _load_library()
    except OSError:
        return False
    else:
        return True


_NULL_POINTER_MSG = "Go parser returned NULL pointer"
_EMPTY_RESULT_MSG = "Go parser returned empty result"


def _call_and_free(lib: ctypes.CDLL, func: Any, *args: Any) -> str:
    """
    Call a Go C-exported function and manage memory.

    Args:
        lib: Loaded CDLL instance.
        func: The ctypes function wrapper to call.
        *args: Arguments to pass to the function.

    Returns:
        The decoded UTF-8 string result.

    Raises:
        RuntimeError: If the function returns NULL or an empty result.

    Responsibility:
        Call a Go C-exported function and manage memory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge._call_and_free` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - RuntimeError: collaborator call used by this boundary
        - func: collaborator call used by this boundary
        - ctypes.cast: collaborator call used by this boundary
        - result.decode: collaborator call used by this boundary
        - lib.FreeCString: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `_call_and_free`

    State and side effects:
        mutates ptr, result.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge._call_and_free` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
    ptr = func(*args)
    if not ptr:
        raise RuntimeError(_NULL_POINTER_MSG)
    try:
        result = ctypes.cast(ptr, ctypes.c_char_p).value
        if result is None:
            raise RuntimeError(_EMPTY_RESULT_MSG)
        return result.decode("utf-8")
    finally:
        lib.FreeCString(ptr)


def parse_gherkin_document(text: str) -> str:
    """
    Parse plain Gherkin text via Go parser.

    Args:
        text: Gherkin feature file content.

    Returns:
        JSON string — either a GherkinDocument object or an error array.

    Responsibility:
        Parse plain Gherkin text via Go parser. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge.parse_gherkin_document` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_library: collaborator call used by this boundary
        - _call_and_free: collaborator call used by this boundary
        - text.encode: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse_gherkin_document`
        - src/pytest_bdd/script/validate_feature_headings.py: imports or references `parse_gherkin_document`

    State and side effects:
        mutates lib.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge.parse_gherkin_document` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    lib = _load_library()
    return _call_and_free(lib, lib.ParseGherkinDocument, text.encode("utf-8"))


def parse_gherkin_markdown(text: str) -> str:
    """
    Parse Markdown Gherkin text via Go parser.

    Args:
        text: Markdown feature file content.

    Returns:
        JSON string — either a GherkinDocument object or an error array.

    Responsibility:
        Parse Markdown Gherkin text via Go parser. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge.parse_gherkin_markdown` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_library: collaborator call used by this boundary
        - _call_and_free: collaborator call used by this boundary
        - text.encode: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse_gherkin_markdown`

    State and side effects:
        mutates lib.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge.parse_gherkin_markdown` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    lib = _load_library()
    return _call_and_free(lib, lib.ParseGherkinMarkdown, text.encode("utf-8"))


def gherkin_go_version() -> str:
    """
    Return the Go gherkin parser version string.

    Responsibility:
        Return the Go gherkin parser version string. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge.gherkin_go_version` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _load_library: collaborator call used by this boundary
        - lib.Version: collaborator call used by this boundary
        - ctypes.cast: collaborator call used by this boundary
        - raw.decode: collaborator call used by this boundary
        - lib.FreeCString: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `gherkin_go_version`

    State and side effects:
        mutates lib, result, raw.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge.gherkin_go_version` keeps its documented import path, ownership boundary, and
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
    lib = _load_library()
    result = lib.Version()
    if not result:
        return "unknown"
    try:
        raw = ctypes.cast(result, ctypes.c_char_p).value
        if raw is None:
            return "unknown"
        return raw.decode("utf-8")
    finally:
        lib.FreeCString(result)


def _reset() -> None:
    """
    Reset library state for testing. Not for production use.

    Responsibility:
        Reset library state for testing. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._bridge._reset` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `_reset`

    State and side effects:
        mutates _lib, _lib_error.

    Invariants:
        - `pytest_bdd._gherkin_go._bridge._reset` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    global _lib, _lib_error  # noqa: PLW0603
    _lib = None
    _lib_error = None
