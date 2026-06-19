# Phase 24: Allure-Cucumber Converter - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 21 new/modified files
**Analogs found:** 19 / 21

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/pytest_bdd/plugin/allure_cucumber/__init__.py` | plugin (init) | package-init | `src/pytest_bdd/plugin/cucumber_json/__init__.py` | exact |
| `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` | middleware | request-response | `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/plugin.py` | component | request-response | `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/hook.py` | middleware | event-driven | `src/pytest_bdd/plugin/cucumber_json/hook.py` | exact |
| `src/pytest_bdd/plugin/allure_cucumber/cli.py` | utility | file-I/O | `src/pytest_bdd/script/render_cucumber_formatters.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py` | component | package-init | `src/pytest_bdd/plugin/cucumber_json/__init__.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/converter/reader.py` | service | file-I/O | `src/pytest_bdd/model/execution_message_adapter.py` | dataflow-match |
| `src/pytest_bdd/plugin/allure_cucumber/converter/collector.py` | service | event-driven | `tests/cases/contract/messages/test_messages_feature_suite.py` (collector logic) | partial |
| `src/pytest_bdd/plugin/allure_cucumber/converter/step_tree.py` | service | transform | None (algorithmic — no direct analog) | none |
| `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py` | service | transform | `tests/cases/contract/contract/test_formatter_golden_parity.py` (mapping patterns) | partial |
| `src/pytest_bdd/plugin/allure_cucumber/converter/emitter.py` | service | file-I/O | `src/pytest_bdd/plugin/cucumber_json/plugin.py` (pytest_sessionfinish) | dataflow-match |
| `src/pytest_bdd/plugin/allure_cucumber/converter/model.py` | model | data | `src/pytest_bdd/model/execution_message_adapter.py` (attrs frozen pattern) | role-match |
| `pyproject.toml` (console_scripts) | config | config | `pyproject.toml` lines 170-172 | exact |
| `pyproject.toml` (pytest11 entry point) | config | config | `pyproject.toml` lines 91-110 | exact |
| `pyproject.toml` (test deps) | config | config | `pyproject.toml` lines 136-150 | exact |
| `tests/cases/contract/contract/test_plugin_structure_contract.py` | test | contract | self (line 15: EXPECTED_PLUGIN_COUNT = 18) | exact |
| `tests/cases/unit/allure/` (test files) | test | unit | `tests/cases/unit/unit/test_plugin_patterns.py` | role-match |
| `tests/cases/contract/allure/` (test files) | test | contract | `tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py` | role-match |
| `tests/cases/integration/allure/` (test files) | test | integration | `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py` | role-match |
| `tests/cases/contract/allure/conftest.py` | test (fixtures) | config | `tests/cases/contract/messages_coverage/conftest.py` | role-match |
| `docs/allure3-events.schema.json` | config | file-I/O | None (greenfield schema artifact) | none |

## Pattern Assignments

### `src/pytest_bdd/plugin/allure_cucumber/__init__.py` (plugin, package-init)

**Analog:** `src/pytest_bdd/plugin/cucumber_json/__init__.py`

**Core pattern** (line 1):
```python
"""Provide src.pytest_bdd.plugin.cucumber_json package helpers."""
```

**Apply to allure_cucumber:**
```python
"""Provide src.pytest_bdd.plugin.allure_cucumber package helpers."""
```

---

### `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` (middleware, request-response)

**Analog:** `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`

**Imports pattern** (lines 1-15):
```python
"""Provide entrypoint helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, cast

import pytest
from attrs import frozen

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager, Stash
from pytest_bdd.model.stash_access import StashBound
```

**Stash-bound state pattern** (lines 48-52, 154-169):
```python
@frozen
class _ReporterStateEntry(StashBound):
    STASH_KEY: ClassVar[str] = _REPORTER_STATE_ATTR
    reporter: object

def _store_reporter_state(config: Config, reporter: object) -> None:
    _ReporterStateEntry(reporter=reporter).set_in_stash(_config_stash(config))

def _resolve_reporter_state(config: Config) -> object | None:
    state = _ReporterStateEntry.find_in_stash(_config_stash(config)).value_or(None)
    return None if state is None else state.reporter

def _clear_reporter_state(config: Config) -> None:
    stash = getattr(config, "stash", None)
    if stash is None:
        return
    with suppress(KeyError, AttributeError):
        del stash[_ReporterStateEntry.STASH_KEY]
```

**pytest_configure pattern** (lines 252-274):
```python
@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """Handle configure."""
    reporter = None
    try:
        reporter = AllureCucumberPlugin(config=config)
    except ConfigurationError as exc:
        raise pytest.UsageError(str(exc)) from exc
    try:
        _store_reporter_state(config, reporter)
        _configure_reporter_instance(reporter, config.pluginmanager)
    except Exception:
        logger.warning("Plugin configuration failed", exc_info=True)
        if reporter is not None:
            _unconfigure_reporter_instance(reporter, config.pluginmanager)
        _clear_reporter_state(config)
        raise

@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    """Handle unconfigure."""
    reporter = _resolve_reporter_state(config)
    if reporter is not None:
        _unconfigure_reporter_instance(reporter, config.pluginmanager)
    _clear_reporter_state(config)
```

**pytest_addoption pattern** (lines 221-249):
```python
def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Allure Cucumber")
    group.addoption(
        "--allure-cucumber-output",
        action="store",
        dest="allure_cucumber_output_dir",
        metavar="PATH",
        default=None,
        help="Output directory for Allure result JSON files.",
    )
```

**Hook spec registration** (lines 195-197):
```python
def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    pluginmanager.add_hookspecs(AllureCucumberHookSpec)
```

---

### `src/pytest_bdd/plugin/allure_cucumber/plugin.py` (component, request-response)

**Analog 1:** `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` — StashBound attrs-style plugin (lines 61-116)

**Imports pattern** (lines 1-50):
```python
"""Provide plugin helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from attrs import define, field

from pytest_bdd.model.stash_access import StashBound  # if using StashBound

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
```

**attrs plugin class pattern** (lines 61-116; truncated for relevance):
```python
@define(eq=False, auto_attribs=False, slots=False)
class AllureCucumberPlugin:
    """Represent allure cucumber plugin state."""

    config: Config = field()
    output_dir: str = "allure-results"
    # ...
    plugin_name: str = "pytest-bdd-allure-cucumber"

    def __attrs_post_init__(self) -> None:
        """Initialize plugin runtime."""
        # initialize services
        pass

    def pytest_sessionfinish(self, session) -> None:
        """Handle sessionfinish — call converter."""
        pass
```

**Analog 2:** `src/pytest_bdd/plugin/cucumber_json/plugin.py` — Simple plugin class pattern (lines 15-22, 128-136)

**Simple plugin init** (lines 18-21):
```python
class LogBDDCucumberJSON:
    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str) -> None:
        self.logfile = Path(os.path.expandvars(logfile)).expanduser().resolve()
```

**pytest_sessionfinish file write** (lines 132-136):
```python
def pytest_sessionfinish(self) -> None:
    for feature in self.features.values():
        Feature.model_validate(feature)
    Path(self.logfile).write_text(json.dumps(list(self.features.values())), encoding="utf-8")
```

**pytest_terminal_summary** (lines 138-140):
```python
def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
    terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
```

---

### `src/pytest_bdd/plugin/allure_cucumber/hook.py` (middleware, event-driven)

**Analog:** `src/pytest_bdd/plugin/cucumber_json/hook.py` (canonical placeholder)

**Core pattern** (entire file, 6 lines):
```python
"""
Hook specifications for the cucumber json plugin.

This module is a canonical package-structure placeholder so source contracts can
require every pytest11 plugin package to provide an explicit hook surface.
"""
```

**Apply:**
```python
"""
Hook specifications for the allure cucumber converter plugin.

This module is a canonical package-structure placeholder so source contracts can
require every pytest11 plugin package to provide an explicit hook surface.
"""
```

**Note:** If the allure converter plugin needs custom hooks (e.g., `pytest_bdd_allure_result`), follow the gherkin_message_reporter pattern from `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` (lines 16-41):
```python
class AllureCucumberHookSpec:
    """Declare hooks used by the allure cucumber plugin."""

    @pytest.hookspec
    def pytest_bdd_allure_result(self, config: Config, result_path: Path) -> None:
        """Emitted after each allure result file is written."""

    @pytest.hookspec
    def pytest_bdd_allure_container(self, config: Config, container_path: Path) -> None:
        """Emitted after each allure container file is written."""
```

---

### `src/pytest_bdd/plugin/allure_cucumber/cli.py` (utility, file-I/O)

**Analog:** `src/pytest_bdd/script/render_cucumber_formatters.py`

**Imports pattern** (lines 1-15):
```python
"""CLI entry point for allure-cucumber converter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert
```

**Argument parsing pattern** (lines 71-97):
```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Cucumber Messages NDJSON to Allure3 JSON results"
    )
    parser.add_argument(
        "messages_ndjson",
        type=Path,
        help="Path to Cucumber Messages NDJSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("allure-results"),
        help="Output directory for Allure result JSON files.",
    )
    return parser.parse_args(argv)
```

**main() pattern with error handling** (lines 125-164):
```python
def main(argv: list[str] | None = None) -> int:
    """Run the allure-cucumber converter."""
    args = parse_args(argv)
    messages_path = args.messages_ndjson
    if not messages_path.is_absolute():
        messages_path = Path.cwd().resolve() / messages_path
    if not messages_path.exists():
        _emit_error(f"Messages NDJSON file was not found: {messages_path}")
        return 1

    try:
        convert(messages_path, args.output)
    except (OSError, ValueError) as exc:
        _emit_error(f"Conversion failed: {exc}")
        return 1

    return 0


def _emit_error(message: str) -> None:
    """Emit error message to stderr."""
    sys.stderr.write(message)
    sys.stderr.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/reader.py` (service, file-I/O)

**Analog:** `src/pytest_bdd/model/execution_message_adapter.py`

**Imports pattern** (lines 1-14):
```python
"""NDJSON reader: stream Cucumber Messages NDJSON into ExecutionProjection objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter, ExecutionProjection
```

**Stream-reading pattern** (derived from RESEARCH.md lines 226-237 and adapter line 200-214):
```python
def read_envelopes(messages_path: Path) -> Iterator[ExecutionProjection]:
    """Read NDJSON file and yield typed ExecutionProjection for each line."""
    with open(messages_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            envelope_dict = json.loads(line)
            yield ExecutionMessageAdapter.deserialize_dict(envelope_dict)
```

**deserialize_dict signature** (lines 200-214 of adapter):
```python
@classmethod
def deserialize_dict(
    cls,
    payload: JSONObject,
    *,
    registry: EnvelopeRegistry | IdentifiableObjectRegistry | None = None,
) -> ExecutionProjection:
    """Instantiate an EventEnvelope from a dictionary and immediately extract its projection state."""
    return cls.deserialize(envelope_from_dict(payload), registry=registry)
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/model.py` (model, data)

**Analog 1:** `src/pytest_bdd/model/execution_message_adapter.py` — attrs frozen pattern (lines 32-66)

**ExecutionProjection attrs pattern** (lines 32-66):
```python
@frozen
class ExecutionProjection:
    """Wrap an event envelope with payload kind, payload, and registry access."""

    envelope: EventEnvelope
    payload_kind: PayloadKind
    payload: object
    registry: IdentifiableObjectRegistry | None = None

    @property
    def payload_id(self) -> str | None:
        raw_id = getattr(self.payload, "id", None)
        if raw_id is None:
            return Nothing.value_or(None)
        return str(raw_id)
```

**Analog 2:** `src/pytest_bdd/model/stash_access.py` — StashBound pattern (lines 117-189)

**Apply to Allure model types:**
```python
from __future__ import annotations

from attrs import define, field
from returns.maybe import Maybe, Nothing
from typing import ClassVar
from uuid import UUID, uuid4

@define
class AllureTestResult:
    """Represent an Allure3 test result."""

    uuid: str = field(factory=lambda: str(uuid4()))
    name: str = ""
    full_name: str = ""
    status: str = "unknown"
    status_details: AllureStatusDetails | None = None
    labels: list[AllureLabel] = field(factory=list)
    links: list[AllureLink] = field(factory=list)
    steps: list[AllureStepResult] = field(factory=list)
    attachments: list[AllureAttachment] = field(factory=list)
    start: int = 0
    stop: int = 0
    stage: str = "finished"


@define
class AllureStepResult:
    """Represent an Allure3 step result."""
    name: str
    status: str
    start: int = 0
    stop: int = 0
    steps: list[AllureStepResult] = field(factory=list)
    attachments: list[AllureAttachment] = field(factory=list)
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/collector.py` (service, event-driven)

**Analog:** Research-informed pattern for grouping by testCaseStartedId (no single existing analog)

**Pattern from RESEARCH.md lines 129-137:**
```python
"""Group cucumber message envelopes by test case for scenario mapping."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterator

from pytest_bdd.model.execution_message_adapter import ExecutionProjection


def group_by_test_case(
    projections: Iterator[ExecutionProjection],
) -> dict[str, list[ExecutionProjection]]:
    """
    Group envelope projections by testCaseStartedId.

    Each TestCaseStarted/TestStepStarted/Attachment event references
    a testCaseStartedId. Group them under that ID for per-scenario processing.
    """
    by_case: dict[str, list[ExecutionProjection]] = defaultdict(list)
    for projection in projections:
        case_id = _extract_test_case_id(projection)
        if case_id is not None:
            by_case[case_id].append(projection)
    return dict(by_case)


def _extract_test_case_id(projection: ExecutionProjection) -> str | None:
    """Get testCaseStartedId from projection payload."""
    raw = getattr(projection.payload, "test_case_started_id", None)
    if raw is None:
        raw = getattr(projection.payload, "testCaseStartedId", None)
    return str(raw) if raw is not None else None
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/step_tree.py` (service, transform)

**No direct analog.** Algorithmic — stack-based reconstruction per RESEARCH.md lines 326-335.

**Pattern from RESEARCH.md:**
```python
"""Reconstruct hierarchical step tree from flat TestStepStarted/Finished pairs."""

from __future__ import annotations

from pytest_bdd.model.execution_message_adapter import ExecutionProjection


def build_step_tree(
    projections: list[ExecutionProjection],
) -> list[dict[str, object]]:
    """
    Build a nested step hierarchy from flat cucumber message events.

    Uses a stack-based approach:
    1. TestStepStarted → push step onto current branch's stack
    2. TestStepFinished → pop from stack, attach to parent
    3. Track testStepId → parent via pickle_step_id references
    """
    stack: list[dict[str, object]] = []
    root_steps: list[dict[str, object]] = []
    # Implementation per RESEARCH.md section "Common Pitfalls #1"
    return root_steps
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py` (service, transform)

**Analog:** Partial — follows data transformation pattern from test files

**Apply pattern (from RESEARCH.md lines 146-152):**
```python
"""Map Cucumber Messages events to Allure3 result objects."""

from __future__ import annotations

from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from .model import AllureTestResult, AllureStepResult, AllureAttachment


def map_test_case_to_result(
    case_id: str,
    projections: list[ExecutionProjection],
) -> AllureTestResult:
    """
    Map a test case's cucumber message projections to an Allure TestResult.

    Mapping table:
    - TestCaseStarted → AllureTestResult (name, labels, start time)
    - TestStepStarted/Finished → AllureStepResult (nested)
    - Attachment → AllureAttachment
    - Unmappable events → structured attachments (never dropped)
    """
    # ...


def map_unmappable_to_attachment(
    projection: ExecutionProjection,
) -> AllureAttachment:
    """Encode unmappable events as structured metadata attachments."""
    # ...
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/emitter.py` (service, file-I/O)

**Analog:** `src/pytest_bdd/plugin/cucumber_json/plugin.py` — file write at sessionfinish (lines 132-140)

**File write pattern** (lines 132-136):
```python
def pytest_sessionfinish(self) -> None:
    for feature in self.features.values():
        Feature.model_validate(feature)
    Path(self.logfile).write_text(json.dumps(list(self.features.values())), encoding="utf-8")
```

**Apply to allure emitter:**
```python
"""Emit Allure model objects as JSON files on disk."""

from __future__ import annotations

import json
from pathlib import Path

from .model import AllureTestResult


def emit_results(
    results: list[AllureTestResult],
    output_dir: Path,
) -> None:
    """Serialize AllureTestResults to JSON files in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        file_name = f"{result.uuid}-result.json"
        file_path = output_dir / file_name
        file_path.write_text(
            json.dumps(attrs.asdict(result), indent=2),
            encoding="utf-8",
        )
```

---

### `src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py` (component, package-init)

**Analog:** `src/pytest_bdd/plugin/cucumber_json/__init__.py`

**Apply pattern:**
```python
"""Allure-Cucumber converter: NDJSON to Allure3 JSON mapping."""

from __future__ import annotations

from pathlib import Path

from .reader import read_envelopes
from .collector import group_by_test_case
from .step_tree import build_step_tree
from .mapper import map_test_case_to_result
from .emitter import emit_results


def convert(messages_path: Path, output_dir: Path) -> None:
    """
    Convert Cucumber Messages NDJSON to Allure3 JSON result files.

    Called by CLI, pytest plugin, or standalone scripts.
    """
    projections = list(read_envelopes(messages_path))
    grouped = group_by_test_case(projections)

    results = []
    for case_id, case_projections in grouped.items():
        result = map_test_case_to_result(case_id, case_projections)
        results.append(result)

    emit_results(results, output_dir)
```

---

### `pyproject.toml` — console_scripts entry point (config, config)

**Analog:** `pyproject.toml` lines 170-172

**Existing pattern:**
```toml
[project.scripts]
compatibility_matrix = "pytest_bdd.script.compatibility_matrix:main"
render_cucumber_formatters = "pytest_bdd.script.render_cucumber_formatters:main"
```

**Applied addition:**
```toml
[project.scripts]
compatibility_matrix = "pytest_bdd.script.compatibility_matrix:main"
render_cucumber_formatters = "pytest_bdd.script.render_cucumber_formatters:main"
allure-cucumber = "pytest_bdd.plugin.allure_cucumber.cli:main"
```

---

### `pyproject.toml` — pytest11 entry point (config, config)

**Analog:** `pyproject.toml` lines 91-110

**Existing pattern:**
```toml
[project.entry-points.pytest11]
"pytest-bdd-code-generator" = "pytest_bdd.plugin.code_generator.entrypoint"
"pytest-bdd-cucumber-formatter-json" = "pytest_bdd.plugin.cucumber_json_formatter.entrypoint:json_plugin"
# ... (18 entries total)
```

**Applied addition (insert alphabetically after line 103):**
```toml
"pytest-bdd-allure-cucumber" = "pytest_bdd.plugin.allure_cucumber.entrypoint"
```

---

### `pyproject.toml` — test dependencies (config, config)

**Analog:** `pyproject.toml` lines 136-150

**Existing test extra pattern:**
```toml
test = [
  "deepdiff",
  "execnet>=2.1.2",
  "GitPython",
  # ... existing deps ...
  "pytest-bdd-ng[doc-gen];python_version>='3.13.0'"
]
```

**Applied addition (append factoryboy and hypothesis to `test` extra):**
```toml
test = [
  # ... existing deps ...
  "factory-boy",
  "hypothesis",
  "pytest-bdd-ng[doc-gen];python_version>='3.13.0'"
]
```

---

### `tests/cases/contract/contract/test_plugin_structure_contract.py` — EXPECTED_PLUGIN_COUNT (test, contract)

**Analog:** Self — line 15

**Existing (line 15):**
```python
EXPECTED_PLUGIN_COUNT = 18
```

**Apply change:**
```python
EXPECTED_PLUGIN_COUNT = 19
```

---

### `tests/cases/unit/allure/` (test, unit)

**Analog:** `tests/cases/unit/unit/` directory structure

**Test file structure pattern** (from `test_plugin_patterns.py` lines 1-21):
```python
"""Unit tests for allure-cucumber converter internals."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes
from pytest_bdd.plugin.allure_cucumber.converter.collector import group_by_test_case
# ... imports ...

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


class TestReader:
    def test_parses_single_envelope(self, tmp_path: Path) -> None:
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text(
            '{"testCaseStarted":{"id":"case-1","testCaseId":"tc-1","attempt":0}}\n',
            encoding="utf-8",
        )
        projections = list(read_envelopes(ndjson))
        assert len(projections) == 1
        assert projections[0].payload_kind == "testCaseStarted"

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text(
            '\n\n{"testRunStarted":{}}\n\n',
            encoding="utf-8",
        )
        projections = list(read_envelopes(ndjson))
        assert len(projections) == 1
```

**Named test directories:**
```
tests/cases/unit/allure/
├── conftest.py
├── test_reader.py
├── test_collector.py
├── test_step_tree.py
├── test_mapper.py
├── test_emitter.py
└── test_model.py
```

---

### `tests/cases/contract/allure/` (test, contract)

**Analog:** `tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py`

**Contract test pattern** (lines 1-22):
```python
"""Contract tests for allure-cucumber converter."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_bdd.compatibility.tomllib import loads
from pytest_bdd.plugin.allure_cucumber import entrypoint as allure_entrypoint
```

**Contract test body patterns:**
- Assert CLI registrations exists in pyproject.toml
- Assert plugin structure (entrypoint.py, plugin.py, hook.py)
- Assert converter output validates against `docs/allure3-events.schema.json`
- Assert golden file parity for known NDJSON inputs
- Use `SimpleNamespace` for mock configs
- Use `monkeypatch` for overrides
- Use `pytest.raises` for error path testing

**Named test directories:**
```
tests/cases/contract/allure/
├── conftest.py
├── test_plugin_structure.py          # REQ-06 (structural check beyond base contract)
├── test_schema_validation.py         # REQ-05 (jsonschema validation)
├── test_cli_contract.py              # REQ-07 (CLI entry point)
├── test_converter_contract.py        # REQ-02, REQ-04 (mapping contracts)
├── test_golden_parity.py             # Golden file comparison tests
└── test_hypothesis.py                # REQ-09 (property-based)
```

---

### `tests/cases/integration/allure/` (test, integration)

**Analog:** `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py`

**Integration test pattern:**
```python
"""Integration tests for allure-cucumber plugin lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_plugin_calls_converter_at_sessionfinish(testdir, tmp_path: Path) -> None:
    """Verify plugin invokes converter when session finishes."""
    testdir.makeconftest("""
        import pytest
        from pathlib import Path
    """)
    testdir.makefile(
        ".feature",
        """
        Feature: Allure Integration
          Scenario: Simple pass
            Given this passes
        """,
    )
    # Run with allure-cucumber output option
    result = testdir.runpytest_subprocess(
        "--allure-cucumber-output", str(tmp_path / "allure-results"),
    )
    result.assert_outcomes(passed=1)
    # Verify output files exist
    assert (tmp_path / "allure-results").exists()
```

**Named test directories:**
```
tests/cases/integration/allure/
├── conftest.py
├── test_plugin.py                   # REQ-08 (pytest_sessionfinish hook)
└── test_cli_integration.py          # CLI end-to-end with real NDJSON
```

---

### `tests/cases/contract/allure/conftest.py` (test, config/fixtures)

**Analog:** `tests/cases/contract/messages_coverage/conftest.py`

**Fixtures pattern** (lines 1-30):
```python
"""Shared fixtures for allure-cucumber contract tests."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

collect_ignore_glob = ["fixtures/*.feature", "fixtures/*.py"]


@pytest.fixture
def sample_ndjson(tmp_path: Path) -> Path:
    """Create a minimal valid Cucumber Messages NDJSON file."""
    ndjson = tmp_path / "messages.ndjson"
    ndjson.write_text(
        json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}) + "\n"
        + json.dumps({"testCaseStarted": {"id": "case-1", "testCaseId": "tc-1", "attempt": 0}}) + "\n"
        + json.dumps({"testStepStarted": {"testStepId": "step-1", "testCaseStartedId": "case-1", "timestamp": {}}}) + "\n"
        + json.dumps({"testStepFinished": {"testStepId": "step-1", "testCaseStartedId": "case-1", "timestamp": {}}}) + "\n"
        + json.dumps({"testCaseFinished": {"testCaseStartedId": "case-1", "timestamp": {}}}) + "\n"
        + json.dumps({"testRunFinished": {"success": True, "timestamp": {}}}) + "\n",
        encoding="utf-8",
    )
    return ndjson


@pytest.fixture
def allure_schema_path() -> Path:
    """Path to committed Allure3 events JSON Schema."""
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "docs" / "allure3-events.schema.json"
```

---

## Shared Patterns

### Canonical 3-File Plugin Structure
**Source:** `tests/cases/contract/contract/test_plugin_structure_contract.py` (lines 35-75)
**Apply to:** `allure_cucumber/` plugin directory

Every pytest11 plugin MUST have:
- `entrypoint.py` — module-level plugin instance, `pytest_addoption`, `pytest_configure`, `pytest_unconfigure`
- `plugin.py` — plugin class (name ending in `Plugin`)
- `hook.py` — canonical placeholder docstring (or HookSpec class if hooks needed)

**Plugin class naming:** Must end with `Plugin` suffix to pass contract test (line 67):
```python
has_canonical_class = any(class_name.endswith("Plugin") for class_name in class_names)
```

---

### pytest11 Entry Point Registration
**Source:** `pyproject.toml` lines 91-110
**Apply to:** entry in `[project.entry-points.pytest11]`

**Pattern:** `"plugin-name" = "pytest_bdd.plugin.plugin_dir.entrypoint"`
- Entry points that reference a module (not a specific object) use bare module path
- Entry points that reference a module-level instance use `:instance_name` suffix
- Alphabetical ordering within the section

---

### StashBound for Plugin Configuration
**Source:** `src/pytest_bdd/model/stash_access.py` (lines 117-189)
**Apply to:** Plugin configuration storage

```python
from attrs import define
from pytest_bdd.model.stash_access import StashBound

@define
class AllureCucumberConfig(StashBound):
    STASH_KEY = "allure-cucumber:config"
    output_dir: str = "allure-results"
```

**Storage pattern** (from `gherkin_message_reporter/entrypoint.py` lines 48-52):
```python
@frozen
class _AllureConfigEntry(StashBound):
    STASH_KEY: ClassVar[str] = "allure-cucumber:config"
    config: AllureCucumberConfig

# Set in pytest_configure:
config_entry = _AllureConfigEntry(config=cfg)
config_entry.set_in_stash(config.stash)

# Get later:
entry = _AllureConfigEntry.find_in_stash(config.stash).value_or(None)
```

---

### attrs Data Class Convention
**Source:** `src/pytest_bdd/model/execution_message_adapter.py` (lines 32-66), `src/pytest_bdd/model/stash_access.py` (lines 117-189)
**Apply to:** ALL data classes (model.py, plugin configs)

- Use `@define` or `@frozen` from `attrs` — NEVER stdlib `dataclass`
- Use `field()` for defaults, `ClassVar` for class-level constants
- Prefer `@frozen` for immutable models, `@define` for mutable plugin state
- Use `from __future__ import annotations` in all modules
- Use `returns.maybe.Maybe` / `Nothing` for optional values (no bare `return None` in non-hook code)

---

### Error Handling
**Source:** `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` (lines 264-274), `src/pytest_bdd/script/render_cucumber_formatters.py` (lines 157-162)
**Apply to:** All plugin, CLI, and converter code

```python
import logging
logger = logging.getLogger(__name__)

# Plugin configuration: log warning with exception info, then re-raise
except Exception:
    logger.warning("Plugin configuration failed", exc_info=True)
    # cleanup
    raise

# CLI: emit to stderr, return exit code (don't suppress; don't use bare except)
except (OSError, ValueError) as exc:
    _emit_error(f"Conversion failed: {exc}")
    return 1

# Specific exception types only — no bare `except Exception:` without logging
```

---

### Test Group Configuration
**Source:** `pyproject.toml` lines 264-274
**Apply to:** All new test files

Test directories are auto-assigned to groups by path:
```toml
test_group_paths = [
  "tests/cases/unit/** = unit",
  "tests/cases/integration/** = integration",
  "tests/cases/contract/** = contract",
]
```

No explicit `pytestmark` needed — the path-based auto-grouping handles it. However, if specific markers are needed for exclusion, follow existing patterns:
```python
pytestmark = [pytest.mark.unit]  # for tests/cases/unit/
```

---

### Test Fixture Pattern (pytester)
**Source:** `tests/cases/contract/messages/test_messages.py`
**Apply to:** Integration tests using `testdir`

```python
def test_with_testdir(testdir: "Testdir", tmp_path: Path) -> None:
    testdir.makefile(
        ".feature",
        "Feature: Test\n  Scenario: Demo\n    Given step",
    )
    testdir.makeconftest("""
        from pytest_bdd import given
        @given("step")
        def step(): pass
    """)
    result = testdir.runpytest_subprocess(
        "--option", str(tmp_path / "output"),
    )
```

---

### pyproject.toml Entry Point Pattern
**Source:** `pyproject.toml` lines 91-110
**Apply to:** Adding `pytest-bdd-allure-cucumber` entry

**Alphabetical insertion point:** After `"pytest-bdd-code-generator"` (line 92), before `"pytest-bdd-cucumber-formatter-json"` (line 93):
```toml
"pytest-bdd-allure-cucumber" = "pytest_bdd.plugin.allure_cucumber.entrypoint"
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/pytest_bdd/plugin/allure_cucumber/converter/step_tree.py` | service | transform | No existing flat-to-nested step tree builder in codebase. Pure algorithmic code per RESEARCH.md "Common Pitfalls #1" stack-based approach. |
| `docs/allure3-events.schema.json` | config | file-I/O | Greenfield schema artifact — no existing JSON Schema files in the project for Allure. Extracted from allure3/allure-python repos per Wave 1. |

---

## Metadata

**Analog search scope:** `src/pytest_bdd/plugin/*/`, `src/pytest_bdd/script/`, `src/pytest_bdd/model/`, `tests/cases/contract/`, `tests/cases/unit/`, `tests/cases/integration/`, `pyproject.toml`
**Files scanned:** 80+ plugin files, 15+ test files, 5 model files
**Pattern extraction date:** 2026-06-09
**Key patterns identified:**
1. **Canonical 3-file plugin** (entrypoint.py + plugin.py + hook.py) — enforced by `test_plugin_structure_contract.py`
2. **StashBound config storage** — `@define`/`@frozen` + `STASH_KEY` + `set_in_stash()`/`find_in_stash()`
3. **attrs data classes** — `@define`/`@frozen` from `attrs`, NEVER `dataclass`
4. **ExecutionMessageAdapter.deserialize_dict()** — reads NDJSON lines into typed `ExecutionProjection`
5. **CLI pattern** — `argparse` + `main(argv)` → `[project.scripts]` in pyproject.toml
6. **pytest11 registration** — `[project.entry-points.pytest11]` → `entrypoint.py` module-level instance
7. **pytester test pattern** — `testdir.makefile` + `testdir.runpytest_subprocess` for integration tests
8. **No return None** — use `Nothing` from `returns` or sentinel values in non-hook code
