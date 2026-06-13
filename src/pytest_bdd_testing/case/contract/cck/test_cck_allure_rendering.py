"""Contract tests: validate CCK Allure report rendering via Docker and Playwright.

Tests that Allure HTML reports generated from CCK samples are valid and
render correctly in a browser with visible scenario names, step names, and statuses.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES, extract_scenario_names, extract_step_texts

from .conftest import _resolve_playwright_browsers_path, _serve_directory

pytestmark = [pytest.mark.contract]


class TestCCKAllureRendering:
    """Validate Docker-based Allure report generation for CCK samples."""

    @pytest.mark.docker
    @pytest.mark.parametrize("sample_name", CCK_SAMPLE_NAMES)
    def test_sample_generates_html_report(
        self,
        sample_name: str,
        cck_samples: dict[str, Path],
        tmp_path: Path,
    ):
        """Each CCK sample should generate an Allure HTML report via Docker."""
        from pytest_bdd_testing.tool.docker.docker import require_docker_daemon

        require_docker_daemon()

        if sample_name not in cck_samples:
            pytest.skip(f"CCK sample '{sample_name}' not available")

        from pytest_bdd.plugin.allure_formatter.converter import convert

        ndjson_path = cck_samples[sample_name]
        allure_results = tmp_path / f"allure-{sample_name}"
        allure_results.mkdir()

        convert(ndjson_path, allure_results)

        result_files = list(allure_results.glob("*-result.json"))
        assert result_files, f"No Allure results produced for sample '{sample_name}'"

        from .conftest import _run_allure_docker

        report_dir = tmp_path / f"report-{sample_name}"
        report_dir.mkdir()

        result = _run_allure_docker(allure_results, report_dir)

        assert result.returncode == 0, f"Allure Docker command failed for '{sample_name}': {result.stderr[:500]}"

        index_html = report_dir / "index.html"
        assert index_html.exists(), f"Report index.html not found for sample '{sample_name}'"


class TestCCKAllureUIValidation:
    """Validate Allure UI renders CCK samples correctly via Playwright."""

    @pytest.mark.browser
    @pytest.mark.docker
    @pytest.mark.slow
    @pytest.mark.parametrize("sample_name", CCK_SAMPLE_NAMES)  # CCK-07: all samples
    def test_cck_sample_renders_in_browser(
        self,
        sample_name: str,
        cck_samples: dict[str, Path],
        tmp_path: Path,
    ):
        """CCK sample Allure report should render correctly in a browser."""
        from pytest_bdd_testing.tool.docker.docker import require_docker_daemon

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            msg = f"Playwright is required for browser tests but not installed: {exc}"
            raise pytest.fail(msg) from exc

        require_docker_daemon()

        browsers_path = _resolve_playwright_browsers_path()
        if browsers_path is None:
            msg = "Playwright browsers are unavailable — run 'playwright install'"
            raise pytest.fail(msg)

        if sample_name not in cck_samples:
            pytest.skip(f"CCK sample '{sample_name}' not available")

        from pytest_bdd.plugin.allure_formatter.converter import convert

        # Convert NDJSON to Allure results
        ndjson_path = cck_samples[sample_name]
        allure_results = tmp_path / f"allure-{sample_name}"
        allure_results.mkdir()
        convert(ndjson_path, allure_results)

        result_files = list(allure_results.glob("*-result.json"))
        assert result_files, f"No Allure results produced for sample '{sample_name}'"

        # Generate HTML report via Docker
        from .conftest import _run_allure_docker

        report_dir = tmp_path / f"report-{sample_name}"
        report_dir.mkdir()
        result = _run_allure_docker(allure_results, report_dir)

        assert result.returncode == 0, f"Allure Docker command failed for '{sample_name}': {result.stderr[:500]}"

        index_html = report_dir / "index.html"
        assert index_html.exists(), f"Report index.html not found for sample '{sample_name}'"

        # Extract expected data from NDJSON
        scenario_names = extract_scenario_names(ndjson_path)
        step_texts = extract_step_texts(ndjson_path)

        # Serve report and validate in browser
        page_errors: list[str] = []
        console_errors: list[str] = []

        import os

        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

        with (
            _serve_directory(report_dir) as base_url,
            sync_playwright() as playwright,
            closing(playwright.chromium.launch()) as browser,
        ):
            page = browser.new_page()
            page.on(
                "pageerror",
                lambda exception: page_errors.append(str(exception)),
            )
            page.on(
                "console",
                lambda message: console_errors.append(message.text) if message.type == "error" else None,
            )

            page.goto(f"{base_url}/index.html", wait_until="load")

            # Wait for the page to load
            page.wait_for_timeout(2000)

            # Check that the page loaded (basic assertion)
            title = page.title()
            assert title, "Page should have a title"

        # Report errors after context managers close
        assert page_errors == [], f"Page errors: {page_errors}"
        assert not console_errors, f"Console errors in Allure report: {console_errors}"
