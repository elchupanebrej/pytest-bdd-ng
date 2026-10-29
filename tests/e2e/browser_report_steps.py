"""BDD acceptance steps for opening a generated Allure report in Chromium."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest
from pytest_cuke import given, then, when


_SCENARIO_NAME = "Chromium shows a passed pytest-cuke scenario"
_ALLURE_PYTEST_VERSION = "2.16.2"
_ALLURE_CLI_VERSION = "3.20.0"


@dataclass
class AllureBrowserContext:
    consumer: Any
    scenario_name: str = _SCENARIO_NAME
    result_directory: Path | None = None
    report_directory: Path | None = None
    result_payload: dict[str, Any] | None = None


@dataclass
class BrowserReportInspection:
    scenario_name: str
    browser_title: str
    visible_text: str
    url: str


def _consumer_path(consumer: Any, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("browser-report files must stay inside the consumer project")
    return Path(consumer.path) / path


@given("the consumer installs the pinned Allure pytest adapter")
def consumer_installs_pinned_allure_pytest_adapter(consumer: Any) -> None:
    uv = shutil.which("uv")
    assert uv is not None, (
        "the browser-report contract needs uv to install Allure in its isolated consumer; "
        "install uv before running this lane"
    )
    result = subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(consumer.python),
            f"allure-pytest=={_ALLURE_PYTEST_VERSION}",
        ],
        cwd=consumer.path,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"could not install allure-pytest=={_ALLURE_PYTEST_VERSION} in the report consumer:\n"
        f"{result.stdout}\n{result.stderr}"
    )
    probe = subprocess.run(
        [str(consumer.python), "-c", "import allure_pytest"],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, f"allure-pytest is not importable in the report consumer:\n{probe.stderr}"


@given("the consumer writes a real reportable pytest-cuke scenario", target_fixture="allure_browser_context")
def consumer_writes_reportable_pytest_cuke_scenario(consumer: Any) -> AllureBrowserContext:
    context = AllureBrowserContext(consumer=consumer)
    feature_path = _consumer_path(consumer, "features/report-content.feature")
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(
        "Feature: Browser report content\n"
        "  Scenario: Chromium shows a passed pytest-cuke scenario\n"
        "    Given the report-producing scenario starts\n"
        "    When pytest-cuke records a passing result\n"
        "    Then the report-producing assertion passes\n",
        encoding="utf-8",
    )
    _consumer_path(consumer, "conftest.py").write_text('pytest_plugins = ["report_steps"]\n', encoding="utf-8")
    _consumer_path(consumer, "report_steps.py").write_text(
        "from pytest_cuke import given, then, when\n\n\n"
        "@given('the report-producing scenario starts')\n"
        "def report_producing_scenario_starts():\n"
        "    pass\n\n\n"
        "@when('pytest-cuke records a passing result')\n"
        "def cuke_records_passing_result():\n"
        "    assert 2 + 2 == 4\n\n\n"
        "@then('the report-producing assertion passes')\n"
        "def report_producing_assertion_passes():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    return context


@then("the consumer run should contain one passed Allure scenario result")
def consumer_run_contains_one_passed_allure_result(
    allure_browser_context: AllureBrowserContext,
    pytest_run_result: subprocess.CompletedProcess[str],
) -> None:
    assert pytest_run_result.returncode == 0, (
        f"the real pytest-cuke report-producing run failed:\n{pytest_run_result.stdout}\n{pytest_run_result.stderr}"
    )
    context = allure_browser_context
    result_directory = _consumer_path(context.consumer, "allure-results")
    results = sorted(result_directory.glob("*-result.json"))
    assert len(results) == 1, f"expected one Allure result from the real pytest run, found {results!r}"
    payload = json.loads(results[0].read_text(encoding="utf-8"))
    assert isinstance(payload, dict), payload
    assert payload.get("status") == "passed", payload
    assert context.scenario_name in str(payload.get("name", "")), payload
    context.result_directory = result_directory
    context.result_payload = payload


class _QuietReportHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _visible_scenario_text(page: Any, scenario_name: str) -> str | None:
    scenario = page.get_by_text(scenario_name, exact=False)
    for index in range(scenario.count()):
        item = scenario.nth(index)
        if item.is_visible():
            return item.inner_text()
    return None


def _open_browser_report(report_directory: Path, scenario_name: str) -> BrowserReportInspection:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        pytest.fail(
            "the browser-report lane requires the Playwright Python package; "
            "install pytest-cuke[test-playwright] in the tox environment",
            pytrace=False,
        )
        raise AssertionError from error

    index_path = report_directory / "index.html"
    assert index_path.is_file(), f"Allure report has no index.html entry point: {report_directory}"
    handler = partial(_QuietReportHandler, directory=str(report_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    report_url = f"http://127.0.0.1:{server.server_port}/index.html"
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as error:
                pytest.fail(
                    "Playwright Chromium is unavailable for the browser-report lane. "
                    "Install the browser binaries with `python -m playwright install --with-deps chromium`. "
                    f"Launch error: {error}",
                    pytrace=False,
                )
            try:
                page = browser.new_page()
                response = page.goto(report_url, wait_until="networkidle", timeout=60_000)
                assert response is not None and response.ok, (
                    f"Playwright could not open the generated Allure report at {report_url}: {response}"
                )
                page.locator("body").wait_for(state="visible", timeout=30_000)
                page.wait_for_function(
                    "document.body !== null && document.body.innerText.trim().length > 0",
                    timeout=30_000,
                )
                expand_all = page.get_by_role("button", name=re.compile(r"^expand all$", re.IGNORECASE))
                if expand_all.count() and expand_all.first.is_visible():
                    expand_all.first.click()
                visible_scenario = _visible_scenario_text(page, scenario_name)
                if visible_scenario is None:
                    for label in ("Suites", "Tests", "Behaviors"):
                        navigation_item = page.get_by_text(label, exact=True)
                        if navigation_item.count() == 0:
                            continue
                        navigation_item.first.click()
                        try:
                            page.get_by_text(scenario_name, exact=False).first.wait_for(
                                state="visible",
                                timeout=10_000,
                            )
                        except Exception:
                            continue
                        visible_scenario = _visible_scenario_text(page, scenario_name)
                        if visible_scenario is not None:
                            break
                body_text = page.locator("body").inner_text()
                assert visible_scenario is not None, (
                    f"the Allure report opened at {page.url}, but Chromium did not render scenario "
                    f"{scenario_name!r} as visible text. Visible page excerpt: {body_text[:3000]!r}"
                )
                return BrowserReportInspection(
                    scenario_name=scenario_name,
                    browser_title=page.title(),
                    visible_text=body_text,
                    url=page.url,
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


@when(
    "I render the real Allure report and review it in Playwright Chromium",
    target_fixture="allure_browser_inspection",
)
def render_and_review_allure_report(
    allure_browser_context: AllureBrowserContext,
) -> BrowserReportInspection:
    context = allure_browser_context
    assert context.result_directory is not None, "the real pytest run must produce Allure results before rendering"
    npx = shutil.which("npx")
    assert npx is not None, (
        "the browser-report lane requires Node.js and npm's npx command to run the pinned Allure 3 renderer; "
        "install Node.js/npm so `npx --yes allure@3.20.0` is available"
    )
    report_directory = _consumer_path(context.consumer, "allure-report")
    result = subprocess.run(
        [
            npx,
            "--yes",
            f"allure@{_ALLURE_CLI_VERSION}",
            "generate",
            str(context.result_directory),
            "-o",
            str(report_directory),
        ],
        cwd=context.consumer.path,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"Allure {_ALLURE_CLI_VERSION} could not generate HTML from the real pytest results:\n"
        f"{result.stdout}\n{result.stderr}"
    )
    rendered_files = [path for path in report_directory.rglob("*.html") if path.is_file() and path.stat().st_size]
    assert rendered_files, f"Allure {_ALLURE_CLI_VERSION} generated no non-empty HTML under {report_directory}"
    context.report_directory = report_directory
    return _open_browser_report(report_directory, context.scenario_name)


@then("Chromium should display the passed pytest-cuke scenario in the rendered report")
def chromium_displays_passed_pytest_cuke_scenario(
    allure_browser_context: AllureBrowserContext,
    allure_browser_inspection: BrowserReportInspection,
) -> None:
    assert allure_browser_context.result_payload is not None, "the report must originate from the real pytest run"
    assert allure_browser_inspection.scenario_name in allure_browser_inspection.visible_text
    assert re.search(r"\bpassed\b", allure_browser_inspection.visible_text, flags=re.IGNORECASE), (
        "Chromium opened the report, but its visible DOM did not show the passed result status. "
        f"Visible page excerpt: {allure_browser_inspection.visible_text[:3000]!r}"
    )
    assert allure_browser_inspection.url.startswith("http://127.0.0.1:"), allure_browser_inspection
