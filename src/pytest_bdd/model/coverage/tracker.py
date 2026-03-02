from dataclasses import dataclass, field


@dataclass
class ObservedCoverage:
    """Runtime data collected during test execution."""

    # Set of (payload_kind, field_path) that were actually populated
    observed_fields: set[tuple[str, str]] = field(default_factory=set)
    # Map of (payload_kind, field_path) to the test case ID that provided the first evidence
    evidence_scenarios: dict[tuple[str, str], str] = field(default_factory=dict)

    def record_field(
        self,
        payload_kind: str,
        field_path: str,
        *,
        evidence_scenario_id: str | None = None,
    ) -> None:
        key = (payload_kind, field_path)
        self.observed_fields.add(key)
        if evidence_scenario_id is not None:
            self.evidence_scenarios.setdefault(key, evidence_scenario_id)
