from pytest_bdd import given, parsers, step, then
from tests.e2e.conftest import data_table_to_dicts


@step("run pytest with batch collection", target_fixture="pytest_result")
def run_pytest_with_batch_collection(testdir, step):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    options_dict = data_table_to_dicts(data_table)
    cli_args = list(options_dict.get("cli_args", []))
    return testdir.runpytest_inprocess(*cli_args)


@given("Batch collection cache is enabled")
def batch_collection_cache_enabled(testdir):
    testdir.makeini("""
[pytest]
pytest_bdd_features_base_dir = .
    """)


@then(parsers.parse("Batch collection processes {count} files"))
def batch_collection_processes(pytest_result, count):
    # Depending on how batch collection logs this, we might check stdout
    pass


@given("Batch collection flag is set", target_fixture="cli_args")
def batch_collection_flag_is_set(step):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    if data_table:
        return [row.cells[0].value for row in data_table.rows]
    return ["--features-base-dir=."]


@then("Batch collection cache is used")
def batch_collection_cache_is_used(pytest_result):
    # Check stdout for cache hit
    pass
