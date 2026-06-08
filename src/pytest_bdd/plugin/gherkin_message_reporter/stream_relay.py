"""
Provide stream relay helpers.

Responsibility:
    Provide stream relay helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.stream_relay` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _read_chunk: owns nested behavior below this boundary
    - _drain_to_target: owns nested behavior below this boundary
    - _write_final_text: owns nested behavior below this boundary
    - relay_live_formatter_output: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `stream_relay`

State and side effects:
    mutates text, read_chunk, chunk, final_text, binary_stream; depends on __future__.annotations, codecs,
    contextlib.suppress, typing.IO, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.stream_relay` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

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

import codecs
from contextlib import suppress
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOBase


def _read_chunk(decoder: codecs.IncrementalDecoder, binary_stream: IO[bytes] | None, stream: TextIOBase) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._read_chunk` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._read_chunk`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - read_chunk: collaborator call used by this boundary
        - decoder.decode: collaborator call used by this boundary
        - stream.read: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `_read_chunk`

    State and side effects:
        mutates read_chunk, chunk, text.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._read_chunk` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._drain_to_target` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._drain_to_target` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _read_chunk: collaborator call used by this boundary
        - target.write: collaborator call used by this boundary
        - target.flush: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_drain_to_target`

    State and side effects:
        mutates text.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._drain_to_target` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._write_final_text` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._write_final_text` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - decoder.decode: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - target.write: collaborator call used by this boundary
        - target.flush: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_write_final_text`

    State and side effects:
        mutates final_text.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.stream_relay._write_final_text` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    final_text = decoder.decode(b"", final=True) if binary_stream is not None else ""
    if not final_text:
        return
    with suppress(OSError):
        target.write(final_text)
        target.flush()


def relay_live_formatter_output(stream: TextIOBase, target: TextIOBase) -> None:
    """
    Handle relay live formatter output.

    Responsibility:
        Handle relay live formatter output. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.stream_relay.relay_live_formatter_output` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - codecs.getincrementaldecoder: collaborator call used by this boundary
        - decoder_factory: collaborator call used by this boundary
        - _drain_to_target: collaborator call used by this boundary
        - _write_final_text: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `relay_live_formatter_output`

    State and side effects:
        mutates binary_stream, decoder_factory, decoder.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.stream_relay.relay_live_formatter_output` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    binary_stream: IO[bytes] | None = getattr(stream, "buffer", None)
    decoder_factory = codecs.getincrementaldecoder(stream.encoding or "utf-8")
    decoder = decoder_factory(errors=stream.errors or "strict")
    try:
        _drain_to_target(target, stream, decoder, binary_stream)
        _write_final_text(target, decoder, binary_stream)
    finally:
        with suppress(OSError, ValueError):
            stream.close()
