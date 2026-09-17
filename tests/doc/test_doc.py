import sys
from filecmp import dircmp
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from pytest import mark

pytestmark = mark.integration


if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


def _load_bdd_tree_to_rst():
    for dependency in ("panflute", "pycmarkgfm", "pypandoc", "docopt"):
        pytest.importorskip(dependency)
    from pytest_bdd.script import bdd_tree_to_rst

    return bdd_tree_to_rst


def test_diff_folders_reports_top_level_and_nested_differences(tmp_path: Path) -> None:
    bdd_tree_to_rst = _load_bdd_tree_to_rst()
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "same.txt").write_text("same", encoding="utf-8")
    (right / "same.txt").write_text("same", encoding="utf-8")

    assert bdd_tree_to_rst.diff_folders(dircmp(str(left), str(right))) is None

    (right / "extra.txt").write_text("extra", encoding="utf-8")
    assert bdd_tree_to_rst.diff_folders(dircmp(str(left), str(right)))

    (right / "extra.txt").unlink()
    (left / "nested").mkdir()
    (right / "nested").mkdir()
    (left / "nested" / "only_left.txt").write_text("left", encoding="utf-8")
    assert bdd_tree_to_rst.diff_folders(dircmp(str(left), str(right)))


def test_adjust_heading_level_shifts_headers_only() -> None:
    bdd_tree_to_rst = _load_bdd_tree_to_rst()
    pf = pytest.importorskip("panflute")

    header = pf.Header(pf.Str("Title"), level=1)
    shifted = bdd_tree_to_rst.adjust_heading_level(header, None, level=2)
    assert isinstance(shifted, pf.Header)
    assert shifted.level == 3

    paragraph = pf.Para(pf.Str("Body"))
    assert bdd_tree_to_rst.adjust_heading_level(paragraph, None, level=2) is paragraph


def test_convert_includes_struct_bdd_files(tmp_path: Path) -> None:
    bdd_tree_to_rst = _load_bdd_tree_to_rst()
    features_path = tmp_path / "features"
    features_path.mkdir()
    (features_path / "simple.bdd.yaml").write_text("Feature: Do nothing\n", encoding="utf-8")
    output_path = tmp_path / "output"
    output_path.mkdir()
    temp_path = tmp_path / "temp"
    temp_path.mkdir()

    bdd_tree_to_rst.convert(features_path.resolve(), output_path.resolve(), temp_path.resolve())

    content = (temp_path / "features.rst").read_text(encoding="utf-8")
    assert "simple" in content
    assert "simple.bdd.yaml" in content
    assert ":code: yaml" in content


@mark.skipif(sys.version_info < (3, 12), reason="Verify only on the latest version")
def test_doc_generation(testdir: "Testdir"):
    try:
        import pypandoc
        from pytest_bdd.script.bdd_tree_to_rst import convert
    except ModuleNotFoundError as err:
        if err.name not in {"panflute", "pycmarkgfm", "pypandoc", "docopt"}:
            raise
        pytest.skip(f"doc-gen extra is not installed ({err.name}); install pytest-bdd-ng[doc-gen]")

    try:
        pypandoc.get_pandoc_path()
    except OSError:
        pytest.skip("pandoc binary is not found; CI installs it via r-lib/actions/setup-pandoc")

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """
    )
    (features_path / "simple_markdown.gherkin.md").write_text(
        # language=gherkin
        """
        # Feature: Simple gherkin markdown
        """
    )
    (features_path / "extra").mkdir()
    (features_path / "extra" / "other_simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do other nothing
        """
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        assert (temp_path / "features.rst").read_text() == dedent(
            # language=rst
            """\
                Features
                ========

                .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                          use cases of **pytest-bdd-ng** by investigation of its regression
                          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests



                simple_markdown
                ---------------

                .. include:: features/simple_markdown.gherkin.rst

                simple
                ------

                .. include:: features/simple.gherkin
                   :code: gherkin

                extra
                -----

                other_simple
                ############

                .. include:: features/extra/other_simple.gherkin
                   :code: gherkin
            """
        )
