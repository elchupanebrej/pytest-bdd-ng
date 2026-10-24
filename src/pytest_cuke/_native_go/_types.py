"""Errors raised by the optional native Gherkin parser."""

from __future__ import annotations

from typing import Any


class NativeParserError(RuntimeError):
    """Base class for failures originating in the native parser backend."""


class NativeParserUnavailable(NativeParserError):
    """The optional Go shared library is absent or cannot be loaded."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            "Go parser is unavailable: "
            f"{reason}. To use --cuke-parser=go, install Go and a C compiler, then build or reinstall pytest-cuke; "
            "or select --cuke-parser=python / set cuke_parser=python."
        )
        self.reason = reason


class NativeParserRuntimeError(NativeParserError):
    """The Go bridge returned invalid or incomplete output."""


class NativeParserSyntaxError(NativeParserError):
    """The Go parser rejected Gherkin input as malformed."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        messages = "; ".join(str(error.get("message", error)) for error in errors)
        super().__init__(messages or "Go Gherkin parser rejected the input")


class NativeParserCompatibilityError(NativeParserError):
    """The native parser output does not match the Python parser contract."""


__all__ = [
    "NativeParserCompatibilityError",
    "NativeParserError",
    "NativeParserRuntimeError",
    "NativeParserSyntaxError",
    "NativeParserUnavailable",
]
