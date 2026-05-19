"""Convert single-file formatter plugins into canonical packages."""

import os
import pathlib

base = r"c:\Users\bulky\Projects\pytest-bdd\src\pytest_bdd\plugin"

plugins = [
    ("cucumber_json_formatter", "JsonFormatterPlugin", "json_plugin"),
    ("cucumber_junit", "JunitFormatterPlugin", "junit_plugin"),
    ("cucumber_pretty", "PrettyFormatterPlugin", "pretty_plugin"),
    ("cucumber_progress", "ProgressFormatterPlugin", "progress_plugin"),
    ("cucumber_progress_bar", "ProgressBarFormatterPlugin", "progress_bar_plugin"),
    ("cucumber_snippets", "SnippetsFormatterPlugin", "snippets_plugin"),
    ("cucumber_summary", "SummaryFormatterPlugin", "summary_plugin"),
    ("cucumber_usage", "UsageFormatterPlugin", "usage_plugin"),
    ("cucumber_usage_json", "UsageJsonFormatterPlugin", "usage_json_plugin"),
]

for pkg_name, class_name, instance_name in plugins:
    old_file = os.path.join(base, f"{pkg_name}.py")
    pkg_dir = os.path.join(base, pkg_name)

    old_content = pathlib.Path(old_file).read_text()

    pathlib.Path(pkg_dir).mkdir(exist_ok=True, parents=True)

    # __init__.py
    pathlib.Path(os.path.join(pkg_dir, "__init__.py")).write_text(
        f'"""Provide src.pytest_bdd.plugin.{pkg_name} package helpers."""\n'
    )

    # plugin.py
    plugin_content = (
        old_content.replace(
            "from .cucumber_formatter_support.base import",
            "from pytest_bdd.plugin.cucumber_formatter_support.base import",
        )
        .replace(
            "from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest, ResolveOutputPath",
            "from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, ResolveOutputPath",
        )
        .replace(
            "module_name=__name__,",
            f'module_name="pytest_bdd.plugin.{pkg_name}.plugin",',
        )
    )
    # Remove the instance line
    lines = plugin_content.rstrip().split("\n")
    while lines and (lines[-1].strip().endswith(f"{class_name}()") or lines[-1].strip() == ""):
        lines.pop()
    plugin_content = "\n".join(lines) + "\n"

    pathlib.Path(os.path.join(pkg_dir, "plugin.py")).write_text(plugin_content)

    # hook.py
    hook_content = (
        '"""\n'
        f"Hook specifications for the {pkg_name.replace('_', ' ')} plugin.\n"
        "\n"
        "This module is a canonical package-structure placeholder so source contracts can\n"
        "require every pytest11 plugin package to provide an explicit hook surface.\n"
        '"""\n'
    )
    pathlib.Path(os.path.join(pkg_dir, "hook.py")).write_text(hook_content)

    # entrypoint.py
    ep_content = (
        f'"""Provide {pkg_name.replace("_", " ")} entrypoint."""\n'
        "\n"
        f"from .plugin import {class_name}\n"
        "\n"
        f"{instance_name} = {class_name}()\n"
    )
    pathlib.Path(os.path.join(pkg_dir, "entrypoint.py")).write_text(ep_content)

    # Remove old file
    pathlib.Path(old_file).unlink()
    print(f"Converted {pkg_name}")

print("Done!")
