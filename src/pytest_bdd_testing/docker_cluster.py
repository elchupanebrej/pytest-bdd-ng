"""Compatibility alias for Docker cluster test support."""

from __future__ import annotations

import sys

from pytest_bdd_testing.tool.docker import cluster as _cluster

sys.modules[__name__] = _cluster
