# Data Model: Execution Context Reporting Consistency

## Entity: SessionExecutionContext

Purpose: Session-root runtime context shared by scenario-scoped execution contexts.

Fields:
- `session_context_id: str` (required, unique per pytest session)
- `run_ref: LifecycleObjectRef` (required)
- `status: ExecutionStatus` (required)
- `transition_index: int` (required, monotonic)
- `active_feature_context_id: str | None`
- `active_scenario_context_id: str | None`
- `active_step_context_id: str | None`
- `reporting_state: ReportingLifecycleState` (required)
- `last_error: ContextErrorState | None`

Validation rules:
- Transition index is monotonic increasing.
- Active IDs must reference open context nodes.

## Entity: ExecutionContext

Purpose: Scenario-scoped runtime execution model; single source of truth for runtime and reporting lookup.

Fields:
- `context_id: str` (required)
- `run_ref|feature_ref|scenario_ref|step_ref|previous_step_ref: LifecycleObjectRef | None`
- `active_hook: HookPhase`
- `stage: ExecutionStage`
- `status: ExecutionStatus`
- `active_set: ActiveObjectSet`
- `transition_index: int`
- `session_context: SessionExecutionContext | None`
- `feature_node|scenario_node|step_node: ExecutionContextNode | None`
- `feature_object|scenario_object|step_object|previous_step_object: Any | None`
- `reporting_state: ReportingLifecycleState`
- `gherkin_registry: GherkinRegistryState`
- `reference_resolver: ReferenceResolverState`
- `message_reference_index: MessageReferenceIndex` (new)

Validation rules:
- Reporter code reads but does not mutate context state.
- `message_reference_index` keys are deterministic and worker-safe.

State transitions:
- `idle -> scenario_setup -> scenario_running -> step_running -> scenario_running -> scenario_teardown -> finished`
- `status: ok -> failed|interrupted`

## Entity: ReportingLifecycleState

Purpose: Runtime correlation IDs and transient lifecycle mappings used for message emission.

Fields:
- `run_started_id: str | None`
- `test_run_hook_started_id: str | None`
- `active_test_case_id: str | None`
- `active_test_case_started_id: str | None`
- `active_test_step_id: str | None`
- `runtime_step_to_test_step_id: dict[int, str]`
- `scenario_attempt_context: dict[str, str | int] | None`
- `step_started_timestamp: Timestamp | None`
- `step_finished_timestamp: Timestamp | None`

Validation rules:
- Scenario-scoped fields reset on scenario completion.
- No synthetic fallback IDs are generated.

## Entity: GherkinRegistryState

Purpose: AST node registry used by runtime lookup and reference reconstruction.

Fields:
- `source_uri: str | None`
- `ast_node_by_id: dict[str, Any]`

Validation rules:
- Keys are stable AST IDs.
- Registry is write-owned by execution flow; reporters read-only.

## Entity: MessageReferenceIndex

Purpose: Context-owned index for message-model object lookup and reverse binding during deserialize.

Fields:
- `entries: dict[tuple[str, str, str], MessageReferenceRecord]`
  - key shape: `(worker_id, payload_kind, payload_id)`

Validation rules:
- Keys must be deterministic.
- Duplicate key insertion is deterministic conflict (diagnostic + reject overwrite unless same payload identity).

## Entity: MessageReferenceRecord

Purpose: Registry record binding message IDs to execution/runtime object references.

Fields:
- `worker_id: str`
- `payload_kind: str`
- `payload_id: str`
- `runtime_ref_kind: LifecycleKind | None`
- `runtime_object_key: str | None` (stable key, not Python memory id)
- `ast_node_ids: tuple[str, ...]`

Validation rules:
- `payload_id` required for all records.
- Runtime key optional for message-only entities, required for round-trip-required entities.

## Entity: ExecutionMessageAdapter

Purpose: Adapter boundary converting execution model <-> cucumber message model.

Operations:
- `serialize(context, runtime_event) -> Message`
- `deserialize(context, message) -> ExecutionProjection`

Validation rules:
- Conversion is deterministic for equal inputs.
- Uses `message_converter` for wire-shape compatibility.
- Resolves/rebuilds links only through `gherkin_registry` and `message_reference_index`.

## Entity: ExecutionProjection

Purpose: Deserialized execution-side projection reconstructed from message model for replay/validation paths.

Fields:
- `run_started_id|test_case_id|test_step_id|hook_ids: str | None`
- `linked_runtime_keys: tuple[str, ...]`
- `linked_ast_node_ids: tuple[str, ...]`
- `diagnostics: tuple[str, ...]`

Validation rules:
- Missing links yield deterministic diagnostics, never synthetic object fabrication.

## Entity: GovernanceDecision

Purpose: Capability classification for uncovered fields in coverage governance.

Fields:
- `capability_id: str`
- `status: CapabilityStatus`
- `release_target: str`
- `rationale: str | None`
- `hard_limitation: str | None`
- `evidence_refs: tuple[str, ...]`
- `recheck_trigger: str | None`

Validation rules:
- Runtime-required fields must be runtime-observed.
- `Non-Implementable` requires objective hard limitation + recheck trigger.
- `Partly-Applicable` must document language/runtime model mismatch.
