"""Session-scoped cache and spawn-based batch parsing for feature collection."""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import multiprocessing
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

from attrs import evolve

from pytest_cuke.compatibility.parser import LegacyParserAdapter
from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.external_examples import has_external_examples_reference
from pytest_cuke.model.message_converter import parse_error_to_envelope
from pytest_cuke.model.stash_access import SessionStash, StashKey
from pytest_cuke.parser import BaseParser, GherkinParser, MarkdownGherkinParser, ParserProtocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.model import Feature


logger = logging.getLogger(__name__)
_BATCH_SERVICE_CONFIG_ATTRIBUTE = "_pytest_cuke_collection_batch_service"


class BatchResultNotReadyError(RuntimeError):
    """A registered feature was requested before its batch had been flushed."""


class BatchFeatureCollectionError(RuntimeError):
    """A feature could not be read or parsed during a collection batch."""


@dataclass(frozen=True, slots=True)
class BatchFeatureRequest:
    path: Path
    uri: str
    encoding: str
    parser: ParserProtocol
    mimetype: str | None
    parser_options: tuple[tuple[str, Any], ...]

    @property
    def key(self) -> tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]:
        parser_type = type(self.parser)
        parser_name = getattr(
            self.parser,
            "cache_identity",
            f"{parser_type.__module__}.{parser_type.__qualname__}",
        )
        id_generator = getattr(self.parser, "id_generator", None)
        if id_generator is not None:
            parser_name = f"{parser_name}@{id(id_generator):x}"
        options = tuple((key, repr(value)) for key, value in self.parser_options)
        return (
            os.path.normcase(str(self.path.resolve())),
            self.encoding,
            parser_name,
            self.mimetype or "",
            str(getattr(self.parser, "kind", "")),
            options,
        )


@dataclass(frozen=True, slots=True)
class _WorkerJob:
    key: tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]
    path: str
    uri: str
    source_media_type: str
    parser_kind: str
    parser_options: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class _ParseErrorDetails:
    message: str
    line: int
    line_text: str
    uri: str
    column: int


@dataclass(frozen=True, slots=True)
class _WorkerOutcome:
    feature: Feature | None = None
    error_type: str | None = None
    error_message: str | None = None
    parse_error: _ParseErrorDetails | None = None


def _parse_error_details(error: Exception) -> _ParseErrorDetails | None:
    if not isinstance(error, FeatureConcreteParseError):
        return None
    return _ParseErrorDetails(
        message=error.parse_message,
        line=error.line,
        line_text=error.line_text,
        uri=error.source_uri,
        column=error.column,
    )


def _parse_error_from_details(details: _ParseErrorDetails) -> FeatureConcreteParseError:
    return FeatureConcreteParseError(
        details.message,
        details.line,
        details.line_text,
        details.uri,
        column=details.column,
    )


def _parse_worker(job: _WorkerJob, content: str) -> _WorkerOutcome:
    """Parse plain source in a spawn worker without invoking pytest collection."""
    parser: GherkinParser | MarkdownGherkinParser
    if job.parser_kind == "gherkin":
        parser = GherkinParser()
    else:
        parser = MarkdownGherkinParser()
    try:
        feature = parser.parse_text(content, uri=job.uri, **dict(job.parser_options))
        feature = evolve(
            feature,
            filename=job.path,
            source_content=content,
            source_media_type=job.source_media_type,
        )
    except Exception as error:
        return _WorkerOutcome(
            error_type=type(error).__name__,
            error_message=str(error),
            parse_error=_parse_error_details(error),
        )
    return _WorkerOutcome(feature=feature)


async def _read_feature_text(path: Path, encoding: str) -> str:
    import aiofiles  # type: ignore[import-untyped]  # Optional dependency checked before the async path.
    async with aiofiles.open(path, mode="r", encoding=encoding) as source:
        return cast("str", await source.read())


async def _read_many_async(requests: Iterable[BatchFeatureRequest]) -> dict[
    tuple[str, str, str, str, str, tuple[tuple[str, str], ...]], str | Exception
]:
    jobs = list(requests)
    outcomes = await asyncio.gather(
        *(_read_feature_text(request.path, request.encoding) for request in jobs),
        return_exceptions=True,
    )
    return {
        request.key: outcome if isinstance(outcome, Exception) else str(outcome)
        for request, outcome in zip(jobs, outcomes, strict=True)
    }


def _read_many_sync(requests: Iterable[BatchFeatureRequest]) -> dict[
    tuple[str, str, str, str, str, tuple[tuple[str, str], ...]], str | Exception
]:
    outcomes: dict[tuple[str, str, str, str, str, tuple[tuple[str, str], ...]], str | Exception] = {}
    for request in requests:
        try:
            outcomes[request.key] = request.path.read_text(encoding=request.encoding)
        except Exception as error:
            outcomes[request.key] = error
    return outcomes


def _aiofiles_available() -> bool:
    try:
        return importlib.util.find_spec("aiofiles") is not None
    except (ImportError, ValueError):
        return False


def platform_default_batch_threshold(*, platform_name: str | None = None) -> int:
    """Return the documented batch size for the current operating system."""
    current_platform = os.name if platform_name is None else platform_name
    return 50 if current_platform == "posix" else 1000


def resolve_batch_threshold(config: Any) -> int:
    """Resolve CLI over ini over the platform default."""
    try:
        command_line = config.getoption("cuke_batch_threshold")
    except (AttributeError, ValueError):
        command_line = None
    if command_line is not None:
        return int(command_line)
    try:
        configured = config.getini("cuke_batch_threshold")
    except (AttributeError, KeyError, ValueError):
        configured = None
    if configured not in (None, ""):
        return int(configured)
    return platform_default_batch_threshold()


class CollectionBatchService:
    """Own parsed feature results for one pytest collection session."""

    STASH_KEY: ClassVar[StashKey[CollectionBatchService]] = StashKey(
        "pytest_cuke_collection_batch_service",
        "Cached feature parse results and pending batch reads for one pytest session.",
    )

    def __init__(self, threshold: int, config: Any = None) -> None:
        if threshold < 1:
            raise ValueError("feature collection batch threshold must be at least 1")
        self.threshold = threshold
        self.config = config
        self.pending: dict[tuple[str, str, str, str, str, tuple[tuple[str, str], ...]], BatchFeatureRequest] = {}
        self.results: dict[
            tuple[str, str, str, str, str, tuple[tuple[str, str], ...]], Feature | Exception
        ] = {}
        self._registered: set[tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]] = set()
        self._stateful_id_generators: dict[int, object] = {}
        self._closed = False
        self._autoload_primed = False

    @property
    def autoload_primed(self) -> bool:
        return self._autoload_primed

    @classmethod
    def for_session(cls, session: Any, config: Any) -> CollectionBatchService:
        stash = SessionStash.from_session(session)
        service = stash.get(cls.STASH_KEY)
        if not isinstance(service, cls):
            service = cls(resolve_batch_threshold(config), config=config)
            stash[cls.STASH_KEY] = service
        else:
            service.config = config
        setattr(config, _BATCH_SERVICE_CONFIG_ATTRIBUTE, service)
        return service

    @classmethod
    def for_config(cls, config: Any) -> CollectionBatchService | None:
        service = getattr(config, _BATCH_SERVICE_CONFIG_ATTRIBUTE, None)
        return service if isinstance(service, cls) else None

    def prime_autoload(self, requests: Iterable[BatchFeatureRequest]) -> None:
        """Register autoload candidates once before their collectors resolve locators."""
        if self._autoload_primed or self._closed:
            return
        self._autoload_primed = True
        self.register_many(requests)
        if len(self._registered) >= self.threshold:
            self.flush()

    def register_many(self, requests: Iterable[BatchFeatureRequest]) -> list[tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]]:
        if self._closed:
            raise RuntimeError("feature collection batch service is closed")
        keys: list[tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]] = []
        for request in requests:
            id_generator = getattr(request.parser, "id_generator", None)
            if id_generator is not None:
                # Retain identity tokens for the cache lifetime so Python cannot
                # reuse an ID for a later generator after its parser is collected.
                self._stateful_id_generators[id(id_generator)] = id_generator
            key = request.key
            keys.append(key)
            self._registered.add(key)
            if key not in self.results and key not in self.pending:
                self.pending[key] = request
        return keys

    def get(self, request: BatchFeatureRequest) -> Feature:
        """Return an already-flushed feature or raise a cached per-file error."""
        try:
            result = self.results[request.key]
        except KeyError as error:
            raise BatchResultNotReadyError(
                f"Feature result for {request.path} is pending; flush the batch before retrieving it."
            ) from error
        if isinstance(result, Exception):
            raise result
        return evolve(result, uri=request.uri, filename=str(request.path.as_posix()))

    def resolve_many(self, requests: Iterable[BatchFeatureRequest]) -> list[Feature]:
        request_list = list(requests)
        keys = self.register_many(request_list)
        if len(self._registered) >= self.threshold:
            self.flush()
        else:
            for key in dict.fromkeys(keys):
                if key in self.pending:
                    self._parse_serial(key)
        return [self.get(request) for request in request_list]

    def flush(self) -> None:
        """Read pending sources asynchronously and parse built-ins in spawn workers."""
        if self._closed or not self.pending:
            return
        requests = list(self.pending.values())
        batch_parse_requests = [request for request in requests if _worker_parser_kind(request.parser) is not None]
        for request in requests:
            if _worker_parser_kind(request.parser) is None:
                self._parse_serial(request.key)
        if not batch_parse_requests:
            return
        uses_async_reads = _aiofiles_available()
        async_reads_attempted = False
        if uses_async_reads:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                async_reads_attempted = True
                read_results = asyncio.run(_read_many_async(batch_parse_requests))
            else:
                # Collection may be invoked while an application owns this thread's loop.
                # Keep collection synchronous there; never nest asyncio.run inside it.
                read_results = _read_many_sync(batch_parse_requests)
        else:
            read_results = _read_many_sync(batch_parse_requests)

        worker_jobs: list[tuple[BatchFeatureRequest, _WorkerJob, str]] = []
        for request in batch_parse_requests:
            key = request.key
            content = read_results[key]
            if isinstance(content, Exception):
                if async_reads_attempted:
                    logger.warning(
                        "Asynchronous feature read failed for %s; falling back to serial reading: %s",
                        request.path,
                        content,
                    )
                else:
                    self._store_error(
                        key,
                        BatchFeatureCollectionError(
                            f"Failed to read feature file '{request.path}': {type(content).__name__}: {content}"
                        ),
                    )
                    continue
                try:
                    content = request.path.read_text(encoding=request.encoding)
                except Exception as serial_error:
                    self._store_error(
                        key,
                        BatchFeatureCollectionError(
                            f"Failed to read feature file '{request.path}' in batch and serial modes: "
                            f"{type(serial_error).__name__}: {serial_error}"
                        ),
                    )
                    continue
            parser_kind = _worker_parser_kind(request.parser)
            if parser_kind is None or has_external_examples_reference(content):
                self._parse_serial(key)
                continue
            parser_options = request.parser_options
            parser = request.parser
            job = _WorkerJob(
                key=key,
                path=str(request.path),
                uri=request.uri,
                source_media_type=cast("BaseParser", parser)._source_media_type(request.path),
                parser_kind=parser_kind,
                parser_options=parser_options,
            )
            worker_jobs.append((request, job, content))

        self._parse_in_workers(worker_jobs)

    def close(self) -> None:
        """Release cached models and pending requests at the end of the session."""
        if self._closed:
            return
        self.pending.clear()
        self.results.clear()
        self._registered.clear()
        self._stateful_id_generators.clear()
        self._closed = True

    def _parse_serial(self, key: tuple[str, str, str, str, str, tuple[tuple[str, str], ...]]) -> None:
        request = self.pending.pop(key, None)
        if request is None:
            return
        try:
            feature = request.parser.parse(
                request.path,
                uri=request.uri,
                encoding=request.encoding,
                **dict(request.parser_options),
            )
        except Exception as error:
            if isinstance(request.parser, LegacyParserAdapter):
                # Preserve extension exceptions as-is; adapting a parser must not
                # disguise an exception raised inside user code.
                self.results[key] = error
            else:
                self._store_collection_failure(
                    key,
                    f"Failed to parse feature file '{request.path}': {type(error).__name__}: {error}",
                    error,
                )
        else:
            self.results[key] = feature

    def _store_error(
        self,
        key: tuple[str, str, str, str, str, tuple[tuple[str, str], ...]],
        error: Exception,
    ) -> None:
        self.pending.pop(key, None)
        self.results[key] = error

    def _parse_in_workers(self, worker_jobs: list[tuple[BatchFeatureRequest, _WorkerJob, str]]) -> None:
        if not worker_jobs:
            return
        try:
            context = multiprocessing.get_context("spawn")
            processes = min(len(worker_jobs), max(1, os.cpu_count() or 1))
            with context.Pool(processes=processes) as pool:
                pending_results = [pool.apply_async(_parse_worker, (job, content)) for _, job, content in worker_jobs]
                pool.close()
                for (request, job, _), async_result in zip(worker_jobs, pending_results, strict=True):
                    try:
                        outcome = async_result.get()
                    except Exception as error:
                        logger.warning(
                            "Batch feature parsing failed for %s; falling back to serial parsing: %s",
                            request.path,
                            error,
                        )
                        self._parse_serial(job.key)
                        continue
                    self.pending.pop(job.key, None)
                    if outcome.feature is not None:
                        self.results[job.key] = outcome.feature
                    else:
                        parse_error = (
                            _parse_error_from_details(outcome.parse_error) if outcome.parse_error is not None else None
                        )
                        self._store_collection_failure(
                            job.key,
                            f"Failed to parse feature file '{request.path}' in batch worker "
                            f"({outcome.error_type or 'ParserError'}): {outcome.error_message or 'unknown error'}",
                            parse_error,
                        )
        except Exception as error:
            logger.warning(
                "Batch feature collection could not start; falling back to serial parsing: %s",
                error,
            )
            for request, job, _ in worker_jobs:
                if job.key in self.pending:
                    self._parse_serial(request.key)

    def _store_collection_failure(
        self,
        key: tuple[str, str, str, str, str, tuple[tuple[str, str], ...]],
        message: str,
        cause: Exception | None,
    ) -> None:
        if isinstance(cause, FeatureConcreteParseError):
            self._emit_parse_error(cause)
        collection_error = BatchFeatureCollectionError(message)
        if cause is not None:
            collection_error.__cause__ = cause
        self.results[key] = collection_error

    def _emit_parse_error(self, error: FeatureConcreteParseError) -> None:
        """Send one parser diagnostic through pytest's public message hook."""
        if error.line < 1 or not error.source_uri:
            return
        hook = getattr(getattr(self.config, "hook", None), "pytest_cuke_message", None)
        if hook is not None:
            hook(config=self.config, message=parse_error_to_envelope(error))


def _worker_parser_kind(parser: ParserProtocol) -> str | None:
    # User-supplied generators carry parent-owned ID state that must not be copied
    # into an independent worker process.
    if getattr(parser, "id_generator", None) is not None:
        return None
    parser_type = type(parser)
    if parser_type is GherkinParser:
        return "gherkin"
    if parser_type is MarkdownGherkinParser:
        return "markdown"
    return None


def get_batch_service(config: Any) -> CollectionBatchService | None:
    """Return this pytest run's service when called during collection."""
    return CollectionBatchService.for_config(config)


__all__ = [
    "BatchFeatureCollectionError",
    "BatchFeatureRequest",
    "BatchResultNotReadyError",
    "CollectionBatchService",
    "get_batch_service",
    "platform_default_batch_threshold",
    "resolve_batch_threshold",
]
