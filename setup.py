"""Optional native Go parser build hook for wheel builds."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel


class build_py(_build_py):
    """Build the optional Go shared library into the wheel package directory."""

    def run(self) -> None:
        super().run()
        self._remove_stale_native_go_artifacts()
        self._build_native_go_library()

    def _remove_stale_native_go_artifacts(self) -> None:
        package_dir = (Path(self.build_lib) / "pytest_cuke" / "_native_go").resolve()
        for library_name in _NATIVE_LIBRARY_NAMES:
            library_path = package_dir / library_name
            library_path.unlink(missing_ok=True)
            library_path.with_suffix(".h").unlink(missing_ok=True)

    def _build_native_go_library(self) -> None:
        mode = os.environ.get("PYTEST_CUKE_BUILD_GO", "auto").strip().lower()
        if mode == "off":
            return
        if mode not in {"auto", "required"}:
            raise RuntimeError("PYTEST_CUKE_BUILD_GO must be 'auto', 'required', or 'off'.")

        output_name = {
            "linux": "libgherkin_go.so",
            "win32": "gherkin_go.dll",
            "darwin": "libgherkin_go.dylib",
        }.get(sys.platform)
        if output_name is None:
            self._native_build_issue(f"native Go parser builds are unsupported on {sys.platform}")
            return

        go = shutil.which("go")
        if go is None:
            self._native_build_issue("Go was not found on PATH")
            return

        configured_cc = os.environ.get("CC", "").strip()
        cc_command = shlex.split(configured_cc, posix=os.name != "nt") if configured_cc else []
        compiler = shutil.which(cc_command[0]) if cc_command else None
        if not configured_cc:
            compiler = next((shutil.which(name) for name in ("gcc", "clang", "cc") if shutil.which(name)), None)
        if compiler is None:
            self._native_build_issue("a C compiler was not found; install gcc/clang or set CC")
            return

        project_root = Path(__file__).resolve().parent
        source_dir = project_root / "native" / "gherkin_go"
        if not (source_dir / "go.mod").is_file():
            self._native_build_issue("native/gherkin_go sources are missing from this source distribution")
            return

        package_dir = (Path(self.build_lib) / "pytest_cuke" / "_native_go").resolve()
        package_dir.mkdir(parents=True, exist_ok=True)
        output_path = package_dir / output_name
        header_path = output_path.with_suffix(".h")
        output_path.unlink(missing_ok=True)
        header_path.unlink(missing_ok=True)

        build_env = os.environ.copy()
        build_env["CGO_ENABLED"] = "1"
        if not configured_cc:
            build_env["CC"] = compiler
        result = subprocess.run(
            [go, "build", "-buildmode=c-shared", "-buildvcs=false", "-o", str(output_path), "./bridge"],
            cwd=source_dir,
            env=build_env,
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode:
            output_path.unlink(missing_ok=True)
            header_path.unlink(missing_ok=True)
            details = (result.stderr or result.stdout).strip() or f"go build exited with {result.returncode}"
            self._native_build_issue(f"native Go parser build failed: {details}")
            return

        header_path.unlink(missing_ok=True)

    @staticmethod
    def _native_build_issue(reason: str) -> None:
        if os.environ.get("PYTEST_CUKE_BUILD_GO", "auto").strip().lower() == "required":
            raise RuntimeError(
                f"PYTEST_CUKE_BUILD_GO=required, but {reason}. Install Go and a C compiler, "
                "or build from a host with native Go support."
            )
        warnings.warn(
            f"Skipping optional pytest-cuke Go parser build: {reason}. "
            "Set PYTEST_CUKE_BUILD_GO=required to make build failures fatal.",
            RuntimeWarning,
            stacklevel=2,
        )


class bdist_wheel(_bdist_wheel):
    """Mark wheels containing the native shared library as platform-specific."""

    def initialize_options(self) -> None:
        super().initialize_options()
        self._contains_native_go = False

    def run(self) -> None:
        if not self.skip_build:
            self.run_command("build")
            build_py_command = self.get_finalized_command("build_py")
            native_dir = Path(build_py_command.build_lib) / "pytest_cuke" / "_native_go"
            self._contains_native_go = any(
                (native_dir / name).is_file() for name in _NATIVE_LIBRARY_NAMES
            )
            if self._contains_native_go:
                self.root_is_pure = False
        super().run()

    def get_tag(self) -> tuple[str, str, str]:
        implementation, abi, platform = super().get_tag()
        if self._contains_native_go:
            return "py3", "none", platform
        return implementation, abi, platform


_NATIVE_LIBRARY_NAMES = ("libgherkin_go.so", "gherkin_go.dll", "libgherkin_go.dylib")

setup(cmdclass={"bdist_wheel": bdist_wheel, "build_py": build_py})
