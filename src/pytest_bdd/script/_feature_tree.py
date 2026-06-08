"""
Feature-tree ordering helpers shared by documentation tooling.

Responsibility:
    Feature-tree ordering helpers shared by documentation tooling. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script._feature_tree` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - OrderedSource: owns nested behavior below this boundary
    - FeatureDirectory: owns nested behavior below this boundary
    - OrderingValidationError: owns nested behavior below this boundary
    - strip_ordering_prefix: owns nested behavior below this boundary
    - source_display_name: owns nested behavior below this boundary
    - classify_source_path: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates path, kind, match, error_code, directory_rel_path; depends on __future__.annotations, re, pathlib.Path,
    typing.Literal, attrs.frozen.

Invariants:
    - `pytest_bdd.script._feature_tree` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises OrderingValidationError, ValueError; callers must treat these as boundary failures.

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

import re
from pathlib import Path
from typing import Literal

from attrs import frozen

SourceKind = Literal["section", "markdown"]

ORDERING_PREFIX_PATTERN = re.compile(r"^(?P<prefix>\d+)[ _-]+(?P<label>.+)$")


@frozen
class OrderedSource:
    """
    Represent a feature-tree source with parsed ordering metadata.

    Responsibility:
        Represent a feature-tree source with parsed ordering metadata. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.OrderedSource` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates path, kind, ordering_prefix, display_name.

    Invariants:
        - `pytest_bdd.script._feature_tree.OrderedSource` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    path: Path
    kind: SourceKind
    ordering_prefix: int
    display_name: str


@frozen
class FeatureDirectory:
    """
    Represent an ordered feature-tree directory.

    Responsibility:
        Represent an ordered feature-tree directory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.FeatureDirectory` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates path, rel_path, files, directories.

    Invariants:
        - `pytest_bdd.script._feature_tree.FeatureDirectory` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    path: Path
    rel_path: Path
    files: tuple[OrderedSource, ...]
    directories: tuple[OrderedSource, ...]


class OrderingValidationError(ValueError):
    """
    Represent ordering validation failures.

    Responsibility:
        Represent ordering validation failures. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.OrderingValidationError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates self.error_code, self.scope_path, self.source_path, self.message.

    Invariants:
        - `pytest_bdd.script._feature_tree.OrderingValidationError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    def __init__(self, error_code: str, scope_path: Path, source_path: Path, message: str) -> None:
        """
        Initialize the ordering validation error.

        Responsibility:
            Initialize the ordering validation error. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.script._feature_tree.OrderingValidationError.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.error_code, self.scope_path, self.source_path, self.message.

        Invariants:
            - `pytest_bdd.script._feature_tree.OrderingValidationError.__init__` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        self.error_code = error_code
        self.scope_path = scope_path
        self.source_path = source_path
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        """
        Return the formatted ordering validation error.

        Returns:
            Formatted validation error.

        Responsibility:
            Return the formatted ordering validation error. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.script._feature_tree.OrderingValidationError.__str__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.scope_path.as_posix: collaborator call used by this boundary
            - self.source_path.as_posix: collaborator call used by this boundary

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
        return (
            f"{self.error_code}: {self.message} "
            f"(scope={self.scope_path.as_posix()}, source={self.source_path.as_posix()})"
        )


def strip_ordering_prefix(name: str) -> str:
    """
    Strip a numeric ordering prefix from a source name.

    Args:
        name: File or directory name.

    Returns:
        Name without an ordering prefix.

    Responsibility:
        Strip a numeric ordering prefix from a source name. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.strip_ordering_prefix` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ORDERING_PREFIX_PATTERN.match: collaborator call used by this boundary
        - match.group.strip: collaborator call used by this boundary
        - match.group: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates match.

    Invariants:
        - `pytest_bdd.script._feature_tree.strip_ordering_prefix` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    match = ORDERING_PREFIX_PATTERN.match(name)
    if match is None:
        return name
    return match.group("label").strip()


def source_display_name(path: Path, kind: SourceKind) -> str:
    """
    Return a display name for an ordered source path.

    Args:
        path: Source path.
        kind: Source kind.

    Returns:
        Human-readable display name.

    Responsibility:
        Return a display name for an ordered source path. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.source_display_name` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - strip_ordering_prefix: collaborator call used by this boundary
        - path.with_suffix: collaborator call used by this boundary

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
    if kind == "section":
        return strip_ordering_prefix(path.name)
    return strip_ordering_prefix(path.with_suffix("").stem)


def classify_source_path(path: Path) -> SourceKind | None:
    """
    Classify a path as a processable feature-tree source.

    Args:
        path: Source path.

    Returns:
        Source kind, or None when path should be ignored.

    Responsibility:
        Classify a path as a processable feature-tree source. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.classify_source_path` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - path.is_dir: collaborator call used by this boundary
        - path.name.endswith: collaborator call used by this boundary

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
    if path.is_dir():
        return "section"
    if path.name.endswith(".feature.md"):
        return "markdown"
    return None


def format_scope_path(scope_rel_path: Path) -> Path:
    """
    Format a relative scope path for error output.

    Args:
        scope_rel_path: Relative scope path.

    Returns:
        Empty path for root scope, otherwise original path.

    Responsibility:
        Format a relative scope path for error output. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.format_scope_path` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - scope_rel_path.as_posix: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

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
    if scope_rel_path.as_posix() == ".":
        return Path()
    return scope_rel_path


def parse_ordered_source(path: Path, kind: SourceKind, scope_rel_path: Path) -> OrderedSource:
    """
    Parse an ordered feature-tree source.

    Args:
        path: Source path.
        kind: Source kind.
        scope_rel_path: Relative directory scope.

    Returns:
        Parsed ordered source.

    Raises:
        OrderingValidationError: If source has no numeric ordering prefix.

    Responsibility:
        Parse an ordered feature-tree source. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.parse_ordered_source` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ORDERING_PREFIX_PATTERN.match: collaborator call used by this boundary
        - OrderingValidationError: collaborator call used by this boundary
        - format_scope_path: collaborator call used by this boundary
        - OrderedSource: collaborator call used by this boundary
        - int: collaborator call used by this boundary
        - match.group: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates match, error_code.

    Invariants:
        - `pytest_bdd.script._feature_tree.parse_ordered_source` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises OrderingValidationError; callers must treat these as boundary failures.

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
    Sort sources by ordering prefix after validating sibling uniqueness.

    Args:
        sources: Parsed ordered sources.
        scope_rel_path: Relative directory scope.

    Returns:
        Sources sorted by numeric ordering prefix.

    Raises:
        OrderingValidationError: If sibling sources share a numeric prefix.

    Responsibility:
        Sort sources by ordering prefix after validating sibling uniqueness. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.sort_ordered_sources` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - OrderingValidationError: collaborator call used by this boundary
        - format_scope_path: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates seen_prefixes, previous, error_code.

    Invariants:
        - `pytest_bdd.script._feature_tree.sort_ordered_sources` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises OrderingValidationError; callers must treat these as boundary failures.

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
    Collect ordered files and directories from a feature-tree directory.

    Args:
        directory_path: Directory to collect.
        features_path: Feature-tree root.

    Returns:
        Tuple of ordered markdown file sources and ordered child directory sources.

    Responsibility:
        Collect ordered files and directories from a feature-tree directory. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.collect_ordered_sources` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sort_ordered_sources: collaborator call used by this boundary
        - directory_path.relative_to: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - directory_path.iterdir: collaborator call used by this boundary
        - classify_source_path: collaborator call used by this boundary
        - parse_ordered_source: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates directory_rel_path, file_sources, directory_sources, kind, ordered_source.

    Invariants:
        - `pytest_bdd.script._feature_tree.collect_ordered_sources` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    Walk a feature tree in deterministic ordering-prefix order.

    Args:
        features_path: Feature-tree root.

    Returns:
        Ordered directory snapshots, including the root directory.

    Raises:
        ValueError: If feature-tree root does not exist or is not a directory.

    Responsibility:
        Walk a feature tree in deterministic ordering-prefix order. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script._feature_tree.walk_feature_tree` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - features_path.exists: collaborator call used by this boundary
        - features_path.is_dir: collaborator call used by this boundary
        - ValueError: collaborator call used by this boundary
        - pending_paths.pop: collaborator call used by this boundary
        - directory_path.relative_to: collaborator call used by this boundary
        - collect_ordered_sources: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates msg, ordered_directories, pending_paths, directory_path, directory_rel_path.

    Invariants:
        - `pytest_bdd.script._feature_tree.walk_feature_tree` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
