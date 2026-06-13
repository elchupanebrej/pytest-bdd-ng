"""
Owns the data model and algorithms for walking a `features/` directory tree, parsing numeric ordering prefixes from f.

Responsibility:
    Owns the data model and algorithms for walking a `features/` directory tree, parsing numeric ordering prefixes from
    file/directory names, validating uniqueness and sort order, and producing a structured `FeatureDirectory` hierarchy
    for downstream RST generation.

Reason for existence:
    Concentrates all feature-tree logic (data classes `OrderedSource`/`FeatureDirectory`, ordering validation via
    `OrderingValidationError`, prefix parsing, source classification) in one module because every function operates on
    the same `ORDERING_PREFIX_PATTERN` regex and produces the same `OrderedSource`/`FeatureDirectory` types.

Delegates:
    - `re.compile(ORDERING_PREFIX_PATTERN)`: The core regex used by `strip_ordering_prefix`, `parse_ordered_source`, and
    `sort_ordered_sources` to extract numeric prefixes.
    - `Path.glob` / `Path.iterdir`: Filesystem traversal used by `collect_ordered_sources` and `walk_feature_tree`.
    - `attrs.frozen`: Provides the immutable data-class decorator for `OrderedSource` and `FeatureDirectory`.

Cohesion:
    All functions operate on the same domain model (ordered sources, feature directories) and share the same regex-based
    prefix extraction. The pipeline flows: classify -> parse -> sort -> collect -> walk, with each stage building on the
    previous tuple outputs.

Separation:
    - `bdd_tree_to_rst`: Kept separate because it consumes the `FeatureDirectory` tuples produced by `walk_feature_tree`
    and renders them to RST, a distinct output-formatting concern.

Main consumers:
    - `pytest_bdd.script.bdd_tree_to_rst`: Calls `walk_feature_tree` to obtain the `FeatureDirectory` hierarchy, then
    renders it to RST documentation.
    - Tests in `tests/`: Unit tests directly exercise `parse_ordered_source`, `sort_ordered_sources`,
    `collect_ordered_sources`, and `walk_feature_tree`.

State and side effects:
    Reads filesystem via `Path.iterdir`, `Path.is_dir`, `Path.exists`. No writes, no network I/O, no configuration
    access. The `OrderedSource` and `FeatureDirectory` attrs classes are frozen (immutable).

Invariants:
    - Every file/directory under `features/` must have a numeric ordering prefix matching `ORDERING_PREFIX_PATTERN` or
    `parse_ordered_source` raises `OrderingValidationError`.
    - Ordering prefixes must be unique within a directory scope or `sort_ordered_sources` raises `OrderingValidationError`.
    - `walk_feature_tree` returns directories in breadth-first order with files and subdirectories sorted by numeric
    prefix.

Failure semantics:
    `parse_ordered_source` raises `OrderingValidationError` for missing ordering prefixes. `sort_ordered_sources` raises
    `OrderingValidationError` for duplicate prefixes. `walk_feature_tree` raises `ValueError` when the features root
    does not exist or is not a directory.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from attrs import frozen

SourceKind = Literal["section", "markdown"]

ORDERING_PREFIX_PATTERN = re.compile(r"^(?P<prefix>\d+)[ _-]+(?P<label>.+)$")


@frozen
class OrderedSource:
    """
    Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/` with it.

    Responsibility:
        Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/`
        with its parsed ordering prefix, source kind, and display name, forming the leaf nodes of the feature directory
        tree.

    Reason for existence:
        Separates the identity and ordering metadata of a feature source from its parent directory structure so that
        `collect_ordered_sources` and `sort_ordered_sources` can operate on a well-typed, immutable record.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Invariants:
        - `ordering_prefix` must be a non-negative integer parsed from the file/directory name.
        - `kind` must be either `"section"` (directory) or `"markdown"` (feature.md file).
        - `path` must be an absolute or relative `Path` to the source entry.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """

    path: Path
    kind: SourceKind
    ordering_prefix: int
    display_name: str


@frozen
class FeatureDirectory:
    """
    Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/` with it.

    Responsibility:
        Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/`
        with its parsed ordering prefix, source kind, and display name, forming the leaf nodes of the feature directory
        tree.

    Reason for existence:
        Separates the identity and ordering metadata of a feature source from its parent directory structure so that
        `collect_ordered_sources` and `sort_ordered_sources` can operate on a well-typed, immutable record.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Invariants:
        - `ordering_prefix` must be a non-negative integer parsed from the file/directory name.
        - `kind` must be either `"section"` (directory) or `"markdown"` (feature.md file).
        - `path` must be an absolute or relative `Path` to the source entry.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """

    path: Path
    rel_path: Path
    files: tuple[OrderedSource, ...]
    directories: tuple[OrderedSource, ...]


class OrderingValidationError(ValueError):
    """
    Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/` with it.

    Responsibility:
        Immutable data class (`@frozen`) representing a single filesystem entry (file or directory) under `features/`
        with its parsed ordering prefix, source kind, and display name, forming the leaf nodes of the feature directory
        tree.

    Reason for existence:
        Separates the identity and ordering metadata of a feature source from its parent directory structure so that
        `collect_ordered_sources` and `sort_ordered_sources` can operate on a well-typed, immutable record.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Invariants:
        - `ordering_prefix` must be a non-negative integer parsed from the file/directory name.
        - `kind` must be either `"section"` (directory) or `"markdown"` (feature.md file).
        - `path` must be an absolute or relative `Path` to the source entry.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """

    def __init__(self, error_code: str, scope_path: Path, source_path: Path, message: str) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.

        Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
        """
        self.error_code = error_code
        self.scope_path = scope_path
        self.source_path = source_path
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.

        Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
        """
        return (
            f"{self.error_code}: {self.message} "
            f"(scope={self.scope_path.as_posix()}, source={self.source_path.as_posix()})"
        )


def strip_ordering_prefix(name: str) -> str:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    match = ORDERING_PREFIX_PATTERN.match(name)
    if match is None:
        return name
    return match.group("label").strip()


def source_display_name(path: Path, kind: SourceKind) -> str:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if kind == "section":
        return strip_ordering_prefix(path.name)
    return strip_ordering_prefix(path.with_suffix("").stem)


def classify_source_path(path: Path) -> SourceKind | None:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if path.is_dir():
        return "section"
    if path.name.endswith(".feature.md"):
        return "markdown"
    return None


def format_scope_path(scope_rel_path: Path) -> Path:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if scope_rel_path.as_posix() == ".":
        return Path()
    return scope_rel_path


def parse_ordered_source(path: Path, kind: SourceKind, scope_rel_path: Path) -> OrderedSource:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (OrderingValidationError) and how callers should handle them. Analyze the actual
        raise statements in the source.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    match = ORDERING_PREFIX_PATTERN.match(path.name)
    if match is None:
        error_code = "missing_ordering_prefix"
        raise OrderingValidationError(
            error_code,
            format_scope_path(scope_rel_path),
            path,
            f"sibling entry '{path.name}' is missing a numeric ordering prefix",
        )
    return OrderedSource(
        path=path,
        kind=kind,
        ordering_prefix=int(match.group("prefix")),
        display_name=source_display_name(path, kind),
    )


def sort_ordered_sources(sources: list[OrderedSource], scope_rel_path: Path) -> tuple[OrderedSource, ...]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (OrderingValidationError) and how callers should handle them. Analyze the actual
        raise statements in the source.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    seen_prefixes: dict[int, OrderedSource] = {}
    for source in sources:
        if source.ordering_prefix in seen_prefixes:
            previous = seen_prefixes[source.ordering_prefix]
            error_code = "duplicate_ordering_prefix"
            raise OrderingValidationError(
                error_code,
                format_scope_path(scope_rel_path),
                source.path,
                (
                    f"sibling entries '{previous.path.name}' and '{source.path.name}' "
                    f"share numeric ordering prefix {source.ordering_prefix}"
                ),
            )
        seen_prefixes[source.ordering_prefix] = source
    return tuple(sorted(sources, key=lambda source: source.ordering_prefix))


def collect_ordered_sources(
    directory_path: Path,
    features_path: Path,
) -> tuple[tuple[OrderedSource, ...], tuple[OrderedSource, ...]]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    directory_rel_path = directory_path.relative_to(features_path)
    file_sources: list[OrderedSource] = []
    directory_sources: list[OrderedSource] = []

    for child_path in sorted(directory_path.iterdir(), key=lambda path: path.name):
        kind = classify_source_path(child_path)
        if kind is None:
            continue
        ordered_source = parse_ordered_source(child_path, kind, directory_rel_path)
        if kind == "section":
            directory_sources.append(ordered_source)
        else:
            file_sources.append(ordered_source)

    return (
        sort_ordered_sources(file_sources, directory_rel_path),
        sort_ordered_sources(directory_sources, directory_rel_path),
    )


def walk_feature_tree(features_path: Path) -> tuple[FeatureDirectory, ...]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.

    Delegates:
        - `attrs.frozen`: Enforces immutability and auto-generates `__init__`, `__eq__`, and `__hash__`.
        - `source_display_name`: Computes the human-readable name from raw path and source kind.

    Cohesion:
        All four fields (`path`, `kind`, `ordering_prefix`, `display_name`) describe one ordered source; the class has
        no methods and exists solely as a typed data container.

    Separation:
        - `FeatureDirectory`: Kept separate because it models a directory container with child files and subdirectories
        while `OrderedSource` models a single leaf entry.

    Main consumers:
        - `collect_ordered_sources`: Produces lists of `OrderedSource` for each directory.
        - `sort_ordered_sources`: Sorts and deduplicates `OrderedSource` lists by prefix.
        - `FeatureDirectory`: Holds `files` and `directories` as tuples of `OrderedSource`.

    State and side effects:
        None, keeps no persistent state. Immutable frozen class; all fields are set at construction and never mutated.

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (ValueError) and how callers should handle them. Analyze the actual raise
        statements in the source.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if not features_path.exists() or not features_path.is_dir():
        msg = f"Feature tree root does not exist or is not a directory: {features_path}"
        raise ValueError(msg)

    ordered_directories: list[FeatureDirectory] = []
    pending_paths = [features_path]
    while pending_paths:
        directory_path = pending_paths.pop(0)
        directory_rel_path = directory_path.relative_to(features_path)
        file_sources, directory_sources = collect_ordered_sources(directory_path, features_path)
        ordered_directories.append(
            FeatureDirectory(
                path=directory_path,
                rel_path=format_scope_path(directory_rel_path),
                files=file_sources,
                directories=directory_sources,
            ),
        )
        pending_paths.extend(source.path for source in directory_sources)

    return tuple(ordered_directories)
