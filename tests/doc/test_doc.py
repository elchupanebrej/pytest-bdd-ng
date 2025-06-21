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
    reason="Verify only on the latest version",
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

                .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                          use cases of **pytest-bdd-ng** by investigation of its regression
                          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests

                .. toctree::
                    :maxdepth: 2

                    features/simple_markdown.gherkin
                    features/simple

                extra
                -----
                .. toctree::
                    :maxdepth: 2

                    features/extra/other_simple
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
