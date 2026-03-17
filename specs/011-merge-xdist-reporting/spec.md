# Feature Specification: Distributed Reporting Stream

**Feature Branch**: `011-merge-xdist-reporting`
**Created**: 2026-03-08
**Status**: Implemented
**Input**: User description: "Сообщения для репортинга должны собираться в единый поток при выполнении с pytest-xdist. Сообщения по сбору сценариев и шагов не должны дублироваться (будут одинаковыми между нодами и мастером), а вот сообщения про выполение - должны сливаться, чтоб можно было получить консолидированный репорт"

## Clarifications

### Session 2026-03-08

- Q: Must distributed reporting work when workers and the controller run on different machines or containers with independent filesystems, and how must acceptance be validated? → A: Yes. Consolidation must work without assuming a shared filesystem, and acceptance must include a test that runs multiple isolated Docker containers and verifies one final aggregated reporting stream.

### Session 2026-03-09

- Q: Are any specific e2e test behaviors required to represent usage within a real xdist run? → A: Yes, there should be an e2e test defined in `.feature` files that presents actual end user work with pytest-xdist.
- Q: What level of xdist modification is acceptable to support all network modes without rsync? → A: A project-local compatibility patch or adapter may target xdist internals, but the solution must not require maintaining a permanent xdist fork.
- Q: What network compatibility scope is mandatory for distributed reporting over xdist/execnet? → A: Support all officially supported xdist remote gateway modes, including execnet `via` and proxy-chain topologies, not only direct socket or SSH execution.
- Q: How should distributed reporting behave if the current xdist version cannot safely expose the required message path? → A: Fail fast with a clear diagnostic instead of silently disabling consolidated reporting or falling back to a side-channel transport.
- Q: May the feature raise the minimum supported pytest-xdist/execnet version if that is required for reliable channel integration? → A: Yes. The feature may raise the minimum supported pytest-xdist/execnet version when needed for a reliable xdist/execnet-based reporting transport.
- Q: What acceptance-validation scope is mandatory for non-direct xdist network topologies? → A: End-to-end acceptance coverage is required for every officially supported remote gateway mode, not only for direct topologies.
- Q: Where must the new tests for this feature run in automation? → A: All tests introduced for this feature must be runnable in the repository's GitHub CI configuration, not only in local developer environments.
- Q: What scripting style is preferred for new acceptance and test helpers? → A: Prefer Python helper scripts and verification utilities wherever practical; keep bash only as a thin wrapper when the behavior is inherently shell-specific.
- Q: Should acceptance tests that exercise the gherkin-message-reporter plugin (e.g., `--cucumber-html`, `--messages-ndjson`) launch pytest as a subprocess or may they re-load the plugin in-process using the `-p no:<name> -p <module>` pattern? → A: Subprocess only. All acceptance tests that activate the reporter plugin MUST invoke pytest in a separate process (`subprocess=true`). The `-p no:pytest-bdd-gherkin-message-reporter -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint` disable-then-re-enable pattern is forbidden in acceptance tests for this feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce One Consolidated Run Stream (Priority: P1)

As a report consumer, I want a distributed test run to produce one consolidated message stream so I can generate one complete report for the whole run instead of combining per-worker outputs manually.

**Why this priority**: A single consolidated stream is the core user value of the feature; without it, distributed execution still requires manual post-processing and can produce incomplete reports.

**Independent Test**: Execute one feature suite in distributed mode across every officially supported remote gateway mode, including direct and chained proxy topologies; verify that each resulting report input contains all execution outcomes from the full run in one ordered stream.

**Acceptance Scenarios**:

1. **Given** a distributed test run where different scenarios execute on different workers in separate containers with independent filesystems, **When** reporting data is collected, **Then** the final output contains execution messages from every worker in one consolidated stream.
2. **Given** a distributed test run with passed, failed, and skipped scenarios across workers, **When** the final stream is produced, **Then** each scenario outcome appears once with its actual execution status.
3. **Given** a report consumer that reads a single message stream, **When** it processes the output of a distributed run, **Then** it can build a complete run-level report without needing worker-specific inputs.

---

### User Story 2 - Suppress Duplicated Collection Messages (Priority: P2)

As a report consumer, I want collection-time scenario and step messages to appear only once so the consolidated report describes the test catalog accurately and is not inflated by duplicate structural data from multiple workers and the controller process.

**Why this priority**: Duplicate collection messages make the consolidated report misleading even if execution messages are merged correctly.

**Independent Test**: Run a distributed execution where controller and workers all observe the same collected scenarios and steps; verify that the final stream contains one structural description per scenario and per step.

**Acceptance Scenarios**:

1. **Given** a distributed run where the same scenario metadata is visible to the controller and all workers, **When** collection messages are consolidated, **Then** the final stream contains one scenario-definition message for that scenario.
2. **Given** a distributed run where the same step metadata is visible to the controller and all workers, **When** collection messages are consolidated, **Then** the final stream contains one step-definition message for each unique step.
3. **Given** a report consumer comparing structural counts to the collected suite, **When** it reads the consolidated stream, **Then** scenario and step totals match the collected suite rather than the number of processes involved.

---

### User Story 3 - Keep Execution Messages Distinct and Traceable (Priority: P3)

As a maintainer investigating distributed test results, I want execution messages from different workers to be merged without being collapsed together so I can trace what actually happened during runtime for each executed scenario and step.

**Why this priority**: Execution data is the evidence of what happened during the run; losing or collapsing distinct execution events would make the consolidated report unreliable for diagnostics.

**Independent Test**: Execute scenarios on multiple workers, including retries or mixed outcomes, and verify that each runtime event remains represented in the final stream while still belonging to one consolidated run.

**Acceptance Scenarios**:

1. **Given** two workers that execute different scenarios at the same time, **When** their runtime messages are merged, **Then** the final stream preserves both sets of execution events.
2. **Given** a scenario that is collected once but produces multiple runtime events during execution, **When** the final stream is produced, **Then** all runtime events needed to explain the observed outcome are preserved.
3. **Given** a distributed run with worker-specific failures, **When** the consolidated stream is reviewed, **Then** consumers can attribute each execution outcome to the correct executed scenario without relying on duplicated collection messages.

### Edge Cases

- A worker terminates before sending its full execution output; the final stream must remain consumable and clearly reflect missing runtime data.
- The active xdist transport implementation cannot safely attach reporting data to the xdist/execnet path for the current version or gateway topology; the run must fail with an explicit compatibility diagnostic rather than degrading to a different transport.
- A scenario is collected successfully but never executes because the run stops early; collection data must remain singular while runtime data reflects non-execution accurately.
- The same scenario executes more than once within one distributed session, such as through retry or re-run behavior; each execution must remain represented without duplicating collection metadata.
- A distributed run uses only one worker; the resulting stream must remain valid and must not change structure compared with a non-distributed run.
- Events arrive from workers in a different order than collection occurred; the consolidated stream must remain deterministic enough for report generation.
- Workers and the controller run on different machines or isolated containers with independent filesystems; consolidated reporting must still succeed without direct access to worker-local report files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST produce one consolidated reporting stream for a distributed test run, including runs where participants do not share a filesystem.
- **FR-002**: The consolidated stream MUST include execution messages emitted from every participating worker in the distributed run.
- **FR-003**: The system MUST treat collection-time scenario messages as run-wide structural data and MUST include each unique scenario-collection message no more than once in the consolidated stream.
- **FR-004**: The system MUST treat collection-time step messages as run-wide structural data and MUST include each unique step-collection message no more than once in the consolidated stream.
- **FR-005**: The system MUST merge execution-time messages from all workers into the consolidated stream rather than selecting only one worker's runtime output.
- **FR-006**: The system MUST preserve enough correlation data in the consolidated stream for report consumers to connect execution messages to the collected scenarios and steps they belong to.
- **FR-007**: The system MUST preserve the actual execution outcome for each executed scenario, including passed, failed, skipped, or otherwise unfinished execution states.
- **FR-008**: The system MUST distinguish between structural duplicates and valid repeated execution events so that deduplication never removes genuine runtime behavior.
- **FR-009**: The system MUST produce a consolidated stream that remains consumable when one or more workers contribute only a partial set of execution messages.
- **FR-010**: The system MUST keep consolidated-report behavior functionally consistent between single-process and distributed execution modes.
- **FR-011**: The system MUST ensure that consolidated structural counts for scenarios and steps match the collected suite rather than the number of controller or worker processes.
- **FR-012**: The system MUST make the consolidated stream sufficient to generate one run-level report without requiring manual merging of per-worker report artifacts.
- **FR-013**: The system MUST support distributed participants that run on different machines or isolated containers with independent local filesystems.
- **FR-014**: The system MUST transfer worker-contributed reporting data to the final consolidator without requiring direct reads from worker-local-only files.
- **FR-015**: The system MUST use the existing xdist/execnet communication path for worker-contributed reporting data and MUST NOT require a separate controller-owned TCP listener.
- **FR-016**: The system MUST avoid rsync as a reporting transport dependency because rsync-based remote synchronization is deprecated for this use case.
- **FR-017**: If public xdist APIs are insufficient, the implementation MAY use a project-local compatibility patch or adapter against xdist internals, but it MUST NOT depend on a permanently maintained xdist fork.
- **FR-018**: The distributed reporting transport MUST work across all officially supported xdist remote gateway modes, including execnet `via` and proxy-chain topologies, rather than supporting only direct socket or SSH connectivity.
- **FR-019**: If the active xdist version or gateway topology cannot safely attach the required reporting transport to the xdist/execnet communication path, distributed reporting MUST fail fast with an explicit diagnostic instead of silently disabling reporting or falling back to a separate transport.
- **FR-020**: The feature MAY raise the minimum supported pytest-xdist and execnet versions when that is required to provide a reliable reporting transport on the xdist/execnet communication path across supported remote gateway modes.
- **FR-021**: The feature MUST provide end-to-end acceptance validation for every officially supported remote gateway mode covered by xdist remote execution support, not only for direct topologies.
- **FR-022**: All tests added for this feature MUST be executable from the repository's GitHub CI configuration in addition to local developer environments.
- **FR-023**: New helper logic added for acceptance orchestration, report verification, or test fixtures MUST prefer Python implementations where practical and MUST limit bash usage to thin shell-specific wrappers.
- **FR-024**: The feature MUST include a clear end-to-end test defined in `.feature` files that illustrates real usage with pytest-xdist, covering both HTML report generation and every officially supported remote gateway mode (socket, relay/via, ssh).
- **FR-025**: Any acceptance test that activates the gherkin-message-reporter plugin (via `--cucumber-html`, `--messages-ndjson`, or equivalent flags) MUST invoke pytest in a dedicated subprocess (`subprocess=true`). Using the in-process `-p no:pytest-bdd-gherkin-message-reporter -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint` disable-and-reload pattern is forbidden in acceptance tests for this feature.

### Key Entities *(include if feature involves data)*

- **Consolidated Reporting Stream**: The single run-level sequence of reporting messages consumed to build the final report for a distributed execution.
- **Collection Message**: A structural reporting message that describes a discovered scenario or step before execution begins.
- **Execution Message**: A runtime reporting message that describes what happened while a scenario or step was executed.
- **Distributed Run Participant**: A controller or worker process that contributes collection or execution data to the same logical test run.
- **Scenario Execution Record**: The logical record that links one executed scenario to its runtime events and final outcome inside the consolidated stream.

### Assumptions & Dependencies

- Distributed execution remains a supported way to run the suite and already produces the collection and execution signals required for reporting.
- Distributed participants may run on separate machines or isolated containers with independent filesystems, so shared storage access cannot be assumed.
- Reporting transport must remain inside xdist/execnet-managed communication so that supported xdist network topologies do not depend on an additional side-channel socket opened by the reporter.
- Supported xdist network topologies include the officially supported remote gateway modes exposed through execnet, including chained proxy routing where workers are not directly reachable from the controller over a separate reporter-managed socket.
- The supported dependency floor for pytest-xdist and execnet may be raised if older versions cannot expose a reliable integration point for reporter traffic on the xdist-managed channel.
- The repository's GitHub CI environment is expected to provide at least one configuration capable of running the feature's newly added validation coverage, including Docker-backed remote acceptance checks where required.
- Scenario and step collection data are identical across participants for the same logical test item and can therefore be treated as shared structural data.
- Report consumers expect one authoritative run-level stream and do not benefit from duplicate structural messages.
- Existing report generation flows can consume a consolidated stream as long as structural messages are singular and execution messages remain complete.
- Acceptance validation for this feature includes end-to-end coverage for every officially supported remote gateway mode; for direct remote execution, at least one end-to-end run must use multiple isolated Docker containers rather than a shared local filesystem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In distributed-run validation, 100% of execution messages emitted by participating workers appear in the final consolidated stream.
- **SC-002**: In distributed-run validation, 0 duplicate scenario-collection messages remain in the final consolidated stream for the same collected scenario.
- **SC-003**: In distributed-run validation, 0 duplicate step-collection messages remain in the final consolidated stream for the same collected step.
- **SC-004**: For a reference suite executed both in single-process and distributed modes, the final report shows the same scenario and step totals in both modes.
- **SC-005**: 100% of distributed-run report fixtures used for acceptance testing can be generated from one consolidated stream without manual merging of worker-specific artifacts.
- **SC-006**: In acceptance coverage for distributed runs with mixed outcomes, 100% of executed scenarios retain their correct final status in the consolidated stream.
- **SC-007**: In acceptance validation executed across at least two isolated Docker containers with independent filesystems, exactly one final consolidated stream is produced for the run without relying on shared storage between participants.
- **SC-008**: 100% of officially supported xdist remote gateway modes have at least one passing end-to-end acceptance scenario that proves consolidated reporting over the xdist/execnet-managed transport path.
- **SC-009**: The GitHub CI configuration for this repository has at least one passing job that executes the tests added for this feature.
