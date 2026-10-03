from __future__ import annotations

import ctypes
from unittest.mock import MagicMock, patch

import pytest

from pytest_cuke._native_go._bridge import parse_gherkin_document
from pytest_cuke._native_go._types import NativeParserRuntimeError


def _native_library(return_value: int | None) -> tuple[MagicMock, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(b'{"feature":{"name":"\xd1\x82\xd0\xb5\xd1\x81\xd1\x82"}}')
    library = MagicMock()
    library.ParseGherkinDocument.return_value = return_value
    library.FreeCString = MagicMock()
    return library, buffer


def test_native_result_decodes_utf8_and_releases_pointer_once() -> None:
    buffer = ctypes.create_string_buffer('{"name":"тест"}'.encode("utf-8"))
    pointer = ctypes.cast(buffer, ctypes.c_void_p).value
    library, _ = _native_library(pointer)

    with patch("pytest_cuke._native_go._bridge._load_library", return_value=library):
        result = parse_gherkin_document("Feature: тест")

    assert result == '{"name":"тест"}'
    library.FreeCString.assert_called_once_with(pointer)


def test_native_result_preserves_utf8_byte_length_and_embedded_nul() -> None:
    buffer = ctypes.create_string_buffer(b"{}")
    pointer = ctypes.cast(buffer, ctypes.c_void_p).value
    library, _ = _native_library(pointer)

    with patch("pytest_cuke._native_go._bridge._load_library", return_value=library):
        parse_gherkin_document("Feature: т\x00ест")

    source, source_length = library.ParseGherkinDocument.call_args.args
    assert source == "Feature: т\x00ест".encode("utf-8")
    assert source_length == len(source)


def test_null_native_result_fails_without_freeing_null() -> None:
    library, _ = _native_library(None)

    with (
        patch("pytest_cuke._native_go._bridge._load_library", return_value=library),
        pytest.raises(NativeParserRuntimeError, match="NULL"),
    ):
        parse_gherkin_document("Feature: Test")

    library.FreeCString.assert_not_called()


def test_empty_native_result_fails_and_releases_pointer_once() -> None:
    buffer = ctypes.create_string_buffer(b"")
    pointer = ctypes.cast(buffer, ctypes.c_void_p).value
    library, _ = _native_library(pointer)

    with (
        patch("pytest_cuke._native_go._bridge._load_library", return_value=library),
        pytest.raises(NativeParserRuntimeError, match="empty"),
    ):
        parse_gherkin_document("Feature: Test")

    library.FreeCString.assert_called_once_with(pointer)


def test_invalid_utf8_native_result_fails_and_releases_pointer_once() -> None:
    buffer = ctypes.create_string_buffer(b"\xff")
    pointer = ctypes.cast(buffer, ctypes.c_void_p).value
    library, _ = _native_library(pointer)

    with (
        patch("pytest_cuke._native_go._bridge._load_library", return_value=library),
        pytest.raises(NativeParserRuntimeError, match="UTF-8"),
    ):
        parse_gherkin_document("Feature: Test")

    library.FreeCString.assert_called_once_with(pointer)
