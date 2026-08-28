from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable

if sys.version_info >= (3, 11):
    from typing import Self, TypeAlias
else:
    from typing_extensions import Self, TypeAlias

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

__all__ = [
    "Protocol",
    "Self",
    "TypeAlias",
    "override",
    "runtime_checkable",
]
