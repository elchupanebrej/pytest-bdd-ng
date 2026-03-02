# Messages Coverage

This project ensures 100% field-level coverage of the `messages` protocol.
It uses schema-driven inventory generation and dynamic runtime traceability to provide full visibility into protocol adoption.

## Capability Status Definitions

* **Implemented**: The capability is fully implemented and mapped.
* **Non-Implementable**: The capability cannot be supported due to technical constraints or language differences.
* **Not-Acceptable**: The capability represents an undesired functionality that violates the implementation principles.
* **Not-Applicable**: The capability does not apply to pytest-bdd-ng execution flows.
* **Pending**: The capability is recognized but not yet evaluated or implemented.

## Governance Dispositions

* **approved**: Capability evidence and policy checks are satisfied for release.
* **blocked**: Capability evidence is missing, inconsistent, or unresolved.
* **deferred**: Capability is intentionally postponed with explicit governance decision.

## Baseline Drift Governance

Weekly baseline drift checks compare previously approved and current capability snapshots.
Any added, changed, or removed capability IDs are treated as governance review inputs before sign-off.
