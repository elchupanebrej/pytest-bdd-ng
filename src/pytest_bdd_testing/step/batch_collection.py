from pytest_bdd import given, parsers, then


def _merge_pytest_ini_options(testdir, **options: str) -> None:
    ini_path = testdir.tmpdir.join("pytest.ini")
    existing = ini_path.read() if ini_path.check(file=1) else "[pytest]\n"
    lines = [line for line in existing.splitlines() if line.strip()]
    if not lines or lines[0].strip() != "[pytest]":
        lines.insert(0, "[pytest]")
    option_names = set(options)
    kept = [lines[0], *[line for line in lines[1:] if line.split("=", 1)[0].strip() not in option_names]]
    kept.extend(f"{key} = {value}" for key, value in options.items())
    ini_path.write("\n".join(kept) + "\n")


@given("Batch collection cache is enabled")
def batch_collection_cache_enabled(testdir) -> None:
    _merge_pytest_ini_options(testdir, bdd_features_base_dir=".")


@then(parsers.parse("Batch collection processes {count} files"))
def batch_collection_processes(pytest_result, count) -> None:
    pytest_result.assert_outcomes(passed=int(count))


@then("Batch collection cache is used")
def batch_collection_cache_is_used(pytest_result, testdir) -> None:
    pytest_result.assert_outcomes(passed=3)
    second_result = testdir.runpytest_inprocess()
    second_result.assert_outcomes(passed=3)
    assert testdir.tmpdir.join(".pytest_cache").check(dir=1)


@then("Batch collection processes many scenarios correctly")
def batch_collection_processes_many(pytest_result) -> None:
    """Verify batch collection discovers all scenarios."""
    stdout = pytest_result.stdout.str()
    assert "5 tests collected" in stdout or "collected 5 items" in stdout, stdout


@given("Batch collection is disabled")
def batch_collection_disabled(testdir) -> None:
    _merge_pytest_ini_options(testdir, bdd_batch_collect="false", bdd_features_base_dir=".")


@given("Batch collection is enabled")
def batch_collection_enabled(testdir) -> None:
    _merge_pytest_ini_options(testdir, bdd_features_base_dir=".")
