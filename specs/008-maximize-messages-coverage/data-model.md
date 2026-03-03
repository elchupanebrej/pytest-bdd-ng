# Data Model: Maximize Messages Capability Coverage

## Entities

### MessageCapability
Canonical capability record generated from upstream `messages` schema inventory.

**Fields**
- `capability_id` (string, required, unique)
- `baseline_release` (string, required)
- `name` (string, required)
- `description` (string, required)
- `category` (enum: `core`, `lifecycle`, `hook`, `attachment`, `parameter`, `metadata`)
- `relevance` (enum: `relevant`, `out_of_scope`)
- `source_reference` (string, required)

**Validation rules**
- `capability_id` must remain stable inside one release cycle.
- Relevant capabilities must appear exactly once in canonical inventory output.

### GovernanceScope
Release-scoped mandatory capability set loaded from normative list.

**Fields**
- `release_target` (string, required)
- `scope_source_path` (string, required)
- `capability_ids` (array[string], required, unique items)
- `scope_hash` (string, required)
- `loaded_at` (datetime string, required)

**Validation rules**
- Every scope ID must exist in `MessageCapability`.
- Scope file hash drift requires governance review.

### RuntimeRequiredScope
Subset that must be covered by real runtime evidence.

**Fields**
- `release_target` (string, required)
- `capability_ids` (array[string], required, unique items)
- `scope_source` (string, required)
- `updated_at` (datetime string, required)

**Validation rules**
- Runtime-required IDs must be subset of governance scope and canonical inventory.
- Scope updates must be justified by extraction feasibility analysis.

### RuntimeCoverageObservation
Observed capability evidence extracted from emitted NDJSON stream.

**Fields**
- `run_id` (string, required)
- `capability_id` (string, required)
- `payload_kind` (string, required)
- `payload_path` (string, required)
- `observed_at` (datetime string, required)
- `evidence_scenario_id` (string, nullable)

**Validation rules**
- Observations must come only from real emitted runtime events.
- Canonical capability ID normalization must be deterministic.

### ExtractionFeasibilityRecord
Assessment entry for whether a capability can be extracted from Python runtime/hook surfaces.

**Fields**
- `capability_id` (string, required)
- `release_target` (string, required)
- `classification` (enum: `extractable_now`, `extractable_after_plugin_extension`, `objectively_unreachable`)
- `assessment_owner` (string, required)
- `assessment_notes` (string, required)
- `evidence_refs` (array[string], required)
- `reviewed_at` (datetime string, required)

**Validation rules**
- `extractable_after_plugin_extension` cannot be mapped to `Non-Implementable`.
- `objectively_unreachable` requires hard limitation evidence and recheck policy.

### CapabilityDecision
Governance decision for one capability in one release target.

**Fields**
- `capability_id` (string, required, foreign key -> `MessageCapability.capability_id`)
- `release_target` (string, required)
- `status` (enum: `Implemented`, `Pending`, `Non-Implementable`, `Not-Applicable`, `Not-Acceptable`)
- `rationale` (string, conditionally required)
- `hard_limitation` (string, required when `status=Non-Implementable`)
- `decision_owner` (string, conditionally required)
- `evidence_refs` (array[string], conditionally required)
- `reviewed_at` (datetime string, conditionally required)
- `recheck_trigger` (string, required when `status=Non-Implementable`)

**Validation rules**
- Exactly one active decision per (`capability_id`, `release_target`).
- Non-implemented statuses require rationale, owner, evidence, and review timestamp.
- `Non-Implementable` requires hard limitation statement and recheck trigger.
- Review timestamp outside current release cycle downgrades effective status to `Pending`.

### OutcomeMappingRule
Deterministic mapping from runtime outcome classes to capability IDs.

**Fields**
- `mapping_id` (string, required, unique)
- `outcome_scope` (enum: `run`, `scenario`, `step`, `hook`, `attachment`)
- `outcome_status` (enum: `passed`, `failed`, `skipped`, `undefined`, `interrupted`, `retry`)
- `capability_ids` (array[string], required, min length 1)
- `priority` (integer, required, >= 0)
- `mapping_rationale` (string, required)

**Validation rules**
- Priority order must produce deterministic rule resolution.
- Fixed readiness matrix must yield zero unmapped and zero ambiguous outcomes.

### GovernanceCapabilityRecord
Per-capability record in generated governance report.

**Fields**
- `capability_id` (string, required)
- `status` (enum, required)
- `disposition` (enum: `approved`, `blocked`, `deferred`)
- `mandatory_scope` (boolean, required)
- `runtime_required` (boolean, required)
- `observed_runtime` (boolean, required)
- `rationale` (string, optional)
- `hard_limitation` (string, optional)
- `decision_owner` (string, optional)
- `reviewed_at` (datetime string, optional)
- `evidence_refs` (array[string], optional)
- `open_risk` (string, optional)
- `recheck_trigger` (string, optional)

**Validation rules**
- `runtime_required=true` and `observed_runtime=false` is release-blocking.
- `Non-Implementable` requires `hard_limitation` and `recheck_trigger`.

### GovernanceReport
Release-facing aggregate report from inventory + observations + decisions.

**Fields**
- `version` (string, required)
- `generated_at` (datetime string, required)
- `baseline_release` (string, required)
- `summary.total_capabilities` (integer)
- `summary.implemented_capabilities` (integer)
- `summary.blocked_capabilities` (integer)
- `summary.deferred_capabilities` (integer)
- `summary.coverage_percentage` (number)
- `summary.runtime_required_total` (integer)
- `summary.runtime_required_covered` (integer)
- `summary.runtime_required_missing` (integer)
- `summary.non_runtime_required_total` (integer)
- `summary.non_runtime_covered` (integer)
- `summary.non_runtime_classified` (integer)
- `summary.mandatory_scope_violations` (integer)
- `capabilities[]` (array of `GovernanceCapabilityRecord`)

**Validation rules**
- Every in-scope capability appears exactly once in `capabilities[]`.
- Release pass requires `runtime_required_missing == 0` and `blocked_capabilities == 0`.

### BaselineDiffRecord
Weekly baseline comparison artifact.

**Fields**
- `cadence` (enum: `weekly`)
- `previous_release` (string, required)
- `current_release` (string, required)
- `added_capability_ids` (array[string])
- `changed_capability_ids` (array[string])
- `removed_capability_ids` (array[string])
- `generated_at` (datetime string, required)

**Validation rules**
- Baseline versions must differ.
- Non-empty drift sets require explicit governance review.

## Relationships

- `MessageCapability` 1 -> N `CapabilityDecision`
- `MessageCapability` 1 -> N `RuntimeCoverageObservation`
- `MessageCapability` 1 -> N `ExtractionFeasibilityRecord`
- `GovernanceScope` 1 -> N `GovernanceCapabilityRecord`
- `RuntimeRequiredScope` 1 -> N `GovernanceCapabilityRecord`
- `OutcomeMappingRule` N -> N `MessageCapability`
- `GovernanceReport` aggregates inventory, observations, and decisions
- `BaselineDiffRecord` references `MessageCapability` IDs for delta computation

## State Transitions

### Extraction Feasibility Lifecycle
1. `extractable_after_plugin_extension` -> `extractable_now` after reporter/plugin implementation.
2. `objectively_unreachable` -> `extractable_after_plugin_extension` when runtime/hook surfaces expand.
3. Any classification -> re-evaluated on `recheck_trigger` activation.

### CapabilityDecision Lifecycle
1. `Pending` -> `Implemented`
2. `Pending` -> `Non-Implementable`
3. `Pending` -> `Not-Applicable`
4. `Pending` -> `Not-Acceptable`
5. Non-implemented status -> `Implemented` after real runtime evidence and review

### Effective Governance Resolution
For each capability in canonical inventory:
1. If runtime observed -> effective status `Implemented`
2. Else if runtime-required -> effective status `Pending` and disposition `blocked`
3. Else if non-runtime-required with valid explicit classification -> disposition by status (`approved` or `deferred`)
4. Else -> effective status `Pending` and disposition `blocked`

### Governance Gate Outcome
1. PASS when runtime-required capabilities are fully observed and blocker count is zero
2. FAIL when runtime-required coverage is incomplete, decisions are invalid/duplicate, or blocker statuses remain
