"""Provide stream relay helpers."""

from __future__ import annotations

import codecs
from contextlib import suppress
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOBase


def _read_chunk(decoder: codecs.IncrementalDecoder, binary_stream: IO[bytes] | None, stream: TextIOBase) -> str:
    if binary_stream is not None:
        # Some cucumber formatters update the terminal with carriage returns or
        # partial writes. Line-oriented relays stall those updates until EOF.
        read_chunk = getattr(binary_stream, "read1", binary_stream.read)
        chunk = read_chunk(4096)
        if not chunk:
            return ""
        return decoder.decode(chunk)
    text = stream.read(1)
    return text or ""


def _drain_to_target(
    target: TextIOBase,
    source: TextIOBase,
    decoder: codecs.IncrementalDecoder,
    binary_stream: IO[bytes] | None,
) -> None:
    while True:
        text = _read_chunk(decoder, binary_stream, source)
        if not text:
            return
        try:
            target.write(text)
            target.flush()
        except OSError:
            return


def _write_final_text(
    target: TextIOBase,
    decoder: codecs.IncrementalDecoder,
    binary_stream: IO[bytes] | None,
) -> None:
    final_text = decoder.decode(b"", final=True) if binary_stream is not None else ""
    if not final_text:
        return
    with suppress(OSError):
        target.write(final_text)
        target.flush()


def relay_live_formatter_output(stream: TextIOBase, target: TextIOBase) -> None:
    """Handle relay live formatter output."""
    binary_stream: IO[bytes] | None = getattr(stream, "buffer", None)
    decoder_factory = codecs.getincrementaldecoder(stream.encoding or "utf-8")
    decoder = decoder_factory(errors=stream.errors or "strict")
    try:
        _drain_to_target(target, stream, decoder, binary_stream)
        _write_final_text(target, decoder, binary_stream)
    finally:
        with suppress(OSError, ValueError):
            stream.close()
