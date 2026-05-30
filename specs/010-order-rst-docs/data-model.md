<!-- markdownlint-disable MD013 -->

# Data Model: Template-Driven Feature Documentation Ordering

## Entity: DocumentationSourceTopic

- Description: A source document or directory-backed topic that contributes one reader-facing documentation entry within a navigation scope.
- Fields:
  - `topic_id` (string, required, unique)
  - `source_path` (string, required, unique)
  - `scope_path` (string, required)
  - `source_kind` (enum: `gherkin`, `markdown_gherkin`, `struct_bdd`, `section_directory`, required)
  - `ordering_prefix` (integer, required)
  - `display_label` (string, required)
  - `generated_page_path` (string, required)
  - `code_type` (enum: `gherkin`, `yaml`, `rst`, required)
- Validation rules:
  - `ordering_prefix` MUST be present for every sibling item in an ordered navigation scope.
  - `display_label` MUST omit the numeric prefix even when `source_path` contains it.
  - `generated_page_path` MUST preserve the numeric prefix derived from the source path.

## Entity: NavigationScope

- Description: A single toctree scope that groups sibling topics or subsections at one depth in the generated feature documentation.
- Fields:
  - `scope_id` (string, required, unique)
  - `scope_path` (string, required, unique)
  - `depth` (integer, required)
  - `heading_label` (string, required)
  - `entries` (array[`DocumentationSourceTopic.topic_id`], required)
  - `ordered` (boolean, required)
- Validation rules:
  - `entries` MUST be sorted by `ordering_prefix` in ascending order.
  - Sibling `ordering_prefix` values MUST be unique within one `scope_id`.
  - `heading_label` MUST omit any numeric prefix carried by the source directory name.

## Entity: TemplateRenderPayload

- Description: The prepared data passed from the coordinator script into templates for index and page rendering.
- Fields:
  - `payload_id` (string, required, unique)
  - `template_id` (string, required)
  - `intro_block` (string, required)
  - `generated_sections` (array[`NavigationScope.scope_id`], required)
  - `suffix_block` (string, required)
  - `render_variables` (map[string, any], required)
- Validation rules:
  - Rendering MUST not require templates to rediscover source files or mutate ordering decisions.
  - `render_variables` MUST contain every heading, underline, label, and path needed to render deterministic output.

## Entity: GeneratedPage

- Description: One generated `.rst` page produced for a feature-backed source topic.
- Fields:
  - `page_id` (string, required, unique)
  - `topic_id` (string, required, references `DocumentationSourceTopic.topic_id`)
  - `output_path` (string, required, unique)
  - `reader_title` (string, required)
  - `heading_level` (integer, required)
  - `content_mode` (enum: `include`, `converted_markdown`, required)
- Validation rules:
  - `output_path` MUST preserve source-derived numeric prefixes.
  - `reader_title` MUST remove numeric prefixes before display.
  - `heading_level` MUST be consistent with directory depth or markdown conversion depth.

## Entity: GeneratedIndexDocument

- Description: The generated `docs/features/features.rst` document composed from preserved manual content and auto-generated navigation sections.
- Fields:
  - `document_path` (string, required, unique)
  - `intro_block` (string, required)
  - `auto_generated_start_marker` (string, required)
  - `auto_generated_end_marker` (string, required)
  - `sections` (array[`NavigationScope.scope_id`], required)
  - `suffix_block` (string, required)
- Validation rules:
  - Content outside the generated markers MUST be preserved during regeneration.
  - Generated sections MUST render in the same order for repeated runs on unchanged sources.

## Entity: OrderingValidationError

- Description: A deterministic validation error raised when numeric ordering requirements are not satisfied.
- Fields:
  - `error_code` (enum: `missing_ordering_prefix`, `duplicate_ordering_prefix`, required)
  - `scope_path` (string, required)
  - `source_path` (string, required)
  - `message` (string, required)
- Validation rules:
  - `error_code` MUST identify whether the failure is caused by a missing or duplicate prefix.
  - `scope_path` and `source_path` MUST be sufficient to locate and fix the offending item.

## Entity: MarkdownHeadingNormalizationRequest

- Description: A conversion request for markdown-backed feature pages whose heading levels need normalization before rendering.
- Fields:
  - `request_id` (string, required, unique)
  - `source_path` (string, required)
  - `heading_shift` (integer, required)
  - `preferred_converter` (enum: `pandoc`, `other_existing_step`, required)
- Validation rules:
  - `heading_shift` MUST match the generated page depth.
  - `preferred_converter` SHOULD be `pandoc` when markdown conversion can rely on the existing `pypandoc` path.

## Relationships

- `DocumentationSourceTopic.scope_path` groups topics into one `NavigationScope`.
- `NavigationScope.entries` references ordered sibling `DocumentationSourceTopic` records.
- `TemplateRenderPayload.generated_sections` references the scopes rendered into `GeneratedIndexDocument`.
- `GeneratedPage.topic_id` references `DocumentationSourceTopic.topic_id`.
- `OrderingValidationError` is emitted for a specific `DocumentationSourceTopic` within one `NavigationScope`.
- `MarkdownHeadingNormalizationRequest.source_path` references a markdown-backed `DocumentationSourceTopic`.

## State Transitions

1. Discover source topics and directories under the feature tree.
2. Derive `NavigationScope` membership from directory structure.
3. Parse and validate numeric prefixes for every sibling item in each ordered scope.
4. Derive reader-facing labels by stripping numeric prefixes while preserving generated paths.
5. Prepare template payloads for index rendering and page rendering.
6. Normalize markdown heading levels through the preferred conversion step when needed.
7. Render pages and the generated index document.
8. Preserve manual intro/suffix content outside generated markers.
9. Emit deterministic `OrderingValidationError` records instead of producing ambiguous output.
