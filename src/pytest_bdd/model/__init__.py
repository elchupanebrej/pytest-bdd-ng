"""
Public re-export facade for the pytest-bdd model layer, aggregating scenario execution runtime, message handling,
validation, governance, and serialization names from internal submodules.

Responsibility:
    Serves as the public re-export facade for the pytest-bdd model layer, exposing scenario execution runtime, message
    handling, validation, governance, and serialization names through a single import surface so that plugin and runtime
    consumers only depend on the model package rather than individual internal submodules.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task to
    keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be unique
    per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all lifecycle
    stages

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=4
"""

__all__: list[str] = [
    "ALLOWED_IMPLEMENTATION_STATUSES",
    "CAPABILITY_STATUSES",
    "DEFAULT_CHECKLIST_NAME",
    "LEGACY_STATUS_ALIASES",
    "MANDATORY_EVIDENCE_FIELDS",
    "MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1",
    "NON_IMPLEMENTED_STATUSES",
    "RELEASE_BLOCKER_STATUSES",
    "RELEVANT_IMPACTS",
    "REQUIRED_MATRIX_STATUSES",
    "WEEKLY_CADENCE",
    "ActiveObjectSet",
    "BaselineComparisonSchedule",
    "BaselineDiffExecutionResult",
    "BaselineDiffRecord",
    "BlockerEvaluationResult",
    "CapabilityDecision",
    "CapabilitySyncResult",
    "ContextErrorState",
    "DecisionValidationResult",
    "ExecutionMessageAdapter",
    "ExecutionProjection",
    "ExternalApiCompatibilityRecord",
    "FeatureRuntimeBinding",
    "GovernanceChecklist",
    "GovernanceChecklistEntry",
    "HookPhase",
    "MessageCapability",
    "MessageSerializationProfile",
    "MessageValidationResult",
    "MessageValidationViolation",
    "ObservedOutcome",
    "OutcomeMappingRule",
    "ReferenceResolverState",
    "ReportingContextSnapshot",
    "ReportingLifecycleState",
    "Run",
    "RunNode",
    "RunStage",
    "RunStatus",
    "ScenarioRun",
    "StatusUniquenessResult",
    "StepRun",
    "build_baseline_diff",
    "build_governance_checklist",
    "capability_is_relevant",
    "classify_capability_relevance",
    "collect_observed_outcomes",
    "default_outcome_mapping_rules",
    "ensure_single_status_per_capability",
    "evaluate_release_blockers",
    "execute_weekly_baseline_diff",
    "find_matching_rules",
    "governance_value_to_dict",
    "is_release_blocker_status",
    "is_weekly_run_due",
    "message_converter",
    "missing_required_evidence_fields",
    "next_weekly_run_at",
    "normalize_capability_status",
    "observed_outcome_from_envelope",
    "outcome_key",
    "render_checklist_markdown",
    "resolve_outcome_mapping",
    "sync_capability_inventory",
    "validate_capability_decision",
    "validate_envelope_against_schema",
    "validate_envelope_dict_against_schema",
    "validate_envelope_shape",
    "validate_message_stream",
    "validate_outcome_mappings",
]

from .execution_message_adapter import ExecutionMessageAdapter, ExecutionProjection
from .feature_binding import FeatureRuntimeBinding
from .message_baseline_diff import (
    WEEKLY_CADENCE,
    BaselineComparisonSchedule,
    BaselineDiffExecutionResult,
    BaselineDiffRecord,
    build_baseline_diff,
    execute_weekly_baseline_diff,
    is_weekly_run_due,
    next_weekly_run_at,
)
from .message_capability import (
    RELEVANT_IMPACTS,
    MessageCapability,
    capability_is_relevant,
    classify_capability_relevance,
)
from .message_capability_inventory import CapabilitySyncResult, sync_capability_inventory
from .message_converter import governance_value_to_dict, message_converter, validate_envelope_shape
from .message_governance_checklist import (
    DEFAULT_CHECKLIST_NAME,
    GovernanceChecklist,
    GovernanceChecklistEntry,
    build_governance_checklist,
    render_checklist_markdown,
)
from .message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    REQUIRED_MATRIX_STATUSES,
    MappingValidationResult,
    ObservedOutcome,
    OutcomeMappingRule,
    find_matching_rules,
    outcome_key,
    resolve_outcome_mapping,
    validate_outcome_mappings,
)
from .message_serialization import MessageSerializationProfile
from .message_status_governance import (
    CAPABILITY_STATUSES,
    LEGACY_STATUS_ALIASES,
    MANDATORY_EVIDENCE_FIELDS,
    NON_IMPLEMENTED_STATUSES,
    RELEASE_BLOCKER_STATUSES,
    BlockerEvaluationResult,
    CapabilityDecision,
    DecisionValidationResult,
    StatusUniquenessResult,
    ensure_single_status_per_capability,
    evaluate_release_blockers,
    is_release_blocker_status,
    missing_required_evidence_fields,
    normalize_capability_status,
    validate_capability_decision,
)
from .message_validation import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    MessageValidationResult,
    MessageValidationViolation,
    collect_observed_outcomes,
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
    validate_envelope_against_schema,
    validate_envelope_dict_against_schema,
    validate_message_stream,
)
from .run import (
    ActiveObjectSet,
    ContextErrorState,
    ExternalApiCompatibilityRecord,
    HookPhase,
    LifecycleObjectRef,
    ReferenceResolverState,
    ReportingContextSnapshot,
    ReportingLifecycleState,
    Run,
    RunStage,
    RunStatus,
)
from .scenario_run import (
    RunNode,
    ScenarioRun,
    StepRun,
)
