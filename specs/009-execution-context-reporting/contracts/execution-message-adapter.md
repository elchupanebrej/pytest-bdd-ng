# Contract: Execution Message Adapter

## Scope

Defines the adapter boundary between runtime execution model and cucumber message model used for reporting.

## Responsibilities

`ExecutionMessageAdapter` MUST:
- serialize execution-side runtime state/events into message-model payloads;
- deserialize message-model payloads into execution-side projections;
- preserve deterministic IDs and reference relationships required by reporting and governance.

## Conversion Rules

1. Runtime path:
   - Execution plugins own runtime objects and context mutations.
   - Reporter requests message payloads through adapter serialization only.

2. Reporting path:
   - Message payloads are emitted after adapter conversion.
   - Reporter transport (`_emit_envelope`) never mutates execution context.

3. Deserialization path:
   - Adapter reconstructs execution projection using context-owned registries.
   - Missing references produce deterministic diagnostics, not synthetic objects.

## Registry & ID Contract

- AST lookup source: `ExecutionContext.gherkin_registry.ast_node_by_id`
- Message reference source: `ExecutionContext.message_reference_index`
- Required deterministic key shape: `(worker_id, payload_kind, payload_id)`
- Python memory identity (`id(...)`) is allowed only for in-process optimization maps and is non-canonical.

## Wire Compatibility

- Adapter uses existing `message_converter` for envelope wire conversion.
- No schema mutation outside cucumber-messages contract.

## Failure Handling

- Missing context / registry entries => deterministic diagnostic record and nullable link resolution.
- Duplicate deterministic registry key => deterministic conflict diagnostic.
- Adapter must not auto-generate fabricated IDs for missing runtime links.

## Validation Requirements

- Round-trip tests (`execution -> message -> execution`) preserve required IDs and links.
- Adapter serialization tests assert message-emission payloads come from adapter path.
- Negative tests assert missing-link behavior remains deterministic and non-fabricating.
