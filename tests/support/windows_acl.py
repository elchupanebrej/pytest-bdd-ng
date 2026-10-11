"""Windows identity lookup helpers for ACL-focused acceptance tests."""

from __future__ import annotations

import csv
import os
import re
import subprocess
from pathlib import Path


_WINDOWS_WHOAMI_ARGUMENTS = ("/user", "/fo", "csv", "/nh")


def windows_identity_lookup_command() -> tuple[str, ...] | None:
    if os.name != "nt":
        return None
    system_root = os.environ.get("SYSTEMROOT")
    assert system_root, "SystemRoot is required to locate the Windows identity executable"
    whoami = Path(system_root) / "System32" / "whoami.exe"
    assert whoami.is_file(), f"Windows identity executable was not found: {whoami}"
    return (str(whoami), *_WINDOWS_WHOAMI_ARGUMENTS)


def windows_acl_user_sid(command: tuple[str, ...]) -> str:
    identity = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert identity.returncode == 0, (
        f"could not identify the current Windows user:\n{identity.stdout}\n{identity.stderr}"
    )
    rows = list(csv.reader(identity.stdout.splitlines()))
    assert rows and len(rows[0]) >= 2, identity.stdout
    sid = rows[0][-1].strip()
    assert re.fullmatch(r"S-1(?:-\d+)+", sid), identity.stdout
    return sid



def assert_windows_identity_lookup_command(command: tuple[str, ...] | None) -> None:
    if os.name != "nt":
        assert command is None
        return

    assert command is not None
    system_root = os.environ.get("SYSTEMROOT")
    assert system_root
    expected = Path(system_root) / "System32" / "whoami.exe"
    actual = os.path.normcase(os.path.abspath(command[0]))
    assert actual == os.path.normcase(os.path.abspath(expected)), command
    assert command[1:] == _WINDOWS_WHOAMI_ARGUMENTS
    windows_acl_user_sid(command)
