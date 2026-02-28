# Data Model: Maximize Messages Capability Coverage

## Entities

### CapabilityInventory
A collection of all possible fields and payloads derived from the `messages` schema.
- **payload_kinds**: List of top-level envelope fields (e.g., `testCaseStarted`).
- **fields**: Map of `(payload_kind, field_path)` to `FieldMetadata`.

### FieldMetadata
- **path**: Dot-separated path to the field.
- **type**: Data type from schema (string, integer, object, etc.).
- **is_required**: Boolean.
- **description**: Documentation from schema.

### ObservedCoverage
Runtime data collected during test execution.
- **observed_fields**: Set of `(payload_kind, field_path)` that were actually populated.
- **evidence_scenarios**: Map of `(payload_kind, field_path)` to the test case ID that provided the first evidence.

### GovernanceReport
The final artifact for release sign-off.
- **total_fields**: Count of all fields in inventory.
- **covered_fields**: Count of observed fields.
- **coverage_percentage**: (covered / total) * 100.
- **gaps**: List of fields marked as "Pending" or "Non-Implementable" with their rationales.

## State Transitions

### Field Coverage Lifecycle
1. **Unobserved**: Field exists in inventory but not yet seen in runtime.
2. **Observed**: Field detected in at least one emitted message.
3. **Verified**: Field observed AND matches the expected value/structure in a specific test scenario.
4. **Documented (Exclusion)**: Field is unobserved but has a valid `Non-Implementable` or `Not-Applicable` rationale.

## Validation Rules
- Every emitted `Envelope` MUST be valid against `Envelope.json`.
- Every field in an emitted `Envelope` MUST be recorded in `ObservedCoverage`.
- All fields in `CapabilityInventory` MUST either be `Observed` or have a documented decision in the Governance Report.
