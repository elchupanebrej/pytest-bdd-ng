from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_bdd.script import sync_messages_contract_schemas

if TYPE_CHECKING:
    from pathlib import Path


def _write_schema(schema_dir: Path, name: str, content: str) -> None:
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / name).write_text(content, encoding="utf-8")


def test_collect_schema_drift_reports_missing_changed_and_extra_files(tmp_path: Path) -> None:
    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    _write_schema(expected, "Envelope.schema.json", '{"expected": true}\n')
    _write_schema(expected, "Source.schema.json", '{"source": true}\n')
    _write_schema(actual, "Envelope.schema.json", '{"actual": true}\n')
    _write_schema(actual, "Extra.schema.json", '{"extra": true}\n')

    drift = sync_messages_contract_schemas.collect_schema_drift(expected, actual)

    assert drift == (
        "changed: Envelope.schema.json",
        "missing: Source.schema.json",
        "extra: Extra.schema.json",
    )


def test_check_mode_exits_when_generated_schemas_are_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    _write_schema(expected, "Envelope.schema.json", '{"expected": true}\n')
    _write_schema(actual, "Envelope.schema.json", '{"actual": true}\n')

    def fetch_schema_tree(destination: Path) -> None:
        sync_messages_contract_schemas.copy_schema_tree(expected, destination)

    monkeypatch.setattr(sync_messages_contract_schemas, "fetch_schema_tree", fetch_schema_tree)

    with pytest.raises(SystemExit) as exc_info:
        sync_messages_contract_schemas.main(["--check", "--schema-path", str(actual)])

    assert exc_info.value.code == 1


def test_check_mode_succeeds_when_generated_schemas_are_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    _write_schema(expected, "Envelope.schema.json", '{"expected": true}\n')
    _write_schema(actual, "Envelope.schema.json", '{"expected": true}\n')

    def fetch_schema_tree(destination: Path) -> None:
        sync_messages_contract_schemas.copy_schema_tree(expected, destination)

    monkeypatch.setattr(sync_messages_contract_schemas, "fetch_schema_tree", fetch_schema_tree)

    sync_messages_contract_schemas.main(["--check", "--schema-path", str(actual)])
