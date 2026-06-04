"""Feature-tree ordering helpers shared by documentation tooling."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from attrs import frozen

SourceKind = Literal["section", "markdown"]

ORDERING_PREFIX_PATTERN = re.compile(r"^(?P<prefix>\d+)[ _-]+(?P<label>.+)$")


@frozen
class OrderedSource:
    """Represent a feature-tree source with parsed ordering metadata."""

    path: Path
    kind: SourceKind
    ordering_prefix: int
    display_name: str


@frozen
class FeatureDirectory:
    """Represent an ordered feature-tree directory."""

    path: Path
    rel_path: Path
    files: tuple[OrderedSource, ...]
    directories: tuple[OrderedSource, ...]


class OrderingValidationError(ValueError):
    """Represent ordering validation failures."""

    def __init__(self, error_code: str, scope_path: Path, source_path: Path, message: str) -> None:
        """Initialize the ordering validation error."""
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
