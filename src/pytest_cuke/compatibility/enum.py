from __future__ import annotations

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    try:
        from strenum import StrEnum
    except ImportError:

        class StrEnum(str, Enum):  # type: ignore[no-redef]
            def __str__(self) -> str:
                return str(self.value)


__all__ = ["StrEnum"]
