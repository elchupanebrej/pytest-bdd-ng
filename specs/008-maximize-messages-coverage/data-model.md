# Data Model: Maximize Messages Capability Coverage

## Entities

### MessageCapability
Represents one relevant capability from the approved upstream baseline.

**Fields**
- `capability_id` (string, required, unique)
- `baseline_release` (string, required)
- `name` (string, required)
- `description` (string, required)
- `category` (enum: `core`, `lifecycle`, `hook`, `attachment`, `parameter`, `metadata`)
- `relevance` (enum: `relevant`, `out_of_scope`)
- `source_reference` (string, required)

**Validation rules**
- `capability_id` must be stable across weekly comparisons.
- Entries marked `out_of_scope` must still remain present in the canonical inventory.

### CapabilityDecision
Represents governance status and evidence for a capability.

**Fields**
- `capability_id` (string, required, foreign key -> `MessageCapability.capability_id`)
- `status` (enum: `Implemented`, `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, `Pending`)
- `rationale` (string, conditionally required)
- `decision_owner` (string, conditionally required)
- `evidence_refs` (array[string], conditionally required)
- `reviewed_at` (datetime string, conditionally required)
- `release_target` (string, required)

**Validation rules**
- Exactly one status per capability.
- For statuses other than `Implemented`, `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at` are mandatory.

### OutcomeMappingRule
Defines deterministic mapping from runtime outcomes to capability IDs.

**Fields**
- `mapping_id` (string, required, unique)
- `outcome_scope` (enum: `run`, `scenario`, `step`, `hook`, `attachment`)
- `outcome_status` (enum: `passed`, `failed`, `skipped`, `undefined`, `interrupted`)
- `capability_ids` (array[string], required, min length 1)
- `priority` (integer, required, >= 0)
- `mapping_rationale` (string, required)

**Validation rules**
- Priority ordering must yield deterministic winner resolution.
- Unmapped statuses in governed mode are treated as failures.

### CoverageEvidence
Stores observed runtime evidence for capability coverage.

**Fields**
- `run_id` (string, required)
- `capability_id` (string, required, foreign key -> `MessageCapability.capability_id`)
- `evidence_scenario_id` (string, required)
- `payload_path` (string, required)
- `observed_at` (datetime string, required)

**Validation rules**
- State-dependent capabilities require at least one linked evidence scenario.
- Evidence must be traceable to emitted runtime outcomes.

### GovernanceChecklistEntry
Release-facing summary for sign-off decisions.

**Fields**
- `capability_id` (string, required)
- `status` (same enum as `CapabilityDecision.status`)
- `disposition` (enum: `approved`, `blocked`, `deferred`)
- `open_risk` (string, nullable)
- `evidence_refs` (array[string])

**Validation rules**
- Every relevant capability has exactly one checklist entry per release target.
- Entries with unresolved evidence cannot have `approved` disposition.

### BaselineDiffRecord
Weekly comparison between prior and current approved baseline.

**Fields**
- `cadence` (enum: `weekly`)
- `previous_release` (string, required)
- `current_release` (string, required)
- `added_capability_ids` (array[string])
- `changed_capability_ids` (array[string])
- `removed_capability_ids` (array[string])
- `generated_at` (datetime string, required)

**Validation rules**
- `previous_release` and `current_release` must differ.
- Non-empty change arrays require governance review before release sign-off.

## Relationships
- `MessageCapability` 1 -> N `CapabilityDecision`
- `MessageCapability` 1 -> N `CoverageEvidence`
- `MessageCapability` 1 -> N `GovernanceChecklistEntry`
- `OutcomeMappingRule` N -> N `MessageCapability`
- `BaselineDiffRecord` references `MessageCapability` IDs to describe change sets

## State Transitions

### CapabilityDecision Lifecycle
1. `Pending` -> `Implemented`
2. `Pending` -> `Non-Implementable`
3. `Pending` -> `Not-Acceptable`
4. `Pending` -> `Not-Applicable`
5. Any non-implemented status -> `Implemented` after new evidence and review

### GovernanceChecklistEntry Lifecycle
1. `blocked` when evidence is missing or inconsistent
2. `deferred` when explicitly accepted for later scope
3. `approved` only when evidence and decision policy are fully satisfied
