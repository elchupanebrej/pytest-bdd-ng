# How to Create a Custom Formatter Plugin

## Problem

You need a custom output format — Slack notifications, Datadog metrics, a
custom dashboard, or simply a different console layout — that isn't
covered by the 13 built-in formatter plugins (cucumber-json, cucumber-junit,
cucumber-pretty, cucumber-progress, cucumber-usage, etc.).

## Solution

Create a plugin package following the **ADR-003 three-file pattern**
(``entrypoint.py`` + ``hook.py`` + ``plugin.py``) and subscribe to
pytest-bdd hooks to capture scenario and step lifecycle events.

### 1. Understand the Cucumber Messages Protocol

All formatters in pytest-bdd-ng operate on the **Cucumber Messages**
protocol — a stream of ``Envelope`` messages serialized as NDJSON (each
message is a single JSON line on its own line). Relevant envelope types:

| Envelope Type | Description |
|---------------|-------------|
| ``TestRunStarted`` | Emitted at the start of the test run. |
| ``TestRunFinished`` | Emitted at the end of the test run. |
| ``TestCaseStarted`` | Emitted before each scenario. |
| ``TestCaseFinished`` | Emitted after each scenario. |
| ``TestStepStarted`` | Emitted before each step. |
| ``TestStepFinished`` | Emitted after each step. |

Envelopes are consumed from a ``Queue`` in the live formatter process and
rendered by JavaScript formatter adapters. However, for Python-only custom
formatters you don't need JavaScript — you can subscribe directly to
pytest-bdd hooks.

### 2. Create a Plugin Package (ADR-003 Pattern)

Every plugin has three files:

**``entrypoint.py``** — instantiates the plugin class and registers it:

```python
from .plugin import SlackNotifierPlugin

slack_notifier_plugin = SlackNotifierPlugin()
```

**``hook.py``** — placeholder for hook specifications (optional for custom
formatters):

```python
"""
Hook specifications for the Slack notifier plugin.

This module is a canonical package-structure placeholder.
"""
```

**``plugin.py``** — the core plugin class with hook implementations:

```python
from __future__ import annotations

import json
import urllib.request
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


class SlackNotifierPlugin:
    """Send scenario results to a Slack webhook."""

    plugin_name = "slack-notifier"

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url
        self.scenarios: list[dict] = []

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_after_scenario(self, request, run):
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            return

        status = "passed"
        if scenario_run.is_failed:
            status = "failed"
        elif scenario_run.status and scenario_run.status.name == "skipped":
            status = "skipped"

        self.scenarios.append({
            "name": scenario_run.name,
            "status": status,
            "duration_ms": scenario_run.duration_ms,
        })

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
        """Post summary to Slack after all scenarios complete."""
        if not self.webhook_url or not self.scenarios:
            return

        passed = sum(1 for s in self.scenarios if s["status"] == "passed")
        failed = sum(1 for s in self.scenarios if s["status"] == "failed")
        total = len(self.scenarios)

        payload = {
            "text": (f"BDD Test Run Complete: {passed}/{total} passed, {failed} failed"),
            "attachments": [
                {
                    "title": s["name"],
                    "text": f"{s['status']} — {s['duration_ms']:.0f}ms",
                    "color": "good" if s["status"] == "passed" else "danger",
                }
                for s in self.scenarios
            ],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)  # noqa: S310 — webhook URL is user-provided

    @pytest.hookimpl(trylast=True)
    def pytest_addoption(self, parser):
        parser.addoption(
            "--slack-webhook",
            action="store",
            default=None,
            help="Slack webhook URL for BDD test result notifications",
        )

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config):
        webhook = config.getoption("--slack-webhook", default=None)
        self.webhook_url = webhook
```

### 3. Available pytest-bdd Hooks

The following hooks are available for formatter plugins:

| Hook | When Called | Signature |
|------|------------|-----------|
| ``pytest_bdd_before_scenario`` | Before each scenario | ``(request, run, gherkin_document, pickle)`` |
| ``pytest_bdd_after_scenario`` | After each scenario | ``(request, run, gherkin_document, pickle)`` |
| ``pytest_bdd_before_step`` | Before each step | ``(request, run, ...)`` |
| ``pytest_bdd_after_step`` | After each step | ``(request, run, ...)`` |
| ``pytest_bdd_step_error`` | When a step fails | ``(request, run, ..., exception)`` |
| ``pytest_bdd_step_func_lookup_error`` | When no step definition is found | ``(request, run, ..., exception)`` |
| ``pytest_bdd_run_scenario`` | Scenario execution entry point | ``(request, run)`` |

Access the current scenario run through ``run.active_scenario_run``, which
provides:

* ``.name`` — scenario name
* ``.is_failed`` — whether the scenario has failed
* ``.status`` — ``RunStatus`` enum (``passed``, ``failed``, ``skipped``,
  ``pending``, ``undefined``)
* ``.duration_ms`` — execution time in milliseconds
* ``.step_run`` — current step run (available during step hooks)

### 4. Register the Plugin as a pytest11 Entry Point

Add to ``pyproject.toml``:

```toml
[project.entry-points.pytest11]
"pytest-bdd-slack-notifier" = "pytest_bdd.plugin.slack_notifier.entrypoint:slack_notifier_plugin"
```

Or, for local plugins, register in ``conftest.py``:

```python
import pytest


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    config.pluginmanager.register(SlackNotifierPlugin(webhook_url=config.getoption("--slack-webhook")))
```

### 5. Output and NDJSON Envelope Framing

If your formatter needs to integrate with the live formatter bridge (for
output that appears during test execution, not just at session end), produce
Cucumber Messages envelopes as NDJSON:

```python
from cucumber_messages import Envelope, TestCase, TestCaseStarted, Timestamp
from uuid import uuid4

envelope = Envelope(
    test_case_started=TestCaseStarted(
        id=str(uuid4()),
        test_case=TestCase(id="scenario-1"),
        timestamp=Timestamp(seconds=0, nanos=0),
    )
)
# Write as one JSON line per message
json_line = envelope.to_json() + "\n"
```

## Complete Example

Directory structure for a Slack notifier plugin:

```text
src/pytest_bdd/plugin/slack_notifier/
    __init__.py
    entrypoint.py
    hook.py
    plugin.py
```

Full ``plugin.py`` as shown in section 2 above. Install and run:

```bash
pytest --slack-webhook https://hooks.slack.com/services/XXX/YYY/ZZZ
```

The plugin collects scenario results during execution and posts a summary
to Slack when the test session finishes.

## Common Mistakes

**Trying to import formatter internals from other plugins.** This triggers the
BLQ1002 ruff rule (cross-plugin import violation). Each plugin is a
self-contained package. Use pytest-bdd hooks instead of importing
``GherkinMessageReporter``, ``PickleRunner``, or other internal classes.

**Not handling the xdist case.** When running with ``pytest -n auto``,
formatter plugins execute on every worker. If your plugin writes to a
shared file or sends HTTP requests without deduplication, you get duplicate
output. Handle xdist by:

1. Implementing ``pytest_configure_node`` to pass configuration to workers.
2. Using ``pytest_sessionfinish`` (controller-only) for final output.
3. Checking ``hasattr(config, "workerinput")`` to detect worker vs.
   controller context:

   ```python
   def pytest_configure(self, config):
       is_worker = hasattr(config, "workerinput")
       if is_worker:
           return  # Skip setup on workers
   ```

**Missing NDJSON envelope framing.** If you output Cucumber Messages
directly, each message must be a single JSON line terminated by ``\n``.
Multi-line JSON or missing newlines break downstream consumers (the
``@cucumber/html-formatter``, CI dashboards, etc.).

**Not using ``trylast=True`` on hook wrappers.** If you want your formatter
to run after all other plugins have processed the event (so you see final
state), use ``@pytest.hookimpl(trylast=True)``. Without it, your hook may
run before step matching or error handling completes, giving you incomplete
data.

**Forgetting to handle skipped scenarios.** Scenarios can be skipped by
``pytest.skip()`` in step definitions or by tag filters. In
``pytest_bdd_after_scenario``, check ``scenario_run.status is None`` before
accessing ``scenario_run.is_failed`` to avoid ``AttributeError``.
