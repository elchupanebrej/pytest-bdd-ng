from __future__ import annotations

from pytest_bdd.compatibility.typing import (
    Protocol,
    Self,
    TypeAlias,
    override,
    runtime_checkable,
)


def test_typing_exports() -> None:
    Alias: TypeAlias = int
    assert Alias is int

    @runtime_checkable
    class Proto(Protocol):
        def method(self) -> Self: ...

    class Impl:
        @override
        def method(self) -> Impl:
            return self

    impl = Impl()
    assert isinstance(impl, Proto)
