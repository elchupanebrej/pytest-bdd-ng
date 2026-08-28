from __future__ import annotations

from unittest.mock import Mock

from pytest_bdd.util.data_table import data_table_to_dicts


def test_data_table_to_dicts() -> None:
    assert data_table_to_dicts(None) == {}
    row = Mock(cells=[Mock(value="col1"), Mock(value="val1")])
    assert data_table_to_dicts(Mock(rows=[row])) == {"col1": ["val1"]}
