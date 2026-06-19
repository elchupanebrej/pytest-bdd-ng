# Pluggy Hooks Refactor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace direct callback passing and config stash access with pluggy hookspecs for all cross-plugin communication in the allure-cucumber module.

**Architecture:** Define hookspecs in `hook.py`, register them via `pytest_addhooks`, implement them on `MessageDrivenListener`, and call them from `AllureCucumberApiHooks` and `AllureCucumberImportPlugin` instead of direct references.

**Tech Stack:** pluggy, attrs, pytest

---

## Problem Analysis

Current cross-plugin communication uses two anti-patterns:

1. **Direct callback:** `AllureCucumberApiHooks(listener=listener)` — holds a reference to the listener and reaches through it to `self.listener.adapter.lifecycle`
2. **Config stash:** `config._allure_cucumber_listener` — import plugin reaches into config to access the listener's adapter

Both should use pluggy hookspecs instead.

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/pytest_bdd/plugin/allure_cucumber/hook.py` | **Rewrite** | Define `AllureCucumberHookSpec` with all cross-plugin hooks |
| `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` | **Modify** | Register hookspecs via `pytest_addhooks`, remove config stash, remove `_ConverterMarker` |
| `src/pytest_bdd/plugin/allure_cucumber/listener.py` | **Modify** | Implement hookspecs via `@pytest.hookimpl` |
| `src/pytest_bdd/plugin/allure_cucumber/api_hooks.py` | **Modify** | Call hooks via `config.hook.xxx()` instead of `self.listener.adapter.lifecycle` |
| `src/pytest_bdd/plugin/allure_cucumber/plugin.py` | **Modify** | Call hooks via `config.hook.xxx()` instead of `config._allure_cucumber_listener` |
| `tests/cases/unit/allure/test_listener.py` | **Modify** | Update tests for new hook-based API |
| `tests/cases/unit/allure/test_api_hooks.py` | **Modify** | Update tests for hook-based calls |
| `tests/cases/unit/allure/test_native_plugin.py` | **Modify** | Remove config stash tests, add hook-based tests |

---

### Task 1: Define AllureCucumberHookSpec

**Files:**
- Modify: `src/pytest_bdd/plugin/allure_cucumber/hook.py`

- [x] **Step 1: Write the hookspec**

```python
"""Hook specifications for the allure-cucumber plugin.

Declares hooks used for cross-plugin communication within the allure-cucumber module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.model.execution_message_adapter import CucumberEnvelopeAdapter


class AllureCucumberHookSpec:
    """Declare hooks for allure-cucumber cross-plugin communication."""

    @pytest.hookspec
    def allure_cucumber_start_step(
        self,
        config: Config,
        uuid: str,
        title: str,
        params: dict | None = None,
    ) -> None:
        """Start a new step in the current test case."""

    @pytest.hookspec
    def allure_cucumber_stop_step(
        self,
        config: Config,
        uuid: str,
        exc_type: type | None = None,
        exc_val: Exception | None = None,
        exc_tb: object | None = None,
    ) -> None:
        """Stop the current step."""

    @pytest.hookspec
    def allure_cucumber_attach_data(
        self,
        config: Config,
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach data to the current test case or step."""

    @pytest.hookspec
    def allure_cucumber_attach_file(
        self,
        config: Config,
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach a file to the current test case or step."""

    @pytest.hookspec(firstresult=True)
    def allure_cucumber_get_adapter(
        self,
        config: Config,
    ) -> CucumberEnvelopeAdapter | None:
        """Return the CucumberEnvelopeAdapter instance for message routing."""
```

- [x] **Step 2: Verify import works**

Run: `python -c "from pytest_bdd.plugin.allure_cucumber.hook import AllureCucumberHookSpec; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add src/pytest_bdd/plugin/allure_cucumber/hook.py
git commit -m "feat: define AllureCucumberHookSpec for cross-plugin communication"
```

---

### Task 2: Register hookspecs and remove _ConverterMarker

**Files:**
- Modify: `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py`

- [x] **Step 1: Add pytest_addhooks and simplify entrypoint**

Remove `_ConverterMarker` class, `_cleanup_converter_marker` function, and all references to `converter_marker`. Add `pytest_addhooks` to register the hookspec. Remove all `config._allure_cucumber_*` stash assignments (except the ones needed for unconfigure — actually none will be needed since pluggy handles lifecycle).

Replace the entire entrypoint with:

```python
"""Provide entrypoint helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hook specifications."""
    from pytest_bdd.plugin.allure_cucumber.hook import AllureCucumberHookSpec

    pluginmanager.add_hookspecs(AllureCucumberHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Allure Cucumber")
    group.addoption(
        "--allure-cucumber-out",
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


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    import functools
    import pytest

    output_dir = getattr(config.option, "allure_cucumber_output_dir", None) or config.getini(
        "allure_cucumber_output_dir",
    )
    messages_in = getattr(config.option, "allure_cucumber_messages_in", None)

    # Fail early if there is a configuration conflict
    if messages_in is not None and not output_dir:
        raise pytest.UsageError(
            "--allure-cucumber-messages-in requires --allure-cucumber-out to write results."
        )

    has_output = getattr(config.option, "allure_cucumber_output_dir", None) is not None or bool(output_dir)
    has_input = messages_in is not None

    if not has_output and not has_input:
        return

    from pytest_bdd.plugin.allure_cucumber.api_hooks import AllureCucumberApiHooks
    from pytest_bdd.plugin.allure_cucumber.listener import MessageDrivenListener

    import allure_commons

    output_path = Path(os.path.expandvars(output_dir or "allure-results")).expanduser().resolve()

    listener = MessageDrivenListener(
        config=config,
        output_dir=str(output_path),
    )
    config.pluginmanager.register(listener, "allure-cucumber-listener")
    config.add_cleanup(functools.partial(config.pluginmanager.unregister, listener))

    api_hooks = AllureCucumberApiHooks(config=config)
    allure_commons.plugin_manager.register(api_hooks)
    config.add_cleanup(functools.partial(allure_commons.plugin_manager.unregister, api_hooks))

    listener.start()

    if has_input:
        from pytest_bdd.plugin.allure_cucumber.plugin import CucumberNDJSONImportPlugin

        import_plugin = CucumberNDJSONImportPlugin(
            config=config,
            output_dir=str(output_path),
            messages_in=messages_in,
        )
        config.pluginmanager.register(import_plugin, "allure-cucumber-import")
        config.add_cleanup(functools.partial(config.pluginmanager.unregister, import_plugin))


def pytest_unconfigure(config: Config) -> None:
    """Handle unconfigure.

    Cleanup is handled by config.add_cleanup callbacks registered in pytest_configure.
    """
```

- [x] **Step 2: Verify no import errors**

Run: `python -c "from pytest_bdd.plugin.allure_cucumber.entrypoint import pytest_addhooks, pytest_configure; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add src/pytest_bdd/plugin/allure_cucumber/entrypoint.py
git commit -m "refactor: register hookspecs via pytest_addhooks, remove config stash"
```

---

### Task 3: Implement hooks on MessageDrivenListener

**Files:**
- Modify: `src/pytest_bdd/plugin/allure_cucumber/listener.py`

- [x] **Step 1: Add hookimpl implementations**

```python
"""MessageDrivenListener — receives pytest_bdd_message, maps to lifecycle."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from attrs import define, field

from pytest_bdd.plugin.allure_cucumber.message_adapter import CucumberEnvelopeAdapter

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.model.execution_message_adapter import CucumberEnvelopeAdapter as CucumberEnvelopeAdapterType
    from pytest_bdd.model.message_extension import EventEnvelope

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class MessageDrivenListener:
    """Receive pytest_bdd_message events and map to AllureLifecycle.

    Implements AllureCucumberHookSpec hooks for cross-plugin communication.
    """

    config: Config = field()
    output_dir: str = field()
    adapter: CucumberEnvelopeAdapter = field(init=False)
    _file_logger: object | None = field(default=None, init=False)

    def __attrs_post_init__(self) -> None:
        from allure_commons.lifecycle import AllureLifecycle

        self.adapter = CucumberEnvelopeAdapter(lifecycle=AllureLifecycle())

    def start(self) -> None:
        """Initialize the file logger and register with allure_commons."""
        import os
        from pathlib import Path

        import allure_commons
        from allure_commons.logger import AllureFileLogger

        output_path = Path(os.path.expandvars(self.output_dir)).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        self._file_logger = AllureFileLogger(str(output_path))
        allure_commons.plugin_manager.register(self._file_logger)

    def stop(self) -> None:
        """Unregister the file logger."""
        import allure_commons

        file_logger = getattr(self, "_file_logger", None)
        if file_logger is not None:
            allure_commons.plugin_manager.unregister(file_logger)
            self._file_logger = None

    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:  # noqa: ARG002
        """Process a single Cucumber Message envelope in real-time."""
        from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

        try:
            projection = ExecutionMessageAdapter.deserialize(message)
            self.adapter.route_envelope(projection)
        except Exception:
            logger.exception("Failed to process envelope: %s", message)

    @pytest.hookimpl
    def allure_cucumber_get_adapter(self, config: Config) -> CucumberEnvelopeAdapterType | None:  # noqa: ARG002
        """Return the adapter for NDJSON import routing."""
        return self.adapter

    @pytest.hookimpl
    def allure_cucumber_start_step(
        self,
        config: Config,  # noqa: ARG002
        uuid: str,
        title: str,
        params: dict | None = None,  # noqa: ARG002
    ) -> None:
        """Start a new step via the lifecycle."""
        with self.adapter.lifecycle.start_step(uuid=uuid) as step:
            step.name = title

    @pytest.hookimpl
    def allure_cucumber_stop_step(
        self,
        config: Config,  # noqa: ARG002
        uuid: str,
        exc_type: type | None = None,  # noqa: ARG002
        exc_val: Exception | None = None,  # noqa: ARG002
        exc_tb: object | None = None,  # noqa: ARG002
    ) -> None:
        """Stop a step via the lifecycle."""
        self.adapter.lifecycle.stop_step(uuid)

    @pytest.hookimpl
    def allure_cucumber_attach_data(
        self,
        config: Config,  # noqa: ARG002
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach data via the lifecycle."""
        from uuid import uuid4

        attachment_uuid = str(uuid4())
        self.adapter.lifecycle.attach_data(
            uuid=attachment_uuid,
            body=body,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )

    @pytest.hookimpl
    def allure_cucumber_attach_file(
        self,
        config: Config,  # noqa: ARG002
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach a file via the lifecycle."""
        from uuid import uuid4

        attachment_uuid = str(uuid4())
        self.adapter.lifecycle.attach_file(
            uuid=attachment_uuid,
            source=source,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )
```

- [x] **Step 2: Verify import works**

Run: `python -c "from pytest_bdd.plugin.allure_cucumber.listener import MessageDrivenListener; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add src/pytest_bdd/plugin/allure_cucumber/listener.py
git commit -m "feat: implement AllureCucumberHookSpec on MessageDrivenListener"
```

---

### Task 4: Refactor AllureCucumberApiHooks to use hooks

**Files:**
- Modify: `src/pytest_bdd/plugin/allure_cucumber/api_hooks.py`

- [x] **Step 1: Rewrite api_hooks to call hooks via config**

```python
"""AllureCucumberApiHooks — implements allure_commons hooks via pluggy dispatch."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureCucumberApiHooks:
    """Implement allure_commons hooks by dispatching to AllureCucumberHookSpec.

    Does not hold any reference to the listener — communication is entirely
    via pluggy hooks dispatched through config.hook.
    """

    config: Config = field()

    def start_step(self, uuid: str, title: str, params: dict | None = None) -> None:  # type: ignore[override]
        """Start a new step in the current test case."""
        self.config.hook.allure_cucumber_start_step(
            config=self.config, uuid=uuid, title=title, params=params,
        )

    def stop_step(
        self,
        uuid: str,
        exc_type: type | None = None,
        exc_val: Exception | None = None,
        exc_tb: object | None = None,
    ) -> None:  # type: ignore[override]
        """Stop the current step."""
        self.config.hook.allure_cucumber_stop_step(
            config=self.config, uuid=uuid,
            exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb,
        )

    def attach_data(
        self,
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:  # type: ignore[override]
        """Attach data to the current test case or step."""
        self.config.hook.allure_cucumber_attach_data(
            config=self.config, body=body, name=name,
            attachment_type=attachment_type, extension=extension,
        )

    def attach_file(
        self,
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:  # type: ignore[override]
        """Attach a file to the current test case or step."""
        self.config.hook.allure_cucumber_attach_file(
            config=self.config, source=source, name=name,
            attachment_type=attachment_type, extension=extension,
        )
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from pytest_bdd.plugin.allure_cucumber.api_hooks import AllureCucumberApiHooks; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/pytest_bdd/plugin/allure_cucumber/api_hooks.py
git commit -m "refactor: api_hooks dispatches via pluggy instead of direct callback"
```

---

### Task 5: Refactor AllureCucumberImportPlugin to use hooks

**Files:**
- Modify: `src/pytest_bdd/plugin/allure_cucumber/plugin.py`

- [x] **Step 1: Replace config stash access with hook call**

```python
"""Provide plugin helpers for NDJSON import mode."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureCucumberImportPlugin:
    """Handle NDJSON import mode — reads file and writes Allure results through the adapter."""

    config: Config = field()
    output_dir: str = field()
    messages_in: str = field()

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        """Deselect all items — import mode does not run BDD scenarios."""
        items.clear()

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self) -> None:
        """Read NDJSON and write Allure results through the listener adapter."""
        if hasattr(self.config, "workerinput"):
            return

        adapter = self.config.hook.allure_cucumber_get_adapter(config=self.config)
        if adapter is None:
            logger.error("No adapter available for NDJSON import mode.")
            return

        input_path = Path(os.path.expandvars(self.messages_in)).expanduser().resolve()
        if not input_path.exists():
            logger.error("NDJSON import file '%s' does not exist.", input_path)
            return

        from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes

        try:
            projections = list(read_envelopes(input_path))
        except Exception:
            logger.exception("Failed to read envelopes from %s", input_path)
            return

        for projection in projections:
            adapter.route_envelope(projection)

    def pytest_terminal_summary(self, terminalreporter: object) -> None:
        """Write terminal summary."""
        if hasattr(self.config, "workerinput"):
            return
        from pytest_bdd.compatibility.pytest import TerminalReporter

        if isinstance(terminalreporter, TerminalReporter):
            terminalreporter.write_sep("-", f"generated allure results: {self.output_dir}")
```

- [x] **Step 2: Verify import works**

Run: `python -c "from pytest_bdd.plugin.allure_cucumber.plugin import AllureCucumberImportPlugin; print('OK')"`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add src/pytest_bdd/plugin/allure_cucumber/plugin.py
git commit -m "refactor: import_plugin uses hooks instead of config stash"
```

---

### Task 6: Update unit tests

**Files:**
- Modify: `tests/cases/unit/allure/test_listener.py`
- Modify: `tests/cases/unit/allure/test_api_hooks.py`
- Modify: `tests/cases/unit/allure/test_native_plugin.py`

- [x] **Step 1: Update test_listener.py**

The listener now implements hookspecs. Update tests to verify hook dispatch:

```python
"""Unit tests for MessageDrivenListener."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.plugin.allure_cucumber.listener import MessageDrivenListener

pytestmark = [pytest.mark.unit]


class TestMessageDrivenListener:
    """Tests for MessageDrivenListener hook implementations."""

    def test_init_creates_adapter(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        assert listener.adapter is not None

    def test_pytest_bdd_message_calls_adapter(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch("pytest_bdd.plugin.allure_cucumber.listener.ExecutionMessageAdapter") as mock_adapter:
            mock_proj = MagicMock()
            mock_adapter.deserialize.return_value = mock_proj
            message = MagicMock()
            listener.pytest_bdd_message(config, message)
            listener.adapter.route_envelope.assert_called_once_with(mock_proj)

    def test_pytest_bdd_message_handles_exception(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch("pytest_bdd.plugin.allure_cucumber.listener.ExecutionMessageAdapter") as mock_adapter:
            mock_adapter.deserialize.side_effect = RuntimeError("bad message")
            message = MagicMock()
            listener.pytest_bdd_message(config, message)

    def test_start_registers_file_logger(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch("allure_commons.plugin_manager") as mock_pm:
            with patch("allure_commons.logger.AllureFileLogger"):
                listener.start()
            mock_pm.register.assert_called()

    def test_stop_unregisters_file_logger(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        listener._file_logger = MagicMock()
        with patch("allure_commons.plugin_manager") as mock_pm:
            listener.stop()
            mock_pm.unregister.assert_called_once()
            assert listener._file_logger is None

    def test_stop_noop_when_no_file_logger(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch("allure_commons.plugin_manager") as mock_pm:
            listener.stop()
            mock_pm.unregister.assert_not_called()

    def test_allure_cucumber_get_adapter_returns_adapter(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        result = listener.allure_cucumber_get_adapter(config=config)
        assert result is listener.adapter

    def test_allure_cucumber_start_step(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch.object(listener.adapter.lifecycle, "start_step") as mock_start:
            listener.allure_cucumber_start_step(config=config, uuid="u1", title="step1")
            mock_start.assert_called_once_with(uuid="u1")

    def test_allure_cucumber_stop_step(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch.object(listener.adapter.lifecycle, "stop_step") as mock_stop:
            listener.allure_cucumber_stop_step(config=config, uuid="u1")
            mock_stop.assert_called_once_with("u1")

    def test_allure_cucumber_attach_data(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch.object(listener.adapter.lifecycle, "attach_data") as mock_attach:
            listener.allure_cucumber_attach_data(
                config=config, body="data", name="file.txt",
                attachment_type="text/plain", extension="txt",
            )
            mock_attach.assert_called_once()

    def test_allure_cucumber_attach_file(self) -> None:
        config = MagicMock(spec=Config)
        listener = MessageDrivenListener(config=config, output_dir="/tmp/test")
        with patch.object(listener.adapter.lifecycle, "attach_file") as mock_attach:
            listener.allure_cucumber_attach_file(
                config=config, source="/path/to/file", name="file.txt",
                attachment_type="image/png", extension="png",
            )
            mock_attach.assert_called_once()
```

- [x] **Step 2: Update test_api_hooks.py**

```python
"""Unit tests for AllureCucumberApiHooks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.plugin.allure_cucumber.api_hooks import AllureCucumberApiHooks

pytestmark = [pytest.mark.unit]


class TestAllureCucumberApiHooks:
    """Tests for AllureCucumberApiHooks hook dispatching."""

    def test_start_step_dispatches_hook(self) -> None:
        config = MagicMock(spec=Config)
        hooks = AllureCucumberApiHooks(config=config)
        hooks.start_step(uuid="u1", title="step1", params={"p": 1})
        config.hook.allure_cucumber_start_step.assert_called_once_with(
            config=config, uuid="u1", title="step1", params={"p": 1},
        )

    def test_stop_step_dispatches_hook(self) -> None:
        config = MagicMock(spec=Config)
        hooks = AllureCucumberApiHooks(config=config)
        hooks.stop_step(uuid="u1", exc_type=ValueError, exc_val=ValueError("x"), exc_tb=None)
        config.hook.allure_cucumber_stop_step.assert_called_once_with(
            config=config, uuid="u1",
            exc_type=ValueError, exc_val=ValueError("x"), exc_tb=None,
        )

    def test_attach_data_dispatches_hook(self) -> None:
        config = MagicMock(spec=Config)
        hooks = AllureCucumberApiHooks(config=config)
        hooks.attach_data(body="data", name="file.txt", attachment_type="text/plain", extension="txt")
        config.hook.allure_cucumber_attach_data.assert_called_once_with(
            config=config, body="data", name="file.txt",
            attachment_type="text/plain", extension="txt",
        )

    def test_attach_file_dispatches_hook(self) -> None:
        config = MagicMock(spec=Config)
        hooks = AllureCucumberApiHooks(config=config)
        hooks.attach_file(source="/path", name="file.png", attachment_type="image/png", extension="png")
        config.hook.allure_cucumber_attach_file.assert_called_once_with(
            config=config, source="/path", name="file.png",
            attachment_type="image/png", extension="png",
        )
```

- [x] **Step 3: Update test_native_plugin.py**

Remove tests that check config stash. Remove the `test_adapter_generates_allure_results` test (it tests the old adapter path). Keep only the relevant tests:

```python
"""Unit tests for allure-cucumber plugin entrypoint."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.plugin.allure_cucumber.entrypoint import pytest_configure
from pytest_bdd.plugin.allure_cucumber.listener import MessageDrivenListener

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock pytest Config."""
    config = MagicMock(spec=Config)
    config.option = MagicMock()
    config.option.allure_cucumber_output_dir = None
    config.option.allure_cucumber_messages_in = None
    config.getini = MagicMock(return_value=None)
    config.pluginmanager = MagicMock()
    return config


def test_plugin_not_registered_by_default(mock_config: MagicMock) -> None:
    """Verify plugin is not registered if no allure options are provided."""
    pytest_configure(mock_config)
    mock_config.pluginmanager.register.assert_not_called()


def test_listener_registered_with_output_dir(mock_config: MagicMock) -> None:
    """Verify MessageDrivenListener is registered when output directory option is provided."""
    mock_config.option.allure_cucumber_output_dir = "allure-results"
    with patch("allure_commons.plugin_manager") as mock_pm:
        with patch("allure_commons.logger.AllureFileLogger"):
            pytest_configure(mock_config)
    mock_config.pluginmanager.register.assert_called()
    registered_plugin = mock_config.pluginmanager.register.call_args[0][0]
    assert isinstance(registered_plugin, MessageDrivenListener)


def test_plugin_requires_output_with_input(mock_config: MagicMock) -> None:
    """Verify UsageError is raised if messages-in is provided without output dir."""
    mock_config.option.allure_cucumber_messages_in = "messages.ndjson"
    mock_config.option.allure_cucumber_output_dir = None
    mock_config.getini.return_value = None

    with pytest.raises(pytest.UsageError, match="requires --allure-cucumber-out"):
        pytest_configure(mock_config)


def test_collection_modifyitems_cleared_in_import_mode(mock_config: MagicMock) -> None:
    """Verify scenario collection is cleared when in NDJSON import mode."""
    from pytest_bdd.plugin.allure_cucumber.plugin import CucumberNDJSONImportPlugin

    plugin = CucumberNDJSONImportPlugin(config=mock_config, output_dir="allure-results", messages_in="messages.ndjson")
    items = [MagicMock(), MagicMock()]
    plugin.pytest_collection_modifyitems(items)
    assert len(items) == 0
```

- [x] **Step 4: Run all unit tests**

Run: `python -m pytest tests/cases/unit/allure/ -v --tb=short`
Expected: All pass

- [x] **Step 5: Commit**

```bash
git add tests/cases/unit/allure/test_listener.py tests/cases/unit/allure/test_api_hooks.py tests/cases/unit/allure/test_native_plugin.py
git commit -m "test: update unit tests for pluggy hooks refactor"
```

---

### Task 7: Run full test suite and fix any regressions

**Files:**
- None (verification only)

- [x] **Step 1: Run all allure tests**

Run: `python -m pytest tests/cases/unit/allure/ tests/cases/integration/allure/ -v --tb=short`
Expected: All pass

- [x] **Step 2: Run contract tests**

Run: `python -m pytest tests/cases/contract/allure/ -v --tb=short`
Expected: Same results as before (6 pre-existing failures from xdist/missing test_case_result)

- [x] **Step 3: Final commit if needed**

```bash
git add -A
git commit -m "chore: final cleanup for pluggy hooks refactor"
```
