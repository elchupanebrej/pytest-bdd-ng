"""Provide src.pytest_bdd.plugin.pickle_runner package helpers."""

from .run_transitions import apply_transition


def __getattr__(name: str) -> object:
    if name in {"build_external_api_compatibility_record", "collect_hook_public_symbols"}:
        from .api_compatibility import (  # noqa: PLC0415 -- breaks circular import
            build_external_api_compatibility_record,
            collect_hook_public_symbols,
        )

        return locals()[name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "apply_transition",
    "build_external_api_compatibility_record",  # noqa: F822 -- defined via PEP 562 __getattr__
    "collect_hook_public_symbols",  # noqa: F822 -- defined via PEP 562 __getattr__
]
