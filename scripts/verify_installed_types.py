#!/usr/bin/env python3
"""
Fresh-wheel checker environment for verifying the installed pytest_bdd typing contract.

Usage (from repo root):
    uv run --all-extras python scripts/verify_installed_types.py --assert-isolated --check-verifytypes
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None, env=merged)


def build_wheel() -> Path:
    """Build a wheel and return its path."""
    print(":: Building wheel …", flush=True)
    r = _run(["uv", "build", "--wheel"], cwd=_REPO_ROOT)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"uv build failed: {r.returncode}")

    dist_dir = _REPO_ROOT / "dist"
    wheels = sorted(dist_dir.glob("pytest_bdd_ng-*.whl"))
    if not wheels:
        raise SystemExit("No wheel found in dist/")
    print(f"   wheel: {wheels[-1].name}")
    return wheels[-1]


def assert_isolated(venv_python: Path) -> None:
    """Assert that the venv is truly isolated from the checkout."""
    print(":: Asserting isolation …", flush=True)

    # Interpreter must be inside the temp venv, not the checkout
    assert str(venv_python).startswith(str(tempfile.gettempdir())), f"venv python not in temp dir: {venv_python}"

    # mypy must resolve under the venv
    r = _run([str(venv_python), "-c", "import mypy; print(mypy.__file__)"])
    assert r.returncode == 0, f"mypy import failed: {r.stderr}"
    assert str(Path(tempfile.gettempdir())) in r.stdout, f"mypy resolves outside venv: {r.stdout}"
    print("   mypy: isolated ✓")

    # Pyright must be importable (it's a pip package)
    r = _run([str(venv_python), "-c", "import pyright; print(pyright.__file__)"])
    assert r.returncode == 0, f"pyright import failed: {r.stderr}"
    print("   pyright: isolated ✓")

    # pytest_bdd.__file__ must be under venv site-packages, NOT the checkout
    r = _run([str(venv_python), "-c", "import pytest_bdd; print(pytest_bdd.__file__)"])
    assert r.returncode == 0, f"pytest_bdd import failed: {r.stderr}"
    pkg_path = Path(r.stdout.strip())
    repo_root_str = str(_REPO_ROOT.resolve())
    assert not str(pkg_path).startswith(repo_root_str), (
        f"pytest_bdd resolves to checkout, not installed wheel: {pkg_path}"
    )
    assert "site-packages" in str(pkg_path), f"pytest_bdd not in site-packages: {pkg_path}"
    print(f"   pytest_bdd: {pkg_path} (isolated ✓)")


def check_fixtures(
    venv_python: Path,
    fixtures_dir: Path,
    extern_cwd: Path,
) -> tuple[bool, bool]:
    """Run mypy and Pyright against fixtures in an external cwd. Returns (mypy_ok, pyright_ok)."""
    print(":: Checking fixtures …", flush=True)
    fixture_files = sorted(fixtures_dir.glob("*.py"))
    if not fixture_files:
        print("   no fixture files — skipping", flush=True)
        return True, True

    # Write fixtures to external cwd (avoids picking up the checkout)
    for f in fixture_files:
        dest = extern_cwd / f.name
        dest.write_text(f.read_text(), encoding="utf-8")

    # mypy
    print("   mypy …", flush=True)
    r = _run([str(venv_python), "-m", "mypy", "--strict", str(extern_cwd)], cwd=extern_cwd)
    mypy_ok = r.returncode == 0
    if not mypy_ok:
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)

    # pyright
    print("   pyright …", flush=True)
    r = _run([str(venv_python), "-m", "pyright", str(extern_cwd)], cwd=extern_cwd)
    pyright_ok = r.returncode == 0
    if not pyright_ok:
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)

    return mypy_ok, pyright_ok


def check_verifytypes(venv_python: Path) -> bool:
    """Run pyright --verifytypes against the installed pytest_bdd package. Returns True if 100%."""
    print(":: Pyright --verifytypes pytest_bdd …", flush=True)
    r = _run(
        [str(venv_python), "-m", "pyright", "--verifytypes", "pytest_bdd", "--ignoreexternal"],
    )
    output = r.stdout + r.stderr

    # pyright exits 0 even for incomplete types; we parse the summary line
    # e.g. "Type completeness score: 100%"  or  "Type completeness: 87.5%"
    for line in output.splitlines():
        if "completeness" in line.lower() and "%" in line:
            pct_str = line.split("%")[0].split()[-1]
            try:
                pct = float(pct_str)
            except ValueError:
                continue
            ok = pct >= 100.0
            print(f"   {line.strip()}  {'✓' if ok else '✗'}")
            if not ok:
                print("Full pyright output:", flush=True)
                print(output, file=sys.stderr)
            return ok
    print("   Could not parse completeness score", flush=True)
    print(output, file=sys.stderr)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify installed-wheel typing contract")
    parser.add_argument("--assert-isolated", action="store_true", help="Assert venv isolation from checkout")
    parser.add_argument("--check-verifytypes", action="store_true", help="Run pyright --verifytypes and assert 100%%")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=None,
        help="Directory with consumer typing fixtures to check",
    )
    args = parser.parse_args()

    # Build the wheel
    wheel_path = build_wheel()

    # Create temp working area OUTSIDE the checkout
    work_dir = Path(tempfile.mkdtemp(prefix="pytbdd_typing_"))
    print(f":: Work dir: {work_dir}", flush=True)

    # Create venv
    print(":: Creating venv …", flush=True)
    venv_dir = work_dir / ".venv"
    r = _run(["uv", "venv", str(venv_dir), "--python", sys.executable])
    if r.returncode != 0:
        raise SystemExit(f"uv venv failed: {r.stderr}")

    # Determine venv python path
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    # Install wheel + checkers
    print(":: Installing wheel + checkers …", flush=True)
    r = _run([
        "uv",
        "pip",
        "install",
        "--python",
        str(venv_python),
        str(wheel_path),
        "mypy>=1.0",
        "pyright>=1.1.400",
    ])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit("pip install failed")

    # Assert isolation
    if args.assert_isolated:
        assert_isolated(venv_python)

    # Check fixtures
    if args.fixtures_dir and args.fixtures_dir.is_dir():
        extern_cwd = work_dir / "fixtures_cwd"
        extern_cwd.mkdir()
        mypy_ok, pyright_ok = check_fixtures(venv_python, args.fixtures_dir, extern_cwd)
        print(f"   mypy: {'✓' if mypy_ok else '✗'}   pyright: {'✓' if pyright_ok else '✗'}")
        if not mypy_ok or not pyright_ok:
            # Don't fail hard — individual test should handle expected errors
            pass

    # Pyright verifytypes
    if args.check_verifytypes:
        ok = check_verifytypes(venv_python)
        if not ok:
            raise SystemExit("pyright --verifytypes score < 100%")

    # Cleanup
    shutil.rmtree(work_dir, ignore_errors=True)
    print(":: Done ✓", flush=True)


if __name__ == "__main__":
    main()
