from __future__ import annotations

import pytest

from pytest_cuke.test_groups.config import parse_test_group_configuration


def test_empty_group_order_disables_grouping_without_warnings() -> None:
    config = parse_test_group_configuration(
        order=(),
        default_group="unknown",
        paths=("malformed", "tests/unit/** = missing"),
        barrier_timeout=0,
    )

    assert config.enabled is False
    assert config.order == ()
    assert config.default_group is None
    assert config.path_mappings == ()
    assert config.warnings == ()


def test_configured_groups_drop_duplicates_and_keep_valid_path_mappings() -> None:
    config = parse_test_group_configuration(
        order=("unit", "contract", "unit", "e2e"),
        default_group="missing",
        paths=(
            "tests/contract/** = contract",
            "malformed",
            "tests/unit/** = missing",
            "tests/unit/** = e2e",
        ),
    )

    assert config.enabled is True
    assert config.order == ("unit", "contract", "e2e")
    assert config.default_group == "unit"
    assert [(mapping.pattern, mapping.group) for mapping in config.path_mappings] == [
        ("tests/contract/**", "contract"),
        ("tests/unit/**", "e2e"),
    ]
    assert len(config.warnings) == 4
    assert any("duplicate" in warning.lower() for warning in config.warnings)
    assert any("malformed" in warning for warning in config.warnings)
    assert any("unknown test group" in warning for warning in config.warnings)
    assert any("default" in warning for warning in config.warnings)


def test_order_lines_split_whitespace_delimited_group_names() -> None:
    config = parse_test_group_configuration(order=("unit integration", "e2e"))

    assert config.order == ("unit", "integration", "e2e")


def test_non_positive_barrier_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="cuke_test_group_barrier_timeout"):
        parse_test_group_configuration(order=("unit",), barrier_timeout=0)


def test_barrier_timeout_string_is_parsed_and_invalid_string_is_rejected() -> None:
    config = parse_test_group_configuration(order=("unit",), barrier_timeout="12.5")

    assert config.barrier_timeout == 12.5
    with pytest.raises(ValueError, match="cuke_test_group_barrier_timeout"):
        parse_test_group_configuration(order=("unit",), barrier_timeout="invalid")


def test_relay_address_is_parsed_for_remote_workers() -> None:
    config = parse_test_group_configuration(order=("unit",), relay=" controller:8889 ")

    assert config.relay == ("controller", 8889)


def test_bracketed_ipv6_relay_address_is_parsed_without_brackets() -> None:
    config = parse_test_group_configuration(order=("unit",), relay="[::1]:8889")

    assert config.relay == ("::1", 8889)


def test_empty_relay_keeps_the_local_filesystem_transport() -> None:
    config = parse_test_group_configuration(order=("unit",), relay="")

    assert config.relay is None


@pytest.mark.parametrize(
    "relay",
    ["controller", "controller:", ":8889", "controller:0", "controller:99999", "a:b", "[::1:8889", "[controller]:8889"],
)
def test_invalid_relay_addresses_are_rejected(relay: str) -> None:
    with pytest.raises(ValueError, match="cuke_test_group_relay"):
        parse_test_group_configuration(order=("unit",), relay=relay)


def test_relay_is_ignored_when_group_ordering_is_disabled() -> None:
    config = parse_test_group_configuration(order=(), relay="invalid")

    assert config.relay is None
