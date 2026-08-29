from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar

from attrs import define

T = TypeVar("T")


@define(slots=True, frozen=True)
class StashKey(Generic[T]):
    name: str
    description: str = ""

    def __repr__(self) -> str:
        return f"<StashKey {self.name!r}>"


class SimpleStash:
    """Dict-backed pure stash storage when pytest Stash is not used."""

    def __init__(self, initial: dict[Any, Any] | None = None) -> None:
        self._storage: dict[Any, Any] = dict(initial) if initial is not None else {}

    def get(self, key: Any, default: Any = None) -> Any:
        return self._storage.get(key, default)

    def setdefault(self, key: Any, default: Any = None) -> Any:
        return self._storage.setdefault(key, default)

    def __getitem__(self, key: Any) -> Any:
        return self._storage[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._storage[key] = value

    def __delitem__(self, key: Any) -> None:
        del self._storage[key]

    def __contains__(self, key: Any) -> bool:
        return key in self._storage

    def __len__(self) -> int:
        return len(self._storage)

    def clear(self) -> None:
        self._storage.clear()


class StashBound:
    STASH_KEY: ClassVar[str] = "pytest_bdd_bound"

    @classmethod
    def stash_missing_message(cls) -> str:
        return f"`{cls.__name__}` is unavailable in config.stash."

    @classmethod
    def stash_duplicate_message(cls) -> str:
        return f"`{cls.__name__}` is already initialized in config.stash."


__all__ = ["SimpleStash", "StashBound", "StashKey"]
