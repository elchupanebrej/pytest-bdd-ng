"""Shared rules for grouping environment matrix evidence."""

from __future__ import annotations

EXPECTED_JOBS = (
    "full-matrix",
    "browser-report",
    "live-formatters-acceptance",
    "remote",
    "native-go-parser",
    "quality",
)
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
SYSTEM_TOOL_VERSION_KEYS = ("node", "npm", "npx", "allure-cli", "uv", "pandoc", "go", "native-compiler")


def required_optional_versions(tox_environment: str) -> tuple[str, ...]:
    """Return optional packages whose presence is part of this environment's contract."""
    required: list[str] = []
    is_playwright_report = "playwright-report" in tox_environment
    is_doc_generation = "doc-gen" in tox_environment
    if is_doc_generation:
        required.extend(("pandoc", "panflute", "pycmarkgfm", "pypandoc"))
    if "allure" in tox_environment or is_playwright_report:
        required.append("allure-pytest")
    if "gherkin33" in tox_environment or "gherkinlatest" in tox_environment or is_playwright_report:
        required.append("gherkin-official")
    if "playwright" in tox_environment:
        required.append("playwright")
    if "xdist" in tox_environment or is_playwright_report:
        required.append("pytest-xdist")
    return tuple(required)


def required_system_tool_versions(tox_environment: str) -> tuple[str, ...]:
    """Return system tools whose actual versions are part of this environment's contract."""
    if "live-formatters-acceptance" in tox_environment:
        return ("node", "npm", "npx", "allure-cli", "uv")
    if "-coverage-" in tox_environment:
        return ("uv",)
    if "doc-gen" in tox_environment:
        return ("pandoc",)
    if "native-go-parser" in tox_environment:
        return ("go", "native-compiler")
    return ()


def system_tool_version_command(tool: str, platform_name: str) -> tuple[str, tuple[str, ...]]:
    """Return the executable lookup name and arguments used to capture a tool version."""
    commands = {
        "node": ("node", ("--version",)),
        "npm": ("npm", ("--version",)),
        "npx": ("npx", ("--version",)),
        "allure-cli": ("npx", ("--yes", "allure@3.20.0", "--version")),
        "uv": ("uv", ("--version",)),
        "pandoc": ("pandoc", ("--version",)),
        "go": ("go", ("version",)),
        "native-compiler": ("gcc" if platform_name in {"win32", "windows"} else "cc", ("--version",)),
    }
    try:
        return commands[tool]
    except KeyError as error:
        raise ValueError(f"unknown system tool version key {tool!r}") from error


def evidence_group(job: str, tox_environment: str) -> str:
    """Return the proof group assigned to an inventory environment."""
    if tox_environment == "py314-doc-gen":
        return "serial"
    if job == "full-matrix":
        return "parallel" if "xdist" in tox_environment else "serial"
    if job in {"browser-report", "live-formatters-acceptance", "native-go-parser"}:
        return "e2e"
    if job == "remote":
        return "external"
    if job == "quality":
        return "quality"
    raise RuntimeError(f"workflow job {job!r} has no full-proof group")
