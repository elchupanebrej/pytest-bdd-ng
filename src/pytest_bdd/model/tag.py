from __future__ import annotations

from attrs import frozen

from pytest_bdd.const import TAG_PREFIX


@frozen
class Tag:
    name: str
    line: int = 0
    id: str | None = None

    @property
    def clean_name(self) -> str:
        return self.name.lstrip(TAG_PREFIX)


__all__ = ["Tag"]
