"""Provide feature documentation contract tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.compatibility.tomllib import loads
from pytest_bdd.script._feature_tree import OrderingValidationError, walk_feature_tree

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from types import ModuleType

REPO_ROOT = Path(__file__).parents[4]
FEATURE_TREE_EXTENSION = REPO_ROOT / "docs" / "ext" / "feature_tree.py"


class FakeSphinxApp:
    """Minimal Sphinx app for extension contract tests."""

    def __init__(self, confdir: Path) -> None:
        """Initialize fake app."""
        self.confdir = str(confdir)
        self.connected_events: list[tuple[str, Callable[..., object]]] = []

    def connect(self, event: str, callback: Callable[..., object]) -> None:
        """Record connected callbacks."""
        self.connected_events.append((event, callback))


def load_feature_tree_extension() -> ModuleType:
    """Load the local Sphinx feature-tree extension module."""
    spec = importlib.util.spec_from_file_location("feature_tree", FEATURE_TREE_EXTENSION)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_feature_source(path: Path, content: str = "# Feature: Example\n") -> None:
    """Write feature source."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content), encoding="utf-8")


def create_ordered_feature_tree(features_path: Path) -> None:
    """Create ordered Markdown feature tree."""
    write_feature_source(
        features_path / "02 Feature" / "02 Markdown parsing.feature.md",
        """\
        # Feature: Markdown parsing

        ## Scenario: Parse markdown
        * Given markdown feature content
        """,
    )
    write_feature_source(
        features_path / "01 Tutorial" / "01 Launch.feature.md",
        """\
        # Feature: Launch tutorial

        ## Scenario: Launch
        * Given tutorial feature content
        """,
    )
    write_feature_source(
        features_path / "02 Feature" / "01 Basics.feature.md",
        """\
        # Feature: Basics
        """,
    )
    write_feature_source(
        features_path / "02 Feature" / "03 Load" / "01 Autoload.feature.md",
        """\
        # Feature: Autoload
        """,
    )


def test_feature_tree_rejects_missing_ordering_prefix(tmp_path: Path) -> None:
    """Verify shared ordering utility rejects missing ordering prefix."""
    features_path = tmp_path / "features"
    write_feature_source(features_path / "01 Tutorial" / "Launch.feature.md")

    with pytest.raises(OrderingValidationError, match="missing_ordering_prefix"):
        walk_feature_tree(features_path)


def test_feature_tree_rejects_duplicate_ordering_prefix(tmp_path: Path) -> None:
    """Verify shared ordering utility rejects duplicate ordering prefix."""
    features_path = tmp_path / "features"
    write_feature_source(features_path / "01 Tutorial" / "01 Launch.feature.md")
    write_feature_source(features_path / "01 Tutorial" / "01 Install.feature.md")

    with pytest.raises(OrderingValidationError, match="duplicate_ordering_prefix"):
        walk_feature_tree(features_path)


def test_feature_tree_extension_registers_builder_hook() -> None:
    """Verify Sphinx extension registers builder-inited hook."""
    extension = load_feature_tree_extension()
    app = FakeSphinxApp(REPO_ROOT / "docs")

    metadata = extension.setup(app)

    assert metadata == {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
    assert app.connected_events == [("builder-inited", extension.prepare_feature_tree)]


def test_feature_tree_extension_generates_markdown_toctrees(tmp_path: Path) -> None:
    """Verify feature-tree extension generates MyST toctree output."""
    docs_path = tmp_path / "docs"
    features_path = tmp_path / "features"
    docs_features_path = docs_path / "features"
    docs_features_path.mkdir(parents=True)
    create_ordered_feature_tree(features_path)

    extension = load_feature_tree_extension()
    extension.prepare_feature_tree(FakeSphinxApp(docs_path))

    rendered_index = (docs_features_path / "features.md").read_text(encoding="utf-8")

    assert "```{toctree}\n:maxdepth: 2\n\n01 Tutorial/01 Launch.feature\n```" in rendered_index
    assert "02 Feature/01 Basics.feature" in rendered_index
    assert "02 Feature/02 Markdown parsing.feature" in rendered_index
    assert "02 Feature/03 Load/01 Autoload.feature" in rendered_index
    assert ".feature.md" not in rendered_index
    assert (docs_features_path / "01 Tutorial" / "01 Launch.feature.md").exists()


def test_feature_tree_extension_preserves_manual_text_around_generated_markers(tmp_path: Path) -> None:
    """Verify feature-tree extension preserves manual intro and suffix."""
    docs_path = tmp_path / "docs"
    features_path = tmp_path / "features"
    docs_features_path = docs_path / "features"
    docs_features_path.mkdir(parents=True)
    create_ordered_feature_tree(features_path)
    (docs_features_path / "features.md").write_text(
        dedent(
            """\
            # Features

            Manual introduction line.

            % BEGIN AUTO-GENERATED FEATURES TREE
            Old generated entry
            % END AUTO-GENERATED FEATURES TREE

            Manual suffix line.
            """,
        ),
        encoding="utf-8",
    )

    extension = load_feature_tree_extension()
    extension.prepare_feature_tree(FakeSphinxApp(docs_path))

    rendered_index = (docs_features_path / "features.md").read_text(encoding="utf-8")

    assert "Manual introduction line." in rendered_index
    assert "Manual suffix line." in rendered_index
    assert "Old generated entry" not in rendered_index
    assert rendered_index.index("Manual introduction line.") < rendered_index.index(
        "% BEGIN AUTO-GENERATED FEATURES TREE",
    )
    assert rendered_index.index("% END AUTO-GENERATED FEATURES TREE") < rendered_index.index("Manual suffix line.")


def test_feature_tree_extension_raises_hard_sphinx_error_on_validation_failure(tmp_path: Path) -> None:
    """Verify feature-tree extension raises hard Sphinx error on validation failure."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()
    features_path = tmp_path / "features"
    write_feature_source(features_path / "01 Tutorial" / "01 Launch.feature.md")
    write_feature_source(features_path / "01 Tutorial" / "01 Install.feature.md")

    extension = load_feature_tree_extension()

    with pytest.raises(extension.ExtensionError, match="duplicate_ordering_prefix"):
        extension.prepare_feature_tree(FakeSphinxApp(docs_path))


def test_docs_migration_uses_markdown_package_metadata_and_includes() -> None:
    """Verify documentation metadata and include pages use Markdown sources."""
    pyproject = loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    docs_include = (REPO_ROOT / "docs" / "include.md").read_text(encoding="utf-8")

    assert pyproject["project"]["readme"] == {
        "file": "README.md",
        "content-type": "text/markdown",
    }
    assert "```{include} ../README.md" in docs_include
    assert "```{include} ../DOCUMENTATION.md" in docs_include
    assert "```{include} ../AUTHORS.md" in docs_include
    assert "```{include} ../LICENSE.md" in docs_include
    assert "```{include} ../CHANGES.md" in docs_include
    assert ".rst" not in docs_include


def test_obsolete_docs_generation_pipeline_is_removed_from_active_paths() -> None:
    """Verify active build, hook, tox, CI, and packaging paths do not reference old generator."""
    old_generator = "bdd_tree" + "_to_rst"
    old_target = "features" + "-docs"
    old_doc_dependency = "py" + "pandoc"
    old_doc_filter = "pan" + "flute"
    forbidden = (old_generator, old_target, old_doc_dependency, old_doc_filter)
    active_paths = (
        "pyproject.toml",
        "Makefile",
        ".pre-commit-config.yaml",
        "tox.ini",
        ".github/workflows/main.yml",
        ".github/workflows/release.yaml",
    )

    for relative_path in active_paths:
        content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert not any(term in content for term in forbidden), relative_path


def test_docs_make_target_runs_sphinx_html_build() -> None:
    """Verify Makefile exposes the Sphinx HTML documentation build."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "docs: env-check" in makefile
    assert "uv run --extra doc-gen sphinx-build -b html docs docs/_build/html" in makefile


def test_legacy_rst_sources_and_feature_rst_artifacts_are_absent() -> None:
    """Verify replaced RST sources and generated feature RST artifacts are absent."""
    replaced_rst_sources = (
        "README.rst",
        "DOCUMENTATION.rst",
        "AUTHORS.rst",
        "LICENSE.rst",
        "CHANGES.rst",
        "docs/index.rst",
        "docs/include.rst",
    )

    for relative_path in replaced_rst_sources:
        assert not (REPO_ROOT / relative_path).exists(), relative_path

    assert not list((REPO_ROOT / "docs" / "features").rglob("*.rst"))


def test_transient_feature_copy_artifacts_are_gitignored() -> None:
    """Verify copied feature docs are treated as transient documentation build artifacts."""
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "docs/features/**/*.feature.md" in gitignore
    assert "docs/features/**/*.feature.gherkin" in gitignore
    assert "docs/features/**/*.bdd.yaml" in gitignore


def test_manual_uat_tracks_blocking_rendering_checks() -> None:
    """Verify manual rendering checks remain explicit merge gates."""
    uat = (REPO_ROOT / ".planning" / "phases" / "19-html-doc-generation-simplification" / "19-UAT.md").read_text(
        encoding="utf-8",
    )

    assert "ReadTheDocs preview" in uat
    assert "README/PyPI rendering" in uat
    assert "CHANGES rendering" in uat
    if "status: complete" in uat:
        assert "PASS" in uat
        assert "All Phase 19 blocking manual checks passed." in uat
    else:
        assert "BLOCKING - pending" in uat
        assert "Do not merge Phase 19" in uat
