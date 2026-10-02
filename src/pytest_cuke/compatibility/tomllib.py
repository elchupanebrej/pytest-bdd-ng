from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from tomllib import TOMLDecodeError, load, loads
else:
    # tomli is the Python <3.11 stdlib backport; absent from type-check envs on
    # >=3.11, so it is listed in the mypy ignore_missing_imports override.
    from tomli import TOMLDecodeError, load, loads

__all__ = [
    "TOMLDecodeError",
    "load",
    "loads",
]
