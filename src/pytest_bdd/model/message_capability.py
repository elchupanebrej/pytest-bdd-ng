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
    }
)


@frozen
class MessageCapability:
    """Represent message capability state."""

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
        """Handle relevance."""
        return classify_capability_relevance(self)


def classify_capability_relevance(capability: MessageCapability) -> CapabilityRelevance:
    """Handle classify capability relevance."""
    if capability.explicit_relevance is not None:
        return capability.explicit_relevance
    if capability.affects.intersection(RELEVANT_IMPACTS):
        return "relevant"
    return "out_of_scope"


def capability_is_relevant(capability: MessageCapability) -> bool:
    """Handle capability is relevant."""
    return classify_capability_relevance(capability) == "relevant"
