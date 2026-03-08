# Data Model: Execution Context Reporting Consistency

## Entity: Run

Purpose: Session-wide runtime root shared across plugins through `pytest.config.stash`.

Fields:
- `id: str` (required, unique per pytest session)
- `run_ref: LifecycleObjectRef` (required)
- `status: RunStatus` (`ok | failed | interrupted`)
- `transition_index: int` (monotonic)
- `feature_bindings_by_uri: dict[str, FeatureRuntimeBinding]`
- `scenario_runs_by_request: dict[str, ScenarioRun]`
- `active_scenario_run: ScenarioRun | None`
- `active_feature_uri: str | None`
- `active_scenario_id: str | None`
- `active_step_id: str | None`
- `last_error: ContextErrorState | None`
- `reporting_state: ReportingLifecycleState`

Relationships:
- Owns many `FeatureRuntimeBinding` records keyed by canonical feature URI.
- Owns many `ScenarioRun` instances keyed by request identity.
- Owns one `ReportingLifecycleState`.
- Shares one `EnvelopeRegistry` through stash key `_pytest_bdd_envelope_registry`.

Validation rules:
- Exactly one `Run` is stored per pytest session stash key `_pytest_bdd_run`.
- `transition_index` only increments.
- `active_feature_uri` must resolve to an existing `FeatureRuntimeBinding` while a scenario is active.

## Entity: FeatureRuntimeBinding

Purpose: Run-owned feature-level execution and lookup state replacing the removed `Feature` adapter.

Fields:
- `uri: str` (required, unique per feature document)
- `filename: str` (required)
- `rel_filename: str | None`
- `source: Source` (required)
- `gherkin_document: GherkinDocument` (required)
- `pickles: tuple[Pickle, ...]`
- `ast_registry: dict[str, Any]`
- `name: str | None`
- `line_number: int | None`
- `description: str | None`
- `tag_names: tuple[str, ...]`

Relationships:
- Owned by exactly one `Run`.
- Referenced by one or more `ScenarioRun` instances via `feature_uri`.

Validation rules:
- `ast_registry` is derived from `gherkin_document` and remains deterministic for identical source input.
- `pickles` are compiled from the bound `gherkin_document`, not from a wrapper adapter.
- No hook, fixture, or reporter API exposes `FeatureRuntimeBinding` directly; it is accessed through `Run`.

## Entity: ScenarioRun

Purpose: Scenario/request-scoped runtime execution state used by hooks, runners, and reporting readers.

Fields:
- `id: str` (required)
- `run_ref: LifecycleObjectRef`
- `active_hook: HookPhase`
- `stage: RunStage`
- `status: RunStatus`
- `active_set: ActiveObjectSet`
- `transition_index: int`
- `feature_uri: str | None`
- `gherkin_document: GherkinDocument | None`
- `feature_source: Source | None`
- `pickle: Pickle | None`
- `step_object: PickleStep | None`
- `previous_step_object: Any | None`
- `feature_ref | scenario_ref | step_ref | previous_step_ref: LifecycleObjectRef | None`
- `feature_node | scenario_node | step_node: RunNode | None`
- `reference_resolver: ReferenceResolverState`
- `run: Run | None`

Relationships:
- Belongs to exactly one `Run`.
- Resolves one active `FeatureRuntimeBinding` through `feature_uri`.

Validation rules:
- `ScenarioRun` is not stored directly in `config.stash`.
- Lifecycle transitions follow hook-driven stage mapping.
- `gherkin_document`, `feature_source`, and `pickle` must all come from the bound `FeatureRuntimeBinding`.
- No `Feature` adapter fields are allowed.

State transitions:
- `idle -> scenario_setup -> scenario_running -> step_running -> scenario_running -> scenario_teardown -> finished`

## Entity: ReportingLifecycleState

Purpose: Correlation state for cucumber message lifecycle emission.

Fields:
- `run_started_id: str | None`
- `test_run_hook_started_id: str | None`
- `active_test_case_id: str | None`
- `active_test_case_started_id: str | None`
- `active_test_step_id: str | None`
- `runtime_step_to_pickle_step_id: dict[int, str]`
- `scenario_attempt_context: dict[str, str | int] | None`
- `step_started_timestamp: Timestamp-like | None`
- `step_finished_timestamp: Timestamp-like | None`

Validation rules:
- Scenario-scoped fields reset after scenario completion.
- Correlation IDs are context-derived; synthetic backfilled IDs are disallowed.

## Entity: LifecycleObjectRef

Purpose: Typed pointer to active runtime objects used in lifecycle snapshots.

Fields:
- `kind: Literal["run", "feature", "scenario", "step"]`
- `object_id: str`
- `name: str | None`
- `source: str | None`
- `is_active: bool`

Validation rules:
- `kind="feature"` points to a feature document identity, not to a `Feature` adapter instance.
- `kind="scenario"` points to the executable runtime `Pickle`.

## Entity: EnvelopeRegistry

Purpose: Session-shared emitted message store plus identifiable object index for reference lookup.

Fields:
- `envelopes: list[EventEnvelope]`
- `identifiable: IdentifiableObjectRegistry`

Validation rules:
- Every added envelope is indexed recursively by `Identifiable.id`.
- Lookup is deterministic by stringified ID.
- Registry ownership lives with `Run`, not with parsed feature wrappers.

## Entity: IdentifiableObjectRegistry

Purpose: ID index for objects reachable from envelope payload trees.

Fields:
- `objects_by_id: dict[str, Identifiable]`

Validation rules:
- Last write wins per ID within one run stream.
- Accepts only objects conforming to the `Identifiable` protocol.

## Entity: ExecutionProjection

Purpose: Adapter-produced projection that exposes a canonical payload kind, payload object, and registry-backed lookup API.

Fields:
- `envelope: EventEnvelope`
- `payload_kind: PayloadKind`
- `payload: Any`
- `registry: IdentifiableObjectRegistry | None`

Validation rules:
- Projection creation is deterministic for equal envelope input.
- `resolve(object_id)` uses run-owned registry state only.

## Entity: GovernanceDecision

Purpose: Classification metadata for capability coverage gating.

Fields:
- `capability_id: str`
- `status: Implemented | Partly-Applicable | Non-Implementable | Not-Acceptable | Not-Applicable | Pending`
- `release_target: str`
- `rationale: str | None`
- `hard_limitation: str | None`
- `decision_owner: str | None`
- `evidence_refs: tuple[str, ...]`
- `reviewed_at: datetime | None`
- `recheck_trigger: str | None`

Validation rules:
- Runtime-required capabilities must be runtime observed.
- `Non-Implementable` requires objective hard-limitation rationale and recheck trigger.
- `Partly-Applicable` requires explicit language/runtime mismatch rationale.
