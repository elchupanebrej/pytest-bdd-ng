from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from attrs import define
from returns.maybe import Maybe, Nothing, Some

from pytest_bdd.exceptions import (
    PytestBDDStashAlreadyInitializedError,
    PytestBDDStashLookupError,
    PytestBDDStashTypeMismatchError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
B = TypeVar("B", bound="StashBound")


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


class StashAccess:
    @staticmethod
    def _stash_get(stash: Any, key: Any) -> Any:
        if hasattr(stash, "get"):
            return stash.get(key, None)
        try:
            if key in stash:
                return stash[key]
            return None
        except (KeyError, TypeError):
            return None

    @classmethod
    def get_optional(cls, stash: Any, stash_type: type[B] | StashKey[B] | Any) -> Maybe[B]:
        key = getattr(stash_type, "STASH_KEY", stash_type)
        candidate = cls._stash_get(stash, key)
        if candidate is None and key != stash_type:
            candidate = cls._stash_get(stash, stash_type)
        if candidate is None:
            return Nothing
        if isinstance(stash_type, type) and not isinstance(candidate, stash_type):
            raise PytestBDDStashTypeMismatchError(
                stash_key=str(key),
                actual_type=type(candidate).__name__,
                expected_type=stash_type.__name__,
            )
        return Some(candidate)

    @classmethod
    def require(cls, stash: Any, stash_type: type[B] | StashKey[B] | Any, *, missing_message: str) -> B:
        candidate = cls.get_optional(stash, stash_type)
        val = candidate.value_or(None)
        if val is not None:
            return val
        raise PytestBDDStashLookupError(missing_message)

    @classmethod
    def set(cls, stash: Any, value: B, key: Any = None) -> B:
        target_key = key if key is not None else getattr(value, "STASH_KEY", type(value).__name__)
        stash[target_key] = value
        return value

    @classmethod
    def create_once(
        cls,
        stash: Any,
        stash_type: type[B] | StashKey[B] | Any,
        *,
        value_factory: Callable[[], B],
        duplicate_message: str,
    ) -> B:
        existing = cls.get_optional(stash, stash_type)
        if existing.value_or(None) is not None:
            raise PytestBDDStashAlreadyInitializedError(duplicate_message)
        val = value_factory()
        return cls.set(stash, val, key=getattr(stash_type, "STASH_KEY", stash_type))


class StashBound:
    STASH_KEY: ClassVar[str] = "pytest_bdd_bound"

    @classmethod
    def stash_missing_message(cls) -> str:
        return f"`{cls.__name__}` is unavailable in config.stash."

    @classmethod
    def stash_duplicate_message(cls) -> str:
        return f"`{cls.__name__}` is already initialized in config.stash."

    @classmethod
    def find_in_stash(cls: type[B], stash: Any) -> Maybe[B]:
        return StashAccess.get_optional(stash, cls)

    @classmethod
    def from_stash(cls: type[B], stash: Any) -> B:
        return StashAccess.require(stash, cls, missing_message=cls.stash_missing_message())

    def set_in_stash(self: B, stash: Any) -> B:
        return StashAccess.set(stash, self)

    def initialize_in_stash(self: B, stash: Any) -> B:
        return StashAccess.create_once(
            stash,
            type(self),
            value_factory=lambda: self,
            duplicate_message=type(self).stash_duplicate_message(),
        )


__all__ = [
    "SimpleStash",
    "StashAccess",
    "StashBound",
    "StashKey",
]
