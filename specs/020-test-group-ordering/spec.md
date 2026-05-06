# Feature Specification: Test Group Ordering

**Feature Branch**: `020-test-group-ordering`  
**Created**: 2026-05-05  
**Status**: Clarified  
**Input**: User description: "Нужно разбить тесты по группам, чтоб быстрые (unit) тесты выполнялись первыми. Тесты, которые используют subprocess, должны идти во второй группе. Тесты завязанные на работу с Docker - должны идти последними"

## Clarifications

### Session 2026-05-05

- Q: How is a test's group membership determined — auto-detection, explicit markers, or a hybrid approach? → A: Hybrid with priority cascade: (1) directory/folder structure sets the base group, (2) `conftest.py` markers override at the directory level, (3) individual test-file markers have final precedence.
- Q: What is the default fail-fast behaviour when a group contains failures — stop or continue? → A: A full suite run always executes all groups regardless of failures. Additionally, dedicated invocation targets exist to run each group in isolation by marker filter.
- Q: When an external resource required by a group is unavailable in the execution environment, should affected tests skip (with warning) or hard-fail? → A: Skip with a visible warning — the CI build continues and the reason is clearly reported.
- Q: What form do the per-group invocation targets take? → A: Pytest marker selectors — each group is a named marker; developers run a specific group via the marker filter without any additional tooling wrapper.
- Q: How is full-suite group ordering enforced at invocation level? → A: A third-party pytest plugin handles in-process reordering of collected items by group marker within a single `pytest` invocation. Local project code may only translate resolved group names into the plugin's ordering markers; it must not sort collected items.
- **Scope correction**: Any named groups in examples are illustrative examples of group membership, not hardcoded definitions. The feature describes a generic, configurable test-group ordering system where users define their own groups and execution order.
- Q: Where are groups, their execution order, and the default group declared? → A: In the standard pytest configuration file (`pyproject.toml` under `[tool.pytest.ini_options]`, or `pytest.ini`); no separate config file is introduced.
- Q: How is a directory mapped to a group? → A: Both mechanisms are supported: (1) explicit glob/path-prefix patterns declared in config take precedence; (2) directory naming convention (directory name matches a configured group name) acts as fallback when no pattern matches.
- Q: How is the group configuration validated, and what happens on error? → A: Configuration is validated at collection time; any misconfiguration (unknown group name, duplicate ordinal, reserved marker clash) emits a visible warning and collection continues — no abort.
- Q: How does a group signal that a required external resource is unavailable? → A: Through standard pytest fixture semantics — if a fixture used by a test raises a skip, the test is marked as skipped. No group-level prerequisite check mechanism is introduced; tests rely on their existing fixtures.
- Q: Is SC-002 ("faster feedback from first group") a distinct measurable criterion or redundant with SC-001/SC-003? → A: Redundant — strict ordering already implies it; SC-002 removed.
- Q: What generic example group names should replace project-specific examples? → A: Use five cost-tier example groups: `instant`, `fast`, `medium`, `slow`, and `external`.
- Q: Should this feature restructure the existing `tests/` tree? → A: No. Keep the current `tests/` tree and assign groups through configuration path mappings, directory naming where already applicable, and pytest markers.
- Q: Where should reusable grouping configuration and resolver code live? → A: In `src/pytest_bdd/...`; `tests/conftest.py` only adapts pytest collection to the reusable utility.
- Q: How should non-group pytest markers be handled during group resolution? → A: Only configured group names are group signals; all other pytest markers are ignored by the grouping resolver.
- Q: May local pytest hooks participate in ordering enforcement? → A: A local collection hook may translate resolved group names into third-party ordering markers, but MUST NOT sort or reorder items itself.
- Q: Where should structured group configuration live? → A: Only in pytest ini-style configuration (`[tool.pytest.ini_options]` in `pyproject.toml` or `pytest.ini`); no separate tool-specific TOML table is used.
- Q: How should group ordering behave under `pytest-xdist`? → A: xdist must preserve runtime group barriers: no later group starts until all earlier group tests finish.
- Q: How should fixture-driven external-resource skips be validated? → A: Add an acceptance scenario requiring a test fixture to call `pytest.skip()`, with later groups still running normally.
- Q: How should ambiguous directory-name convention be handled? → A: Exact directory segment matching can resolve to at most one configured group after duplicate group names are normalized; no separate ambiguity case is needed.
- Q: How should the `<= 2 seconds` overhead criterion be measured? → A: Measure collection-phase wall-clock delta for `pytest --collect-only` with grouping enabled versus disabled.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define and Configure Test Groups (Priority: P1)

A developer needs to partition the test suite into an ordered set of named groups, where each group represents a tier of tests with similar cost, speed, or environmental requirements. They define the groups and their execution order through project configuration, then assign tests to groups via the marker cascade (directory → conftest → test file). The initial project configuration uses five generic cost-tier examples (`instant`, `fast`, `medium`, `slow`, `external`), but the mechanism supports any number of groups with any project-defined names.

**Why this priority**: The ability to define and configure groups is the foundational capability; without it, none of the ordering or isolation benefits can be realised.

**Independent Test**: Can be fully tested by defining two or more named groups in configuration, assigning tests to each group, and verifying the assignments resolve correctly through the cascade.

**Acceptance Scenarios**:

1. **Given** a project with two or more named groups defined in configuration, **When** tests are annotated via directory, conftest, or file-level markers, **Then** each test resolves to exactly one group according to the cascade priority rules.
2. **Given** a test with no group marker at any level, **When** the suite is collected, **Then** the test is assigned to the configured default group.
3. **Given** conflicting group signals at different cascade levels (e.g., directory says Group A, test file says Group B), **When** the suite is collected, **Then** the most specific level (test file) wins and the test is assigned to Group B.
4. **Given** the existing test directory tree has mixed historical concerns, **When** the grouping feature is applied, **Then** files remain in their current locations and group membership is expressed through configuration and markers only.

---

### User Story 2 - Run the Full Suite in Group Order (Priority: P2)

A developer runs the full test suite and all defined groups execute in the configured sequence, from the first (highest-priority) group to the last, regardless of failures in any intermediate group. This gives the developer fast feedback from lighter groups before heavier groups consume resources, without requiring any change to how they invoke the suite.

**Why this priority**: The ordering guarantee is the core value proposition; it must work transparently in the existing invocation workflow.

**Independent Test**: Can be fully tested by defining three or more groups, placing tests in each, running the full suite, and verifying completion timestamps show strict group-level ordering.

**Acceptance Scenarios**:

1. **Given** a suite with N configured groups, **When** the full suite is executed, **Then** all tests in Group 1 complete before any test in Group 2 begins, and all tests in Group 2 complete before any test in Group 3 begins (and so on for N groups).
2. **Given** a test in an earlier group fails, **When** the full suite is executed, **Then** all subsequent groups still execute to completion — no group is skipped due to a prior group's failure.
3. **Given** all tests in a group are skipped, **When** the full suite is executed, **Then** the suite advances to the next group without error.
4. **Given** a group's tests depend on fixtures that check for an external resource, **When** those fixtures signal that the resource is unavailable by skipping, **Then** each affected test is individually marked as skipped; other groups are unaffected.
5. **Given** a test in an earlier group uses a fixture that calls `pytest.skip()` because an external resource is unavailable, **When** the full suite is executed, **Then** the skipped test is reported as a normal pytest skip and tests in later groups still run.

---

### User Story 3 - Run a Single Group in Isolation (Priority: P3)

A developer wants to run only the tests belonging to a specific group — for example, to iterate quickly on a low-cost group without waiting for slower groups, or to verify external-dependency tests in a dedicated CI step. They select the target group by its marker name; only tests assigned to that group are collected and run.

**Why this priority**: Per-group isolation targets directly enable the fast-feedback and CI-gate use cases that motivate the grouping feature.

**Independent Test**: Can be fully tested by running the suite with a single group's marker filter and verifying no tests from other groups appear in the results.

**Acceptance Scenarios**:

1. **Given** a suite with multiple groups, **When** the suite is invoked with a single group's marker filter, **Then** only tests assigned to that group are collected and executed.
2. **Given** a group filter is applied, **When** tests from other groups would normally run, **Then** they are excluded from collection entirely (not skipped — not collected).
3. **Given** an empty group is selected (all tests in that group are skipped or the group has no tests), **When** the suite is invoked with that group's marker filter, **Then** the suite exits cleanly with a "no tests ran" result rather than an error.

---

### Edge Cases

- What happens when a test belongs to more than one group via conflicting cascade signals? → The most specific level wins (test-file marker > conftest marker > config path pattern > directory naming convention); ties at the same level resolve to the latest (heaviest) configured group.
- What happens when a configured group name collides with an existing pytest marker? → The group name must not shadow built-in pytest markers; this is a configuration validation concern.
- What happens when duplicate group names are configured? → Configuration validation emits a visible warning and normalizes duplicate group names before directory naming convention is applied, so exact directory segment matching can resolve to at most one configured group.
- How does ordering interact with parallel test execution (pytest-xdist)? → Runtime group barriers are required: no test from a later group may start until every test from all earlier groups has finished. Parallelism may apply within a group but not across group boundaries.
- What happens when a group is defined in configuration but has zero tests assigned? → The group is silently skipped; no error or warning is raised.
- What happens when a test carries ordinary pytest markers that are not configured group names? → They are ignored by group resolution; only configured group names participate in assignment.
- What happens when a configured path or group declaration references an unknown group? → A visible warning is emitted at collection time; invalid configuration entries are ignored or fall back to the default group as applicable, and execution continues.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A full suite run MUST execute all configured groups in their defined order, regardless of failures in any group.
- **FR-002**: The set of groups and their execution order MUST be configurable by the project; the system MUST NOT hardcode any specific group names or count.
- **FR-003**: The directory-level group assignment MUST support two mechanisms in priority order: (1) explicit glob or path-prefix patterns declared in the pytest configuration file, mapping path patterns to group names; (2) directory naming convention, where a directory whose name matches a configured group name is automatically assigned to that group. Config-defined patterns take precedence over naming convention.
- **FR-003a**: A test's overall group is determined by a three-level priority cascade applied after directory-level assignment: (1) directory structure (via pattern or convention) provides the base, (2) a `conftest.py` marker in the same or parent directory overrides the base, (3) a marker declared in the test file itself takes final precedence.
- **FR-003b**: The feature MUST NOT require moving or renaming existing test files or directories; any existing-tree classification MUST be represented through configuration path mappings, existing directory naming matches, or pytest group markers.
- **FR-004**: Tests whose group cannot be resolved through the full cascade (no matching path pattern, no matching directory name, no conftest marker, no test-file marker) MUST be assigned to the configurable default group.
- **FR-005**: A test assigned to group N MUST NOT execute before all tests in all groups with a lower ordinal have completed.
- **FR-006**: When a test receives conflicting group signals at the same cascade level, it MUST be assigned to the latest (highest ordinal) group among the candidates.
- **FR-007**: Skipping all tests in a group MUST NOT prevent subsequent groups from executing.
- **FR-008**: The grouping mechanism MUST integrate with the existing test invocation workflow without requiring developers to change how they invoke the suite.
- **FR-009**: The grouping mechanism MUST be compatible with the project's current parallelisation strategy (xdist), preserving runtime inter-group barriers while allowing intra-group parallelism.
- **FR-010**: Each group MUST be selectable as a standalone run using its configured marker name as a pytest marker filter, allowing developers to run only that group's tests.
- **FR-011**: Tests that cannot run due to an unavailable prerequisite MUST be handled through standard pytest fixture skip semantics: if a fixture raises a skip signal, the dependent test is marked as skipped. No group-level prerequisite check mechanism is introduced by this feature.
- **FR-012**: Full-suite group ordering MUST be enforced by a third-party pytest plugin that reorders collected items by group marker within a single `pytest` invocation. Project code MAY provide a pytest collection hook that translates resolved group names into the plugin's ordering markers, but project code MUST NOT sort, reorder, or otherwise mutate item order directly.
- **FR-013**: Group names, their execution order, the default group, and path mappings MUST be declared only through pytest ini-style configuration (`pyproject.toml` `[tool.pytest.ini_options]` or `pytest.ini`); no separate tool-specific TOML table or additional configuration file type is introduced.
- **FR-014**: At collection time, the group configuration MUST be validated; any misconfiguration in group configuration (unknown group name referenced by path mappings, duplicate group entries, default group not present in `groups`, or group name clashing with a built-in pytest marker) MUST emit a clearly worded warning visible in the test output; collection and execution MUST continue.
- **FR-014a**: Group resolution MUST treat only names declared in `Group Configuration.groups` as group markers. All other pytest markers MUST be ignored by the grouping resolver and MUST NOT require hardcoded ignore lists.
- **FR-015**: Reusable group configuration parsing, validation, and resolution logic MUST live under `src/pytest_bdd/...` and be covered by the repository's normal static typing and formatting gates; `tests/conftest.py` MAY contain only pytest-specific adapter code.

### Key Entities

- **Test Group**: A user-defined, named, ordered tier that determines when its assigned tests execute relative to other groups. Groups are defined in project configuration with an explicit ordinal or priority.
- **Group Configuration**: The project-level definition of all groups, their names, their execution order, path mappings, and the name of the default group. Declared only in pytest ini-style configuration (`pyproject.toml` `[tool.pytest.ini_options]` or `pytest.ini`).
- **Group Marker**: A label applied at the directory, conftest, or test-file level that assigns tests to a named group. Marker names correspond to group names defined in Group Configuration.
- **Group Marker Priority**: The resolution order for conflicting group signals — directory structure (lowest) → conftest marker → test-file marker (highest).
- **Group Ordering Policy**: The rule set governing execution sequence and precedence resolution when a test matches multiple groups.
- **Group Ordering Utility**: The reusable source module that parses group configuration, validates it, resolves item assignments, and exposes pytest-adapter functions without depending on individual test modules.

## Agentic Validation Constraints

- **TDD Contract**: The specifications detailed here form the "WHAT" defined by Speckit. They must be rigid enough to drive automated RED-GREEN-REFACTOR cycles by subagents leveraging Superpowers.
- **Validation**: All acceptance scenarios must be mechanically verifiable without human intuition to serve as strict unit-test targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full suite run completes with all configured groups executing in defined order in 100% of invocations, regardless of inter-group failures.
- **SC-003**: Zero tests from a later-ordered group start before all tests in all earlier-ordered groups have completed, in any observed local, CI, or xdist run.
- **SC-004**: Applying group markers to an existing test suite requires no changes to individual test logic — only annotation and configuration changes.
- **SC-004a**: Applying the initial grouping to the existing suite requires no test file moves or test directory renames.
- **SC-005**: Each group can be executed in isolation by filtering on its configured marker name, producing a valid test result containing only that group's tests.
- **SC-006**: The ordering mechanism introduces no more than 2 seconds of additional collection-phase wall-clock overhead, measured by comparing `pytest --collect-only` with grouping enabled versus disabled on the same environment.
- **SC-007**: The reusable grouping utility is included in the same linting and type-checking gates as other new source code.

## Assumptions

- The existing test suite has implicit tiers that can be identified and annotated without rewriting test logic; the initial project configuration will use five example groups: `instant`, `fast`, `medium`, `slow`, and `external`. These are example cost tiers, not fixed definitions for all projects.
- "Directory designation" means a naming or structural convention that the configuration maps to a group; the exact convention (e.g., folder name prefix, path pattern) is determined during planning.
- The current mixed historical `tests/` tree is intentionally preserved for this feature; tree cleanup or semantic directory migration is out of scope.
- The group ordering feature applies to the full local and CI test suite; per-developer IDE test runs are out of scope for ordering enforcement.
- Parallel execution within a group (via xdist) may continue, but xdist execution must preserve runtime group barriers between configured groups.
- Tests currently passing in CI must continue to pass after the grouping mechanism is applied with no regressions.
- A suitable third-party pytest plugin for marker-based collection reordering exists and will be selected during planning; authoring a custom ordering plugin is out of scope.
