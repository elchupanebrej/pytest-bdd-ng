"""pytest-bdd public API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytest_bdd.scenario import FeaturePathType, scenario, scenarios

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.steps import given, step, then, when
    from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

__all__ = ["given", "scenario", "scenarios", "step", "then", "when"]


def __getattr__(name: str) -> Any:
    if name in {"given", "step", "then", "when"}:
        from pytest_bdd.steps import given, step, then, when

        return {
            "given": given,
            "step": step,
            "then": then,
            "when": when,
        }[name]
    if name == "PytestBDDStepDefinitionWarning":
        from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

        return PytestBDDStepDefinitionWarning
    if name == "__version__":
        from pytest_bdd.util.packaging import get_distribution_version

        return str(get_distribution_version("pytest-bdd-ng"))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
