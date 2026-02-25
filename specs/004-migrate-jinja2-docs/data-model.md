<!-- markdownlint-disable MD013 -->

# Data Model: Jinja2 Documentation Generation Migration

## Entity: TemplateAsset

- Description: A template file consumed by generation flows.
- Fields:
  - `template_id` (string, required, unique)
  - `relative_path` (string, required)
  - `engine` (enum: `jinja2`, required)
  - `packaged` (boolean, required)
- Validation rules:
  - `relative_path` MUST resolve under `src/pytest_bdd/template/`.
  - `engine` MUST be `jinja2` for all migrated assets.

## Entity: TemplateRenderContext

- Description: Render-time payload used by a template.
- Fields:
  - `context_id` (string, required)
  - `template_id` (string, required, references `TemplateAsset.template_id`)
  - `variables` (map[string, any], required)
  - `render_mode` (enum: `code_generation`, `docs_generation`, required)
- Validation rules:
  - Required variables for each template MUST be present before rendering.
  - Rendering MUST be deterministic for identical input context.

## Entity: GeneratedDocumentationBlock

- Description: Regenerable section within a documentation index file.
- Fields:
  - `start_marker` (string, required)
  - `end_marker` (string, required)
  - `entries` (array[string], required)
  - `content_hash` (string, required)
- Validation rules:
  - `start_marker` and `end_marker` MUST both exist when replacement mode is used.
  - Replacement MUST modify only content between markers.

## Entity: ManualDocumentationBlock

- Description: Human-maintained documentation content outside generated marker boundaries.
- Fields:
  - `location` (enum: `prefix`, `suffix`, `standalone`, required)
  - `content_hash` (string, required)
  - `preserved` (boolean, required)
- Validation rules:
  - Regeneration MUST preserve manual prefix/suffix content unless explicitly edited by a maintainer.

## Entity: FeaturesIndexScopePolicy

- Description: Scope constraints for `docs/features/features.rst` content.
- Fields:
  - `document_path` (string, required)
  - `allow_generated_navigation` (boolean, required)
  - `allow_user_facing_context` (boolean, required)
  - `allow_internal_implementation_notes` (boolean, required)
  - `allow_conversion_history_notes` (boolean, required)
- Validation rules:
  - `document_path` MUST equal `docs/features/features.rst`.
  - `allow_generated_navigation` MUST be `true`.
  - `allow_internal_implementation_notes` MUST be `false`.
  - `allow_conversion_history_notes` MUST be `false`.

## Entity: GenerationParityCase

- Description: A test scenario validating migration output parity.
- Fields:
  - `case_id` (string, required, unique)
  - `input_fixture` (string, required)
  - `expected_output_snapshot` (string, required)
  - `parity_mode` (enum: `semantic`, required)
  - `covers_special_content` (boolean, required)
- Validation rules:
  - Parity checks MUST pass semantic equivalence against baseline behavior.
  - Special-content coverage MUST include quote-heavy and unicode cases.

## Entity: DocumentationSyncCheck

- Description: Validation record proving generated docs are up to date.
- Fields:
  - `check_id` (string, required)
  - `trigger` (enum: `pre_commit`, `manual`, `ci`, required)
  - `generated_docs_changed` (boolean, required)
  - `status` (enum: `pass`, `fail`, required)
- Validation rules:
  - `status` MUST be `fail` when `generated_docs_changed` is `true` in `pre_commit` mode.

## Entity: PackagingTemplateManifest

- Description: Declared template assets included in built distributions.
- Fields:
  - `manifest_id` (string, required)
  - `included_assets` (array[string], required)
  - `removed_assets` (array[string], required)
- Validation rules:
  - All runtime-required Jinja2 templates MUST appear in `included_assets`.
  - Legacy Mako templates in migration scope MUST appear in `removed_assets`.

## Relationships

- `TemplateRenderContext.template_id` references `TemplateAsset.template_id`.
- `GeneratedDocumentationBlock` and `ManualDocumentationBlock` are complementary regions in one documentation file.
- `FeaturesIndexScopePolicy` constrains allowed content for `GeneratedDocumentationBlock` output at `docs/features/features.rst`.
- `GenerationParityCase` validates outputs produced from one or more `TemplateAsset` render operations.
- `DocumentationSyncCheck` validates synchronization of files affected by docs-generation runs.
- `PackagingTemplateManifest` tracks shipping state for migrated `TemplateAsset` instances.

## State Transitions

1. Resolve `TemplateAsset` from package resources.
2. Render using `TemplateRenderContext`.
3. Write output artifact targets.
4. Replace only `GeneratedDocumentationBlock` while preserving `ManualDocumentationBlock`.
5. Validate `FeaturesIndexScopePolicy` for `docs/features/features.rst`.
6. Validate semantic parity using `GenerationParityCase`.
7. Run `DocumentationSyncCheck` and block commits when docs are stale.
