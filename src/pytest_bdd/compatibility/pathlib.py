from __future__ import annotations

import sys

GlobError = IndexError if sys.version_info < (3, 13) else ValueError

__all__ = ["GlobError"]
