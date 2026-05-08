"""Provide message capability helpers."""

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

        """
        return classify_capability_relevance(self)


def classify_capability_relevance(capability: MessageCapability) -> CapabilityRelevance:
    """
    Classify a given capability based on its explicit relevance or inferred impact.

    Returns:
        The evaluated relevance, classifying it as either 'relevant' or 'out_of_scope'.

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

    """
    return classify_capability_relevance(capability) == "relevant"
