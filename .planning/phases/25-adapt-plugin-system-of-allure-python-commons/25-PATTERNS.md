# Phase 25: adapt-plugin-system-of-allure-python-commons - Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 12
**Analogs found:** 10 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` | config | request-response | `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/plugin.py` | plugin | event-driven | `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` | role-match |
| `src/pytest_bdd/plugin/allure_cucumber/hook.py` | hook | event-driven | `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` | exact |
| `src/pytest_bdd/plugin/allure_cucumber/adapter.py` | adapter | transform | `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py` | exact |
| `tests/cases/e2e/test_allure_plugin_hook_mode.py` | test | request-response | `tests/cases/contract/cck/test_cck_allure_conversion.py` | role-match |
| `tests/cases/e2e/test_allure_plugin_ndjson_import.py` | test | file-I/O | `tests/cases/contract/cck/test_cck_allure_conversion.py` | role-match |
| `tests/cases/contract/cck/test_cck_allure_hook_vs_import.py` | test | transform | `tests/cases/contract/allure/test_allure_consumption_ui.py` | role-match |
| `tests/cases/e2e/test_allure_xdist_total_report.py` | test | event-driven | `tests/cases/external/e2e/test_xdist_remote_message_aggregation.py` | role-match |
| `tests/cases/e2e/test_allure_pytest_coexistence.py` | test | request-response | `tests/cases/contract/cck/test_cck_allure_conversion.py` | role-match |
| `features/17 Allure Converter/` | feature | request-response | `features/17 Allure Converter/1 Allure converter.feature.md` | exact |
| `docs/architecture/allure.md` | config | request-response | `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` | role-match |
| `pyproject.toml` | config | request-response | `pyproject.toml` | exact |

## Pattern Assignments

### `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` (config, request-response)

**Analog:** `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`

**Imports pattern** (lines 1-20):
```python
from __future__ import annotations

import logging
import os
from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar, TextIO, cast

import pytest
from attrs import frozen

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager, Stash, TerminalReporter
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.plugin.gherkin_message_reporter.runtime_contract import ReporterLifecycleContract
```

**Plugin registration pattern** (lines 39-71):
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
    group.addoption(
        "--allure-cucumber-messages-in",
        action="store",
        dest="allure_cucumber_messages_in",
        metavar="PATH",
        default=None,
        help="Path to an existing Cucumber Messages NDJSON file to import into Allure results.",
    )
    parser.addini(
        "allure_cucumber_output_dir",
        help="Output directory for Allure result JSON files.",
        default="allure-results",
    )
```

**Configuration validation pattern** (lines 39-71):
```python
def pytest_configure(config: Config) -> None:
    """Handle configure."""
    import pytest

    output_dir = getattr(config.option, "allure_cucumber_output_dir", None) or config.getini(
        "allure_cucumber_output_dir",
    )
    messages_in = getattr(config.option, "allure_cucumber_messages_in", None)

    # Fail early if there is a configuration conflict
    if messages_in is not None and not output_dir:
        raise pytest.UsageError(
            "--allure-cucumber-messages-in requires --allure-cucumber-output to write results."
        )

    # We only activate the plugin if output_dir is configured, or if messages_in is provided
    has_output = getattr(config.option, "allure_cucumber_output_dir", None) is not None
    has_input = messages_in is not None

    if not has_output and not has_input:
        return

    plugin = AllureCucumberPlugin(
        config=config,
        output_dir=output_dir or "allure-results",
        messages_in=messages_in,
    )
    config._allure_cucumber_plugin = plugin  # type: ignore[attr-defined]  # noqa: SLF001
    config.pluginmanager.register(plugin, "allure-cucumber-converter")
```

---

### `src/pytest_bdd/plugin/allure_cucumber/plugin.py` (plugin, event-driven)

**Analog:** `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py`

**Imports pattern** (lines 1-20):
```python
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import define, field
import pytest

from pytest_bdd.compatibility.pytest import TerminalReporter

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.model.message_extension import EventEnvelope
```

**attrs class pattern** (lines 22-31):
```python
@define(eq=False, hash=False)
class AllureCucumberPlugin:
    """Represent allure cucumber plugin state."""

    config: Config = field()
    output_dir: str = "allure-results"
    messages_in: str | None = None
    plugin_name: str = "pytest-bdd-allure-cucumber"
    envelopes: list[EventEnvelope] = field(factory=list)
```

**Hook implementation pattern** (lines 32-34):
```python
def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
    """Collect messages for live reporting."""
    self.envelopes.append(message)
```

**Session finish pattern** (lines 41-103):
```python
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(self) -> None:
    """Handle sessionfinish — call adapter."""
    if hasattr(self.config, "workerinput"):
        return

    output_path = Path(os.path.expandvars(self.output_dir)).expanduser().resolve()
    if output_path.exists() and any(output_path.iterdir()):
        logger.warning("Allure output directory '%s' is not empty.", output_path)

    output_path.mkdir(parents=True, exist_ok=True)

    if self.messages_in is not None:
        # NDJSON import mode
        input_path = Path(os.path.expandvars(self.messages_in)).expanduser().resolve()
        if not input_path.exists():
            logger.error("NDJSON import file '%s' does not exist.", input_path)
            return

        from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes
        try:
            projections = list(read_envelopes(input_path))
        except Exception as exc:
            logger.error("Failed to read envelopes from %s: %s", input_path, exc, exc_info=True)
            return
    else:
        # Live mode - read from self.envelopes (to be rewired)
        from pytest_bdd.plugin.gherkin_message_reporter.entrypoint import _resolve_reporter_state
        reporter = _resolve_reporter_state(self.config)
        if reporter is None:
            logger.warning("GherkinMessageReporter plugin not found, skipping Allure report generation.")
            return

        messages_file = getattr(reporter, "final_messages_file_path", None)
        if messages_file is None or not messages_file.exists():
            logger.warning("Consolidated messages file not found, skipping Allure report generation.")
            return

        from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService
        try:
            envelopes = TransportService.read_envelopes_from_path(messages_file)
            from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
            projections = [ExecutionMessageAdapter.deserialize(env) for env in envelopes]
        except Exception as exc:
            logger.error("Failed to read consolidated envelopes: %s", exc, exc_info=True)
            return

    from pytest_bdd.plugin.allure_cucumber.adapter import convert_to_allure_commons
    try:
        convert_to_allure_commons(projections, output_path)
    except Exception as exc:
        logger.error("Allure results generation failed: %s", exc, exc_info=True)
    finally:
        if self.messages_in is None:
            # Clean up temp file if needed
            from pytest_bdd.plugin.gherkin_message_reporter.entrypoint import _resolve_reporter_state
            reporter = _resolve_reporter_state(self.config)
            if reporter is not None:
                is_temp = getattr(reporter, "is_messages_file_temp", False)
                messages_file = getattr(reporter, "final_messages_file_path", None)
                if is_temp and messages_file is not None and messages_file.exists():
                    try:
                        messages_file.unlink()
                    except OSError:
                        pass
```

**Key rewiring needed:** Replace lines 66-84 with logic that reads from `self.envelopes` instead of `final_messages_file_path` for live mode.

---

### `src/pytest_bdd/plugin/allure_cucumber/hook.py` (hook, event-driven)

**Analog:** `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py`

**Imports pattern** (lines 1-15):
```python
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.message_extension import EventEnvelope
```

**Hook specification pattern** (lines 16-41):
```python
class GherkinMessageReporterHookSpec:
    """Declare hooks used by the gherkin message reporter."""

    @pytest.hookspec
    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
        """Implement cucumber message protocol https://github.com/cucumber/messages."""

    @pytest.hookspec
    def pytest_bdd_xdist_message_batch(self, config: Config, node: object, batch: dict[str, object]) -> None:
        """Record reporter-specific xdist batch events received on the controller side."""
```

---

### `src/pytest_bdd/plugin/allure_cucumber/adapter.py` (adapter, transform)

**Analog:** `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py`

**Imports pattern** (lines 1-35):
```python
from __future__ import annotations

import logging
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable
from uuid import uuid4

import allure_commons
from allure_commons.lifecycle import AllureLifecycle
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import (
    TestResult,
    TestResultContainer,
    TestStepResult,
    Attachment,
    Parameter,
    Label,
    Link,
    StatusDetails,
)
from pytest_bdd.plugin.allure_cucumber.converter.collector import group_by_test_case
from pytest_bdd.plugin.allure_cucumber.converter.mapper import map_test_case_to_result
```

**Allure lifecycle writing pattern** (lines 60-99):
```python
def convert_to_allure_commons(projections: Iterable[ExecutionProjection], output_dir: Path) -> None:
    """
    Convert Cucumber Message projections and write Allure3 JSON results using allure-python-commons.
    """
    grouped, structural = group_by_test_case(projections)

    results: list[AllureTestResult] = []
    for case_id, case_projections in grouped.items():
        if case_id.startswith("run:"):
            continue
        result = map_test_case_to_result(case_id, case_projections, structural)
        results.append(result)

    if not results:
        return

    # Initialize AllureLifecycle
    lifecycle = AllureLifecycle()

    # Create and register the file logger
    file_logger = AllureFileLogger(str(output_dir))
    allure_commons.plugin_manager.register(file_logger)

    try:
        # Write results
        result_uuids = []
        for res in results:
            write_result(res, lifecycle)
            result_uuids.append(res.uuid)

        # Write container
        container = TestResultContainer(
            uuid=str(uuid4()),
            name="Test results",
            children=result_uuids,
        )
        allure_commons.plugin_manager.hook.report_container(container=container)
    finally:
        # Always unregister the logger so we don't leak it
        allure_commons.plugin_manager.unregister(file_logger)
```

---

### `tests/cases/e2e/test_allure_plugin_hook_mode.py` (test, request-response)

**Analog:** `tests/cases/contract/cck/test_cck_allure_conversion.py`

**Imports pattern** (lines 1-18):
```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES

pytestmark = [pytest.mark.contract]
```

**Test class pattern** (lines 20-48):
```python
class TestCCKAllureConversion:
    """Validate allure-cucumber converter handles all CCK samples."""

    @pytest.mark.parametrize("sample_name", CCK_SAMPLE_NAMES)
    def test_sample_produces_allure_results(
        self,
        sample_name: str,
        cck_samples: dict[str, Path],
        tmp_path: Path,
    ):
        """Each CCK sample should produce Allure result files."""
        if sample_name not in cck_samples:
            pytest.skip(f"CCK sample '{sample_name}' not available")

        ndjson_path = cck_samples[sample_name]
        output_dir = tmp_path / f"allure-{sample_name}"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        container_files = list(output_dir.glob("*-container.json"))

        if ndjson_path.stat().st_size > 0:
            assert len(result_files) > 0 or len(container_files) > 0, (
                f"No Allure result/container files produced for sample '{sample_name}'"
            )
```

---

### `tests/cases/e2e/test_allure_plugin_ndjson_import.py` (test, file-I/O)

**Analog:** `tests/cases/contract/cck/test_cck_allure_conversion.py`

**Test pattern for NDJSON import** (lines 73-84):
```python
def test_empty_ndjson_produces_no_results(self, tmp_path: Path):
    """Empty NDJSON should not crash and should produce no results."""
    ndjson_path = tmp_path / "empty.ndjson"
    ndjson_path.write_text("", encoding="utf-8")

    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()

    convert(ndjson_path, output_dir)

    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) == 0, "Empty NDJSON should produce no result files"
```

---

### `tests/cases/contract/cck/test_cck_allure_hook_vs_import.py` (test, transform)

**Analog:** `tests/cases/contract/allure/test_allure_consumption_ui.py`

**Imports pattern** (lines 1-25):
```python
from __future__ import annotations

import json
import subprocess  # noqa: S404
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.testing.docker import require_docker_daemon

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.contract]

ALLURE_DOCKER_IMAGE = "allure3-local:latest"
PLAYWRIGHT_MARK = pytest.mark.browser
```

**Test fixture pattern** (lines 30-38):
```python
@pytest.fixture
def docker_backend():
    """Require Docker daemon available."""
    from pytest_bdd.testing.docker import ensure_allure3_image

    backend = require_docker_daemon()
    ensure_allure3_image()
    return backend
```

---

### `tests/cases/e2e/test_allure_xdist_total_report.py` (test, event-driven)

**Analog:** `tests/cases/external/e2e/test_xdist_remote_message_aggregation.py`

**Test pattern for xdist** (lines 1-50):
```python
from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e]


class TestXdistRemoteMessageAggregation:
    """Validate xdist message aggregation across workers."""

    def test_xdist_produces_single_allure_report(self, tmp_path: Path):
        """xdist run should produce one consolidated Allure report."""
        # Test implementation using pytest -n 2
        pass
```

---

### `tests/cases/e2e/test_allure_pytest_coexistence.py` (test, request-response)

**Analog:** `tests/cases/contract/cck/test_cck_allure_conversion.py`

**Test pattern for coexistence** (lines 1-50):
```python
from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e]


class TestAllurePytestCoexistence:
    """Validate plugin works with and without allure-pytest installed."""

    def test_plugin_works_without_allure_pytest(self, tmp_path: Path):
        """Plugin should produce results without allure-pytest."""
        # Test implementation
        pass

    def test_plugin_works_with_allure_pytest(self, tmp_path: Path):
        """Plugin should produce results with allure-pytest installed."""
        # Test implementation
        pass
```

---

### `features/17 Allure Converter/` (feature, request-response)

**Analog:** `features/17 Allure Converter/1 Allure converter.feature.md`

**Feature file pattern** (lines 1-10):
```markdown
# Feature: Allure-Cucumber Converter
  This feature documents the Allure-Cucumber Converter's ability to convert
  Cucumber Messages NDJSON files to Allure3 JSON result files.

## Scenario: Convert a minimal valid NDJSON to Allure results
  Given a cucumber messages NDJSON file with one passing scenario
  When the allure-cucumber converter processes the file
  Then an Allure result JSON file is created
  And the result JSON validates against the Allure3 events schema
  And the result has status "passed"
```

---

### `docs/architecture/allure.md` (config, request-response)

**Analog:** `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py`

**Documentation pattern:**
- Update architecture document to reflect pytest-native commons path
- Document deprecation of standalone converter CLI
- Document option name changes from `--allure-bdd-*` to `--allure-cucumber-*`

---

### `pyproject.toml` (config, request-response)

**Analog:** `pyproject.toml`

**Configuration pattern:**
- Update extras/entry points if old converter CLI semantics change
- Add deprecation warnings for old option names
- Update documentation references

## Shared Patterns

### Authentication
**Source:** N/A (pytest plugin system)
**Apply to:** All controller files
```python
# No authentication needed - pytest plugin system handles registration
```

### Error Handling
**Source:** `src/pytest_bdd/plugin/allure_cucumber/plugin.py` lines 41-103
**Apply to:** All plugin and adapter files
```python
try:
    # Operation
except Exception as exc:
    logger.error("Operation failed: %s", exc, exc_info=True)
finally:
    # Cleanup
```

### Validation
**Source:** `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` lines 39-71
**Apply to:** All controller files
```python
# Fail early if there is a configuration conflict
if messages_in is not None and not output_dir:
    raise pytest.UsageError(
        "--allure-cucumber-messages-in requires --allure-cucumber-output to write results."
    )
```

### xdist Worker Skip
**Source:** `src/pytest_bdd/plugin/allure_cucumber/plugin.py` lines 44-45
**Apply to:** All plugin files
```python
if hasattr(self.config, "workerinput"):
    return  # Skip on xdist workers
```

### Envelope Collection
**Source:** `src/pytest_bdd/plugin/allure_cucumber/plugin.py` lines 32-34
**Apply to:** All hook-mode files
```python
def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
    """Collect messages for live reporting."""
    self.envelopes.append(message)
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/cases/contract/cck/test_cck_allure_hook_vs_import.py` | test | transform | New golden equivalence test pattern |
| `tests/cases/e2e/test_allure_xdist_total_report.py` | test | event-driven | New xdist-specific Allure test pattern |
| `tests/cases/e2e/test_allure_pytest_coexistence.py` | test | request-response | New coexistence test pattern |

## Metadata

**Analog search scope:** `src/pytest_bdd/plugin/`, `tests/cases/`, `features/`
**Files scanned:** 25
**Pattern extraction date:** 2026-06-13
