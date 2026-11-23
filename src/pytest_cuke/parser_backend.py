"""Resolve and coordinate Gherkin parser backends."""

from __future__ import annotations

import json
import logging
import re
import warnings
from enum import Enum
from typing import Any, cast

from pytest_cuke.exceptions import FeatureConcreteParseError

logger = logging.getLogger(__name__)

_SYNTAX_LOCATION = re.compile(r"\((?P<line>\d+):(?P<column>\d+)\):")


class ParserBackend(str, Enum):
    """Supported Gherkin parser selection modes."""

    AUTO = "auto"
    GO = "go"
    PYTHON = "python"

    def __str__(self) -> str:
        return self.value


def resolve_parser_backend(config: Any = None) -> ParserBackend:
    """Resolve CLI-over-ini parser configuration, treating unknown values as auto."""
    value: Any = None
    if config is not None:
        getoption = getattr(config, "getoption", None)
        if callable(getoption):
            try:
                value = getoption("cuke_parser")
            except (AttributeError, KeyError, ValueError):
                value = None
        if value is None:
            getini = getattr(config, "getini", None)
            if callable(getini):
                try:
                    value = getini("cuke_parser")
                except (AttributeError, KeyError, ValueError):
                    value = None

    return normalize_parser_backend(value)


def normalize_parser_backend(value: Any) -> ParserBackend:
    """Normalize a selector value, warning and using auto for unsupported strings."""
    normalized = str(value or ParserBackend.AUTO.value).strip().lower()
    try:
        return ParserBackend(normalized)
    except ValueError:
        diagnostic = f"Unknown cuke_parser value {value!r}; using auto parser selection"
        logger.warning(diagnostic)
        warnings.warn(diagnostic, UserWarning, stacklevel=2)
        return ParserBackend.AUTO


def parse_gherkin_document(
    content: str,
    backend: ParserBackend | str | None,
    *,
    markdown: bool,
    python_parser: Any,
    uri: str = "",
) -> dict[str, Any]:
    """Parse Gherkin with the selected backend, preserving Python semantics on fallback."""
    selected_backend = normalize_parser_backend(backend)
    if selected_backend is ParserBackend.PYTHON:
        return cast("dict[str, Any]", python_parser())

    try:
        native_document = _parse_native_document(content, markdown=markdown)
    except Exception as exc:
        from pytest_cuke._native_go._types import (  # noqa: PLC0415
            NativeParserCompatibilityError,
            NativeParserError,
            NativeParserSyntaxError,
        )

        if isinstance(exc, NativeParserSyntaxError):
            if markdown and selected_backend is ParserBackend.GO:
                # Markdown parses natively in every mode, so report Go's own location.
                raise _markdown_syntax_error(exc, content, uri) from exc
            # Reparse through the canonical Python parser to preserve its source location.
            python_document = cast("dict[str, Any]", python_parser())
            if selected_backend is ParserBackend.GO:
                raise NativeParserCompatibilityError(
                    f"Go parser rejected input accepted by the Python parser: {exc}"
                ) from exc
            _warn_fallback(f"native parser rejected input that Python accepts: {exc}")
            return python_document
        if isinstance(exc, NativeParserError) and selected_backend is ParserBackend.GO:
            raise
        if selected_backend is ParserBackend.GO:
            raise NativeParserError(f"Go parser failed: {exc}") from exc
        _warn_fallback(str(exc) or type(exc).__name__)
        return cast("dict[str, Any]", python_parser())

    return native_document


def _parse_native_document(content: str, *, markdown: bool) -> dict[str, Any]:
    """Import and invoke the ctypes adapter only after native parsing is selected."""
    from pytest_cuke._native_go._types import (  # noqa: PLC0415
        NativeParserRuntimeError,
        NativeParserSyntaxError,
        NativeParserUnavailable,
    )

    try:
        if markdown:
            from pytest_cuke._native_go._bridge import parse_gherkin_markdown  # noqa: PLC0415

            encoded_result = parse_gherkin_markdown(content)
        else:
            from pytest_cuke._native_go._bridge import parse_gherkin_document as parse_plain  # noqa: PLC0415

            encoded_result = parse_plain(content)
    except OSError as exc:
        raise NativeParserUnavailable(str(exc)) from exc
    except NativeParserRuntimeError:
        raise
    except Exception as exc:
        raise NativeParserRuntimeError(f"native bridge failed: {exc}") from exc

    try:
        payload = json.loads(encoded_result)
    except (json.JSONDecodeError, TypeError) as exc:
        raise NativeParserRuntimeError(f"native bridge returned invalid JSON: {exc}") from exc

    if isinstance(payload, list):
        if all(isinstance(item, dict) and "message" in item for item in payload):
            raise NativeParserSyntaxError(cast("list[dict[str, Any]]", payload))
        raise NativeParserRuntimeError("native bridge returned an unexpected JSON array")
    if not isinstance(payload, dict):
        raise NativeParserRuntimeError("native bridge returned a non-object document")
    if payload.get("errorType") == "syntax":
        errors = payload.get("errors")
        if not isinstance(errors, list) or not all(isinstance(item, dict) for item in errors):
            raise NativeParserRuntimeError("native syntax error payload is malformed")
        raise NativeParserSyntaxError(cast("list[dict[str, Any]]", errors))
    if payload.get("errorType"):
        raise NativeParserRuntimeError(str(payload.get("message") or "native parser reported an internal error"))

    feature = payload.get("feature")
    if not isinstance(feature, dict):
        raise NativeParserRuntimeError("native parser returned a null or empty Feature")
    _normalize_null_collections(payload)
    return payload


def _normalize_null_collections(value: Any) -> None:
    """Make native nil slices compatible with the Python AST-to-model converter."""
    array_fields = {"children", "tags", "steps", "examples", "tableBody", "cells", "rows", "comments"}
    if isinstance(value, dict):
        for key, child in tuple(value.items()):
            if child is None and key in array_fields:
                value[key] = []
            else:
                _normalize_null_collections(child)
    elif isinstance(value, list):
        for child in value:
            _normalize_null_collections(child)


def _markdown_syntax_error(exc: Any, content: str, uri: str) -> FeatureConcreteParseError:
    """Rebuild a Go Markdown syntax error with the Python parser's location fields."""
    message = str(exc)
    location = _SYNTAX_LOCATION.search(message)
    line = int(location["line"]) if location else 0
    column = max(int(location["column"]), 1) if location else 1
    lines = content.splitlines()
    line_text = lines[line - 1] if 1 <= line <= len(lines) else ""
    return FeatureConcreteParseError(message, line, line_text, uri, column=column)


def _warn_fallback(reason: str) -> None:
    diagnostic = f"Go parser fallback ({reason}); falling back to Python"
    logger.warning(diagnostic)
    warnings.warn(diagnostic, RuntimeWarning, stacklevel=3)


__all__ = ["ParserBackend", "normalize_parser_backend", "parse_gherkin_document", "resolve_parser_backend"]
