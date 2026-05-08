"""
Converts directory tree containing Gherkin files into a tree which would be included into rst files.

Usage:
    bdd_tree_to_rst.py [--snapshot=<snapshot_path>] <features_dir> <output_dir>

Options:
    --snapshot=<snapshot_path> Path to save snapshot on found diff between old and new documentation
"""

from __future__ import annotations

import re
import sys
from collections import deque
from filecmp import dircmp
from functools import lru_cache, reduce
from operator import truediv
from os.path import commonpath
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Protocol, cast

import pypandoc  # type: ignore[import-not-found, import-untyped]
from attrs import frozen
from docopt import docopt
from jinja2 import Environment, Template
from pathlib2 import Path  # type: ignore[import-not-found, import-untyped]

from pytest_bdd.compatibility.importlib.resources import files

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

SECTION_SYMBOLS = "-~^\"$%&'()*+,./:;<=>?@[\\]^_`{|}#!="
AUTO_GENERATED_START_MARKER = ".. BEGIN AUTO-GENERATED FEATURES TREE"
AUTO_GENERATED_END_MARKER = ".. END AUTO-GENERATED FEATURES TREE"
ORDERING_PREFIX_PATTERN = re.compile(r"^(?P<prefix>\d+)[ _-]+(?P<label>.+)$")
TEMPLATE_ENV = Environment(autoescape=False, keep_trailing_newline=True)  # noqa: S701


class _DirCmp(Protocol):
    diff_files: list[str]
    left_only: list[str]
    right_only: list[str]
    subdirs: Mapping[str, _DirCmp]

    def report(self) -> None: ...


@frozen
class ToctreeSection:
    """Represent toctree section state."""

    heading: str
    depth: int
    entries: tuple[str, ...]


@frozen
class OrderedSource:
    """Represent ordered source state."""

    path: Path
    kind: str
    ordering_prefix: int
    display_name: str


class OrderingValidationError(ValueError):
    """Represent ordering validation error failures."""

    def __init__(self, error_code: str, scope_path: Path, source_path: Path, message: str) -> None:
        """Initialize the ordering validation error."""
        self.error_code = error_code
        self.scope_path = scope_path
        self.source_path = source_path
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        """
        Return the formatted heading validation error.

        Returns:
            Formatted error string.

        """
        return (
            f"{self.error_code}: {self.message} "
            f"(scope={self.scope_path.as_posix()}, source={self.source_path.as_posix()})"
        )


@lru_cache(maxsize=8)
def load_template(template_name: str) -> Template:
    """
    Load a Jinja2 template by name.

    Args:
        template_name: Name of the template file.

    Returns:
        Compiled Jinja2 template.

    """
    template_source = files("pytest_bdd.template").joinpath(template_name).read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


def diff_folders(dcmp: _DirCmp) -> list[object] | None:
    """
    Compare two directory trees and return differences.

    Args:
        dcmp: Directory comparison object.

    Returns:
        List of differences or None if identical.

    """
    diff: list[object] = [dcmp.diff_files, dcmp.left_only, dcmp.right_only]
    if any(diff):
        dcmp.report()
        return diff
    subdiffs: list[object] = [result for child in dcmp.subdirs.values() if (result := diff_folders(child)) is not None]
    if any(subdiffs):
        return subdiffs
    return None


def extract_existing_intro(
    existing_index_file: Path,
    top_level_headings: Sequence[str],
) -> tuple[str, str]:
    """
    Extract intro and suffix from existing index file.

    Args:
        existing_index_file: Path to existing index.rst.
        top_level_headings: List of top-level heading names.

    Returns:
        Tuple of (intro_text, suffix_text).

    """
    if not existing_index_file.exists():
        return "", ""

    existing_content = existing_index_file.read_text(encoding="utf-8")

    if AUTO_GENERATED_START_MARKER in existing_content and AUTO_GENERATED_END_MARKER in existing_content:
        before_generated, _, generated_and_suffix = existing_content.partition(AUTO_GENERATED_START_MARKER)
        _, _, suffix = generated_and_suffix.partition(AUTO_GENERATED_END_MARKER)
        return before_generated.rstrip("\n"), suffix.lstrip("\n").rstrip("\n")

    heading_matches = []
    for heading in top_level_headings:
        heading_block = f"{heading}\n{SECTION_SYMBOLS[0] * len(heading)}\n.. toctree::"
        if (index := existing_content.find(heading_block)) != -1:
            heading_matches.append(index)

    if heading_matches:
        return existing_content[: min(heading_matches)].rstrip("\n"), ""

    return existing_content.rstrip("\n"), ""


def render_toctree_section(section: ToctreeSection) -> str:
    """
    Render a toctree section as RST.

    Args:
        section: Toctree section to render.

    Returns:
        Rendered RST string.

    """
    underline = SECTION_SYMBOLS[section.depth - 1] * len(section.heading) if section.heading else ""
    template = load_template("features_section.rst.jinja2")
    rendered_section = cast(
        "str",
        template.render(
            heading=section.heading,
            underline=underline,
            entries=section.entries,
        ),
    )
    return rendered_section.lstrip("\n").rstrip("\n")


def render_index_document(intro_block: str, sections_content: str, suffix_block: str) -> str:
    """
    Render the index document as RST.

    Args:
        intro_block: Intro text before generated content.
        sections_content: Rendered sections content.
        suffix_block: Suffix text after generated content.

    Returns:
        Complete rendered index document.

    """
    template = load_template("features_index.rst.jinja2")
    rendered_index = cast(
        "str",
        template.render(
            intro_block=intro_block,
            start_marker=AUTO_GENERATED_START_MARKER,
            end_marker=AUTO_GENERATED_END_MARKER,
            sections_content=sections_content,
            suffix_block=suffix_block,
        ),
    )
    return rendered_index.rstrip("\n") + "\n"


def render_generated_index(
    sections: Sequence[ToctreeSection],
    existing_index_file: Path,
) -> str:
    """
    Render the generated index document.

    Args:
        sections: Toctree sections to render.
        existing_index_file: Path to existing index file.

    Returns:
        Complete rendered index.

    """
    top_level_headings = [section.heading for section in sections if section.depth == 1 and section.heading]
    preserved_intro, preserved_suffix = extract_existing_intro(existing_index_file, top_level_headings)
    sections_content = "\n\n".join(map(render_toctree_section, sections)).rstrip("\n")
    return render_index_document(
        preserved_intro.rstrip("\n"),
        sections_content,
        preserved_suffix.lstrip("\n").rstrip("\n"),
    )


def strip_ordering_prefix(name: str) -> str:
    """
    Strip ordering prefix from a name.

    Args:
        name: Name to strip prefix from.

    Returns:
        Name without ordering prefix.

    """
    match = ORDERING_PREFIX_PATTERN.match(name)
    if match is None:
        return name
    return match.group("label").strip()


def source_display_name(path: Path, kind: str) -> str:
    """
    Get display name for a source path.

    Args:
        path: Source path.
        kind: Source kind (section, markdown, etc).

    Returns:
        Display name for the source.

    """
    if kind == "section":
        return strip_ordering_prefix(path.name)
    if kind == "markdown":
        return strip_ordering_prefix(path.with_suffix("").stem)
    return strip_ordering_prefix(path.stem)


def classify_source_path(path: Path) -> str:
    """
    Classify a source path into a category.

    Args:
        path: Path to classify.

    Returns:
        Category string (section, markdown, yaml, gherkin, ignore).

    """
    if path.is_dir():
        return "section"
    if path.name.endswith((".gherkin.md", ".feature.md")):
        return "markdown"
    if path.name.endswith(".bdd.yaml"):
        return "yaml"
    if path.name.endswith((".gherkin", ".feature")):
        return "gherkin"
    return "ignore"


def format_scope_path(scope_rel_path: Path) -> Path:
    """
    Format a scope path for display.

    Args:
        scope_rel_path: Relative scope path.

    Returns:
        Formatted path.

    """
    if scope_rel_path.as_posix() == ".":
        return Path(".")
    return scope_rel_path


def parse_ordered_source(path: Path, kind: str, scope_rel_path: Path) -> OrderedSource:
    """
    Parse an ordered source from a path.

    Args:
        path: Path to parse.
        kind: Source kind.
        scope_rel_path: Relative scope path.

    Returns:
        Parsed ordered source.

    Raises:
        OrderingValidationError: If the operation cannot be completed.

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


def sort_ordered_sources(sources: Sequence[OrderedSource], scope_rel_path: Path) -> list[OrderedSource]:
    """
    Sort ordered sources by ordering prefix.

    Args:
        sources: Sources to sort.
        scope_rel_path: Relative scope path.

    Returns:
        Sorted list of sources.

    Raises:
        OrderingValidationError: If the operation cannot be completed.

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
    return sorted(sources, key=lambda source: source.ordering_prefix)


def collect_ordered_sources(
    processable_path: Path,
    features_path: Path,
) -> tuple[list[OrderedSource], list[OrderedSource]]:
    """
    Collect ordered sources from a directory.

    Args:
        processable_path: Directory to collect from.
        features_path: Features root path.

    Returns:
        Tuple of (file_sources, directory_sources).

    """
    processable_rel_path = processable_path.relative_to(features_path)
    ordered_file_sources: list[OrderedSource] = []
    ordered_dir_sources: list[OrderedSource] = []

    for child_path in processable_path.iterdir():
        kind = classify_source_path(child_path)
        if kind == "ignore":
            continue
        ordered_source = parse_ordered_source(child_path, kind, processable_rel_path)
        if kind == "section":
            ordered_dir_sources.append(ordered_source)
        else:
            ordered_file_sources.append(ordered_source)

    return (
        sort_ordered_sources(ordered_file_sources, processable_rel_path),
        sort_ordered_sources(ordered_dir_sources, processable_rel_path),
    )


def render_include_page(title: str, rel_path: Path, include_path: str, code_type: str) -> str:
    """
    Render an include page in RST format.

    Args:
        title: Page title.
        rel_path: Relative path.
        include_path: Path to include.
        code_type: Type of code (e.g., gherkin, yaml).

    Returns:
        Rendered include page.

    """
    template = load_template("feature_include.rst.jinja2")
    rendered_include = cast(
        "str",
        template.render(
            title=title,
            underline=SECTION_SYMBOLS[len(rel_path.parts) - 1] * len(title),
            include_path=include_path,
            code_type=code_type,
        ),
    )
    return rendered_include.rstrip("\n") + "\n"


def convert(features_path: Path, output_path: Path, temp_path: Path) -> None:
    """
    Convert feature files to RST documentation.

    Args:
        features_path: Path to features directory.
        output_path: Output path for RST files.
        temp_path: Temporary directory for processing.

    """
    base_output_common_path = Path(commonpath([str(features_path), str(output_path)]))
    features_path_rel_to_common_path = features_path.relative_to(base_output_common_path)
    output_path_rel_to_common_path = output_path.parent.relative_to(base_output_common_path)
    # TODO: move side effect from this method
    index_file = temp_path / "features.rst"
    existing_index_file = output_path / "features.rst"

    output_path_rel_to_features_path = (
        reduce(truediv, [".."] * len(output_path_rel_to_common_path.parts), Path()) / features_path_rel_to_common_path
    )
    processable_paths = deque([features_path])

    sections: list[ToctreeSection] = []

    while processable_paths:
        processable_path = processable_paths.popleft()

        processable_rel_path = processable_path.relative_to(features_path)
        ordered_file_sources, ordered_dir_sources = collect_ordered_sources(processable_path, features_path)

        toctree_entries: list[str] = []

        for ordered_source in ordered_file_sources:
            path = ordered_source.path
            rel_path = path.relative_to(features_path)
            offset = len(rel_path.parts)
            abs_path = temp_path / rel_path
            abs_path.parent.mkdir(exist_ok=True, parents=True)
            if ordered_source.kind == "markdown":
                rst_content = pypandoc.convert_text(
                    (features_path / rel_path).read_text(),
                    "rst",
                    format="gfm",
                    extra_args=[f"--shift-heading-level-by={offset + 1}", "--eol=lf"],
                )
                abs_path.with_suffix(".rst").write_text(rst_content, encoding="utf-8", newline="\n")
            else:
                codetype = "yaml" if ordered_source.kind == "yaml" else "gherkin"
                abs_path.with_suffix(".rst").write_text(
                    render_include_page(
                        ordered_source.display_name,
                        rel_path,
                        (
                            reduce(truediv, [".."] * len(rel_path.parts), Path())
                            / (output_path_rel_to_features_path / rel_path)
                        ).as_posix(),
                        codetype,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )

            toctree_path = rel_path.with_suffix("").as_posix()
            toctree_entries.append(toctree_path)

        if toctree_entries:
            sections.append(
                ToctreeSection(
                    heading=strip_ordering_prefix(processable_rel_path.name),
                    depth=len(processable_rel_path.parts),
                    entries=tuple(toctree_entries),
                ),
            )

        processable_paths.extendleft(source.path for source in reversed(ordered_dir_sources))

    index_file.write_text(render_generated_index(sections, existing_index_file), newline="\n")


def ensure_pandoc_installed() -> None:
    """Ensure pandoc installed."""
    pypandoc.ensure_pandoc_installed()


def main() -> None:  # pragma: no cover
    """
    Run main.

    Raises:
        ValueError: If the operation cannot be completed.

    """
    arguments = docopt(__doc__)
    ensure_pandoc_installed()
    features_dir = Path(arguments["<features_dir>"]).resolve()
    if not features_dir.exists() or not features_dir.is_dir():
        msg = f"Wrong input features directory {features_dir} is provided"
        raise ValueError(msg)
    output_dir = Path(arguments["<output_dir>"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir = Path(p) if (p := arguments.get("--snapshot")) else None

    with TemporaryDirectory() as temp_dirname:
        temp_dir = Path(temp_dirname)
        try:
            convert(features_dir, output_dir, temp_dir)
        except OrderingValidationError as exc:
            sys.exit(str(exc))

        if diff := diff_folders(cast("_DirCmp", dircmp(str(output_dir), temp_dir))):
            if snapshot_dir is not None:
                rmtree(snapshot_dir, ignore_errors=True)
                copytree(output_dir, str(snapshot_dir), dirs_exist_ok=True)

            rmtree(output_dir, ignore_errors=True)
            copytree(temp_dirname, str(output_dir), dirs_exist_ok=True)

            sys.exit(f"Documentation is generated and overwritten; Diff:{diff}")


if __name__ == "__main__":  # pragma: no cover
    main()
