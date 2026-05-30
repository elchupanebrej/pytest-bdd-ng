# Data Model: Cucumber Formatter Support

## Entity: FormatterDefinition

Purpose: Static description of one supported formatter flag and how it maps to
the Node.js formatter ecosystem.

Fields:
- `option_attr: str` (required, unique pytest config destination)
- `cli_flag: str` (required, unique public flag such as `--cucumber-json`)
- `formatter_id: str` (required, stable formatter identifier such as `json`)
- `package_name: str` (required, npm package to resolve)
- `output_mode: stdout | path | optional_path` (required)
- `terminal_output: bool` (required)

Validation rules:
- `cli_flag` and `option_attr` are unique across definitions.
- `terminal_output=true` only when `output_mode` can target stdout.
- `pretty` maps to `@cucumber/pretty-formatter`; all other supported formatters
  in scope map to `@cucumber/cucumber`.

## Entity: FormatterRequest

Purpose: One formatter request derived from pytest CLI options for the active run.

Fields:
- `request_id: str` (required)
- `definition: FormatterDefinition` (required)
- `requested_value: bool | str` (required)
- `target_kind: terminal | file` (required)
- `output_path: str | None`
- `enabled: bool` (required)

Relationships:
- References one `FormatterDefinition`.
- Belongs to one `FormatterExecutionPlan`.

Validation rules:
- `enabled=true` is required for inclusion in the execution plan.
- `output_mode=path` requires a non-empty `output_path`.
- `output_mode=optional_path` uses terminal output when the requested value is
  stdout sentinel mode and file output otherwise.
- At most one enabled request may have `target_kind=terminal`.

## Entity: FormatterExecutionPlan

Purpose: Validated render plan produced from the collected formatter requests
and the canonical NDJSON source for one pytest run.

Fields:
- `messages_ndjson_path: str` (required)
- `requests: list[FormatterRequest]` (required)
- `terminal_request: FormatterRequest | None`
- `file_requests: list[FormatterRequest]`
- `required_packages: list[str]`
- `validation_state: collecting | ready | terminal_conflict | missing_output_directory | invalid`
- `validation_errors: list[FormatterValidationError]`
- `render_phase: sessionfinish_post_consolidation` (required)

Relationships:
- Owns many `FormatterRequest` records.
- Owns one `NpmProvisioningState`.
- Produces one `NodeRenderInvocation` when `validation_state=ready`.

Validation rules:
- `validation_state=ready` requires a canonical NDJSON path and zero validation
  errors.
- `terminal_conflict` is used when more than one terminal formatter request is
  active.
- `missing_output_directory` is used when any file request targets a parent
  directory that does not already exist.
- same normalized output path may appear in at most one file request.

State transitions:
- `collecting -> ready`
- `collecting -> terminal_conflict`
- `collecting -> missing_output_directory`
- `ready -> invalid` only if dependency resolution fails before rendering

## Entity: FormatterValidationError

Purpose: Structured validation failure captured before renderer invocation.

Fields:
- `code: MULTIPLE_TERMINAL_FORMATTERS | OUTPUT_DIRECTORY_NOT_FOUND | FILE_OUTPUT_PATH_CONFLICT | FORMATTER_PACKAGE_INSTALL_FAILED | NODE_OR_NPM_NOT_AVAILABLE`
- `message: str` (required)
- `related_flags: list[str]`
- `related_path: str | None`

Relationships:
- Belongs to one `FormatterExecutionPlan`.

Validation rules:
- `MULTIPLE_TERMINAL_FORMATTERS` is emitted when more than one terminal request
  is active.
- `OUTPUT_DIRECTORY_NOT_FOUND` is emitted when a file target parent directory
  does not already exist.
- `FILE_OUTPUT_PATH_CONFLICT` is emitted when multiple file requests resolve to
  the same normalized destination path.

## Entity: NpmProvisioningState

Purpose: Tracks how required Node.js formatter packages are resolved for a run.

Fields:
- `required_packages: list[str]` (required)
- `resolved_packages: list[str]`
- `install_scope: global` (required when install is attempted)
- `install_attempted: bool` (required)
- `manual_install_hint: str | None`
- `status: resolved | installed | failed`

Relationships:
- Belongs to one `FormatterExecutionPlan`.

Validation rules:
- `status=resolved` means every required package was already available without
  provisioning.
- `status=installed` means at least one package required `npm install -g`.
- `status=failed` requires a non-empty `manual_install_hint`.

## Entity: NodeRenderInvocation

Purpose: Concrete Python-to-Node handoff used to render formatter outputs from
the canonical NDJSON stream.

Fields:
- `node_executable: str` (required)
- `working_directory: str` (required)
- `messages_ndjson_path: str` (required)
- `requested_outputs: list[dict[str, str]]` (required)
- `package_roots: list[str]`
- `stdout_passthrough: bool` (required)
- `stderr_passthrough: bool` (required)
- `exit_code: int | None`
- `status: pending | succeeded | failed`

Relationships:
- Belongs to one `FormatterExecutionPlan`.

Validation rules:
- `requested_outputs` preserves the validated formatter selection from the
  execution plan.
- `stdout_passthrough=true` is required when a terminal formatter is active.
- `status=failed` requires a non-zero `exit_code` or an explicit launch error.

## Modeling Note

- The standalone NDJSON post-processing script can reuse the same
  `FormatterExecutionPlan`, `NpmProvisioningState`, and `NodeRenderInvocation`
  concepts, but it is not required to introduce additional formatter semantics
  beyond the pytest-facing contract defined in this feature spec.
