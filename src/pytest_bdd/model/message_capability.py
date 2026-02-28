from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

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


@dataclass(frozen=True, slots=True)
class MessageCapability:
    capability_id: str
    baseline_release: str
    name: str
    description: str
    category: CapabilityCategory
    affects: frozenset[CapabilityImpact] = field(default_factory=frozenset)
    source_reference: str = ""
    explicit_relevance: CapabilityRelevance | None = None

    @property
    def relevance(self) -> CapabilityRelevance:
        return classify_capability_relevance(self)


def classify_capability_relevance(capability: MessageCapability) -> CapabilityRelevance:
    if capability.explicit_relevance is not None:
        return capability.explicit_relevance
    if capability.affects.intersection(RELEVANT_IMPACTS):
        return "relevant"
    return "out_of_scope"


def capability_is_relevant(capability: MessageCapability) -> bool:
    return classify_capability_relevance(capability) == "relevant"
