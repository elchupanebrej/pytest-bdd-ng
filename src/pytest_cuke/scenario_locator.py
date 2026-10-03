from __future__ import annotations

from functools import reduce
from hashlib import sha256
from operator import methodcaller, truediv
from os.path import commonpath, normcase
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable
from urllib.parse import urlparse
from urllib.request import urlopen

from attrs import define, evolve, field

from pytest_cuke.batch_collection import BatchFeatureRequest, get_batch_service
from pytest_cuke.compatibility.parser import LegacyParserAdapter
from pytest_cuke.feature_sources import FeatureSourceError, resolve_feature_sources, resolve_feature_url
from pytest_cuke.heading_scanner import enforce_feature_heading_policy
from pytest_cuke.mimetypes import STRUCT_BDD_FORMATS, Mimetype
from pytest_cuke.model import DataTable, DocString, Feature, Scenario, Step, TableCell, TableRow
from pytest_cuke.parser import (
    GherkinParser,
    MarkdownParser,
    ParserRegistration,
    ParserRegistry,
    default_parser_registry,
)
from pytest_cuke.parser_backend import resolve_parser_backend

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from pytest_cuke.parser import ParserProtocol


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
        all_scenarios = getattr(feature, "all_scenarios", feature.scenarios)
        for scenario in all_scenarios:
            if scenario.examples:
                for section_index, example in enumerate(scenario.examples, start=1):
                    if not example.header or not example.rows:
                        continue
                    headers = [c.value for c in example.header.cells]
                    for row_index, row in enumerate(example.rows):
                        mapping = {
                            h: (c.value if i < len(row.cells) else "")
                            for i, (h, c) in enumerate(zip(headers, row.cells, strict=False))
                        }
                        expanded_steps = []
                        for step in scenario.steps:
                            expanded_name = step.name
                            for k, v in mapping.items():
                                expanded_name = expanded_name.replace(f"<{k}>", v)

                            expanded_doc_string = step.doc_string
                            if expanded_doc_string is not None:
                                ds_content = expanded_doc_string.content
                                for k, v in mapping.items():
                                    ds_content = ds_content.replace(f"<{k}>", v)
                                expanded_doc_string = DocString(
                                    content=ds_content,
                                    media_type=expanded_doc_string.media_type,
                                    line=expanded_doc_string.line,
                                    id=expanded_doc_string.id,
                                )

                            expanded_data_table = step.data_table
                            if expanded_data_table is not None:
                                new_rows = []
                                for r in expanded_data_table.rows:
                                    new_cells = []
                                    for cell in r.cells:
                                        c_val = cell.value
                                        for k, v in mapping.items():
                                            c_val = c_val.replace(f"<{k}>", v)
                                        new_cells.append(TableCell(value=c_val, line=cell.line, id=cell.id))
                                    new_rows.append(TableRow(cells=tuple(new_cells), line=r.line, id=r.id))
                                expanded_data_table = DataTable(
                                    rows=tuple(new_rows),
                                    line=expanded_data_table.line,
                                    id=expanded_data_table.id,
                                )

                            expanded_steps.append(
                                Step(
                                    name=expanded_name,
                                    keyword=step.keyword,
                                    line=step.line,
                                    doc_string=expanded_doc_string,
                                    data_table=expanded_data_table,
                                    type=step.type,
                                    id=step.id,
                                )
                            )
                        expanded_tags = scenario.tags + (example.tags or ())
                        external_row_source = (
                            example.external_source.row_source(row_index, row.id) if example.external_source else None
                        )
                        identity_section = (
                            external_row_source.section_index if external_row_source is not None else section_index
                        )
                        identity_source = (
                            f"{feature.uri or feature.filename or feature.name}\0{external_row_source.path}"
                            if external_row_source
                            else ""
                        )
                        identity_digest = (
                            sha256(identity_source.encode("utf-8")).hexdigest()[:12] if identity_source else ""
                        )
                        expanded_name = (
                            f"{scenario.name}[external_examples:[section: {identity_section}, row: {row_index + 1}]]"
                            if external_row_source is not None
                            else f"{scenario.name}[table_rows:[line: {row.line}]]"
                        )
                        expanded_id = (
                            f"{scenario.id or scenario.name}-external-{identity_digest}"
                            f"-section-{identity_section}-row-{row_index + 1}"
                            if external_row_source is not None
                            else f"{scenario.id or scenario.name}-{row.id or row.line}"
                        )
                        expanded_scenario = Scenario(
                            name=expanded_name,
                            keyword=scenario.keyword,
                            description=scenario.description,
                            line=scenario.line,
                            id=expanded_id,
                            tags=expanded_tags,
                            steps=tuple(expanded_steps),
                            background=scenario.background,
                            examples=(),
                            external_example_source=external_row_source,
                            source_ast_node_ids=tuple(
                                node_id for node_id in (scenario.id, row.id) if node_id is not None
                            ),
                        )
                        if self.filter_ is None or self.filter_(config, feature, expanded_scenario):
                            yield feature, expanded_scenario
            elif self.filter_ is None or self.filter_(config, feature, scenario):
                yield feature, scenario

    def resolve(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[tuple[Feature, Scenario]]:
        feature_resolver = cast("ScenarioLocatorFeatureResolver", self)
        for feature in feature_resolver.resolve_features(config, registry=registry):
            yield from self.filter_scenarios(feature, config)


def _parser_from_config_hook(config: Any, path: Path, mimetype: str | None) -> Any:
    hook = getattr(config, "hook", None)
    if hook is None:
        return None

    resolved_mimetype = mimetype or hook.pytest_cuke_get_mimetype(config=config, path=path)
    if resolved_mimetype is None:
        return None

    parser_provider = hook.pytest_cuke_get_parser(config=config, mimetype=resolved_mimetype)
    if parser_provider is None:
        return None
    return _resolve_parser_provider(parser_provider, config)


def _resolve_parser_provider(parser_provider: Any, config: Any) -> ParserProtocol | None:
    if isinstance(parser_provider, ParserRegistration):
        return parser_provider.resolve(config)
    if isinstance(parser_provider, type):
        return cast("ParserProtocol", parser_provider())
    if callable(parser_provider) and not callable(getattr(parser_provider, "parse", None)):
        return cast("ParserProtocol", parser_provider())
    return cast("ParserProtocol | None", parser_provider)


@define
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    url_paths: list[str] = field(factory=list)
    encoding: str = "utf-8"
    features_base_url: str | None = None
    mimetype: str | None = None
    parser_type: type[ParserProtocol] | None = None
    parser: ParserProtocol | None = None
    parse_args: Any = None

    def resolve_features(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[Feature]:
        reg = registry or default_parser_registry
        source_settings = resolve_feature_sources(config, features_base_url=self.features_base_url)
        urls = [resolve_feature_url(path, source_settings.features_base_url) for path in self.url_paths]

        for url in urls:
            try:
                with urlopen(url) as resp:  # noqa: S310
                    content_type = resp.headers.get_content_type()
                    content = resp.read().decode(self.encoding)
            except Exception as error:
                raise FeatureSourceError(f"Could not load feature source {url!r}: {error}") from error

            try:
                media_type = self.mimetype or content_type
                p: Any = self.parser
                if p is None:
                    if self.parser_type is not None:
                        p = self.parser_type()
                    elif registry is not None:
                        if media_type:
                            p = reg.get_parser_for_mimetype(media_type)
                        if p is None:
                            p = reg.get_parser_for_path(url)
                        if p is None:
                            p = _parser_from_config_hook(config, Path(url), self.mimetype or content_type)
                    else:
                        p = _parser_from_config_hook(config, Path(url), self.mimetype or content_type)
                        if p is None and media_type:
                            p = reg.get_parser_for_mimetype(media_type)
                        if p is None:
                            p = reg.get_parser_for_path(url)
                p = _resolve_parser_provider(p, config)

                if p is None:
                    raise FeatureSourceError(f"No parser is registered for feature source {url!r}.")
                if isinstance(p, LegacyParserAdapter):
                    source_name = Path(urlparse(url).path).name or "remote.feature"
                    with TemporaryDirectory() as temp_dir:
                        source_path = Path(temp_dir) / source_name
                        source_path.write_text(content, encoding=self.encoding)
                        feature = p.parse(
                            source_path,
                            uri=url,
                            encoding=self.encoding,
                            _pytest_cuke_parse_args=self.parse_args,
                        )
                        has_temporary_filename = (
                            feature.filename is not None and Path(feature.filename).resolve() == source_path.resolve()
                        )
                        if has_temporary_filename:
                            # The legacy result points at the temporary download, which is deleted on exit.
                            feature = evolve(feature, filename=None)
                else:
                    parser_options = _parser_backend_options(p, config)
                    feature = p.parse_text(content, uri=url, **parser_options)
                if feature.source_content is None:
                    feature = evolve(
                        feature,
                        source_content=content,
                        source_media_type=feature.source_media_type or media_type or Mimetype.gherkin_plain.value,
                    )
            except Exception as error:
                if isinstance(error, FeatureSourceError):
                    raise
                raise FeatureSourceError(f"Could not parse feature source {url!r}: {error}") from error
            yield feature


DEFAULT_FEATURE_SUFFIXES = (
    ".feature",
    ".gherkin",
    ".feature.md",
    ".gherkin.md",
    *(format_.suffix for format_ in STRUCT_BDD_FORMATS),
)
DEFAULT_FEATURE_PATTERNS = tuple(f"**/*{suffix}" for suffix in DEFAULT_FEATURE_SUFFIXES)


def _iter_default_feature_paths(root: Path) -> Iterable[Path]:
    """Yield supported feature files recursively with platform-stable suffix matching."""
    for candidate in root.rglob("*"):
        matches_supported_suffix = any(
            candidate.name.casefold().endswith(suffix) for suffix in DEFAULT_FEATURE_SUFFIXES
        )
        if candidate.is_file() and matches_supported_suffix:
            yield candidate


@define
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    feature_paths: list[str | Path] = field(factory=list)
    encoding: str = "utf-8"
    features_base_dir: Path | str | Callable[[Any], Path | str] | None = None
    mimetype: str | None = None
    parser_type: type[ParserProtocol] | None = None
    parser: ParserProtocol | None = None
    parse_args: Any = None

    def _resolve_features_base_dir(self, config: Any = None) -> Path:
        return resolve_feature_sources(config, features_base_dir=self.features_base_dir).features_base_dir

    def _gen_feature_paths(self, features_base_dir: Path) -> Iterable[Path]:
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = (
                    feature_pathlike if feature_pathlike.is_absolute() else features_base_dir / feature_pathlike
                )
                if feature_path.is_dir():
                    yield from _iter_default_feature_paths(feature_path)
                elif feature_path.is_file():
                    yield feature_path
            else:
                raw_str = str(feature_pathlike)
                path_obj = Path(raw_str)
                if path_obj.is_absolute():
                    if path_obj.is_dir():
                        yield from _iter_default_feature_paths(path_obj)
                    elif path_obj.is_file():
                        yield path_obj
                    else:
                        yield from filter(
                            methodcaller("is_file"),
                            path_obj.parent.glob(path_obj.name),
                        )
                elif raw_str in (".", ""):
                    yield from _iter_default_feature_paths(features_base_dir)
                elif any(c in raw_str for c in ("*", "?", "[")):
                    yield from filter(methodcaller("is_file"), features_base_dir.glob(raw_str))
                else:
                    target = features_base_dir / path_obj
                    if target.is_dir():
                        yield from _iter_default_feature_paths(target)
                    elif target.is_file():
                        yield target
                    else:
                        yield from filter(methodcaller("is_file"), features_base_dir.glob(raw_str))

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

    def build_batch_requests(
        self,
        config: Any = None,
        registry: ParserRegistry | None = None,
        feature_paths: Iterable[Path] | None = None,
    ) -> list[BatchFeatureRequest]:
        reg = registry or default_parser_registry
        base_dir = self._resolve_features_base_dir(config)
        seen: set[str] = set()
        requests: list[BatchFeatureRequest] = []

        paths = feature_paths if feature_paths is not None else self._gen_feature_paths(base_dir)
        if feature_paths is None and self.feature_paths and not base_dir.is_dir():
            has_relative_source = any(not Path(str(path)).is_absolute() for path in self.feature_paths)
            if has_relative_source:
                raise FeatureSourceError(
                    f"Local feature root {str(base_dir)!r}, selected by --cuke-features-dir or "
                    "cuke_features_dir, does not exist."
                )
        for feature_path in paths:
            canon_key = normcase(str(feature_path.resolve()))
            if canon_key in seen:
                continue
            seen.add(canon_key)

            uri = self._build_file_uri(base_dir, feature_path)
            p: Any = self.parser
            if p is None:
                if self.parser_type is not None:
                    p = self.parser_type()
                elif self.mimetype is not None:
                    p = reg.get_parser_for_mimetype(self.mimetype)
                    if p is None:
                        p = _parser_from_config_hook(config, feature_path, self.mimetype)
                elif registry is not None:
                    p = reg.get_parser_for_path(feature_path)
                    if p is None:
                        p = _parser_from_config_hook(config, feature_path, None)
                else:
                    p = _parser_from_config_hook(config, feature_path, None)
                    if p is None:
                        p = reg.get_parser_for_path(feature_path)
            p = _resolve_parser_provider(p, config)

            if p is not None:
                parser_options = _parser_backend_options(p, config)
                if isinstance(p, LegacyParserAdapter):
                    parser_options["_pytest_cuke_parse_args"] = self.parse_args
                requests.append(
                    BatchFeatureRequest(
                        path=feature_path,
                        uri=uri,
                        encoding=self.encoding,
                        parser=p,
                        mimetype=self.mimetype,
                        parser_options=tuple(parser_options.items()),
                    )
                )
        return requests

    def resolve_features(self, config: Any = None, registry: ParserRegistry | None = None) -> Iterable[Feature]:
        requests = self.build_batch_requests(config, registry)
        service = get_batch_service(config) if config is not None else None
        if service is not None:
            features = service.resolve_many(requests)
        else:
            features = [
                request.parser.parse(
                    request.path,
                    uri=request.uri,
                    encoding=request.encoding,
                    **dict(request.parser_options),
                )
                for request in requests
            ]

        for feature, request in zip(features, requests, strict=True):
            if _strict_heading_policy_enabled(config):
                enforce_feature_heading_policy(feature, feature.filename or request.uri)
            yield feature


def _strict_heading_policy_enabled(config: Any) -> bool:
    if config is None:
        return False
    try:
        is_strict = config.getoption("cuke_strict")
    except (AttributeError, ValueError):
        is_strict = None
    if is_strict is None:
        try:
            is_strict = config.getini("cuke_strict")
        except (AttributeError, KeyError, ValueError):
            is_strict = False
    return bool(is_strict)

    @staticmethod
    def _resolve_parser_from_hooks(feature_path: Path, config: Any) -> ParserProtocol | None:
        hook = getattr(config, "hook", None)
        if hook is None:
            return None
        mimetype = hook.pytest_bdd_get_mimetype(config=config, path=feature_path)
        if not mimetype:
            return None
        parser = hook.pytest_bdd_get_parser(config=config, mimetype=mimetype)
        if callable(parser):
            return parser()
        return parser


def _parser_backend_options(parser: ParserProtocol, config: Any) -> dict[str, str]:
    if isinstance(parser, (GherkinParser, MarkdownParser)):
        return {"parser_mode": resolve_parser_backend(config).value}
    return {}


__all__ = [
    "FileScenarioLocator",
    "ScenarioLocatorFeatureResolver",
    "ScenarioLocatorFilterMixin",
    "ScenarioLocatorResolver",
    "UrlScenarioLocator",
]
