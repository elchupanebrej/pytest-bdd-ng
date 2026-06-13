"""
Serves as a public API facade that re-exports the complete message stream validation public API through a single wild.

Responsibility:
    Serves as a public API facade that re-exports the complete message stream validation public API through a single
    wildcard import from pytest_bdd.message_stream_validation.facade, including the core validation function
    (validate_message_stream), capability ID collection (collect_observed_capability_ids), outcome observation functions
    (collect_observed_outcomes, observed_outcome_from_envelope, default_outcome_mapping_rules), and the
    ALLOWED_IMPLEMENTATION_STATUSES constant. This module is the canonical import point for any code that needs to
    validate cucumber-messages protocol compliance of a message stream.

Reason for existence:
    Provides a short, stable import path for the validation API while keeping the implementation split across two
    internal modules (pipeline.py for stream validation logic, status.py for outcome mapping logic). The facade module
    aggregates these into a single namespace, and this __init__.py wildcard-imports from facade to maintain the Python
    package convention where `from pytest_bdd.message_stream_validation import X` works as expected. Without this
    module, consumers would need to know the internal module structure and import directly from pipeline or status.

Delegates:
    - pytest_bdd.message_stream_validation.facade: All public API symbols (validate_message_stream,
    collect_observed_capability_ids, collect_observed_outcomes, observed_outcome_from_envelope,
    default_outcome_mapping_rules, ALLOWED_IMPLEMENTATION_STATUSES) are re-exported via wildcard import from this
    module.
    - pytest_bdd.message_stream_validation.pipeline: The actual stream validation logic (validate_message_stream,
    collect_observed_capability_ids), invoked internally by facade.
    - pytest_bdd.message_stream_validation.status: The outcome mapping and observation logic (collect_observed_outcomes,
    observed_outcome_from_envelope, default_outcome_mapping_rules), invoked internally by facade.

Cohesion:
    Perfect cohesion as a facade: the single responsibility is re-exporting the validation API. There is no
    implementation logic, so there is no risk of internal cohesion conflicts.

Separation:
    - pytest_bdd.message_stream_validation.facade: Kept separate because facade.py explicitly enumerates and documents
    the re-exported symbols with justification, while __init__.py relies on the wildcard — facade is the "truth source"
    for what constitutes the public API.
    - pytest_bdd.model.message_extension: Kept separate because message_extension owns the event envelope type
    definitions (EventEnvelope, get_payload_kind), while the validation package owns the validation rules applied to
    those envelopes — types vs policy.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter: Uses validate_message_stream to validate cucumber-messages protocol
    compliance of generated message streams during BDD test execution.
    - pytest_bdd.model.coverage tests: Uses collect_observed_capability_ids and collect_observed_outcomes for coverage
    analysis of message streams.

State and side effects:
    None, keeps no persistent state. The wildcard import executes at module load time but has no other side effects.

Invariants:
    - The wildcard import (`from pytest_bdd.message_stream_validation.facade import *`) must remain the only executable
    line beyond the docstring and noqa directives.
    - Every public API function added to facade.py automatically becomes available through this package without
    additional changes.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=1
    #arch-eval:locational_stability=5
"""

from pytest_bdd.message_stream_validation.facade import *  # noqa: F403  -- intentional re-export or import for public API facade
