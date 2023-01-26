from contextlib import suppress
from functools import partial
from pathlib import Path

from pytest import Config

from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.struct_bdd.parser import StructBDDParser


class StructBDDPlugin:
    extension_to_mimetype = {
        StructBDDParser.KIND.YAML: Mimetype.struct_bdd_yaml,
        StructBDDParser.KIND.HOCON: Mimetype.struct_bdd_hocon,
        StructBDDParser.KIND.JSON5: Mimetype.struct_bdd_json5,
        StructBDDParser.KIND.JSON: Mimetype.struct_bdd_json,
        StructBDDParser.KIND.HJSON: Mimetype.struct_bdd_hjson,
        StructBDDParser.KIND.TOML: Mimetype.struct_bdd_toml,
    }

    def pytest_bdd_get_parser(self, config: Config, mimetype: Mimetype):
        with suppress(KeyError):
            return partial(
                StructBDDParser,
                kind={
                    Mimetype.struct_bdd_yaml: StructBDDParser.KIND.YAML.value,
                    Mimetype.struct_bdd_hocon: StructBDDParser.KIND.HOCON.value,
                    Mimetype.struct_bdd_json5: StructBDDParser.KIND.JSON5.value,
                    Mimetype.struct_bdd_json: StructBDDParser.KIND.JSON.value,
                    Mimetype.struct_bdd_hjson: StructBDDParser.KIND.HJSON.value,
                    Mimetype.struct_bdd_toml: StructBDDParser.KIND.TOML.value,
                }[mimetype],
            )

    def pytest_bdd_get_mimetype(self, config: Config, path: Path):
        for extension_suffix, mimetype in self.extension_to_mimetype.items():
            if str(path).endswith(f".bdd.{extension_suffix.value}"):
                return mimetype, None
