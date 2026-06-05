"""Provide sys compatibility helpers."""

from sys import _getframe

__all__ = [
    "get_frame",
]

get_frame = _getframe
