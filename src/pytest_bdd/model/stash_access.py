"""Provide stash access helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, TypeVar, cast

from typing_extensions import Self

import pytest_bdd.types.exception as exceptions

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_bdd.compatibility.pytest import Stash

T = TypeVar("T", bound="StashBound")


class _StringKeyStash(Protocol):
    def __getitem__(self, key: str) -> object: ...

    def __setitem__(self, key: str, value: object) -> None: ...

    def __contains__(self, key: str) -> bool: ...

    def get(self, key: str, default: object | None = None) -> object | None: ...


class StashAccess:
    """Access pytest stash values across pytest versions."""

    @staticmethod
    def _stash_get(stash: Stash, key: str) -> object | None:
        string_stash = cast(_StringKeyStash, stash)
        if hasattr(string_stash, "get"):
            return string_stash.get(key, None)
        return string_stash[key] if key in string_stash else None  # noqa: SIM401

    @classmethod
    def get_optional(cls, stash: Stash, stash_type: type[T]) -> T | None:
        """
        Return optional.

        Raises:
            PytestBDDStashTypeMismatchError: If the operation cannot be completed.

        """
        candidate = cls._stash_get(stash, stash_type.STASH_KEY)
        if candidate is None:
            return None
        if isinstance(candidate, stash_type):
            return candidate
        raise exceptions.PytestBDDStashTypeMismatchError(
            stash_key=stash_type.STASH_KEY,
            actual_type=type(candidate).__name__,
            expected_type=stash_type.__name__,
        )

    @classmethod
    def require(cls, stash: Stash, stash_type: type[T], *, missing_message: str) -> T:
        """
        Handle require.

        Raises:
            PytestBDDStashLookupError: If the operation cannot be completed.

        """
        candidate = cls.get_optional(stash, stash_type)
        if candidate is not None:
            return candidate
        raise exceptions.PytestBDDStashLookupError(missing_message)

    @classmethod
    def set(cls, stash: Stash, value: T) -> T:
        """Handle set."""
        cast(_StringKeyStash, stash)[value.STASH_KEY] = value
        return value

    @classmethod
    def create_once(
        cls,
        stash: Stash,
        stash_type: type[T],
        *,
        value_factory: Callable[[], T],
        duplicate_message: str,
    ) -> T:
        """
        Represent create once state.

        Raises:
            PytestBDDStashAlreadyInitializedError: If the operation cannot be completed.

        """
        existing = cls.get_optional(stash, stash_type)
        if existing is not None:
            raise exceptions.PytestBDDStashAlreadyInitializedError(duplicate_message)
        return cls.set(stash, value_factory())


class StashBound:
    """Represent stash bound state."""

    STASH_KEY: ClassVar[str]

    @classmethod
    def stash_missing_message(cls) -> str:
        """Handle stash missing message."""
        return f"`{cls.__name__}` is unavailable in config.stash."

    @classmethod
    def stash_duplicate_message(cls) -> str:
        """Handle stash duplicate message."""
        return f"`{cls.__name__}` is already initialized in config.stash."

    @classmethod
    def find_in_stash(cls, stash: Stash) -> Self | None:
        """Find in stash."""
        return StashAccess.get_optional(stash, cls)

    @classmethod
    def from_stash(cls, stash: Stash) -> Self:
        """Create stash."""
        return StashAccess.require(stash, cls, missing_message=cls.stash_missing_message())

    def set_in_stash(self, stash: Stash) -> Self:
        """Handle set in stash."""
        return StashAccess.set(stash, self)

    def initialize_in_stash(self, stash: Stash) -> Self:
        """Handle initialize in stash."""
        return StashAccess.create_once(
            stash,
            type(self),
            value_factory=lambda: self,
            duplicate_message=type(self).stash_duplicate_message(),
        )
