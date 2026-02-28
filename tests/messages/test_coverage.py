from pathlib import Path

from pytest_bdd.model.coverage.inventory import generate_inventory

SCHEMA_DIR = Path(__file__).parent.parent.parent / "messages" / "jsonschema" / "src"


def test_generate_inventory_from_schema():
    inventory = generate_inventory(SCHEMA_DIR)

    # Verify that payload_kinds are extracted from Envelope.json
    assert "testCaseStarted" in inventory.payload_kinds
    assert "testStepFinished" in inventory.payload_kinds

    # Verify some deeply nested fields are extracted correctly
    # e.g., testCaseStarted has fields like 'id', 'testCaseId', 'timestamp.seconds'

    assert ("testCaseStarted", "id") in inventory.fields
    assert inventory.fields["testCaseStarted", "id"].type == "string"

    # Check timestamp which is an object with seconds and nanos
    assert ("testCaseStarted", "timestamp.seconds") in inventory.fields
    assert inventory.fields["testCaseStarted", "timestamp.seconds"].type == "integer"


def test_field_metadata_attributes():
    inventory = generate_inventory(SCHEMA_DIR)

    field_meta = inventory.fields["testCaseStarted", "id"]
    assert field_meta.path == "id"
    assert isinstance(field_meta.is_required, bool)


def test_schema_driven_coverage_validation():
    # Will be implemented alongside the validator
    pass
