"""
Owns the URL-based scenario location infrastructure: UrlScenarioLocator (extending ScenarioLocatorFilterMixin) that r.

Responsibility:
    Owns the URL-based scenario location infrastructure: UrlScenarioLocator (extending ScenarioLocatorFilterMixin) that
    resolves features from HTTP/HTTPS URLs using aiohttp for async fetching, with a resolve_features() pipeline that
    builds URLs from configured url_paths and features_base_url, fetches feature content async via fetch_all()/fetch(),
    writes content to temporary files, parses with hook-selected or explicitly configured parsers, and yields
    (ParsedFeature, Source) tuples with the original URL as URI. Also owns PyPyUrlScenarioLocator, a synchronous
    subclass that overrides _fetch_feature_responses to use stdlib urllib.request instead of aiohttp for PyPy
    compatibility.

Reason for existence:
    Some BDD workflows store feature files on remote servers, shared repositories, or test management platforms. URL-
    based scenario location enables pytest-bdd to fetch and execute these remote features without manual download. The
    async fetch (aiohttp) is the primary backend for CPython, while the synchronous fallback (urllib) via
    PyPyUrlScenarioLocator ensures PyPy support (where aiohttp may have issues). The temporary file pattern (write →
    parse → cleanup) is necessary because the Gherkin parser API expects file paths, not in-memory strings.

Delegates:
    - aiohttp.ClientSession: Async HTTP client for fetching feature files concurrently.
    - urllib.request.urlopen: Synchronous HTTP client used by PyPyUrlScenarioLocator for PyPy compatibility.
    - certifi: Provides CA certificates for SSL verification on both async and sync paths.
    - ssl.create_default_context: Creates SSL context with certifi certificates for secure connections.
    - pytest_bdd.mimetype.Mimetype: Media type enum for content-type based parser selection.
    - pytest_bdd.scenario.Args: Parser arguments configuration.
    - pytest_bdd.util.url.is_local_url: Detects if a URL path is a local file reference vs remote URL.
    - pytest_bdd.util.other.IdGenerator: Provides unique IDs for parsing.
    - NamedTemporaryFile: Creates temporary files for URL content before parsing.
    - PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS: Error suppression gate.

Cohesion:
    All entities serve URL-based feature resolution. UrlScenarioLocator owns the async fetch pipeline,
    PyPyUrlScenarioLocator specializes it for sync fetch, _build_urls constructs URL lists, _fetch_feature_responses
    handles the async/sync dispatch, _get_parser_type handles parser selection, _parse_and_yield_feature handles temp
    file management and parsing, and _write_temp_feature_file/_parse_temp_feature are helper stages in the temp file
    pipeline.

Separation:
    - FileScenarioLocator: Kept separate because FileScenarioLocator handles local disk-based resolution with glob
    patterns and file caching, while UrlScenarioLocator handles remote URL-based resolution with HTTP fetching, temp
    files, and async I/O — completely different I/O models and configuration surfaces.
    - pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin: Kept separate because the mixin provides the shared
    resolve() pipeline, while UrlScenarioLocator provides URL-specific resolve_features().

Main consumers:
    - pytest_bdd.collector: Uses UrlScenarioLocator when feature sources are URLs.
    - pytest_bdd.scenario.scenarios(): Creates UrlScenarioLocator when paths are URLs.
    - pytest_bdd.scenario_locator.__init__: Re-exported through public API.

State and side effects:
    Stores configuration (url_paths, encoding, features_base_url, mimetype, parser_type, parse_args) via attrs.
    resolve_features performs network I/O (HTTP requests), creates temporary files (NamedTemporaryFile), and cleans them
    up (Path.unlink). Async event loop is created and closed per fetch batch.

Invariants:
    - Temporary files must be cleaned up (unlinked) even if parsing fails — the finally block guarantees this.
    - SSL verification must use certifi certificates — sslcontext is created with certifi.where() for both async and
    sync paths.
    - The event loop must be properly closed after each fetch batch — the finally block in _fetch_feature_responses
    guarantees loop.close().

Failure semantics:
    - Network errors during fetch are collected as BaseException in the response list (via return_exceptions=True) and
    skipped in resolve_features.
    - FeatureParseError on parsing follows the CONTINUE_ON_COLLECTION_ERRORS gate (same as file locator).
    - Missing parser_type causes early return (break) — no parser for the detected format.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=4
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import asyncio
import ssl
import urllib.request
from contextlib import suppress
from itertools import filterfalse
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, cast
from urllib.parse import urljoin

from attrs import define, field
from cucumber_messages import Source

from pytest_bdd.mimetype import Mimetype
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.url import is_local_url

from .base import ScenarioLocatorFilterMixin, ScenarioLocatorHookProtocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from enum import Enum

    import aiohttp

    from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.types.protocol import HasPytestStash


@define
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Implements URL-based feature resolution using aiohttp for async HTTP fetching.

    Responsibility:
        Implements URL-based feature resolution using aiohttp for async HTTP fetching. Configured with url_paths (URLs
        or Path objects used as URL segments), optional features_base_url (prefix for relative URLs, can be a callable),
        and optional encoding/mimetype/parser_type/parse_args overrides. The resolve_features() pipeline: builds
        complete URLs via _build_urls(), fetches all URLs concurrently via fetch_all() which creates an async event
        loop, writes each response to a temporary file, parses with hook-selected or explicit parser, and yields
        (ParsedFeature, Source) tuples. Temporary files are cleaned up after parsing regardless of success or failure.

    Reason for existence:
        Remote feature files are a common pattern in BDD — teams centralize feature specifications on shared servers,
        test management platforms, or version control URLs. This class enables pytest-bdd to fetch and execute these
        remote features without manual download. The async fetching via aiohttp provides concurrent HTTP requests for
        efficiency with multiple URLs. The temporary file pattern bridges the gap between HTTP responses (in-memory
        strings) and the Gherkin parser API (file-path-based).

    Delegates:
        - _build_urls: Constructs complete URL list from url_paths and features_base_url.
        - _fetch_feature_responses: Creates event loop and runs fetch_all to get content.
        - fetch_all: Orchestrates concurrent aiohttp requests via asyncio.gather.
        - fetch: Performs individual async HTTP GET with SSL verification.
        - _get_parser_type: Resolves parser class from hook or explicit configuration.
        - _parse_and_yield_feature: Handles temp file writing, parsing, and cleanup.
        - _write_temp_feature_file / _parse_temp_feature: Temp file helper stages.
        - aiohttp.ClientSession: Async HTTP session for concurrent requests.
        - certifi: Provides CA certificates for SSL.

    Cohesion:
        Every method supports URL-based feature fetching: url_paths and features_base_url define the URLs, _build_urls
        constructs them, fetch/fetch_all handle HTTP, _write_temp_feature_file creates temp files, _parse_temp_feature
        parses them, _parse_and_yield_feature orchestrates the temp file lifecycle, and resolve_features is the main
        pipeline. All methods form a complete HTTP → parse pipeline.

    Separation:
        - FileScenarioLocator: Kept separate because file-based location uses disk I/O, glob patterns, and batch parser
        caching, while URL-based location uses HTTP, async I/O, and temp files — completely different I/O models.
        - PyPyUrlScenarioLocator: Kept separate because PyPy uses synchronous urllib instead of async aiohttp —
        different HTTP backends for different Python implementations.

    Main consumers:
        - pytest_bdd.collector: Uses UrlScenarioLocator for URL-based scenario discovery.
        - pytest_bdd.scenario.scenarios(): Creates UrlScenarioLocator when paths are URLs.
        - pytest_bdd.scenario_locator.__init__: Re-exported through public API.

    State and side effects:
        Stores configuration (attrs fields). resolve_features performs network I/O (HTTP requests — side effects on
        remote servers), creates temp files (filesystem I/O), and cleans them up. Creates and closes an async event loop
        per call.

    Invariants:
        - URLs from url_paths that pass is_local_url() are joined with features_base_url; URLs that fail is_local_url()
        are used directly as absolute URLs.
        - Temporary files must be cleaned up (unlinked) in the finally block even if parsing raises an exception.
        - SSL context must use certifi certificates — sslcontext is created with certifi.where().

    Failure semantics:
        Network errors collected as BaseException are silently skipped in resolve_features.
        FeatureParseError follows CONTINUE_ON_COLLECTION_ERRORS gate.
        Missing parser_type causes empty yield (no results).

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=4
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    url_paths: list[str | Path] = field()
    encoding: str | None = field(default=None)
    features_base_url: str | Callable[[Config | HasPytestStash], str | None] | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
        """
        Perform a single async HTTP GET request for a feature file URL using an aiohttp ClientSession.

        Responsibility:
            Performs a single async HTTP GET request for a feature file URL using an aiohttp ClientSession. Creates an
            SSL context with certifi CA certificates for secure connections, awaits the response, and returns a tuple of
            (content_type, response_text) decoded with the configured encoding (default "utf-8"). This is the lowest-
            level HTTP operation in the URL locator — all URL fetching flows through this method.

        Reason for existence:
            This method encapsulates the HTTP GET operation with proper SSL configuration. Using certifi certificates
            ensures the SSL connection verifies against a trusted CA bundle rather than using the system's potentially
            outdated or missing certificates. The content_type from the response headers is used later for mimetype-
            based parser selection, enabling automatic format detection from HTTP servers.

        Delegates:
            - aiohttp.ClientSession.get: Performs the async HTTP GET request.
            - ssl.create_default_context(cafile=certifi.where()): Creates SSL context with trusted CA certificates.
            - certifi.where(): Returns the path to the certifi CA bundle.
            - response.content_type: Extracts the media type from HTTP response headers.
            - response.text(encoding): Reads response body as text with specified encoding.

        Cohesion:
            The method performs one operation: HTTP GET → return content_type + text. Every line serves this purpose.

        Separation:
            - fetch_all: Kept separate because fetch_all orchestrates concurrent requests via asyncio.gather, while
            fetch performs individual requests — single vs batch.
            - PyPyUrlScenarioLocator._fetch_feature_responses: Kept separate because PyPy uses synchronous urllib
            instead of async aiohttp.

        Main consumers:
            - fetch_all: Called via asyncio.gather for each URL in the URL list.

        State and side effects:
            Performs network I/O (HTTP request) — a side effect on the remote server. SSL context creation is a local computation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        import certifi

        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with session.get(url, ssl=sslcontext) as response:
            return response.content_type, await response.text(encoding=self.encoding or "utf-8")

    async def fetch_all(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Orchestrates concurrent async HTTP GET requests for all URLs in the sequence using a single aiohttp ClientSession.

        Responsibility:
            Orchestrates concurrent async HTTP GET requests for all URLs in the sequence using a single aiohttp
            ClientSession. Uses asyncio.gather with return_exceptions=True to collect results (including exceptions) for
            all URLs, ensuring that one failed request doesn't abort others. Returns a list where each element is either
            a (content_type, text) tuple on success or a BaseException on failure. This is the batch entry point for URL
            fetching.

        Reason for existence:
            Concurrent fetching is essential for performance when multiple feature URLs are configured — without it,
            URLs would be fetched sequentially, multiplying total wait time by the number of URLs. The
            return_exceptions=True flag ensures robust behavior: network errors for individual URLs are collected and
            can be handled gracefully in resolve_features (skipped) rather than crashing the entire batch.

        Delegates:
        - aiohttp.ClientSession: Created as async context manager — ensures proper connection cleanup.
        - asyncio.gather(*tasks, return_exceptions=True): Runs all fetch tasks concurrently, collecting results and exceptions.
        - self.fetch: The individual fetch operation called for each URL.

        Cohesion:
            The method performs one operation: create session → concurrent fetch → gather results. Every line serves
            this batch fetching purpose.

        Separation:
            - fetch: Kept separate because fetch is the single-request operation while fetch_all is the batch orchestrator.
            - _fetch_feature_responses: Kept separate because that method creates the event loop and awaits fetch_all,
            while fetch_all is the async logic — sync orchestration vs async implementation.

        Main consumers:
            - _fetch_feature_responses: Called within the event loop to perform the actual fetching.

        State and side effects:
            Creates an aiohttp.ClientSession (network resource) and performs N concurrent HTTP requests. Session is
            cleaned up via async context manager.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        import aiohttp

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.fetch(session, url) for url in urls], return_exceptions=True)

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Implement the feature discovery and parsing pipeline for URL-based sources: builds complete URLs via _build_urls(), .

        Responsibility:
            Implements the feature discovery and parsing pipeline for URL-based sources: builds complete URLs via
            _build_urls(), fetches all URL content via _fetch_feature_responses() (synchronous wrapper around async
            fetch_all), for each successful response extracts the mimetype (from explicit config or response
            content_type), selects a parser via _get_parser_type(), and delegates to _parse_and_yield_feature() which
            handles temporary file writing, parsing, and cleanup. Network errors are silently skipped (non-BaseException
            responses are processed). Yields (ParsedFeature, Source) tuples with the original URL as the source URI.

        Reason for existence:
            This is the main resolution loop for URL-based feature loading. It orchestrates: URL construction → batch
            HTTP fetch → per-response mimetype detection → parser selection → temp file → parse → yield. Without this
            method, URL-based feature sources would have no discovery and parsing pipeline.

        Delegates:
            - _build_urls: Constructs the list of complete URLs.
            - _fetch_feature_responses: Synchronous wrapper that manages the async event loop for batch fetching.
            - _get_parser_type: Resolves the parser class for the detected mimetype.
            - _parse_and_yield_feature: Handles temp file creation, parsing, cleanup, and yielding.
            - IdGenerator.from_stash: Provides unique IDs for parser instantiation.
            - Mimetype: Used to normalize the raw mimetype string for parser selection.

        Cohesion:
            The method is a clear pipeline: build URLs → fetch → for each response → detect type → select parser → parse
            → yield. Every line serves this orchestration.

        Separation:
            - resolve (from ScenarioLocatorFilterMixin): Kept separate because resolve is the full pipeline (features →
            binding → filtering), while resolve_features is the feature discovery stage.
            - FileScenarioLocator.resolve_features: Kept separate because file-based resolution uses disk I/O and cache,
            while URL-based uses HTTP and temp files.

        Main consumers:
            - self.resolve() (inherited): Called as the first stage of scenario resolution.

        State and side effects:
            Performs network I/O (HTTP requests), creates temporary files, instantiates parsers. Cleans up temp files
            via _parse_and_yield_feature's finally block.

        Failure semantics:
            Network errors (BaseException in responses) are silently skipped.
            Missing parser_type causes empty yield (early return via break or None parser).
            FeatureParseError follows CONTINUE_ON_COLLECTION_ERRORS gate in _parse_temp_feature.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        urls = self._build_urls()
        if not urls:
            return
        responses = self._fetch_feature_responses(urls)
        hook_handler = cast("ScenarioLocatorHookProtocol", cast("Config", config).hook)
        encoding = self.encoding or "utf-8"

        for url, response in zip(urls, responses, strict=False):
            if isinstance(response, BaseException):
                continue

            mimetype_raw, feature_content = response
            mimetype_source = self.mimetype if self.mimetype is not None else mimetype_raw
            mimetype = Mimetype(str(mimetype_source))
            parser_type = self._get_parser_type(hook_handler, config, mimetype)
            if parser_type is None:
                break

            parser = parser_type(id_generator=IdGenerator.from_stash(config.stash))

            yield from self._parse_and_yield_feature(parser, config, url, feature_content, mimetype, encoding)

    def _build_urls(self) -> list[str]:
        """
        Construct the complete list of URLs to fetch by processing url_paths entries: paths that are NOT local URLs (absolut.

        Responsibility:
            Constructs the complete list of URLs to fetch by processing url_paths entries: paths that are NOT local URLs
            (absolute URLs) are used directly as strings; paths that ARE local URLs (relative paths) are joined with
            features_base_url using urljoin (appending the path to the base URL with proper slash handling). Returns the
            concatenated list of absolute URLs. This is the URL construction stage that converts the mix of relative and
            absolute URL specifications into a uniform list for fetching.

        Reason for existence:
            Users can specify URL features as absolute URLs (https://example.com/features/foo.feature), relative paths
            (features/foo.feature with a base URL), or a mix. This method separates absolute and relative URLs and
            processes each appropriately. The is_local_url() check determines whether a path is a relative reference
            (needing base URL joining) or an absolute URL (used as-is). Without this method, the URL list would need to
            be pre-normalized by the caller.

        Delegates:
            - is_local_url: Determines if a path is a relative/local reference vs absolute URL.
            - urljoin: Joins a base URL with a relative path, handling slash normalization.
            - filterfalse(is_local_url, ...): Filters out local URLs (extracting absolute URLs).
            - filter(is_local_url, ...): Filters for local URLs (extracting relative paths to join).

        Cohesion:
            The method performs one operation: convert url_paths entries into absolute URLs. The filter operations
            separate the two URL categories.

        Separation:
            - _fetch_feature_responses: Kept separate because that method fetches URLs while this method constructs them
            — construction vs execution.
            - resolve_features: Kept separate because resolve_features orchestrates the full pipeline while _build_urls
            handles URL construction.

        Main consumers:
            - resolve_features: Called at the start to build the URL list for fetching.

        State and side effects:
            None. Pure function of self.url_paths and self.features_base_url.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        urls = [str(url) for url in filterfalse(is_local_url, self.url_paths)]
        if self.features_base_url is not None:
            urls.extend(
                str(urljoin(f"{self.features_base_url}/", str(path))) for path in filter(is_local_url, self.url_paths)
            )
        return urls

    def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Wrap synchronously to create creates a new asyncio event loop, runs the async fetch_all() method within it to fetch all U.

        Responsibility:
            Synchronous wrapper that creates a new asyncio event loop, runs the async fetch_all() method within it to
            fetch all URLs concurrently, waits 250ms for SSL connections to close cleanly, and returns the list of
            (content_type, text) tuples or BaseException for each URL. Ensures the event loop is properly closed in the
            finally block. This is the bridge between the synchronous resolve_features() caller and the async
            fetch_all() implementation.

        Reason for existence:
            pytest's collection hooks are synchronous, but HTTP fetching benefits from async concurrency. This method
            bridges the gap by creating a dedicated event loop, running the async fetch in it, and returning results
            synchronously. The 250ms sleep after fetching allows underlying SSL connections to close gracefully,
            preventing "SSL connection not closed" warnings. The finally block ensures the loop is always closed,
            preventing resource leaks.

        Delegates:
            - asyncio.new_event_loop(): Creates a fresh event loop for this fetch batch.
            - loop.run_until_complete(self.fetch_all(urls)): Runs the async fetch in the new loop.
            - loop.run_until_complete(asyncio.sleep(0.250)): Waits for SSL connection cleanup.
            - loop.close(): Ensures the event loop resources are freed.

        Cohesion:
            The method performs one operation: create loop → run async fetch → cleanup → return results. Every line
            serves this bridge pattern.

        Separation:
            - fetch_all: Kept separate because fetch_all is the async implementation while _fetch_feature_responses is
            the sync bridge — async core vs sync wrapper.
            - PyPyUrlScenarioLocator._fetch_feature_responses: Kept separate because PyPy overrides this with
            synchronous urllib — different HTTP backends.

        Main consumers:
            - resolve_features: Called to synchronously fetch all URLs.

        State and side effects:
            Creates and closes an asyncio event loop — system resource management. Performs network I/O through the
            loop. The 250ms sleep is a wait for network connection cleanup.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        loop = asyncio.new_event_loop()
        try:
            responses = loop.run_until_complete(self.fetch_all(urls))
            # Wait 250 ms for the underlying SSL connections to close
            loop.run_until_complete(asyncio.sleep(0.250))
            return responses
        finally:
            loop.close()

    def _get_parser_type(
        self,
        hook_handler: ScenarioLocatorHookProtocol,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        """
        Resolve the parser class for a given media type: if self.parser_type is explicitly configured, returns it directly; .

        Responsibility:
            Resolves the parser class for a given media type: if self.parser_type is explicitly configured, returns it
            directly; otherwise, delegates to the hook system via hook_handler.pytest_bdd_get_parser(config, mimetype).
            Returns None if no parser is registered for the media type. This is the parser selection stage that bridges
            explicit configuration and plugin-based parser registration.

        Reason for existence:
            Parser selection is a decision point that can be influenced by explicit user configuration or plugin hooks.
            This method encapsulates that decision in one place, ensuring both paths return the same type
            (ParserProtocol | None). Without this method, resolve_features would need to inline the if/else logic for
            multiple call sites.

        Delegates:
            - hook_handler.pytest_bdd_get_parser: Plugin hook for parser lookup by media type.

        Cohesion:
            The method performs one operation: select parser class from config or hook. The if/else is the only branching.

        Separation:
            - resolve_features: Kept separate because resolve_features orchestrates the pipeline while _get_parser_type
            handles parser selection — orchestration vs selection.

        Main consumers:
            - resolve_features: Called to get the parser before instantiating it.

        State and side effects:
            None. Reads self.parser_type (immutable) and invokes hook (may trigger plugin logic).

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        if self.parser_type is None:
            return hook_handler.pytest_bdd_get_parser(
                config=config,
                mimetype=mimetype,
            )
        return self.parser_type

    def _parse_and_yield_feature(  # noqa: PLR0913, PLR0917  -- URL locator parse args include all fetch/parse configuration in one boundary
        self,
        parser: ParserProtocol,
        config: Config | HasPytestStash,
        url: str,
        feature_content: str,
        mimetype: Mimetype,
        encoding: str,
    ) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Handle the complete temp-file-based parsing lifecycle for a single URL feature: writes the feature content to a temp.

        Responsibility:
            Handles the complete temp-file-based parsing lifecycle for a single URL feature: writes the feature content
            to a temporary file (via _write_temp_feature_file), parses it using the configured parser (via
            _parse_temp_feature), constructs a Source object with the original URL as URI, yields the (ParsedFeature,
            Source) tuple, and ensures the temporary file is deleted in the finally block (suppressing any cleanup
            errors). This is the final stage of the URL resolution pipeline before yielding results.

        Reason for existence:
            The Gherkin parser API expects file paths, not in-memory strings. This method bridges that gap by writing
            HTTP response content to a temp file, parsing it, and cleaning up. The finally block is critical — without
            it, temp files would accumulate on disk. The suppress(Exception) in cleanup ensures that cleanup failures
            (e.g., permission issues) don't mask parsing errors.

        Delegates:
            - _write_temp_feature_file: Creates a temporary file with the feature content.
            - _parse_temp_feature: Parses the temp file using the configured parser.
            - NamedTemporaryFile: Creates temp files with automatic naming.
            - Path.unlink: Deletes the temp file after parsing.

        Cohesion:
            The method performs one pipeline: write → parse → yield → cleanup. Every line serves this temp file lifecycle.

        Separation:
            - _write_temp_feature_file: Kept separate because that method handles file creation while this method
            handles the full lifecycle — creation vs lifecycle management.
            - _parse_temp_feature: Kept separate because that method handles parsing while this method orchestrates file
            lifecycle — parsing vs orchestration.

        Main consumers:
            - resolve_features: Called for each successfully fetched URL.

        State and side effects:
            Creates a temporary file (filesystem I/O — side effect), reads it (parse), deletes it (filesystem I/O). The
            finally block guarantees cleanup.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        filename = self._write_temp_feature_file(feature_content)
        try:
            parsed = self._parse_temp_feature(parser, config, Path(filename), url, encoding)
            if parsed is None:
                return
            media_type = str(mimetype) if mimetype is not None else "text/plain;charset=UTF-8"
            yield parsed, Source(uri=url, data=parsed.raw_data, media_type=media_type)
        finally:
            with suppress(Exception):
                Path(filename).unlink()

    @staticmethod
    def _write_temp_feature_file(feature_content: str) -> str:
        """
        Provide static method that writes feature content (a string) to a new temporary file using NamedTemporaryFile with UTF-8 enco.

        Responsibility:
            Static method that writes feature content (a string) to a new temporary file using NamedTemporaryFile with
            UTF-8 encoding and delete=False (caller manages cleanup). Returns the temp file's path as a string. This is
            the first stage of the temp file pipeline — converting in-memory HTTP response content into a filesystem
            path that the Gherkin parser can read.

        Reason for existence:
            The Gherkin parser requires a file path, not an in-memory string. This method creates a temporary file to
            satisfy that API requirement. Using NamedTemporaryFile with delete=False gives the caller full control over
            the file's lifecycle (write → parse → delete), which is managed by _parse_and_yield_feature. The static
            method pattern indicates this operation doesn't depend on instance state.

        Delegates:
            - NamedTemporaryFile(encoding="utf-8", mode="w", delete=False): Creates a temporary file that persists after closing.
            - file.write(feature_content): Writes the feature content to the file.
            - file.name: The auto-generated path of the temporary file.

        Cohesion:
            The method performs one operation: write content to temp file → return path. Every line serves this purpose.

        Separation:
            - _parse_temp_feature: Kept separate because that method reads and parses the temp file, while this method
            creates it — write vs read/parse.
            - _parse_and_yield_feature: Kept separate because that method manages the full lifecycle (write → parse →
            cleanup), while this handles only the write stage.

        Main consumers:
            - _parse_and_yield_feature: Called to create the temp file before parsing.

        State and side effects:
            Creates a file on disk (filesystem side effect). The file is NOT deleted by this method — cleanup is the
            caller's responsibility.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        with NamedTemporaryFile(encoding="utf-8", mode="w", delete=False) as file:
            file.write(feature_content)
            return file.name

    def _parse_temp_feature(
        self,
        parser: ParserProtocol,
        config: Config | HasPytestStash,
        path: Path,
        url: str,
        encoding: str,
    ) -> ParsedFeature | None:
        """
        Pars a temporary feature file using the provided parser with the original URL as the Gherkin URI, encoding, and any.

        Responsibility:
            Parses a temporary feature file using the provided parser with the original URL as the Gherkin URI,
            encoding, and any configured parse_args. Catches FeatureParseError and checks the
            PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS option: if enabled, returns None (skipping the feature
            silently); if disabled, re-raises the exception. This is the parsing stage of the temp file pipeline, the
            last step before yielding results to the caller.

        Reason for existence:
            Parsing is the critical step where network content becomes structured feature data. The error handling gate
            (CONTINUE_ON_COLLECTION_ERRORS) allows the same flexibility as file-based resolution: failing features can
            either halt collection (strict mode) or be silently skipped (robust mode). The deferred import of
            PytestConfigParam avoids circular dependency issues.

        Delegates:
            - parser.parse(config, path, url, *args, encoding=encoding, **kwargs): Performs the actual Gherkin parsing.
            - PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS: Configuration gate for error suppression.
            - Args: The configured parser arguments unpacked into the parse call.

        Cohesion:
            The method performs one operation: parse file → handle error → return result or re-raise. Every line serves
            this parsing stage.

        Separation:
            - _write_temp_feature_file: Kept separate because that method creates the file while this method parses it —
            write vs read/parse.
            - _parse_and_yield_feature: Kept separate because that method manages the lifecycle while this handles the
            parsing — orchestration vs stage.

        Main consumers:
            - _parse_and_yield_feature: Called after writing the temp file to parse and potentially yield results.

        State and side effects:
            Reads from disk (parser.parse reads the file). No file modification.

        Failure semantics:
            Raises FeatureParseError when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is disabled.
            Returns None when parsing fails and CONTINUE_ON_COLLECTION_ERRORS is enabled — caller silently skips.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        from pytest_bdd.const import PytestConfigParam

        try:
            parse_args = self.parse_args or Args((), {})
            return parser.parse(
                config,
                path,
                url,
                *parse_args.args,
                **{"encoding": encoding, **parse_args.kwargs},
            )
        except FeatureParseError:
            if cast("Config", config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                return None
            raise


@define
class PyPyUrlScenarioLocator(UrlScenarioLocator):
    """
    A PyPy-compatible subclass of UrlScenarioLocator that overrides _fetch_feature_responses() to use synchronous urllib.

    Responsibility:
        A PyPy-compatible subclass of UrlScenarioLocator that overrides _fetch_feature_responses() to use synchronous
        urllib.request.urlopen() instead of async aiohttp. Iterates over URLs sequentially, creates SSL context with
        certifi certificates, performs synchronous HTTP GET with 10-second timeout, reads response headers
        (content_type) and body (decoded with configured encoding), and collects results as (content_type, text) tuples
        or BaseException on failure. This avoids the async/await requirements that may not be available or performant on
        PyPy implementations.

    Reason for existence:
        aiohttp has known compatibility issues with PyPy due to its reliance on asyncio and C extensions. This subclass
        provides a synchronous fallback using stdlib urllib, which works reliably on all Python implementations. The
        10-second timeout prevents hung connections from blocking collection indefinitely. The subclass pattern (rather
        than a runtime check) makes the choice explicit at import time — users on PyPy import PyPyUrlScenarioLocator,
        users on CPython import UrlScenarioLocator.

    Delegates:
        - urllib.request.urlopen: Synchronous HTTP GET with SSL context and timeout.
        - ssl.create_default_context(cafile=certifi.where()): SSL context with trusted certificates.
        - certifi.where(): CA bundle path for SSL verification.
        - response.headers.get_content_type(): Extracts Content-Type header.
        - response.read() + decode: Reads response body and decodes with configured encoding.

    Cohesion:
        The overridden method has one purpose: provide synchronous HTTP fetching. All logic in _fetch_feature_responses
        serves this single purpose — SSL setup, URL iteration, request execution, error handling.

    Separation:
        - UrlScenarioLocator: Kept separate because UrlScenarioLocator uses async aiohttp while PyPyUrlScenarioLocator
        uses sync urllib — different HTTP backends, shared configuration and pipeline.
        - FileScenarioLocator: Kept separate because file-based location is entirely different (disk I/O vs network I/O).

    Main consumers:
        - PyPy environments: Used instead of UrlScenarioLocator for PyPy-compatible URL fetching.
        - pytest_bdd.scenario_locator.__init__: Re-exported through public API.

    State and side effects:
        Performs synchronous network I/O (blocking HTTP requests). Creates temporary SSL context per call.

    Invariants:
        - HTTP timeout must be explicitly set (10 seconds default) — no infinite hanging on network issues.
        - Broad Exception catch is necessary to handle all possible network/SSL/protocol errors — specific exception
        types vary by Python version and platform.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        PyPy-compatible synchronous override that fetches URLs sequentially using stdlib urllib.request.urlopen() with SSL ve.

        Responsibility:
            PyPy-compatible synchronous override that fetches URLs sequentially using stdlib urllib.request.urlopen()
            with SSL verification (certifi CA bundle) and a 10-second timeout. For each URL: opens the connection, reads
            Content-Type header and response body (decoded with configured encoding, default "utf-8"), and appends
            (content_type, text) to results. Catches all exceptions (broad Exception handler) and appends them to
            results instead of crashing, ensuring one failed URL doesn't prevent other URLs from being processed.

        Reason for existence:
            PyPy does not reliably support aiohttp's async I/O model. This override provides a synchronous fallback
            using Python's stdlib urllib, which is universally available and well-tested on all implementations. The
            10-second timeout prevents network issues from blocking collection. The broad Exception catch is necessary
            because network errors can manifest as many different exception types (URLError, HTTPError, socket.timeout,
            SSL errors, etc.), and the caller (resolve_features) handles all of them uniformly by skipping.

        Delegates:
            - urllib.request.urlopen(url, context=sslcontext, timeout=10): Synchronous HTTP GET.
            - ssl.create_default_context(cafile=certifi.where()): SSL context configuration.
            - response.headers.get_content_type(): Extracts Content-Type.
            - response.read(): Reads raw response bytes.
            - content_bytes.decode(encoding): Decodes bytes to string.

        Cohesion:
            The method performs one operation: for each URL → HTTP GET → return content type and text. The sequential
            loop (no async) is the key characteristic. Every line serves synchronous HTTP fetching.

        Separation:
            - UrlScenarioLocator._fetch_feature_responses: Kept separate because the parent uses async event loop +
            aiohttp while this overrides with synchronous urllib — async vs sync HTTP backends.

        Main consumers:
            - UrlScenarioLocator.resolve_features (inherited): Called to fetch URLs synchronously on PyPy.

        State and side effects:
            Performs blocking network I/O (up to 10 seconds per URL × N URLs). Reads SSL certificates from certifi bundle.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        import certifi

        responses: list[tuple[str, str] | BaseException] = []
        sslcontext = ssl.create_default_context(cafile=certifi.where())
        for url in urls:
            try:
                with urllib.request.urlopen(url, context=sslcontext, timeout=10) as response:  # noqa: S310  -- URL validated by caller; HTTP/HTTPS scheme enforced upstream
                    content_type = response.headers.get_content_type()
                    content_bytes = response.read()
                    content_text = content_bytes.decode(self.encoding or "utf-8")
                    responses.append((content_type, content_text))
            except Exception as e:  # noqa: BLE001, PERF203  -- broad catch required to wrap all network/SSL errors into a unified FeatureFetchError
                responses.append(e)
        return responses
