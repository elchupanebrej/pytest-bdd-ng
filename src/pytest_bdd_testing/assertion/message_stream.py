"""Message stream assertions backed by PyHamcrest."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hamcrest import assert_that, empty, equal_to, has_length

from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule, validate_outcome_mappings
from pytest_bdd.model.message_validation import collect_observed_outcomes

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from cucumber_messages import Envelope as Message


def assert_unique_payload_ids(payloads: Iterable[object]) -> None:
    """Assert that all payload objects have unique string IDs."""
    ids = [getattr(p, "id", "") for p in payloads if isinstance(getattr(p, "id", None), str)]
    assert_that(
        len(ids),
        equal_to(len(set(ids))),
        f"Duplicate payload IDs found: {ids!r}",
    )


def assert_fixed_matrix_mapping_is_valid(
    messages: Iterable[Message],
    mapping_rules: list[OutcomeMappingRule],
) -> None:
    """Assert that a fixed outcome mapping matrix passes all validation checks."""
    observed_outcomes = collect_observed_outcomes(list(messages))
    result = validate_outcome_mappings(mapping_rules, observed_outcomes)
    assert_that(result.status, equal_to("pass"), f"Matrix validation failed: {result}")
    assert_that(result.ambiguous_outcomes, empty())
    assert_that(result.unmapped_outcomes, empty())
    assert_that(result.missing_required_matrix_cases, empty())


def assert_single_output_file(paths: Iterable[Path]) -> Path:
    """Assert exactly one path exists in the given iterable and return it."""
    concrete = [p for p in paths if p.exists()]
    assert_that(
        concrete,
        has_length(1),
        f"Expected exactly 1 output file, found {len(concrete)}: {concrete!r}",
    )
    return concrete[0]
