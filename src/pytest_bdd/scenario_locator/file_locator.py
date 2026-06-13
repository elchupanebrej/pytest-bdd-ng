"""
Owns the file-system-based scenario location infrastructure: FileScenarioLocatorDefaults (providing default encoding .

Responsibility:
    Owns the file-system-based scenario location infrastructure: FileScenarioLocatorDefaults (providing default encoding
    "utf-8" and empty parse Args), and FileScenarioLocator (extending ScenarioLocatorFilterMixin to implement
    resolve_features() that discovers feature files from disk using configurable features_base_dir, feature_paths (paths
    or globs), and optional encoding/mimetype/parser_type overrides). Implements _resolved_feature_paths (property that
    globs path patterns into resolved Path objects), _try_get_cached_feature (checks FeatureBatchParser cache for pre-
    parsed GherkinDocuments), and the full resolve_features pipeline: resolve paths → check cache → detect mimetype via
    hook → select parser via hook → parse with error handling (PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS gate) →
    yield (ParsedFeature, Source) tuples.

Reason for existence:
    File-system-based feature loading is the primary (and most common) way users provide BDD feature files to pytest-
    bdd. This module handles the full pipeline from path specification (including glob patterns like
    "features/**/*.feature") through caching, mimetype detection, parser selection, parsing, and error handling. Without
    this module, users would need to manually register each feature file, losing the convenience of directory-based
    discovery and glob pattern matching. The caching integration with FeatureBatchParser significantly improves
    performance for large feature sets by avoiding re-parsing on every test collection.

Delegates:
    - FeatureBatchParser (from pytest_bdd.collector_batch): Caches parsed GherkinDocuments for performance — checked via
    _try_get_cached_feature before re-parsing.
    - pytest_bdd.compatibility.parser.ParsedFeature and ParserProtocol: The parsed feature data type and parser interface.
    - pytest_bdd.compatibility.path.relpath: Computes relative paths for URI generation.
    - pytest_bdd.compatibility.pathlib.GlobError: Exception type for invalid glob patterns, caught in
    _resolved_feature_paths for graceful fallback.
    - pytest_bdd.scenario.Args: Arguments passed to the parser for customization.
    - pytest_bdd.types.exception.FeatureParseError: Exception caught during parsing, handled by
    CONTINUE_ON_COLLECTION_ERRORS gate.
    - ScenarioLocatorHookProtocol: Hook interface for mimetype detection and parser selection.
    - PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS: Configuration option controlling error-suppression behavior.

Cohesion:
    All entities in this module serve file-system-based feature resolution. FileScenarioLocatorDefaults provides default
    configuration values, FileScenarioLocator implements the resolution pipeline, _resolved_feature_paths handles
    path/glob resolution, and _try_get_cached_feature handles batch parser cache integration. Every method is a stage in
    the "discover files → parse files → yield results" pipeline.

Separation:
    - pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator: Kept separate because UrlScenarioLocator resolves
    features from URLs (HTTP/networking) while FileScenarioLocator resolves from local files — completely different
    feature sources, though they share the base mixin.
    - pytest_bdd.collector_batch.FeatureBatchParser: Kept separate because the batch parser owns cached document
    storage, while FileScenarioLocator consumes the cache — storage vs consumer.
    - pytest_bdd.parser: Kept separate because parser owns the Gherkin parsing algorithms, while file_locator owns file
    discovery and parser invocation — discovery vs parsing.

Main consumers:
    - pytest_bdd.collector: Uses FileScenarioLocator during test collection to discover feature files in the project.
    - pytest_bdd.scenario.scenarios(): Creates FileScenarioLocator instances when the scenarios() function is called
    with directory or file paths.
    - pytest_bdd.scenario_locator.__init__: Re-exports FileScenarioLocator and FileScenarioLocatorDefaults through the
    public API.

State and side effects:
    FileScenarioLocator stores configuration (features_base_dir, feature_paths, encoding, mimetype, parser_type,
    parse_args) via attrs — immutable after construction. _resolved_feature_paths reads from disk (glob) — a read-only
    filesystem operation. _try_get_cached_feature reads from FeatureBatchParser cache. resolve_features reads files from
    disk and may raise FeatureParseError.

Invariants:
    - features_base_dir must be a valid directory Path — it serves as the root for all relative feature_paths glob
    resolution.
    - _try_get_cached_feature must check batch_parser.is_flushed before using cached documents — unflushed parsers have
    incomplete caches.
    - CONTINUE_ON_COLLECTION_ERRORS gate must suppress FeatureParseError and continue to the next file, not re-raise —
    this is the "robustness over strictness" design choice.

Failure semantics:
    - Raises FeatureParseError when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is False — this halts collection
    immediately.
    - GlobError in _resolved_feature_paths triggers fallback to "**/*" glob rather than raising an error.
    - Returns early (break) when parser_type is None — no parser registered for the detected format.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import os
from enum import Enum
from operator import methodcaller
from pathlib import Path
from typing import TYPE_CHECKING, cast

from attrs import define, field
from cucumber_messages import Source

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pathlib import GlobError
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.util.other import IdGenerator

from .base import ScenarioLocatorFilterMixin

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.mimetype import Mimetype
    from pytest_bdd.types.protocol import HasPytestStash


class FileScenarioLocatorDefaults:
    """
    Owns the default configuration values for file-based scenario location: encoding() returns "utf-8" as the default fil.

    Responsibility:
        Owns the default configuration values for file-based scenario location: encoding() returns "utf-8" as the
        default file encoding for reading feature files, and parse_args() returns Args((), {}) — empty positional and
        keyword arguments passed to the parser. These defaults are used by FileScenarioLocator when the corresponding
        configuration attributes (encoding, parse_args) are not explicitly set, providing sensible defaults without
        requiring users to specify them.

    Reason for existence:
        Centralizing defaults in a dedicated class (rather than using module-level constants or inline defaults) makes
        the default values discoverable and overridable. If users want to change the default encoding for their project,
        they can subclass FileScenarioLocator and set Defaults to their custom defaults class. The pattern matches the
        "convention over configuration" principle — most users don't need to change these values, but power users can.

    Delegates:
        - None. Returns hardcoded string and Args values.

    Cohesion:
        Both static methods provide default configuration values — they are "what configuration value should be used if
        none is specified?" answers for the file locator. They belong together because they form the complete default
        surface for file-based location.

    Separation:
        - FileScenarioLocator: Kept separate because FileScenarioLocator owns the resolution pipeline and configuration
        storage, while FileScenarioLocatorDefaults owns the default values — implementation vs defaults.
        - UrlScenarioLocator: Kept separate because URL-based location has different defaults (no equivalent defaults
        class), since URL locators don't use file encoding or parser args in the same way.

    Main consumers:
        - FileScenarioLocator: Uses FileScenarioLocatorDefaults via the Defaults class attribute — encoding and
        parse_args fall back to these values when not explicitly configured.

    State and side effects:
        None. Static methods returning constant values.

    Invariants:
        - encoding() must return a valid Python codec name that can be passed to open() and Path.read_text().
        - parse_args() must return an Args with no required arguments — empty defaults should not break parser invocation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    @staticmethod
    def encoding() -> str:
        """
        Return "utf-8" as the default file encoding for reading feature files.

        Responsibility:
            Returns "utf-8" as the default file encoding for reading feature files. This encoding is used when
            FileScenarioLocator.encoding is not explicitly set, ensuring feature files are read with a consistent,
            Unicode-compatible encoding that handles the full range of Gherkin syntax including non-ASCII characters in
            step text.

        Reason for existence:
            UTF-8 is the universal default for text files in modern Python development and is the encoding expected by
            the Gherkin specification. Providing this default means users don't need to specify encoding unless they
            have legacy files in other encodings (e.g., Latin-1). The static method pattern allows overrides via
            subclassing the Defaults class.

        Delegates:
            - None. Returns a constant string.

        Cohesion:
            Single, obvious purpose: return the default encoding.

        Separation:
            - parse_args: Kept separate because encoding answers "how to read the file" while parse_args answers "what
            arguments to pass to the parser" — reading vs parsing configuration.

        Main consumers:
            - FileScenarioLocator.resolve_features: Falls back to this when self.encoding is None.

        State and side effects:
            None. Static method returning constant.

        Architecture score:
            #arch-eval:reason_for_existence=2
            #arch-eval:owned_responsibility=2
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=4
        """
        return "utf-8"

    @staticmethod
    def parse_args() -> Args:
        """
        Return Args((), {}) — an empty Args object with no positional arguments and no keyword arguments — as the default pa.

        Responsibility:
            Returns Args((), {}) — an empty Args object with no positional arguments and no keyword arguments — as the
            default parser arguments. When FileScenarioLocator.parse_args is not explicitly set, these empty defaults
            are passed to the parser, meaning the parser is invoked with only the required positional arguments (config,
            path, uri, encoding) and no additional configuration.

        Reason for existence:
            Parser classes may accept optional configuration arguments (e.g., language, strict mode), but the default is
            "no extra configuration." Providing an empty Args default means users don't need to configure parser args
            unless they need custom behavior. The Args type is a simple named tuple variant that stores (*args,
            **kwargs) for deferred unpacking.

        Delegates:
            - None. Returns a constant Args instance.

        Cohesion:
            Single purpose: return default parser arguments.

        Separation:
            - encoding: Kept separate because these answer different configuration questions — reading vs parsing configuration.

        Main consumers:
            - FileScenarioLocator.resolve_features: Falls back to this when self.parse_args is None.

        State and side effects:
            None. Static method returning constant.

        Architecture score:
            #arch-eval:reason_for_existence=2
            #arch-eval:owned_responsibility=2
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=4
        """
        return Args((), {})


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Implements file-system-based feature resolution by extending ScenarioLocatorFilterMixin with disk-specific discovery .

    Responsibility:
        Implements file-system-based feature resolution by extending ScenarioLocatorFilterMixin with disk-specific
        discovery logic. Configured with features_base_dir (root directory for path resolution), feature_paths (list of
        paths or glob patterns), and optional overrides for encoding, mimetype, parser_type, and parse_args. The
        resolve_features() pipeline: resolves paths/globs into concrete Path objects via _resolved_feature_paths, checks
        the FeatureBatchParser cache via _try_get_cached_feature for pre-parsed documents, detects mimetype via
        pytest_bdd_get_mimetype hook (or explicit configuration), selects parser via pytest_bdd_get_parser hook (or
        explicit configuration), parses feature files with error handling gated by
        PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS, and yields (ParsedFeature, Source) tuples with "file:" URIs.

    Reason for existence:
        This is the primary way pytest-bdd discovers feature files — from local directories and globs on the filesystem.
        It integrates the batch parser cache for performance, the hook-based plugin system for format extensibility, and
        the pytest configuration system for error handling policy. Without this class, every user would need to manually
        register each feature file, losing the power of directory-based discovery and automatic format detection.

    Delegates:
        - _resolved_feature_paths: Resolves path specifications into concrete Path objects with glob support.
        - _try_get_cached_feature: Checks batch parser cache for pre-parsed documents.
        - config.hook.pytest_bdd_get_mimetype / pytest_bdd_get_parser: Hook-based format detection and parser selection.
        - ParserProtocol.parse: Parses feature files from disk into ParsedFeature objects.
        - FeatureBatchParser.find_in_stash: Locates the batch parser in pytest stash.
        - PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS: Configuration gate for error suppression.
        - ScenarioLocatorFilterMixin: Inherits the resolve() pipeline and filter infrastructure.

    Cohesion:
        Every attribute and method serves file-system-based feature resolution: features_base_dir and feature_paths
        define WHERE to look, encoding/mimetype/parser_type define HOW to read, _resolved_feature_paths resolves paths,
        _try_get_cached_feature checks cache, resolve_features orchestrates the full pipeline. The class is a complete,
        self-contained feature resolution engine.

    Separation:
        - UrlScenarioLocator: Kept separate because UrlScenarioLocator handles URL/network-based resolution with HTTP
        fetching, temp file management, and async I/O, while FileScenarioLocator handles local files with disk I/O and
        glob patterns — different I/O models and configuration surfaces.
        - FeatureBatchParser: Kept separate because the batch parser is a caching layer that FileScenarioLocator
        consumes — cache vs consumer.

    Main consumers:
        - pytest_bdd.collector: Uses FileScenarioLocator during test collection.
        - pytest_bdd.scenario.scenarios(): Creates FileScenarioLocator when paths point to local files/directories.
        - pytest_bdd.scenario_locator.__init__: Re-exported through public API.

    State and side effects:
        Stores configuration (attrs fields, immutable after construction). resolve_features reads from disk (file I/O),
        reads from batch parser cache, invokes hooks (plugin I/O). _try_get_cached_feature may trigger deferred imports
        (returns.maybe).

    Invariants:
        - URI format must be "file:" + relative path with forward slashes (as_posix()) — this is the standard Gherkin
        source URI format.
        - features_base_dir must be a valid directory Path accessible from the current working directory.
        - CONTINUE_ON_COLLECTION_ERRORS must suppress FeatureParseError and continue iteration — the loop must not break
        on parse errors when this option is enabled.

    Failure semantics:
        Raises FeatureParseError when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is disabled — halts collection.
        Returns early when parser_type is None — no parser registered for the detected format means no scenarios can be
        extracted.
        Globs that don't match any files produce an empty iterator — no error, just no features found.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    Defaults = FileScenarioLocatorDefaults
    features_base_dir: Path = field()
    feature_paths: list[str | Path] = field(factory=list)
    encoding: str | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    @staticmethod
    def _try_get_cached_feature(
        config: Config | HasPytestStash,
        feature_path: Path,
        uri: str,
        encoding: str,
        media_type: str | None,
    ) -> tuple[ParsedFeature, Source] | None:
        """
        Attempt to retrieve a pre-parsed GherkinDocument from the FeatureBatchParser cache: locates the batch parser in conf.

        Responsibility:
            Attempts to retrieve a pre-parsed GherkinDocument from the FeatureBatchParser cache: locates the batch
            parser in config.stash, checks if it's flushed (cache is complete), looks up the feature_path in the cache,
            and if found, constructs a ParsedFeature + Source tuple from the cached document without re-reading or re-
            parsing the file from disk. Returns None if the cache is unavailable, unflushed, or lacks the requested
            document. This is the primary performance optimization for large feature sets — avoiding repeated file I/O
            and Gherkin parsing.

        Reason for existence:
            During test collection, the same feature file may be discovered multiple times (e.g., by different test
            modules). Without caching, each discovery would re-read and re-parse the file, which is wasteful. The batch
            parser cache stores pre-parsed documents indexed by file path, enabling O(1) cache hits. The is_flushed
            check is critical: an unflushed cache is incomplete (batch parsing still in progress), and using it would
            produce incorrect results. The deferred import of returns.maybe.Nothing avoids circular dependency issues.

        Delegates:
            - FeatureBatchParser.find_in_stash(config.stash): Locates the batch parser in pytest stash, returns Maybe type.
            - batch_parser.get(feature_path): Looks up a GherkinDocument by Path key.
            - feature_path.read_text(encoding): Reads raw file content for the Source object when cache hit.
            - returns.maybe.Nothing: Provides type-safe None value for Maybe.return_or(None).

        Cohesion:
            The method performs one operation: check cache → if hit, construct result → else None. Every branch serves
            this cache lookup pipeline.

        Separation:
            - resolve_features: Kept separate because resolve_features orchestrates the full pipeline (cache check →
            hook detection → parsing), while _try_get_cached_feature handles only the cache check stage.

        Main consumers:
            - resolve_features: Called at the start of processing each feature path to check cache before re-parsing.

        State and side effects:
            Reads from FeatureBatchParser cache and disk (feature_path.read_text). Does not modify cache or filesystem.
            The deferred import of returns.maybe triggers module loading on first call.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        from returns.maybe import Nothing

        batch_parser = FeatureBatchParser.find_in_stash(config.stash).value_or(None)
        if batch_parser is None or not batch_parser.is_flushed:
            return Nothing.value_or(None)
        cached_doc = batch_parser.get(feature_path)
        if cached_doc is None:
            return Nothing.value_or(None)
        cached_doc.uri = uri  # mypy union attribute narrowing
        raw_data = feature_path.read_text(encoding=encoding)
        parsed = ParsedFeature(
            gherkin_document=cached_doc,
            filename=str(feature_path.as_posix()),
            raw_data=raw_data,
        )
        source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
        return parsed, Source(uri=uri, data=parsed.raw_data, media_type=source_media_type)

    @property
    def _resolved_feature_paths(self) -> Iterator[Path]:
        """
        Property that resolves the configured feature_paths into concrete Path objects: for Path entries, checks if the path .

        Responsibility:
            Property that resolves the configured feature_paths into concrete Path objects: for Path entries, checks if
            the path is a directory (globs all files recursively via "**/*" pattern) or a file (yields directly). For
            string entries, attempts glob resolution against features_base_dir using glob("**/*") for "**/*" patterns
            that match Gherkin suffixes, with a fallback to full recursive glob on GlobError. Results are filtered to
            only include files (isfile check), sorted for deterministic ordering, and deduplicated (resolved in
            resolve_features). This is the entry point for feature file discovery — it converts user-specified path
            patterns into the concrete file paths that will be parsed.

        Reason for existence:
            Users specify feature files as a mix of Path objects, string paths, and glob patterns (e.g.,
            "features/**/*.feature"). This property resolves all these specifications into a unified iterator of Path
            objects, handling the complexity of glob expansion, directory traversal, and error recovery. Without this
            property, resolve_features would need to inline all this path resolution logic, significantly increasing its
            complexity.

        Delegates:
            - Path.is_dir() / Path.is_file(): Checks whether a resolved path is a directory or file.
            - Path.glob(): Expands glob patterns against the features_base_dir.
            - sorted() + filter(methodcaller("is_file")): Ensures deterministic ordering and file-only results.
            - os.fspath(): Converts string paths to OS-native format for glob.

        Cohesion:
        The property performs one operation: resolve path specifications → concrete Path objects. The if/else branching
        handles the different input types (Path vs str, dir vs file), all serving the same resolution purpose.

        Separation:
            - resolve_features: Kept separate because resolve_features orchestrates the full pipeline (paths → cache →
            hooks → parse), while _resolved_feature_paths handles only the path resolution stage — discovery vs full
            pipeline.
            - _try_get_cached_feature: Kept separate because that method handles cache lookup, a later stage in the pipeline.

        Main consumers:
            - resolve_features: Iterates over the resolved paths to check cache and parse each file.

        State and side effects:
            Reads from disk (Path.is_dir, Path.is_file, Path.glob) — filesystem traversal with no modification. Results
            are generated lazily via yield.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = self.features_base_dir / feature_pathlike
                if feature_path.is_dir():
                    yield from sorted(filter(methodcaller("is_file"), feature_path.glob("**/*")))
                else:
                    yield feature_path
            else:
                try:
                    yield from sorted(
                        filter(
                            methodcaller("is_file"),
                            self.features_base_dir.glob(os.fspath(feature_pathlike)),
                        ),
                    )
                except GlobError:
                    yield from sorted(filter(methodcaller("is_file"), self.features_base_dir.glob("**/*")))

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Implement the feature discovery and parsing pipeline for file-system-based sources: iterates over resolved feature p.

        Responsibility:
            Implements the feature discovery and parsing pipeline for file-system-based sources: iterates over resolved
            feature paths (deduplicating by path string key), for each path detects the media type (via self.mimetype or
            hook), selects the parser (via self.parser_type or hook), checks the batch parser cache for pre-parsed
            documents (_try_get_cached_feature), and if not cached, instantiates the parser with an IdGenerator from
            stash, parses the file with encoding and parse_args, and handles FeatureParseError using the
            CONTINUE_ON_COLLECTION_ERRORS pytest option gate. Yields (ParsedFeature, Source) tuples with "file:" URIs
            using relative paths from features_base_dir.

        Reason for existence:
            This is the main resolution loop for file-based feature loading. It orchestrates all the sub-stages: path
            resolution → deduplication → mimetype detection → parser selection → cache check → parsing → error handling
            → result construction. Without this method, the locator would have no way to actually produce
            ParsedFeature+Source tuples from the configured paths.

        Delegates:
            - _resolved_feature_paths: Provides the iterator of resolved Path objects.
            - config.hook.pytest_bdd_get_mimetype / pytest_bdd_get_parser: Hook-based format/parser resolution.
            - _try_get_cached_feature: Checks batch parser cache.
            - ParserProtocol: Parses feature files into ParsedFeature objects.
            - IdGenerator.from_stash: Provides unique IDs for parsing.
            - relpath: Computes relative paths for URI construction.
            - PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS: Error suppression gate.

        Cohesion:
            The method is a clear pipeline: for each path → check cache → detect format → select parser → instantiate
            parser → parse → handle errors → yield result. Every line serves this pipeline orchestration.

        Separation:
            - resolve (from ScenarioLocatorFilterMixin): Kept separate because resolve orchestrates the full scenario
            resolution (features → binding → filtering → yielding triples), while resolve_features handles only the
            feature discovery stage — pipeline orchestrator vs stage implementation.
            - _resolved_feature_paths: Kept separate because that handles path specification resolution while this
            handles the parsing pipeline.

        Main consumers:
            - self.resolve() (inherited from ScenarioLocatorFilterMixin): Called as the first stage of the resolution pipeline.

        State and side effects:
            Reads from disk (file I/O), batch parser cache (read), hook invocations (plugin I/O). Instantiating parsers
            and parsing files may have side effects (e.g., registering documents with the Run model via the parser's
            id_generator). Does not modify filesystem.

        Failure semantics:
            Raises FeatureParseError when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is False — halts collection.
            Continues (skipping the file) when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is True — graceful degradation.
            Breaks (stops iteration) when parser_type is None — no parser registered for the format, no scenarios can be produced.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        from pytest_bdd.const import PytestConfigParam

        already_resolved_feature_paths: set[str] = set()

        for feature_path in self._resolved_feature_paths:
            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                continue

            already_resolved_feature_paths.add(feature_path_key)

            hook_handler = cast("Config", config).hook
            encoding = self.encoding or "utf-8"

            if self.mimetype is None:
                media_type = hook_handler.pytest_bdd_get_mimetype(config=config, path=feature_path)
            elif isinstance(self.mimetype, (Enum,)):
                media_type = self.mimetype.value
            else:
                media_type = self.mimetype

            if self.parser_type is None:
                parser_type = hook_handler.pytest_bdd_get_parser(
                    config=config,
                    mimetype=media_type,
                )
            else:
                parser_type = self.parser_type

            if parser_type is None:
                break

            parser = parser_type(id_generator=IdGenerator.from_stash(config.stash))
            rel_feature_path = Path(relpath(feature_path, self.features_base_dir))
            uri = "file:" + rel_feature_path.as_posix()

            # Check batch parser cache for pre-parsed document
            cached_result = self._try_get_cached_feature(config, feature_path, uri, encoding, media_type)
            if cached_result is not None:
                yield cached_result
                continue

            try:
                parse_args = self.parse_args or Args((), {})
                parsed = parser.parse(
                    config,
                    feature_path,
                    uri,
                    *parse_args.args,
                    **{"encoding": encoding, **parse_args.kwargs},
                )
            except FeatureParseError:
                if cast("Config", config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                    continue
                else:
                    raise
            source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
            yield parsed, Source(uri=uri, data=parsed.raw_data, media_type=source_media_type)
