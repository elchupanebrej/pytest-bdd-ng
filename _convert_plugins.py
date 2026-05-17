"""Convert single-file formatter plugins into canonical packages."""

import os

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

    with open(old_file) as f:
        old_content = f.read()

    os.makedirs(pkg_dir, exist_ok=True)

    # __init__.py
    with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
        f.write(f'"""Provide src.pytest_bdd.plugin.{pkg_name} package helpers."""\n')

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

    with open(os.path.join(pkg_dir, "plugin.py"), "w") as f:
        f.write(plugin_content)

    # hook.py
    hook_content = (
        '"""\n'
        f"Hook specifications for the {pkg_name.replace('_', ' ')} plugin.\n"
        "\n"
        "This module is a canonical package-structure placeholder so source contracts can\n"
        "require every pytest11 plugin package to provide an explicit hook surface.\n"
        '"""\n'
    )
    with open(os.path.join(pkg_dir, "hook.py"), "w") as f:
        f.write(hook_content)

    # entrypoint.py
    ep_content = (
        f'"""Provide {pkg_name.replace("_", " ")} entrypoint."""\n'
        "\n"
        f"from .plugin import {class_name}\n"
        "\n"
        f"{instance_name} = {class_name}()\n"
    )
    with open(os.path.join(pkg_dir, "entrypoint.py"), "w") as f:
        f.write(ep_content)

    # Remove old file
    os.remove(old_file)
    print(f"Converted {pkg_name}")

print("Done!")
