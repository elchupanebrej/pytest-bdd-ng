"""Shared fixtures for CCK (Cucumber Compatibility Kit) Allure compatibility tests.

Provides session-scoped CCK sample downloading, NDJSON-to-Allure conversion,
Docker-based report generation, and Playwright browser validation helpers.
"""

from __future__ import annotations

import os
import subprocess  # noqa: S404
import sys
from collections.abc import Generator
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.testing.cck import (
    CCK_RELEASE_TAG,
    download_all_cck_samples,
    extract_scenario_names,
    extract_step_texts,
)
from pytest_bdd.testing.docker import ensure_allure3_image, require_docker_daemon

ALLURE_DOCKER_IMAGE = "allure3-local:latest"


@pytest.fixture(scope="session")
def cck_samples_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped directory for all CCK sample downloads."""
    return tmp_path_factory.mktemp("cck_samples")


@pytest.fixture(scope="session")
def cck_samples(cck_samples_dir: Path) -> dict[str, Path]:
    """Session-scoped download of all CCK sample NDJSON files."""
    return download_all_cck_samples(cck_samples_dir, CCK_RELEASE_TAG)


@pytest.fixture
def cck_sample_name() -> str:
    """Name of the CCK sample being tested.

    Override this fixture to test a specific sample.
    """
    return "minimal"


@pytest.fixture
def cck_sample(cck_samples: dict[str, Path], cck_sample_name: str) -> Path:
    """Path to a single CCK sample NDJSON file."""
    if cck_sample_name not in cck_samples:
        pytest.skip(f"CCK sample '{cck_sample_name}' not available")
    return cck_samples[cck_sample_name]


@pytest.fixture
def allure_output(tmp_path: Path, cck_sample: Path) -> Path:
    """Convert a CCK sample to Allure results."""
    output = tmp_path / "allure-results"
    output.mkdir()
    convert(cck_sample, output)
    return output


def _run_allure_docker(allure_results: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run Allure report generation via Docker."""
    return subprocess.run(  # noqa: S603
        [  # noqa: S607
            "docker",
            "run",
            "--rm",
            "-v",
            f"{allure_results}:/allure-results:ro",
            "-v",
            f"{output_dir}:/allure-report",
            ALLURE_DOCKER_IMAGE,
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


@pytest.fixture
def allure_report(allure_output: Path, tmp_path: Path) -> Path:
    """Generate an Allure HTML report via Docker."""
    require_docker_daemon()
    ensure_allure3_image()
    report_dir = tmp_path / "allure-report"
    report_dir.mkdir()

    result = _run_allure_docker(allure_output, report_dir)

    assert result.returncode == 0, f"Allure Docker command failed: {result.stderr[:500]}"

    index_html = report_dir / "index.html"
    assert index_html.exists(), "Allure report index.html not generated"

    return report_dir


def _resolve_playwright_browsers_path() -> Path | None:
    """Resolve Playwright browser installation path."""
    configured_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if configured_path and configured_path != "0":
        path = Path(configured_path)
        return path if path.exists() else None

    if os.name == "posix":
        import pwd

        user_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        if sys.platform == "darwin":
            path = user_home / "Library/Caches/ms-playwright"
        else:
            path = user_home / ".cache/ms-playwright"
        return path if path.exists() else None

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        path = Path(user_profile) / "AppData/Local/ms-playwright"
        return path if path.exists() else None
    return None


@contextmanager
def _serve_directory(directory: Path) -> Generator[str, None, None]:
    """Serve a directory over HTTP on a random port.

    Yields:
        The base URL of the HTTP server.
    """

    class _QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            _ = (format, args)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.fixture
def serve_directory():
    """Fixture that provides the _serve_directory context manager."""
    return _serve_directory


@pytest.fixture
def scenario_names(cck_sample: Path) -> list[str]:
    """Extract scenario names from the CCK sample."""
    return extract_scenario_names(cck_sample)


@pytest.fixture
def step_texts(cck_sample: Path) -> list[str]:
    """Extract step texts from the CCK sample."""
    return extract_step_texts(cck_sample)
