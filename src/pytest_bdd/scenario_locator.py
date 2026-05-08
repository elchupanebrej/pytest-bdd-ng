"""Provide scenario locator helpers."""

from __future__ import annotations

import asyncio
import os
import ssl
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import suppress
from enum import Enum
from functools import reduce
from itertools import filterfalse
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Protocol, TypeAlias, cast, runtime_checkable
from urllib.parse import urljoin

from attrs import define, field
from cucumber_messages import (
    GherkinDocument,
    Pickle,
    Source,
)

from pytest_bdd.compatibility.pathlib import GlobError
from pytest_bdd.compatibility.pytest import Config, get_config_root_path
from pytest_bdd.const import PytestConfigParam
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_run import FeatureRuntimeBinding, Run
from pytest_bdd.plugin.scenario_test_collector.const import FeatureBaseLoad
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.url import is_local_url

if TYPE_CHECKING:
    import aiohttp

    from pytest_bdd.compatibility.parser import ParserProtocol


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    """Register locator feature resolver."""

    def resolve_features(
        self,
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[GherkinDocument, Source]]:  # pragma: no cover
        """Resolve features."""
        ...


@runtime_checkable
class ScenarioLocatorReadObserver(Protocol):
    """Register locator read observer."""

    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:  # pragma: no cover
        """Handle on source loaded."""
        ...

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:  # pragma: no cover
        """Handle on feature loaded."""
        ...

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:  # pragma: no cover
        """Handle on pickle loaded."""
        ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    """Register locator resolver."""

    """Represent scenario locator resolver state."""

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterable[tuple[GherkinDocument, Pickle, Source]]:  # pragma: no cover
        """Resolve resolve."""
        ...


class ScenarioLocatorHookProtocol(Protocol):
    """Register locator hook protocol."""

    def pytest_bdd_get_mimetype(self, *, config: Config, path: Path) -> Mimetype | str | Enum | None:
        """Handle bdd get mimetype."""
        ...

    def pytest_bdd_get_parser(
        self,
        *,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        """Handle bdd get parser."""
        ...


ScenarioLocatorFilterT: TypeAlias = Callable[[Config | HasPytestStash, GherkinDocument, Pickle], bool]


@define
class ScenarioLocatorFilterMixin(ScenarioLocatorFeatureResolver, ScenarioLocatorResolver):
    """
    Register locator filter mixin.

    Yields:
        Generated values.

    """

    filter_: ScenarioLocatorFilterT | None = field(default=None, kw_only=True)

    def filter_scenarios(
        self,
        gherkin_document: GherkinDocument,
        pickles: Iterable[Pickle],
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[GherkinDocument, Pickle]]:
        """
        Filter scenarios based on filter criteria.

        Args:
            gherkin_document: Parsed Gherkin document.
            pickles: List of pickle scenarios.
            config: Pytest config.

        Returns:
            Filtered tuples of (document, pickle).

        """
        return (
            (gherkin_document, pickle)
            for pickle in pickles
            if self.filter_ is None or self.filter_(config, gherkin_document, pickle)
        )

    @staticmethod
    def _bind_feature(
        gherkin_document: GherkinDocument,
        source: Source,
        config: Config | HasPytestStash,
    ) -> FeatureRuntimeBinding:
        """
        Bind a Gherkin document to the runtime.

        Args:
            gherkin_document: Parsed Gherkin document.
            source: Feature source information.
            config: Pytest config.

        Returns:
            Feature runtime binding.

        """
        run = Run.from_stash(config.stash)
        binding = run.ensure_feature_binding(gherkin_document=gherkin_document, source=source)
        binding.ensure_pickles(id_generator=IdGenerator.from_stash(config.stash))
        return binding

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
        """
        Resolve resolve.

        Yields:
            Generated values.

        """
        for gherkin_document, feature_source in self.resolve_features(config):
            binding = self._bind_feature(gherkin_document, feature_source, config)
            if observer is not None:
                observer.on_source_loaded(gherkin_document, feature_source)
                observer.on_feature_loaded(gherkin_document)
            for _, pickle in self.filter_scenarios(gherkin_document, binding.pickles, config):
                if observer is not None:
                    observer.on_pickle_loaded(gherkin_document, pickle)
                yield gherkin_document, pickle, feature_source


@define
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Represent url scenario locator state.

    Yields:
        Generated values.

    """

    url_paths: list[str | Path] = field()
    encoding: str | None = field(default=None)
    features_base_url: str | Callable[[Config | HasPytestStash], str | None] | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
        """
        Fetch content from URL.

        Args:
            session: aiohttp client session.
            url: URL to fetch.

        Returns:
            Tuple of (content_type, content_text).

        """
        import certifi

        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with session.get(url, ssl=sslcontext) as response:
            return response.content_type, await response.text(encoding=self.encoding or "utf-8")

    async def fetch_all(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Fetch all URLs concurrently.

        Args:
            urls: Sequence of URLs to fetch.

        Returns:
            List of tuples (content_type, content_text) or exceptions.

        """
        import aiohttp

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.fetch(session, url) for url in urls], return_exceptions=True)

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[GherkinDocument, Source]]:
        """
        Resolve features.

        Yields:
            Generated values.

        """
        urls = self._build_urls()
        if not urls:
            return
        responses = self._fetch_feature_responses(urls)
        hook_handler = cast(ScenarioLocatorHookProtocol, cast(Config, config).hook)
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
        urls = [str(url) for url in filterfalse(is_local_url, self.url_paths)]
        if self.features_base_url is not None:
            urls.extend(
                str(urljoin(f"{self.features_base_url}/", str(path))) for path in filter(is_local_url, self.url_paths)
            )
        return urls

    def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        loop = asyncio.new_event_loop()
        responses = loop.run_until_complete(self.fetch_all(urls))
        # Wait 250 ms for the underlying SSL connections to close
        loop.run_until_complete(asyncio.sleep(0.250))
        loop.close()
        return responses

    def _get_parser_type(
        self,
        hook_handler: ScenarioLocatorHookProtocol,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        if self.parser_type is None:
            return hook_handler.pytest_bdd_get_parser(
                config=config,
                mimetype=mimetype,
            )
        return self.parser_type

    def _parse_and_yield_feature(
        self,
        parser: ParserProtocol,
        config: Config | HasPytestStash,
        url: str,
        feature_content: str,
        mimetype: Mimetype,
        encoding: str,
    ) -> Iterator[tuple[GherkinDocument, Source]]:
        filename = None
        try:
            with NamedTemporaryFile(encoding="utf-8", mode="w", delete=False) as f:
                filename = f.name
                f.write(feature_content)
            try:
                parse_args = self.parse_args or Args((), {})
                feature, feature_data = parser.parse(
                    config,
                    Path(filename),
                    url,
                    *parse_args.args,
                    **{"encoding": encoding, **parse_args.kwargs},
                )
            except FeatureParseError:
                if cast(Config, config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                    return
                else:
                    raise
            media_type = str(mimetype) if mimetype is not None else "text/plain;charset=UTF-8"
            yield feature, Source(uri=url, data=feature_data, media_type=media_type)
        finally:
            if filename is not None:
                with suppress(Exception):
                    Path(filename).unlink()


class FileScenarioLocatorDefaults:
    """Provide default values for file scenario locators."""

    @staticmethod
    def encoding() -> str:
        """
        Return default encoding for feature files.

        Returns:
            Default encoding (utf-8).

        """
        return "utf-8"

    @staticmethod
    def parse_args() -> Args:
        """
        Return default parse arguments.

        Returns:
            Default args tuple.

        """
        return Args((), {})


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Represent file scenario locator state.

    Yields:
        Generated values.

    """

    Defaults = FileScenarioLocatorDefaults
    feature_paths: list[str | Path] = field(factory=list)
    encoding: str | None = field(default=None)
    features_base_dir: str | Path | Callable[[Config | HasPytestStash], str | Path] | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    def _resolve_features_base_dir(self, config: Config | HasPytestStash) -> Path:
        try:
            # TODO: refactor, move out from class usage to initialization or higher
            # TODO: add base dir command line option
            base_dir: str | Path | Callable[[Config | HasPytestStash], str | Path]
            if self.features_base_dir is None:
                base_dir = cast(Config, config).getini(str(FeatureBaseLoad.Ini.DIR_OPTION))
            else:
                base_dir = self.features_base_dir
        except (ValueError, KeyError):
            base_dir = get_config_root_path(cast(Config, config))
        else:
            if callable(base_dir):
                base_dir = cast(str | Path, base_dir(config))

            base_dir = (get_config_root_path(cast(Config, config)) / Path(base_dir)).resolve()

        return cast(Path, base_dir)

    def _gen_feature_paths(self, features_base_dir: Path) -> Iterator[Path]:
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = features_base_dir / feature_pathlike
                if feature_path.is_dir():
                    yield from filter(methodcaller("is_file"), feature_path.glob("**/*"))
                else:
                    yield feature_path
            else:
                try:
                    yield from filter(
                        methodcaller("is_file"),
                        features_base_dir.glob(os.fspath(feature_pathlike)),
                    )
                except GlobError:
                    yield from filter(methodcaller("is_file"), features_base_dir.glob("**/*"))

    @staticmethod
    def _build_file_uri(features_base_dir: Path, feature_path: Path) -> str:
        if feature_path.is_absolute():
            try:
                common_path = Path(commonpath([feature_path, features_base_dir]))
            except ValueError:
                rel_feature_path = feature_path
            else:
                sub_levels = len(features_base_dir.relative_to(common_path).parts)
                sub_path = reduce(truediv, [".."] * sub_levels, Path())
                rel_feature_path = sub_path / feature_path.relative_to(common_path)
        else:
            rel_feature_path = feature_path

        return "file:" + str(rel_feature_path.as_posix())

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[GherkinDocument, Source]]:
        """
        Resolve features.

        Yields:
            Generated values.

        Raises:
            FeatureParseError: If a configured feature cannot be parsed.

        """
        features_base_dir = self._resolve_features_base_dir(config)
        already_resolved_feature_paths: set[str] = set()

        for feature_path in self._gen_feature_paths(features_base_dir=features_base_dir):
            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                break

            uri = self._build_file_uri(features_base_dir, feature_path)
            already_resolved_feature_paths.add(feature_path_key)
            hook_handler = cast(Config, config).hook
            encoding = self.encoding or "utf-8"

            if self.mimetype is None:
                media_type = hook_handler.pytest_bdd_get_mimetype(config=cast(Config, config), path=feature_path)
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

            try:
                parse_args = self.parse_args or Args((), {})
                feature, feature_data = parser.parse(
                    config,
                    feature_path,
                    uri,
                    *parse_args.args,
                    **{"encoding": encoding, **parse_args.kwargs},
                )
            except FeatureParseError:
                if cast(Config, config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                    continue
                else:
                    raise
            source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
            yield feature, Source(uri=uri, data=feature_data, media_type=source_media_type)
