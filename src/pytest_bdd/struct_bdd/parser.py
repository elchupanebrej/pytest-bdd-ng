from __future__ import annotations

from collections.abc import Callable  # noqa: TCH003
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any

from attrs import define

from pytest_bdd.exceptions import FeatureConcreteParseError
from pytest_bdd.parser import BaseParser, default_parser_registry
from pytest_bdd.struct_bdd.model import Step
from pytest_bdd.struct_bdd.model_builder import StepToFeatureASTBuilder

if TYPE_CHECKING:
    from pytest_bdd.model import Feature


class StructBDDKind(str, Enum):
    YAML = "yaml"
    TOML = "toml"
    JSON = "json"
    JSON5 = "json5"
    HJSON = "hjson"
    HOCON = "hocon"


@define
class StructBDDParser(BaseParser):
    KIND = StructBDDKind
    kind: str | None = None
    loader: Callable[..., Any] | None = None

    def __attrs_post_init__(self) -> None:
        if self.loader is None:
            if self.kind is None:
                self.kind = StructBDDKind.YAML.value
            self.loader = self.build_loader()

    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        *,
        filename: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        try:
            assert self.loader is not None
            raw = self.loader(content)
            step = Step.model_validate(raw)
            return StepToFeatureASTBuilder(model=step).build_feature(uri=uri or "", filename=filename)
        except Exception as err:
            raise FeatureConcreteParseError(
                f"Failed to parse structured BDD ({self.kind or 'custom'}): {err}",
                filename=filename,
                uri=uri,
            ) from err

    def build_loader(self) -> Callable[..., Any]:
        if self.kind == StructBDDKind.YAML.value:
            from yaml import FullLoader
            from yaml import load as load_yaml

            return partial(load_yaml, Loader=FullLoader)
        if self.kind == StructBDDKind.TOML.value:
            from pytest_bdd.compatibility.tomllib import loads as load_toml

            return load_toml
        if self.kind == StructBDDKind.JSON.value:
            from json import loads as load_json

            return load_json
        if self.kind == StructBDDKind.JSON5.value:
            from json5 import loads as load_json5

            return load_json5
        if self.kind == StructBDDKind.HJSON.value:
            from hjson import loads as load_hjson

            return load_hjson
        if self.kind == StructBDDKind.HOCON.value:
            from json import loads

            from pyhocon import ConfigFactory, HOCONConverter

            def load_hocon(s: str, *args: Any, **kwargs: Any) -> Any:
                return loads(HOCONConverter.to_json(config=ConfigFactory.parse_string(s)))

            return load_hocon

        msg = f"Unsupported struct BDD kind: {self.kind}"
        raise ValueError(msg)


# Register default parsers
yaml_parser = StructBDDParser(kind=StructBDDKind.YAML.value)
toml_parser = StructBDDParser(kind=StructBDDKind.TOML.value)
json_parser = StructBDDParser(kind=StructBDDKind.JSON.value)

for _key in [".bdd.yaml", ".bdd.yml", ".yaml", ".yml", "application/x-yaml", "text/yaml"]:
    default_parser_registry.register(_key, yaml_parser)

for _key in [".bdd.toml", ".toml", "application/toml"]:
    default_parser_registry.register(_key, toml_parser)

for _key in [".bdd.json", ".json", "application/json"]:
    default_parser_registry.register(_key, json_parser)

__all__ = ["StructBDDKind", "StructBDDParser", "json_parser", "toml_parser", "yaml_parser"]
