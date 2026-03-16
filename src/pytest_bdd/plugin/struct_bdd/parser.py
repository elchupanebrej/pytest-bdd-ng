from functools import partial
from pathlib import Path
from typing import Any

from attr import attrib, attrs

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash

from .model import Step
from .model_builder import GherkinDocumentBuilder


@attrs
class StructBDDParser(ParserProtocol):
    class KIND(StrEnum):
        HOCON = "hocon"
        HJSON = "hjson"
        JSON = "json"
        JSON5 = "json5"
        TOML = "toml"
        YAML = "yaml"

    kind = attrib(kw_only=True)
    loader = attrib(kw_only=True)

    @kind.default
    def kind_default(self):
        return self.KIND.YAML.value if getattr(self, "loader", None) is None else None

    @loader.default
    def loader_default(self):
        return self.build_loader()

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args,
        **kwargs,
    ) -> tuple[Any, str]:
        _ = config
        encoding = kwargs.pop("encoding", "utf-8")
        mode = kwargs.pop("mode", "r")
        with path.open(mode=mode, encoding=encoding) as feature_file:
            content = feature_file.read()
        filename = str(path.as_posix())
        raw_step = self.loader(content, *args, **kwargs)
        step = Step.model_validate(raw_step)
        gherkin_document = GherkinDocumentBuilder(model=step).build_feature(
            filename,
            uri,
            self.id_generator,
        )  # type: ignore[call-arg]
        return gherkin_document, content

    # TODO make loaders part of public API
    def build_loader(self):
        if self.kind is self.KIND.YAML:
            from yaml import FullLoader
            from yaml import load as load_yaml

            return partial(load_yaml, Loader=FullLoader)
        if self.kind is self.KIND.TOML:
            from pytest_bdd.compatibility.tomllib import loads as load_toml

            return load_toml
        if self.kind is self.KIND.JSON:
            from json import loads as load_json

            return load_json
        if self.kind is self.KIND.JSON5:
            from json5 import loads as load_json5

            return load_json5
        if self.kind is self.KIND.HJSON:
            from hjson import loads as load_hjson

            return load_hjson
        if self.kind is self.KIND.HOCON:
            from json import loads

            from pyhocon import ConfigFactory, HOCONConverter

            def load_hocon(
                s,
                hocon_parse_args=(),
                hocon_parse_kwargs=None,
                hocon_to_json_args=(),
                hocon_to_json_kwargs=None,
                json_args=(),
                json_kwargs=None,
            ):
                hocon_to_json_kwargs = hocon_to_json_kwargs or {}
                hocon_parse_kwargs = hocon_parse_kwargs or {}
                json_kwargs = json_kwargs or {}
                return loads(
                    HOCONConverter.to_json(
                        ConfigFactory.parse_string(s, *hocon_parse_args, **hocon_parse_kwargs),
                        *hocon_to_json_args,
                        **hocon_to_json_kwargs,
                    ),
                    *json_args,
                    **json_kwargs,
                )

            return load_hocon
        return None
