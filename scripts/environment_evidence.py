"""Shared rules for grouping environment matrix evidence."""

from __future__ import annotations

EXPECTED_JOBS = ("full-matrix", "browser-report", "remote", "native-go-parser", "quality")
EVIDENCE_GROUPS = ("serial", "parallel", "e2e", "external", "quality")
TEST_EVIDENCE_GROUPS = frozenset(("serial", "parallel", "e2e", "external"))
OPTIONAL_VERSION_KEYS = (
    "allure-pytest",
    "gherkin-official",
    "pandoc",
    "panflute",
    "playwright",
    "pycmarkgfm",
    "pypandoc",
    "pytest-xdist",
    "PyYAML",
)
SYSTEM_TOOL_VERSION_KEYS = ("pandoc",)


def required_optional_versions(tox_environment: str) -> tuple[str, ...]:
    """Return optional packages whose presence is part of this environment's contract."""
    required: list[str] = []
    is_playwright_report = "playwright-report" in tox_environment
    is_doc_generation = "doc-gen" in tox_environment
    if is_doc_generation:
        required.extend(("pandoc", "panflute", "pycmarkgfm", "pypandoc"))
    if "allure" in tox_environment or is_playwright_report:
        required.append("allure-pytest")
    if (
        "gherkin33" in tox_environment
        or "gherkinlatest" in tox_environment
        or is_playwright_report
    ):
        required.append("gherkin-official")
    if "playwright" in tox_environment:
        required.append("playwright")
    if "xdist" in tox_environment or is_playwright_report:
        required.append("pytest-xdist")
    return tuple(required)


def required_system_tool_versions(tox_environment: str) -> tuple[str, ...]:
    """Return system tools whose actual versions are part of this environment's contract."""
    if "doc-gen" in tox_environment:
        return ("pandoc",)
    return ()


def evidence_group(job: str, tox_environment: str) -> str:
    """Return the proof group assigned to an inventory environment."""
    if tox_environment == "py314-doc-gen":
        return "serial"
    if job == "full-matrix":
        return "parallel" if "xdist" in tox_environment else "serial"
    if job in {"browser-report", "native-go-parser"}:
        return "e2e"
    if job == "remote":
        return "external"
    if job == "quality":
        return "quality"
    raise RuntimeError(f"workflow job {job!r} has no full-proof group")
