import asyncio
import os
import ssl
from collections.abc import Callable, Iterable
from contextlib import suppress
from enum import Enum
from functools import partial, reduce
from itertools import filterfalse
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable
from urllib.parse import urljoin

import aiohttp
import certifi
from attrs import define, field
from cucumber_messages import (
    GherkinDocument,
    Pickle,
    Source,
)

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pathlib import GlobError
from pytest_bdd.compatibility.pytest import Config, get_config_root_path
from pytest_bdd.const import PytestConfigParam
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.plugin.scenario_test_collector.const import FeatureBaseLoad
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.url import is_local_url

if TYPE_CHECKING:
    from pytest_bdd.compatibility.typing import TypeAlias


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    def resolve_features(
        self,
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[GherkinDocument, Source]]:  # pragma: no cover
        ...


@runtime_checkable
class ScenarioLocatorReadObserver(Protocol):
    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:  # pragma: no cover
        ...

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:  # pragma: no cover
        ...

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:  # pragma: no cover
        ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterable[tuple[GherkinDocument, Pickle, Source]]:  # pragma: no cover
        ...


ScenarioLocatorFilterT: "TypeAlias" = Callable[[Config, GherkinDocument, Pickle], bool]


@define
class ScenarioLocatorFilterMixin(ScenarioLocatorFeatureResolver, ScenarioLocatorResolver):
    filter_: ScenarioLocatorFilterT | None = field(default=None, kw_only=True)

    def filter_scenarios(self, gherkin_document: GherkinDocument, pickles: Iterable[Pickle], config):
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
    ):
        run = Run.from_stash(config.stash)
        binding = run.ensure_feature_binding(gherkin_document=gherkin_document, source=source)
        binding.ensure_pickles(id_generator=IdGenerator.from_stash(config.stash))
        return binding

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ):
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
    url_paths = field()
    encoding = field()
    features_base_url = field()
    mimetype = field()
    parser_type = field()
    parse_args = field()

    async def fetch(self, session: aiohttp.ClientSession, url):
        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with session.get(url, ssl=sslcontext) as response:
            return response.content_type, await response.text(encoding=self.encoding)

    async def fetch_all(self, urls):
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.fetch(session, url) for url in urls], return_exceptions=True)

    def resolve_features(self, config: Config | HasPytestStash):
        urls = self._build_urls()
        if not urls:
            return
        responses = self._fetch_feature_responses(urls)
        hook_handler = cast(Config, config).hook
        encoding = self.encoding

        for url, response in zip(urls, responses, strict=False):
            if isinstance(response, Exception):
                continue

            mimetype_raw, feature_content = response
            mimetype = Mimetype(self.mimetype if self.mimetype is not None else mimetype_raw)
            parser_type = self._get_parser_type(hook_handler, config, mimetype)
            if parser_type is None:
                break

            parser = parser_type(id_generator=IdGenerator.from_stash(config.stash))

            yield from self._parse_and_yield_feature(parser, config, url, feature_content, mimetype, encoding)

    def _build_urls(self):
        urls = [*filterfalse(is_local_url, self.url_paths)]
        if self.features_base_url is not None:
            urls.extend(
                map(
                    partial(urljoin, f"{self.features_base_url}/"),
                    filter(is_local_url, self.url_paths),
                )
            )
        return urls

    def _fetch_feature_responses(self, urls):
        loop = asyncio.new_event_loop()
        responses = loop.run_until_complete(self.fetch_all(urls))
        # Wait 250 ms for the underlying SSL connections to close
        loop.run_until_complete(asyncio.sleep(0.250))
        loop.close()
        return responses

    def _get_parser_type(self, hook_handler, config, mimetype):
        if self.parser_type is None:
            return hook_handler.pytest_bdd_get_parser(
                config=config,
                mimetype=mimetype,
            )
        return self.parser_type

    def _parse_and_yield_feature(self, parser, config, url, feature_content, mimetype, encoding):
        filename = None
        try:
            with NamedTemporaryFile(encoding="utf-8", mode="w", delete=False) as f:
                filename = f.name
                f.write(feature_content)
            try:
                feature, feature_data = parser.parse(
                    config,
                    Path(filename),
                    url,
                    *self.parse_args.args,
                    **{"encoding": encoding, **self.parse_args.kwargs},
                )
            except FeatureParseError:
                if config.getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
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
    @staticmethod
    def encoding():
        return "utf-8"

    @staticmethod
    def parse_args():
        return Args((), {})


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    Defaults = FileScenarioLocatorDefaults
    feature_paths: list[str | Path] = field(factory=list)
    encoding = field(
        default=FileScenarioLocatorDefaults.encoding,
        converter=lambda _: _ if _ is not None else FileScenarioLocatorDefaults.encoding(),
    )
    features_base_dir: str | Path | None = field(default=None)
    mimetype: str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args = field(
        factory=FileScenarioLocatorDefaults.parse_args,
        converter=lambda _: _ if _ is not None else FileScenarioLocatorDefaults.parse_args(),
    )

    def _resolve_features_base_dir(self, config: Config | HasPytestStash):
        try:
            if self.features_base_dir is None:
                # TODO: refactor, move out from class usage to initialization or higher
                # TODO: add base dir command line option
                features_base_dir = cast(Config, config).getini(str(FeatureBaseLoad.Ini.DIR_OPTION))
            else:
                features_base_dir = self.features_base_dir
        except (ValueError, KeyError):
            features_base_dir = get_config_root_path(cast(Config, config))
        else:
            if callable(features_base_dir):
                features_base_dir = features_base_dir(config)

            features_base_dir = (get_config_root_path(cast(Config, config)) / Path(features_base_dir)).resolve()

        return features_base_dir

    def _gen_feature_paths(self, features_base_dir):
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
    def _build_file_uri(features_base_dir: Path, feature_path: Path):
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

    def resolve_features(self, config: Config | HasPytestStash):
        features_base_dir = self._resolve_features_base_dir(config)
        already_resolved_feature_paths = set()

        for feature_path in self._gen_feature_paths(features_base_dir=features_base_dir):
            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                break

            uri = self._build_file_uri(features_base_dir, feature_path)
            already_resolved_feature_paths.add(feature_path_key)
            hook_handler = cast(Config, config).hook
            encoding = self.encoding

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

            try:
                feature, feature_data = parser.parse(
                    config,
                    feature_path,
                    uri,
                    *self.parse_args.args,
                    **{"encoding": encoding, **self.parse_args.kwargs},
                )
            except FeatureParseError:
                if cast(Config, config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                    continue
                else:
                    raise
            source_media_type = str(media_type) if media_type is not None else "text/plain;charset=UTF-8"
            yield feature, Source(uri=uri, data=feature_data, media_type=source_media_type)
