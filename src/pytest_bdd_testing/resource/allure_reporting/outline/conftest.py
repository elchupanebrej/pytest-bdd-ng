from pytest_bdd import given


@given("value one step")
@given("value two step")
def _value() -> None:
    pass
