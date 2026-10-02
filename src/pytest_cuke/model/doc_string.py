from __future__ import annotations

from attrs import frozen


@frozen
class DocString:
    content: str
    media_type: str | None = None
    line: int = 0
    id: str | None = None


__all__ = ["DocString"]
