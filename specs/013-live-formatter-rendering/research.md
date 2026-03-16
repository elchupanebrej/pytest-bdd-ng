# Research: Live Formatter Rendering

## Research Inputs

- Repository reporting entrypoint:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`
- Repository reporter coordination root:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- Repository standalone replay entrypoint:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/render_cucumber_formatters.py`
- Repository standalone replay service:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py`
- Repository xdist remote bootstrap:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd_worker_bootstrap/xdist_remote.py`
- Repository formatter support and discovery:
  `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/`
- Primary dependency guidance reviewed through current `pytest-xdist`
  documentation for worker/controller execution context and environment
  boundaries

## Decision 1: Keep one long-lived formatter session per pytest run

- **Decision**: Start one long-lived formatter session for each pytest run and
  keep it open for the duration of the run so active formatters consume
  envelopes as they are emitted.
- **Rationale**: This directly satisfies the feature requirement that
  formatters consume a live incremental stream. It also preserves formatter
  state across the run, allowing each formatter to decide when to print or
  flush output without waiting for final NDJSON replay.
- **Alternatives considered**:
  - Post-run rendering from the final NDJSON file: rejected because it violates
    the live-consumption requirement.
  - Spawning a fresh formatter process for every batch or event: rejected
    because it destroys stateful formatter behavior and adds avoidable process
    overhead.

## Decision 2: Render only on the controller/main authority during distributed runs

- **Decision**: During `pytest-xdist` runs, workers publish incremental message
  batches to the controller/main authority, and only that authority owns active
  formatter processes and user-visible live output.
- **Rationale**: Centralized rendering prevents duplicate or competing output,
  aligns with `pytest-xdist` controller/worker roles, and matches the existing
  repository transport pattern that already distinguishes worker publication
  from controller consolidation.
- **Alternatives considered**:
  - Worker-local formatter rendering: rejected because users would see
    duplicated or fragmented output from multiple authorities.
  - Shared-filesystem polling by the controller: rejected because the existing
    transport already carries batch data and network-based workers may not share
    a filesystem.

## Decision 3: All active formatter requests must consume the same live stream

- **Decision**: Any requested cucumber formatter should be attached to the same
  live envelope stream during the run. File-oriented formatters may finalize
  their visible artifacts when the stream closes, but they must not depend on a
  separate post-run-only replay path.
- **Rationale**: The feature description states that formatters must consume the
  stream during the run and may report in their own way. This allows terminal
  formatters to emit immediately while file-oriented or summary-oriented
  formatters can buffer internally and finalize at the end without diverging to
  a different execution model.
- **Alternatives considered**:
  - Keep terminal formatters live while file formatters remain deferred:
    rejected because it splits the runtime contract across two models.
  - Convert every formatter into immediate terminal output only: rejected
    because it would break file-producing formatters.

## Decision 4: Preserve per-source order and use controller arrival order across sources

- **Decision**: Preserve message order within each execution source and allow
  the controller to interleave sources in the order batches arrive. Keep the
  canonical NDJSON stream as the final consistency artifact rather than
  blocking live output on global reordering.
- **Rationale**: Per-source order is the minimum deterministic guarantee users
  need for meaningful progress output. Enforcing a total global order before
  rendering would delay live output and recreate the post-run behavior this
  feature is replacing.
- **Alternatives considered**:
  - Global timestamp-based reordering before rendering: rejected because it
    delays output and introduces fragile clock or ordering assumptions.
  - Unordered cross-source delivery: rejected because it would allow within-
    source regressions that make progress output misleading.

## Decision 5: Treat live delivery interruption as a surfaced runtime/reporting error

- **Decision**: If live delivery cannot be established or is interrupted in a
  way that makes the stream unreliable, surface an actionable error instead of
  silently downgrading to post-run rendering.
- **Rationale**: Silent fallback would hide a broken live-reporting contract and
  make the feature appear to work while violating the user-visible requirement.
  Users need a clear signal that the run no longer satisfies the live-rendering
  guarantee.
- **Alternatives considered**:
  - Silent fallback to NDJSON replay after session finish: rejected because it
    conceals behavior drift.
  - Best-effort warning with partial live output and success status: rejected
    because it leaves output correctness ambiguous.

## Decision 6: Preserve existing entrypoints as compatibility surfaces

- **Decision**: Keep the existing formatter CLI flags and standalone NDJSON
  replay entrypoint as supported compatibility surfaces, but align them to the
  same formatter request normalization and payload model used by live sessions.
- **Rationale**: Users already rely on these entrypoints. Reusing one request
  model minimizes contract drift while allowing the live-session feature to
  improve runtime behavior without introducing parallel public interfaces.
- **Alternatives considered**:
  - Introduce a new live-only CLI separate from existing formatter flags:
    rejected because it needlessly fragments the user interface.
  - Drop standalone replay support: rejected because repository compatibility
    tests and user workflows already depend on replaying an existing NDJSON
    stream.

## Decision 7: Automatic capture switching belongs to the product path, not the test harness

- **Decision**: Terminal formatter runs must exercise the real pytest-bdd-ng
  entrypoint and rely on product-owned automatic capture switching instead of
  helper-injected `-s` or `--capture=no` flags.
- **Rationale**: Helper-forced capture settings can make acceptance tests pass
  while masking regressions in the actual CLI experience. Keeping capture
  switching inside the product path ensures both local and remote validation
  reflect what users really run.
- **Alternatives considered**:
  - Keep acceptance helpers injecting `--capture=no`: rejected because it
    validates a workaround instead of the shipping behavior.
  - Leave capture behavior implicit and undocumented: rejected because live
    terminal rendering depends on an explicit, testable runtime contract.

## Decision 8: Split live reporting into orchestration modules and per-formatter plugins

- **Decision**: Break the `gherkin_message_reporter` runtime into a thin
  registration facade, dedicated orchestration modules, and one formatter
  plugin module per supported formatter.
- **Rationale**: The clarified spec requires separation between message
  handling and reporter-specific rendering. Isolating orchestration from
  formatter modules reduces change coupling and prevents one monolithic module
  from absorbing unrelated responsibilities.
- **Alternatives considered**:
  - Keep one large plugin file with helper sections: rejected because it still
    centralizes formatter-specific logic in one module.
  - Split only terminal versus file formatters: rejected because the spec
    requires separate formatter plugin modules per supported formatter.

## Decision 9: Render long generated scripts from repository templates/resources

- **Decision**: Any generated helper script longer than 20 lines must be stored
  as a checked-in resource/template asset and rendered into a temporary file at
  runtime.
- **Rationale**: Long inline script literals are hard to review, reason about,
  and test. Template-backed assets keep script behavior explicit and align both
  product runtime and test-support code with the clarified spec.
- **Alternatives considered**:
  - Keep long generated scripts inline and rely on comments: rejected because
    comments do not reduce the review and maintenance cost of multi-dozen-line
    embedded programs.
  - Move every generated script to standalone checked-in executables: rejected
    because some runtime values still need rendering into temporary artifacts.

## Decision 10: Register split modules as real pytest or pluggy plugins

- **Decision**: Reporter-specific modules and orchestration components must
  participate as real pytest or pluggy plugins through hook registration and
  lifecycle callbacks rather than existing only as helper classes invoked by a
  custom registry.
- **Rationale**: Hook-based registration keeps runtime behavior visible to
  pytest lifecycle management and avoids a fake "plugin split" where one facade
  still manually orchestrates all behavior internally.
- **Alternatives considered**:
  - Keep a custom in-process registry that instantiates helper modules:
    rejected because it does not satisfy the requirement for real pytest or
    pluggy plugin participation.
  - Register only one orchestration plugin and keep formatter modules as plain
    helpers: rejected because formatter-specific behavior would still live
    outside the hook system.

## Decision 11: Scope live-reporting state to plugin and pytest-owned runtime objects

- **Decision**: Mutable live-reporting state must live on plugin instances or
  pytest-owned runtime containers such as `config.stash`, request objects, or
  explicit run/session state objects.
- **Rationale**: Module-level mutable state makes nested runs, xdist worker
  identity, and lifecycle isolation brittle. Plugin-owned or pytest-owned state
  aligns the feature with pytest lifecycle boundaries and makes startup and
  shutdown behavior deterministic and testable.
- **Alternatives considered**:
  - Keep mutable module-level globals with reset helpers: rejected because it
    still allows hidden cross-run leakage and fragile cleanup paths.
  - Use uppercase pseudo-constants for mutable coordination state: rejected
    because it obscures mutability and weakens code review signals.

## Decision 12: Reduce the reporter root to a narrow coordination boundary

- **Decision**: `GherkinMessageReporter` must become a narrow coordination root
  that owns public runtime lifecycle and shared state references only. Service
  graph assembly, formatter request resolution, xdist role selection, and
  live-output or Node-runtime preparation move into dedicated collaborators.
- **Rationale**: The current aggregate root already stopped being a mixin
  monolith, but it still knows too much about assembly and mode selection.
  Shrinking it lowers change coupling and prevents every new execution mode
  from re-expanding the root object.
- **Alternatives considered**:
  - Keep the large root and split only more helper modules: rejected because
    the root would still remain the architectural choke point.
  - Move everything into free functions: rejected because the runtime still
    needs one explicit coordination owner and lifecycle surface.

## Decision 13: Formalize one entrypoint-to-runtime lifecycle contract

- **Decision**: The pytest entrypoint and the reporting runtime must interact
  through one explicit public lifecycle contract for configure, unconfigure,
  and public render calls. Duck typing against private attributes or private
  methods is forbidden.
- **Rationale**: Compatibility fallback logic in the entrypoint makes the
  runtime boundary ambiguous and keeps internal structure observable from
  outside. One explicit contract narrows the public surface and makes both
  contract tests and refactors cleaner.
- **Alternatives considered**:
  - Keep duck typing for flexibility: rejected because it encodes compatibility
    debt and rewards partially structured reporter objects.
  - Move entrypoint logic into the root object: rejected because the entrypoint
    still needs to remain a thin pytest-facing surface.

## Decision 14: Replace reporter-backed service access with explicit narrow collaborators

- **Decision**: Runtime services may depend only on direct collaborators that
  are injected explicitly. Reporter-backed service-locator accessors are not an
  acceptable long-term dependency mechanism.
- **Rationale**: Typed service accessors are better than magic `__getattr__`,
  but they still hide the real service dependency graph inside one owning
  object. Explicit collaborator injection makes review, testing, and local
  reasoning much simpler.
- **Alternatives considered**:
  - Keep typed reporter-backed service properties: rejected because they still
    let any service reach any sibling service.
  - Collapse all service logic back into one orchestration module: rejected
    because it recreates the monolith the feature is trying to remove.

## Decision 15: Standalone replay must use a first-class application service

- **Decision**: Standalone NDJSON replay must be implemented through a first-
  class rendering service that accepts normalized formatter requests and
  canonical message inputs without requiring synthetic pytest `Config` objects
  or ad hoc pluginmanager construction.
- **Rationale**: Synthetic pytest runtime objects make the replay path depend on
  pytest internals instead of on a stable replay boundary. A first-class
  service keeps replay usable outside a live pytest session and preserves a
  cleaner public contract.
- **Alternatives considered**:
  - Keep replay built on a fake pytest runtime: rejected because it couples
    standalone tooling to internals that are not its domain model.
  - Create a completely separate replay stack: rejected because both live and
    replay flows must still share canonical formatter request and asset logic.

## Decision 16: Formatter plugins must own formatter-specific behavior

- **Decision**: Each formatter plugin must own its formatter-specific
  request-building and runtime-asset behavior through its module or dedicated
  formatter-owned collaborators. Shared support code may provide common
  primitives only.
- **Rationale**: Independent loading alone is not enough if most behavior still
  lives in one shared base. Real ownership keeps formatter evolution local and
  prevents the support layer from becoming a second monolith.
- **Alternatives considered**:
  - Keep formatter modules as declarative wrappers over one rich base class:
    rejected because formatter-specific behavior would still be centralized.
  - Duplicate all shared behavior per formatter: rejected because small shared
    primitives are still useful and reduce pure boilerplate.

## Decision 17: Use one canonical discovery source per execution mode

- **Decision**: Pytest runtime discovery remains hook-based and pytest11-driven.
  Standalone replay discovery uses one explicit catalog path built from the
  supported formatter inventory. Package-scan fallback is removed from
  supported runtime paths.
- **Rationale**: Two discovery policies for the same formatter set create drift
  and make tests pass through a path that production does not use. One source
  of truth per mode keeps inventory deterministic.
- **Alternatives considered**:
  - Keep package-scan fallback for convenience: rejected because it silently
    tolerates environments that bypass the supported plugin-discovery contract.
  - Hardcode formatter lists separately in runtime and replay code: rejected
    because it recreates duplication in a different form.
