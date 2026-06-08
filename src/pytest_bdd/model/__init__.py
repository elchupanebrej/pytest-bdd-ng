# init: public-api  # init: no-check
"""
Provide src.pytest_bdd.model package helpers.

Responsibility:
    Provide src.pytest_bdd.model package helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `model`
    - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `model`

State and side effects:
    depends on execution_message_adapter.ExecutionMessageAdapter, execution_message_adapter.ExecutionProjection,
    feature_binding.FeatureRuntimeBinding, message_baseline_diff.WEEKLY_CADENCE,
    message_baseline_diff.BaselineComparisonSchedule.

Invariants:
    - `pytest_bdd.model` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

from .execution_message_adapter import ExecutionMessageAdapter as ExecutionMessageAdapter
from .execution_message_adapter import ExecutionProjection as ExecutionProjection
from .feature_binding import FeatureRuntimeBinding as FeatureRuntimeBinding
from .message_baseline_diff import (
    WEEKLY_CADENCE as WEEKLY_CADENCE,
)
from .message_baseline_diff import (
    BaselineComparisonSchedule as BaselineComparisonSchedule,
)
from .message_baseline_diff import (
    BaselineDiffExecutionResult as BaselineDiffExecutionResult,
)
from .message_baseline_diff import (
    BaselineDiffRecord as BaselineDiffRecord,
)
from .message_baseline_diff import (
    build_baseline_diff as build_baseline_diff,
)
from .message_baseline_diff import (
    execute_weekly_baseline_diff as execute_weekly_baseline_diff,
)
from .message_baseline_diff import (
    is_weekly_run_due as is_weekly_run_due,
)
from .message_baseline_diff import (
    next_weekly_run_at as next_weekly_run_at,
)
from .message_capability import (
    RELEVANT_IMPACTS as RELEVANT_IMPACTS,
)
from .message_capability import (
    MessageCapability as MessageCapability,
)
from .message_capability import (
    capability_is_relevant as capability_is_relevant,
)
from .message_capability import (
    classify_capability_relevance as classify_capability_relevance,
)
from .message_capability_inventory import CapabilitySyncResult as CapabilitySyncResult
from .message_capability_inventory import sync_capability_inventory as sync_capability_inventory
from .message_converter import governance_value_to_dict as governance_value_to_dict
from .message_converter import message_converter as message_converter
from .message_converter import validate_envelope_shape as validate_envelope_shape
from .message_governance_checklist import (
    DEFAULT_CHECKLIST_NAME as DEFAULT_CHECKLIST_NAME,
)
from .message_governance_checklist import (
    GovernanceChecklist as GovernanceChecklist,
)
from .message_governance_checklist import (
    GovernanceChecklistEntry as GovernanceChecklistEntry,
)
from .message_governance_checklist import (
    build_governance_checklist as build_governance_checklist,
)
from .message_governance_checklist import (
    render_checklist_markdown as render_checklist_markdown,
)
from .message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1 as MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
)
from .message_outcome_mapping import (
    REQUIRED_MATRIX_STATUSES as REQUIRED_MATRIX_STATUSES,
)
from .message_outcome_mapping import (
    MappingValidationResult as MappingValidationResult,
)
from .message_outcome_mapping import (
    ObservedOutcome as ObservedOutcome,
)
from .message_outcome_mapping import (
    OutcomeMappingRule as OutcomeMappingRule,
)
from .message_outcome_mapping import (
    find_matching_rules as find_matching_rules,
)
from .message_outcome_mapping import (
    outcome_key as outcome_key,
)
from .message_outcome_mapping import (
    resolve_outcome_mapping as resolve_outcome_mapping,
)
from .message_outcome_mapping import (
    validate_outcome_mappings as validate_outcome_mappings,
)
from .message_serialization import MessageSerializationProfile as MessageSerializationProfile
from .message_status_governance import (
    CAPABILITY_STATUSES as CAPABILITY_STATUSES,
)
from .message_status_governance import (
    LEGACY_STATUS_ALIASES as LEGACY_STATUS_ALIASES,
)
from .message_status_governance import (
    MANDATORY_EVIDENCE_FIELDS as MANDATORY_EVIDENCE_FIELDS,
)
from .message_status_governance import (
    NON_IMPLEMENTED_STATUSES as NON_IMPLEMENTED_STATUSES,
)
from .message_status_governance import (
    RELEASE_BLOCKER_STATUSES as RELEASE_BLOCKER_STATUSES,
)
from .message_status_governance import (
    BlockerEvaluationResult as BlockerEvaluationResult,
)
from .message_status_governance import (
    CapabilityDecision as CapabilityDecision,
)
from .message_status_governance import (
    DecisionValidationResult as DecisionValidationResult,
)
from .message_status_governance import (
    StatusUniquenessResult as StatusUniquenessResult,
)
from .message_status_governance import (
    ensure_single_status_per_capability as ensure_single_status_per_capability,
)
from .message_status_governance import (
    evaluate_release_blockers as evaluate_release_blockers,
)
from .message_status_governance import (
    is_release_blocker_status as is_release_blocker_status,
)
from .message_status_governance import (
    missing_required_evidence_fields as missing_required_evidence_fields,
)
from .message_status_governance import (
    normalize_capability_status as normalize_capability_status,
)
from .message_status_governance import (
    validate_capability_decision as validate_capability_decision,
)
from .message_validation import (
    ALLOWED_IMPLEMENTATION_STATUSES as ALLOWED_IMPLEMENTATION_STATUSES,
)
from .message_validation import (
    MessageValidationResult as MessageValidationResult,
)
from .message_validation import (
    MessageValidationViolation as MessageValidationViolation,
)
from .message_validation import (
    collect_observed_outcomes as collect_observed_outcomes,
)
from .message_validation import (
    default_outcome_mapping_rules as default_outcome_mapping_rules,
)
from .message_validation import (
    observed_outcome_from_envelope as observed_outcome_from_envelope,
)
from .message_validation import (
    validate_envelope_against_schema as validate_envelope_against_schema,
)
from .message_validation import (
    validate_envelope_dict_against_schema as validate_envelope_dict_against_schema,
)
from .message_validation import (
    validate_message_stream as validate_message_stream,
)
from .run import (
    ActiveObjectSet as ActiveObjectSet,
)
from .run import (
    ContextErrorState as ContextErrorState,
)
from .run import (
    ExternalApiCompatibilityRecord as ExternalApiCompatibilityRecord,
)
from .run import (
    HookPhase as HookPhase,
)
from .run import (
    LifecycleObjectRef as LifecycleObjectRef,
)
from .run import (
    ReferenceResolverState as ReferenceResolverState,
)
from .run import (
    ReportingContextSnapshot as ReportingContextSnapshot,
)
from .run import (
    ReportingLifecycleState as ReportingLifecycleState,
)
from .run import (
    Run as Run,
)
from .run import (
    RunStage as RunStage,
)
from .run import (
    RunStatus as RunStatus,
)
from .scenario_run import (
    RunNode as RunNode,
)
from .scenario_run import (
    ScenarioRun as ScenarioRun,
)
from .scenario_run import (
    StepRun as StepRun,
)
