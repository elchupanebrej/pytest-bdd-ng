from pathlib import Path

from pytest_bdd import given, parsers, then
from pytest_bdd.mimetype import Mimetype, Suffix, gherkin_suffixes, struct_bdd_suffixes


@given(parsers.parse("File extension is {ext}"), target_fixture="file_path")
def file_extension(testdir, ext):
    content = ""
    file_path = testdir.makefile(ext, test=content)
    return Path(file_path)


@then(parsers.parse("Mimetype resolves to {mimetype}"))
def mimetype_resolves_to(file_path, mimetype):
    # Depending on how the file mimetype is mapped.
    # In pytest_bdd it's typically deduced from the suffix.
    ext = file_path.suffix
    matched = None
    for suf in gherkin_suffixes:
        if ext == suf.value:
            if suf == Suffix.gherkin_markdown:
                matched = Mimetype.gherkin_markdown
            else:
                matched = Mimetype.gherkin_plain
    for suf in struct_bdd_suffixes:
        if ext == suf.value:
            if suf == Suffix.struct_bdd_yaml:
                matched = Mimetype.struct_bdd_yaml
            elif suf == Suffix.struct_bdd_json:
                matched = Mimetype.struct_bdd_json
            elif suf == Suffix.struct_bdd_hocon:
                matched = Mimetype.struct_bdd_hocon
            elif suf == Suffix.struct_bdd_toml:
                matched = Mimetype.struct_bdd_toml
    assert matched and matched.value == mimetype


@then(parsers.parse("Suffix resolves to {suffix}"))
def suffix_resolves_to(file_path, suffix):
    ext = file_path.suffix
    matched = None
    for suf in [*gherkin_suffixes, *struct_bdd_suffixes]:
        if ext == suf.value:
            matched = suf
            break
    assert matched and matched.value == suffix


@given("Mimetype hook override is set")
def mimetype_hook_override(monkeypatch):
    monkeypatch.setattr("pytest_bdd.mimetype.get_mimetype", lambda x: Mimetype.gherkin_plain)
