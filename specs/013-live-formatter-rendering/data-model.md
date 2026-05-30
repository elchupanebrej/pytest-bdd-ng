# Data Model: Live Formatter Rendering

## Overview

The feature extends reporting runtime state rather than introducing persistent
storage. The model therefore focuses on request normalization, live session
ownership, cross-worker delivery, final consistency artifacts, and the design
entities that enforce plugin decomposition, explicit lifecycle contracts,
first-class standalone replay, formatter-owned behavior, and single-source
discovery policy.

## Entities

### ExecutionEnvelope

Represents one reportable execution event before batching or final
consolidation.

| Field | Type | Description |
|-------|------|-------------|
| `envelope_key` | string | Stable deduplication key derived from the execution source plus the underlying message identity. |
| `source_id` | string | Execution source that emitted the envelope. |
| `message_kind` | string | Canonical message type carried by the envelope. |
| `source_sequence` | integer | Source-local order index used to preserve within-source delivery order. |
| `payload_reference` | string | Logical reference to the serialized message body carried through live delivery and canonical NDJSON. |

**Validation rules**

- `envelope_key` must be unique within the canonical stream for a run.
- `source_sequence` must be monotonic within a given `source_id`.
- The same `envelope_key` must not be rendered twice by the live formatter
  session.

### FormatterRequest

Represents one user-requested formatter output participating in the run.

| Field | Type | Description |
|-------|------|-------------|
| `request_key` | string | Stable identifier derived from the CLI flag and output target. |
| `cli_flag` | string | User-facing formatter flag that activated the request. |
| `formatter_name` | string | Canonical formatter identifier. |
| `package_name` | string | Required formatter package name. |
| `output_target` | string or null | Target path when the formatter writes a file; null when output is rendered directly to the active console stream. |
| `render_mode` | enum | `console`, `file`, or `mixed`, describing where visible output may appear. |
| `live_required` | boolean | Always true for this feature, because all active formatters consume the live stream. |

**Validation rules**

- `request_key` must be unique within a run.
- `cli_flag`, `formatter_name`, and `package_name` must resolve to one known
  formatter definition.
- `output_target` must be absent for console-only requests and present for
  required file outputs.

### LiveFormatterSession

Represents the long-lived runtime session that owns active formatters.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique identifier for the reporting session. |
| `authority_role` | enum | `single-process`, `controller`, or `disabled`. |
| `status` | enum | `pending`, `active`, `closing`, `completed`, or `failed`. |
| `requests` | list of `FormatterRequest` | Active formatter outputs attached to this session. |
| `message_sources` | set of strings | Known execution-source identifiers contributing events. |
| `delivery_error` | string or null | Actionable failure reason when live delivery becomes unreliable. |
| `canonical_stream_path` | string | Final NDJSON artifact used for consistency validation and compatibility replay. |

**State transitions**

- `pending -> active`: reporter starts and formatter session is ready to consume
  live envelopes.
- `active -> closing`: test execution ends and no more live envelopes should be
  accepted.
- `closing -> completed`: formatter cleanup finishes and final consistency
  checks pass.
- `pending|active|closing -> failed`: live delivery cannot be established or is
  interrupted in a way that invalidates reliable reporting.

### MessageDeliveryBatch

Represents a unit of incremental delivery from one execution source.

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | string | Execution source that produced the batch. |
| `batch_sequence` | integer | Monotonic per-source sequence number. |
| `envelope_count` | integer | Number of envelopes included in the batch. |
| `envelope_keys` | list of strings | Ordered `ExecutionEnvelope.envelope_key` values carried by the batch. |
| `arrival_index` | integer | Controller-side arrival order across all sources. |
| `complete` | boolean | Whether the producing source has declared delivery complete. |
| `interruption_reason` | string or null | Failure reason when a source cannot finish delivery cleanly. |

**Validation rules**

- `batch_sequence` must increase monotonically for a given `source_id`.
- `envelope_count` must match the number of transmitted envelopes.
- `envelope_keys` must preserve the same order as the enclosed envelopes.
- `complete=true` must be accompanied by a final manifest for the source.

### ReportingAuthority

Represents the one authority that may render formatter output.

| Field | Type | Description |
|-------|------|-------------|
| `authority_id` | string | Stable identifier for the reporting authority. |
| `role` | enum | `local-main`, `xdist-controller`, or `worker`. |
| `renders_live_output` | boolean | Whether this authority may own formatter output. |
| `receives_batches_from` | set of strings | Source identifiers that can send batches to this authority. |
| `worker_rendering_blocked` | boolean | Indicates that worker-local formatter rendering is forbidden. |

**Validation rules**

- Exactly one authority per run may have `renders_live_output=true`.
- Worker authorities must always set `renders_live_output=false` during
  distributed runs.

### CanonicalMessageStream

Represents the final run-wide message artifact used for validation and replay.

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Absolute path to the canonical NDJSON artifact. |
| `source_ids` | set of strings | Execution sources represented in the final stream. |
| `envelope_count` | integer | Total envelopes consolidated into the artifact. |
| `deduplication_status` | enum | `clean`, `duplicate-detected`, or `identity-missing`. |
| `validation_status` | enum | `valid`, `invalid`, or `warning`. |
| `consistency_status` | enum | `consistent`, `incomplete`, or `duplicate-detected`. |

**Validation rules**

- The stream must include all completed sources that participated in the run.
- Every accepted envelope must retain a stable deduplication identity in the
  final stream.
- Final consistency must not report missing or duplicate events.

### ReporterCoordinationRoot

Represents the narrow coordination object that owns public reporting runtime
entrypoints.

| Field | Type | Description |
|-------|------|-------------|
| `root_key` | string | Stable identifier for the runtime root. |
| `module_path` | string | Python module that defines the coordination root. |
| `public_lifecycle_contract` | list of strings | Supported public lifecycle methods exposed to the entrypoint and replay boundaries. |
| `owned_state_keys` | list of strings | `RuntimeStateContainer.container_key` values directly owned by the root. |
| `assembly_delegate_keys` | list of strings | Collaborators responsible for request resolution, service assembly, xdist role decisions, and runtime preparation. |
| `forbidden_responsibilities` | list of strings | Responsibilities intentionally excluded from the root to keep the boundary narrow. |

**Validation rules**

- `public_lifecycle_contract` must be explicit and non-empty.
- `assembly_delegate_keys` must be non-empty for this feature.
- `forbidden_responsibilities` must include formatter request resolution,
  service-graph assembly, xdist role selection, and live-output or Node-runtime
  preparation.

### ReporterPluginModule

Represents one plugin module participating in live reporting orchestration or
formatter-specific rendering.

| Field | Type | Description |
|-------|------|-------------|
| `plugin_key` | string | Stable identifier for the module role. |
| `module_path` | string | Python module path implementing the plugin responsibility. |
| `role` | enum | `entrypoint`, `message-stream`, `session`, `formatter-renderer`, or `standalone-renderer`. |
| `formatter_name` | string or null | Supported formatter for reporter modules; null for orchestration modules. |
| `registration_mode` | enum | `pytest11-entrypoint`, `pytest-plugin-manager`, `pluggy-hook-registration`, or `application-service`. |
| `hook_bindings` | list of strings | Hook names or lifecycle callbacks implemented by the plugin module. |
| `state_owner_key` | string | `RuntimeStateContainer.container_key` that owns mutable runtime state for the module. |
| `collaborator_keys` | list of strings | Direct collaborators that the module may call explicitly. |
| `template_assets` | list of strings | Template/resource assets rendered by the module, if any. |
| `owns_formatter_behavior` | boolean | Whether the module owns formatter-specific request or runtime behavior for its formatter. |

**Validation rules**

- Exactly one module per run may own the `message-stream` role.
- `formatter-renderer` modules must map one-to-one with supported formatter
  names.
- Every plugin module must declare a non-empty `registration_mode` and at
  least one `hook_bindings` entry unless `role=standalone-renderer`.
- `collaborator_keys` must list only explicit direct collaborators; sibling
  service lookup through reporter-backed service-locator accessors is forbidden.
- `formatter-renderer` modules must set `owns_formatter_behavior=true`.

### RuntimeStateContainer

Represents the runtime object that owns mutable live-reporting state.

| Field | Type | Description |
|-------|------|-------------|
| `container_key` | string | Stable identifier for the state owner. |
| `owner_scope` | enum | `plugin-instance`, `pytest-config`, `pytest-request`, `run-context`, or `session-context`. |
| `storage_mechanism` | enum | `instance-attribute`, `config-stash`, `request-attribute`, or `context-object`. |
| `module_path` | string | Module that defines the owning runtime object. |
| `mutable_global_forbidden` | boolean | Always true for this feature to document the no-global-state invariant. |

**Validation rules**

- `owner_scope` must correspond to a pytest lifecycle boundary or a plugin
  instance with deterministic startup and shutdown.
- `storage_mechanism` must not rely on mutable module-level globals.
- `mutable_global_forbidden` must always remain true for live-reporting state.

### StandaloneFormatterRenderingService

Represents the first-class application boundary used to replay canonical NDJSON
into formatter outputs outside a live pytest session.

| Field | Type | Description |
|-------|------|-------------|
| `service_key` | string | Stable identifier for the standalone rendering service. |
| `module_path` | string | Python module path that exposes the standalone rendering API. |
| `input_stream_path` | string | Absolute path to the canonical NDJSON input artifact. |
| `formatter_requests` | list of `FormatterRequest` | Requested formatter outputs for replay. |
| `discovery_policy_key` | string | `FormatterDiscoveryPolicy.policy_key` governing formatter resolution in standalone mode. |
| `uses_synthetic_pytest_config` | boolean | Must remain false for supported standalone flows. |
| `uses_ad_hoc_pluginmanager` | boolean | Must remain false for supported standalone flows. |

**Validation rules**

- `uses_synthetic_pytest_config` must remain false.
- `uses_ad_hoc_pluginmanager` must remain false.
- The service must reuse canonical formatter request and runtime-asset models
  rather than defining a separate replay-specific request type.

### FormatterDiscoveryPolicy

Represents the single supported formatter discovery rule for one execution
mode.

| Field | Type | Description |
|-------|------|-------------|
| `policy_key` | string | Stable identifier for the discovery policy. |
| `execution_mode` | enum | `pytest-runtime` or `standalone-replay`. |
| `canonical_source` | enum | `pytest11-and-hooks` or `explicit-formatter-catalog`. |
| `fallback_sources` | list of strings | Additional discovery mechanisms; must be empty for supported execution modes. |
| `inventory_scope` | string | Human-readable description of the formatter set covered by this policy. |

**Validation rules**

- Each `execution_mode` must map to exactly one `canonical_source`.
- `fallback_sources` must remain empty for supported execution modes in this
  feature.
- The same formatter inventory must not be resolved by both canonical and
  package-scan fallback paths in one mode.

### RenderedScriptAsset

Represents a runtime or test-support script rendered from a checked-in template
asset.

| Field | Type | Description |
|-------|------|-------------|
| `asset_key` | string | Stable identifier for the rendered asset. |
| `template_path` | string | Repository path to the checked-in template/resource file. |
| `render_target_path` | string | Temporary runtime path for the rendered script. |
| `owner_plugin_key` | string | `ReporterPluginModule.plugin_key` that owns rendering the asset. |
| `rendered_line_count` | integer | Effective line count of the rendered script. |
| `runtime_variables` | set of strings | Placeholder names injected during rendering. |

**Validation rules**

- Scripts with `rendered_line_count > 20` must originate from a
  `template_path`, not an inline string literal.
- `owner_plugin_key` must resolve to an existing `ReporterPluginModule`.
- Rendered script cleanup must not remove the checked-in template/resource
  asset.

## Relationships

- One `LiveFormatterSession` owns many `FormatterRequest` entries.
- Many `ExecutionEnvelope` records feed one `MessageDeliveryBatch`.
- One `ReportingAuthority` owns at most one active `LiveFormatterSession`.
- Many `MessageDeliveryBatch` records feed one `LiveFormatterSession`.
- One `CanonicalMessageStream` is produced from all accepted batches and local
  `ExecutionEnvelope` records for the run.
- One `ReporterCoordinationRoot` delegates assembly and mode-selection work to
  many `ReporterPluginModule` collaborators.
- Many `ReporterPluginModule` records with role `formatter-renderer` consume
  the same `LiveFormatterSession` through formatter-specific modules.
- One `ReporterPluginModule` may render many `RenderedScriptAsset` instances.
- One `RuntimeStateContainer` may own mutable state for many
  `ReporterPluginModule` records, but every module must resolve to exactly one
  state owner.
- One `StandaloneFormatterRenderingService` reuses the same `FormatterRequest`
  model and the same `CanonicalMessageStream` artifact used by live reporting.
- One `FormatterDiscoveryPolicy` governs either pytest runtime discovery or
  standalone replay discovery, but not both simultaneously.
