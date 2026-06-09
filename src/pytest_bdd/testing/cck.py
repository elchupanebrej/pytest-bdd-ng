"""
Cucumber Compatibility Kit (CCK) download utility.

Provides functions to download CCK sample NDJSON files from the official
cucumber/compatibility-kit repository without cloning the entire repo.
"""

from __future__ import annotations

import base64
import json
import logging
import subprocess  # noqa: S404
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

CCK_REPO = "cucumber/compatibility-kit"
CCK_RELEASE_TAG = "v29.2.2"

CCK_SAMPLE_NAMES: list[str] = [
    "all-statuses",
    "ambiguous",
    "attachments",
    "backgrounds",
    "cdata",
    "data-tables",
    "doc-strings",
    "empty",
    "examples-tables",
    "examples-tables-attachment",
    "examples-tables-undefined",
    "failedish-combinations",
    "global-hooks",
    "global-hooks-afterall-error",
    "global-hooks-attachments",
    "global-hooks-beforeall-error",
    "hooks",
    "hooks-attachment",
    "hooks-conditional",
    "hooks-named",
    "hooks-skipped",
    "hooks-undefined",
    "markdown",
    "minimal",
    "multiple-features",
    "multiple-features-reversed",
    "parameter-types",
    "pending",
    "pending-exception",
    "regular-expression",
    "retry",
    "retry-ambiguous",
    "retry-pending",
    "retry-undefined",
    "rules",
    "rules-backgrounds",
    "skipped",
    "skipped-exception",
    "skipped-failing-hook",
    "stack-traces",
    "test-run-exception",
    "undefined",
    "unknown-parameter-type",
    "unused-steps",
]


def _download_via_gh_api(sample_name: str, tag: str, cache_dir: Path) -> Path | None:
    """
    Download a CCK sample NDJSON file using the gh CLI.

    Returns:
        Path to the downloaded NDJSON file, or None if download failed.

    """
    ndjson_path = cache_dir / f"{sample_name}.ndjson"
    if ndjson_path.exists():
        logger.debug("Using cached CCK sample: %s", ndjson_path)
        return ndjson_path

    url = f"repos/{CCK_REPO}/contents/devkit/samples/{sample_name}/{sample_name}.ndjson?ref={tag}"
    try:
        result = subprocess.run(  # noqa: S603
            ["gh", "api", url, "--jq", ".content"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("gh api download failed for %s: %s", sample_name, exc)
        return None

    if result.returncode != 0:
        logger.warning("gh api failed for %s: %s", sample_name, result.stderr)
        return None

    content = base64.b64decode(result.stdout.strip())
    ndjson_path.write_bytes(content)
    logger.debug("Downloaded CCK sample via gh api: %s", sample_name)
    return ndjson_path


def _download_via_urllib(sample_name: str, tag: str, cache_dir: Path) -> Path | None:
    """
    Download a CCK sample NDJSON file using urllib (fallback).

    Returns:
        Path to the downloaded NDJSON file, or None if download failed.

    """
    ndjson_path = cache_dir / f"{sample_name}.ndjson"
    if ndjson_path.exists():
        logger.debug("Using cached CCK sample: %s", ndjson_path)
        return ndjson_path

    url = f"https://raw.githubusercontent.com/{CCK_REPO}/{tag}/devkit/samples/{sample_name}/{sample_name}.ndjson"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            ndjson_path.write_bytes(content)
            logger.debug("Downloaded CCK sample via urllib: %s", sample_name)
            return ndjson_path
    except (urllib.error.URLError, OSError) as exc:
        logger.warning("urllib download failed for %s: %s", sample_name, exc)
        return None


def download_cck_sample(
    sample_name: str,
    cache_dir: Path,
    tag: str = CCK_RELEASE_TAG,
) -> Path:
    """
    Download a single CCK sample NDJSON file.

    Tries gh API first, falls back to urllib.
    Caches downloads in the provided directory.

    Args:
        sample_name: Name of the CCK sample (e.g., "minimal").
        cache_dir: Directory to cache downloaded files.
        tag: Git tag to download from.

    Returns:
        Path to the downloaded NDJSON file.

    Raises:
        RuntimeError: If download fails via both methods.

    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    path = _download_via_gh_api(sample_name, tag, cache_dir)
    if path is not None:
        return path

    path = _download_via_urllib(sample_name, tag, cache_dir)
    if path is not None:
        return path

    msg = (
        f"Failed to download CCK sample '{sample_name}' via both gh API and urllib. "
        f"Check network connectivity and that tag '{tag}' exists in {CCK_REPO}."
    )
    raise RuntimeError(msg)


def download_all_cck_samples(
    cache_dir: Path,
    tag: str = CCK_RELEASE_TAG,
) -> dict[str, Path]:
    """
    Download all CCK sample NDJSON files.

    Args:
        cache_dir: Directory to cache downloaded files.
        tag: Git tag to download from.

    Returns:
        Dictionary mapping sample names to their file paths.

    """
    samples: dict[str, Path] = {}
    for name in CCK_SAMPLE_NAMES:
        try:
            path = download_cck_sample(name, cache_dir, tag)
            samples[name] = path
        except RuntimeError:  # noqa: PERF203 — intentional per-sample error recovery
            logger.exception("Failed to download CCK sample '%s'", name)
    return samples


def extract_scenario_names(ndjson_path: Path) -> list[str]:
    """
    Extract scenario names from a CCK NDJSON file.

    Parses pickle messages to extract scenario names.

    Args:
        ndjson_path: Path to the NDJSON file.

    Returns:
        List of scenario names found in the file.

    """
    names: list[str] = []
    with Path(ndjson_path).open(encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                envelope = json.loads(line)
                if "pickle" in envelope:
                    pickle_data = envelope["pickle"]
                    if "name" in pickle_data:
                        names.append(pickle_data["name"])
            except json.JSONDecodeError:
                continue
    return names


def extract_step_texts(ndjson_path: Path) -> list[str]:
    """
    Extract step texts from a CCK NDJSON file.

    Parses pickle messages to extract step texts.

    Args:
        ndjson_path: Path to the NDJSON file.

    Returns:
        List of step texts found in the file.

    """
    texts: list[str] = []
    with Path(ndjson_path).open(encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                envelope = json.loads(line)
                if "pickle" in envelope:
                    pickle_data = envelope["pickle"]
                    texts.extend(step.get("text", "") for step in pickle_data.get("steps", []))
            except json.JSONDecodeError:
                continue
    return texts


def extract_expected_status(ndjson_path: Path) -> str:
    """
    Extract the expected test status from a CCK NDJSON file.

    Parses testStepFinished messages to determine the overall status.

    Args:
        ndjson_path: Path to the NDJSON file.

    Returns:
        The expected status string (e.g., "PASSED", "FAILED").

    """
    statuses: list[str] = []
    with Path(ndjson_path).open(encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                envelope = json.loads(line)
                if "testStepFinished" in envelope:
                    result = envelope["testStepFinished"].get("testStepResult", {})
                    status = result.get("status", "UNKNOWN")
                    statuses.append(status)
            except json.JSONDecodeError:
                continue

    if not statuses:
        return "UNKNOWN"
    if any(s == "FAILED" for s in statuses):
        return "FAILED"
    if all(s == "PASSED" for s in statuses):
        return "PASSED"
    return statuses[0] if statuses else "UNKNOWN"
