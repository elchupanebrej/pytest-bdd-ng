"""Build and verify the optional Go parser through a source distribution."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Build a pure sdist, build its native wheel, then test both consumers."""
    if len(sys.argv) != 2:
        print("usage: python scripts/test_native_go_parser.py <output-directory>", file=sys.stderr)
        return 2

    output_root = Path(sys.argv[1]).resolve()
    source_dir = output_root / "source"
    native_dir = output_root / "native"
    source_dir.mkdir(parents=True, exist_ok=True)
    native_dir.mkdir(parents=True, exist_ok=True)

    pure_environment = os.environ.copy()
    pure_environment["PYTEST_CUKE_BUILD_GO"] = "off"
    source_build = subprocess.run(  # noqa: S603 - fixed build command and interpreter
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(source_dir)],
        env=pure_environment,
        check=False,
    )
    if source_build.returncode:
        return source_build.returncode

    source_distributions = list(source_dir.glob("pytest_cuke-*.tar.gz"))
    if len(source_distributions) != 1:
        print(f"expected one pytest-cuke source archive, found {source_distributions}", file=sys.stderr)
        return 2

    native_environment = os.environ.copy()
    native_environment["PYTEST_CUKE_BUILD_GO"] = "required"
    native_build = subprocess.run(  # noqa: S603 - fixed pip wheel command and source archive
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(native_dir),
            str(source_distributions[0]),
        ],
        env=native_environment,
        check=False,
    )
    if native_build.returncode:
        return native_build.returncode

    wheels = list(native_dir.glob("pytest_cuke-*.whl"))
    if len(wheels) != 1:
        print(f"expected one native pytest-cuke wheel, found {wheels}", file=sys.stderr)
        return 2

    consumer_environment = os.environ.copy()
    consumer_environment["PYTEST_CUKE_BUILD_GO"] = "off"
    consumer_environment["PYTEST_CUKE_NATIVE_WHEEL"] = str(wheels[0])
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "features/native-go-parser/optional-native-go-parser.feature",
        ],
        env=consumer_environment,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
