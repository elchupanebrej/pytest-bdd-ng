"""
Lazy-batched asynchronous feature file parsing for the pytest collection phase.

Responsibility:
    Lazy-batched asynchronous feature file parsing for the pytest collection phase. Defines FeatureBatchParser, a
    StashBound class that accumulates feature file paths during collection, then parses them all at once when the batch
    is flushed. Supports three parsing strategies: synchronous (for small batches below a configurable threshold),
    parallel multiprocessing (for large batches, using starmap over a spawn-context Pool), and async I/O via aiofiles
    (when available, for reading files in parallel before parsing). Also provides module-level helper functions
    (_parse_feature_file, _parse_python, _documents_equivalent, _resolve_mimetype) used by the batch parser.

Reason for existence:
    Without batching, each feature file would be read and parsed individually during collection, causing O(n) file I/O
    operations and Gherkin parse calls that cannot benefit from parallelism. This module is the information expert for
    "parse many feature files efficiently." It is placed in the parsing layer (order 2) because its primary concern is
    Gherkin document production — it consumes the Go ctypes parser, the Python CucumberIOBaseParser, and the
    cucumber_messages GherkinDocument type. It is separated from the synchronous parser.py because it adds batching,
    threshold-based strategy selection, async I/O, multiprocessing, and Go-parser fallback logic that the individual
    parse() methods in parser.py do not need.

Delegates:
    - _parse_feature_file: Module-level function that parses a single feature file, preferring the Go ctypes parser with
    fallback to Python, and converts the result to a GherkinDocument via message_converter.
    - _parse_python: Parses Gherkin text using the Python CucumberIOBaseParser and returns a raw dict.
    - _documents_equivalent: Compares Go and Python parser outputs (with id-stripping normalization) to detect parser
    divergence.
    - _resolve_mimetype: Determines the Gherkin mimetype (plain vs markdown) from the file extension.
    - pytest_bdd.model.message_converter.from_dict: Converts raw dict to typed GherkinDocument.
    - pytest_bdd.model.stash_access.StashBound: Provides find_in_stash classmethod for pytest.config.stash integration.
    - cucumber_messages.GherkinDocument: Typed output type stored in _cache.
    - gherkin.ast_builder.AstBuilder / gherkin.parser.Parser: Python Gherkin parser components.
    - pytest_bdd._gherkin_go._get_parser: Go ctypes parser bridge.

Cohesion:
    Every entity in this module serves the single pipeline: accumulate paths → read files (sync/async) → parse
    (sync/multiprocess/fallback) → cache GherkinDocuments → retrieve on demand. The FeatureBatchParser class owns the
    state machine (pending → flushed), threshold logic, and strategy dispatch. The module-level functions are pure
    parsing/comparison utilities that do not depend on the class. There is no unrelated logic.

Separation:
    - pytest_bdd.parser: Owns the individual synchronous parser implementations (GherkinParser, MarkdownGherkinParser).
    The batch parser calls _parse_feature_file which internally delegates to the Go parser and falls back to
    _parse_python, but does not use GherkinParser or MarkdownGherkinParser directly — it bypasses them for performance.
    - pytest_bdd.model.message_converter: Owns the dict-to-GherkinDocument conversion. The batch parser consumes it but
    does not own the conversion logic.
    - pytest_bdd._gherkin_go: Owns the Go ctypes bridge. The batch parser imports it conditionally at function-call time.

Main consumers:
    - pytest_bdd.collector.FeatureFileModule.collect: Calls FeatureBatchParser.find_in_stash to retrieve the batch
    parser, checks has_pending(), and calls flush() before collecting.
    - pytest_bdd.plugin.scenario_test_collector: Creates and installs the FeatureBatchParser instance into
    pytest.config.stash during plugin registration; calls register() for each discovered feature file path.
    - pytest_bdd.scenario.scenarios: May interact with the batch parser indirectly through the collection pipeline, but
    does not import this module directly.

State and side effects:
    FeatureBatchParser maintains three mutable fields: _pending (list of Path), _cache (dict[Path, GherkinDocument]),
    and _flushed (bool). The _threshold determines strategy selection. flush() triggers file I/O (reading feature
    files), multiprocessing pool creation (with spawn context), and async event loop execution (asyncio.run). The parsed
    documents are stored in _cache and accessible via get() after flush. The instance is stored in pytest.config.stash
    under STASH_KEY. The module-level _parse_feature_file function has side effects: it imports pytest_bdd._gherkin_go
    dynamically and may raise GherkinParseError which carries source URI information.

Invariants:
    - Once _flushed is True, register() must not append to _pending (paths are parsed immediately and cached instead).
    - get() must raise RuntimeError if called before _flushed is True.
    - The Go parser result is preferred, but if Go fails or produces different output than Python, the Python result is
    used (verification is done per-file for markdown, not globally).
    - The multiprocessing pool uses "spawn" context to avoid issues with forked process state in pytest environments.

Failure semantics:
    FeatureBatchParser.get() raises RuntimeError with _GET_BEFORE_FLUSH_MSG if called before flush. OSError during file
    reading logs a warning and skips the file. CompositeParserException and GherkinParseError are caught and re-raised
    (in _parse_feature_file) or logged (in fallback paths). Multiprocessing failures (OSError, RuntimeError, ValueError
    from pool creation) trigger a warning and fall back to synchronous parsing.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
from pathlib import Path  # noqa: TC003  -- type checking import needed at runtime for isinstance/validators
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
    Lazy-batched feature file parser that accumulates feature file Paths during pytest collection, then parses them all a.

    Responsibility:
        Lazy-batched feature file parser that accumulates feature file Paths during pytest collection, then parses them
        all at once when flush() is called. Selects a parsing strategy based on the number of pending files relative to
        a configurable threshold: synchronous sequential parsing for small batches (< threshold), and parallel
        multiprocessing parsing (with spawn-context Pool.starmap) for large batches (>= threshold). When aiofiles is
        available, file reading is done asynchronously before parallel parsing. Supports late registration (calling
        register() after flush()) by parsing files immediately and caching them. Integrates with pytest.config.stash via
        StashBound for singleton lifecycle management.

    Reason for existence:
        Parsing each feature file individually during collection is O(n) in I/O and CPU time. Batching allows the parser
        to read files in parallel (async I/O) and parse them using multiple processes (multiprocessing Pool),
        dramatically reducing collection time for projects with many feature files. This class is the information expert
        for "how and when to batch-parse feature files." It is kept separate from the synchronous parser.py parsers
        because it adds a state machine (pending → flushed), strategy selection (threshold-based), multiprocessing
        coordination, and async I/O that are orthogonal to how an individual Gherkin document is parsed.

    Delegates:
        - _parse_feature_file: Module-level worker that parses a single file (Go parser with Python fallback) and
        returns (path, GherkinDocument). Called by _parse_sync, _parse_and_cache, and register() for late registrations.
        - _parse_sync: Sequential synchronous parsing loop for small batches.
        - _read_files_sync / _read_files_async: Read file contents (sync or async) into memory before parsing.
        - _parse_and_cache: Parallel parsing using multiprocessing Pool.starmap with spawn context and synchronous fallback.
        - StashBound.find_in_stash: Retrieves the singleton parser instance from pytest.config.stash.

    Cohesion:
        Every method in this class participates in the state machine around _pending, _cache, and _flushed. register()
        adds paths, has_pending() queries, flush() transitions the state and triggers parsing, get() retrieves cached
        documents. The private _parse* and _read* methods all serve flush()'s strategy selection. There is no logic
        unrelated to batch-parse lifecycle management.

    Separation:
        - pytest_bdd.parser.GherkinParser / MarkdownGherkinParser: Synchronous parsers that parse one file at a time
        with full error reporting. The batch parser does not use them — it uses _parse_feature_file which directly calls
        the Go parser and falls back to the raw CucumberIOBaseParser.
        - pytest_bdd.collector.FeatureFileModule: Consumes the batch parser (finds it in stash, flushes it) but does not
        own the batching strategy or thresholds.

    Main consumers:
        - pytest_bdd.collector.FeatureFileModule.collect: Finds the batch parser in stash and calls flush() before collection.
        - pytest_bdd.plugin.scenario_test_collector: Creates the FeatureBatchParser instance and registers it in
        pytest.config.stash. Calls register() for each discovered feature file path.

    State and side effects:
        _pending: list[Path] — accumulated feature file paths awaiting flush. Cleared on flush. _cache: dict[Path,
        GherkinDocument] — parsed documents, populated during flush or late registration. _flushed: bool — set True on
        first flush; once True, register() parses immediately. _threshold: int — strategy boundary; defaults to 50 on
        POSIX, 1000 on Windows. flush() triggers file I/O (reading feature files), multiprocessing pool creation, and
        asyncio event loop execution. The instance is stored in pytest.config.stash.

    Invariants:
        - Before flush: _pending accumulates paths, _flushed is False, _cache is empty. register() appends to _pending.
        - After flush: _pending is empty, _flushed is True, _cache contains parsed documents. register() parses immediately.
        - get() must not be called before flush() — raises RuntimeError.

    Failure semantics:
        get() raises RuntimeError if called before flush. OSError during file read is logged as warning and the file is
        skipped. CompositeParserException and GherkinParseError in _parse_feature_file are re-raised to the caller.
        Multiprocessing failures (OSError, RuntimeError, ValueError) trigger fallback to synchronous parsing with a
        warning log.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
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
        Read-only property exposing the internal _flushed flag.

        Responsibility:
            Read-only property exposing the internal _flushed flag. Returns True if flush() has been called at least
            once, False otherwise. Consumers can use this to check whether the batch parser has transitioned out of the
            accumulation phase before attempting to call get() or register().

        Reason for existence:
            Exposes the flushed state as a public read-only attribute rather than directly accessing the private
            _flushed field. This is a minimal encapsulation boundary that could later add derived logic (e.g., checking
            if _pending is also empty) without changing the consumer API.

        Delegates:
            - None. Directly returns the _flushed field.

        Cohesion:
            Single-purpose accessor with no branching or side effects. Entirely cohesive with the state-machine concern
            of FeatureBatchParser.

        Separation:
            - has_pending(): Reports whether there are unparsed paths AND the batch has not been flushed. is_flushed
            reports only the flushed flag regardless of pending state.

        Main consumers:
            - External code checking whether the batch parser has completed its flush cycle. Not currently consumed
            within the module itself (internal code reads _flushed directly).

        State and side effects:
            None. Pure read accessor.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        return self._flushed

    def set_threshold(self, threshold: int) -> None:
        """
        Mutates the batch-size threshold that determines whether flush() uses synchronous or parallel parsing.

        Responsibility:
            Mutates the batch-size threshold that determines whether flush() uses synchronous or parallel parsing. When
            the number of pending files is below the threshold, files are parsed synchronously in a loop; at or above,
            multiprocessing (or async+multiprocessing) is used. Allows callers to tune the performance characteristics
            based on environment constraints (e.g., CI with limited cores, or development with many small feature
            files).

        Reason for existence:
            The threshold is platform-dependent by default (50 on POSIX, 1000 on Windows) because multiprocessing
            overhead differs across platforms. This method provides a runtime override for environments where the
            default is inappropriate. It exists as a separate setter (rather than making _threshold a public attribute)
            to allow future validation logic.

        Delegates:
            - None. Directly assigns self._threshold.

        Cohesion:
            Single-purpose setter. Cohesive with the batch strategy selection concern.

        Separation:
            - flush(): Uses _threshold to choose the parsing strategy. set_threshold configures it.

        Main consumers:
            - Plugin initialization code that wants to override the default threshold based on environment or configuration.

        State and side effects:
            Mutates self._threshold. No validation, no I/O, no stash access.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        self._threshold = threshold

    def register(self, path: Path) -> int:
        """
        Register a feature file path for batch parsing.

        Responsibility:
            Registers a feature file path for batch parsing. Before flush(): appends the path to the internal _pending
            list and returns the new length. After flush() (late registration): immediately reads and parses the file,
            caches the GherkinDocument in _cache, and returns the current _pending length (which will be 0 if _pending
            was cleared). Handles OSError and general Exception gracefully by logging warnings/errors and continuing.

        Reason for existence:
            This is the primary entry point for feeding feature file paths into the batch parser during pytest
            collection. The dual-mode behavior (accumulate before flush, parse-immediately after flush) allows the same
            API to be used both during the main collection walk and for any late-discovered files. The return value
            (pending count) allows callers to check whether the batch threshold has been reached.

        Delegates:
            - path.read_bytes(): Reads the feature file content for immediate parsing in late-registration mode.
            - _parse_feature_file: Parses the file content into a (path, GherkinDocument) tuple in late-registration mode.
            - list.append: Adds the path to _pending in pre-flush mode.

        Cohesion:
            The method is a single if/else dispatch on _flushed state, with both branches serving the same purpose:
            "ensure this path's GherkinDocument will be available in _cache." Cohesive with the batch lifecycle.

        Separation:
            - flush(): Consumes the accumulated _pending list. register() populates it.
            - get(): Retrieves cached documents. register() populates the cache.

        Main consumers:
            - pytest_bdd.plugin.scenario_test_collector: Calls register() for each feature file path discovered during
            pytest collection.

        State and side effects:
            Pre-flush: appends to _pending (mutable list). Post-flush: reads file from disk (I/O), calls
            _parse_feature_file (potentially imports Go parser, runs Python parser), populates _cache. Logs warnings on
            OSError, exceptions on parse failure. No pytest stash access directly.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Report whether there are unparsed feature files awaiting flush.

        Responsibility:
            Reports whether there are unparsed feature files awaiting flush. Returns True only when _pending is non-
            empty AND _flushed is False. Once flush() is called (even if it processed zero files), this returns False
            forever.

        Reason for existence:
            Callers (specifically FeatureFileModule.collect()) need to know whether they should call flush() before
            proceeding with collection. This predicate encapsulates the condition check so callers don't need to inspect
            _pending and _flushed directly.

        Delegates:
            - None. Directly checks _pending and _flushed fields.

        Cohesion:
            Single-purpose boolean predicate. Cohesive with the batch lifecycle state machine.

        Separation:
            - is_flushed: Reports only the flushed flag, ignoring pending state. has_pending combines both.

        Main consumers:
            - pytest_bdd.collector.FeatureFileModule.collect: Guards the flush() call.

        State and side effects:
            None. Pure read accessor of internal state.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        return bool(self._pending) and not self._flushed

    def flush(self) -> int:
        """
        Transitions the batch parser from accumulation to completion: takes a snapshot of _pending, clears it, sets _flushed=.

        Responsibility:
            Transitions the batch parser from accumulation to completion: takes a snapshot of _pending, clears it, sets
            _flushed=True, and parses all accumulated files using the strategy determined by comparing len(pending)
            against _threshold. Below threshold: calls _parse_sync (sequential). At or above threshold: reads all files
            (async if aiofiles is available, otherwise sync), then calls _parse_and_cache (parallel multiprocessing with
            spawn context). Returns the count of successfully parsed files. If already flushed or no pending files, sets
            _flushed=True and returns 0.

        Reason for existence:
            This is the core method that realizes the batching optimization. It is the information expert for "when and
            how to transition from accumulation to batch processing." The threshold-based strategy selection allows the
            parser to avoid multiprocessing overhead for small feature sets while leveraging parallelism for large ones.
            The async file reading (when available) further reduces I/O wait time before CPU-bound parsing begins.

        Delegates:
            - _parse_sync: Handles synchronous sequential parsing for small batches.
            - _read_files_async / _read_files_sync: Reads all file contents into memory.
            - _parse_and_cache: Handles parallel multiprocessing parsing for large batches.
            - list() constructor: Snapshots _pending to avoid mutation during parsing.
            - list.clear(): Empties _pending after snapshot.

        Cohesion:
            The method is a pure orchestrator: snapshot state, select strategy, delegate, return count. Every branch
            serves the single purpose of "parse all pending files and cache results."

        Separation:
            - register(): Populates _pending before flush. flush() consumes it.
            - get(): Retrieves cached documents after flush. flush() populates the cache.

        Main consumers:
            - pytest_bdd.collector.FeatureFileModule.collect: Calls flush() to ensure all feature files are parsed
            before test collection begins.
            - Potentially any code that wants to force batch parsing to complete.

        State and side effects:
            Mutates _pending (clears it), _flushed (sets to True), _cache (populates with parsed GherkinDocuments).
            Triggers file I/O (reading feature files), multiprocessing pool creation (spawn context), asyncio event loop
            (asyncio.run). Logs info about strategy selection. The state transition is idempotent — calling flush()
            again after the first call returns 0 immediately.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
        Sequentially parses a list of feature file paths in the current process.

        Responsibility:
            Sequentially parses a list of feature file paths in the current process. For each path, calls
            _parse_feature_file to read and parse the file, then caches the resulting GherkinDocument in self._cache.
            Handles OSError during file read and general Exception during parsing by logging and continuing to the next
            file. This is the fallback strategy for small batches where multiprocessing overhead would exceed the
            benefit.

        Reason for existence:
            Multiprocessing has a non-trivial startup cost (spawning processes, serializing data). For batches smaller
            than _threshold, sequential parsing in the current process is faster. This method isolates the sync strategy
            so that flush() only needs to choose between _parse_sync and the parallel path without knowing the details
            of either.

        Delegates:
            - _parse_one (inner function): Reads a single file, calls _parse_feature_file, caches the result, and
            handles errors with logging.
            - _parse_feature_file: The actual parsing worker (Go parser with Python fallback).

        Cohesion:
            The method wraps a simple for-loop over paths with an inner function for per-file error handling. The inner
            function _parse_one is defined locally because it captures self._cache — it is intrinsically coupled to this
            instance's state.

        Separation:
            - _parse_and_cache: Handles parallel multiprocessing parsing. _parse_sync handles sequential.
            - _read_files_sync / _read_files_async: Separate file-reading concerns. _parse_sync reads and parses in one
            step per file.

        Main consumers:
            - flush(): Called when the pending count is below the threshold.

        State and side effects:
            Populates self._cache with parsed GherkinDocuments. Reads files from disk. Logs warnings/errors on failures.
            The inner function _parse_one is a closure over self.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """

        def _parse_one(p: Path) -> None:
            """
            Read a single feature file from disk (p.read_bytes()), calls _parse_feature_file to parse it, and stores the resulti.

            Responsibility:
                Reads a single feature file from disk (p.read_bytes()), calls _parse_feature_file to parse it, and
                stores the resulting GherkinDocument in the enclosing FeatureBatchParser's _cache dict. If OSError
                occurs during file read, logs a warning. If any other Exception occurs during parsing, logs the full
                exception. This inner function exists because it closes over self._cache and is only meaningful within
                the context of _parse_sync's sequential loop.

            Reason for existence:
                Defined as an inner function to capture self._cache from the enclosing _parse_sync method scope. This
                avoids passing self as an explicit parameter and keeps the per-file error handling logic local to the
                sequential parsing strategy. It is the sync counterpart to the _parse_one inner function in
                _read_files_sync.

            Delegates:
                - p.read_bytes(): Reads the file content.
                - _parse_feature_file: Parses the bytes into a (path, GherkinDocument) tuple.

            Cohesion:
                The function performs exactly three steps: read, parse, cache. All serve the single purpose of "parse
                one file and store the result."

            Separation:
                - _read_files_sync._read_one: Reads the file but does not parse it — returns (path, bytes) for later batch parsing.
                - _parse_and_cache._parse_safe: Similar parse-and-cache logic but used in the multiprocessing fallback path.

            Main consumers:
                - _parse_sync: Calls _parse_one in a for-loop over paths.

            State and side effects:
                Reads file from disk. Mutates self._cache (via closure). Logs warnings/errors.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
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
        Read all files in the given path list synchronously using Path.read_bytes().

        Responsibility:
            Reads all files in the given path list synchronously using Path.read_bytes(). For each path, attempts to
            read the file content; on OSError, logs a warning and skips the file. Returns a list of (Path, bytes) tuples
            for successfully read files only. This is used by flush() as the file-reading step before parallel parsing
            when aiofiles is not available.

        Reason for existence:
            Separates file I/O from parsing so that flush() can read all files into memory first, then hand the byte
            contents to the multiprocessing pool for parallel parsing. This separation is necessary because
            multiprocessing workers cannot reliably access filesystem paths that may be relative or on network mounts —
            the bytes must be in the parent process's memory before being sent to workers. The synchronous version
            exists as a fallback when aiofiles is not installed.

        Delegates:
            - _read_one (inner function): Reads a single file and returns (Path, bytes) or None on OSError.
            - Path.read_bytes(): Reads the file content.

        Cohesion:
            The method orchestrates a list comprehension over paths with an inner function for per-file error handling.
            The inner function _read_one captures nothing — it is defined locally only for organizational clarity.

        Separation:
            - _read_files_async: Same purpose but uses aiofiles and asyncio for parallel reads.
            - _parse_sync: Reads and parses in a single step per file, unlike this method which separates the two phases.

        Main consumers:
            - flush(): Called when batch threshold is met and aiofiles is not available.

        State and side effects:
            Reads files from disk. No mutation of instance state (staticmethod). Logs warnings on OSError.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """

        def _read_one(p: Path) -> tuple[Path, bytes] | None:
            """
            Read a single file from disk using Path.read_bytes().

            Responsibility:
                Reads a single file from disk using Path.read_bytes(). Returns a (Path, bytes) tuple on success, or None
                if OSError occurs (file missing, permission denied, etc.). This inner function exists to encapsulate
                per-file error handling within the list comprehension of _read_files_sync.

            Reason for existence:
                Defined as an inner function to keep the error-handling logic close to the iteration site and to avoid
                polluting the module namespace with a single-purpose helper. The None return on error allows the outer
                list comprehension to filter out failed reads cleanly.

            Delegates:
                - Path.read_bytes(): Reads the file content.

            Cohesion:
                Single-purpose: read one file, return content or None. No branching beyond error handling.

            Separation:
                - _parse_sync._parse_one: Reads AND parses in one step. _read_one only reads.
                - _read_files_async._read_all._read_one: Async equivalent using aiofiles.

            Main consumers:
                - _read_files_sync: Called in a list comprehension.

            State and side effects:
                Reads file from disk. No mutation. Logs warning on OSError.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
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
        Read all files in the given path list concurrently using aiofiles and asyncio.

        Responsibility:
            Reads all files in the given path list concurrently using aiofiles and asyncio. Creates an async task per
            file, runs them all via asyncio.gather, then filters results: successfully read files (returning bytes) are
            kept; files that raised OSError are logged as warnings and excluded. Uses asyncio.run() to execute the async
            read-all coroutine synchronously. This is the preferred file-reading strategy when aiofiles is installed, as
            it parallelizes I/O before CPU-bound parsing begins.

        Reason for existence:
            File I/O is often the bottleneck in batch parsing, especially for projects with many feature files on
            network or spinning-disk storage. Concurrent async reads can significantly reduce total I/O wait time
            compared to sequential reads. This method is the aiofiles-aware variant of _read_files_sync. It is a
            staticmethod because it needs no access to instance state — it purely transforms paths to bytes.

        Delegates:
            - _read_all (inner async coroutine): Orchestrates the concurrent reads via asyncio.gather.
            - _read_one (inner async coroutine): Opens a single file with aiofiles.open and reads its content.
            - asyncio.gather: Runs all _read_one tasks concurrently.
            - asyncio.run: Executes the async coroutine synchronously.

        Cohesion:
            The method is a synchronous wrapper around an async core. The async _read_all and _read_one coroutines are
            nested because they are only meaningful in this context. All logic serves "read all files concurrently."

        Separation:
            - _read_files_sync: Synchronous equivalent. Used when aiofiles is not available.
            - _parse_sync: Does not separate reading from parsing — the separation is the whole point of this method.

        Main consumers:
            - flush(): Called when batch threshold is met and aiofiles is available (import succeeds).

        State and side effects:
            Reads files from disk concurrently. Executes asyncio event loop via asyncio.run(). No mutation of instance
            state (staticmethod). Logs warnings on OSError.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """

        async def _read_all() -> list[tuple[Path, bytes | Exception]]:
            """
            Orchestrates concurrent file reading by creating an asyncio task (_read_one) for each path, running all tasks in para.

            Responsibility:
                Orchestrates concurrent file reading by creating an asyncio task (_read_one) for each path, running all
                tasks in parallel via asyncio.gather, and returning a list of (Path, bytes | Exception) tuples. The
                Exception union type allows OSError from individual reads to be collected and filtered by the caller
                rather than failing the entire batch.

            Reason for existence:
                asyncio.gather is the standard mechanism for running multiple coroutines concurrently. This coroutine
                wraps the gather call so that the caller (_read_files_async) can use asyncio.run() to execute it
                synchronously. It exists as a nested async def because asyncio.gather must be awaited inside a
                coroutine.

            Delegates:
                - _read_one (inner async coroutine): Performs the actual file read for a single path.
                - asyncio.gather: Runs all _read_one tasks concurrently.

            Cohesion:
                Single-purpose orchestrator: create tasks, gather results. All logic serves "run all reads in parallel."

            Separation:
                - _read_files_sync._read_one: Synchronous equivalent for single files.

            Main consumers:
                - _read_files_async: Called via asyncio.run().

            State and side effects:
                Launches concurrent file reads. No mutation of instance state. The asyncio event loop manages task scheduling.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
            """

            async def _read_one(p: Path) -> tuple[Path, bytes | Exception]:
                """
                Open a single file asynchronously using aiofiles.open in binary read mode, reads its entire content, and returns a (.

                Responsibility:
                    Opens a single file asynchronously using aiofiles.open in binary read mode, reads its entire
                    content, and returns a (Path, bytes) tuple. If OSError occurs (file missing, permission denied),
                    returns (Path, OSError) so the caller can decide whether to log and skip. This is the atomic unit of
                    async file reading in the batch pipeline.

                Reason for existence:
                    Defined as an inner async coroutine to be used with asyncio.gather. The Exception-in-return-value
                    pattern (instead of letting the exception propagate) allows all concurrent reads to complete even if
                    some fail — gather() would cancel remaining tasks on first exception otherwise. This design lets the
                    caller collect both successes and failures and decide how to handle each.

                Delegates:
                    - aiofiles.open: Asynchronously opens the file.
                    - f.read(): Asynchronously reads the full file content.

                Cohesion:
                    Single-purpose: read one file asynchronously. Error handling is part of the read concern.

                Separation:
                    - _read_files_sync._read_one: Synchronous equivalent. Uses Path.read_bytes() instead of aiofiles.

                Main consumers:
                    - _read_all: Called via asyncio.gather for each path.

                State and side effects:
                    Reads file from disk asynchronously. No mutation. The async context manager (aiofiles.open) manages
                    the file descriptor lifecycle.

                Architecture score:
                    #arch-eval:reason_for_existence=3
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=5
                    #arch-eval:cohesion=5
                    #arch-eval:separation=5
                    #arch-eval:consumer_clarity=3
                    #arch-eval:state_invariants=5
                    #arch-eval:entity_fullness=2
                    #arch-eval:locational_stability=5
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
        Pars pre-read file contents using multiprocessing for parallelism.

        Responsibility:
            Parses pre-read file contents using multiprocessing for parallelism. Attempts to create a spawn-context
            multiprocessing Pool and use pool.starmap to distribute _parse_feature_file calls across workers. If
            multiprocessing fails (OSError, RuntimeError, ValueError — common in constrained environments like CI
            containers or when pickling fails), falls back to synchronous sequential parsing via the nested _parse_safe
            function. All successfully parsed (path, GherkinDocument) tuples are stored in self._cache.

        Reason for existence:
            CPU-bound Gherkin parsing benefits from parallelism when there are many files. Using starmap with pre-read
            bytes avoids the need for workers to access the filesystem. The spawn context is used explicitly (instead of
            fork) because pytest may have threads or locks held that are unsafe to fork. The fallback to synchronous
            parsing ensures robustness in environments where multiprocessing is unavailable.

        Delegates:
            - multiprocessing.get_context("spawn"): Creates a spawn-context multiprocessing context.
            - Pool.starmap: Distributes _parse_feature_file calls across worker processes.
            - _parse_safe (inner function): Synchronous fallback parser used when multiprocessing fails.
            - _parse_feature_file: The actual parsing worker function.

        Cohesion:
            The method is a try/except around the multiprocessing path with a nested fallback function. Both paths serve
            the same purpose: parse all contents and cache results.

        Separation:
            - _parse_sync: Reads files itself and parses sequentially. _parse_and_cache receives pre-read bytes and
            parses in parallel (or falls back to sequential).

        Main consumers:
            - flush(): Called for large batches after file reading.

        State and side effects:
            Populates self._cache. Creates and destroys a multiprocessing Pool (may spawn child processes). Logs
            warnings if multiprocessing fails. The nested _parse_safe is a closure over nothing relevant.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
                Fall back to synchronous parser for a single (path, bytes) pair.

                Responsibility:
                    Synchronous fallback parser for a single (path, bytes) pair. Calls _parse_feature_file and returns
                    the (path, GherkinDocument) tuple on success. On any exception (OSError, RuntimeError, ValueError),
                    logs the full exception and returns None. Used only when the multiprocessing Pool fails to
                    initialize, allowing the batch to complete sequentially instead of aborting.

                Reason for existence:
                    When multiprocessing is unavailable (e.g., restricted CI environments, or when the data cannot be
                    pickled), the batch parser must still produce results. This inner function provides that fallback,
                    wrapping _parse_feature_file in an error-tolerant envelope so that one bad file does not fail the
                    entire batch.

                Delegates:
                    - _parse_feature_file: The actual parsing worker.

                Cohesion:
                    Single-purpose: parse one file tolerantly. The error handling is the primary reason this function
                    exists separately from _parse_feature_file.

                Separation:
                    - _parse_sync._parse_one: Similar error-tolerant parse-one function but reads the file itself rather
                    than receiving pre-read bytes.
                    - _parse_feature_file: The raw parsing function that may raise. _parse_safe wraps it.

                Main consumers:
                    - _parse_and_cache: Called in a list comprehension when multiprocessing fails.

                State and side effects:
                    Calls _parse_feature_file (may import Go parser). Logs exceptions on failure. Returns None to signal
                    failure to the caller's list comprehension filter.

                Architecture score:
                    #arch-eval:reason_for_existence=3
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=5
                    #arch-eval:cohesion=5
                    #arch-eval:separation=5
                    #arch-eval:consumer_clarity=3
                    #arch-eval:state_invariants=5
                    #arch-eval:entity_fullness=2
                    #arch-eval:locational_stability=5
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
        Retrieve a previously parsed GherkinDocument from the internal _cache by its feature file Path.

        Responsibility:
            Retrieves a previously parsed GherkinDocument from the internal _cache by its feature file Path. Must only
            be called after flush() has been called (i.e., _flushed is True). Raises RuntimeError if called before
            flush. Returns None if the path was not successfully parsed (e.g., due to file read or parse errors during
            flush).

        Reason for existence:
            After the batch is flushed, consumers need access to the parsed GherkinDocuments. This method provides
            controlled access with a guard against premature retrieval — the cached documents are only meaningful after
            parsing is complete. The RuntimeError guard catches programming errors where a consumer tries to read
            documents before the batch has been processed.

        Delegates:
            - dict.get: Retrieves the document from _cache by path key.

        Cohesion:
            Single-purpose accessor with a precondition guard. Cohesive with the batch lifecycle.

        Separation:
            - register(): Populates _cache (either during flush or for late registrations). get() reads it.
            - flush(): Transitions _flushed to True, enabling get() to succeed.

        Main consumers:
            - Code that needs parsed GherkinDocuments after the collection phase. Not currently consumed within the
            collector module itself (FeatureFileModule does not call get()).

        State and side effects:
            None. Pure read accessor with precondition check. No I/O, no mutation.

        Failure semantics:
            Raises RuntimeError with _GET_BEFORE_FLUSH_MSG if called before _flushed is True. Returns None for paths not
            found in _cache.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if not self._flushed:
            raise RuntimeError(_GET_BEFORE_FLUSH_MSG)
        return self._cache.get(path)


def _parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]:
    """
    Pars a single feature file's raw bytes into a (Path, GherkinDocument) tuple.

    Responsibility:
        Parses a single feature file's raw bytes into a (Path, GherkinDocument) tuple. Decodes bytes to UTF-8 text,
        constructs a file:// URI from the path, and delegates to the Go ctypes parser (via
        pytest_bdd._gherkin_go._get_parser) for high-performance parsing. If the Go parser raises GherkinParseError, the
        error's source URIs are patched to reference the actual file path before re-raising. If the Go parser is
        unavailable (GherkinGoNotAvailable, OSError, RuntimeError), falls back to the Python parser (_parse_python). For
        markdown feature files (.feature.md), additionally parses with the Python parser and compares results; if the
        parsers diverge, the Python result is preferred and a warning is logged. Converts the final raw dict to a typed
        GherkinDocument via message_converter.from_dict.

    Reason for existence:
        This is the primary parsing worker function used by all batch parsing paths (_parse_sync, _parse_and_cache,
        register() late registration). It encapsulates the Go-vs-Python parser selection, the markdown divergence check,
        and the dict-to-GherkinDocument conversion. It is a module-level function (not a FeatureBatchParser method)
        because it is called from multiprocessing worker processes via pool.starmap and must be picklable — methods of
        an attrs instance are not reliably picklable.

    Delegates:
        - pytest_bdd._gherkin_go._get_parser: Returns the Go ctypes parser callable.
        - pytest_bdd._gherkin_go._types.GherkinParseError: Go parser error type caught and re-raised.
        - pytest_bdd._gherkin_go._types.GherkinGoNotAvailable: Sentinel for Go parser unavailability.
        - _parse_python: Python Gherkin parser fallback.
        - _documents_equivalent: Compares Go and Python parser outputs for markdown files.
        - _resolve_mimetype: Determines if the file is markdown based on extension.
        - pytest_bdd.model.message_converter.from_dict: Converts raw dict to GherkinDocument.

    Cohesion:
        The function is a linear pipeline: decode → resolve mimetype → try Go parser → patch errors || fallback to
        Python → optionally verify with Python for markdown → convert to GherkinDocument. Every step serves the single
        purpose of "produce a typed GherkinDocument from raw bytes."

    Separation:
        - pytest_bdd.parser.GherkinParser.parse: The synchronous parser class that includes error reporting via
        emit_parse_error. _parse_feature_file bypasses it for performance.
        - _parse_python: Only handles the Python parser path. _parse_feature_file adds Go parser and verification logic.

    Main consumers:
        - FeatureBatchParser._parse_sync: Called in a loop for each file.
        - FeatureBatchParser._parse_and_cache: Called via pool.starmap for parallel parsing.
        - FeatureBatchParser.register: Called for late-registration parsing.

    State and side effects:
        Imports pytest_bdd._gherkin_go dynamically (imports occur inside the function body). Decodes bytes to string.
        Calls Go parser (via ctypes, potential FFI side effects). May log warnings. The returned GherkinDocument is
        constructed via message_converter.from_dict which performs validation.

    Failure semantics:
        GherkinParseError from the Go parser is re-raised after patching source URIs with the actual file path.
        GherkinGoNotAvailable, OSError, and RuntimeError from the Go parser trigger fallback to _parse_python. If
        _parse_python also fails, the CompositeParserException propagates to the caller.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
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
    Pars Gherkin text using the pure-Python CucumberIOBaseParser with a default AstBuilder (no custom ID generator).

    Responsibility:
        Parses Gherkin text using the pure-Python CucumberIOBaseParser with a default AstBuilder (no custom ID
        generator). Returns the raw dictionary produced by gherkin.parser.Parser.parse(). This is the fallback parser
        used when the Go ctypes parser is unavailable or when verifying markdown parse results against the Go parser
        output. The parser instance is explicitly deleted after use to free memory.

    Reason for existence:
        The Python parser serves as both a fallback (when Go is unavailable) and a verification tool (comparing Go
        output for markdown files). It is a standalone module-level function (not a FeatureBatchParser method) because
        _parse_feature_file is called from multiprocessing workers and must be picklable — this function is also called
        from those workers.

    Delegates:
        - CucumberIOBaseParser: The python gherkin library's parser class.
        - AstBuilder: The default AST builder with sequential ID generation.
        - parser.parse(): Produces the raw dict from Gherkin text.

    Cohesion:
        Single-purpose: parse text to dict. The explicit `del parser` is a memory optimization, not a separate concern.

    Separation:
        - pytest_bdd.parser.GherkinParser.parse: Uses the same underlying CucumberIOBaseParser but adds error reporting,
        URI annotation, normalization, and GherkinDocument construction. This function is intentionally minimal to avoid
        coupling batch parsing to the full parser pipeline.
        - _parse_feature_file: Calls _parse_python as a fallback and wraps the result in message_converter.from_dict.

    Main consumers:
        - _parse_feature_file: Called when Go parser is unavailable or for markdown verification.

    State and side effects:
        Creates and destroys a CucumberIOBaseParser instance. No file I/O, no logging, no stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    parser = CucumberIOBaseParser(ast_builder=AstBuilder())
    raw_dict = parser.parse(text)
    del parser
    return cast("dict[str, object]", raw_dict)


def _documents_equivalent(go_doc: dict[str, object], python_doc: dict[str, object]) -> bool:
    """
    Compare two Gherkin document dicts (one from Go parser, one from Python parser) for structural equivalence, ignoring.

    Responsibility:
        Compares two Gherkin document dicts (one from Go parser, one from Python parser) for structural equivalence,
        ignoring fields that are expected to differ between parser implementations. Normalizes both documents by
        recursively stripping None values and the "id" key from all nested dicts, then performs a standard dict equality
        comparison. Used exclusively for markdown feature files to detect parser divergence.

    Reason for existence:
        The Go and Python parsers may produce slightly different ASTs for the same Gherkin input — different ID
        generation, different handling of optional fields, different whitespace in descriptions. This function provides
        a tolerant comparison that ignores these expected differences. If the normalized documents differ, it indicates
        a genuine parsing divergence that needs investigation.

    Delegates:
        - _normalize (inner function): Recursively strips None values and "id" keys from a nested dict structure,
        returning the normalized structure for comparison.

    Cohesion:
        The function has a single purpose: "are these two parse results functionally equivalent?" The normalization is
        an implementation detail of the comparison, not a separate concern.

    Separation:
        - _parse_feature_file: Calls _documents_equivalent to decide whether to use the Go or Python result for markdown files.

    Main consumers:
        - _parse_feature_file: Called for markdown feature files to verify Go parser output.

    State and side effects:
        None, keeps no persistent state. Pure function with no I/O, no logging, no stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    def _normalize(doc: dict[str, object]) -> Any:  # noqa: ANN401  # returns dynamically structured BDD document dictionaries
        """
        Recursively normalizes a Gherkin document dict for comparison by stripping all None values and keys named "id" from e.

        Responsibility:
            Recursively normalizes a Gherkin document dict for comparison by stripping all None values and keys named
            "id" from every nested dict. Non-dict values are returned unchanged (recursion base case). For dicts,
            rebuilds the dict with only non-None, non-"id" values, recursively normalizing each value. This ensures that
            parser-specific metadata (like internal IDs) and missing optional fields don't cause false mismatches during
            equivalence checks.

        Reason for existence:
            The Go and Python Gherkin parsers assign different internal IDs to AST nodes and handle optional fields
            differently. A direct dict comparison would report false differences. This normalization function removes
            those parser-specific artifacts before comparison. It is defined inside _documents_equivalent because it is
            only meaningful in the context of comparing documents.

        Delegates:
            - Recursive calls to self for nested dicts and list values.

        Cohesion:
            Single-purpose: strip None/"id" recursively. The entire function body is one dict comprehension with a recursion guard.

        Separation:
            - pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload._normalize: Similar normalization but for
            a different purpose (filling in missing location fields, not stripping for comparison).

        Main consumers:
            - _documents_equivalent: Called to normalize both documents before comparison.

        State and side effects:
            None. Pure recursive function. Creates new dicts, does not mutate input.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if not isinstance(doc, dict):
            return doc  # recursion base case
        return {k: _normalize(v) for k, v in doc.items() if v is not None and k != "id"}  # type: ignore[arg-type]  # recursive values of varying types

    return cast("bool", _normalize(go_doc) == _normalize(python_doc))


def _resolve_mimetype(path: Path) -> str:
    """
    Determine the Gherkin mimetype for a feature file based on its file extension.

    Responsibility:
        Determines the Gherkin mimetype for a feature file based on its file extension. Returns
        "text/x.cucumber.gherkin+markdown" for files ending with ".feature.md" (case-insensitive), and
        "text/x.cucumber.gherkin+plain" for all other files. This classification drives the parser selection and
        markdown verification logic in _parse_feature_file.

    Reason for existence:
        The mimetype determines whether the Gherkin parser should expect plain Gherkin or Gherkin-in-Markdown syntax.
        This function centralizes the extension-to-mimetype mapping so that multiple call sites (_parse_feature_file and
        potentially others) don't duplicate the suffix check. It is a module-level function because it is a pure utility
        with no state dependencies.

    Delegates:
        - path.name.lower(): Normalizes the filename for case-insensitive comparison.
        - str.endswith(): Checks for the ".feature.md" suffix.

    Cohesion:
        Single-purpose: map file extension to mimetype string. One if/else, no side effects.

    Separation:
        - pytest_bdd.mimetype: Defines the Mimetype enum with constants for these and other mimetypes. _resolve_mimetype
        returns raw strings that correspond to Mimetype enum values but does not import the enum.

    Main consumers:
        - _parse_feature_file: Called to determine if a feature file is markdown, which triggers the Go-Python
        verification check.

    State and side effects:
        None. Pure function.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    name = path.name.lower()
    if name.endswith(".feature.md"):
        return "text/x.cucumber.gherkin+markdown"
    return "text/x.cucumber.gherkin+plain"
