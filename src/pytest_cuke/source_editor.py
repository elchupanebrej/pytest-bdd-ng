"""Transactional, append-only updates for generated step definitions."""

from __future__ import annotations

import difflib
import io
import os
import shutil
import stat
import subprocess
import tempfile
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class SourceEditError(RuntimeError):
    """A target source update could not be safely completed."""


class SourceFormatter(Protocol):
    def __call__(self, source: str, path: Path) -> str: ...


class SourceValidator(Protocol):
    def __call__(self, source: bytes, path: Path) -> None: ...


@dataclass(frozen=True)
class SourceEditResult:
    """Result of validating or applying a generated source update."""

    changed: bool
    diff: str = ""


def update_source_file(
    target: Path,
    addition: str,
    *,
    preview: bool = False,
    keep_on_error: bool = False,
    formatter: SourceFormatter | None = None,
    validator: SourceValidator | None = None,
) -> SourceEditResult:
    """Append generated source while preserving the original file bytes.

    The formatter sees only the generated fragment, so formatting never
    rewrites hand-authored source. The validator sees the complete candidate.
    The target is replaced atomically only after formatting and validation pass.
    """
    resolved_target = target.resolve(strict=True)
    if not resolved_target.is_file():
        raise SourceEditError(f"target is not a regular file: {target}")

    original = resolved_target.read_bytes()
    validate = validator or _validate_python
    try:
        validate(original, resolved_target)
    except Exception as error:
        raise SourceEditError(f"existing target is not valid Python: {error}") from error

    if not addition.strip():
        return SourceEditResult(changed=False)

    encoding = _detect_encoding(original, resolved_target)
    newline = _detect_newline(original)
    attempted = _append_fragment(original, addition, encoding, newline, resolved_target)
    candidate = attempted
    format_source = formatter or _format_with_ruff_if_available

    try:
        formatted = format_source(addition, resolved_target)
        candidate = _append_fragment(original, formatted, encoding, newline, resolved_target)
        validate(candidate, resolved_target)
    except Exception as error:
        if keep_on_error and candidate != original:
            _atomic_write(resolved_target, candidate)
        if isinstance(error, SourceEditError):
            raise
        if isinstance(error, SyntaxError):
            raise SourceEditError(f"generated source is invalid Python: {error}") from error
        raise SourceEditError(f"could not format or validate generated source: {error}") from error

    if candidate == original:
        return SourceEditResult(changed=False)

    diff = _source_diff(original, candidate, encoding, resolved_target)
    if not preview:
        _atomic_write(resolved_target, candidate)
    return SourceEditResult(changed=True, diff=diff)


def _detect_encoding(source: bytes, path: Path) -> str:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(source).readline)
    except (SyntaxError, UnicodeDecodeError) as error:
        raise SourceEditError(f"could not detect target encoding for {path}: {error}") from error
    return encoding


def _detect_newline(source: bytes) -> str:
    crlf = source.find(b"\r\n")
    lf = source.find(b"\n")
    cr = source.find(b"\r")
    candidates = [
        (position, newline) for position, newline in ((crlf, "\r\n"), (lf, "\n"), (cr, "\r")) if position >= 0
    ]
    return min(candidates, default=(0, "\n"), key=lambda pair: pair[0])[1]


def _encode_fragment(source: str, encoding: str, path: Path) -> bytes:
    normalized_encoding = encoding.lower().replace("_", "-")
    actual_encoding = "utf-8" if normalized_encoding == "utf-8-sig" else encoding
    try:
        return source.encode(actual_encoding)
    except (LookupError, UnicodeEncodeError) as error:
        raise SourceEditError(f"generated source cannot be encoded as {encoding} for {path}: {error}") from error


def _append_fragment(original: bytes, addition: str, encoding: str, newline: str, path: Path) -> bytes:
    normalized_addition = addition.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not normalized_addition.strip():
        return original
    newline_bytes = _encode_fragment(newline, encoding, path)
    if not original:
        separator = b""
    elif original.endswith((b"\n", b"\r")):
        separator = newline_bytes
    else:
        separator = newline_bytes * 2
    rendered = normalized_addition.replace("\n", newline) + newline
    return original + separator + _encode_fragment(rendered, encoding, path)


def _format_with_ruff_if_available(source: str, path: Path) -> str:
    executable = shutil.which("ruff")
    if executable is None:
        return source
    # The formatter is resolved from PATH and invoked with fixed arguments without a shell.
    result = subprocess.run(  # noqa: S603
        [executable, "format", "--stdin-filename", str(path), "-"],
        input=source,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        diagnostic = result.stderr.strip() or result.stdout.strip() or f"ruff exited with {result.returncode}"
        raise SourceEditError(f"ruff format failed: {diagnostic}")
    return result.stdout


def _validate_python(source: bytes, path: Path) -> None:
    compile(source, str(path), "exec")


def _source_diff(original: bytes, candidate: bytes, encoding: str, path: Path) -> str:
    actual_encoding = "utf-8" if encoding.lower().replace("_", "-") == "utf-8-sig" else encoding
    before = original.decode(actual_encoding)
    after = candidate.decode(actual_encoding)
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
    )


def _atomic_write(path: Path, content: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise SourceEditError(f"could not update {path}: {error}") from error


__all__ = ["SourceEditError", "SourceEditResult", "update_source_file"]
