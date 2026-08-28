from __future__ import annotations

import mimetypes

from pytest_bdd.mimetype import (
    Mimetype,
    Suffix,
    gherkin_suffixes,
    link_suffixes,
    register_mimetypes,
    struct_bdd_suffixes,
)


def test_mimetype_and_suffix_enums() -> None:
    assert Mimetype.gherkin_plain == "text/x.cucumber.gherkin+plain"
    assert Mimetype.gherkin_markdown == "text/x.cucumber.gherkin+markdown"
    assert Mimetype.struct_bdd_yaml == "application/x.struct_bdd+yaml"
    assert Suffix.feature == ".feature"
    assert Suffix.gherkin in gherkin_suffixes
    assert Suffix.struct_bdd in struct_bdd_suffixes
    assert Suffix.url in link_suffixes


def test_mimetypes_registration() -> None:
    register_mimetypes()
    assert mimetypes.guess_type("test.feature")[0] == Mimetype.gherkin_plain
    assert mimetypes.guess_type("test.gherkin")[0] == Mimetype.gherkin_plain
    assert mimetypes.guess_type("test.toml")[0] == Mimetype.toml
    assert mimetypes.guess_type("test.yaml")[0] == Mimetype.yaml
