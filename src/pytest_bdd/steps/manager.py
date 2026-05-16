"""StepDefinitionManager namespace class for backward compatibility."""

from __future__ import annotations

from pytest_bdd.steps.definition import Definition
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import NamespaceStepRegistryProtocol, Registry, StepProtocol


class StepDefinitionManager:
    """
    Step definition manager — namespace class exposing Registry, Matcher, Definition.

    This class exists for backward compatibility. Code that accesses
    ``StepDefinitionManager.Registry``, ``StepDefinitionManager.Matcher``,
    or ``StepDefinitionManager.Definition`` will continue to work.
    """

    Registry = Registry
    Matcher = Matcher
    Definition = Definition
    StepProtocol = StepProtocol
    NamespaceStepRegistryProtocol = NamespaceStepRegistryProtocol
