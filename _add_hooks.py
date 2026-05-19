"""Add missing hook.py files to pre-existing plugin packages."""

import os
import pathlib

base = r"c:\Users\bulky\Projects\pytest-bdd\src\pytest_bdd\plugin"
missing = ["cucumber_json", "gherkin_terminal_reporter", "scenario_reporter", "struct_bdd"]
for pkg in missing:
    hook_path = os.path.join(base, pkg, "hook.py")
    label = pkg.replace("_", " ")
    content = (
        '"""\n'
        f"Hook specifications for the {label} plugin.\n"
        "\n"
        "This module is a canonical package-structure placeholder so source contracts can\n"
        "require every pytest11 plugin package to provide an explicit hook surface.\n"
        '"""\n'
    )
    pathlib.Path(hook_path).write_text(content)
    print(f"Created {hook_path}")
print("Done")
