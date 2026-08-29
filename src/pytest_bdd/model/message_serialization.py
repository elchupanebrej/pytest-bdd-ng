from __future__ import annotations

import json
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from pytest_bdd.model.message_converter import envelope_from_dict, envelope_to_dict, validate_envelope_shape

if TYPE_CHECKING:
    from collections.abc import Iterable

    import messages


def serialize_envelope(envelope: messages.Envelope) -> str:
    validate_envelope_shape(envelope)
    return json.dumps(envelope_to_dict(envelope))


def deserialize_envelope(data: str | dict[str, Any]) -> messages.Envelope:
    return envelope_from_dict(json.loads(data) if isinstance(data, str) else data)


def dump_ndjson(envelopes: Iterable[messages.Envelope], target: IO[str] | Path | str | None = None) -> str:
    lines = [serialize_envelope(env) for env in envelopes]
    ndjson_str = "\n".join(lines) + ("\n" if lines else "")
    if target is not None:
        if isinstance(target, str | Path):
            Path(target).write_text(ndjson_str, encoding="utf-8")
        else:
            target.write(ndjson_str)
    return ndjson_str


def load_ndjson(source: IO[str] | Path | str) -> list[messages.Envelope]:
    if isinstance(source, Path):
        content = source.read_text(encoding="utf-8")
    elif isinstance(source, str):
        content = source
        if "\n" not in source and "\r" not in source:
            try:
                p = Path(source)
                if p.is_file():
                    content = p.read_text(encoding="utf-8")
            except (OSError, ValueError):
                pass
    else:
        content = source.read()
    return [deserialize_envelope(line.strip()) for line in content.splitlines() if line.strip()]


__all__ = ["deserialize_envelope", "dump_ndjson", "load_ndjson", "serialize_envelope"]
