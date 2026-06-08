# init: allow  # init: no-check
"""Testing helpers for cucumber formatters in pytest-bdd-ng."""

from pytest_bdd_testing.cucumber_formatters.registry import (
    assert_formatter_output_is_not_mixed_with_pytest_terminal,
    assert_pytest_terminal_reporter_suppressed,
    assert_pytest_terminal_reporter_visible,
    build_sample_suite,
    enable_fake_node_capture,
    expected_formatter_output,
    expected_formatter_output_lines,
    expected_formatter_visible_line,
    install_formatter_hook_registry,
    read_fake_formatter_telemetry,
    read_fake_node_captures,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
    with_pytester_terminal_capture_disabled,
)
from pytest_bdd_testing.cucumber_formatters.rendering import (
    install_fake_node,
    materialize_fake_node_runtime,
    materialize_live_formatter_runtime,
)
