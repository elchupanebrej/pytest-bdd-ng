"""Provide lazy-batched async feature file parser for collection acceleration."""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
from pathlib import Path  # noqa: TC003
from typing import ClassVar

from attrs import define, field
from cucumber_messages import GherkinDocument
from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser as CucumberIOBaseParser
from returns.maybe import Nothing
from returns.result import Result

from pytest_bdd.model import message_converter
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.types.failure_reasons import CollectorFailure

logger = logging.getLogger(__name__)
CollectorParseResult = Result[object, CollectorFailure]

try:
    import aiofiles

    _aiofiles_available = True
except ImportError:
    _aiofiles_available = False

_REGISTER_AFTER_FLUSH_MSG = "Cannot register paths after batch has been flushed"
_GET_BEFORE_FLUSH_MSG = "Cannot retrieve document before batch is flushed"


@define
class FeatureBatchParser(StashBound):
    """
    Session-scoped lazy-batched feature file parser.

    Accumulates file paths during pytest directory walk and flushes them
    through a concurrent asyncio read + multiprocessing parse pipeline
    on first access.
    """

    STASH_KEY: ClassVar[str] = "_pytest_bdd_batch_parser"
    DEFAULT_THRESHOLD: ClassVar[int] = 50 if os.name == "posix" else 1000

    _pending: list[Path] = field(factory=list)
    _cache: dict[Path, GherkinDocument] = field(factory=dict)
    _flushed: bool = field(default=False)
    _threshold: int = field(default=DEFAULT_THRESHOLD)

    @property
    def is_flushed(self) -> bool:
        """Return True if the batch has already been flushed."""
        return self._flushed

    def set_threshold(self, threshold: int) -> None:
        """
        Set the minimum number of files to enable parallel batch collection.

        Args:
            threshold: Minimum file count for parallel mode.

        """
        self._threshold = threshold

    def register(self, path: Path) -> int:
        """
        Register a feature file path for deferred processing.

        Args:
            path: Absolute path to a .feature file.

        Returns:
            The number of pending paths after registration.

        Raises:
            RuntimeError: If the batch has already been flushed.

        """
        if self._flushed:
            raise RuntimeError(_REGISTER_AFTER_FLUSH_MSG)
        self._pending.append(path)
        return len(self._pending)

    def has_pending(self) -> bool:
        """
        Check if there are unprocessed paths.

        Returns:
            True if there are pending paths and flush has not been called.

        """
        return bool(self._pending) and not self._flushed

    def flush(self) -> int:
        """
        Execute the concurrent read + parallel parse pipeline for all pending paths.

        If the number of pending files is below the threshold, uses a synchronous
        read+parse path to avoid multiprocessing Pool startup overhead.

        Returns:
            The number of successfully parsed files.

        """
        if self._flushed or not self._pending:
            self._flushed = True
            return 0

        pending = list(self._pending)
        self._pending.clear()
        self._flushed = True

        if len(pending) < self._threshold:
            logger.info("Below batch threshold (%d < %d), using sync parse", len(pending), self._threshold)
            self._parse_sync(pending)
        else:
            logger.info("Above batch threshold (%d >= %d), using parallel parse", len(pending), self._threshold)
            contents = self._read_files_async(pending) if _aiofiles_available else self._read_files_sync(pending)
            if contents:
                self._parse_and_cache(contents)

        return sum(1 for p in pending if p in self._cache)

    def _parse_sync(self, paths: list[Path]) -> None:
        """Parse files synchronously, one at a time, without multiprocessing."""

        def _parse_one(p: Path) -> None:
            try:
                content = p.read_bytes()
                _, doc = _parse_feature_file(p, content)
                self._cache[p] = doc
            except OSError:
                logger.warning("Failed to read feature file: %s", p, exc_info=True)
            except Exception:
                logger.exception("Failed to parse feature file: %s", p)

        for path in paths:
            _parse_one(path)

    @staticmethod
    def _read_files_sync(paths: list[Path]) -> list[tuple[Path, bytes]]:
        """
        Read files synchronously as fallback.

        Returns:
            List of (path, content) tuples for files that were read successfully.

        """

        def _read_one(p: Path) -> tuple[Path, bytes] | None:
            try:
                return (p, p.read_bytes())
            except OSError:
                logger.warning("Failed to read feature file: %s", p, exc_info=True)
                return Nothing.value_or(None)

        return [r for p in paths if (r := _read_one(p)) is not None]

    @staticmethod
    def _read_files_async(paths: list[Path]) -> list[tuple[Path, bytes]]:
        """
        Read files concurrently using aiofiles.

        Returns:
            List of (path, content) tuples for files that were read successfully.

        """

        async def _read_all() -> list[tuple[Path, bytes | Exception]]:
            async def _read_one(p: Path) -> tuple[Path, bytes | Exception]:
                try:
                    async with aiofiles.open(p, "rb") as f:  # type: ignore[union-attr]
                        return (p, await f.read())
                except OSError as e:
                    return (p, e)

            return await asyncio.gather(*(_read_one(p) for p in paths))

        raw_results = asyncio.run(_read_all())
        results: list[tuple[Path, bytes]] = []
        for path, result in raw_results:
            if isinstance(result, bytes):
                results.append((path, result))
            else:
                logger.warning("Failed to read feature file: %s", path, exc_info=result)
        return results

    def _parse_and_cache(self, contents: list[tuple[Path, bytes]]) -> None:
        """Parse file contents and populate cache."""
        try:
            ctx = multiprocessing.get_context("spawn")
            with ctx.Pool() as pool:
                parse_results = pool.starmap(_parse_feature_file, contents)
        except (OSError, RuntimeError, ValueError):
            logger.warning("Multiprocessing parse failed, falling back to synchronous parse", exc_info=True)
            parse_results = []

            def _parse_safe(p: Path, c: bytes) -> tuple[Path, GherkinDocument] | None:
                try:
                    return _parse_feature_file(p, c)
                except (OSError, RuntimeError, ValueError):
                    logger.exception("Failed to parse feature file: %s", p)
                    return Nothing.value_or(None)

            parse_results = [r for p, c in contents if (r := _parse_safe(p, c)) is not None]

        for path, doc in parse_results:
            self._cache[path] = doc

    def get(self, path: Path) -> GherkinDocument | None:
        """
        Retrieve a parsed Gherkin document from cache.

        Args:
            path: Absolute path to a .feature file.

        Returns:
            The parsed GherkinDocument, or None if the path was not registered
            or its parse failed.

        Raises:
            RuntimeError: If flush has not been called yet.

        """
        if not self._flushed:
            raise RuntimeError(_GET_BEFORE_FLUSH_MSG)
        return self._cache.get(path)


def _parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]:
    """
    Parse a single feature file from raw bytes content.

    Must be a module-level free function so it is picklable by multiprocessing.Pool.

    Args:
        path: Absolute path to the feature file (for error attribution).
        content: Raw UTF-8 bytes of the file content.

    Returns:
        A tuple of (path, parsed GherkinDocument).

    """
    text = content.decode("utf-8")
    mimetype_str = _resolve_mimetype(path)
    is_markdown = mimetype_str.endswith("+markdown")

    if _should_use_go_backend():
        raw_dict = _try_go_parse(text, path)
        if raw_dict is not None:
            if is_markdown:
                python_dict = _parse_python(text)
                if not _documents_equivalent(raw_dict, python_dict):
                    logger.warning(
                        "Go and Python parsers produced different results for %s, using Python result",
                        path,
                    )
                    raw_dict = python_dict
            gherkin_document = message_converter.from_dict(raw_dict, GherkinDocument)
            return (path, gherkin_document)

    raw_dict = _parse_python(text)
    gherkin_document = message_converter.from_dict(raw_dict, GherkinDocument)
    return (path, gherkin_document)


def _parse_python(text: str) -> dict:
    """Parse Gherkin text using the Python parser."""
    parser = CucumberIOBaseParser(ast_builder=AstBuilder())
    raw_dict = parser.parse(text)
    del parser
    return raw_dict


def _documents_equivalent(go_doc: dict, python_doc: dict) -> bool:
    """Check if Go and Python GherkinDocument dicts are semantically equivalent."""

    def _normalize(doc: dict) -> dict:
        if not isinstance(doc, dict):
            return doc
        return {k: _normalize(v) for k, v in doc.items() if v is not None and k != "id"}

    return _normalize(go_doc) == _normalize(python_doc)


def _resolve_mimetype(path: Path) -> str:
    """Resolve mimetype value from file extension for the Go parser."""
    name = path.name.lower()
    if name.endswith(".feature.md"):
        return "text/x.cucumber.gherkin+markdown"
    return "text/x.cucumber.gherkin+plain"


def _try_go_parse(text: str, path: Path) -> dict | None:
    """Attempt to parse via Go backend. Returns dict or None (for fallback)."""
    try:
        from pytest_bdd._gherkin_go import parse as go_parse
        from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError
        from pytest_bdd.mimetype import Mimetype

        mimetype_str = _resolve_mimetype(path)
        mimetype = Mimetype(mimetype_str)
        return go_parse(text, mimetype=mimetype)
    except GherkinParseError as exc:
        for err in exc.errors:
            if "source" in err and isinstance(err["source"], dict):
                err["source"]["uri"] = str(path)
        raise
    except GherkinGoNotAvailable:
        if _strict_go_mode():
            raise
        logger.debug("Go gherkin parser unavailable for %s, falling back to Python", path)
        return Nothing.value_or(None)
    except (OSError, RuntimeError):
        if _strict_go_mode():
            raise
        logger.warning("Go gherkin parser failed for %s, falling back to Python", path, exc_info=True)
        return Nothing.value_or(None)


def _should_use_go_backend() -> bool:
    """Check if Go backend should be attempted based on env var."""
    from pytest_bdd._gherkin_go import should_use_go_backend

    return should_use_go_backend()


def _strict_go_mode() -> bool:
    """Check if Go backend is forced — no fallback to Python."""
    from pytest_bdd._gherkin_go import is_strict_go_mode

    return is_strict_go_mode()
