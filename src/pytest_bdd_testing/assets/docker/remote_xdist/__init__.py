"""Compatibility path alias for remote xdist Docker assets."""

from __future__ import annotations

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[3] / "resource" / "docker" / "remote_xdist")]
