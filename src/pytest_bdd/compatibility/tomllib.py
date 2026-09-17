from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from tomllib import TOMLDecodeError, load, loads
else:
    # tomli is the Python <3.11 stdlib backport; the type-check environment only
    # installs tomllib, so mypy cannot resolve the stubs for this runtime branch.
    from tomli import TOMLDecodeError, load, loads  # type: ignore[import-not-found]

__all__ = [
    "TOMLDecodeError",
    "load",
    "loads",
]
