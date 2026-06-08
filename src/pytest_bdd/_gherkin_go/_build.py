"""
Setuptools command to build the Go gherkin parser shared library.

Responsibility:
    Setuptools command to build the Go gherkin parser shared library. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._gherkin_go._build` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - BuildGoCommand: owns nested behavior below this boundary
    - _go_available: owns nested behavior below this boundary
    - _c_compiler_available: owns nested behavior below this boundary
    - _shared_lib_name: owns nested behavior below this boundary
    - _source_hash: owns nested behavior below this boundary
    - _should_skip_build: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates Command, logger, description, user_options, go_dir; depends on __future__.annotations, hashlib, logging, os,
    shutil.

Invariants:
    - `pytest_bdd._gherkin_go._build` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

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
    """
    Compile the Go gherkin parser to a shared library via cgo.

    Responsibility:
        Compile the Go gherkin parser to a shared library via cgo. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build.BuildGoCommand` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - initialize_options: owns nested behavior below this boundary
        - finalize_options: owns nested behavior below this boundary
        - run: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates description, user_options, go_dir, output_dir, output_name.

    Invariants:
        - `pytest_bdd._gherkin_go._build.BuildGoCommand` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    description = "build Go gherkin parser shared library"
    user_options: ClassVar[list[tuple[str, str | None, str]]] = []

    def initialize_options(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._build.BuildGoCommand.initialize_options` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._build.BuildGoCommand.initialize_options`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def finalize_options(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._build.BuildGoCommand.finalize_options` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._build.BuildGoCommand.finalize_options`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """

    def run(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._build.BuildGoCommand.run` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._build.BuildGoCommand.run` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - logger.warning: collaborator call used by this boundary
            - logger.info: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - cmd.extend: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - _go_available: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `run`
            - src/pytest_bdd/model/feature_binding.py: imports or references `run`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `run`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `run`
            - src/pytest_bdd/model/run_access.py: imports or references `run`

        State and side effects:
            mutates go_dir, output_dir, output_name, output_path, hash_value.

        Invariants:
            - `pytest_bdd._gherkin_go._build.BuildGoCommand.run` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.warning("Go gherkin parser build failed: %s. Skipping.", exc)
            if output_path.exists():
                output_path.unlink()


def _go_available() -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd._gherkin_go._build._go_available` owns documented function behavior.
        It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build._go_available` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - shutil.which: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return shutil.which("go") is not None


def _c_compiler_available() -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd._gherkin_go._build._c_compiler_available` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build._c_compiler_available` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - shutil.which: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return shutil.which("gcc") is not None or shutil.which("clang") is not None


def _shared_lib_name() -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd._gherkin_go._build._shared_lib_name` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build._shared_lib_name` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates platform.

    Invariants:
        - `pytest_bdd._gherkin_go._build._shared_lib_name` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    platform = sys.platform
    if platform == "win32":
        return "gherkin_go.dll"
    if platform == "darwin":
        return "libgherkin_go.dylib"
    return "libgherkin_go.so"


def _source_hash(go_dir: Path) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd._gherkin_go._build._source_hash` owns documented function behavior.
        It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build._source_hash` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - hashlib.sha256: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - go_dir.rglob: collaborator call used by this boundary
        - hasher.update: collaborator call used by this boundary
        - go_file.read_bytes: collaborator call used by this boundary
        - hasher.hexdigest: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates hasher.

    Invariants:
        - `pytest_bdd._gherkin_go._build._source_hash` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    hasher = hashlib.sha256()
    for go_file in sorted(go_dir.rglob("*.go")):
        hasher.update(go_file.read_bytes())
    return hasher.hexdigest()


def _should_skip_build(output_path: Path, hash_file: Path, current_hash: str) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd._gherkin_go._build._should_skip_build` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._build._should_skip_build` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - output_path.exists: collaborator call used by this boundary
        - hash_file.exists: collaborator call used by this boundary
        - hash_file.read_text.strip: collaborator call used by this boundary
        - hash_file.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if not output_path.exists():
        return False
    if not hash_file.exists():
        return False
    return hash_file.read_text(encoding="utf-8").strip() == current_hash
