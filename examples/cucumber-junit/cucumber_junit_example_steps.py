"""Public-facade step definitions used by the Cucumber JUnit example."""

from __future__ import annotations

import json
from typing import Any

from pytest_cuke import given, parsers, then, when


@given("the Cucumber JUnit example prepares a profile", target_fixture="profile")
def prepare_profile() -> dict[str, Any]:
    return {"ready": True}


@given("the Cucumber JUnit example confirms its profile setup")
def confirm_profile_setup(profile: dict[str, Any]) -> None:
    assert profile["ready"] is True


@when("the Cucumber JUnit example receives a profile document")
def receive_profile_document(step: Any, profile: dict[str, Any]) -> None:
    assert step.doc_string is not None
    assert step.doc_string.media_type == "application/json"
    profile["document"] = json.loads(step.doc_string.content)


@when("the Cucumber JUnit example receives profile fields")
def receive_profile_fields(step: Any, profile: dict[str, Any]) -> None:
    assert step.data_table is not None
    profile["fields"] = step.data_table.as_dicts()


@then(parsers.parse('the Cucumber JUnit example accepts "{customer}"'))
def accept_profile(customer: str, profile: dict[str, Any]) -> None:
    assert profile["document"] == {"customer": customer, "active": True}
    assert profile["fields"] == [{"field": "customer", "value": customer}, {"field": "active", "value": "true"}]
