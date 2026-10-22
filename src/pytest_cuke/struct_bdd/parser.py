from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from attrs import define

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.mimetypes import STRUCT_BDD_FORMATS
from pytest_cuke.parser import BaseParser, default_parser_registry
from pytest_cuke.struct_bdd.model import Step
from pytest_cuke.struct_bdd.model_builder import StepToFeatureASTBuilder

if TYPE_CHECKING:
    from pytest_cuke.model import Feature


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
        if self.kind is None:
            self.kind = StructBDDKind.YAML.value

    def parse(self, path: Path | str, uri: str | None = None, encoding: str = "utf-8", **kwargs: Any) -> Feature:
        resolved_path = Path(path).resolve()
        kwargs.setdefault("filename", str(resolved_path))
        try:
            return super().parse(path, uri=uri, encoding=encoding, **kwargs)
        except FeatureConcreteParseError:
            raise
        except OSError as err:
            raise FeatureConcreteParseError(
                f"Failed to read structured BDD ({self.kind or 'custom'}): {err}",
                0,
                "",
                str(resolved_path),
            ) from err

    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        *,
        filename: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        try:
            if self.loader is None:
                self.loader = self.build_loader()
            raw = self.loader(content)
            step = Step.model_validate(raw)
            return StepToFeatureASTBuilder(model=step).build_feature(uri=uri or "", filename=filename)
        except Exception as err:
            error_constructor = cast("Callable[..., FeatureConcreteParseError]", FeatureConcreteParseError)
            source_path = filename or uri or "<structured BDD text>"
            raise error_constructor(
                f"Failed to parse structured BDD ({self.kind or 'custom'}): {err}",
                0,
                "",
                source_path,
            ) from err

    def build_loader(self) -> Callable[..., Any]:
        if self.kind == StructBDDKind.YAML.value:
            yaml = self._load_optional("yaml")

            return partial(yaml.load, Loader=yaml.FullLoader)
        if self.kind == StructBDDKind.TOML.value:
            from pytest_cuke.compatibility.tomllib import loads as load_toml

            return load_toml
        if self.kind == StructBDDKind.JSON.value:
            from json import loads as load_json

            return load_json
        if self.kind == StructBDDKind.JSON5.value:
            return cast("Callable[..., Any]", self._load_optional("json5").loads)
        if self.kind == StructBDDKind.HJSON.value:
            return cast("Callable[..., Any]", self._load_optional("hjson").loads)
        if self.kind == StructBDDKind.HOCON.value:
            from json import loads

            pyhocon = self._load_optional("pyhocon")

            def load_hocon(s: str, *args: Any, **kwargs: Any) -> Any:
                return loads(pyhocon.HOCONConverter.to_json(config=pyhocon.ConfigFactory.parse_string(s)))

            return load_hocon

        msg = f"Unsupported struct BDD kind: {self.kind}"
        raise ValueError(msg)

    @staticmethod
    def _load_optional(module_name: str) -> Any:
        try:
            return import_module(module_name)
        except ImportError as error:
            msg = (
                f"Optional StructBDD parser loader '{module_name}' could not be imported. "
                'Install the optional parsers with `pip install "pytest-cuke[struct-bdd]"`. '
                f"Import error: {error}"
            )
            raise ImportError(msg) from error


# Register every supported compound suffix and media type from the shared
# format table. Plain .yaml/.json files intentionally remain outside this
# registry so they cannot be mistaken for features.
for _format in STRUCT_BDD_FORMATS:
    default_parser_registry.register(
        _format.suffix,
        partial(StructBDDParser, kind=_format.kind),
    )
    default_parser_registry.register(
        _format.mimetype.value,
        partial(StructBDDParser, kind=_format.kind),
    )

yaml_parser = StructBDDParser(kind=StructBDDKind.YAML.value)
toml_parser = StructBDDParser(kind=StructBDDKind.TOML.value)
json_parser = StructBDDParser(kind=StructBDDKind.JSON.value)

__all__ = ["StructBDDKind", "StructBDDParser", "json_parser", "toml_parser", "yaml_parser"]
