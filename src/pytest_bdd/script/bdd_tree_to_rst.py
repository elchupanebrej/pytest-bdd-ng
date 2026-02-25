"""Converts directory tree containing Gherkin files into a tree which would be included into rst files

Usage:
    bdd_tree_to_rst.py [--snapshot=<snapshot_path>] <features_dir> <output_dir>

Options:
    --snapshot=<snapshot_path> Path to save snapshot on found diff between old and new documentation
"""

import sys
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from filecmp import dircmp
from functools import lru_cache, reduce
from itertools import chain, zip_longest
from operator import methodcaller, truediv
from os.path import commonpath
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import cast

import pypandoc  # type: ignore[import-not-found, import-untyped]
from docopt import docopt
from jinja2 import Environment
from pathlib2 import Path  # type: ignore[import-not-found, import-untyped]

from pytest_bdd.compatibility.importlib.resources import files

SECTION_SYMBOLS = "-~^\"$%&'()*+,./:;<=>?@[\\]^_`{|}#!="
AUTO_GENERATED_START_MARKER = ".. BEGIN AUTO-GENERATED FEATURES TREE"
AUTO_GENERATED_END_MARKER = ".. END AUTO-GENERATED FEATURES TREE"
DEFAULT_INDEX_PREFIX = dedent(
    # language=rst
    """\
    Features
    ========

    .. NOTE:: This page is generated from feature files under ``features/``.
              Manual edits should be limited to this introduction block.
              The navigation tree below is regenerated automatically.
    """,
).rstrip("\n")
TEMPLATE_ENV = Environment(autoescape=False, keep_trailing_newline=True)  # noqa: S701


@dataclass(frozen=True)
class ToctreeSection:
    heading: str
    depth: int
    entries: tuple[str, ...]


@lru_cache(maxsize=8)
def load_template(template_name: str):
    template_source = files("pytest_bdd.template").joinpath(template_name).read_text(encoding="utf-8")
    return TEMPLATE_ENV.from_string(template_source)


def diff_folders(dcmp):
    if any(diff := [dcmp.diff_files, dcmp.left_only, dcmp.right_only]):
        dcmp.report()
        return diff
    if any(diff := list(map(diff_folders, dcmp.subdirs.values()))):
        return diff
    return None


def extract_existing_intro(
    existing_index_file: Path,
    top_level_headings: Sequence[str],
) -> tuple[str, str]:
    if not existing_index_file.exists():
        return DEFAULT_INDEX_PREFIX, ""

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
    underline = SECTION_SYMBOLS[section.depth - 1] * len(section.heading) if section.heading else ""
    template = load_template("features_section.rst.jinja2")
    rendered_section = cast(
        str,
        template.render(
            heading=section.heading,
            underline=underline,
            entries=section.entries,
        ),
    )
    return rendered_section.lstrip("\n").rstrip("\n")


def render_generated_index(
    sections: Sequence[ToctreeSection],
    existing_index_file: Path,
) -> str:
    top_level_headings = [section.heading for section in sections if section.depth == 1 and section.heading]
    preserved_intro, preserved_suffix = extract_existing_intro(existing_index_file, top_level_headings)

    sections_content = "\n\n".join(map(render_toctree_section, sections)).rstrip("\n")

    content = "\n".join(
        [
            preserved_intro.rstrip("\n"),
            "",
            AUTO_GENERATED_START_MARKER,
            "",
            sections_content,
            "",
            AUTO_GENERATED_END_MARKER,
        ],
    )

    if preserved_suffix:
        stripped_suffix = preserved_suffix.lstrip("\n").rstrip("\n")
        content = f"{content}\n\n{stripped_suffix}"

    return content.rstrip("\n") + "\n"


def render_include_page(rel_path: Path, include_path: str, code_type: str) -> str:
    template = load_template("feature_include.rst.jinja2")
    rendered_include = cast(
        str,
        template.render(
            title=rel_path.stem,
            underline=SECTION_SYMBOLS[len(rel_path.parts) - 1] * len(rel_path.stem),
            include_path=include_path,
            code_type=code_type,
        ),
    )
    return rendered_include.rstrip("\n") + "\n"


def convert(features_path: Path, output_path: Path, temp_path: Path):
    base_output_common_path = Path(commonpath([str(features_path), str(output_path)]))
    features_path_rel_to_common_path = features_path.relative_to(base_output_common_path)
    output_path_rel_to_common_path = output_path.parent.relative_to(base_output_common_path)
    # TODO move side effect from this method
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

        gherkin_file_paths = [
            *processable_path.glob("*.gherkin"),
            *processable_path.glob("*.feature"),
        ]
        markdown_gherkin_file_paths = [
            *processable_path.glob("*.gherkin.md"),
            *processable_path.glob("*.feature.md"),
        ]
        # TODO rework file extension
        struct_bdd_file_paths = processable_path.glob("*.bdd.yaml")

        sub_processable_paths = list(filter(methodcaller("is_dir"), processable_path.iterdir()))

        toctree_entries: list[str] = []

        for path in markdown_gherkin_file_paths:
            rel_path = path.relative_to(features_path)
            offset = len(rel_path.parts)

            abs_path = temp_path / rel_path
            abs_path.parent.mkdir(exist_ok=True, parents=True)

            rst_content = pypandoc.convert_text(
                (features_path / rel_path).read_text(),
                "rst",
                format="gfm",
                extra_args=[f"--shift-heading-level-by={offset + 1}", "--eol=lf"],
            )

            abs_path.with_suffix(".rst").write_text(rst_content, encoding="utf-8", newline="\n")

            toctree_path = path.relative_to(features_path).with_suffix("").as_posix()
            toctree_entries.append(toctree_path)

        for path, codetype in chain(
            zip_longest(gherkin_file_paths, [], fillvalue="gherkin"),
            zip_longest(struct_bdd_file_paths, [], fillvalue="yaml"),
        ):
            rel_path = cast(Path, path).relative_to(features_path)
            abs_path = temp_path / rel_path
            abs_path.parent.mkdir(exist_ok=True, parents=True)

            abs_path.with_suffix(".rst").write_text(
                render_include_page(
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
                    heading=processable_rel_path.name,
                    depth=len(processable_rel_path.parts),
                    entries=tuple(toctree_entries),
                ),
            )

        processable_paths.extendleft(sub_processable_paths)

    index_file.write_text(render_generated_index(sections, existing_index_file), newline="\n")


def main():  # pragma: no cover
    arguments = docopt(__doc__)
    features_dir = Path(arguments["<features_dir>"]).resolve()
    if not features_dir.exists() or not features_dir.is_dir():
        msg = f"Wrong input features directory {features_dir} is provided"
        raise ValueError(msg)
    output_dir = Path(arguments["<output_dir>"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir = Path(p) if (p := arguments.get("--snapshot")) else None

    with TemporaryDirectory() as temp_dirname:
        temp_dir = Path(temp_dirname)
        convert(features_dir, output_dir, temp_dir)

        if diff := diff_folders(dircmp(str(output_dir), temp_dir)):
            if snapshot_dir is not None:
                rmtree(snapshot_dir, ignore_errors=True)
                copytree(output_dir, str(snapshot_dir), dirs_exist_ok=True)

            rmtree(output_dir, ignore_errors=True)
            copytree(temp_dirname, str(output_dir), dirs_exist_ok=True)

            sys.exit(f"Documentation is generated and overwritten; Diff:{diff}")


if __name__ == "__main__":  # pragma: no cover
    main()
