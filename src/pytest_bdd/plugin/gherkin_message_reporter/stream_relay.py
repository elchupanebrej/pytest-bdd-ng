"""Provide stream relay helpers."""

from __future__ import annotations

import codecs
from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOBase


def relay_live_formatter_output(stream: TextIOBase, target: TextIOBase) -> None:
    """Handle relay live formatter output."""
    binary_stream = getattr(stream, "buffer", None)
    decoder_factory = codecs.getincrementaldecoder(stream.encoding or "utf-8")
    decoder = decoder_factory(errors=stream.errors or "strict")
    try:
        while True:
            if binary_stream is not None:
                # Some cucumber formatters update the terminal with carriage returns or
                # partial writes. Line-oriented relays stall those updates until EOF.
                read_chunk = getattr(binary_stream, "read1", binary_stream.read)
                chunk = read_chunk(4096)
                if not chunk:
                    break
                text = decoder.decode(chunk)
            else:
                text = stream.read(1)
                if not text:
                    break
            if not text:
                continue
            try:
                target.write(text)
                target.flush()
            except OSError:
                break
        final_text = decoder.decode(b"", final=True) if binary_stream is not None else ""
        if final_text:
            with suppress(OSError):
                target.write(final_text)
                target.flush()
    finally:
        with suppress(OSError, ValueError):
            stream.close()
