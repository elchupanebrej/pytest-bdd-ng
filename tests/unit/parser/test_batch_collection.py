from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import pytest

from pytest_cuke.batch_collection import (
    BatchFeatureRequest,
    BatchFeatureCollectionError,
    BatchResultNotReadyError,
    CollectionBatchService,
    platform_default_batch_threshold,
    resolve_batch_threshold,
)
from pytest_cuke.model import Feature
from pytest_cuke.parser import BaseParser, GherkinParser
from pytest_cuke.utils import IdGenerator


class _Config:
    def __init__(self, option: int | None, ini: int | None) -> None:
        self.option = option
        self.ini = ini

    def getoption(self, name: str) -> int | None:
        assert name == "cuke_batch_threshold"
        return self.option

    def getini(self, name: str) -> int | None:
        assert name == "cuke_batch_threshold"
        return self.ini


class _CountingParser(BaseParser):
    calls = 0

    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature:
        type(self).calls += 1
        return Feature(name=content.strip(), uri=uri or "")


class _FailingParser(BaseParser):
    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature:
        raise ValueError("custom parser rejected the source")


def _request(path: Path, *, uri: str | None = None, parser: BaseParser | None = None) -> BatchFeatureRequest:
    return BatchFeatureRequest(
        path=path,
        uri=uri or f"file:{path.name}",
        encoding="utf-8",
        parser=parser or _CountingParser(),
        mimetype="text/x-gherkin",
        parser_options=(),
    )


@pytest.mark.parametrize(
    ("option", "ini", "expected"),
    [(7, 9, 7), (None, 9, 9), (None, None, platform_default_batch_threshold())],
)
def test_batch_threshold_prefers_cli_then_ini_then_platform_default(
    option: int | None,
    ini: int | None,
    expected: int,
) -> None:
    assert resolve_batch_threshold(_Config(option, ini)) == expected


@pytest.mark.parametrize(("platform_name", "expected"), [("posix", 50), ("nt", 1000)])
def test_platform_default_batch_threshold(platform_name: str, expected: int) -> None:
    assert platform_default_batch_threshold(platform_name=platform_name) == expected


def test_batch_service_requires_flush_and_accepts_late_registration(tmp_path: Path) -> None:
    first = tmp_path / "first.feature"
    first.write_text("First feature", encoding="utf-8")
    second = tmp_path / "second.feature"
    second.write_text("Second feature", encoding="utf-8")
    service = CollectionBatchService(threshold=10)
    first_request = _request(first)

    service.register_many([first_request])
    with pytest.raises(BatchResultNotReadyError, match="flush the batch"):
        service.get(first_request)

    service.flush()
    assert service.get(first_request).name == "First feature"
    service.flush()

    second_request = _request(second)
    service.register_many([second_request])
    with pytest.raises(BatchResultNotReadyError):
        service.get(second_request)
    service.flush()
    assert service.get(second_request).name == "Second feature"


def test_empty_flush_is_a_no_op(tmp_path: Path) -> None:
    service = CollectionBatchService(threshold=1)
    service.flush()
    service.flush()
    assert service.pending == {}
    assert service.results == {}


def test_normalized_path_cache_parses_once_and_keeps_binding_uri(tmp_path: Path) -> None:
    feature_path = tmp_path / "catalog.feature"
    feature_path.write_text("Catalog feature", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    alias_path = tmp_path / "nested" / ".." / "catalog.feature"
    parser = _CountingParser()
    _CountingParser.calls = 0
    first = _request(feature_path, uri="file:features/catalog.feature", parser=parser)
    second = _request(alias_path, uri="file:../features/catalog.feature")
    service = CollectionBatchService(threshold=10)

    first_result, second_result = service.resolve_many([first, second])

    assert _CountingParser.calls == 1
    assert first_result.name == second_result.name == "Catalog feature"
    assert first_result.uri == "file:features/catalog.feature"
    assert second_result.uri == "file:../features/catalog.feature"
    assert second_result.filename == str(alias_path.as_posix())


def test_custom_parser_failure_keeps_the_feature_path(tmp_path: Path) -> None:
    path = tmp_path / "custom.feature"
    path.write_text("Custom input", encoding="utf-8")
    request = _request(path, parser=_FailingParser())
    service = CollectionBatchService(threshold=10)

    with pytest.raises(BatchFeatureCollectionError) as error:
        service.resolve_many([request])

    assert str(path) in str(error.value)
    assert "ValueError: custom parser rejected the source" in str(error.value)


@pytest.mark.parametrize("parser_mode", ["python", "auto"])
def test_spawn_batch_parses_feature_models(tmp_path: Path, parser_mode: str) -> None:
    path = tmp_path / "spawned.feature"
    path.write_text("Feature: Spawned\n  Scenario: Parsed in a worker\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:spawned.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", parser_mode),),
    )
    service = CollectionBatchService(threshold=1)

    feature = service.resolve_many([request])[0]
    serial_feature = GherkinParser().parse(
        path,
        uri=request.uri,
        encoding=request.encoding,
        parser_mode=parser_mode,
    )

    assert feature.name == "Spawned"
    assert feature.scenarios[0].name == "Parsed in a worker"
    assert feature.source_content == path.read_text(encoding="utf-8")
    assert feature == serial_feature


def test_parser_with_parent_owned_id_generator_stays_in_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "parent-id-generator.feature"
    path.write_text("Feature: Parent IDs\n  Scenario: Parent-owned identity\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:parent-id-generator.feature",
        encoding="utf-8",
        parser=GherkinParser(id_generator=IdGenerator()),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    def spawn_not_expected(_worker_jobs: object) -> None:
        pytest.fail("a parser with a parent-owned ID generator must be parsed in the parent")

    monkeypatch.setattr(service, "_parse_in_workers", spawn_not_expected)

    feature = service.resolve_many([request])[0]

    assert feature.scenarios[0].name == "Parent-owned identity"


def test_distinct_parent_id_generators_do_not_share_a_cached_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "stateful-parser.feature"
    path.write_text("Feature: Stateful parser\n  Scenario: Preserve parser state\n", encoding="utf-8")
    first_generator = IdGenerator()
    second_generator = IdGenerator()
    first = BatchFeatureRequest(
        path=path,
        uri="file:first-stateful.feature",
        encoding="utf-8",
        parser=GherkinParser(id_generator=first_generator),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    second = BatchFeatureRequest(
        path=path,
        uri="file:second-stateful.feature",
        encoding="utf-8",
        parser=GherkinParser(id_generator=second_generator),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=10)
    original_parse_text = GherkinParser.parse_text
    generators_seen: list[IdGenerator] = []

    def count_parse_text(parser: GherkinParser, *args: Any, **kwargs: Any) -> Feature:
        generators_seen.append(parser.id_generator)
        return original_parse_text(parser, *args, **kwargs)

    monkeypatch.setattr(GherkinParser, "parse_text", count_parse_text)

    first_feature, second_feature = service.resolve_many([first, second])

    assert generators_seen == [first_generator, second_generator]
    assert first_feature.uri == first.uri
    assert second_feature.uri == second.uri
    assert service._stateful_id_generators == {
        id(first_generator): first_generator,
        id(second_generator): second_generator,
    }


def test_missing_aiofiles_uses_synchronous_reads_and_still_spawns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "sync-read.feature"
    source = "Feature: Sync read\n  Scenario: Spawn parse\n"
    path.write_text(source, encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:sync-read.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)
    original_read_text = Path.read_text
    reads = 0

    def counted_read_text(feature_path: Path, *args: Any, **kwargs: Any) -> str:
        nonlocal reads
        reads += 1
        return original_read_text(feature_path, *args, **kwargs)

    def async_reader_must_not_run(_requests: object) -> Any:
        pytest.fail("aiofiles absence should use synchronous reads")

    monkeypatch.setattr("pytest_cuke.batch_collection._aiofiles_available", lambda: False)
    monkeypatch.setattr("pytest_cuke.batch_collection._read_many_async", async_reader_must_not_run)
    monkeypatch.setattr(Path, "read_text", counted_read_text)

    feature = service.resolve_many([request])[0]

    assert reads == 1
    assert feature.source_content == source
    assert feature.scenarios[0].name == "Spawn parse"


def test_spawn_start_failure_falls_back_to_serial_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "fallback.feature"
    path.write_text("Feature: Fallback\n  Scenario: Parsed serially\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:fallback.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    def unavailable_spawn(_method: str) -> Any:
        raise RuntimeError("spawn unavailable")

    monkeypatch.setattr("pytest_cuke.batch_collection.multiprocessing.get_context", unavailable_spawn)
    with caplog.at_level(logging.WARNING, logger="pytest_cuke.batch_collection"):
        feature = service.resolve_many([request])[0]

    assert feature.scenarios[0].name == "Parsed serially"
    assert "falling back to serial parsing" in caplog.text


def test_worker_failure_falls_back_to_serial_without_dropping_the_feature(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "worker-failure.feature"
    path.write_text("Feature: Worker failure\n  Scenario: Kept by fallback\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:worker-failure.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    class WorkerFailure:
        def get(self) -> Any:
            raise RuntimeError("simulated worker failure")

    class PoolDouble:
        def __init__(self) -> None:
            self.closed = False
            self.exited = False

        def __enter__(self) -> PoolDouble:
            return self

        def __exit__(self, *_args: object) -> None:
            self.exited = True

        def apply_async(self, *_args: object) -> WorkerFailure:
            return WorkerFailure()

        def close(self) -> None:
            self.closed = True

    class ContextDouble:
        def __init__(self) -> None:
            self.pool = PoolDouble()

        def Pool(self, **_kwargs: object) -> PoolDouble:
            return self.pool

    context = ContextDouble()
    monkeypatch.setattr("pytest_cuke.batch_collection.multiprocessing.get_context", lambda _method: context)

    with caplog.at_level(logging.WARNING, logger="pytest_cuke.batch_collection"):
        feature = service.resolve_many([request])[0]

    assert context.pool.closed
    assert context.pool.exited
    assert feature.scenarios[0].name == "Kept by fallback"
    assert "falling back to serial parsing" in caplog.text


def test_keyboard_interrupt_exits_the_spawn_pool_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "interrupted.feature"
    path.write_text("Feature: Interrupted\n  Scenario: Pending\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:interrupted.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    class InterruptingResult:
        def get(self) -> Any:
            raise KeyboardInterrupt

    class PoolDouble:
        exited = False

        def __enter__(self) -> PoolDouble:
            return self

        def __exit__(self, *_args: object) -> None:
            self.exited = True

        def apply_async(self, *_args: object) -> InterruptingResult:
            return InterruptingResult()

        def close(self) -> None:
            pass

    class ContextDouble:
        def __init__(self) -> None:
            self.pool = PoolDouble()

        def Pool(self, **_kwargs: object) -> PoolDouble:
            return self.pool

    context = ContextDouble()
    monkeypatch.setattr("pytest_cuke.batch_collection.multiprocessing.get_context", lambda _method: context)

    with pytest.raises(KeyboardInterrupt):
        service.resolve_many([request])

    assert context.pool.exited
    service.close()


def test_async_read_failure_retries_serially_and_keeps_file_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "unreadable.feature"
    path.mkdir()
    request = BatchFeatureRequest(
        path=path,
        uri="file:unreadable.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    async def failed_async_read(_requests: object) -> dict[Any, Exception]:
        return {request.key: IsADirectoryError(str(path))}

    monkeypatch.setattr("pytest_cuke.batch_collection._aiofiles_available", lambda: True)
    monkeypatch.setattr("pytest_cuke.batch_collection._read_many_async", failed_async_read)

    with caplog.at_level(logging.WARNING, logger="pytest_cuke.batch_collection"), pytest.raises(
        BatchFeatureCollectionError
    ) as error:
        service.resolve_many([request])

    assert str(path) in str(error.value)
    assert any(error_name in str(error.value) for error_name in ("IsADirectoryError", "PermissionError"))
    assert "falling back to serial reading" in caplog.text


def test_collection_inside_running_loop_does_not_call_asyncio_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "active-loop.feature"
    path.write_text("Feature: Active loop\n  Scenario: Parsed safely\n", encoding="utf-8")
    request = BatchFeatureRequest(
        path=path,
        uri="file:active-loop.feature",
        encoding="utf-8",
        parser=GherkinParser(),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service = CollectionBatchService(threshold=1)

    async def collect() -> Feature:
        def nested_loop_forbidden(*_args: object, **_kwargs: object) -> None:
            pytest.fail("collection must not call asyncio.run inside a running event loop")

        monkeypatch.setattr("pytest_cuke.batch_collection._aiofiles_available", lambda: True)
        monkeypatch.setattr(asyncio, "run", nested_loop_forbidden)
        return service.resolve_many([request])[0]

    feature = asyncio.run(collect())

    assert feature.scenarios[0].name == "Parsed safely"


def test_batch_service_close_clears_session_cache(tmp_path: Path) -> None:
    path = tmp_path / "cached.feature"
    path.write_text("Feature: Cached\n  Scenario: Cached result\n", encoding="utf-8")
    service = CollectionBatchService(threshold=10)
    request = BatchFeatureRequest(
        path=path,
        uri="file:cached.feature",
        encoding="utf-8",
        parser=GherkinParser(id_generator=IdGenerator()),
        mimetype="text/x-gherkin",
        parser_options=(("parser_mode", "python"),),
    )
    service.resolve_many([request])
    assert service._stateful_id_generators

    service.close()

    assert service.pending == {}
    assert service.results == {}
    assert service._stateful_id_generators == {}
    with pytest.raises(RuntimeError, match="closed"):
        service.register_many([request])


def test_session_finish_closes_batch_cache_after_interrupted_run(tmp_path: Path) -> None:
    from pytest_cuke.plugin import pytest_sessionfinish

    class Session:
        def __init__(self, config: _Config) -> None:
            self.config = config
            self.stash: dict[Any, Any] = {}

    config = _Config(option=1, ini=None)
    session = Session(config)
    service = CollectionBatchService.for_session(session, config)
    path = tmp_path / "interrupted-session.feature"
    path.write_text("Cached result", encoding="utf-8")
    service.resolve_many([_request(path)])

    pytest_sessionfinish(session, exitstatus=2)

    assert service._closed
    assert service.pending == {}
    assert service.results == {}


def test_batch_service_is_stored_per_session() -> None:
    class Session:
        def __init__(self) -> None:
            self.stash: dict[Any, Any] = {}

    first_session = Session()
    second_session = Session()
    config = _Config(option=4, ini=8)

    first_service = CollectionBatchService.for_session(first_session, config)
    repeated_service = CollectionBatchService.for_session(first_session, config)
    second_service = CollectionBatchService.for_session(second_session, config)

    assert first_service is repeated_service
    assert first_service is not second_service
    assert first_service.threshold == second_service.threshold == 4
