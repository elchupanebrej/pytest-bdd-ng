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
    contract for callers. (SystemExit) and how callers should handle them. Analyze the actual raise statements in the
    source.>

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

import argparse
import filecmp
import importlib
import shutil
import stat
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol, cast

from pytest_bdd.util.packaging import get_distribution_version

SCHEMA_PATH = Path(__file__).parent.parent / "model" / "message_jsonschema"
SCHEMA_REPOSITORY_URL = "https://github.com/cucumber/messages.git"
SCHEMA_REPOSITORY_FOLDER = Path("jsonschema", "src")


class _GitRemote(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    def fetch(self, *args: object, **kwargs: object) -> object:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
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
        ...


class _GitRemotes(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    origin: _GitRemote


class _GitGit(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    def config(self, *args: object, **kwargs: object) -> object:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
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
        ...

    def checkout(self, *args: object, **kwargs: object) -> object:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
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
        ...


class _GitRepo(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    git: _GitGit
    remotes: _GitRemotes

    @classmethod
    def init(cls, path: Path) -> "_GitRepo":
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
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
        ...

    def create_remote(self, name: str, url: str) -> object:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
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
        ...


class _GitModule(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
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

    Repo: type[_GitRepo]


def copy_schema_tree(source: Path, destination: Path) -> None:
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
    if destination.exists():
        destination.chmod(destination.stat().st_mode | stat.S_IWRITE)
    shutil.rmtree(str(destination), ignore_errors=True)
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(source)
            dest_name = rel_path.name
            if dest_name.endswith(".json") and not dest_name.endswith(".schema.json"):
                dest_name = dest_name[:-5] + ".schema.json"
            dest_file = destination / rel_path.parent / dest_name
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest_file)


def fetch_schema_tree(destination: Path) -> None:
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
    git_module = cast("_GitModule", importlib.import_module("git"))
    tag_name = f"v{get_distribution_version('cucumber_messages')}"

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "messages"
        repo_path.mkdir(parents=True)
        repo = git_module.Repo.init(repo_path)
        repo.git.config("core.sparseCheckout", "true")
        repo.create_remote("origin", SCHEMA_REPOSITORY_URL)

        sparse_checkout_file = repo_path / ".git" / "info" / "sparse-checkout"
        with sparse_checkout_file.open("w", encoding="utf-8") as f:
            f.write(f"{SCHEMA_REPOSITORY_FOLDER.as_posix()}/**\n")

        repo.remotes.origin.fetch(f"refs/tags/{tag_name}:refs/tags/{tag_name}")
        repo.git.checkout(tag_name)
        copy_schema_tree(repo_path / SCHEMA_REPOSITORY_FOLDER, destination)


def _are_files_equal(file1: Path, file2: Path) -> bool:
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
    try:
        content1 = file1.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
        content2 = file2.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
    except (OSError, UnicodeDecodeError):
        return filecmp.cmp(file1, file2, shallow=False)
    else:
        return content1 == content2


def collect_schema_drift(expected: Path, actual: Path) -> tuple[str, ...]:
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

    # pylint: disable=missing-responsibility-doc,missing-architecture-score
    def normalize_key(key: str) -> str:
        if key.endswith(".json") and not key.endswith(".schema.json"):
            return key[:-5] + ".schema.json"
        return key

    expected_files = {
        normalize_key(path.relative_to(expected).as_posix()): path for path in expected.rglob("*") if path.is_file()
    }
    actual_files = {
        normalize_key(path.relative_to(actual).as_posix()): path for path in actual.rglob("*") if path.is_file()
    }

    changed = [
        f"changed: {relative_path}"
        for relative_path in sorted(expected_files.keys() & actual_files.keys())
        if not _are_files_equal(expected_files[relative_path], actual_files[relative_path])
    ]
    missing = [f"missing: {relative_path}" for relative_path in sorted(expected_files.keys() - actual_files.keys())]
    extra = [f"extra: {relative_path}" for relative_path in sorted(actual_files.keys() - expected_files.keys())]
    return tuple(changed + missing + extra)


def sync_schema_files(schema_path: Path = SCHEMA_PATH) -> None:
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
    with TemporaryDirectory() as tmpdir:
        fetched_schema_path = Path(tmpdir) / "schema"
        fetch_schema_tree(fetched_schema_path)
        copy_schema_tree(fetched_schema_path, schema_path)


def check_schema_files(schema_path: Path = SCHEMA_PATH) -> tuple[str, ...]:
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
    with TemporaryDirectory() as tmpdir:
        fetched_schema_path = Path(tmpdir) / "schema"
        fetch_schema_tree(fetched_schema_path)
        return collect_schema_drift(fetched_schema_path, schema_path)


def main(argv: list[str] | None = None) -> None:
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
        handling contract for callers. (SystemExit) and how callers should handle them. Analyze the actual raise
        statements in the source.>

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
    parser = argparse.ArgumentParser(description="Synchronize generated Cucumber messages JSON schema assets.")
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=SCHEMA_PATH,
        help="Generated schema directory to update or check.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated schemas differ from the cucumber-messages contract version.",
    )
    args = parser.parse_args(argv)

    if args.check:
        drift = check_schema_files(args.schema_path)
        if drift:
            print("Generated Cucumber messages schemas are stale:", file=sys.stderr)  # noqa: T201  -- stderr output for CI/pre-commit schema validation feedback
            for entry in drift:
                print(f"  {entry}", file=sys.stderr)  # noqa: T201  -- stderr output for CI/pre-commit schema validation feedback
            raise SystemExit(1)
        return

    sync_schema_files(args.schema_path)


if __name__ == "__main__":
    main()
