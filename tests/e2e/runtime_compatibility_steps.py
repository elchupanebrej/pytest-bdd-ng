"""BDD steps for runtime compatibility regressions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest_cuke.steps.manager as step_manager
from pytest_cuke import given, then, when


class _LocalsMappingWithoutSetdefault:
    """Model a frame-local mapping that supports item access without dict helpers."""

    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def __contains__(self, key: object) -> bool:
        return key in self.values

    def __getitem__(self, key: str) -> object:
        return self.values[key]

    def __setitem__(self, key: str, value: object) -> None:
        self.values[key] = value


@given("worker-root pytester projects share one checkout feature")
def worker_root_pytester_projects_share_feature(pytester: Any) -> None:
    project_path = getattr(pytester, "path", None)
    if project_path is None:
        project_path = pytester.tmpdir
    project = Path(str(project_path))
    for worker_root in (
        "pytest-cuke-execnet-remote-0-first",
        "pytest-cuke-execnet-remote-1-second",
    ):
        feature_path = project / worker_root / "features" / "checkout.feature"
        feature_path.parent.mkdir(parents=True)
        feature_path.write_text(
            "Feature: Checkout\n"
            "  Scenario: checkout loads\n"
            "    Given the basket is ready\n",
            encoding="utf-8",
        )

    pytester.makepyfile(
        test_checkout="""
import os
from pathlib import Path

from pytest_cuke import given, scenarios


@given("the basket is ready")
def basket_is_ready():
    pass


test_checkout = scenarios(
    f"{os.environ['PYTEST_CUKE_REMOTE_ROOT']}/features/checkout.feature",
    features_base_dir=Path(__file__).parent,
)
"""
    )


@when("I collect the checkout feature from both worker roots", target_fixture="worker_scenario_node_ids")
def collect_worker_root_node_ids(pytester: Any, monkeypatch: Any) -> tuple[str, str]:
    node_ids: list[str] = []
    for worker_root in (
        "pytest-cuke-execnet-remote-0-first",
        "pytest-cuke-execnet-remote-1-second",
    ):
        monkeypatch.setenv("PYTEST_CUKE_REMOTE_ROOT", worker_root)
        result = pytester.runpytest_subprocess("--collect-only", "-q", "test_checkout.py")
        output = result.stdout.str()
        assert result.ret == 0, output
        collected = [line.strip() for line in result.stdout.lines if line.strip().startswith("test_checkout.py::")]
        assert len(collected) == 1, output
        node_ids.append(collected[0])
    return node_ids[0], node_ids[1]


@then("both child collections expose the same worker-independent scenario node ID")
def worker_root_node_ids_are_stable(worker_scenario_node_ids: tuple[str, str]) -> None:
    first, second = worker_scenario_node_ids
    assert first == second
    assert "file:_remote/features/checkout.feature-Checkout-checkout loads" in first
    assert "pytest-cuke-execnet-remote-" not in first


@when(
    "I register a target fixture in FrameLocalsProxy-style locals",
    target_fixture="proxy_step_registration",
)
def register_target_fixture_with_proxy_locals(monkeypatch: Any) -> tuple[_LocalsMappingWithoutSetdefault, Any]:
    caller_locals = _LocalsMappingWithoutSetdefault()
    monkeypatch.setattr(step_manager, "get_caller_module_locals", lambda stacklevel=1: caller_locals)

    def registered_step() -> None:
        pass

    registered = given("a runtime compatibility step", target_fixture="runtime_compatibility_target")(registered_step)
    return caller_locals, registered


@then("registration adds a fixture without requiring mapping.setdefault")
def proxy_locals_registration_succeeds(
    proxy_step_registration: tuple[_LocalsMappingWithoutSetdefault, Any],
) -> None:
    caller_locals, registered = proxy_step_registration
    assert registered.__name__ == "registered_step"
    assert callable(caller_locals["runtime_compatibility_target"])
    assert any(value is registered for value in caller_locals.values.values())
