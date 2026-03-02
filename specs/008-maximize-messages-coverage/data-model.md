# Data Model: Maximize Messages Capability Coverage

## Entities

### MessageCapability
Catalog entry generated from upstream `messages` schema inventory.

**Fields**
- `capability_id` (string, required, unique)
- `baseline_release` (string, required)
- `name` (string, required)
- `description` (string, required)
- `category` (enum: `core`, `lifecycle`, `hook`, `attachment`, `parameter`, `metadata`)
- `relevance` (enum: `relevant`, `out_of_scope`)
- `source_reference` (string, required)

**Validation rules**
- `capability_id` is stable for weekly diffing within a baseline release.
- Inventory generation must include each relevant capability exactly once.

### MandatoryCapabilityScope
Release-specific mandatory implementation scope loaded from the normative list file.

**Fields**
- `release_target` (string, required)
- `scope_source_path` (string, required, absolute path)
- `capability_ids` (array[string], required, unique items)
- `scope_version_hash` (string, required)
- `loaded_at` (datetime string, required)

**Validation rules**
- For this feature, `scope_source_path` MUST be `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt`.
- `capability_ids` cardinality MUST equal `323` for the approved release target.
- Every mandatory `capability_id` must exist in `MessageCapability`.

### CapabilityDecision
Governance status for one capability in one release target.

**Fields**
- `capability_id` (string, required, foreign key -> `MessageCapability.capability_id`)
- `status` (enum: `Implemented`, `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, `Pending`)
- `rationale` (string, conditionally required)
- `decision_owner` (string, conditionally required)
- `evidence_refs` (array[string], conditionally required)
- `reviewed_at` (datetime string, conditionally required)
- `release_target` (string, required)

**Validation rules**
- Exactly one active decision per (`capability_id`, `release_target`).
- Non-implemented statuses require `rationale`, `decision_owner`, `evidence_refs`, `reviewed_at`.
- For capability IDs in `MandatoryCapabilityScope`, only `Implemented` is permitted at release gate.

### RuntimeCoverageObservation
Observed coverage evidence from emitted message stream.

**Fields**
- `run_id` (string, required)
- `capability_id` (string, required, foreign key -> `MessageCapability.capability_id`)
- `payload_kind` (string, required)
- `payload_path` (string, required)
- `observed_at` (datetime string, required)
- `evidence_scenario_id` (string, nullable)

**Validation rules**
- Capability ID derivation must use canonical normalized matching.
- Observations for mandatory IDs are required for `Implemented` release status.

### OutcomeMappingRule
Deterministic mapping from runtime outcome classes to capability IDs.

**Fields**
- `mapping_id` (string, required, unique)
- `outcome_scope` (enum: `run`, `scenario`, `step`, `hook`, `attachment`)
- `outcome_status` (enum: `passed`, `failed`, `skipped`, `undefined`, `interrupted`, `retry`)
- `capability_ids` (array[string], required, min length 1)
- `priority` (integer, required, `>= 0`)
- `mapping_rationale` (string, required)

**Validation rules**
- Priority order must deterministically resolve ties.
- Fixed readiness matrix outcomes must map with 100% determinism.

### GovernanceReport
Release-facing summary artifact generated from inventory + observations + decisions.

**Fields**
- `version` (string, required)
- `generated_at` (datetime string, required)
- `baseline_release` (string, required)
- `summary.total_capabilities` (integer)
- `summary.implemented_capabilities` (integer)
- `summary.blocked_capabilities` (integer)
- `summary.deferred_capabilities` (integer)
- `summary.coverage_percentage` (number)
- `summary.mandatory_capabilities_total` (integer, optional)
- `summary.mandatory_capabilities_implemented` (integer, optional)
- `summary.mandatory_scope_violations` (integer, optional)
- `capabilities[]` (array of capability status records)

**Validation rules**
- `capabilities[]` must contain one row per `MessageCapability` in-scope inventory.
- `mandatory_scope_violations` must be `0` for release readiness pass.

### BaselineDiffRecord
Weekly comparison between previous and current baseline snapshots.

**Fields**
- `cadence` (enum: `weekly`)
- `previous_release` (string, required)
- `current_release` (string, required)
- `added_capability_ids` (array[string])
- `changed_capability_ids` (array[string])
- `removed_capability_ids` (array[string])
- `generated_at` (datetime string, required)

**Validation rules**
- `previous_release` and `current_release` differ.
- Non-empty change sets require governance review before release sign-off.

## Relationships
- `MessageCapability` 1 -> N `CapabilityDecision`
- `MessageCapability` 1 -> N `RuntimeCoverageObservation`
- `MandatoryCapabilityScope` 1 -> N `CapabilityDecision` (by `release_target` + `capability_id`)
- `OutcomeMappingRule` N -> N `MessageCapability`
- `GovernanceReport` aggregates `MessageCapability`, `RuntimeCoverageObservation`, and `CapabilityDecision`
- `BaselineDiffRecord` references `MessageCapability` IDs for delta computation

## State Transitions

### CapabilityDecision Lifecycle (non-mandatory IDs)
1. `Pending` -> `Implemented`
2. `Pending` -> `Non-Implementable`
3. `Pending` -> `Not-Applicable`
4. `Pending` -> `Not-Acceptable`
5. Any non-implemented status -> `Implemented` after evidence and review

### CapabilityDecision Lifecycle (mandatory IDs)
1. `Pending` -> `Implemented`
2. Any transition to `Non-Implementable`, `Not-Applicable`, or `Not-Acceptable` is invalid for release gate

### Governance Gate Outcome
1. PASS when all mandatory IDs are `Implemented`, no blockers, and evidence fields are complete
2. FAIL when any mandatory ID is not `Implemented`, any duplicate decision exists, or any blocker remains
