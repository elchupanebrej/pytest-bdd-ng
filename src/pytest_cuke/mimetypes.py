from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Mimetype(Enum):
    gherkin_plain = "text/x.cucumber.gherkin+plain"
    markdown = "text/x.cucumber.gherkin+markdown"
    struct_bdd_yaml = "application/x.struct_bdd+yaml"
    struct_bdd_hocon = "application/x.struct_bdd+hocon"
    struct_bdd_json5 = "application/x.struct_bdd+json5"
    struct_bdd_json = "application/x.struct_bdd+json"
    struct_bdd_hjson = "application/x.struct_bdd+hjson"
    struct_bdd_toml = "application/x.struct_bdd+toml"
    python = "text/x-python"


@dataclass(frozen=True)
class StructBDDFormat:
    """One supported structured-BDD file suffix and its parser metadata."""

    suffix: str
    mimetype: Mimetype
    kind: str


# Keep suffixes, parser kinds, and hook media types together so discovery and
# parser selection cannot drift apart. Order does not affect matching; callers
# use longest-suffix matching explicitly.
STRUCT_BDD_FORMATS = (
    StructBDDFormat(".bdd.yaml", Mimetype.struct_bdd_yaml, "yaml"),
    StructBDDFormat(".bdd.yml", Mimetype.struct_bdd_yaml, "yaml"),
    StructBDDFormat(".bdd.hocon", Mimetype.struct_bdd_hocon, "hocon"),
    StructBDDFormat(".bdd.json5", Mimetype.struct_bdd_json5, "json5"),
    StructBDDFormat(".bdd.json", Mimetype.struct_bdd_json, "json"),
    StructBDDFormat(".bdd.hjson", Mimetype.struct_bdd_hjson, "hjson"),
    StructBDDFormat(".bdd.toml", Mimetype.struct_bdd_toml, "toml"),
    StructBDDFormat(".bdd", Mimetype.struct_bdd_yaml, "yaml"),
)


def struct_bdd_format_for_path(path: str | Path) -> StructBDDFormat | None:
    """Return the longest matching StructBDD suffix, without case sensitivity."""
    name = Path(path).name.casefold()
    for format_ in sorted(STRUCT_BDD_FORMATS, key=lambda value: len(value.suffix), reverse=True):
        if name.endswith(format_.suffix):
            return format_
    return None


def struct_bdd_format_for_mimetype(mimetype: str) -> StructBDDFormat | None:
    """Return StructBDD metadata for a supported media type."""
    return next((format_ for format_ in STRUCT_BDD_FORMATS if format_.mimetype.value == mimetype), None)
