# Test Responsibility Template — Field Guide

This guide explains every field of the **Test Responsibility Template** that is injected into
each test function docstring. The template is machine-parsed and also reviewed by humans, so
every field must be filled accurately.

> **Who fills it?** This template is filled by agents (via `scripts/fill_test_docstrings.py`)
> or by junior developers writing new tests. All placeholders in `<angle-brackets>` must be
> replaced. Default scores must be reviewed and adjusted.

---

## Template (reference)

```text
Test target:
    <test_target>
Test type:
    <test_type>
Test scenario:
    <scenario_description>
BDD reference:
    <bdd_reference_or_none>
Fixtures:
    - None
Mocks:
    - None
Side effects:
    None
Reduction:
    <reduction_reason>
Escalation:
    <escalation_reason>
Atomicity:
    <atomicity_reason>
Autonomy:
    <autonomy_reason>
Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
```

---

## Field Definitions

---

### `Test target`

**What it is:** The specific *behavior, contract, invariant, or property* this test exists to
protect. Not a file path, not a class name — the *reason the test was written*.

Ask yourself: *"If this test fails, what has broken in the system?"* The answer to that
question is the test target.

**Do:** Write a sentence fragment naming the behavior. Start with the component, then
describe the invariant or rule it must uphold.

**Do not:** Write a module path, a class name, or a function signature. Those belong in
`Test scenario`, not here.

**✅ Good examples:**
```text
Test target:
    ScenarioRun raises RuntimeError when step outcome is UNDEFINED and strict mode is on
```
```text
Test target:
    GherkinParser preserves original line numbers in parsed steps
```
```text
Test target:
    scenarios() collects all scenario items from a feature file with parametrized examples
```

**❌ Bad examples:**
```text
Test target:
    pytest_bdd.parser          # module path — not a behavior
```
```text
Test target:
    GherkinParser              # class name — not a behavior
```
```text
Test target:
    test behavior of the parser  # too vague, adds no information
```

---

### `Test type`

**What it is:** The architectural level of this test. Choose exactly one of the following
values:

| Value | When to use |
|---|---|
| `Unit` | Tests a single function/class in isolation; all dependencies are mocked or replaced |
| `Integration` | Tests the interaction between two or more real components (no mocks for the boundary being tested) |
| `E2E` | Tests a full user-visible flow from entry point to output (subprocess, CLI, HTTP) |
| `Contract` | Verifies a stable public interface (API surface, Makefile targets, config keys) that external consumers depend on |
| `Compat` | Verifies behavior across Python versions, pytest versions, or other matrix axes |

**Do:** Write exactly the value from the table above, nothing else.

**Do not:** Add the word "test", write free-form descriptions, or invent new categories.

**✅ Good examples:**
```text
Test type:
    Unit
```
```text
Test type:
    Integration
```

**❌ Bad examples:**
```text
Test type:
    Unit test          # do not add the word "test"
```
```text
Test type:
    functional         # not a recognized value; use Integration or E2E
```

---

### `Test scenario`

**What it is:** A plain-English, one-to-two sentence description of the exact setup and
assertion this test performs. Must be specific enough that a developer can understand what
is being verified without reading the test body.

**Do:** Use the structure *"Given [preconditions], when [action], then [expected outcome]."*
Be specific about the values, conditions, and expected results.

**Do not:** Write generic sentences like "verifies correct behavior" or repeat the function
name as a sentence.

**✅ Good examples:**
```text
Test scenario:
    Given a feature file with a scenario that has an undefined step, when the test is
    collected in strict mode, then the test item raises PytestBDDException on setup.
```
```text
Test scenario:
    Given a Registry with two overlapping step definitions, when a step is matched,
    then the first registered definition wins and no AmbiguousStepError is raised.
```

**❌ Bad examples:**
```text
Test scenario:
    Verifies correct behavior.                           # too vague
```
```text
Test scenario:
    Verifies correct behavior and edge cases of pytest_bdd.parser.GherkinParser.  # auto-fill garbage
```

---

### `BDD reference`

**What it is:** The relative path and scenario title of a `.feature.md` scenario that this
test implements or is directly covered by. Write `None` if no BDD scenario exists for this test.

**Do:** Use the format `path/to/file.feature.md :: Scenario title`.

**Do not:** Point to a directory, write a partial path, or write `N/A`.

**✅ Good examples:**
```text
BDD reference:
    features/02 Feature/scenario-matching.feature.md :: Step is ambiguous
```
```text
BDD reference:
    None
```

**❌ Bad examples:**
```text
BDD reference:
    features/              # directory, not a scenario
```
```text
BDD reference:
    N/A                    # use None
```

---

### `Fixtures`

**What it is:** A list of every pytest fixture this test function receives — whether declared
in its signature, inherited from `conftest.py`, or used via `autouse`. For each fixture,
write its name followed by a colon and a one-line description of what it provides.

**Do:** List each fixture on its own line with `- name: description`. Write `- None` if the
test uses no fixtures.

**Do not:** Comma-separate multiple fixtures on one line, or list fixtures the test does not
actually use.

**✅ Good examples:**
```text
Fixtures:
    - testdir: Provides an isolated temporary pytest project directory
    - registry: A pre-populated step Registry with three step definitions
```
```text
Fixtures:
    - None
```

**❌ Bad examples:**
```text
Fixtures:
    - testdir, registry    # list each on its own line
```
```text
Fixtures:
    - pytest fixtures      # not a fixture name
```

---

### `Mocks`

**What it is:** A list of every object, function, or attribute that is replaced by a fake
during this test (via `unittest.mock`, `monkeypatch`, `pytest-mock`, or manual patching).
For each mock, write what is replaced and what behavior the mock provides or suppresses.

**Do:** Write `- target: what it does`. Write `- None` if nothing is mocked.

**Do not:** Name the mock module; name the thing being mocked.

**✅ Good examples:**
```text
Mocks:
    - subprocess.run: returns exit code 0 to simulate successful gherkin compilation
    - builtins.open: raises PermissionError to test the error handling path
```
```text
Mocks:
    - None
```

**❌ Bad examples:**
```text
Mocks:
    - subprocess    # too vague; name the function, not the module
```
```text
Mocks:
    - mock objects  # meaningless
```

---

### `Side effects`

**What it is:** Any observable effect this test produces outside its assertions — file
writes, environment variable mutations, network calls, stdout output, subprocess spawning,
database mutations, etc.

**Do:** Describe what is created, mutated, or called and whether it is cleaned up. Write
`None` only if the test is truly side-effect-free (pure in-memory computation, no I/O).

**Do not:** Write `None` when the test actually spawns a subprocess or writes to disk.

**✅ Good examples:**
```text
Side effects:
    Creates a temporary .feature.md file under tmp_path; removed by pytest after the test.
```
```text
Side effects:
    Writes NDJSON to stdout via a subprocess; subprocess is isolated via testdir fixture.
```
```text
Side effects:
    None
```

**❌ Bad examples:**
```text
Side effects:
    None    # written when the test actually spawns a subprocess
```

---

### `Reduction`

**What it is:** The reason this test **cannot be moved to a lower architectural level**
(e.g., why it cannot be a unit test if it is currently an integration test).

**Do:** Name the specific dependency or behavior that makes lower-level testing impossible
or meaningless. Say what would be *lost* or *broken* by moving down a level.

**Do not:** Write a generic sentence about "requiring pytest" or "needing real execution".
That is true of almost every test and explains nothing.

**✅ Good examples:**
```text
Reduction:
    Cannot be unit — the behavior under test is the interaction between the pytest
    collection hook and the file system; mocking either would eliminate the invariant.
```
```text
Reduction:
    Cannot be unit — requires a real subprocess to verify stdout formatting produced
    by the Cucumber pretty formatter binary.
```

**❌ Bad examples:**
```text
Reduction:
    Requires pytest execution and AST parsing to validate behavior.   # generic, explains nothing
```
```text
Reduction:
    It cannot be lower.    # explains nothing
```

---

### `Escalation`

**What it is:** The reason this test **cannot be moved to a higher architectural level**
(e.g., why it cannot be an E2E test if it is currently an integration test).

**Do:** Name what would be *overcomplicated, impossible to trigger, or redundant* at a
higher level. Be specific about why the current level is the right one.

**Do not:** Write generic sentences about "redundancy" or "speed".

**✅ Good examples:**
```text
Escalation:
    Cannot be E2E — the error condition requires injecting a mid-run exception that
    cannot be triggered through the public CLI surface.
```
```text
Escalation:
    Cannot be integration — the assertion is purely on the return value of a pure
    function; no real dependency interaction is needed or useful.
```

**❌ Bad examples:**
```text
Escalation:
    Testing at a higher level would be redundant and slow down execution.  # generic
```

---

### `Atomicity`

**What it is:** The reason this test **cannot be split into two or more smaller tests**.

**Do:** If the test has multiple assertions, explain why they *must* stay together (shared
expensive setup, sequential state, mutually dependent invariants). If the test has a single
assertion, write "Single assertion — already atomic."

**Do not:** Write that assertions are "related" without explaining *why* splitting would hurt.

**✅ Good examples:**
```text
Atomicity:
    All assertions verify properties of the same parsed GherkinDocument; re-parsing
    for each assertion would be expensive and would not improve fault isolation.
```
```text
Atomicity:
    Single assertion — already atomic.
```

**❌ Bad examples:**
```text
Atomicity:
    Verifies closely related features that share the same setup state.  # generic auto-fill
```

---

### `Autonomy`

**What it is:** The reason this test **cannot be merged with another existing test**.

**Do:** Name the specific behavior or edge case that is *unique to this test* and is not
covered by any sibling test. If a sibling covers the happy path, explain that this one
covers a specific error path, boundary condition, or configuration variant.

**Do not:** Write that merging "would make debugging harder" without specifying what distinct
case this test owns.

**✅ Good examples:**
```text
Autonomy:
    Covers the strict-mode-off code path; the sibling test_strict_mode_on covers the
    opposite branch. Merging would create a conditional inside the test body, hiding
    which scenario caused a failure.
```
```text
Autonomy:
    Only test that exercises the PermissionError branch in the file writer; no other
    test reaches this exception path.
```

**❌ Bad examples:**
```text
Autonomy:
    Merging would create complex dependencies and make debugging harder.  # generic auto-fill
```
```text
Autonomy:
    This test is unique.    # states the obvious without explaining why
```

---

## Test quality scores

Four machine-readable scores appended to every test function docstring. Each score is an
integer from **1 to 5**. Default values in the template must be reviewed and corrected for
every test — do not leave defaults unchanged without verifying they are accurate.

```text
#test-eval:isolation=5
#test-eval:determinism=5
#test-eval:setup_complexity=1
#test-eval:assertions_clarity=5
```

---

### `isolation` — How isolated is the test from external state?

| Score | Meaning |
|---|---|
| **5** | Fully isolated — pure in-memory, no I/O, no global state, no subprocesses |
| **4** | Mostly isolated — uses `tmp_path` or an in-process fake for I/O |
| **3** | Uses real filesystem or real in-process DB |
| **2** | Shares mutable global state with other tests (e.g., module-level singletons) |
| **1** | Depends on external services, CI environment variables, or test execution order |

---

### `determinism` — Does the test produce the same result on every run?

| Score | Meaning |
|---|---|
| **5** | Fully deterministic — same result every run on any machine |
| **4** | Deterministic except for timing-sensitive assertions (e.g., `time.sleep`) |
| **3** | Occasionally flaky under high load or on slow machines |
| **2** | Flaky — fails intermittently without code changes |
| **1** | Unreliable — regularly produces false positives or negatives |

---

### `setup_complexity` — How much setup does the test require?

| Score | Meaning |
|---|---|
| **1** | No setup — test body is self-contained, no fixtures |
| **2** | One or two simple fixtures |
| **3** | Multiple fixtures or non-trivial data preparation |
| **4** | Complex multi-step setup or deeply nested fixture chains |
| **5** | Very complex — requires subprocess, Docker, or multi-fixture orchestration |

> ⚠️ **Note:** Lower `setup_complexity` is better. A score of 4–5 is a warning sign that
> the test may need to be redesigned or split.

---

### `assertions_clarity` — How informative are failures when the test breaks?

| Score | Meaning |
|---|---|
| **5** | Every assertion has a descriptive `msg=` parameter or is fully self-explanatory |
| **4** | Assertions are clear without explicit messages (values speak for themselves) |
| **3** | Some assertions require reading the test body to understand what failed |
| **2** | Raw `assert` with no message; failure output gives minimal context |
| **1** | Assertions are opaque — failure message gives no hint of what behavior broke |
