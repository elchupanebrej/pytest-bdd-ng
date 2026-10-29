from __future__ import annotations

import importlib
from pathlib import Path

import pytest_cuke
from pytest_cuke.compatibility.tomllib import load

PUBLIC_NAMES = {"given", "when", "then", "step", "parsers", "scenario", "scenarios"}


def test_public_api_is_exactly_the_seven_accepted_names() -> None:
    assert set(pytest_cuke.__all__) == PUBLIC_NAMES
    assert all(hasattr(pytest_cuke, name) for name in PUBLIC_NAMES)


def test_wildcard_import_and_private_names_follow_the_facade_boundary() -> None:
    namespace: dict[str, object] = {}
    exec("from pytest_cuke import *", namespace)
    assert {name for name in namespace if name != "__builtins__"} == PUBLIC_NAMES
    assert not any(hasattr(pytest_cuke, name) for name in ("Feature", "Scenario", "Step", "Runner"))
    assert importlib.import_module("pytest_cuke.plugin") is not None


def test_public_api_callables_and_parser_facade() -> None:
    for name in ("given", "when", "then", "step", "scenario", "scenarios"):
        assert callable(getattr(pytest_cuke, name))

    assert all(callable(getattr(pytest_cuke.parsers, name)) for name in ("parse", "re", "cfparse", "cuke_expressions"))


def test_canonical_plugin_and_command_entrypoints_are_registered() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    with (repo_root / "pyproject.toml").open("rb") as f:
        data = load(f)

    project = data["project"]
    assert project["name"] == "pytest-cuke"
    assert project["entry-points"]["pytest11"] == {"cuke": "pytest_cuke.plugin"}
    assert project["scripts"] == {"pytest-cuke": "pytest_cuke.cli:main", "cuke": "pytest_cuke.cli:main"}
