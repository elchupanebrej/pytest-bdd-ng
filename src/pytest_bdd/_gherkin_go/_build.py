"""Setuptools command to build the Go gherkin parser shared library."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from setuptools import Command
else:
    Command = object


logger = logging.getLogger(__name__)


class BuildGoCommand(Command):
    """Compile the Go gherkin parser to a shared library via cgo."""

    description = "build Go gherkin parser shared library"
    user_options: ClassVar[list[tuple[str, str | None, str]]] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        if not _go_available():
            logger.warning("Go toolchain not found on PATH; skipping gherkin-go library build")
            return

        if not _c_compiler_available():
            logger.warning("C compiler not found; cgo requires gcc/clang. Skipping gherkin-go library build")
            return

        go_dir = Path("gherkin_go", "bridge")
        if not go_dir.is_dir():
            logger.warning("Go source directory %s not found; skipping build", go_dir)
            return

        output_dir = Path("src", "pytest_bdd", "_gherkin_go")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = _shared_lib_name()
        output_path = output_dir / output_name

        hash_value = _source_hash(go_dir)
        hash_file = output_dir / ".gherkin_go_build_hash"

        if _should_skip_build(output_path, hash_file, hash_value):
            logger.info("Go gherkin parser sources unchanged; skipping build")
            return

        logger.info("Building Go gherkin parser shared library...")
        cmd = ["go", "build", "-buildmode=c-shared"]
        if sys.platform == "win32":
            cmd.extend(["-ldflags", "-extldflags=-static"])
        cmd.extend(["-o", str(output_path), "."])
        try:
            subprocess.run(
                cmd,
                cwd=str(go_dir),
                check=True,
                env={**os.environ, "CGO_ENABLED": "1"},
            )
            hash_file.write_text(hash_value)
            logger.info("Go gherkin parser built successfully: %s", output_path)
        except subprocess.CalledProcessError as exc:
            logger.warning("Go gherkin parser build failed: %s. Skipping.", exc)
            if output_path.exists():
                output_path.unlink()


def _go_available() -> bool:
    return shutil.which("go") is not None


def _c_compiler_available() -> bool:
    return shutil.which("gcc") is not None or shutil.which("clang") is not None


def _shared_lib_name() -> str:
    platform = sys.platform
    if platform == "win32":
        return "gherkin_go.dll"
    if platform == "darwin":
        return "libgherkin_go.dylib"
    return "libgherkin_go.so"


def _source_hash(go_dir: Path) -> str:
    hasher = hashlib.sha256()
    for go_file in sorted(go_dir.rglob("*.go")):
        hasher.update(go_file.read_bytes())
    return hasher.hexdigest()


def _should_skip_build(output_path: Path, hash_file: Path, current_hash: str) -> bool:
    if not output_path.exists():
        return False
    if not hash_file.exists():
        return False
    return hash_file.read_text(encoding="utf-8").strip() == current_hash
