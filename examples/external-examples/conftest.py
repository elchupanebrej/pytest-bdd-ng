from pytest import fixture

from pytest_cuke import given, parsers, then, when


@fixture
def lookup_state():
    return {"ready": True}


@given("the user lookup service is ready", target_fixture="lookup_ready")
def lookup_service(lookup_state):
    assert lookup_state["ready"]
    return lookup_state


@when(parsers.parse("I look up user {name} with tier {tier}"), target_fixture="found_user")
def lookup_user(lookup_ready, name, tier):
    return {"name": name, "tier": tier, "service": lookup_ready}


@then(parsers.parse("the found user is {name} with tier {tier}"))
def check_found_user(found_user, name, tier):
    assert found_user["name"] == name
    assert found_user["tier"] == tier
    assert found_user["service"]["ready"]
