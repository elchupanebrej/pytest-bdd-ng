import pytest
from pytest_bdd import given, parsers, step, then

from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

if not STRUCT_BDD_INSTALLED:
    pytest.skip("StructBDD not installed", allow_module_level=True)


@given(parsers.parse("StructBDD format is {format}"), target_fixture="struct_bdd_file")
def struct_bdd_format(testdir, format):
    content = ""
    if format == "yaml":
        content = "Name: StructBDD Feature"
        return testdir.makefile(".bdd.yaml", struct=content)
    elif format == "json":
        content = '{"Name": "StructBDD Feature"}'
        return testdir.makefile(".bdd.json", struct=content)
    elif format == "hocon":
        content = 'Name = "StructBDD Feature"'
        return testdir.makefile(".bdd.hocon", struct=content)
    elif format == "toml":
        content = 'Name = "StructBDD Feature"'
        return testdir.makefile(".bdd.toml", struct=content)
    return testdir.makefile(".bdd.yaml", struct="Name: Default")


@given("StructBDD parse error occurs", target_fixture="struct_bdd_file")
def struct_bdd_parse_error(testdir):
    content = "Invalid StructBDD: [}"
    return testdir.makefile(".bdd.yaml", struct=content)


@then(parsers.parse("StructBDD deserialization fails with {error}"))
def struct_bdd_deserialization_fails(pytest_result, error):
    stdout = pytest_result.stdout.str()
    assert error in stdout


@step("run pytest with StructBDD feature", target_fixture="pytest_result")
def run_pytest_struct_bdd(testdir, struct_bdd_file):
    return testdir.runpytest_inprocess("--features", str(struct_bdd_file))
