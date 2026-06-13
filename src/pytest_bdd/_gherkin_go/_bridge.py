"""
Own the ctypes bridge to the Go gherkin parser shared library: load platform-specific .so/.dll/.dylib, configure c.

Responsibility:
    Owns the ctypes bridge to the Go gherkin parser shared library: loads platform-specific .so/.dll/.dylib, configures
    ctypes function signatures, and provides Python wrapper functions. the single primary job, contract, or behavior
    this module directly implements and owns. This defines the boundary for where changes to this logic belong. Must be
    at least 140 characters.>

Reason for existence:
    Centralizes all ctypes-level interaction with the Go shared library so the rest of _gherkin_go calls high-level
    Python functions. why this code is kept together in this specific module rather than being merged elsewhere. Why is
    it the information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
    knowledge. Must be at least 140 characters.>

Delegates:
    - ctypes.CDLL: Loads the shared library. ctypes.c_char_p/c_void_p: Type annotations. Module-level _lib cache.

Cohesion:
    Every function serves the bridge pipeline: load library -> configure signatures -> provide wrapped Go calls. why all
    logic inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
    Share same imports and control flow? Or is it a bag of unrelated utilities?>

Separation:
    - _types: Kept separate because it defines exception types while _bridge handles low-level ctypes marshaling.

Main consumers:
    - _gherkin_go (parse, _check_go_available, _log_version): All import and call _bridge functions.

State and side effects:
    Loads native shared library from disk via ctypes.CDLL. Caches library handle in _lib. any local mutable state,
    file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source
    code. If stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - The shared library must exist at the expected platform-specific path. _lib is cached globally. the assumptions,
    data constraints, or execution rules that must always hold true for this entity and can never be broken. Analyze the
    actual source for implicit contracts.>

Failure semantics:
    _load_library raises OSError. _call_and_free raises RuntimeError for NULL pointers. what errors this entity raises
    (OSError, RuntimeError, re-raise) and how callers should handle them. Analyze the actual raise statements in the
    source.>

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
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
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Failure semantics:
        Raises OSError for unsupported platform, missing library, or ctypes.CDLL failure. what errors this entity raises
        (OSError, re-raise) and how callers should handle them. Analyze the actual raise statements in the source.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    global _lib, _lib_error  # noqa: PLW0603  -- module-level cache for shared library handle, reset on unload

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
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
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
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Failure semantics:
        Raises OSError for unsupported platform, missing library, or ctypes.CDLL failure. what errors this entity raises
        (RuntimeError) and how callers should handle them. Analyze the actual raise statements in the source.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
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
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    lib = _load_library()
    return _call_and_free(lib, lib.ParseGherkinDocument, text.encode("utf-8"))


def parse_gherkin_markdown(text: str) -> str:
    """
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    lib = _load_library()
    return _call_and_free(lib, lib.ParseGherkinMarkdown, text.encode("utf-8"))


def gherkin_go_version() -> str:
    """
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
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
    Load the platform-specific Go parser shared library via ctypes.CDLL, cache the handle, configure function signatur.

    Responsibility:
        Loads the platform-specific Go parser shared library via ctypes.CDLL, caches the handle, configures function
        signatures, raises OSError on failure. the single primary job, contract, or behavior this function directly
        implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140
        characters.>

    Reason for existence:
        Encapsulates platform-detection and ctypes-loading with caching so the library is loaded once per process. why
        this code is kept together in this specific function rather than being merged elsewhere. Why is it the
        information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
        knowledge. Must be at least 140 characters.>

    Delegates:
        - ctypes.CDLL: Loads native library. sys.platform + _PLATFORM_LIB_MAP: Platform detection.

    Cohesion:
        Single pipeline: check cache -> resolve lib name -> verify path -> load -> configure -> return. why all logic
        inside this entity belongs together. Analyze the actual source: do all functions operate on same local state?
        Share same imports and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - gherkin_go_available: Kept separate because it only checks availability while _load_library performs the actual load.

    Main consumers:
        - All other bridge functions: Call _load_library as the first step.

    State and side effects:
        Loads native shared library from disk. Sets module-level _lib and _lib_error. any local mutable state,
        file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual
        source code. If stateless, specify 'None, keeps no persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    global _lib, _lib_error  # noqa: PLW0603  -- reset module-level library handle cache on teardown
    _lib = None
    _lib_error = None
