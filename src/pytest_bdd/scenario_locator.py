# ruff: noqa
from __future__ import annotations

import asyncio
import os
import ssl
import sys
from collections.abc import Callable, Iterable  # noqa: TC003
from contextlib import suppress
from functools import partial, reduce
from itertools import filterfalse
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from urllib.parse import urljoin
from urllib.request import urlopen

import aiohttp
import certifi
from attrs import Factory, attrib, attrs, define, field

from pytest_bdd.parser import ParserRegistry, default_parser_registry
from pytest_bdd.utils import is_local_url

if TYPE_CHECKING:
    from pytest_bdd.model import Feature, Scenario
    from pytest_bdd.parser import ParserProtocol


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    def resolve_features(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[Feature]: ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    def resolve(
        self, config: Any = None, registry: ParserRegistry | None = None
    ) -> Iterable[tuple[Feature, Scenario]]: ...


@define
class ScenarioLocatorFilterMixin:
    filter_: Callable[[Any, Feature, Scenario], bool] | None = field(default=None, kw_only=True)

    def filter_scenarios(self, feature: Feature, config: Any = None) -> Iterable[tuple[Feature, Scenario]]:
        for scenario in feature.scenarios:
            if self.filter_ is None or self.filter_(config, feature, scenario):
                yield feature, scenario

    def resolve(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[tuple[Feature, Scenario]]:
        for feature in self.resolve_features(config, registry=registry):  # type: ignore[attr-defined]
            yield from self.filter_scenarios(feature, config)


@define
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    url_paths: list[str] = field(factory=list)
    encoding: str = "utf-8"
    features_base_url: str | None = None
    mimetype: str | None = None
    parser_type: type[ParserProtocol] | None = None
    parser: ParserProtocol | None = None

    def resolve_features(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[Feature]:
        reg = registry or default_parser_registry
        urls = list(filterfalse(is_local_url, self.url_paths))
        if self.features_base_url is not None:
            urls.extend(
                map(
                    partial(urljoin, f"{self.features_base_url}/"),
                    filter(is_local_url, self.url_paths),
                )
            )

        for url in urls:
            try:
                with urlopen(url) as resp:  # noqa: S310
                    content_type = resp.headers.get_content_type()
                    content = resp.read().decode(self.encoding)

                media_type = self.mimetype or content_type
                p = self.parser
                if p is None:
                    if self.parser_type is not None:
                        p = self.parser_type()
                    elif media_type:
                        p = reg.get_parser_for_mimetype(media_type)
                    else:
                        p = reg.get_parser_for_path(url)

                if p is not None:
                    yield p.parse_text(content, uri=url)
            except Exception:  # noqa: S112
                continue


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    feature_paths: list[str | Path] = field(factory=list)
    encoding: str = "utf-8"
    features_base_dir: str | Path | None = None
    mimetype: str | None = None
    parser_type: type[ParserProtocol] | None = None
    parser: ParserProtocol | None = None

    def _resolve_features_base_dir(self, config: Any = None) -> Path:
        if self.features_base_dir is not None:
            base = self.features_base_dir
            if callable(base):
                base = base(config)
            return Path(base).resolve()

        if config is not None:
            try:
                ini_val = config.getini("bdd_features_base_dir")
                if ini_val:
                    return Path(ini_val).resolve()
            except (AttributeError, ValueError, KeyError):
                pass
            root = getattr(config, "rootpath", getattr(config, "rootdir", None))
            if root:
                return Path(root).resolve()

        return Path.cwd()

    def _gen_feature_paths(self, features_base_dir: Path) -> Iterable[Path]:
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = (
                    feature_pathlike if feature_pathlike.is_absolute() else features_base_dir / feature_pathlike
                )
                if feature_path.is_dir():
                    yield from filter(methodcaller("is_file"), feature_path.glob("**/*"))
                elif feature_path.is_file():
                    yield feature_path
            else:
                raw_str = str(feature_pathlike)
                path_obj = Path(raw_str)
                if path_obj.is_absolute():
                    if path_obj.is_dir():
                        yield from filter(methodcaller("is_file"), path_obj.glob("**/*"))
                    elif path_obj.is_file():
                        yield path_obj
                    else:
                        yield from filter(
                            methodcaller("is_file"),
                            path_obj.parent.glob(path_obj.name),
                        )
                else:
                    found = list(filter(methodcaller("is_file"), features_base_dir.glob(raw_str)))
                    if found:
                        yield from found
                    else:
                        target = features_base_dir / path_obj
                        if target.is_dir():
                            yield from filter(methodcaller("is_file"), target.glob("**/*"))
                        elif target.is_file():
                            yield target

    @staticmethod
    def _build_file_uri(features_base_dir: Path, feature_path: Path) -> str:
        if feature_path.is_absolute():
            try:
                common_path = Path(commonpath([feature_path, features_base_dir]))
                sub_levels = len(features_base_dir.relative_to(common_path).parts)
                sub_path = reduce(truediv, [".."] * sub_levels, Path())
                rel_feature_path = sub_path / feature_path.relative_to(common_path)
            except ValueError:
                rel_feature_path = feature_path
        else:
            rel_feature_path = feature_path

        return f"file:{rel_feature_path.as_posix()}"

    def resolve_features(self, config: Union[Config, PytestBDDIdGeneratorHandler]):
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

            parser = parser_type(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)

            feature, feature_data = parser.parse(
                config,
                feature_path,
                uri,
                *self.parse_args.args,
                **{**dict(encoding=encoding), **self.parse_args.kwargs},
            )
            try:
                yield feature, Source(uri=uri, data=feature_data, media_type=media_type)  # type: ignore[call-arg] # migration to pydantic2
            except ValidationError as e:
                # Workaround because of https://github.com/cucumber/messages/issues/161
                yield feature, None
