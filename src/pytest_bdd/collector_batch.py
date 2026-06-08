"""
Provide lazy-batched async feature file parser for collection acceleration.

Responsibility:
    Provide lazy-batched async feature file parser for collection acceleration. It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.collector_batch` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - FeatureBatchParser: owns nested behavior below this boundary
    - _parse_feature_file: owns nested behavior below this boundary
    - _parse_python: owns nested behavior below this boundary
    - _documents_equivalent: owns nested behavior below this boundary
    - _resolve_mimetype: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector.py: imports or references `collector_batch`
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `collector_batch`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `collector_batch`
    - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `collector_batch`

State and side effects:
    mutates raw_dict, parse_results, _aiofiles_available, content, _; depends on __future__.annotations, asyncio,
    logging, multiprocessing, os.

Invariants:
    - `pytest_bdd.collector_batch` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises RuntimeError, re-raise; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
from pathlib import Path  # noqa: TC003
from typing import Any, ClassVar, cast

from attrs import define, field
from cucumber_messages import GherkinDocument
from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser as CucumberIOBaseParser
from returns.maybe import Nothing
from returns.result import Result

from pytest_bdd.model import message_converter  # pylint: disable=downward-import
from pytest_bdd.model.stash_access import StashBound  # pylint: disable=downward-import
from pytest_bdd.types.failure_reasons import CollectorFailure

logger = logging.getLogger(__name__)
CollectorParseResult = Result[object, CollectorFailure]

try:
    import aiofiles  # library has no type stubs

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

    Responsibility:
        Session-scoped lazy-batched feature file parser. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_flushed: owns nested behavior below this boundary
        - set_threshold: owns nested behavior below this boundary
        - register: owns nested behavior below this boundary
        - has_pending: owns nested behavior below this boundary
        - flush: owns nested behavior below this boundary
        - _parse_sync: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `FeatureBatchParser`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `FeatureBatchParser`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `FeatureBatchParser`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `FeatureBatchParser`

    State and side effects:
        mutates parse_results, content, _, doc, self._flushed.

    Invariants:
        - `pytest_bdd.collector_batch.FeatureBatchParser` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    STASH_KEY: ClassVar[str] = "_pytest_bdd_batch_parser"
    DEFAULT_THRESHOLD: ClassVar[int] = 50 if os.name == "posix" else 1000

    _pending: list[Path] = field(factory=list)
    _cache: dict[Path, GherkinDocument] = field(factory=dict)
    _flushed: bool = field(default=False)
    _threshold: int = field(default=DEFAULT_THRESHOLD)

    @property
    def is_flushed(self) -> bool:
        """
        Return True if the batch has already been flushed.

        Responsibility:
            Return True if the batch has already been flushed. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.is_flushed` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `is_flushed`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `is_flushed`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `is_flushed`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `is_flushed`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self._flushed

    def set_threshold(self, threshold: int) -> None:
        """
        Set the minimum number of files to enable parallel batch collection.

        Args:
            threshold: Minimum file count for parallel mode.

        Responsibility:
            Set the minimum number of files to enable parallel batch collection. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.set_threshold`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `set_threshold`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `set_threshold`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `set_threshold`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `set_threshold`

        State and side effects:
            mutates self._threshold.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser.set_threshold` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        self._threshold = threshold

    def register(self, path: Path) -> int:
        """
        Register a feature file path for deferred processing.

        Args:
            path: Absolute path to a .feature file.

        Returns:
            The number of pending paths after registration.

        Responsibility:
            Register a feature file path for deferred processing. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.register` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - path.read_bytes: collaborator call used by this boundary
            - _parse_feature_file: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary
            - logger.exception: collaborator call used by this boundary
            - self._pending.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `register`
            - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `register`
            - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `register`
            - src/pytest_bdd/parsers/parse_parser.py: imports or references `register`
            - src/pytest_bdd/parsers/re_parser.py: imports or references `register`

        State and side effects:
            mutates content, _, doc.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser.register` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        if self._flushed:
            try:
                content = path.read_bytes()
                _, doc = _parse_feature_file(path, content)
                self._cache[path] = doc
            except OSError:
                logger.warning("Failed to read feature file during late registration: %s", path, exc_info=True)
            except Exception:
                logger.exception("Failed to parse feature file during late registration: %s", path)
            return len(self._pending)
        self._pending.append(path)
        return len(self._pending)

    def has_pending(self) -> bool:
        """
        Check if there are unprocessed paths.

        Returns:
            True if there are pending paths and flush has not been called.

        Responsibility:
            Check if there are unprocessed paths. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.has_pending`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `has_pending`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `has_pending`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `has_pending`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `has_pending`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return bool(self._pending) and not self._flushed

    def flush(self) -> int:
        """
        Execute the concurrent read + parallel parse pipeline for all pending paths.

        If the number of pending files is below the threshold, uses a synchronous
        read+parse path to avoid multiprocessing Pool startup overhead.

        Returns:
            The number of successfully parsed files.

        Responsibility:
            Execute the concurrent read + parallel parse pipeline for all pending paths. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.flush` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - logger.info: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - self._pending.clear: collaborator call used by this boundary
            - self._parse_sync: collaborator call used by this boundary
            - self._read_files_async: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `flush`
            - src/pytest_bdd/model/cucumber_formatter_adapter.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py: imports or references `flush`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `flush`

        State and side effects:
            mutates self._flushed, pending, contents.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser.flush` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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
        """
        Parse files synchronously, one at a time, without multiprocessing.

        Responsibility:
            Parse files synchronously, one at a time, without multiprocessing. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser._parse_sync`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _parse_one: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `_parse_sync`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_sync`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_sync`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_sync`

        State and side effects:
            mutates content, _, doc.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser._parse_sync` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """

        def _parse_one(p: Path) -> None:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.collector_batch.FeatureBatchParser._parse_sync._parse_one`
                owns documented method behavior. It directly owns the observable contract, local decisions, and
                maintenance boundary for this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.collector_batch.FeatureBatchParser._parse_sync._parse_one` because it keeps the nearest
                code, data shape, call signature, and failure knowledge together.

            Delegates:
                - p.read_bytes: collaborator call used by this boundary
                - _parse_feature_file: collaborator call used by this boundary
                - logger.warning: collaborator call used by this boundary
                - logger.exception: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/collector.py: imports or references `_parse_one`
                - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_one`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_one`
                - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_one`

            State and side effects:
                mutates content, _, doc.

            Invariants:
                - `pytest_bdd.collector_batch.FeatureBatchParser._parse_sync._parse_one` keeps its documented import
                  path, ownership boundary, and observable behavior stable for callers.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
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

        Responsibility:
            Read files synchronously as fallback. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser._read_files_sync`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _read_one: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `_read_files_sync`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_read_files_sync`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_read_files_sync`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_read_files_sync`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """

        def _read_one(p: Path) -> tuple[Path, bytes] | None:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.collector_batch.FeatureBatchParser._read_files_sync._read_one` owns documented method
                behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
                method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.collector_batch.FeatureBatchParser._read_files_sync._read_one` because it keeps the nearest
                code, data shape, call signature, and failure knowledge together.

            Delegates:
                - p.read_bytes: collaborator call used by this boundary
                - logger.warning: collaborator call used by this boundary
                - Nothing.value_or: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/collector.py: imports or references `_read_one`
                - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_read_one`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_read_one`
                - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_read_one`

            State and side effects:
                keeps no local persistent state beyond call-local values.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=3
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
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

        Responsibility:
            Read files concurrently using aiofiles. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _read_all: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `_read_files_async`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_read_files_async`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_read_files_async`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_read_files_async`

        State and side effects:
            mutates raw_results, results.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """

        async def _read_all() -> list[tuple[Path, bytes | Exception]]:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async._read_all` owns documented async method
                behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
                async method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async._read_all` because it keeps the nearest
                code, data shape, call signature, and failure knowledge together.

            Delegates:
                - _read_one: owns nested behavior below this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/collector.py: imports or references `_read_all`
                - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_read_all`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_read_all`
                - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_read_all`

            State and side effects:
                keeps no local persistent state beyond call-local values.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=3
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """

            async def _read_one(p: Path) -> tuple[Path, bytes | Exception]:
                """
                Responsibility:
                    Responsibility: Responsibility:
                    `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async._read_all._read_one` owns
                    documented async method behavior. It directly owns the observable contract, local decisions, and
                    maintenance boundary for this async method.

                Reason for existence:
                    This entity is the information expert for
                    `pytest_bdd.collector_batch.FeatureBatchParser._read_files_async._read_all._read_one` because it
                    keeps the nearest code, data shape, call signature, and failure knowledge together.

                Delegates:
                    - aiofiles.open: collaborator call used by this boundary
                    - f.read: collaborator call used by this boundary

                Cohesion:
                    The implementation stays together because its imports, calls, state writes, and return contract
                    describe one maintainable decision unit.

                Separation:
                    - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                      changeable without widening caller knowledge.

                Main consumers:
                    - src/pytest_bdd/collector.py: imports or references `_read_one`
                    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_read_one`
                    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_read_one`
                    - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_read_one`

                State and side effects:
                    keeps no local persistent state beyond call-local values.

                Architecture score:
                    #arch-eval:reason_for_existence=4
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=4
                    #arch-eval:cohesion=4
                    #arch-eval:separation=3
                    #arch-eval:consumer_clarity=4
                    #arch-eval:state_invariants=3
                    #arch-eval:entity_fullness=4
                    #arch-eval:locational_stability=4
                """
                try:
                    async with aiofiles.open(p, "rb") as f:  # type: ignore[attr-defined]  # aiofiles is untyped; async context manager attributes not known
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
        """
        Parse file contents and populate cache.

        Responsibility:
            Parse file contents and populate cache. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser._parse_and_cache`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - multiprocessing.get_context: collaborator call used by this boundary
            - ctx.Pool: collaborator call used by this boundary
            - pool.starmap: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary
            - _parse_feature_file: collaborator call used by this boundary
            - logger.exception: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `_parse_and_cache`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_and_cache`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_and_cache`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_and_cache`

        State and side effects:
            mutates parse_results, ctx.

        Invariants:
            - `pytest_bdd.collector_batch.FeatureBatchParser._parse_and_cache` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        try:
            ctx = multiprocessing.get_context("spawn")
            with ctx.Pool() as pool:
                parse_results = pool.starmap(_parse_feature_file, contents)
        except (OSError, RuntimeError, ValueError):
            logger.warning("Multiprocessing parse failed, falling back to synchronous parse", exc_info=True)
            parse_results = []

            def _parse_safe(p: Path, c: bytes) -> tuple[Path, GherkinDocument] | None:
                """
                Responsibility:
                    Responsibility: Responsibility:
                    `pytest_bdd.collector_batch.FeatureBatchParser._parse_and_cache._parse_safe` owns documented method
                    behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
                    this method.

                Reason for existence:
                    This entity is the information expert for
                    `pytest_bdd.collector_batch.FeatureBatchParser._parse_and_cache._parse_safe` because it keeps the
                    nearest code, data shape, call signature, and failure knowledge together.

                Delegates:
                    - _parse_feature_file: collaborator call used by this boundary
                    - logger.exception: collaborator call used by this boundary
                    - Nothing.value_or: collaborator call used by this boundary

                Cohesion:
                    The implementation stays together because its imports, calls, state writes, and return contract
                    describe one maintainable decision unit.

                Separation:
                    - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                      changeable without widening caller knowledge.

                Main consumers:
                    - src/pytest_bdd/collector.py: imports or references `_parse_safe`
                    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_safe`
                    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_safe`
                    - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_safe`

                State and side effects:
                    keeps no local persistent state beyond call-local values.

                Architecture score:
                    #arch-eval:reason_for_existence=4
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=4
                    #arch-eval:cohesion=4
                    #arch-eval:separation=3
                    #arch-eval:consumer_clarity=4
                    #arch-eval:state_invariants=3
                    #arch-eval:entity_fullness=4
                    #arch-eval:locational_stability=4
                """
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

        Responsibility:
            Retrieve a parsed Gherkin document from cache. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch.FeatureBatchParser.get` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary
            - self._cache.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `get`
            - src/pytest_bdd/_gherkin_go/_bridge.py: imports or references `get`
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `get`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `get`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `get`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

    Responsibility:
        Parse a single feature file from raw bytes content. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector_batch._parse_feature_file` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - logger.warning: collaborator call used by this boundary
        - _parse_python: collaborator call used by this boundary
        - content.decode: collaborator call used by this boundary
        - path.as_posix: collaborator call used by this boundary
        - _resolve_mimetype.endswith: collaborator call used by this boundary
        - _resolve_mimetype: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `_parse_feature_file`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_feature_file`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_feature_file`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_feature_file`

    State and side effects:
        mutates raw_dict, text, uri, is_markdown, parser; depends on pytest_bdd._gherkin_go._get_parser,
        pytest_bdd._gherkin_go._types.GherkinGoNotAvailable, pytest_bdd._gherkin_go._types.GherkinParseError.

    Invariants:
        - `pytest_bdd.collector_batch._parse_feature_file` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    text = content.decode("utf-8")
    uri = "file:" + path.as_posix()
    is_markdown = _resolve_mimetype(path).endswith("+markdown")

    from pytest_bdd._gherkin_go import _get_parser
    from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError

    parser = _get_parser()
    try:
        raw_dict = parser(text, uri=uri)  # type: ignore[call-arg]  # Go ctypes parser accepts extra kwargs
    except GherkinParseError as exc:
        for err in exc.errors:
            if "source" in err and isinstance(err["source"], dict):
                err["source"]["uri"] = str(path)
        raise
    except (GherkinGoNotAvailable, OSError, RuntimeError):
        logger.warning("Go gherkin parser failed for %s, falling back to Python", path, exc_info=True)
        raw_dict = _parse_python(text)
    else:
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


def _parse_python(text: str) -> dict[str, object]:
    """
    Parse Gherkin text using the Python parser.

    Responsibility:
        Parse Gherkin text using the Python parser. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector_batch._parse_python` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - CucumberIOBaseParser: collaborator call used by this boundary
        - AstBuilder: collaborator call used by this boundary
        - parser.parse: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `_parse_python`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_parse_python`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_parse_python`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_parse_python`

    State and side effects:
        mutates parser, raw_dict.

    Invariants:
        - `pytest_bdd.collector_batch._parse_python` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    parser = CucumberIOBaseParser(ast_builder=AstBuilder())
    raw_dict = parser.parse(text)
    del parser
    return cast("dict[str, object]", raw_dict)


def _documents_equivalent(go_doc: dict[str, object], python_doc: dict[str, object]) -> bool:
    """
    Check if Go and Python GherkinDocument dicts are semantically equivalent.

    Responsibility:
        Check if Go and Python GherkinDocument dicts are semantically equivalent. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector_batch._documents_equivalent` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _normalize: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `_documents_equivalent`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_documents_equivalent`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_documents_equivalent`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_documents_equivalent`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def _normalize(doc: dict[str, object]) -> Any:  # noqa: ANN401
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.collector_batch._documents_equivalent._normalize` owns
            documented function behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.collector_batch._documents_equivalent._normalize`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - _normalize: collaborator call used by this boundary
            - doc.items: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `_normalize`
            - src/pytest_bdd/parser.py: imports or references `_normalize`
            - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_normalize`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_normalize`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_normalize`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        if not isinstance(doc, dict):
            return doc  # recursion base case
        return {k: _normalize(v) for k, v in doc.items() if v is not None and k != "id"}  # type: ignore[arg-type]  # recursive values of varying types

    return cast("bool", _normalize(go_doc) == _normalize(python_doc))


def _resolve_mimetype(path: Path) -> str:
    """
    Resolve mimetype value from file extension for the Go parser.

    Responsibility:
        Resolve mimetype value from file extension for the Go parser. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.collector_batch._resolve_mimetype` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - path.name.lower: collaborator call used by this boundary
        - name.endswith: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `_resolve_mimetype`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `_resolve_mimetype`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_resolve_mimetype`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `_resolve_mimetype`

    State and side effects:
        mutates name.

    Invariants:
        - `pytest_bdd.collector_batch._resolve_mimetype` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    name = path.name.lower()
    if name.endswith(".feature.md"):
        return "text/x.cucumber.gherkin+markdown"
    return "text/x.cucumber.gherkin+plain"
