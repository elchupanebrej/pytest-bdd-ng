from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Protocol, cast

from attrs import define, field
from cucumber_messages import GherkinDocument  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash

from .model import Step
from .model_builder import GherkinDocumentBuilder


class Loader(Protocol):
    def __call__(self, content: str) -> object: ...


@define
class StructBDDParser(ParserProtocol):
    class KIND(StrEnum):
        """Supported struct BDD source formats."""

        HOCON = "hocon"
        HJSON = "hjson"
        JSON = "json"
        JSON5 = "json5"
        TOML = "toml"
        YAML = "yaml"

    kind: KIND | str | None = field(kw_only=True)
    loader: Loader | None = field(kw_only=True)

    @kind.default
    def kind_default(self) -> str | None:
        return self.KIND.YAML.value if getattr(self, "loader", None) is None else None

    @loader.default
    def loader_default(self) -> Loader | None:
        return self.build_loader()

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> tuple[GherkinDocument, str]:
        _ = config
        encoding = cast(str, kwargs.pop("encoding", "utf-8"))
        mode = cast(str, kwargs.pop("mode", "r"))
        with path.open(mode=mode, encoding=encoding) as feature_file:
            content = cast(str, feature_file.read())
        filename = str(path.as_posix())
        raw_step = cast(Loader, self.loader)(content, *args, **kwargs)
        step = Step.model_validate(raw_step)
        gherkin_document = GherkinDocumentBuilder(model=step).build_feature(
            filename,
            uri,
            self.id_generator,
        )
        return gherkin_document, content

    # TODO: make loaders part of public API
    def build_loader(self) -> Loader | None:
        if self.kind is self.KIND.YAML:
            from yaml import FullLoader
            from yaml import load as load_yaml

            return cast(Loader, partial(load_yaml, Loader=FullLoader))
        if self.kind is self.KIND.TOML:
            from pytest_bdd.compatibility.tomllib import loads as load_toml

            return cast(Loader, load_toml)
        if self.kind is self.KIND.JSON:
            from json import loads as load_json

            return cast(Loader, load_json)
        if self.kind is self.KIND.JSON5:
            from json5 import loads as load_json5

            return cast(Loader, load_json5)
        if self.kind is self.KIND.HJSON:
            from hjson import loads as load_hjson

            return cast(Loader, load_hjson)
        if self.kind is self.KIND.HOCON:
            from json import loads

            from pyhocon import ConfigFactory, HOCONConverter

            def load_hocon(
                s: str,
                hocon_parse_args: Sequence[object] = (),
                hocon_parse_kwargs: Mapping[str, object] | None = None,
                hocon_to_json_args: Sequence[object] = (),
                hocon_to_json_kwargs: Mapping[str, object] | None = None,
                json_args: Sequence[object] = (),
                json_kwargs: Mapping[str, object] | None = None,
            ) -> object:
                hocon_to_json_kwargs = hocon_to_json_kwargs or {}
                hocon_parse_kwargs = hocon_parse_kwargs or {}
                json_kwargs = json_kwargs or {}
                return cast(
                    object,
                    loads(
                        HOCONConverter.to_json(
                            ConfigFactory.parse_string(s, *hocon_parse_args, **hocon_parse_kwargs),
                            *hocon_to_json_args,
                            **hocon_to_json_kwargs,
                        ),
                        *json_args,
                        **json_kwargs,  # type: ignore[arg-type]
                    ),
                )

            return cast(Loader, load_hocon)
        return None
