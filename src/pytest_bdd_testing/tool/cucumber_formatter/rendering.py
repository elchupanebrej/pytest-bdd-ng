"""
`pytest_bdd.cucumber_formatters.rendering` — Fake Node.js runtime materialization and cucumber formatter runtime
rendering pipeline for test infrastructure, owning template loading, shim generation, and live formatter asset
rendering.

Responsibility:
    This module owns the complete fake Node.js runtime materialization and cucumber formatter runtime rendering pipeline
    for the test infrastructure. It is the single source of truth for: (a) the `_FAKE_FORMATTER_OUTPUTS` dictionary that
    defines the expected stdout output for each fake formatter type (summary, progress, progress-bar, snippets, pretty,
    usage, json, junit, usage-json); (b) the template-loading and string-replacement rendering helpers that load
    Jinja2-style templates from the `pytest_bdd_testing/test_data/templates/cucumber_formatters/` package resource
    directory; (c) the fake-node binary generation that creates executable Python shims (`node`, `npm`, `node.cmd`,
    `npm.cmd`) in a temp directory, along with a fake `node_modules` tree containing stub `package.json` files for
    preinstalled packages and optionally fake HTML formatter assets (main.js, main.css, index.mustache.html); (d) the
    live formatter runtime rendering that discovers formatter plugins via `FormatterPluginCatalog`, builds
    `CucumberFormatterRequest` objects, renders per-plugin runtime assets to the filesystem, and returns the entry-point
    script path and payload specs; and (e) the top-level `install_fake_node` convenience function that materializes the
    fake runtime and monkeypatches PATH, NODE_PATH, FAKE_GLOBAL_NODE_MODULES_ROOT, and PYTEST_BDD_FAKE_NODE_CAPTURE_DIR
    into the process environment.

Reason for existence:
    This module is kept separate from `registry` because it exclusively owns filesystem-level operations (template
    loading, directory creation, file writing, executable permission setting, Windows .cmd shim generation) and imports
    from `shutil`, `stat`, `pytest_bdd.compatibility.importlib.resources.files`,
    `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterRequest`, and
    `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog` — heavyweight dependencies that the
    process-orchestration module (registry) does not share. Merging rendering into registry would create a ~1400-line
    module spanning two unrelated operational domains (subprocess management + filesystem simulation) with no shared
    control flow or state. The module also serves as the authoritative owner of the fake formatter output contract: the
    `_FAKE_FORMATTER_OUTPUTS` dict is defined here because it is the expected output of the fake node runtime that this
    module materializes, creating a natural co-location of the simulation and its expected behavior.

Delegates:
    - `pytest_bdd.compatibility.importlib.resources.files("pytest_bdd_testing")`: Provides access to the
    `resource/templates/cucumber_formatters/` directory as a traversable package resource, used by
    `_load_support_template` to read Jinja2-style template files bundled with the package.
    - `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterRequest`: The typed request object used by
    `materialize_live_formatter_runtime` to construct per-formatter requests from plugin metadata; each request carries
    option_attr, cli_flag, formatter, package_name, output_path, plugin_module, runtime_kind, runtime_specifier,
    runtime_module_path, runtime_export_name, runtime_template_name, and discovery_order.
    - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog`: Discovered by both
    `materialize_live_formatter_runtime` and `materialize_fake_node_runtime` (indirectly via the preinstalled_packages
    default) to resolve which formatter plugins exist, their metadata, and their runtime rendering capabilities.
    - `_load_support_template`: Reads a raw template file from the package resources; used by `_render_support_template`.
    - `_render_support_template`: Loads a template and performs string replacements for the given placeholder dict; used
    by `materialize_fake_node_runtime` to render `fake_node_runtime.py.j2` and `fake_npm_runtime.py.j2` with the
    `_FAKE_FORMATTER_OUTPUTS` dictionary injected.
    - `_fake_node_python_executable`: Resolves which Python executable to use in fake-node shim scripts; handles the
    PYTEST_BDD_FAKE_NODE_PYTHON override and the PyPy edge case where `sys.executable` may be a PyPy-specific binary
    that doesn't support CPython-compatible invocation.
    - `_write_windows_command_shim`: Creates a Windows `.cmd` batch file that proxies to the Python shim, ensuring
    `node` and `npm` commands work on Windows via the fake runtime.
    - `_write_fake_html_formatter_assets`: Creates stub dist/ and src/ files for the `@cucumber/html-formatter` package
    when it is included in `preinstalled_packages`.

Cohesion:
    Every function in this module contributes to the single goal of "materialize a fake Node.js / cucumber formatter
    runtime on disk that behaves deterministically without requiring real Node.js." The template helpers
    (`_load_support_template`, `_render_support_template`) feed into the fake-node binary generation
    (`materialize_fake_node_runtime`). The Python-executable resolution (`_fake_node_python_executable`) feeds into both
    the fake-node scripts and the Windows shims (`_write_windows_command_shim`). The HTML formatter asset writer
    (`_write_fake_html_formatter_assets`) is a specialization of the fake-modules setup within
    `materialize_fake_node_runtime`. The live formatter runtime renderer (`materialize_live_formatter_runtime`) shares
    the same `FormatterPluginCatalog` discovery and template-writing patterns but targets the real cucumber formatter
    runtime protocol rather than the fake-node simulation. The `install_fake_node` function composes
    `materialize_fake_node_runtime` with `monkeypatch` calls to provide a one-step setup. There are no unrelated
    utilities or bag-of-functions patterns — every function is on the critical path from "no runtime" to "fake runtime
    ready."

Separation:
    - `registry`: Kept separate because it owns subprocess execution, assertion logic, CLI-argument inspection, coverage
    suspension, and telemetry reading — all of which operate above the filesystem-simulation layer. Registry imports
    rendering only via a deferred local import for `_FAKE_FORMATTER_OUTPUTS`; rendering never imports registry.
    - `__init__`: Kept separate because it is a pure re-export facade; rendering is one of the two backing modules it
    delegates to.
    - `pytest_bdd.plugin.gherkin_message_reporter`: Kept separate because it is the production formatter bridge plugin;
    rendering is the test-only simulation layer that mimics its runtime behavior.

Main consumers:
    - `pytest_bdd_testing.cucumber_formatters.__init__`: Re-exports `install_fake_node`,
    `materialize_fake_node_runtime`, and `materialize_live_formatter_runtime`.
    - `pytest_bdd_testing.cucumber_formatters.registry`: Uses `_FAKE_FORMATTER_OUTPUTS` via a deferred import in
    `expected_formatter_output`.
    - `pytest_bdd_testing.cases.e2e.conftest`: Imports `install_fake_node` for the e2e fixture setup.
    - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Uses `install_fake_node` for the core formatter
    integration tests.
    - `pytest_bdd_testing.cases.contract.contract.test_formatter_golden_parity`: Imports `install_fake_node` for golden-
    output parity testing.
    - `pytest_bdd_testing.cases.integration.hook.test_live_formatter_terminal_layout`: Imports
    `materialize_live_formatter_runtime` for live formatter terminal layout tests.
    - `pytest_bdd_testing.cases.compat.compatibility.test_render_cucumber_formatters`: Imports
    `materialize_live_formatter_runtime` for compatibility tests.
    - `pytest_bdd_testing.cases.external.support.test_docker_wsl2`: Imports `materialize_fake_node_runtime` for
    Docker/WSL2 test support.
    - `pytest_bdd_testing.e2e.cucumber_formatter_support`: Re-exports `install_fake_node` and
    `materialize_fake_node_runtime`.

State and side effects:
    The module defines three module-level constants (`_FAKE_FORMATTER_OUTPUTS`, `_REPO_ROOT`, `_TEMPLATE_RESOURCE_DIR`)
    that are computed once at import time and never mutated. `materialize_fake_node_runtime` creates directories and
    writes files (Python scripts, package.json stubs, .cmd shims, HTML formatter assets) under the given `root_path`.
    `materialize_live_formatter_runtime` creates directories and writes rendered runtime asset files under `root_path`.
    `install_fake_node` calls `materialize_fake_node_runtime` and then mutates the process environment via
    `monkeypatch.setenv` (scoped to the test duration). `_write_windows_command_shim` writes `.cmd` files. No network
    I/O, no pytest stash access.

Invariants:
    - `_FAKE_FORMATTER_OUTPUTS` must contain an entry for every formatter name that the fake node runtime's
    `--formatter` flag accepts; the keys are the formatter names used in test assertions and must match the names in
    `FormatterPluginCatalog`.
    - `_REPO_ROOT` is computed as `Path(__file__).resolve().parents[4]` and must resolve to the repository root; this is
    coupled to the directory depth of this file under `src/pytest_bdd_testing/tool/cucumber_formatter/`.
    - `_TEMPLATE_RESOURCE_DIR` must point to the `resource/templates/cucumber_formatters/` directory inside the
    `pytest_bdd_testing` package; templates placed there are loaded by name without path prefixes.
    - The fake node runtime shim scripts (`fake_node_runtime.py.j2`, `fake_npm_runtime.py.j2`) must accept the
    `__FORMATTER_OUTPUTS__` replacement placeholder, which receives the `repr()` of `_FAKE_FORMATTER_OUTPUTS`.
    - `_fake_node_python_executable` must return a Python executable that can run the fake node shim scripts; on PyPy,
    it falls back to a system `python` if the resolved path differs from `sys.executable`.
    - Windows `.cmd` shims must be created alongside the Unix shims when the platform supports `.cmd` execution; the
    shim writes a batch file that invokes the Python executable with the target script path and forwards all arguments.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRequest,
)
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

_FAKE_FORMATTER_OUTPUTS = {
    "summary": "Summary: 2 scenarios (1 passed, 1 failed)\n",
    "progress": "Progress: .F\n",
    "progress-bar": "Progress bar: .[##########] 2/2\n",
    "snippets": (
        "Snippet suggestion: missing step definition\n@given('an undefined step')\ndef an_undefined_step():\n    ...\n"
    ),
    "pretty": "Feature: formatter coverage\n  Scenario: passing scenario\n  Scenario: failing scenario\n",
    "usage": "Usage: Given a passing step x1; Given a failing step x1\n",
    "json": 'JSON formatter payload\n{"formatter": "json", "passed": 1, "failed": 1}\n',
    "junit": (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuite name="pytest-bdd-ng" tests="2" failures="1">\n'
        '  <testcase name="passing scenario" classname="formatter_suite"/>\n'
        '  <testcase name="failing scenario" classname="formatter_suite">\n'
        '    <failure message="boom">RuntimeError: boom</failure>\n'
        "  </testcase>\n"
        "</testsuite>\n"
    ),
    "usage-json": (
        '{"formatter": "usage-json", "steps": [{"text": "Given a passing step", "count": 1}, '
        '{"text": "Given a failing step", "count": 1}]}\n'
    ),
}

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE_RESOURCE_DIR = files("pytest_bdd_testing").joinpath("resource", "templates", "cucumber_formatters")


def _load_support_template(template_name: str) -> str:
    """
    `rendering._load_support_template` — Reads a named template file from the package resource directory and returns its
    contents as a UTF-8 string.

    Responsibility:
        Reads a named template file from the `pytest_bdd_testing/test_data/templates/cucumber_formatters/` package
        resource directory and returns its contents as a UTF-8 string. This is the raw template loader — it performs no
        string replacement or rendering. Template files (e.g., `fake_node_runtime.py.j2`, `fake_npm_runtime.py.j2`)
        contain `__PLACEHOLDER__` markers that are resolved by the caller (`_render_support_template`).

    Reason for existence:
        This function isolates the package-resource access protocol (using
        `pytest_bdd.compatibility.importlib.resources.files` with `joinpath` and `read_text`) so that template consumers
        don't need to know the resource directory structure or the encoding. If the template storage mechanism changes
        (e.g., to a different directory or to in-memory templates), only this function needs updating.

    Delegates:
        - `_TEMPLATE_RESOURCE_DIR.joinpath(template_name)`: Resolves the template file path within the package resource
        directory.
        - `.read_text(encoding="utf-8")`: Reads the file content as a UTF-8 string.

    Cohesion:
        Single-expression function performing one operation: read a file from the template resource directory. Fully cohesive.

    Separation:
        - `_render_support_template`: Kept separate because it adds the string-replacement step on top of the raw
        template loaded by this function.

    Main consumers:
        - `_render_support_template`: Calls `_load_support_template(template_name)` as the first step of template rendering.

    State and side effects:
        Reads a file from the package resource directory (bundled with the installed package). No writes, no network
        I/O, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return str(_TEMPLATE_RESOURCE_DIR.joinpath(template_name).read_text(encoding="utf-8"))


def _render_support_template(template_name: str, *, replacements: dict[str, str] | None = None) -> str:
    """
    `rendering._render_support_template` — Loads a template by name and performs string replacements for each key-value
    pair in the replacements dict.

    Responsibility:
        Loads a template by name from the package resource directory and performs simple string replacements for each
        key-value pair in the `replacements` dict. This is a minimal template renderer — it uses `str.replace` on
        placeholder strings rather than a full template engine like Jinja2, because the templates only need to
        substitute one or two well-known placeholders (e.g., `__FORMATTER_OUTPUTS__`). If no replacements are provided,
        the raw template is returned unmodified.

    Reason for existence:
        This function composes template loading and placeholder substitution into a single call so that consumers
        (`materialize_fake_node_runtime`) don't need to sequence two operations. It also provides a clear semantic
        boundary: "render a support template" means "load and substitute placeholders." If a more sophisticated template
        engine is ever needed, only this function changes.

    Delegates:
        - `_load_support_template`: Called to read the raw template file content as a UTF-8 string.

    Cohesion:
        This function performs two tightly related steps (load + replace) that together constitute "template rendering."
        No unrelated logic.

    Separation:
        - `_load_support_template`: Kept separate because it is the raw loader; this function adds the replacement step.
        - `materialize_fake_node_runtime`: Kept separate because it calls this function with specific template names and
        replacements; this function is the generic renderer.

    Main consumers:
        - `materialize_fake_node_runtime`: Calls `_render_support_template("fake_node_runtime.py.j2",
        replacements={...})` and `_render_support_template("fake_npm_runtime.py.j2")` to produce the fake node and npm
        shim scripts.

    State and side effects:
        Reads a template file from the package resource directory (via `_load_support_template`). No writes, no network
        I/O, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    rendered = _load_support_template(template_name)
    if not replacements:
        return rendered
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def _fake_node_python_executable() -> str:
    """
    `rendering._fake_node_python_executable` — Determines the Python executable to embed in fake node/npm shims,
    respecting PYTEST_BDD_FAKE_NODE_PYTHON override and PyPy fallback.

    Responsibility:
        Determines which Python executable to embed in the fake node and npm shim scripts (both the Unix Python scripts
        and the Windows .cmd wrappers). The resolution logic is: (a) if the `PYTEST_BDD_FAKE_NODE_PYTHON` environment
        variable is set, use its value directly — this allows CI or developers to override the Python used by the fake
        runtime; (b) if running on PyPy, search for a `python` executable on PATH and use it only if it resolves to a
        different path than `sys.executable` — this handles the case where PyPy's own binary may not be suitable for
        running the fake runtime shims; (c) otherwise, use `sys.executable`, which is the same Python interpreter
        running the current test session.

    Reason for existence:
        This function centralizes the Python-executable resolution logic so that both the Unix shim scripts (written by
        `materialize_fake_node_runtime`) and the Windows .cmd shims (written by `_write_windows_command_shim`) use the
        same executable. The PyPy-specific fallback is a non-obvious edge case that would be easy to miss if inlined —
        isolating it here makes it explicit and testable.

    Delegates:
        - `shutil.which("python")`: Searches PATH for a `python` executable (used only in the PyPy fallback path).
        - `os.environ.get("PYTEST_BDD_FAKE_NODE_PYTHON")`: Checks for the override environment variable.
        - `os.path.normcase` / `Path.resolve`: Used to normalize and compare executable paths on case-insensitive filesystems.

    Cohesion:
        The function's entire body is a three-branch decision tree answering the single question "which Python
        executable should the fake node shims use?" No unrelated logic.

    Separation:
        - `_write_windows_command_shim`: Kept separate because it calls this function and writes the resulting path into
        a .cmd file; this function is the pure query.
        - `materialize_fake_node_runtime`: Kept separate because it writes the Unix shim scripts that embed this
        function's result; this function is the resolution helper.

    Main consumers:
        - `_write_windows_command_shim`: Calls `_fake_node_python_executable()` to get the Python path for the .cmd shim.
        - `materialize_fake_node_runtime`: Indirectly consumes the resolved executable through
        `_write_windows_command_shim`; the Unix shim scripts use `#!/usr/bin/env python` or `sys.executable` directly in
        the template.

    State and side effects:
        Reads the `PYTEST_BDD_FAKE_NODE_PYTHON` environment variable. May call `shutil.which` to search PATH (filesystem
        read). No writes, no environment mutation, no network I/O.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    override = os.environ.get("PYTEST_BDD_FAKE_NODE_PYTHON")
    if override:
        return override
    if sys.implementation.name == "pypy":
        python_executable = shutil.which("python")
        if python_executable and os.path.normcase(str(Path(python_executable).resolve())) != os.path.normcase(
            str(Path(sys.executable).resolve()),
        ):
            return python_executable
    return sys.executable


def _write_windows_command_shim(command_path: Path, target_script_path: Path) -> None:
    """
    `rendering._write_windows_command_shim` — Creates a Windows .cmd batch file that proxies execution to the Python
    shim at the target script path.

    Responsibility:
        Creates a Windows `.cmd` batch file at `command_path` that proxies execution to the Python shim at
        `target_script_path`. The batch file uses `@echo off` for clean output, invokes the resolved Python executable
        (via `_fake_node_python_executable`) with the target script path as the first argument, and forwards all
        additional arguments via `%*`. This ensures that commands like `node` and `npm` work seamlessly on Windows when
        the fake runtime is installed on PATH — the `.cmd` file is what Windows actually executes when `node` is typed
        at the command line.

    Reason for existence:
        Windows does not execute Unix-style Python scripts directly from PATH without a file association or a
        `.cmd`/`.bat` wrapper. This function encapsulates the wrapper-generation protocol so that
        `materialize_fake_node_runtime` doesn't need platform-specific branching in its main body — it unconditionally
        calls this function, and on non-Windows platforms the `.cmd` files are harmless unused artifacts. The function
        also localizes the `.cmd` file format (CRLF line endings, `@echo off`, quote-wrapped executable path, `%*`
        argument forwarding).

    Delegates:
        - `_fake_node_python_executable`: Called to resolve which Python executable to embed in the .cmd file.

    Cohesion:
        Single responsibility: write a Windows command shim to disk. No unrelated logic.

    Separation:
        - `_fake_node_python_executable`: Kept separate because it is the pure query; this function writes the result to disk.
        - `materialize_fake_node_runtime`: Kept separate because it calls this function twice (for node.cmd and
        npm.cmd); this function is the reusable writer.

    Main consumers:
        - `materialize_fake_node_runtime`: Calls `_write_windows_command_shim(bin_dir / "node.cmd", node_path)` and
        `_write_windows_command_shim(bin_dir / "npm.cmd", npm_path)`.

    State and side effects:
        Writes a `.cmd` file to disk at `command_path`. No network I/O, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    python_executable = _fake_node_python_executable()
    command_path.write_text(
        "\r\n".join(
            (
                "@echo off",
                f'"{python_executable}" "{target_script_path}" %*',
                "",
            ),
        ),
        encoding="utf-8",
    )


def _write_fake_html_formatter_assets(package_dir: Path) -> None:
    """
    `rendering._write_fake_html_formatter_assets` — Creates stub dist/ and src/ files for @cucumber/html-formatter
    inside the fake node_modules tree.

    Responsibility:
        Creates stub files for the `@cucumber/html-formatter` package inside the fake `node_modules` tree:
        - `dist/main.js`: A one-liner that sets `window.CUCUMBER_HTML_FORMATTER_TEST = true` so tests can detect that
        the fake HTML formatter was loaded.
        - `dist/main.css`: A minimal CSS rule (`body { font-family: sans-serif; }`) so the formatter doesn't fail on
        missing CSS.
        - `src/index.mustache.html`: A minimal Mustache template that renders the HTML document structure with
        `{{title}}`, `{{css}}`, `{{messages}}`, and `{{script}}` placeholders, matching the contract expected by
        `@cucumber/html-formatter`'s runtime.

    Reason for existence:
        The `@cucumber/html-formatter` package is special among the preinstalled fake packages because it has actual
        runtime files (JS, CSS, Mustache template) that the cucumber runtime may try to read at execution time. The
        other fake packages only need a `package.json`. This function isolates all HTML-formatter-specific asset
        creation so that `materialize_fake_node_runtime`'s main package-creation loop stays simple (create dir + write
        package.json) with a single conditional branch for the HTML formatter.

    Delegates:
        - `package_dir / "dist"` and `package_dir / "src"`: Subdirectories created under the package directory to hold
        the stub files.
        - `.write_text(...)`: Writes each stub file with UTF-8 encoding.

    Cohesion:
        This function creates three files that together constitute a complete (though minimal) `@cucumber/html-
        formatter` package. All three files are required for the formatter to function without errors — they form an
        atomic unit.

    Separation:
        - `materialize_fake_node_runtime`: Kept separate because it iterates all preinstalled packages and conditionally
        calls this function for the HTML formatter; this function is the specialized asset writer.
        - `_render_support_template`: Kept separate because it handles Jinja2-style template rendering from package
        resources; this function writes hardcoded stub content directly.

    Main consumers:
        - `materialize_fake_node_runtime`: Called when `package_name == "@cucumber/html-formatter"` during the fake
        module tree construction.

    State and side effects:
        Creates directories (`dist/`, `src/`) and writes three files (`main.js`, `main.css`, `index.mustache.html`)
        under `package_dir`. No network I/O, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    dist_dir = package_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "main.js").write_text("window.CUCUMBER_HTML_FORMATTER_TEST = true;\n", encoding="utf-8")
    (dist_dir / "main.css").write_text("body { font-family: sans-serif; }\n", encoding="utf-8")
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "index.mustache.html").write_text(
        "<!doctype html><html><head><title>{{title}}</title><style>{{css}}</style></head>"
        "<body><script>window.CUCUMBER_MESSAGES=[{{messages}}];</script><script>{{script}}</script></body></html>",
        encoding="utf-8",
    )


def materialize_fake_node_runtime(
    root_path: Path,
    *,
    preinstalled_packages: tuple[str, ...] = ("@cucumber/cucumber", "@cucumber/pretty-formatter"),
) -> dict[str, Path]:
    """
    `rendering.materialize_fake_node_runtime` — Creates a complete fake Node.js runtime on disk with executable node/npm
    Python shims, stub package.json files, and telemetry capture directory.

    Responsibility:
        Creates a complete fake Node.js runtime environment on disk under `root_path`, consisting of:
        - `fake-node-bin/`: Contains executable Python shims for `node` and `npm` (and `node.cmd` / `npm.cmd` Windows
        wrappers) that simulate real Node.js by running Python scripts which output deterministic fake formatter results
        and log invocation telemetry to JSON capture files.
        - `fake-node-modules/`: Contains stub `package.json` files for each `preinstalled_packages` entry, creating a
        realistic `node_modules` tree structure. If `@cucumber/html-formatter` is included, its stub also gets fake
        dist/ and src/ assets.
        - `fake-global-node-modules/`: An empty directory reserved for global module simulation.
        - `fake-node-captures/`: An empty directory where the fake node runtime writes JSON telemetry files recording
        each invocation's formatter names, envelope counts, console write counts, etc.

    Reason for existence:
        This function is the single entry point for all fake Node.js runtime materialization. It exists as a dedicated
        function rather than being part of `install_fake_node` because the materialization (filesystem operations) and
        the installation (environment variable patching) are separate concerns — some tests may want to materialize the
        runtime without immediately installing it on PATH, or may want to inspect the filesystem layout before
        activation. The function encapsulates the complete directory structure and file content protocol, including the
        rendering of the Python shim templates with the `_FAKE_FORMATTER_OUTPUTS` dictionary injected.

    Delegates:
        - `_render_support_template`: Called to render `fake_node_runtime.py.j2` (with `__FORMATTER_OUTPUTS__` replaced
        by the repr of `_FAKE_FORMATTER_OUTPUTS`) and `fake_npm_runtime.py.j2` (raw template, no replacements).
        - `_write_windows_command_shim`: Called to create `node.cmd` and `npm.cmd` Windows wrappers.
        - `_write_fake_html_formatter_assets`: Conditionally called when `@cucumber/html-formatter` is in
        `preinstalled_packages` to create stub dist/ and src/ files.
        - `Path.mkdir` / `Path.write_text` / `Path.chmod`: Standard filesystem operations for directory creation, file
        writing, and executable permission setting.

    Cohesion:
        Every line in this function contributes to creating the fake Node.js runtime directory tree. Directory creation,
        package.json stubbing, Python shim rendering, Windows shim generation, and executable permission setting are all
        steps in a single pipeline: "produce a fake runtime on disk."

    Separation:
        - `install_fake_node`: Kept separate because it calls this function and then monkeypatches environment
        variables; this function is the pure-materialization step.
        - `materialize_live_formatter_runtime`: Kept separate because it creates real cucumber formatter runtime
        artifacts (not fake node shims); the two functions target different testing scenarios.

    Main consumers:
        - `install_fake_node`: Calls `materialize_fake_node_runtime(tmp_path, preinstalled_packages=...)` as the first
        step of fake-node installation.
        - `pytest_bdd_testing.cases.external.support.test_docker_wsl2`: Calls `materialize_fake_node_runtime` directly
        for Docker/WSL2 test support.
        - `pytest_bdd_testing.cases.contract.support.test_cucumber_formatters`: Imports and calls
        `materialize_fake_node_runtime` for unit-level contract tests.

    State and side effects:
        Creates multiple directories and files on disk under `root_path`. Sets executable permission bits on the `node`
        and `npm` shim files via `chmod`. No network I/O, no environment mutation, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    root_path.mkdir(parents=True, exist_ok=True)
    bin_dir = root_path / "fake-node-bin"
    bin_dir.mkdir(exist_ok=True)
    seed_node_modules = root_path / "fake-node-modules"
    seed_node_modules.mkdir(exist_ok=True)
    global_node_modules = root_path / "fake-global-node-modules"
    global_node_modules.mkdir(exist_ok=True)
    capture_dir = root_path / "fake-node-captures"
    capture_dir.mkdir(exist_ok=True)

    for package_name in preinstalled_packages:
        package_dir = seed_node_modules.joinpath(*package_name.split("/"))
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "package.json").write_text(
            json.dumps({"name": package_name, "version": "0.0.0-test"}, indent=2) + "\n",
            encoding="utf-8",
        )
        if package_name == "@cucumber/html-formatter":
            _write_fake_html_formatter_assets(package_dir)

    node_path = bin_dir / "node"
    node_path.write_text(
        _render_support_template(
            "fake_node_runtime.py.j2",
            replacements={"__FORMATTER_OUTPUTS__": repr(_FAKE_FORMATTER_OUTPUTS)},
        ),
        encoding="utf-8",
        newline="\n",
    )
    node_path.chmod(node_path.stat().st_mode | stat.S_IEXEC)

    npm_path = bin_dir / "npm"
    npm_path.write_text(
        _render_support_template("fake_npm_runtime.py.j2"),
        encoding="utf-8",
        newline="\n",
    )
    npm_path.chmod(npm_path.stat().st_mode | stat.S_IEXEC)
    _write_windows_command_shim(bin_dir / "node.cmd", node_path)
    _write_windows_command_shim(bin_dir / "npm.cmd", npm_path)
    return {
        "bin_dir": bin_dir,
        "seed_node_modules": seed_node_modules,
        "global_node_modules": global_node_modules,
        "capture_dir": capture_dir,
    }


def materialize_live_formatter_runtime(
    root_path: Path,
    *formatter_names: str,
    output_paths: dict[str, str | None] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    """
    `rendering.materialize_live_formatter_runtime` — Builds a real cucumber formatter runtime on disk using
    FormatterPluginCatalog discovery and per-plugin asset rendering.

    Responsibility:
        Builds a complete cucumber formatter runtime on disk under `root_path` for one or more named formatters, using
        the real `FormatterPluginCatalog` to discover plugin metadata and render per-plugin runtime assets. For each
        formatter name, the function: (a) looks up the plugin in the catalog's by-name index; (b) constructs a
        `CucumberFormatterRequest` with all metadata fields (option_attr, cli_flag, formatter, package_name,
        output_path, plugin_module, runtime_kind, runtime_specifier, runtime_module_path, runtime_export_name,
        runtime_template_name, discovery_order); (c) collects a corresponding payload spec dict for test assertions; (d)
        calls `FormatterPluginCatalog.render_runtime_assets` to render all plugin-specific runtime assets (e.g.,
        JavaScript modules, configuration files) to their relative paths under `root_path`. Returns a tuple of (path to
        the entry-point `render_cucumber_formatters.js` script, list of payload specs for test assertions).

    Reason for existence:
        This function is the production-path counterpart to `materialize_fake_node_runtime`. While
        `materialize_fake_node_runtime` creates a simulated Node.js runtime for tests that don't need real Node.js, this
        function creates the actual cucumber formatter runtime artifacts that a real Node.js process would consume. It
        exercises the real `FormatterPluginCatalog.discover()` and `render_runtime_assets()` paths, making it suitable
        for integration tests that verify the formatter plugin discovery and rendering pipeline end-to-end. The function
        exists in rendering rather than registry because it performs filesystem materialization (writing rendered assets
        to disk), which is the rendering module's core competency.

    Delegates:
        - `FormatterPluginCatalog.discover()`: Called twice — once to get `plugins_by_name()` for resolving individual
        formatter plugins, and once to call `render_runtime_assets()` for rendering.
        - `FormatterPluginCatalog.by_name()`: Provides a dict mapping formatter names to plugin metadata objects.
        - `FormatterPluginCatalog.render_runtime_assets(tuple(formatter_requests))`: Renders all plugin-specific runtime
        assets and returns a dict of relative path → rendered content.
        - `CucumberFormatterRequest(...)`: Constructs the typed request object for each formatter from the plugin's
        metadata fields.
        - `Path.mkdir` / `Path.write_text`: Standard filesystem operations for writing rendered assets to disk.

    Cohesion:
        Every line in this function serves the "build live formatter runtime" pipeline: resolve plugins → build requests
        → build payload specs → render assets → write assets to disk. The function is a single, linear transformation
        from formatter names to a filesystem runtime and metadata payload.

    Separation:
        - `materialize_fake_node_runtime`: Kept separate because it creates fake node shims and stub modules; this
        function creates real formatter runtime artifacts using the actual plugin catalog.
        - `install_formatter_hook_registry` (in registry): Kept separate because it installs an in-process hook proxy;
        this function materializes runtime files on disk for out-of-process execution.

    Main consumers:
        - `pytest_bdd_testing.cases.integration.hook.test_live_formatter_terminal_layout`: Imports and calls
        `materialize_live_formatter_runtime` for live formatter terminal layout tests.
        - `pytest_bdd_testing.cases.compat.compatibility.test_render_cucumber_formatters`: Imports and calls
        `materialize_live_formatter_runtime` for compatibility tests.

    State and side effects:
        Creates directories and writes rendered runtime asset files to disk under `root_path`. Reads the
        `FormatterPluginCatalog` (which may scan the filesystem for plugin entry points). No network I/O, no environment
        mutation, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    output_paths = {} if output_paths is None else dict(output_paths)
    plugins_by_name = FormatterPluginCatalog.discover().by_name()
    formatter_requests: list[CucumberFormatterRequest] = []
    payload_specs: list[dict[str, object]] = []

    for formatter_name in formatter_names:
        plugin = plugins_by_name[formatter_name]
        output_path = output_paths.get(formatter_name)
        formatter_request = CucumberFormatterRequest(
            option_attr=plugin.option_attr,
            cli_flag=plugin.cli_flag,
            formatter=plugin.formatter,
            package_name=plugin.package_name,
            output_path=Path(output_path) if output_path is not None else None,
            plugin_module=plugin.module_name,
            runtime_kind=plugin.runtime_kind,
            runtime_specifier=plugin.runtime_specifier or plugin.formatter,
            runtime_module_path=plugin.module_runtime_path if plugin.has_module_runtime else None,
            runtime_export_name=plugin.runtime_export_name,
            runtime_template_name=plugin.module_runtime_template_name if plugin.has_module_runtime else None,
            discovery_order=plugin.discovery_order,
        )
        formatter_requests.append(formatter_request)
        payload_specs.append(
            {
                "formatter": formatter_request.formatter,
                "outputPath": output_path,
                "cliFlag": formatter_request.cli_flag,
                "runtime": {
                    "kind": formatter_request.runtime_kind.value,
                    "specifier": formatter_request.runtime_specifier,
                    "modulePath": formatter_request.runtime_module_path,
                    "exportName": formatter_request.runtime_export_name,
                },
            },
        )

    runtime_assets = FormatterPluginCatalog.discover().render_runtime_assets(tuple(formatter_requests))
    for relative_path, rendered_asset in runtime_assets.items():
        asset_path = root_path / relative_path
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(rendered_asset, encoding="utf-8")

    return root_path / "render_cucumber_formatters.js", payload_specs


def install_fake_node(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    *,
    preinstalled_packages: tuple[str, ...] = ("@cucumber/cucumber", "@cucumber/pretty-formatter"),
) -> None:
    """
    `pytest_bdd.cucumber_formatters.rendering.install_fake_node` — One-step setup that materializes the fake Node.js
    runtime and monkeypatches PATH, NODE_PATH, and capture env vars.

    Responsibility:
        Provides a one-step setup function that materializes the fake Node.js runtime under `tmp_path` and monkeypatches
        the process environment so that subsequent `subprocess` invocations (e.g., via `run_pytest_via_real_entrypoint`)
        will find and use the fake `node` and `npm` binaries instead of any real Node.js installation. The environment
        variables set are: `PATH` (prepended with `fake-node-bin`), `NODE_PATH` (set to `fake-node-modules`),
        `FAKE_GLOBAL_NODE_MODULES_ROOT` (set to `fake-global-node-modules`), and `PYTEST_BDD_FAKE_NODE_CAPTURE_DIR` (set
        to `fake-node-captures`). All monkeypatches are scoped to the test duration by pytest's `monkeypatch` fixture.

    Reason for existence:
        This function is the top-level convenience entry point that composes `materialize_fake_node_runtime` (which
        creates the fake runtime on disk) with `monkeypatch.setenv` calls (which activate it on PATH). It exists as a
        separate function rather than being a simple two-line composition because the four `setenv` calls form a
        protocol that must be performed together and in the correct order — missing any one would cause the fake runtime
        to malfunction silently. By providing this function, test code gets a single `install_fake_node(monkeypatch,
        tmp_path)` call that is self-documenting and guaranteed to set up all four environment variables correctly.

    Delegates:
        - `materialize_fake_node_runtime`: Called to create the fake Node.js runtime directory tree and return the paths
        to bin_dir, seed_node_modules, global_node_modules, and capture_dir.
        - `monkeypatch.setenv`: Called four times to set PATH, NODE_PATH, FAKE_GLOBAL_NODE_MODULES_ROOT, and
        PYTEST_BDD_FAKE_NODE_CAPTURE_DIR.

    Cohesion:
        This function performs the two-step "materialize + activate" protocol that is always needed together in tests.
        No unrelated logic.

    Separation:
        - `materialize_fake_node_runtime`: Kept separate because it is the pure-materialization step; this function adds
        the environment activation.
        - `enable_fake_node_capture` (in registry): Kept separate because it only sets
        `PYTEST_BDD_FAKE_NODE_CAPTURE_DIR` without installing the full fake runtime; that function is used when fake
        node is already installed and only capture needs enabling.

    Main consumers:
        - `pytest_bdd_testing.cases.e2e.conftest`: Calls `install_fake_node` in the e2e conftest fixture setup.
        - `pytest_bdd_testing.cases.e2e.steps_formatters`: Calls `install_fake_node` as a Gherkin step-definition primitive.
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Calls `install_fake_node` for the core formatter
        integration tests.
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters_feature`: Calls `install_fake_node` for feature-
        level formatter tests.
        - `pytest_bdd_testing.cases.contract.contract.test_formatter_golden_parity`: Calls `install_fake_node` for
        golden-output parity testing.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_message_aggregation`: Calls `install_fake_node` for xdist tests.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_remote_message_aggregation`: Calls `install_fake_node` for
        xdist remote tests.

    State and side effects:
        Creates directories and files on disk under `tmp_path` (via `materialize_fake_node_runtime`). Mutates the
        process environment via `monkeypatch.setenv` (scoped to the test duration). No network I/O, no pytest stash
        access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    runtime = materialize_fake_node_runtime(tmp_path, preinstalled_packages=preinstalled_packages)
    monkeypatch.setenv("PATH", f"{runtime['bin_dir']}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("NODE_PATH", str(runtime["seed_node_modules"]))
    monkeypatch.setenv("FAKE_GLOBAL_NODE_MODULES_ROOT", str(runtime["global_node_modules"]))
    monkeypatch.setenv("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", str(runtime["capture_dir"]))
