"""Converts directory tree containing Gherkin files into a tree which would be included into rst files

Usage:
    bdd_tree_to_rst.py [--snapshot=<snapshot_path>] <features_dir> <output_dir>

Options:
    --snapshot=<snapshot_path> Path to save snapshot on found diff between old and new documentation
"""

import re
import sys
from collections import deque
from filecmp import dircmp
from functools import reduce
from itertools import chain
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import panflute as pf  # type: ignore[import-not-found]  # Optional doc-gen dependency.
import pycmarkgfm  # type: ignore[import-not-found]  # Optional doc-gen dependency.
import pypandoc  # type: ignore[import-not-found]  # Optional doc-gen dependency.
from docopt import docopt

SECTION_SYMBOLS = "-#!\"$%&'()*+,./:;<=>?@[\\]^_`{|}~="

# GFM reuses heading ids such as scenario-1 across pages, and Pandoc turns
# every heading id into an explicit RST target. Those targets collide once the
# fragments are included into one document, so drop them; no generated page
# links to them.
PANDOC_HEADING_TARGET = re.compile(r"^\.\. _[A-Za-z0-9][A-Za-z0-9_-]*:\n\n", re.MULTILINE)

# Pandoc 3.4 keeps the fence language in ``.. code:: <language>``, and the
# strict Sphinx build warns when Pygments has no lexer for it. csv/tsv have
# none; add any other fence language that Pygments lacks here.
UNSUPPORTED_CODE_LANGUAGES = {"csv": "text", "tsv": "text"}
CODE_LANGUAGE = re.compile(r"^(?P<indent>[ \t]*)\.\. code:: (?P<language>\S+)$", re.MULTILINE)


def strip_pandoc_heading_targets(rst_content: str) -> str:
    return PANDOC_HEADING_TARGET.sub("", rst_content)


def normalize_code_languages(rst_content: str) -> str:
    def replace(match: "re.Match[str]") -> str:
        if language := UNSUPPORTED_CODE_LANGUAGES.get(match["language"]):
            return f"{match['indent']}.. code:: {language}"
        return match[0]

    return CODE_LANGUAGE.sub(replace, rst_content)


def diff_folders(dcmp: dircmp[Any]) -> list[Any]:
    if any(diff := [dcmp.diff_files, dcmp.left_only, dcmp.right_only]):
        dcmp.report()
        return diff
    if any(diff := list(map(diff_folders, dcmp.subdirs.values()))):
        return diff
    return []


def adjust_heading_level(elem: Any, doc: Any, *, level: int) -> Any:
    if isinstance(elem, pf.Header):
        new_level = elem.level + level
        return pf.Header(*elem.content, level=new_level)
    return elem


def index_underline(depth: int, title: str) -> str:
    """Underline an index title one level below its parent.

    docutils fixes each underline character to the depth where it first
    appears, in document order, and included fragments introduce their own
    characters first. Deeper index levels would then need a new character
    below an already known one, which docutils rejects as an inconsistent
    title level, so index titles stop nesting after the second level.
    """
    return SECTION_SYMBOLS[min(depth - 1, 1)] * len(title)


def convert(features_path: Path, output_path: Path, temp_path: Path) -> None:
    base_output_common_path = Path(commonpath([str(features_path), str(output_path)]))
    features_path_rel_to_common_path = features_path.relative_to(base_output_common_path)
    output_path_rel_to_common_path = output_path.relative_to(base_output_common_path)
    # TODO move side effect from this method
    index_file = temp_path / "features.rst"

    output_path_rel_to_features_path = (
        reduce(truediv, [".."] * len(output_path_rel_to_common_path.parts), Path()) / features_path_rel_to_common_path
    )
    processable_paths = deque([features_path])

    content = ""
    content += dedent(
        # language=rst
        """\
            Features
            ========

            .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                      use cases of **pytest-cuke** by investigation of its regression
                      test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/rewrite-from-2.3.1/tests
        """
    )

    while processable_paths:
        processable_path = processable_paths.popleft()

        processable_rel_path = processable_path.relative_to(features_path)
        content += dedent(
            # language=rst
            f"""\
                {processable_rel_path.name}
                {index_underline(len(processable_rel_path.parts), processable_rel_path.name)}

            """
        )

        # Filesystem order varies per directory and filesystem; sort every walk so
        # a regenerated index is identical on any machine.
        gherkin_file_paths = sorted(chain(processable_path.glob("*.gherkin"), processable_path.glob("*.feature")))
        markdown_gherkin_file_paths = sorted(
            chain(processable_path.glob("*.gherkin.md"), processable_path.glob("*.feature.md"))
        )
        struct_bdd_file_paths = sorted(processable_path.glob("*.bdd.yaml"))

        sub_processable_paths = sorted(filter(methodcaller("is_dir"), processable_path.iterdir()))

        for path in markdown_gherkin_file_paths:
            rel_path = path.relative_to(features_path)
            offset = len(rel_path.parts)

            abs_path = temp_path / rel_path
            abs_path.parent.mkdir(exist_ok=True, parents=True)

            html_data = pycmarkgfm.gfm_to_html((features_path / rel_path).read_text())

            rst_content = pypandoc.convert_text(
                html_data, "rst", format="html", extra_args=[f"--shift-heading-level-by={min(offset + 1, 3)}"]
            )
            rst_content = strip_pandoc_heading_targets(rst_content)
            rst_content = normalize_code_languages(rst_content)

            abs_path.with_suffix(".rst").write_text(rst_content, encoding="utf-8")

            stemmed_path = Path(rel_path.stem).stem

            content += dedent(
                # language=rst
                f"""\
                    {stemmed_path}
                    {index_underline(offset, stemmed_path)}

                    .. include:: {path.relative_to(features_path).with_suffix(".rst").as_posix()}

                """
            )

        for path in gherkin_file_paths:
            rel_path = path.relative_to(features_path)
            content += dedent(
                # language=rst
                f"""\
                    {rel_path.stem}
                    {index_underline(len(rel_path.parts), rel_path.stem)}

                    .. include:: {(output_path_rel_to_features_path / path.relative_to(features_path)).as_posix()}
                       :code: gherkin

                """
            )

        for path in struct_bdd_file_paths:
            rel_path = path.relative_to(features_path)
            content += dedent(
                # language=rst
                f"""\
                    {rel_path.stem}
                    {index_underline(len(rel_path.parts), rel_path.stem)}

                    .. include:: {(output_path_rel_to_features_path / path.relative_to(features_path)).as_posix()}
                       :code: yaml

                """
            )

        processable_paths.extendleft(reversed(sub_processable_paths))

    index_file.write_text(content.rstrip("\n") + "\n")


def main() -> None:  # pragma: no cover
    arguments = docopt(__doc__)
    features_dir = Path(arguments["<features_dir>"]).resolve()
    if not features_dir.exists() or not features_dir.is_dir():
        raise ValueError(f"Wrong input features directory {features_dir} is provided")
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
