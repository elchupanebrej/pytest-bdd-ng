"""
Machine-readable code-generation events.

Responsibility:
    Machine-readable code-generation events. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.events` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - MissingScenarioBindingEvent: owns nested behavior below this boundary
    - MissingStepDefinitionEvent: owns nested behavior below this boundary
    - to_ndjson: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `events`
    - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `events`

State and side effects:
    mutates feature, scenario, line, type, keyword; depends on __future__.annotations, json, typing.Literal, attrs.

Invariants:
    - `pytest_bdd.plugin.code_generator.events` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import json
from typing import Literal

import attrs


@attrs.define(frozen=True)
class MissingScenarioBindingEvent:
    """
    Represent a scenario that has no pytest binding.

    Responsibility:
        Represent a scenario that has no pytest binding. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.events.MissingScenarioBindingEvent`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `MissingScenarioBindingEvent`
        - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `MissingScenarioBindingEvent`

    State and side effects:
        mutates feature, scenario, line, type.

    Invariants:
        - `pytest_bdd.plugin.code_generator.events.MissingScenarioBindingEvent` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    feature: str
    scenario: str
    line: int | None
    type: Literal["missing_scenario_binding"] = "missing_scenario_binding"

    def as_dict(self) -> dict[str, object]:
        """
        Return JSON-serializable event data.

        Returns:
            Event fields as a dictionary.

        Responsibility:
            Return JSON-serializable event data. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.events.MissingScenarioBindingEvent.as_dict` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - attrs.asdict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return attrs.asdict(self)


@attrs.define(frozen=True)
class MissingStepDefinitionEvent:
    """
    Represent a step that has no step definition.

    Responsibility:
        Represent a step that has no step definition. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.events.MissingStepDefinitionEvent`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `MissingStepDefinitionEvent`
        - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `MissingStepDefinitionEvent`

    State and side effects:
        mutates feature, scenario, keyword, text, line.

    Invariants:
        - `pytest_bdd.plugin.code_generator.events.MissingStepDefinitionEvent` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    feature: str
    scenario: str
    keyword: str
    text: str
    line: int | None
    type: Literal["missing_step_definition"] = "missing_step_definition"

    def as_dict(self) -> dict[str, object]:
        """
        Return JSON-serializable event data.

        Returns:
            Event fields as a dictionary.

        Responsibility:
            Return JSON-serializable event data. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.code_generator.events.MissingStepDefinitionEvent.as_dict` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - attrs.asdict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return attrs.asdict(self)


CodeGenerationEvent = MissingScenarioBindingEvent | MissingStepDefinitionEvent


def to_ndjson(events: list[CodeGenerationEvent]) -> str:
    """
    Serialize code-generation events as sorted-key NDJSON.

    Returns:
        NDJSON event stream.

    Responsibility:
        Serialize code-generation events as sorted-key NDJSON. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.events.to_ndjson` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - event.as_dict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `to_ndjson`
        - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `to_ndjson`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return "\n".join(json.dumps(event.as_dict(), sort_keys=True) for event in events)
