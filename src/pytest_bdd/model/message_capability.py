"""
Provide message capability helpers.

Responsibility:
    Provide message capability helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_capability` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - MessageCapability: owns nested behavior below this boundary
    - classify_capability_relevance: owns nested behavior below this boundary
    - capability_is_relevant: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `message_capability`

State and side effects:
    mutates CapabilityCategory, CapabilityRelevance, CapabilityImpact, RELEVANT_IMPACTS, capability_id; depends on
    __future__.annotations, typing.Final, typing.Literal, attrs.field, attrs.frozen.

Invariants:
    - `pytest_bdd.model.message_capability` keeps its documented import path, ownership boundary, and observable
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

from typing import Final, Literal

from attrs import field, frozen

CapabilityCategory = Literal["core", "lifecycle", "hook", "attachment", "parameter", "metadata"]
CapabilityRelevance = Literal["relevant", "out_of_scope"]
CapabilityImpact = Literal[
    "emitted_envelope_payload",
    "lifecycle_linkage",
    "status_mapping",
    "governance_checklist_output",
]

RELEVANT_IMPACTS: Final[frozenset[CapabilityImpact]] = frozenset(
    {
        "emitted_envelope_payload",
        "lifecycle_linkage",
        "status_mapping",
        "governance_checklist_output",
    },
)


@frozen
class MessageCapability:
    """
    Represent a distinct capability introduced by a cucumber-messages schema release.

    Used to track supported features and generate compatibility inventories.

    Responsibility:
        Represent a distinct capability introduced by a cucumber-messages schema release. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability.MessageCapability` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - relevance: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `MessageCapability`
        - src/pytest_bdd/model/message_baseline_diff.py: imports or references `MessageCapability`
        - src/pytest_bdd/model/message_capability_inventory.py: imports or references `MessageCapability`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `MessageCapability`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `MessageCapability`

    State and side effects:
        mutates capability_id, baseline_release, name, description, category.

    Invariants:
        - `pytest_bdd.model.message_capability.MessageCapability` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    capability_id: str
    baseline_release: str
    name: str
    description: str
    category: CapabilityCategory
    affects: frozenset[CapabilityImpact] = field(factory=frozenset)
    source_reference: str = ""
    explicit_relevance: CapabilityRelevance | None = None

    @property
    def relevance(self) -> CapabilityRelevance:
        """
        Determine whether this capability falls within the supported scope of the project.

        Returns:
            The relevance classification indicating if the capability is supported or out of scope.

        Responsibility:
            Determine whether this capability falls within the supported scope of the project. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_capability.MessageCapability.relevance`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - classify_capability_relevance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_baseline_diff.py: imports or references `relevance`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `relevance`

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
        return classify_capability_relevance(self)


def classify_capability_relevance(capability: MessageCapability) -> CapabilityRelevance:
    """
    Classify a given capability based on its explicit relevance or inferred impact.

    Returns:
        The evaluated relevance, classifying it as either 'relevant' or 'out_of_scope'.

    Responsibility:
        Classify a given capability based on its explicit relevance or inferred impact. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability.classify_capability_relevance`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - capability.affects.intersection: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `classify_capability_relevance`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `classify_capability_relevance`

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
    if capability.explicit_relevance is not None:
        return capability.explicit_relevance
    if capability.affects.intersection(RELEVANT_IMPACTS):
        return "relevant"
    return "out_of_scope"


def capability_is_relevant(capability: MessageCapability) -> bool:
    """
    Check if the specified message capability is considered relevant for the project.

    Returns:
        True if the capability is classified as relevant, False otherwise.

    Responsibility:
        Check if the specified message capability is considered relevant for the project. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability.capability_is_relevant` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - classify_capability_relevance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `capability_is_relevant`
        - src/pytest_bdd/model/message_capability_inventory.py: imports or references `capability_is_relevant`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `capability_is_relevant`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `capability_is_relevant`

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
    return classify_capability_relevance(capability) == "relevant"
