"""
Serves as the public API aggregation module for the message_stream_validation subpackage, explicitly re-exporting all.

Responsibility:
    Serves as the public API aggregation module for the message_stream_validation subpackage, explicitly re-exporting
    all public symbols from the internal pipeline and status modules: validate_message_stream and
    collect_observed_capability_ids from pipeline.py, and collect_observed_outcomes, default_outcome_mapping_rules,
    observed_outcome_from_envelope, plus the ALLOWED_IMPLEMENTATION_STATUSES constant from pipeline.py. This module is
    the canonical import point for any code that needs to validate cucumber-messages protocol streams or collect outcome
    observations.

Reason for existence:
    Separates the public API surface from internal implementation details. pipeline.py contains the complex
    validate_message_stream orchestration logic with many private helper functions (_payload_id, _track_fields,
    _payload_object_for_kind, _is_non_empty_text), while status.py contains outcome derivation and mapping logic.
    Consumers should not need to know the internal module structure — they import from facade (or through __init__.py
    which wildcard-imports from facade). This module explicitly enumerates the public symbols with F401 suppression
    comments, making the API contract visible and reviewable.

Delegates:
    - pytest_bdd.message_stream_validation.pipeline: Provides validate_message_stream, collect_observed_capability_ids,
    and ALLOWED_IMPLEMENTATION_STATUSES.
    - pytest_bdd.message_stream_validation.status: Provides collect_observed_outcomes, default_outcome_mapping_rules,
    and observed_outcome_from_envelope.

Cohesion:
    Every import in this module serves the purpose of exposing the validation subpackage's public API. The imports are
    organized by source module (pipeline, status) and annotated with justification comments. No non-re-export code
    exists.

Separation:
    - pytest_bdd.message_stream_validation.pipeline: Kept separate because pipeline.py owns the actual validation
    orchestration logic with all its private helpers, while facade.py is a thin re-export layer — mechanism vs
    interface.
    - pytest_bdd.message_stream_validation.status: Kept separate because status.py owns outcome observation and mapping
    logic, while facade.py aggregates without implementing.

Main consumers:
    - pytest_bdd.message_stream_validation.__init__: Wildcard-imports from this facade to expose the complete API
    through the package namespace.
    - pytest_bdd.plugin.gherkin_message_reporter: Imports validate_message_stream for message stream compliance
    validation during BDD execution.
    - Test suites for message stream validation: Import validation and outcome functions for testing message protocol
    compliance.

State and side effects:
    None, keeps no persistent state. All imports are read-only namespace operations.

Invariants:
    - Every public symbol defined in the internal subpackage modules must be re-exported through this facade to maintain
    a complete public API.
    - No implementation logic may be added to this module — it must remain a pure re-export layer.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.message_stream_validation.pipeline import (  # noqa: F401  -- intentional re-export or import for public API facade
    ALLOWED_IMPLEMENTATION_STATUSES,
    collect_observed_capability_ids,
    validate_message_stream,
)
from pytest_bdd.message_stream_validation.status import (  # noqa: F401  -- intentional re-export or import for public API facade
    collect_observed_outcomes,
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
)
