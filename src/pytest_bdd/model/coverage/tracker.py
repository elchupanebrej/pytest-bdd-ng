"""
Provide tracker.

Responsibility:
    Provide tracker. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.coverage.tracker` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - ObservedCoverage: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `tracker`
    - src/pytest_bdd/model/message_validation_result.py: imports or references `tracker`

State and side effects:
    mutates observed_fields, evidence_scenarios, key; depends on attrs.define, attrs.field,
    inventory.canonical_capability_key.

Invariants:
    - `pytest_bdd.model.coverage.tracker` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from attrs import define, field

from .inventory import canonical_capability_key


@define(slots=False)
class ObservedCoverage:
    """
    Runtime data collected during test execution.

    Responsibility:
        Runtime data collected during test execution. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.tracker.ObservedCoverage` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - record_field: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `ObservedCoverage`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `ObservedCoverage`

    State and side effects:
        mutates observed_fields, evidence_scenarios, key.

    Invariants:
        - `pytest_bdd.model.coverage.tracker.ObservedCoverage` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    # Set of (payload_kind, field_path) that were actually populated
    observed_fields: set[tuple[str, str]] = field(factory=set)
    # Map of (payload_kind, field_path) to the test case ID that provided the first evidence
    evidence_scenarios: dict[tuple[str, str], str] = field(factory=dict)

    def record_field(
        self,
        payload_kind: str,
        field_path: str,
        *,
        evidence_scenario_id: str | None = None,
    ) -> None:
        """
        Record a field observation.

        Args:
            payload_kind: The kind of payload the field belongs to.
            field_path: The path of the field.
            evidence_scenario_id: Optional scenario ID that provided evidence.

        Responsibility:
            Record a field observation. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.coverage.tracker.ObservedCoverage.record_field`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - canonical_capability_key: collaborator call used by this boundary
            - self.observed_fields.add: collaborator call used by this boundary
            - self.evidence_scenarios.setdefault: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `record_field`
            - src/pytest_bdd/model/message_validation_result.py: imports or references `record_field`

        State and side effects:
            mutates key.

        Invariants:
            - `pytest_bdd.model.coverage.tracker.ObservedCoverage.record_field` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        key = canonical_capability_key(payload_kind, field_path)
        self.observed_fields.add(key)
        if evidence_scenario_id is not None:
            self.evidence_scenarios.setdefault(key, evidence_scenario_id)
