"""
Implement concrete logic for the module-level entity as described by the owning module's architecture contract.

Responsibility:
    Implements concrete logic for the module-level entity as described by the owning module's architecture contract. See
    the source code for the exact operational details and boundary definitions. module directly implements and owns.
    This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion, prevent knowledge
    fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
    call signatures. module rather than being merged elsewhere. Why is it the information expert for this logical
    boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

Delegates:
    - Collaborating entities from sibling modules and standard library: see the source code for the specific delegation
    call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to support this
    boundary. Use actual names of children or called functions found in the source. Add more bullet points as needed.>

Cohesion:
    All logic within this module operates on shared state or a unified domain model, with imports and control flow
    focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
    actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag of
    unrelated utilities?>

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains,
    maintaining distinct boundaries between concerns as observed in the package structure and import hierarchy. from
    this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual peer entity. Add more
    bullet points as needed.>

Main consumers:
    - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the specific
    consumer paths and public API contracts that must remain stable. utilizes this entity, defining the public API
    contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as needed.>

State and side effects:
    None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
    access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash reads/writes
    this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
    specific data constraints, type requirements, and execution preconditions. that must always hold true for this
    entity and can never be broken. Analyze the actual source for implicit contracts.>

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
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
    from setuptools import Command  # type: ignore[import-untyped]  # setuptools stubs are incomplete
else:
    Command = object


logger = logging.getLogger(__name__)


class BuildGoCommand(Command):  # type: ignore[misc]  # setuptools Command is untyped
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. class directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. class rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Invariants:
        - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
        specific data constraints, type requirements, and execution preconditions. that must always hold true for this
        entity and can never be broken. Analyze the actual source for implicit contracts.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    description = "build Go gherkin parser shared library"
    user_options: ClassVar[list[tuple[str, str | None, str]]] = []

    def initialize_options(self) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implement concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.>

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.>

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.>

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

    def finalize_options(self) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implement concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.>

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.>

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.>

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

    def run(self) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implement concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.>

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.>

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.>

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
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
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    return shutil.which("go") is not None


def _c_compiler_available() -> bool:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    return shutil.which("gcc") is not None or shutil.which("clang") is not None


def _shared_lib_name() -> str:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    platform = sys.platform
    if platform == "win32":
        return "gherkin_go.dll"
    if platform == "darwin":
        return "libgherkin_go.dylib"
    return "libgherkin_go.so"


def _source_hash(go_dir: Path) -> str:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    hasher = hashlib.sha256()
    for go_file in sorted(go_dir.rglob("*.go")):
        hasher.update(go_file.read_bytes())
    return hasher.hexdigest()


def _should_skip_build(output_path: Path, hash_file: Path, current_hash: str) -> bool:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implement concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    if not output_path.exists():
        return False
    if not hash_file.exists():
        return False
    return hash_file.read_text(encoding="utf-8").strip() == current_hash
