"""Low-level ctypes bridge to the Go gherkin parser shared library."""

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
    """Check if the Go shared library is loadable."""
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

    """
    lib = _load_library()
    return _call_and_free(lib, lib.ParseGherkinMarkdown, text.encode("utf-8"))


def gherkin_go_version() -> str:
    """Return the Go gherkin parser version string."""
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
    """Reset library state for testing. Not for production use."""
    global _lib, _lib_error  # noqa: PLW0603
    _lib = None
    _lib_error = None
