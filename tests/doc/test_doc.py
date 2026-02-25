import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


@pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ]
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)
def test_doc_generation(testdir: "Testdir"):
    from pytest_bdd.script.bdd_tree_to_rst import convert

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """,
    )
    (features_path / "simple_markdown.gherkin.md").write_text(
        dedent(
            # language=markdown
            """\
            # Feature: Simple gherkin markdown
            Some feature description

            ## Scenario:
            *  Given some step
        """,
        ),
    )
    (features_path / "extra").mkdir()
    (features_path / "extra" / "other_simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do other nothing
        """,
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

                .. NOTE:: This page is generated from feature files under ``features/``.
                          Manual edits should be limited to this introduction block.
                          The navigation tree below is regenerated automatically.

                .. BEGIN AUTO-GENERATED FEATURES TREE
                .. toctree::
                    :maxdepth: 2

                    simple_markdown.gherkin
                    simple

                extra
                -----
                .. toctree::
                    :maxdepth: 2

                    extra/other_simple
                .. END AUTO-GENERATED FEATURES TREE
            """,
        )

        assert (temp_path / "simple_markdown.gherkin.rst").read_text() == dedent(
            # language=rst
            """\
                Feature: Simple gherkin markdown
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                Some feature description

                Scenario:
                ^^^^^^^^^

                -  Given some step
            """,
        )

        assert (temp_path / "simple.rst").read_text() == dedent(
            # language=rst
            """\
                simple
                ------

                .. include:: ../features/simple.gherkin
                   :code: gherkin
            """,
        )

        assert (temp_path / "extra" / "other_simple.rst").read_text() == dedent(
            # language=rst
            """\
                other_simple
                ############

                .. include:: ../../features/extra/other_simple.gherkin
                   :code: gherkin
            """,
        )


@pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ]
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)
def test_doc_generation_preserves_manual_sections(testdir: "Testdir"):
    from pytest_bdd.script.bdd_tree_to_rst import convert

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()
    (output_path / "features.rst").write_text(
        dedent(
            # language=rst
            """\
            Features
            ========

            Manual introduction line.

            .. BEGIN AUTO-GENERATED FEATURES TREE
            Legacy section
            --------------
            .. toctree::
                :maxdepth: 2

                features/legacy
            .. END AUTO-GENERATED FEATURES TREE

            Manual suffix line.
            """,
        ),
    )

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        rendered_index = (temp_path / "features.rst").read_text()

        assert "Manual introduction line." in rendered_index
        assert "Manual suffix line." in rendered_index
        assert "Legacy section" not in rendered_index
        assert "simple" in rendered_index


@pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ]
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)
def test_doc_generation_without_markers_preserves_intro_prefix(testdir: "Testdir"):
    from pytest_bdd.script.bdd_tree_to_rst import convert

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()
    (output_path / "features.rst").write_text(
        dedent(
            # language=rst
            """\
            Features
            ========

            Manual intro without markers.

            Tutorial
            --------
            .. toctree::
                :maxdepth: 2

                features/legacy
            """,
        ),
    )

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        rendered_index = (temp_path / "features.rst").read_text()

        assert "Manual intro without markers." in rendered_index
        assert "features/legacy" not in rendered_index
        assert "simple" in rendered_index


@pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ]
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)
def test_doc_generation_is_idempotent_with_existing_generated_markers(testdir: "Testdir"):
    from pytest_bdd.script.bdd_tree_to_rst import convert

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()
    (output_path / "features.rst").write_text(
        dedent(
            # language=rst
            """\
            Features
            ========

            Manual prefix.

            .. BEGIN AUTO-GENERATED FEATURES TREE
            Old section
            ----------
            .. toctree::
                :maxdepth: 2

                features/legacy
            .. END AUTO-GENERATED FEATURES TREE
            """,
        ),
    )

    with TemporaryDirectory() as temp_first, TemporaryDirectory() as temp_second:
        first_path = Path(temp_first)
        second_path = Path(temp_second)

        convert(features_path.resolve(), output_path.resolve(), first_path)
        (output_path / "features.rst").write_text((first_path / "features.rst").read_text(), encoding="utf-8")
        convert(features_path.resolve(), output_path.resolve(), second_path)

        first_render = (first_path / "features.rst").read_text()
        second_render = (second_path / "features.rst").read_text()

        assert first_render == second_render


@pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ]
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)
def test_doc_generation_cli_fails_when_generated_docs_are_stale(testdir: "Testdir", monkeypatch: pytest.MonkeyPatch):
    from pytest_bdd.script.bdd_tree_to_rst import main

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()
    (output_path / "features.rst").write_text(
        dedent(
            # language=rst
            """\
            Features
            ========

            .. BEGIN AUTO-GENERATED FEATURES TREE
            .. toctree::
                :maxdepth: 2

                features/legacy
            .. END AUTO-GENERATED FEATURES TREE
            """,
        ),
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bdd_tree_to_rst.py",
            str(features_path),
            str(output_path),
        ],
    )

    with pytest.raises(SystemExit, match="Documentation is generated and overwritten; Diff:"):
        main()
