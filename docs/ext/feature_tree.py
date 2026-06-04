"""Prepare feature Markdown sources for Sphinx builds."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Any

from sphinx.errors import ExtensionError

from pytest_bdd.script._feature_tree import (  # noqa: PLC2701
    FeatureDirectory,
    OrderingValidationError,
    strip_ordering_prefix,
    walk_feature_tree,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.application import Sphinx

AUTO_GENERATED_START_MARKER = "% BEGIN AUTO-GENERATED FEATURES TREE"
AUTO_GENERATED_END_MARKER = "% END AUTO-GENERATED FEATURES TREE"
MIN_RST_TITLE_LINES = 2
DEFAULT_FEATURES_INTRO = """# Features

```{note}
This page is generated from feature files under `features/`.
Manual edits should be limited to this introduction block.
The navigation tree below is regenerated automatically.
```"""


def _project_root(app: Sphinx) -> Path:
    return Path(app.confdir).parent.resolve()


def _features_source_root(app: Sphinx) -> Path:
    return _project_root(app) / "features"


def _features_docs_root(app: Sphinx) -> Path:
    return Path(app.confdir).resolve() / "features"


def _features_index_path(app: Sphinx) -> Path:
    return _features_docs_root(app) / "features.md"


def _legacy_features_index_path(app: Sphinx) -> Path:
    return _features_docs_root(app) / "features.rst"


def _extract_marked_blocks(content: str) -> tuple[str, str] | None:
    if AUTO_GENERATED_START_MARKER not in content or AUTO_GENERATED_END_MARKER not in content:
        return None
    intro, _, generated_and_suffix = content.partition(AUTO_GENERATED_START_MARKER)
    _, _, suffix = generated_and_suffix.partition(AUTO_GENERATED_END_MARKER)
    return intro.rstrip("\n"), suffix.lstrip("\n").rstrip("\n")


def _convert_legacy_intro(content: str) -> str:
    intro, _, _ = content.partition(".. BEGIN AUTO-GENERATED FEATURES TREE")
    stripped_intro = intro.strip()
    if not stripped_intro:
        return DEFAULT_FEATURES_INTRO

    lines = stripped_intro.splitlines()
    if len(lines) >= MIN_RST_TITLE_LINES and set(lines[1]) == {"="}:
        title = lines[0]
        body_lines = lines[2:]
    else:
        title = "Features"
        body_lines = lines

    note_lines: list[str] = []
    plain_lines: list[str] = []
    in_note = False
    for line in body_lines:
        if line.startswith(".. NOTE::"):
            in_note = True
            note_text = line.removeprefix(".. NOTE::").strip()
            if note_text:
                note_lines.append(note_text)
            continue
        if in_note and line.startswith("          "):
            note_lines.append(line.strip())
            continue
        if line.strip():
            plain_lines.append(line)

    blocks = [f"# {title}"]
    if note_lines:
        blocks.append("```{note}\n" + "\n".join(note_lines) + "\n```")
    if plain_lines:
        blocks.append("\n".join(plain_lines))
    return "\n\n".join(blocks).rstrip("\n")


def _manual_blocks(index_path: Path, legacy_index_path: Path) -> tuple[str, str]:
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        marked_blocks = _extract_marked_blocks(content)
        if marked_blocks is not None:
            return marked_blocks
        return content.rstrip("\n"), ""

    if legacy_index_path.exists():
        return _convert_legacy_intro(legacy_index_path.read_text(encoding="utf-8")), ""

    return DEFAULT_FEATURES_INTRO, ""


def _heading_level(feature_directory: FeatureDirectory) -> int:
    if not feature_directory.rel_path.parts:
        return 2
    return len(feature_directory.rel_path.parts) + 1


def _section_heading(feature_directory: FeatureDirectory) -> str:
    if not feature_directory.rel_path.parts:
        return "Features"
    return strip_ordering_prefix(feature_directory.rel_path.name)


def _toctree_entry(source_path: Path, features_path: Path) -> str:
    return source_path.relative_to(features_path).with_suffix("").as_posix()


def _render_generated_block(
    feature_directories: Sequence[FeatureDirectory],
    features_path: Path,
) -> str:
    sections: list[str] = []
    for feature_directory in feature_directories:
        if not feature_directory.files:
            continue

        heading_prefix = "#" * _heading_level(feature_directory)
        entries = "\n".join(_toctree_entry(source.path, features_path) for source in feature_directory.files)
        sections.append(
            f"{heading_prefix} {_section_heading(feature_directory)}\n\n```{{toctree}}\n:maxdepth: 2\n\n{entries}\n```",
        )

    return "\n\n".join(sections).rstrip("\n")


def _render_index(intro: str, generated_block: str, suffix: str) -> str:
    content_blocks = [
        intro.rstrip("\n"),
        AUTO_GENERATED_START_MARKER,
        generated_block.rstrip("\n"),
        AUTO_GENERATED_END_MARKER,
    ]
    if suffix:
        content_blocks.append(suffix)
    return "\n\n".join(content_blocks).rstrip("\n") + "\n"


def _copy_feature_sources(
    feature_directories: Sequence[FeatureDirectory],
    features_path: Path,
    docs_features_path: Path,
) -> None:
    for feature_directory in feature_directories:
        for source in feature_directory.files:
            rel_path = source.path.relative_to(features_path)
            target_path = docs_features_path / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(source.path, target_path)


def _prepare_feature_tree(
    features_path: Path,
    docs_features_path: Path,
    index_path: Path,
    legacy_index_path: Path,
) -> None:
    feature_directories = walk_feature_tree(features_path)
    docs_features_path.mkdir(parents=True, exist_ok=True)
    _copy_feature_sources(feature_directories, features_path, docs_features_path)
    intro, suffix = _manual_blocks(index_path, legacy_index_path)
    generated_block = _render_generated_block(feature_directories, features_path)
    index_path.write_text(_render_index(intro, generated_block, suffix), encoding="utf-8", newline="\n")


def prepare_feature_tree(app: Sphinx) -> None:
    """
    Validate and copy feature Markdown sources for Sphinx.

    Args:
        app: Sphinx application.

    Raises:
        ExtensionError: If validation, copying, or index writing fails.

    """
    features_path = _features_source_root(app)
    docs_features_path = _features_docs_root(app)
    index_path = _features_index_path(app)
    legacy_index_path = _legacy_features_index_path(app)
    try:
        _prepare_feature_tree(features_path, docs_features_path, index_path, legacy_index_path)
    except (OSError, OrderingValidationError, ValueError) as exc:
        msg = f"Failed to prepare Sphinx feature tree from {features_path} to {docs_features_path}: {exc}"
        raise ExtensionError(msg) from exc


def setup(app: Sphinx) -> dict[str, Any]:
    """
    Register Sphinx feature-tree preparation hooks.

    Args:
        app: Sphinx application.

    Returns:
        Sphinx extension metadata.

    """
    app.connect("builder-inited", prepare_feature_tree)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
