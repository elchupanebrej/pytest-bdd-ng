import mimetypes

from pytest_bdd.compatibility.enum import StrEnum


class Mimetype(StrEnum):
    gherkin_plain = "text/x.cucumber.gherkin+plain"
    gherkin_markdown = "text/x.cucumber.gherkin+markdown"
    struct_bdd_yaml = "application/x.struct_bdd+yaml"
    struct_bdd_hocon = "application/x.struct_bdd+hocon"
    struct_bdd_json5 = "application/x.struct_bdd+json5"
    struct_bdd_json = "application/x.struct_bdd+json"
    struct_bdd_hjson = "application/x.struct_bdd+hjson"
    struct_bdd_toml = "application/x.struct_bdd+toml"

    python = "text/x-python"

    markdown = "text/markdown"
    yaml = "application/x-yaml"
    hocon = "application/x-hocon"
    toml = "text/toml"
    json = "application/json"
    json5 = "application/json5"
    hjson = "application/x-hjson"


class Suffix(StrEnum):
    gherkin = ".gherkin"
    feature = ".feature"
    struct_bdd = ".bdd"
    url = ".url"
    desktop = ".desktop"
    webloc = ".webloc"
    markdown = ".md"
    yaml = ".yaml"
    yml = ".yml"
    ndjson = ".ndjson"
    hocon = ".hocon"
    toml = ".toml"
    hjson = ".hjson"
    json5 = ".json5"


gherkin_suffixes = {Suffix.gherkin, Suffix.feature}
struct_bdd_suffixes = {Suffix.struct_bdd}
link_suffixes = {Suffix.url, Suffix.desktop, Suffix.webloc}

mimetype_suffix_pairs = [
    (Mimetype.gherkin_plain, Suffix.gherkin),
    (Mimetype.gherkin_plain, Suffix.feature),
    (Mimetype.markdown, Suffix.markdown),
    (Mimetype.yaml, Suffix.yaml),
    (Mimetype.yaml, Suffix.yml),
    (Mimetype.hocon, Suffix.hocon),
    (Mimetype.toml, Suffix.toml),
    (Mimetype.hjson, Suffix.hjson),
    (Mimetype.json5, Suffix.json5),
]

for mimetype, suffix in mimetype_suffix_pairs:
    mimetypes.add_type(str(mimetype), str(suffix))
