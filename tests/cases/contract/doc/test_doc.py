"""Provide test doc helpers."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.script.bdd_tree_to_rst import OrderingValidationError, convert, main

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


AUTO_GENERATED_START_MARKER = ".. BEGIN AUTO-GENERATED FEATURES TREE"
AUTO_GENERATED_END_MARKER = ".. END AUTO-GENERATED FEATURES TREE"


def write_feature_source(path: Path, content: str) -> None:
    """Write feature source."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content), encoding="utf-8")


def create_ordered_feature_tree(features_path: Path) -> None:
    """Create ordered feature tree."""
    write_feature_source(
        features_path / "01 Tutorial" / "01 Launch.feature",
        # language=gherkin
        """\
        Feature: Launch tutorial
        """,
    )
    write_feature_source(
        features_path / "02 Feature" / "01 Basics.feature",
        # language=gherkin
        """\
        Feature: Basics
        """,
    )
    write_feature_source(
        features_path / "02 Feature" / "02 Markdown parsing.feature.md",
        # language=markdown
        """\
        # Feature: Markdown parsing
        Some feature description

        ## Scenario: Parse markdown
        * Given markdown feature content
        """,
    )
    write_feature_source(
        features_path / "02 Feature" / "03 Load" / "01 Autoload.feature",
        # language=gherkin
        """\
        Feature: Autoload
        """,
    )


def assert_in_order(text: str, *parts: str) -> None:
    """Assert in order."""
    positions = [text.index(part) for part in parts]
    assert positions == sorted(positions)


LATEST_PY313_LINUX_ONLY = pytest.mark.skipif(
    not (
        all(
            [
                sys.version_info.major == 3,
                sys.version_info.minor == 13,
                sys.platform.startswith("linux"),
            ],
        )
    ),
    reason="Verify only on the latest python version and linux environment",
)


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_orders_prefixed_sections_and_entries(testdir: "Testdir") -> None:
    """Verify doc generation orders prefixed sections and entries."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    create_ordered_feature_tree(features_path)

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

            Tutorial
            --------
            .. toctree::
                :maxdepth: 2

                01 Tutorial/01 Launch

            Feature
            -------
            .. toctree::
                :maxdepth: 2

                02 Feature/01 Basics
                02 Feature/02 Markdown parsing.feature

            Load
            ~~~~
            .. toctree::
                :maxdepth: 2

                02 Feature/03 Load/01 Autoload

            .. END AUTO-GENERATED FEATURES TREE
            """,
        )

        launch_page = (temp_path / "01 Tutorial" / "01 Launch.rst").read_text()
        basics_page = (temp_path / "02 Feature" / "01 Basics.rst").read_text()

        assert launch_page.startswith("Launch\n")
        assert ".. include:: ../../features/01 Tutorial/01 Launch.feature" in launch_page
        assert basics_page.startswith("Basics\n")
        assert ".. include:: ../../features/02 Feature/01 Basics.feature" in basics_page
        assert (temp_path / "02 Feature" / "02 Markdown parsing.feature.rst").exists()


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_preserves_manual_sections_and_positions(testdir: "Testdir") -> None:
    """Verify doc generation preserves manual sections and positions."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    create_ordered_feature_tree(features_path)

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
        encoding="utf-8",
    )

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        rendered_index = (temp_path / "features.rst").read_text()

        assert "Manual introduction line." in rendered_index
        assert "Manual suffix line." in rendered_index
        assert "Legacy section" not in rendered_index
        assert_in_order(
            rendered_index,
            "Manual introduction line.",
            AUTO_GENERATED_START_MARKER,
            "Tutorial",
            AUTO_GENERATED_END_MARKER,
            "Manual suffix line.",
        )


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_without_markers_preserves_intro_prefix_for_ordered_headings(testdir: "Testdir") -> None:
    """Verify doc generation without markers preserves intro prefix for ordered headings."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    create_ordered_feature_tree(features_path)

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()
    (output_path / "features.rst").write_text(
        dedent(
            # language=rst
            """\
            Features
            ========

            Manual intro without markers.

            Feature
            -------
            .. toctree::
                :maxdepth: 2

                features/legacy-feature

            Tutorial
            --------
            .. toctree::
                :maxdepth: 2

                features/legacy-tutorial
            """,
        ),
        encoding="utf-8",
    )

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        rendered_index = (temp_path / "features.rst").read_text()

        assert "Manual intro without markers." in rendered_index
        assert "features/legacy-feature" not in rendered_index
        assert "features/legacy-tutorial" not in rendered_index
        assert_in_order(
            rendered_index,
            "Manual intro without markers.",
            "Tutorial\n--------",
            "Feature\n-------",
            "Load\n~~~~",
        )


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_is_idempotent_with_existing_generated_markers(testdir: "Testdir") -> None:
    """Verify doc generation is idempotent with existing generated markers."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    create_ordered_feature_tree(features_path)

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
        encoding="utf-8",
    )

    with TemporaryDirectory() as temp_first, TemporaryDirectory() as temp_second:
        first_path = Path(temp_first)
        second_path = Path(temp_second)

        convert(features_path.resolve(), output_path.resolve(), first_path)
        (output_path / "features.rst").write_text((first_path / "features.rst").read_text(), encoding="utf-8")
        convert(features_path.resolve(), output_path.resolve(), second_path)

        assert (first_path / "features.rst").read_text() == (second_path / "features.rst").read_text()


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_rejects_missing_ordering_prefix(testdir: "Testdir") -> None:
    """Verify doc generation rejects missing ordering prefix."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    write_feature_source(
        features_path / "01 Tutorial" / "Launch.feature",
        # language=gherkin
        """\
        Feature: Launch tutorial
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        with pytest.raises(OrderingValidationError, match="missing_ordering_prefix"):
            convert(features_path.resolve(), output_path.resolve(), temp_path)


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_rejects_duplicate_ordering_prefix(testdir: "Testdir") -> None:
    """Verify doc generation rejects duplicate ordering prefix."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    write_feature_source(
        features_path / "01 Tutorial" / "01 Launch.feature",
        # language=gherkin
        """\
        Feature: Launch tutorial
        """,
    )
    write_feature_source(
        features_path / "01 Tutorial" / "01 Install.feature",
        # language=gherkin
        """\
        Feature: Install tutorial
        """,
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        with pytest.raises(OrderingValidationError, match="duplicate_ordering_prefix"):
            convert(features_path.resolve(), output_path.resolve(), temp_path)


@LATEST_PY313_LINUX_ONLY
def test_doc_generation_cli_fails_when_generated_docs_are_stale(
    testdir: "Testdir",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify doc generation cli fails when generated docs are stale."""

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    create_ordered_feature_tree(features_path)

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
        encoding="utf-8",
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
