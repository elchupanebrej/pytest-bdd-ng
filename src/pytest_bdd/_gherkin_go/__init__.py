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

Failure semantics:
    Refer to the source code for the specific exception types raised by this entity and the documented error-handling
    contract for callers. (GherkinGoNotAvailable, GherkinParseError) and how callers should handle them. Analyze the
    actual raise statements in the source.>

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

import json
import logging
import os
from typing import TYPE_CHECKING, cast

from pytest_bdd._gherkin_go._bridge import gherkin_go_available
from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError
from pytest_bdd.mimetype import Mimetype

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

_go_version_logged = False

_GO_INSTALL_HINT = (
    "PYTEST_BDD_GHERKIN_BACKEND=go but go-parser not installed. Install with: pip install pytest-bdd-ng[go-parser]"
)


def _get_parser() -> Callable[[str, str], dict[str, object]]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()

    if backend == "go":
        _check_go_available()  # noqa: PLC0415  -- conditional runtime import to defer Go library loading
        from pytest_bdd._gherkin_go import (
            parse as go_parse,  # noqa: PLC0415  -- conditional runtime import to defer Go library loading
        )

        return go_parse

    if backend == "python":
        from gherkin.parser import (
            Parser as GherkinParser,  # noqa: PLC0415  -- conditional runtime import, parser only needed in this backend branch
        )

        logger.debug("Using Python gherkin parser (PYTEST_BDD_GHERKIN_BACKEND=python)")

        def _python_parse_backend(text: str, uri: str = "<string>") -> dict[str, object]:
            """
            Implement concrete logic for the method/function-level entity as described by the owning module's architecture contr.

            Responsibility:
            Implements concrete logic for the method/function-level entity as described by the owning module's
            architecture contract. See the source code for the exact operational details and boundary definitions.
            function directly implements and owns. This defines the boundary for where changes to this logic belong.
            Must be at least 140 characters.>

            Reason for existence:
                Consolidates related logic within a single method/function boundary to maintain high cohesion, prevent
                knowledge fragmentation, and serve as the information expert for its domain concepts as observed in the
                source imports and call signatures. function rather than being merged elsewhere. Why is it the
                information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure
                knowledge. Must be at least 140 characters.>

            Delegates:
                - Collaborating entities from sibling modules and standard library: see the source code for the specific
                delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator
                performs to support this boundary. Use actual names of children or called functions found in the source.
                Add more bullet points as needed.>

            Cohesion:
                All logic within this method/function operates on shared state or a unified domain model, with imports
                and control flow focused on a single responsibility as observed in the source code structure and data
                dependencies. Analyze the actual source: do all functions operate on same local state? Share same
                imports and control flow? Or is it a bag of unrelated utilities?>

            Separation:
                - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated
                knowledge domains, maintaining distinct boundaries between concerns as observed in the package structure
                and import hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once.
                Name the actual peer entity. Add more bullet points as needed.>

            Main consumers:
                - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
                specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining
                the public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet
                points as needed.>

            State and side effects:
                None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O,
                configuration access, or pytest stash interactions implemented by this entity. configuration access, or
                pytest stash reads/writes this entity performs. Analyze the actual source code. If stateless, specify
                'None, keeps no persistent state'.>

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
            # noqa: ARG001  -- uri parameter unused in Python backend; required by parser protocol signature
            return cast("dict[str, object]", GherkinParser().parse(text))

        return _python_parse_backend

    # auto or unknown value
    if backend != "auto":
        logger.warning("Unknown PYTEST_BDD_GHERKIN_BACKEND value '%s', treating as 'auto'", backend)

    try:
        from pytest_bdd._gherkin_go._bridge import (
            gherkin_go_available,  # noqa: PLC0415  -- conditional runtime import inside try block
        )

        if gherkin_go_available():
            from pytest_bdd._gherkin_go import (
                parse as go_parse,  # noqa: PLC0415  -- conditional runtime import after availability check
            )

            logger.info("Using Go gherkin parser backend")
            return go_parse
    except ImportError:
        pass

    logger.debug("Go gherkin parser unavailable, using Python fallback")
    from gherkin.parser import (
        Parser as GherkinParser,  # noqa: PLC0415  -- fallback runtime import, deferred until auto-detection path
    )

    def _python_parse_auto(text: str, uri: str = "<string>") -> dict[str, object]:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. function directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. function rather than being merged elsewhere. Why is it the information
            expert for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must
            be at least 140 characters.>

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
        return cast("dict[str, object]", GherkinParser().parse(text))

    return _python_parse_auto


def _check_go_available() -> None:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (GherkinGoNotAvailable) and how callers should handle them. Analyze the actual
        raise statements in the source.>

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
    if not gherkin_go_available():
        raise GherkinGoNotAvailable(_GO_INSTALL_HINT)


def should_use_go_backend() -> bool:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()
    if backend == "python":
        return False
    if backend not in {"auto", "go"}:
        logger.warning("Unknown PYTEST_BDD_GHERKIN_BACKEND value '%s', treating as 'auto'", backend)
    return True


def is_strict_go_mode() -> bool:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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
    return os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower() == "go"


def _log_version() -> None:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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
    global _go_version_logged
    if _go_version_logged:
        return
    _go_version_logged = True
    try:
        from pytest_bdd._gherkin_go._bridge import (
            gherkin_go_version,  # noqa: PLC0415  -- deferred import, only used when version logging is needed
        )

        logger.info("Using Go gherkin parser %s", gherkin_go_version())
    except Exception:  # noqa: BLE001  -- version logging is best-effort; any failure must not abort parser initialization
        logger.debug("Failed to retrieve Go parser version", exc_info=True)


def parse(text: str, uri: str = "<string>") -> dict[str, object]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (GherkinGoNotAvailable, GherkinParseError) and how callers should handle them.
        Analyze the actual raise statements in the source.>

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
    from pytest_bdd._gherkin_go._bridge import parse_gherkin_document, parse_gherkin_markdown

    if not gherkin_go_available():
        msg = "Go shared library not found in package data"
        logger.warning("Go gherkin parser unavailable (%s)", msg)
        raise GherkinGoNotAvailable(msg)

    json_str = parse_gherkin_markdown(text) if uri.endswith(".md") else parse_gherkin_document(text)

    result = json.loads(json_str)
    if not isinstance(result, dict):
        raise GherkinParseError(result)

    _log_version()
    return result
