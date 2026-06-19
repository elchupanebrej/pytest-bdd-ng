"""Compatibility alias for Docker test support."""

from __future__ import annotations

import sys

from pytest_bdd_testing.tool.docker import docker as _docker

sys.modules[__name__] = _docker
