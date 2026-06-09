"""Step definitions for CCK Allure Compatibility feature."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from pytest_bdd import given, parsers, then, when
from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.testing.cck import download_cck_sample
from pytest_bdd.testing.docker import require_docker_daemon


@given(parsers.parse('the CCK sample "{name}" is available'))
def cck_sample_available(name: str, tmp_path: Path) -> Path:
    """Download and provide access to a CCK sample NDJSON file."""
    cache_dir = tmp_path / "cck_cache"
    cache_dir.mkdir()
    return download_cck_sample(name, cache_dir)


@given("the allure-cucumber converter processes the sample")
def allure_converter_processes(cck_sample: Path, tmp_path: Path) -> Path:
    """Convert the CCK sample to Allure results."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()
    convert(cck_sample, output_dir)
    return output_dir


@given("the Allure HTML report is generated via Docker")
def allure_html_report_generated(allure_output: Path, tmp_path: Path) -> Path:
    """Generate an Allure HTML report via Docker."""
    from pytest_bdd.testing.docker import ensure_allure3_image

    require_docker_daemon()
    ensure_allure3_image()

    import subprocess  # noqa: S404

    report_dir = tmp_path / "allure-report"
    report_dir.mkdir()

    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "docker",
            "run",
            "--rm",
            "-v",
            f"{allure_output}:/allure-results:ro",
            "-v",
            f"{report_dir}:/allure-report",
            "allure3-local:latest",
            "allure",
            "generate",
            "/allure-results",
            "-o",
            "/allure-report",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, f"Allure Docker command failed: {result.stderr[:500]}"

    index_html = report_dir / "index.html"
    assert index_html.exists(), "Allure report index.html not generated"

    return report_dir


@when("the report is served via HTTP")
def report_served_via_http(allure_report: Path, tmp_path: Path) -> str:
    """Start an HTTP server to serve the Allure report."""
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    class _QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(allure_report), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            _ = (format, args)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Store server reference for cleanup
    tmp_path._http_server = server  # type: ignore[attr-defined]
    tmp_path._http_thread = thread  # type: ignore[attr-defined]

    return f"http://127.0.0.1:{server.server_port}"


@when("the browser navigates to the report")
def browser_navigates_to_report(report_served_via_http: str, tmp_path: Path) -> None:
    """Open the Allure report in a Playwright browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        msg = f"Playwright is required for browser tests but not installed: {exc}"
        raise pytest.fail(msg) from exc

    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not browsers_path:
        if sys.platform == "darwin":
            browsers_path = str(Path.home() / "Library/Caches/ms-playwright")
        elif sys.platform == "linux":
            browsers_path = str(Path.home() / ".cache/ms-playwright")
        else:
            browsers_path = str(Path.home() / "AppData/Local/ms-playwright")

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    page_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda exception: page_errors.append(str(exception)))

        page.goto(f"{report_served_via_http}/index.html", wait_until="load")
        page.wait_for_timeout(2000)

        # Store page for assertions
        tmp_path._playwright_page = page  # type: ignore[attr-defined]
        tmp_path._playwright_browser = browser  # type: ignore[attr-defined]
        tmp_path._page_errors = page_errors  # type: ignore[attr-defined]


@then(parsers.parse('the scenario name "{name}" is visible'))
def scenario_name_visible(name: str, tmp_path: Path) -> None:
    """Assert that a scenario name is visible in the Allure report."""
    page = tmp_path._playwright_page  # type: ignore[attr-defined]

    # Try to find the scenario name in the page content
    content = page.content()
    assert name in content, f"Scenario name '{name}' not found in report"

    # Cleanup
    browser = tmp_path._playwright_browser  # type: ignore[attr-defined]
    browser.close()


@then(parsers.parse('the step "{step}" is visible'))
def step_visible(step: str, tmp_path: Path) -> None:
    """Assert that a step text is visible in the Allure report."""
    page = tmp_path._playwright_page  # type: ignore[attr-defined]

    content = page.content()
    assert step in content, f"Step '{step}' not found in report"

    # Cleanup
    browser = tmp_path._playwright_browser  # type: ignore[attr-defined]
    browser.close()


@then(parsers.parse('the test status "{status}" is visible'))
def test_status_visible(status: str, tmp_path: Path) -> None:
    """Assert that a test status is visible in the Allure report."""
    page = tmp_path._playwright_page  # type: ignore[attr-defined]

    content = page.content()
    # Allure reports typically show status in various ways
    assert status.lower() in content.lower(), f"Status '{status}' not found in report"

    # Cleanup
    browser = tmp_path._playwright_browser  # type: ignore[attr-defined]
    browser.close()

    # Also cleanup HTTP server
    server = tmp_path._http_server  # type: ignore[attr-defined]
    thread = tmp_path._http_thread  # type: ignore[attr-defined]
    server.shutdown()
    thread.join()
    server.server_close()
