# Parity evidence ledger (cycle 2, revision 8ea8a5fd)

Ticket: `elchupanebrej/pytest-bdd-ng#409`. Reference: `origin/refactoring` at `fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce`. This file is generated from `ledger.json`; the JSON is the machine-readable ledger.

## Revision and artifact

- Final revision: `8ea8a5fd5b48a25f9c8d395b388858fefa107676`, ref `parity/cycle-2-proof`. The ref is public, so the SHA stays resolvable after CI artifacts expire.
- Proof run: [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) attempt 2, success, `8ea8a5fd5b48a25f9c8d395b388858fefa107676`.
- #392 recovery run: [45389101155](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45389101155) attempt 4, success, same SHA.
- Wheel: `pytest_cuke-2.3.1-py3-none-any.whl`, SHA-256 `9746d9afbd656698c48be18a3f5a4b5371a1ea8be3f3c0bdc51fe653dc437a8e`, pure Python, built from `8ea8a5fd5b48a25f9c8d395b388858fefa107676`.
- Build command: `git worktree add /tmp/opencode/proof-wheel 8ea8a5fd && cd /tmp/opencode/proof-wheel && PYTEST_CUKE_BUILD_GO=off uv build --wheel --out-dir /tmp/opencode/proof-wheel-dist`.

## Consumer acceptance (re-run on that wheel)

Environment: CPython 3.13.15 / pytest 9.2.0; PyPy 3.12.15 (PyPy 8.0.1) for the PyPy lanes.

| Feature | Runtime | Exit | Result |
| --- | --- | ---: | --- |
| `features/compatibility/tutorial-example-acceptance.feature` | CPython 3.13.15 | 0 | 1 passed |
| `features/compatibility/pypy-runtime-acceptance.feature` | PyPy 3.12.15 | 0 | 1 passed |
| `features/compatibility/pypy-core-without-pydantic.feature` | PyPy 3.12.15 | 0 | 5 passed |
| `features/compatibility/optional-struct-bdd-extra.feature` | CPython 3.13.15 | 0 | 2 passed |
| `features/compatibility/runtime-compatibility-regressions.feature` | CPython 3.13.15 | 0 | 2 passed |
| `features/compatibility/compatibility-matrix-migration-audit.feature` | CPython 3.13.15 | 0 | 9 passed |
| `features/compatibility/browser-report.feature` | CPython 3.13.15 | 0 | 1 passed |

Examples: 7 independent projects, 17 passed, every project exit 0. Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 <venv>/bin/python -m pytest -q -p pytest_cuke.plugin -c pyproject.toml --rootdir=. (tutorial adds 'tests features')`.

## Parity statement

> **No full parity is claimed. Of the 219 external declarations, 204 are proven analogues, 10 are agreed replacements/additions, 3 are agreed exclusions, and 2 remain unproven gaps. Because declarations 133, 179 are unproven at 8ea8a5fd5b48a25f9c8d395b388858fefa107676, pytest-cuke must not be described as having full functional parity with origin/refactoring at fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce.**

The machine-readable flag is `false`. It agrees with the prose.

## Counts

| Category | Rows |
| --- | ---: |
| proven analogue | 204 |
| agreed replacement/addition | 10 |
| agreed exclusion | 3 |
| unproven gap | 2 |
| **Total** | **219** |

Row identities are unique (`path:line`), and the category counts are computed from the 219 rows.

## Numbered decisions cited

Citations resolve to this table. `US-15` and `US-27` are numbered user stories in #385 that carry the owner decision; their question numbers were not preserved in the harness record. Every other citation is a numbered owner question from the parity discussion recorded in #385.

| Id | Kind | Text | Source |
| --- | --- | --- | --- |
| `US-15` | numbered user story with owner decision | User story 15: a Python stub for a missing step without requiring Node. Owner decision: the missing-step hint is a usable pytest-cuke Python stub by default; the original JavaScript snippets formatter is replaced, not restored. | #385 user story 15 + Implementation Decisions (question number not preserved) |
| `US-27` | numbered user story with owner decision | User story 27: ordinary tests run without Node and report what to install when a selected formatter lacks dependencies. Out of Scope: automatic Node/npm installation; the product must not install formatter packages on demand. | #385 user story 27 + Out of Scope (question number not preserved) |
| `89-92` | numbered decision range | A manual binding path resolves from the configured root, or from pytest rootdir when none is set; a completely empty NDJSON stream is an error; an explicitly bound .feature.md without a Feature declaration is an error; one failing test does not by itself make the shared Allure stage broken, and real session-finish errors are surfaced. | harness parity-discussion.md, questions 89-92 |
| `93-94` | numbered decision range | Manual binding uses the configured root, falling back to pytest rootdir. The full reproducible Messages audit with probe execution and coverage checks belongs to the product and may be invoked by the harness. | harness parity-discussion.md, questions 93-94 |
| `99` | numbered decision | A .feature.md without a Feature declaration is an error both for an explicit binding and for automatic discovery. | harness parity-discussion.md, question 99 |
| `105` | numbered decision | Every step marked @not_implemented is an error by default; skip mode is selected explicitly. A marked step must not succeed in error mode. The previous success-without-execution mode is not restored. | harness parity-discussion.md, question 105 |
| `106` | numbered decision | A plain .feature file without a Feature declaration is an error. An empty directory and a Feature header with no scenarios are separate cases. | harness parity-discussion.md, question 106 |
| `107` | numbered decision | In error mode the body of a @not_implemented step is not executed and the scenario fails immediately with a clear error; in skip mode the body is also not executed. | harness parity-discussion.md, question 107 |
| `109` | numbered decision | A scenario-local tolerant policy takes precedence over the global setting, including the CLI. An explicitly allowed error stays visible and the scenario may continue. | harness parity-discussion.md, question 109 |
| `119` | numbered decision | Allure compatibility is defined by the supported format and verified against real Allure 2/3; the old design schema is not a separate mandatory contract and is updated or replaced when it conflicts with actual compatibility. | harness parity-discussion.md, question 119 |
| `121` | numbered decision | Source-code architecture evaluation, its prose descriptions, and the entity-to-score mapping belong to the Development Harness; they are stored there and updated on request. Architecture scores and score descriptions are not stored next to product sources. | harness parity-discussion.md, owner change recorded with answer 121 |
| `125` | numbered decision | The architecture mapping with scores and score descriptions is versioned in the private harness repository, not a separate score-history system; only current scores are authoritative. | harness parity-discussion.md, question 125 |

## Unproven gaps (2)

| Id | File:line | Declaration | Why it is still unproven | Exercising run at the proof SHA |
| ---: | --- | --- | --- | --- |
| 133 | `08 Go Parser/01 Go parser backend.feature.md:55` | Environment variable controls backend selection | No run sets PYTEST_BDD_GHERKIN_BACKEND. The product selects the backend through the cuke_parser CLI/ini setting (auto\|go\|python); no test or feature at 8ea8a5fd reads the reference environment variable. The exact old name is not preserved and no numbered decision names an approved replacement for it. | none |
| 179 | `12 Formatters/08 CCK Allure compatibility.feature.md:18` | Allure report renders step names | No job checks Allure step names in the rendered report. Browser report acceptance (browser-report) renders only the passed-scenario page and asserts the scenario name and passed status. The native Allure cells assert result JSON steps but do not render the browser report. | none |

Both rows were also unexecuted in the previous ledger. They are not promoted on an older revision, a partial probe, or an implementation without a run.

## The 16 formerly unexecuted rows

The ticket text says thirteen. The source ledger records sixteen rows whose probe was `not executed` and seven more unproven rows that were executed and showed a mismatch (23 unproven in total). The ledger's own set is authoritative, so this table has sixteen rows. Fourteen are now exercised at `8ea8a5fd`; two are not.

| Id | File:line | Recorded reason (at e063e53f) | At 8ea8a5fd | Run / job |
| ---: | --- | --- | --- | --- |
| 122 | `07 Report/08 xdist remote network reporting.feature.md:16` | Docker daemon unavailable; execnet socket transport not executed on this revision | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-socket) |
| 123 | `07 Report/08 xdist remote network reporting.feature.md:33` | Docker daemon unavailable; relay transport not executed on this revision | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-via) |
| 124 | `07 Report/08 xdist remote network reporting.feature.md:50` | Docker daemon unavailable; SSH transport not executed on this revision | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-ssh) |
| 130 | `08 Go Parser/01 Go parser backend.feature.md:27` | pure wheel has no native Go bridge and no Go toolchain is available; native parse not executed on e063e53f | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Native Go parser acceptance (native-linux) |
| 132 | `08 Go Parser/01 Go parser backend.feature.md:51` | version logging requires the native bridge; not executed on e063e53f | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Full runtime matrix (cpython-314-linux / py314-pytestlatest-coverage-lin) |
| 133 | `08 Go Parser/01 Go parser backend.feature.md:55` | backend selection not re-executed against the native bridge | unproven gap | none |
| 156 | `12 Formatters/02 Progress formatters.feature.md:44` | no distinct quiet mode was found/tested on the installed CLI | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) |
| 157 | `12 Formatters/02 Progress formatters.feature.md:51` | no distinct verbose mode was found/tested on the installed CLI | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) |
| 179 | `12 Formatters/08 CCK Allure compatibility.feature.md:18` | browser acceptance checks the scenario name and passed status, not step names | unproven gap | none |
| 193 | `15 Compatibility/01 Python version compatibility.feature.md:27` | only the CLI pair policy was checked; the full supported Python/pytest/OS run matrix was not executed | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / aggregate-proof |
| 201 | `17 Debug MCP/01 Agentic debugging.feature.md:4` | the installed-wheel Debug MCP acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |
| 202 | `17 Debug MCP/01 Agentic debugging.feature.md:10` | the installed-wheel Debug MCP acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |
| 203 | `17 Debug MCP/01 Agentic debugging.feature.md:26` | the installed-wheel Debug MCP acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |
| 204 | `17 Debug MCP/01 Agentic debugging.feature.md:33` | the installed-wheel Debug MCP acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |
| 205 | `17 Debug MCP/01 Agentic debugging.feature.md:39` | the installed-wheel Debug MCP acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |
| 206 | `17 Debug MCP/01 Agentic debugging.feature.md:45` | the installed-wheel Debug MCP xdist acceptance feature exceeded the 30-minute run limit without a result | proven analogue | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) |

## Agreed replacements and exclusions (13)

| Id | Category | File:line | Decision | Basis |
| ---: | --- | --- | --- | --- |
| 129 | agreed exclusion | `07 Report/09 Cucumber formatter reports.feature.md:155` | `US-27` | #385 Out of Scope: automatic Node/npm installation; the product must not auto-install formatter packages |
| 158 | agreed replacement/addition | `12 Formatters/03 Snippets formatter.feature.md:23` | `US-15` | #385 agrees a Python snippet without Node; the original JS snippets formatter is not required |
| 159 | agreed replacement/addition | `12 Formatters/03 Snippets formatter.feature.md:30` | `US-15` | #385 agrees the Python snippet shape; the JS template is replaced |
| 169 | agreed replacement/addition | `12 Formatters/06 Allure formatter.feature.md:54` | `89-92` | Decisions 89-92: a completely empty NDJSON stream is an error (exit 2). The previous note cited only decision 91; 91 is the .feature.md missing-Feature clause, so the citation is corrected to the grouped range. |
| 175 | agreed replacement/addition | `12 Formatters/07 Allure schema field coverage.feature.md:9` | `119` | #385 decision 119: the old design schema is superseded by real Allure 2/3 compatibility; result fields and statuses are generated |
| 176 | agreed replacement/addition | `12 Formatters/07 Allure schema field coverage.feature.md:81` | `119` | #385 decision 119: old schema is not a separate mandatory contract |
| 177 | agreed replacement/addition | `12 Formatters/07 Allure schema field coverage.feature.md:121` | `119` | #385 decision 119: container schema is evaluated by real Allure; generated summary has 0 broken |
| 188 | agreed replacement/addition | `13 Code Generator/01 Code generation.feature.md:328` | `105, 107` | Decisions 105 and 107: error by default, explicit skip mode, body not executed; the previous success-without-execution mode is not restored. |
| 189 | agreed replacement/addition | `13 Code Generator/01 Code generation.feature.md:375` | `109` | Corrected citation: the tolerant-policy decision is 109 (local policy precedence and visible allowed error). The previous ledger cited 131, which is the custom MIME-hook decision. |
| 199 | agreed replacement/addition | `16 Batch Collection/01 Batch collection edge cases.feature.md:73` | `99, 106` | Reclassified from unproven gap to agreed replacement. The reference scenario expects no failure for a malformed .feature.md; decisions 99 and 106 require a missing Feature declaration to be an error. #405 implements that decision at the proof head. |
| 211 | agreed exclusion | `18 Development/03 Architecture Tooling.feature.md:7` | `121, 125` | #385 moved architecture evaluation/tooling out of the product interface |
| 212 | agreed exclusion | `18 Development/03 Architecture Tooling.feature.md:25` | `121, 125` | #385 moved architecture scores and their mapping to the harness; not product functionality |
| 219 | agreed replacement/addition | `18 Development/07 Messages Coverage Audit.feature.md:4` | `93-94` | #385: the full reproducible Messages audit belongs to the product; a shell-script presence check is replaced |

## Reconciliation of the previously unnamed or misclassified row

The reference inventory extracted 221 lines. Two are Scenario/Scenario Outline lines inside Gherkin DocStrings, not external declarations. They were the unnamed phantom rows in the 221 count. They are now named in the appendix and reclassified as test data; the external count is 219.

Two further corrections are recorded in the rows: the malformed-feature row (`16 Batch Collection/01 Batch collection edge cases.feature.md:73`) moves from `unproven gap` to `agreed replacement/addition` because decisions 99 and 106 intentionally change the reference behaviour to a parse error; and the tolerant row (`13 Code Generator/01 Code generation.feature.md:375`) no longer cites decision 131, which is the custom MIME-hook decision, but decision 109, which is the tolerant-policy decision.

## Claims the proof-run jobs do not cover

The ledger does not promote, and must not be read as covering, the claims #418 names:

- `#397`: the end-to-end failed-publish contract (`tests/integration/debug-mcp/test_publish_failure.py`) skips in matrix cells and is not selected by the debug-mcp lane. The six original Debug MCP rows are proven by the debug-mcp cell; that file is not.
- `#403` / `#404`: the rejection scenarios in `features/compatibility/environment-proof-aggregation.feature` are not selected by any workflow command. The ledger's compatibility row claims the passing 59-environment matrix, not those rejections.
- `#406`: the per-run hold cap in `tests/integration/debug-mcp/test_controls.py` is not selected with the extra installed. No ledger row claims it.
- `#408`: the mutation claim that each rewritten assertion fails when its behaviour breaks has no mutation run. No ledger row claims it.

## Matrix: 219 external declarations

`Run / job` names the proof run (`45279198666`) and the job or cell. `Probe` is a local probe, and `old probe` is the #390 probe recorded in the harness evidence. Rows with no run are unproven.

### 01 Tutorial (1)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `01 Tutorial/01 Launch.feature.md:4` | Catalog example with simplest steps | proven analogue | probe A1-tutorial | harness probe: installed-tutorial-evidence.md | 1 passed |

### 02 Feature (38)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 2 | `02 Feature/01 Non-strict gherkin.feature.md:6` | Execute non-strict Gherkin background and scenario sections | proven analogue | probe F-nonstrict | harness probe: non-strict-gherkin-evidence.md | 2 passed |
| 3 | `02 Feature/02 Tag conversion.feature.md:3` | Convert feature tags to pytest marks | proven analogue | probe T1-passed | harness probe: tag-conversion-evidence.md | 1 passed, 3 deselected |
| 4 | `02 Feature/03 Markdown parsing.feature.md:6` | Parse and execute Markdown-based Gherkin steps | proven analogue | probe F-markdown | harness probe: markdown-execution-evidence.md | 1 passed |
| 5 | `02 Feature/04 Localization.feature.md:5` | Parse localized feature keywords | proven analogue | probe F-locale | harness probe: localization-evidence.md | 1 passed |
| 6 | `02 Feature/05 Rule.feature.md:6` | Discover scenarios under rules and nested rules | proven analogue | probe F-rule | harness probe: rule-discovery-evidence.md | 8 passed |
| 7 | `02 Feature/06 Tag.feature.md:64` | Run pytest with marker passed | proven analogue | probe T1-passed | harness probe: feature-tag-matrix-evidence.md | 1 passed, 3 deselected |
| 8 | `02 Feature/06 Tag.feature.md:76` | Run pytest with marker failed | proven analogue | probe T1-failed | harness probe: feature-tag-matrix-evidence.md | 1 failed, 3 deselected |
| 9 | `02 Feature/06 Tag.feature.md:88` | Run pytest with marker passed or failed | proven analogue | probe T1-passed-or-failed | harness probe: feature-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 10 | `02 Feature/06 Tag.feature.md:100` | Run pytest with marker not both | proven analogue | probe T1-not-both | harness probe: feature-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 11 | `02 Feature/06 Tag.feature.md:112` | Run pytest with marker both | proven analogue | probe T1-both | harness probe: feature-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 12 | `02 Feature/06 Tag.feature.md:124` | Run pytest with no marker | proven analogue | probe T1-all | harness probe: feature-tag-matrix-evidence.md | 2 passed, 2 failed |
| 13 | `02 Feature/07 Description.feature.md:8` | Keep feature description text | proven analogue | probe F-description | harness probe: description-evidence.md | 1 passed |
| 14 | `02 Feature/08 Error reporting.feature.md:7` | Reject multiple Feature declarations in one file | proven analogue | probe F-duplicate | harness probe: duplicate-feature-declaration-evidence.md | 1 error |
| 15 | `02 Feature/09 Load/01 Scenario without steps.feature.md:4` | Report parse error when no scenario is defined | proven analogue | probe F-naked | harness probe: naked-steps-error-evidence.md | 1 error |
| 16 | `02 Feature/09 Load/02 Scenario search from base url.feature.md:47` | Search from configured base URL | proven analogue | probe P-http | harness probe: http-named-scenario-evidence.md | 1 passed; GET /remote.feature and /rows.csv |
| 17 | `02 Feature/09 Load/03 Scenario function loader.feature.md:21` | "scenario" function is used as decorator | proven analogue | probe S11-loader | harness probe: scenario-loader-forms-evidence.md | 4 passed |
| 18 | `02 Feature/09 Load/03 Scenario function loader.feature.md:43` | "scenarios" function is used as decorator | proven analogue | probe S11-loader | harness probe: scenario-loader-forms-evidence.md | 4 passed |
| 19 | `02 Feature/09 Load/03 Scenario function loader.feature.md:65` | "scenario" function is used to register feature as test | proven analogue | probe S11-loader | harness probe: scenario-loader-forms-evidence.md | 4 passed |
| 20 | `02 Feature/09 Load/03 Scenario function loader.feature.md:82` | "scenarios" function is used to register feature as test | proven analogue | probe S11-loader | harness probe: scenario-loader-forms-evidence.md | 4 passed |
| 21 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:6` | Load feature from explicit HTTP URL | proven analogue | probe P-http-gherkin-enum-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Full runtime matrix (cpython-314-linux / py314-pytestlatest-coverage-lin) | cell passed: 1905 selected, 0 failed (1810 passed in this command) |
| 22 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:44` | Load feature using HTTP base URL from pytest.toml | proven analogue | probe P-http-base | harness probe: http-named-scenario-evidence.md | 1 passed; GET /remote.feature and /rows.csv |
| 23 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:81` | Load feature URL from Windows shortcut file | proven analogue | probe P-shortcuts | harness probe: shortcut-evidence.md | 6 single-scenario runs, all 1 passed, exit 0; broken links exit 2 |
| 24 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:138` | Load feature URL from freedesktop desktop link | proven analogue | probe P-shortcuts | harness probe: shortcut-evidence.md | 6 single-scenario runs, all 1 passed, exit 0; broken links exit 2 |
| 25 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:196` | Load feature URL from macOS webloc file | proven analogue | probe P-shortcuts | harness probe: shortcut-evidence.md | 6 single-scenario runs, all 1 passed, exit 0; broken links exit 2 |
| 26 | `02 Feature/09 Load/04 HTTP feature loading.feature.md:251` | Load StructBDD document from explicit HTTP URL | proven analogue | probe P-struct-enum-proof-head | local probe on the 8ea8a5fd wheel | 1 passed |
| 27 | `02 Feature/09 Load/05 Autoload.feature.md:34` | Feature is loaded by default | proven analogue | probe P-autoload-default-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Full runtime matrix (cpython-314-linux / py314-pytestlatest-coverage-lin) | cell passed: 1905 selected, 0 failed (1810 passed in this command) |
| 28 | `02 Feature/09 Load/05 Autoload.feature.md:42` | Feature autoload could be disabled via command line | proven analogue | probe P-autoload-cli-off | harness probe: autoload-default-root-evidence.md | 1 passed; no feature collected |
| 29 | `02 Feature/09 Load/05 Autoload.feature.md:54` | Feature autoload could be disabled via pytest.toml | proven analogue | probe P-autoload-ini-off | harness probe: autoload-default-root-evidence.md | 2 passed (explicit binding + regular test); no autoload |
| 30 | `02 Feature/09 Load/05 Autoload.feature.md:69` | Explicit scenario binding still runs when autoload is disabled | proven analogue | probe P-autoload-explicit | harness probe: autoload-default-root-evidence.md | 1 passed |
| 31 | `02 Feature/09 Load/05 Autoload.feature.md:92` | Explicit binding supports features_base_dir while autoload is disabled | proven analogue | probe P-autoload-explicit | harness probe: autoload-default-root-evidence.md | 1 passed |
| 32 | `02 Feature/09 Load/06 Feature base directory resolution.feature.md:66` | Resolve by ini-configured base directory | proven analogue | probe P-autoload-ini-dir | harness probe: autoload-default-root-evidence.md | 2 passed |
| 33 | `02 Feature/09 Load/06 Feature base directory resolution.feature.md:85` | Explicit argument overrides invalid ini base directory | proven analogue | probe P-autoload-override | harness probe: autoload-default-root-evidence.md | 1 passed |
| 34 | `02 Feature/09 Load/07 Scenario search from base directory.feature.md:45` | Search from configured base directory | proven analogue | probe P-autoload-ini-dir | harness probe: autoload-default-root-evidence.md | 2 passed |
| 35 | `02 Feature/09 Load/08 Batch collection.feature.md:45` | Batch collection is enabled by default | proven analogue | probe P-batch-auto | harness probe: batch-unit-evidence.md | 3 passed |
| 36 | `02 Feature/09 Load/08 Batch collection.feature.md:53` | Batch collection can be disabled via command line. | proven analogue | probe P-batch-off | harness probe: batch-unit-evidence.md | 3 passed |
| 37 | `02 Feature/09 Load/08 Batch collection.feature.md:65` | Batch collection can be disabled via pytest.toml | proven analogue | probe P-batch-ini-off | harness probe: batch-unit-evidence.md | 3 passed |
| 38 | `02 Feature/09 Load/08 Batch collection.feature.md:80` | Batch threshold can be set via pytest.toml | proven analogue | probe P-batch-threshold | harness probe: batch-unit-evidence.md | 3 passed |
| 39 | `02 Feature/09 Load/08 Batch collection.feature.md:95` | Explicit scenario binding still works with batch disabled | proven analogue | probe P-batch-bound | harness probe: batch-unit-evidence.md | 1 passed |

### 03 Scenario (32)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 40 | `03 Scenario/01 Scenario binding.feature.md:6` | Bind a test function to an existing scenario | proven analogue | probe S8-fixture-flow | harness probe: fixture-flow-evidence.md | 2 passed |
| 41 | `03 Scenario/01 Scenario binding.feature.md:55` | Skip when bound scenario is missing | proven analogue | probe S12-missing-binding | harness probe: missing-scenario-binding-evidence.md | 1 skipped |
| 42 | `03 Scenario/02 Tag.feature.md:47` | Run pytest selecting tests tagged with `passed` | proven analogue | probe T2-passed | harness probe: scenario-tag-rule-matrix-evidence.md | 1 passed, 3 deselected |
| 43 | `03 Scenario/02 Tag.feature.md:59` | Run pytest selecting tests tagged with `failed` | proven analogue | probe T2-failed | harness probe: scenario-tag-rule-matrix-evidence.md | 1 failed, 3 deselected |
| 44 | `03 Scenario/02 Tag.feature.md:71` | Run pytest selecting tests tagged with `passed` or `failed` | proven analogue | probe T2-passed-or-failed | harness probe: scenario-tag-rule-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 45 | `03 Scenario/02 Tag.feature.md:83` | Run pytest selecting tests not tagged with `both` | proven analogue | probe T2-not-both | harness probe: scenario-tag-rule-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 46 | `03 Scenario/02 Tag.feature.md:95` | Run pytest selecting tests tagged with `both` | proven analogue | probe T2-both | harness probe: scenario-tag-rule-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 47 | `03 Scenario/02 Tag.feature.md:107` | Run pytest without marker selection (all tests) | proven analogue | probe T2-all | harness probe: scenario-tag-rule-matrix-evidence.md | 2 passed, 2 failed |
| 48 | `03 Scenario/03 Description.feature.md:8` | Keep scenario description text | proven analogue | probe F-description | harness probe: description-evidence.md | 1 passed |
| 49 | `03 Scenario/04 Tag filtering.feature.md:6` | Select scenarios by marker expression | proven analogue | probe T5-smoke | harness probe: tag-filter-evidence.md | 2 passed, 1 deselected |
| 50 | `03 Scenario/04 Tag filtering.feature.md:58` | Keep tags working after background blocks | proven analogue | probe T6-background | harness probe: tag-after-background-evidence.md | 1 passed, 1 deselected |
| 51 | `03 Scenario/05 Alias.feature.md:7` | Alias-decorated steps execute consistently | proven analogue | probe S7-alias | harness probe: step-alias-evidence.md | 1 passed |
| 52 | `03 Scenario/06 Scenarios loader.feature.md:6` | Load scenarios with `scenarios()` and keep bound scenario explicit | proven analogue | probe S11-loader | harness probe: scenario-loader-forms-evidence.md | 4 passed |
| 53 | `03 Scenario/06 Scenarios loader.feature.md:82` | Skip when no scenarios are found by `scenarios()` | proven analogue | probe S13-loader-empty | harness probe: missing-scenario-binding-evidence.md | 1 skipped |
| 54 | `03 Scenario/07 Background.feature.md:6` | Background values are available and execute in order | proven analogue | probe F-background-order | harness probe: background-order-evidence.md | 2 passed |
| 55 | `03 Scenario/08 Outline/01 Runtime expansion.feature.md:6` | Outline examples expand with parametrized fixtures | proven analogue | probe F-outline-params | harness probe: outline-pytest-parameters-evidence.md | 2 passed |
| 56 | `03 Scenario/08 Outline/01 Runtime expansion.feature.md:74` | Invalid outline example table reports parsing error | proven analogue | probe F-invalid-outline | harness probe: invalid-outline-table-evidence.md | 1 error |
| 57 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:52` | Run pytest with marker "passed" | proven analogue | probe T3-passed | harness probe: examples-tag-matrix-evidence.md | 1 passed, 3 deselected |
| 58 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:64` | Run pytest with no marker filter | proven analogue | probe T3-all | harness probe: examples-tag-matrix-evidence.md | 2 passed, 2 failed |
| 59 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:76` | Run pytest with marker 'passed or failed' | proven analogue | probe T3-passed-or-failed | harness probe: examples-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 60 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:88` | Run pytest with marker 'not both' | proven analogue | probe T3-not-both | harness probe: examples-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 61 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:100` | Run pytest with marker 'both' | proven analogue | probe T3-both | harness probe: examples-tag-matrix-evidence.md | 1 passed, 1 failed, 2 deselected |
| 62 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:112` | Run pytest with all markers | proven analogue | probe T3-all | harness probe: examples-tag-matrix-evidence.md | 2 passed, 2 failed |
| 63 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:164` | Run pytest with feature_tag | proven analogue | probe T4-feature_tag | harness probe: examples-tag-filter-evidence.md | 2 passed |
| 64 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:176` | Run pytest with examples_tag | proven analogue | probe T4-examples_tag | harness probe: examples-tag-filter-evidence.md | 1 passed, 1 deselected |
| 65 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:188` | Run pytest with not feature_tag | proven analogue | probe T4-not-feature_tag | harness probe: examples-tag-filter-evidence.md | 2 deselected |
| 66 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:200` | Run pytest with not examples_tag | proven analogue | probe T4-not-examples_tag | harness probe: examples-tag-filter-evidence.md | 1 passed, 1 deselected |
| 67 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:212` | Run pytest with feature_tag and collect only | proven analogue | probe T4-collect-feature_tag | harness probe: examples-tag-filter-evidence.md | 2 tests collected |
| 68 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:223` | Run pytest with examples_tag and collect only | proven analogue | probe T4-collect-examples_tag | harness probe: examples-tag-filter-evidence.md | 1/2 tests collected (1 deselected) |
| 69 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:234` | Run pytest with not feature_tag and collect only | proven analogue | probe T4-collect-not-feature_tag | harness probe: examples-tag-filter-evidence.md | no tests collected (2 deselected) |
| 70 | `03 Scenario/08 Outline/02 Examples Tag.feature.md:245` | Run pytest with not examples_tag and collect only | proven analogue | probe T4-collect-not-examples_tag | harness probe: examples-tag-filter-evidence.md | 1/2 tests collected (1 deselected) |
| 71 | `03 Scenario/08 Outline/03 Empty values.feature.md:6` | Scenario outline accepts empty example values | proven analogue | probe F-empty-values | harness probe: outline-empty-values-evidence.md | 1 passed |

### 04 Step (9)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 72 | `04 Step/01 Doc string.feature.md:2` | Read step doc string | proven analogue | probe S9-step-data | harness probe: installed-step-data-evidence.md | 2 passed |
| 73 | `04 Step/02 Data table.feature.md:2` | Read step data table | proven analogue | probe S9-step-data | harness probe: installed-step-data-evidence.md | 2 passed |
| 74 | `04 Step/03 Step definition bounding.feature.md:2` | Steps are executed by corresponding step keyword decorator | proven analogue | probe S5-0 | harness probe: liberal-steps-evidence.md | 1 passed |
| 75 | `04 Step/03 Step definition bounding.feature.md:86` | Steps could be executed by aliased step keyword decorator | proven analogue | probe S5-1 | harness probe: liberal-steps-evidence.md | 1 passed |
| 76 | `04 Step/03 Step definition bounding.feature.md:177` | Same step is used with different keywords | proven analogue | probe S5-2 | harness probe: liberal-steps-evidence.md | 1 passed |
| 77 | `04 Step/03 Step definition bounding.feature.md:212` | Keyworded steps could be treated as liberal by pytest command line option | proven analogue | probe S5-3 | harness probe: liberal-steps-evidence.md | 1 passed |
| 78 | `04 Step/04 Step lifecycle and errors.feature.md:5` | Missing step definition produces a clear failure | proven analogue | probe P-missing-hint | harness probe: missing-steps-evidence.md | 1 failed; Python snippet for the missing step |
| 79 | `04 Step/04 Step lifecycle and errors.feature.md:26` | One function can serve multiple step aliases | proven analogue | probe S7-alias | harness probe: step-alias-evidence.md | 1 passed |
| 80 | `04 Step/04 Step lifecycle and errors.feature.md:73` | Unknown first keyword resolves through generic step decorator | proven analogue | probe S10-generic | harness probe: generic-first-step-evidence.md | 1 passed |

### 05 Step definition (18)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 81 | `05 Step definition/01 Pytest fixtures substitution.feature.md:11` | Resolve pytest fixtures in step parameters | proven analogue | probe S8-fixture-flow | harness probe: fixture-flow-evidence.md | 2 passed |
| 82 | `05 Step definition/02 Target fixtures specification.feature.md:7` | Single fixture injection | proven analogue | probe S4-0 | harness probe: step-contract-evidence.md | 2 passed |
| 83 | `05 Step definition/02 Target fixtures specification.feature.md:52` | Multiple fixtures injection | proven analogue | probe S4-1 | harness probe: step-contract-evidence.md | 2 passed |
| 84 | `05 Step definition/03 Parameters/01 Conversion.feature.md:13` | for non-anonymous groups | proven analogue | probe S2-0 | harness probe: anonymous-parameter-conversion-evidence.md | 1 passed |
| 85 | `05 Step definition/03 Parameters/01 Conversion.feature.md:43` | anonymous group parameter conversion with named mapping | proven analogue | probe S2-1 | harness probe: anonymous-parameter-conversion-evidence.md | 1 passed |
| 86 | `05 Step definition/03 Parameters/01 Conversion.feature.md:68` | cucumber expressions parameter conversion | proven analogue | probe S2-2 | harness probe: anonymous-parameter-conversion-evidence.md | 1 passed |
| 87 | `05 Step definition/03 Parameters/02 Parsing by custom parser.feature.md:3` | Parse parameters with custom parser | proven analogue | probe S6-step-contract | harness probe: step-contract-evidence.md | 3 passed |
| 88 | `05 Step definition/03 Parameters/03 Injection as fixtures.feature.md:13` | Step parameters are injected as fixtures by default | proven analogue | probe S3-0 | harness probe: parameter-injection-isolation-evidence.md | 3 passed |
| 89 | `05 Step definition/03 Parameters/03 Injection as fixtures.feature.md:80` | Step parameters injection as fixtures could be disabled | proven analogue | probe S3-1 | harness probe: parameter-injection-isolation-evidence.md | 2 passed |
| 90 | `05 Step definition/03 Parameters/03 Injection as fixtures.feature.md:145` | Step parameters renaming on injection as fixtures | proven analogue | probe S3-2 | harness probe: parameter-injection-isolation-evidence.md | 2 passed |
| 91 | `05 Step definition/03 Parameters/03 Injection as fixtures.feature.md:205` | Only allowed step parameters injection as fixtures | proven analogue | probe S3-3 | harness probe: parameter-injection-isolation-evidence.md | 2 passed |
| 92 | `05 Step definition/03 Parameters/04 Parsing.feature.md:25` | Heuristic parser guesses a type and builds particular parser to be applied | proven analogue | probe S1-0 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 93 | `05 Step definition/03 Parameters/04 Parsing.feature.md:80` | by "parse" | proven analogue | probe S1-1 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 94 | `05 Step definition/03 Parameters/04 Parsing.feature.md:137` | by "cfparse" | proven analogue | probe S1-2 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 95 | `05 Step definition/03 Parameters/04 Parsing.feature.md:195` | by "cucumber-expressions" | proven analogue | probe S1-3 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 96 | `05 Step definition/03 Parameters/04 Parsing.feature.md:251` | by [Cucumber regular expression](https://github.com/cucumber/cucumber-expressions) step parser | proven analogue | probe S1-4 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 97 | `05 Step definition/03 Parameters/04 Parsing.feature.md:303` | by "regular-expressions" | proven analogue | probe S1-5 | harness probe: step-parser-matrix-evidence.md | 1 passed |
| 98 | `05 Step definition/03 Parameters/05 Defaults.feature.md:2` | Apply default parameter values | proven analogue | probe S6-step-contract | harness probe: step-contract-evidence.md | 3 passed |

### 06 StructBDD (9)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 99 | `06 StructBDD/01 Steps.feature.md:5` | Execute steps from StructBDD YAML definition | proven analogue | probe B1-formats | harness probe: struct-bdd-evidence.md | 8 passed |
| 100 | `06 StructBDD/01 Steps.feature.md:76` | StructBDD examples expand into multiple executions | proven analogue | probe B2-joined | harness probe: struct-bdd-joined-examples-evidence.md | 4 passed; DEDUPE_COUNTS 4 4 |
| 101 | `06 StructBDD/02 StructBDD edge cases.feature.md:27` | Parse HOCON StructBDD file | proven analogue | probe B1-formats | harness probe: struct-bdd-evidence.md | 8 passed |
| 102 | `06 StructBDD/02 StructBDD edge cases.feature.md:39` | Parse TOML StructBDD file | proven analogue | probe B1-formats | harness probe: struct-bdd-evidence.md | 8 passed |
| 103 | `06 StructBDD/02 StructBDD edge cases.feature.md:51` | StructBDD deserialization error on malformed input | proven analogue | probe B4-malformed | harness probe: struct-bdd-evidence.md | 1 error |
| 104 | `06 StructBDD/02 StructBDD edge cases.feature.md:66` | StructBDD skipped when not installed | proven analogue | probe A3-pypy-core | harness probe: struct-bdd-evidence.md | 5 passed |
| 105 | `06 StructBDD/03 Deserialization.feature.md:5` | Node, Table, and Step defaults deserialize safely | proven analogue | probe B1-formats | harness probe: struct-bdd-joined-examples-evidence.md | 8 passed |
| 106 | `06 StructBDD/03 Deserialization.feature.md:42` | Joined examples build expanded tables and executable pickles | proven analogue | probe B2-joined | harness probe: struct-bdd-joined-examples-evidence.md | 4 passed; DEDUPE_COUNTS 4 4 |
| 107 | `06 StructBDD/03 Deserialization.feature.md:109` | Nested alternative steps deserialize without errors | proven analogue | probe B3-nested | harness probe: struct-bdd-joined-examples-evidence.md | 3 passed; DEDUPE_COUNTS 3 3 |

### 07 Report (22)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 108 | `07 Report/01 Gherkin terminal reporter.feature.md:5` | Verbose reporter shows feature and scenario names | proven analogue | probe P-live-pretty-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) | cell passed: 130 selected, 130 passed |
| 109 | `07 Report/01 Gherkin terminal reporter.feature.md:53` | Double-verbose mode renders substituted outline values | proven analogue | probe P-live-pretty-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) | cell passed: 130 selected, 130 passed |
| 110 | `07 Report/02 Gathering.feature.md:23` | NDJson(JSONL) could be produced on the feature run | proven analogue | probe R-messages | harness probe: incomplete-allure-evidence.md | 1 failed, 1 passed, 1 skipped; 42 envelopes |
| 111 | `07 Report/02 Gathering.feature.md:39` | HTML report could be produced on the feature run | proven analogue | probe R-html | harness probe: cucumber-html-browser-evidence.md | 1 failed, 1 passed, 1 skipped; 933 KB HTML |
| 112 | `07 Report/02 Gathering.feature.md:57` | Verbose reporting handles complex scenario parameters | proven analogue | probe R-complex | harness probe: complex-parameters-report-evidence.md | 1 passed |
| 113 | `07 Report/03 Allure scenario.feature.md:5` | Scenario reporting writes Allure-Cucumber results | proven analogue | probe P-allure-full | harness probe: report-outcomes-evidence.md | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 114 | `07 Report/04 Allure outline.feature.md:5` | Outline reporting writes Allure-Cucumber results | proven analogue | probe P-allure-full | harness probe: incomplete-allure-evidence.md | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 115 | `07 Report/05 Cucumber JSON reporter.feature.md:5` | Generate cucumber JSON with mixed pass/fail scenarios | proven analogue | probe R-json | harness probe: report-outcomes-evidence.md | 1 failed, 1 passed, 1 skipped |
| 116 | `07 Report/05 Cucumber JSON reporter.feature.md:63` | Outline example rows are serialized into separate cucumber entries | proven analogue | probe R-outline-json | harness probe: outline-json-report-evidence.md | 2 passed; JSON has two separate elements with substituted steps |
| 117 | `07 Report/05 Cucumber JSON reporter.feature.md:111` | Generate cucumber JSON with skipped scenario via tag | proven analogue | probe R-json-tag-skip | harness probe: report-outcomes-evidence.md | 1 passed, 1 skipped; skipped-by-tag status in JSON |
| 118 | `07 Report/05 Cucumber JSON reporter.feature.md:154` | Generate cucumber JSON with dynamically skipped scenario | proven analogue | probe R-json | harness probe: report-outcomes-evidence.md | 1 failed, 1 passed, 1 skipped |
| 119 | `07 Report/06 Allure/01 scenario.feature:2` | Simple passed scenario | proven analogue | probe P-allure-full | harness probe: allure-full-surface-evidence.md | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 120 | `07 Report/06 Allure/02 outline.feature:2` | Scenario outline | proven analogue | probe P-allure-full | harness probe: allure-full-surface-evidence.md | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 121 | `07 Report/07 xdist HTML reporting.feature.md:44` | Single consolidated HTML report is produced from a distributed xdist run | proven analogue | probe R-xdist-html | harness probe: cucumber-html-browser-evidence.md | 1 failed, 1 passed, 1 skipped; one HTML with gw0/gw1 stages |
| 122 | `07 Report/08 xdist remote network reporting.feature.md:16` | Consolidated report is produced when workers communicate over execnet socket | proven analogue | probe P-remote-socket-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-socket) | cell passed: 6 selected, 6 passed (complete and worker-interrupted) |
| 123 | `07 Report/08 xdist remote network reporting.feature.md:33` | Consolidated report is produced when workers communicate via a relay node | proven analogue | probe P-remote-via-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-via) | cell passed: 6 selected, 6 passed (complete and worker-interrupted) |
| 124 | `07 Report/08 xdist remote network reporting.feature.md:50` | Consolidated report is produced when workers communicate over SSH | proven analogue | probe P-remote-ssh-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Remote xdist acceptance (remote-ssh) | cell passed: 6 selected, 6 passed (complete and worker-interrupted) |
| 125 | `07 Report/09 Cucumber formatter reports.feature.md:45` | Console formatter flags can be rendered during the pytest run | proven analogue | probe R-summary | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; 3 scenarios, duration |
| 126 | `07 Report/09 Cucumber formatter reports.feature.md:70` | File formatter flags can be rendered during the pytest run | proven analogue | probe R-junit | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; tests=3 failures=1 |
| 127 | `07 Report/09 Cucumber formatter reports.feature.md:98` | Multiple cucumber formatter outputs can be requested in one run | proven analogue | probe R-multi | harness probe: installed-examples-evidence.md | 1 failed, 1 passed; all three outputs produced |
| 128 | `07 Report/09 Cucumber formatter reports.feature.md:122` | Existing NDJSON can be post-processed into formatter outputs | proven analogue | probe R-replay-multi | harness probe: installed-examples-evidence.md | JUnit XML and usage JSON produced |
| 129 | `07 Report/09 Cucumber formatter reports.feature.md:155` | Missing formatter packages are auto-installed on demand | agreed exclusion | decision US-27 | agreed | ERROR: requires npm package '@cucumber/cucumber'; install it with npm install |

### 08 Go Parser (4)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 130 | `08 Go Parser/01 Go parser backend.feature.md:27` | Parse succeeds when Go library is available | proven analogue | probe P-native-go-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Native Go parser acceptance (native-linux) | native-linux cell passed: 40 selected, 40 passed |
| 131 | `08 Go Parser/01 Go parser backend.feature.md:39` | Falls back to Python parser when Go unavailable | proven analogue | probe P-go-fallback | harness probe: pytest-scenario-report-evidence.md | Go parser unavailable warning; Python fallback executed |
| 132 | `08 Go Parser/01 Go parser backend.feature.md:51` | Go parser version is logged on first use | proven analogue | probe P-go-version-log-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Full runtime matrix (cpython-314-linux / py314-pytestlatest-coverage-lin) | cell passed: 1905 selected, 0 failed (1810 passed in this command) |
| 133 | `08 Go Parser/01 Go parser backend.feature.md:55` | Environment variable controls backend selection | unproven gap | unproven: No run sets PYTEST_BDD_GHERKIN_BACKEND. The product selects the backend through the cuke_parser CLI/ini setting (auto\|go\|python); no test or feature at 8ea8a5fd reads the reference environment variable. The exact old name is not preserved and no numbered decision names an approved replacement for it. | none at this SHA |  |

### 09 Tag Expressions (8)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 134 | `09 Tag Expressions/01 Tag expression evaluation.feature.md:4` | Evaluate AND expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 135 | `09 Tag Expressions/01 Tag expression evaluation.feature.md:9` | Evaluate OR expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 136 | `09 Tag Expressions/01 Tag expression evaluation.feature.md:15` | Evaluate NOT expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 137 | `09 Tag Expressions/01 Tag expression evaluation.feature.md:20` | Complex boolean expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 138 | `09 Tag Expressions/02 Edge cases.feature.md:4` | Empty tag expression evaluates to True | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 139 | `09 Tag Expressions/02 Edge cases.feature.md:10` | Single tag expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 140 | `09 Tag Expressions/02 Edge cases.feature.md:15` | Triple AND expression | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |
| 141 | `09 Tag Expressions/02 Edge cases.feature.md:20` | Deeply nested parentheses | proven analogue | probe P-tag-expr | harness probe: tag-expression-unit-evidence.md | 18/18 truth checks across 8 scenarios |

### 10 Heading Validation (3)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 142 | `10 Heading Validation/01 Heading validation.feature.md:4` | Empty feature heading is detected | proven analogue | probe P-heading-feature | harness probe: heading-validator-evidence.md | EMPTY_HEADING_TITLE, heading_type=feature |
| 143 | `10 Heading Validation/01 Heading validation.feature.md:9` | Empty scenario heading is detected | proven analogue | probe P-heading-scenario | harness probe: heading-validator-evidence.md | EMPTY_HEADING_TITLE, heading_type=scenario |
| 144 | `10 Heading Validation/01 Heading validation.feature.md:14` | Valid headings pass validation | proven analogue | probe P-heading-clean | harness probe: heading-validator-evidence.md | status=pass, violations=[] |

### 11 Mimetype (5)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 145 | `11 Mimetype/01 Mimetype detection.feature.md:4` | Detect .feature extension as gherkin_plain | proven analogue | probe M-mimetype | harness probe: mimetype-basic-evidence.md | gherkin_plain, gherkin_markdown, struct_bdd_yaml/hjson/json5/toml/hocon |
| 146 | `11 Mimetype/01 Mimetype detection.feature.md:8` | Detect .feature.md extension as gherkin_markdown | proven analogue | probe M-mimetype | harness probe: mimetype-basic-evidence.md | gherkin_plain, gherkin_markdown, struct_bdd_yaml/hjson/json5/toml/hocon |
| 147 | `11 Mimetype/01 Mimetype detection.feature.md:12` | Detect .bdd.yaml extension as struct_bdd_yaml | proven analogue | probe M-mimetype | harness probe: mimetype-basic-evidence.md | gherkin_plain, gherkin_markdown, struct_bdd_yaml/hjson/json5/toml/hocon |
| 148 | `11 Mimetype/01 Mimetype detection.feature.md:16` | Mimetype hook override routes correctly | proven analogue | probe E-custom-parser | harness probe: installed-examples-evidence.md | 1 passed |
| 149 | `11 Mimetype/02 Edge cases.feature.md:4` | StructBDD extension resolves correctly | proven analogue | probe M-mimetype | harness probe: struct-bdd-evidence.md | gherkin_plain, gherkin_markdown, struct_bdd_yaml/hjson/json5/toml/hocon |

### 12 Formatters (31)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 150 | `12 Formatters/01 JUnit XML reporter.feature.md:27` | JUnit XML output contains test suite structure | proven analogue | probe R-junit | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; tests=3 failures=1 |
| 151 | `12 Formatters/01 JUnit XML reporter.feature.md:42` | JUnit XML contains test case elements | proven analogue | probe R-junit | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; tests=3 failures=1 |
| 152 | `12 Formatters/01 JUnit XML reporter.feature.md:49` | JUnit XML contains failure element on failed test | proven analogue | probe R-junit | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; tests=3 failures=1 |
| 153 | `12 Formatters/01 JUnit XML reporter.feature.md:70` | JUnit XML output is valid XML | proven analogue | probe R-junit | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; tests=3 failures=1 |
| 154 | `12 Formatters/02 Progress formatters.feature.md:30` | Progress formatter shows output during run | proven analogue | probe R-progress | harness probe: progress-formatters-evidence.md | 1 failed, 1 passed, 1 skipped |
| 155 | `12 Formatters/02 Progress formatters.feature.md:37` | Progress bar formatter shows bar during run | proven analogue | probe R-progress-bar | harness probe: progress-formatters-evidence.md | 1 failed, 1 passed, 1 skipped |
| 156 | `12 Formatters/02 Progress formatters.feature.md:44` | Progress formatter quiet mode | proven analogue | probe P-progress-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) | cell passed: 130 selected, 130 passed |
| 157 | `12 Formatters/02 Progress formatters.feature.md:51` | Progress formatter verbose mode | proven analogue | probe P-progress-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) | cell passed: 130 selected, 130 passed |
| 158 | `12 Formatters/03 Snippets formatter.feature.md:23` | Snippets formatter suggests undefined step | agreed replacement/addition | decision US-15 | agreed | 1 failed; Python snippet for the missing step |
| 159 | `12 Formatters/03 Snippets formatter.feature.md:30` | Snippet template format is correct | agreed replacement/addition | decision US-15 | agreed | 1 failed; Python snippet for the missing step |
| 160 | `12 Formatters/04 Summary formatter.feature.md:28` | Summary shows run statistics | proven analogue | probe R-summary | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; 3 scenarios, duration |
| 161 | `12 Formatters/04 Summary formatter.feature.md:35` | Summary shows duration | proven analogue | probe R-summary | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; 3 scenarios, duration |
| 162 | `12 Formatters/04 Summary formatter.feature.md:42` | Summary shows failed test count | proven analogue | probe R-summary | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; 3 scenarios, duration |
| 163 | `12 Formatters/05 Usage statistics.feature.md:28` | Usage formatter shows step definition counts | proven analogue | probe P-usage-count-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Live formatter acceptance (live-formatters-linux) | cell passed: 130 selected, 130 passed |
| 164 | `12 Formatters/05 Usage statistics.feature.md:35` | Usage JSON formatter produces valid JSON | proven analogue | probe R-usage-json | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; valid JSON with matches arrays |
| 165 | `12 Formatters/05 Usage statistics.feature.md:42` | Usage detects unused step definitions | proven analogue | probe R-usage | harness probe: installed-examples-evidence.md | 1 passed; usage table lists one match and UNUSED for the unused step |
| 166 | `12 Formatters/05 Usage statistics.feature.md:64` | Usage JSON contains step match counts | proven analogue | probe R-usage-json | harness probe: installed-examples-evidence.md | 1 failed, 1 passed, 1 skipped; valid JSON with matches arrays |
| 167 | `12 Formatters/06 Allure formatter.feature.md:6` | Convert a minimal valid NDJSON to Allure results | proven analogue | probe P-allure-convert | harness probe: allure-converter-evidence.md | 8 files written for 3 scenarios |
| 168 | `12 Formatters/06 Allure formatter.feature.md:29` | Convert NDJSON with multiple scenarios | proven analogue | probe P-allure-convert | harness probe: incomplete-allure-evidence.md | 8 files written for 3 scenarios |
| 169 | `12 Formatters/06 Allure formatter.feature.md:54` | Handle empty NDJSON gracefully | agreed replacement/addition | decision 89-92 | agreed | input contains no Cucumber messages |
| 170 | `12 Formatters/06 Allure formatter.feature.md:63` | CLI rejects nonexistent input file | proven analogue | probe P-allure-missing | harness probe: allure-converter-evidence.md | cannot read input |
| 171 | `12 Formatters/06 Allure formatter.feature.md:71` | Runtime plugin generates Allure results during pytest run | proven analogue | probe R-allure | harness probe: report-outcomes-evidence.md | 1 failed, 1 passed, 1 skipped; 3 result JSON |
| 172 | `12 Formatters/06 Allure formatter.feature.md:123` | Live mode generates Allure results without NDJSON file | proven analogue | probe R-allure | harness probe: report-outcomes-evidence.md | 1 failed, 1 passed, 1 skipped; 3 result JSON |
| 173 | `12 Formatters/06 Allure formatter.feature.md:166` | Runtime plugin renders full pytest-bdd feature surface in an Allure report | proven analogue | probe P-allure-full | harness probe: allure-full-surface-evidence.md | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 174 | `12 Formatters/06 Allure formatter.feature.md:338` | Convert existing NDJSON file to Allure report via CLI | proven analogue | probe P-allure-convert | harness probe: allure-converter-evidence.md | 8 files written for 3 scenarios |
| 175 | `12 Formatters/07 Allure schema field coverage.feature.md:9` | Live pytest CLI run produces TestResult schema fields | agreed replacement/addition | decision 119 | agreed | 2 passed, 2 failed; 4 result JSON with names, statuses and steps |
| 176 | `12 Formatters/07 Allure schema field coverage.feature.md:81` | Post-hoc pytest CLI import produces TestResult schema fields | agreed replacement/addition | decision 119 | agreed | 8 files written for 3 scenarios |
| 177 | `12 Formatters/07 Allure schema field coverage.feature.md:121` | Post-hoc pytest CLI import produces container schema fields | agreed replacement/addition | decision 119 | agreed | summary.json: 2 passed, 2 failed, 0 broken |
| 178 | `12 Formatters/08 CCK Allure compatibility.feature.md:10` | Allure report renders scenario names | proven analogue | probe A6-browser | harness probe: allure-container-semantics-evidence.md | 1 passed |
| 179 | `12 Formatters/08 CCK Allure compatibility.feature.md:18` | Allure report renders step names | unproven gap | unproven: No job checks Allure step names in the rendered report. Browser report acceptance (browser-report) renders only the passed-scenario page and asserts the scenario name and passed status. The native Allure cells assert result JSON steps but do not render the browser report. | none at this SHA |  |
| 180 | `12 Formatters/08 CCK Allure compatibility.feature.md:26` | Allure report renders test status | proven analogue | probe A6-browser | harness probe: allure-container-semantics-evidence.md | 1 passed |

### 13 Code Generator (9)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 181 | `13 Code Generator/01 Code generation.feature.md:4` | Gather missing artifacts as NDJSON | proven analogue | probe P-gen-gather | harness probe: gather-missing-ndjson-evidence.md | missing_scenario_binding + missing_step_definition JSON |
| 182 | `13 Code Generator/01 Code generation.feature.md:44` | Bind a feature idempotently | proven analogue | probe P-gen-bind | harness probe: binding-generator-idempotence-evidence.md | status=unchanged; target byte-identical; pytest 1 passed |
| 183 | `13 Code Generator/01 Code generation.feature.md:76` | Generate inert missing step skeletons | proven analogue | probe P-gen-steps | harness probe: generation-result-evidence.md | status=changed, steps_added=1 |
| 184 | `13 Code Generator/01 Code generation.feature.md:119` | Mock-run validates bindings without executing lifecycle code | proven analogue | probe P-mock-binding | harness probe: mock-binding-evidence.md | 2 passed; no body-*.txt or step-executed.txt; duplicate-bindings diagnostic |
| 185 | `13 Code Generator/01 Code generation.feature.md:169` | Mock-run emits IDE bootstrap messages without executing bodies | proven analogue | probe P-mock-ide | harness probe: mock-binding-evidence.md | 1 passed; launch+step-binding attachments; body not run |
| 186 | `13 Code Generator/01 Code generation.feature.md:221` | Mock-run emits missing-step diagnostics for code authoring | proven analogue | probe P-mock-missing | harness probe: mock-binding-evidence.md | 1 failed; launch+diagnostic attachments with missing step |
| 187 | `13 Code Generator/01 Code generation.feature.md:264` | Mock-run reports duplicate source bindings | proven analogue | probe P-mock-binding | harness probe: mock-binding-evidence.md | 2 passed; no body-*.txt or step-executed.txt; duplicate-bindings diagnostic |
| 188 | `13 Code Generator/01 Code generation.feature.md:328` | Not implemented steps can be treated as passed work in progress | agreed replacement/addition | decision 105, 107 | agreed | 1 failed; Not-implemented step failed by policy; body not run |
| 189 | `13 Code Generator/01 Code generation.feature.md:375` | Tolerant ignored failures let scenarios continue | agreed replacement/addition | decision 109 | agreed | 1 passed; continued.txt written |

### 14 Scenario Reporter (3)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 190 | `14 Scenario Reporter/01 Scenario reporting.feature.md:46` | Scenario reporter records scenario name | proven analogue | probe R-scenario-report | harness probe: pytest-scenario-report-evidence.md | 2 passed; jsonl has scenario name and attachment scenario |
| 191 | `14 Scenario Reporter/01 Scenario reporting.feature.md:50` | Scenario reporter records scenario that uses attachments | proven analogue | probe R-scenario-report | harness probe: pytest-scenario-report-evidence.md | 2 passed; jsonl has scenario name and attachment scenario |
| 192 | `14 Scenario Reporter/01 Scenario reporting.feature.md:55` | Scenario reporter records passed scenario | proven analogue | probe R-scenario-report | harness probe: pytest-scenario-report-evidence.md | 2 passed; jsonl has scenario name and attachment scenario |

### 15 Compatibility (2)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 193 | `15 Compatibility/01 Python version compatibility.feature.md:27` | Pytest version compatibility holds for supported range | proven analogue | probe P-full-matrix-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / aggregate-proof | aggregate-proof passed: 59/59 expected environments, outcome passed |
| 194 | `15 Compatibility/01 Python version compatibility.feature.md:31` | Pytest mark expression parsing works | proven analogue | probe T5-and | harness probe: feature-tag-matrix-evidence.md | 1 passed, 2 deselected |

### 16 Batch Collection (6)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 195 | `16 Batch Collection/01 Batch collection edge cases.feature.md:39` | Batch collection processes multiple files | proven analogue | probe P-batch-auto | harness probe: batch-unit-evidence.md | 3 passed |
| 196 | `16 Batch Collection/01 Batch collection edge cases.feature.md:43` | Batch collection cache is used on second run | proven analogue | probe P-batch-cache | harness probe: batch-unit-evidence.md | 3 passed, 1 skipped on both runs; .pytest_cache exists |
| 197 | `16 Batch Collection/01 Batch collection edge cases.feature.md:48` | Batch collection flag can disable batch mode | proven analogue | probe P-batch-off | harness probe: batch-unit-evidence.md | 3 passed |
| 198 | `16 Batch Collection/01 Batch collection edge cases.feature.md:59` | Batch collection handles empty feature directory | proven analogue | probe P-batch-empty | harness probe: batch-unit-evidence.md | 3 passed, 1 skipped |
| 199 | `16 Batch Collection/01 Batch collection edge cases.feature.md:73` | Batch collection handles malformed feature file | agreed replacement/addition | decision 99, 106 | agreed | cell passed: 1905 selected, 0 failed (1810 passed in this command) |
| 200 | `16 Batch Collection/02 Edge cases with large files.feature.md:33` | Batch collection discovers multiple feature files via directory scan | proven analogue | probe P-batch-auto | harness probe: batch-unit-evidence.md | 3 passed |

### 17 Debug MCP (6)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 201 | `17 Debug MCP/01 Agentic debugging.feature.md:4` | Enabled debug MCP session publishes discovery endpoints | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |
| 202 | `17 Debug MCP/01 Agentic debugging.feature.md:10` | Failed pytest phases are held independently | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |
| 203 | `17 Debug MCP/01 Agentic debugging.feature.md:26` | Investigation artifacts are written as JSON and Markdown | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |
| 204 | `17 Debug MCP/01 Agentic debugging.feature.md:33` | Invalid investigation artifacts are rejected | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |
| 205 | `17 Debug MCP/01 Agentic debugging.feature.md:39` | BDD metadata is included in investigation artifacts | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |
| 206 | `17 Debug MCP/01 Agentic debugging.feature.md:45` | xdist root discovery references all worker sessions | proven analogue | probe P-debug-mcp-proof-head | [45279198666](https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/45279198666) / Optional integration acceptance (debug-mcp-py314-linux / py314-debug-mcp) | cell passed: 20 selected, 20 passed |

### 18 Development (13)

| Id | File:line | Declaration | Category | Decision / reason | Evidence | Result |
| ---: | --- | --- | --- | --- | --- | --- |
| 207 | `18 Development/01 Allure Converter CLI.feature.md:4` | Convert Cucumber Messages NDJSON to Allure results | proven analogue | probe P-allure-convert | harness probe: allure-converter-evidence.md | 8 files written for 3 scenarios |
| 208 | `18 Development/01 Allure Converter CLI.feature.md:34` | Handle missing NDJSON file gracefully | proven analogue | probe P-allure-missing | harness probe: allure-converter-evidence.md | cannot read input |
| 209 | `18 Development/02 Headings Validator.feature.md:4` | Heading validation passes on clean feature document | proven analogue | probe P-heading-clean | harness probe: heading-validator-evidence.md | status=pass, violations=[] |
| 210 | `18 Development/02 Headings Validator.feature.md:17` | Heading validation fails on empty feature heading | proven analogue | probe P-heading-feature | harness probe: heading-validator-evidence.md | EMPTY_HEADING_TITLE, heading_type=feature |
| 211 | `18 Development/03 Architecture Tooling.feature.md:7` | Inject responsibility template into mockup Python file | agreed exclusion | decision 121, 125 | agreed | commands: compatibility, convert, generate, messages, replay, sync, validate; no architecture command |
| 212 | `18 Development/03 Architecture Tooling.feature.md:25` | Collect architecture scores | agreed exclusion | decision 121, 125 | agreed | commands: compatibility, convert, generate, messages, replay, sync, validate; no architecture command |
| 213 | `18 Development/04 Compatibility Matrix.feature.md:7` | Check compatibility for a specific Python and pytest version pair | proven analogue | probe P-compat-pair | harness probe: compatibility-cli-evidence.md | supported (compatible) |
| 214 | `18 Development/04 Compatibility Matrix.feature.md:13` | Reject incompatible pair | proven analogue | probe P-compat-reject | harness probe: compatibility-cli-evidence.md | compatible but unsupported by the project (eol_python) |
| 215 | `18 Development/04 Compatibility Matrix.feature.md:19` | Generate tox environment names from tox.ini | proven analogue | probe P-compat-tox | harness probe: compatibility-cli-evidence.md | py311-pytest80 / py314-pytestlatest |
| 216 | `18 Development/05 Messages Contract Schema Sync.feature.md:4` | Schema check passes on identical schema set | proven analogue | probe P-schema-pass | harness probe: schema-sync-evidence.md | schemas are up to date |
| 217 | `18 Development/05 Messages Contract Schema Sync.feature.md:10` | Schema check fails when local schema has drifted | proven analogue | probe P-schema-drift | harness probe: schema-sync-evidence.md | changed: Attachment.schema.json; schema drift detected |
| 218 | `18 Development/06 Cucumber Formatter Renderer.feature.md:4` | Render cucumber summary from NDJSON messages | proven analogue | probe R-replay-summary | harness probe: installed-examples-evidence.md | 3 scenarios (1 failed, 1 skipped, 1 passed) |
| 219 | `18 Development/07 Messages Coverage Audit.feature.md:4` | Verify the shell script presence and gap documentation | agreed replacement/addition | decision 93-94 | agreed | runtime capability report with observed fields; exit 120 signals ungoverned fields |

## Appendix: nested DocString lines (not external declarations)

| Group | File | Line | Kind | Why excluded |
| --- | --- | ---: | --- | --- |
| 07 Report | `06 Allure/01 scenario.feature` | 7 | Scenario | Scenario-like text inside a Gherkin DocString; test data, not a declaration |
| 07 Report | `06 Allure/02 outline.feature` | 7 | Scenario Outline | Scenario-like text inside a Gherkin DocString; test data, not a declaration |

## Sources and method

- Classification source: Development Harness tasks/branch-audit/results/refactoring-transfer-research-2026-11-03/parity-classification-2026-11-20.json (219 rows at e063e53f).
- Reference inventory: Development Harness tasks/branch-audit/results/refactoring-transfer-research-2026-11-03/original-scenario-inventory.md.
- Per-row evidence for unchanged rows: Development Harness tasks/branch-audit/results/refactoring-transfer-research-2026-11-03/*-evidence.md unless the row names a CI run.
- Decisions: Development Harness parity-discussion.md and product #385.
- Coverage caveats: product #418 close comments name claims no proof-run job exercises.

Re-check:

```console
# resolve the revision
PATH="$PWD/scripts/wsl-bin:$PATH" rtk git ls-remote origin parity/cycle-2-proof
# build the wheel
git worktree add /tmp/opencode/proof-wheel 8ea8a5fd
cd /tmp/opencode/proof-wheel
PYTEST_CUKE_BUILD_GO=off uv build --wheel --out-dir /tmp/opencode/proof-wheel-dist
sha256sum /tmp/opencode/proof-wheel-dist/pytest_cuke-2.3.1-py3-none-any.whl
# receive the proof evidence
PATH="$PWD/scripts/wsl-bin:$PATH" rtk gh run download 45279198666 \
  --repo elchupanebrej/pytest-bdd-ng -D artifacts/45279198666
```
