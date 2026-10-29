"""Low-level ctypes bridge to the optional Go Gherkin parser library."""

from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path
from threading import RLock
from typing import Any

from pytest_cuke._native_go._types import NativeParserRuntimeError

logger = logging.getLogger(__name__)

_PLATFORM_LIB_MAP = {
    "linux": "libgherkin_go.so",
    "win32": "gherkin_go.dll",
    "darwin": "libgherkin_go.dylib",
}
_lib: ctypes.CDLL | None = None
_lib_error: str | None = None
_load_lock = RLock()


def _load_library() -> ctypes.CDLL:
    """Load and configure the packaged Go shared library once per process."""
    global _lib, _lib_error  # noqa: PLW0603
    with _load_lock:
        if _lib is not None:
            return _lib
        if _lib_error is not None:
            raise OSError(_lib_error)

        lib_name = _PLATFORM_LIB_MAP.get(sys.platform)
        if lib_name is None:
            _lib_error = f"unsupported platform: {sys.platform}"
            raise OSError(_lib_error)

        lib_path = Path(__file__).parent / lib_name
        if not lib_path.is_file():
            _lib_error = f"shared library not found: {lib_path}"
            raise OSError(_lib_error)

        try:
            library = ctypes.CDLL(str(lib_path))
            for function_name in ("ParseGherkinDocument", "ParseGherkinMarkdown"):
                function = getattr(library, function_name)
                function.argtypes = [ctypes.c_char_p, ctypes.c_int]
                function.restype = ctypes.c_void_p
            library.FreeCString.argtypes = [ctypes.c_void_p]
            library.FreeCString.restype = None
            library.Version.argtypes = []
            library.Version.restype = ctypes.c_void_p
        except (AttributeError, OSError) as exc:
            _lib_error = f"failed to load {lib_path}: {exc}"
            raise OSError(_lib_error) from exc

        _lib = library
        return library


def gherkin_go_available() -> bool:
    """Return whether this process can load the packaged Go parser."""
    try:
        _load_library()
    except OSError:
        return False
    return True


def _call_and_free(library: ctypes.CDLL, function: Any, *args: Any) -> str:
    pointer = function(*args)
    pointer_value = pointer.value if isinstance(pointer, ctypes.c_void_p) else pointer
    if not pointer_value:
        raise NativeParserRuntimeError("Go parser returned a NULL pointer")

    try:
        raw_result = ctypes.string_at(pointer_value)
        if not raw_result:
            raise NativeParserRuntimeError("Go parser returned an empty result")
        try:
            return raw_result.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise NativeParserRuntimeError("Go parser result is not valid UTF-8") from exc
    finally:
        library.FreeCString(pointer_value)


def _parse(function_name: str, text: str) -> str:
    library = _load_library()
    encoded = text.encode("utf-8")
    function = getattr(library, function_name)
    return _call_and_free(library, function, encoded, len(encoded))


def parse_gherkin_document(text: str) -> str:
    """Parse plain Gherkin and return its Cucumber Messages JSON document."""
    return _parse("ParseGherkinDocument", text)


def parse_gherkin_markdown(text: str) -> str:
    """Parse Markdown containing Gherkin and return its Messages JSON document."""
    return _parse("ParseGherkinMarkdown", text)


def gherkin_go_version() -> str:
    """Return the packaged Gherkin Go parser version, or ``unknown``."""
    library = _load_library()
    pointer = library.Version()
    pointer_value = pointer.value if isinstance(pointer, ctypes.c_void_p) else pointer
    if not pointer_value:
        return "unknown"
    try:
        raw_result = ctypes.string_at(pointer_value)
        if not raw_result:
            return "unknown"
        return raw_result.decode("utf-8")
    except (NativeParserRuntimeError, UnicodeDecodeError):
        logger.debug("Go parser returned an invalid version string", exc_info=True)
        return "unknown"
    finally:
        library.FreeCString(pointer_value)


def _reset() -> None:
    """Clear cached loader state for isolated tests."""
    global _lib, _lib_error  # noqa: PLW0603
    with _load_lock:
        _lib = None
        _lib_error = None


__all__ = [
    "gherkin_go_available",
    "gherkin_go_version",
    "parse_gherkin_document",
    "parse_gherkin_markdown",
]
