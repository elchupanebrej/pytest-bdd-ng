import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

from pytest import mark

if TYPE_CHECKING:  # pragma: no cover
    from pytest_cuke.compatibility.pytest import Testdir


@mark.doc_gen
@mark.skipif(sys.version_info < (3, 12), reason="Verify only on the latest version")
def test_doc_generation(testdir: "Testdir"):
    from pytest_cuke.script.bdd_tree_to_rst import convert

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
                          use cases of **pytest-cuke** by investigation of its regression
                          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/rewrite-from-2.3.1/tests



                simple_markdown
                ---------------

                .. include:: simple_markdown.gherkin.rst

                simple
                ------

                .. include:: ../features/simple.gherkin
                   :code: gherkin

                extra
                -----

                other_simple
                ############

                .. include:: ../features/extra/other_simple.gherkin
                   :code: gherkin
            """
        )


@mark.doc_gen
def test_doc_generation_sorts_sections(monkeypatch, tmp_path: Path):
    from pytest_cuke.script.bdd_tree_to_rst import convert

    features_path = tmp_path / "features"
    features_path.mkdir()
    (features_path / "zeta.gherkin").write_text("Feature: Zeta\n")
    (features_path / "alpha.gherkin").write_text("Feature: Alpha\n")
    for name in ("second", "first"):
        (features_path / name).mkdir()
        (features_path / name / "child.gherkin").write_text(f"Feature: {name}\n")

    real_iterdir, real_glob = Path.iterdir, Path.glob
    monkeypatch.setattr(Path, "iterdir", lambda self: iter(reversed(list(real_iterdir(self)))))
    monkeypatch.setattr(Path, "glob", lambda self, pattern: iter(reversed(list(real_glob(self, pattern)))))

    with TemporaryDirectory() as temp_dirname:
        convert(features_path.resolve(), (tmp_path / "output").resolve(), Path(temp_dirname))
        index = (Path(temp_dirname) / "features.rst").read_text()

    assert index.index("\nalpha\n-----") < index.index("\nzeta\n----")
    assert index.index("\nfirst\n-----") < index.index("\nsecond\n------")


@mark.doc_gen
def test_docs_drift_detects_a_changed_source(tmp_path: Path):
    from shutil import copytree

    from pytest_cuke.script.bdd_tree_to_rst import convert
    from pytest_cuke.script.docs_drift import check, normalize_trailing_whitespace

    source_path = tmp_path / "features"
    source_path.mkdir()
    (source_path / "example.feature.md").write_text("# Feature: Example\n")
    docs_path = tmp_path / "docs" / "features"
    docs_path.parent.mkdir()

    with TemporaryDirectory() as temp_dirname:
        convert(source_path.resolve(), docs_path.resolve(), Path(temp_dirname))
        copytree(temp_dirname, docs_path)
    normalize_trailing_whitespace(docs_path)

    assert check(source_path, docs_path) == []

    (source_path / "example.feature.md").write_text("# Feature: Example\n\n- added\n")
    assert check(source_path, docs_path) == ["generated page differs from its source: example.feature.rst"]


@mark.doc_gen
def test_nested_markdown_fragment_nests_below_its_index_title(tmp_path: Path):
    from pytest_cuke.script.bdd_tree_to_rst import convert

    features_path = tmp_path / "features"
    page = features_path / "deep" / "er"
    page.mkdir(parents=True)
    (page / "example.feature.md").write_text("# Feature: Example\n")

    with TemporaryDirectory() as temp_dirname:
        convert(features_path.resolve(), (tmp_path / "output").resolve(), Path(temp_dirname))
        index = (Path(temp_dirname) / "features.rst").read_text()
        fragment = (Path(temp_dirname) / "deep" / "er" / "example.feature.rst").read_text()

    assert "\ner\n##\n" in index
    assert fragment.startswith("Feature: Example\n^^^^^^^^^^^^^^^^\n")


@mark.doc_gen
def test_unknown_code_languages_render_as_plain_text():
    from pytest_cuke.script.bdd_tree_to_rst import normalize_code_languages

    assert normalize_code_languages("   .. code:: csv\n\n      a,b\n") == "   .. code:: text\n\n      a,b\n"
    assert normalize_code_languages(".. code:: gherkin\n") == ".. code:: gherkin\n"


@mark.doc_gen
def test_generated_headings_have_no_duplicate_targets():
    from pytest_cuke.script.bdd_tree_to_rst import strip_pandoc_heading_targets

    generated = ".. _scenario-1:\n\nScenario:\n'''''''''\n"
    assert strip_pandoc_heading_targets(generated) == "Scenario:\n'''''''''\n"
