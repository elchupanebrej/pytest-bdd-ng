"""Assertion primitives for pytest-bdd-ng testing."""

from pytest_bdd_testing.assertion.formatter import (
    assert_formatter_output_is_not_mixed_with_pytest_terminal,
    assert_pytest_terminal_reporter_suppressed,
    assert_pytest_terminal_reporter_visible,
)
from pytest_bdd_testing.assertion.message_governance import (
    assert_contains_all,
    assert_non_empty_text,
    assert_unique,
)
from pytest_bdd_testing.assertion.message_stream import (
    assert_fixed_matrix_mapping_is_valid,
    assert_single_output_file,
    assert_unique_payload_ids,
)
