"""Provide stash access helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, TypeVar, cast

from returns.maybe import Maybe, Nothing, Some
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
        string_stash = cast("_StringKeyStash", stash)
        if hasattr(string_stash, "get"):
            return string_stash.get(key, None)
        return string_stash[key] if key in string_stash else None  # noqa: SIM401

    @classmethod
    def get_optional(cls, stash: Stash, stash_type: type[T]) -> Maybe[T]:
        """
        Retrieve an instance of the specified type from the pytest stash if it exists.

        Returns:
            The instance stored in the stash matching the requested type, or Nothing if it has not been set.

        Raises:
            PytestBDDStashTypeMismatchError: If the value's type doesn't match expected.

        """
        candidate = cls._stash_get(stash, stash_type.STASH_KEY)
        if candidate is None:
            return Nothing
        if isinstance(candidate, stash_type):
            return Some(candidate)
        raise exceptions.PytestBDDStashTypeMismatchError(
            stash_key=stash_type.STASH_KEY,
            actual_type=type(candidate).__name__,
            expected_type=stash_type.__name__,
        )

    @classmethod
    def require(cls, stash: Stash, stash_type: type[T], *, missing_message: str) -> T:
        """
        Retrieve a required instance of the specified type from the pytest stash.

        Returns:
            The guaranteed instance of the requested type stored in the stash.

        Raises:
            PytestBDDStashLookupError: If the required instance is not found in the stash.

        """
        candidate = cls.get_optional(stash, stash_type)
        if (value := candidate.value_or(None)) is not None:
            return value
        raise exceptions.PytestBDDStashLookupError(missing_message)

    @classmethod
    def set(cls, stash: Stash, value: T) -> T:
        """
        Store a type-bound value in the pytest stash using its designated class key.

        Returns:
            The newly stored value.

        """
        cast("_StringKeyStash", stash)[value.STASH_KEY] = value
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
        Initialize and store a value in the pytest stash only if it doesn't already exist.

        Returns:
            The newly created and stored value.

        Raises:
            PytestBDDStashAlreadyInitializedError: If a value for the target type is already present in the stash.

        """
        existing = cls.get_optional(stash, stash_type)
        if existing.value_or(None) is not None:
            raise exceptions.PytestBDDStashAlreadyInitializedError(duplicate_message)
        return cls.set(stash, value_factory())


class StashBound:
    """A generic base class that automatically bounds its subclasses to specific keys within the pytest stash."""

    STASH_KEY: ClassVar[str]

    @classmethod
    def stash_missing_message(cls) -> str:
        """
        Construct a default error message for when the bound type is missing from the stash.

        Returns:
            A formatted string explaining that the bound class is unavailable in the current stash.

        """
        return f"`{cls.__name__}` is unavailable in config.stash."

    @classmethod
    def stash_duplicate_message(cls) -> str:
        """
        Construct a default error message for when the bound type already exists in the stash.

        Returns:
            A formatted string explaining that the bound class has already been initialized in the stash.

        """
        return f"`{cls.__name__}` is already initialized in config.stash."

    @classmethod
    def find_in_stash(cls, stash: Stash) -> Maybe[Self]:
        """
        Look up the bound type in the provided pytest stash.

        Returns:
            The stored instance of the bound type, or Nothing if not found.

        """
        return StashAccess.get_optional(stash, cls)

    @classmethod
    def from_stash(cls, stash: Stash) -> Self:
        """
        Retrieve the bound type from the provided pytest stash, enforcing its existence.

        Returns:
            The guaranteed instance of the bound type stored in the stash.

        """
        return StashAccess.require(stash, cls, missing_message=cls.stash_missing_message())

    def set_in_stash(self, stash: Stash) -> Self:
        """
        Store the current instance within the provided pytest stash.

        Returns:
            The instance that was successfully stored.

        """
        return StashAccess.set(stash, self)

    def initialize_in_stash(self, stash: Stash) -> Self:
        """
        Safely initialize the current instance within the pytest stash, ensuring no duplication.

        Returns:
            The instance that was successfully stored.

        """
        return StashAccess.create_once(
            stash,
            type(self),
            value_factory=lambda: self,
            duplicate_message=type(self).stash_duplicate_message(),
        )
