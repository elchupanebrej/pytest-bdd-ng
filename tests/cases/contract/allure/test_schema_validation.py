"""Contract tests: validate Allure JSON against committed schema."""

from __future__ import annotations

import json

import jsonschema
import pytest

from pytest_bdd.plugin.allure_cucumber.converter import convert

pytestmark = [pytest.mark.contract]


def test_schema_exists_and_is_valid(allure_schema_path):
    """The committed schema file must be valid JSONSchema draft-2020-12."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_minimal_result_validates(allure_schema_path, sample_valid_result):
    """A minimal valid Allure3 TestResult must validate against the schema."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(sample_valid_result, schema)


def test_minimal_container_validates(allure_schema_path, sample_valid_container):
    """A minimal valid Allure3 Container must validate against the schema."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(sample_valid_container, schema)


def test_malformed_result_rejected(allure_schema_path):
    """A dict missing required 'uuid' field must be rejected by the schema."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    bad_result = {"name": "no uuid"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_result, schema)


def test_invalid_status_rejected(allure_schema_path):
    """A TestResult with an unrecognized status value must be rejected."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    bad_result = {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "status": "not-a-real-status",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_result, schema)


def test_converter_output_validates(allure_schema_path, sample_ndjson, converter_output_dir):
    """Converter output must validate against the canonical Allure3 schema."""
    schema = json.loads(allure_schema_path.read_text(encoding="utf-8"))
    convert(sample_ndjson, converter_output_dir)

    result_files = list(converter_output_dir.glob("*-result.json"))
    container_files = list(converter_output_dir.glob("*-container.json"))

    assert len(result_files) >= 1, "Expected at least one result file"
    assert len(container_files) >= 1, "Expected at least one container file"

    for f in result_files:
        instance = json.loads(f.read_text(encoding="utf-8"))
        jsonschema.validate(instance, schema)

    for f in container_files:
        instance = json.loads(f.read_text(encoding="utf-8"))
        jsonschema.validate(instance, schema)
