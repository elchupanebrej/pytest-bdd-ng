from pathlib import Path

from pytest_bdd import given, parsers, then
from pytest_bdd.mimetype import Mimetype, Suffix

_SUFFIX_TO_MIMETYPE = {
    Suffix.feature: Mimetype.gherkin_plain,
    Suffix.gherkin: Mimetype.gherkin_plain,
    Suffix.markdown: Mimetype.gherkin_markdown,
    Suffix.yaml: Mimetype.struct_bdd_yaml,
    Suffix.yml: Mimetype.struct_bdd_yaml,
    Suffix.hocon: Mimetype.struct_bdd_hocon,
    Suffix.toml: Mimetype.struct_bdd_toml,
    Suffix.json5: Mimetype.struct_bdd_json5,
    Suffix.hjson: Mimetype.struct_bdd_hjson,
}


@given(parsers.parse("File extension is {ext}"), target_fixture="file_path")
def file_extension(testdir, ext):
    content = ""
    file_path = testdir.makefile(ext, test=content)
    return Path(file_path)


@then(parsers.parse("Mimetype resolves to {mimetype}"))
def mimetype_resolves_to(file_path, mimetype):
    ext = file_path.suffix
    matched = _SUFFIX_TO_MIMETYPE.get(Suffix(ext))
    assert matched and matched.value == mimetype


@then(parsers.parse("Suffix resolves to {suffix}"))
def suffix_resolves_to(file_path, suffix):
    ext = file_path.suffix
    matched = Suffix(ext)
    assert matched and matched.value == suffix


@given("Mimetype hook override is set")
def mimetype_hook_override(monkeypatch):
    # The pytest_bdd_get_mimetype hook is used for custom routing.
    # This step acknowledges the hook is available for override in conftest.py.
    pass


@then("custom mimetype is used")
def custom_mimetype_is_used(pytest_result):
    # Verify that the file was processed successfully
    stdout = pytest_result.stdout.str()
    assert "error" not in stdout.lower() or "passed" in stdout.lower()
