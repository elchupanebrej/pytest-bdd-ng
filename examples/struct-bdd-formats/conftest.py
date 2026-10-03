from pytest_cuke import given, then


@given("the StructBDD format example is runnable", target_fixture="format_example")
def format_example() -> bool:
    return True


@then("the StructBDD format example passes")
def format_example_passes(format_example: bool) -> None:
    assert format_example is True
