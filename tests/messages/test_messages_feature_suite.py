from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from cucumber_messages import (
    Attachment,  # type:ignore[attr-defined]
    AttachmentContentEncoding,  # type:ignore[attr-defined]
    Hook,  # type:ignore[attr-defined]
)
from cucumber_messages import TestStepFinished as CucumberTestStepFinished  # type:ignore[attr-defined]
from deepdiff import DeepDiff  # type:ignore[import-untyped]

from pytest_bdd.model.message_extension import PAYLOAD_KINDS, get_payload_kind, has_single_payload
from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter

from .message_model_coverage import (
    build_expected_coverage_tree,
    build_observed_coverage_tree,
    dump_yaml,
    is_path_populated,
    load_oracle_payload_tree,
)
from .message_stream_assertions import parse_ndjson_messages

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Testdir

ORACLE_PATH = Path(__file__).with_name("oracles") / "messages_model_coverage_oracle.yaml"
MESSAGE_REPORTER_PLUGIN = "pytest_bdd.plugin.gherkin_message_reporter.entrypoint"
MESSAGE_REPORTER_PLUGIN_NAME = "pytest-bdd-gherkin-message-reporter"


def _is_populated(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (bytes, bytearray)):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return bool(value)
    return True


def _build_feature_suite(testdir: Testdir, tmp_path: Path) -> dict[str, list[object]]:
    GherkinMessageReporter.parameter_type_registry.clear()
    GherkinMessageReporter.hook_registry.clear()
    GherkinMessageReporter.hook_registration_registry.clear()

    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
        [pytest]
        markers =
            tag
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        coverage="""\
        @tag
        Feature: message full-surface coverage

          @tag
          Scenario: pass path
            Given A 5 thick line from 10,20,30 to 40,50,60
            And Attach "plain body" as text attachment
            And Attach "binary body" as bytes attachment

          @tag
          Scenario: structured argument path
            Given A table step
              | key | value |
              | foo | bar |
            And A doc string step
              \"\"\"text/plain
              payload text
              \"\"\"

          @tag
          Scenario: fail path
            Given This step fails
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from cucumber_expressions.parameter_type import ParameterType
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        from pytest_bdd import given
        from pytest_bdd.hook import after_tag, around_mark, before_mark, before_tag
        from pytest_bdd.parsers import cucumber_expression


        class Coordinate:
            def __init__(self, x: int, y: int, z: int):
                self.x = x
                self.y = y
                self.z = z

            def __eq__(self, other):
                return (
                    isinstance(other, Coordinate)
                    and self.x == other.x
                    and self.y == other.y
                    and self.z == other.z
                )


        @pytest.fixture
        def parameter_type_registry():
            registry = ParameterTypeRegistry()
            registry.define_parameter_type(
                ParameterType(
                    "coordinate",
                    r"(\\d+),\\s*(\\d+),\\s*(\\d+)",
                    Coordinate,
                    lambda x, y, z: Coordinate(int(x), int(y), int(z)),
                    True,
                    False,
                )
            )
            return registry


        @before_tag("@tag", name="before")
        def _before_tag(request):
            ...


        @before_mark("tag")
        def _before_mark(request):
            ...


        @after_tag("@tag", name="after")
        def _after_tag(request):
            ...


        @around_mark("tag", "around")
        def _around_mark(request):
            yield


        @given(
            cucumber_expression("A {int} thick line from {coordinate} to {coordinate}"),
            anonymous_group_names=["thick", "start", "end"],
        )
        def _cucumber_expression(thick, start, end):
            assert int(thick) == 5
            assert start == Coordinate(10, 20, 30)
            assert end == Coordinate(40, 50, 60)


        @given('Attach "{value}" as text attachment')
        def _attach_text(attach, value):
            attach(value, media_type="text/plain;charset=UTF-8")


        @given('Attach "{value}" as bytes attachment')
        def _attach_bytes(attach, value):
            attach(value.encode("utf-8"), file_name="payload.bin")


        @given("A table step")
        def _table_step():
            ...


        @given("A doc string step")
        def _doc_string_step():
            ...


        @given("This step fails")
        def _fail():
            raise RuntimeError("boom")
        """,
    )

    ndjson_path = tmp_path / "messages-feature-suite.ndjson"
    result = testdir.runpytest(
        "-p",
        f"no:{MESSAGE_REPORTER_PLUGIN_NAME}",
        "-p",
        MESSAGE_REPORTER_PLUGIN,
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=2, failed=1)

    messages = parse_ndjson_messages(ndjson_path)
    assert messages, "Expected at least one message envelope."
    assert all(has_single_payload(message) for message in messages)

    payloads_by_kind: dict[str, list[object]] = defaultdict(list)
    for message in messages:
        payload_kind = get_payload_kind(message)
        assert payload_kind is not None
        payloads_by_kind[payload_kind].append(getattr(message, payload_kind))
    return payloads_by_kind


def test_feature_driven_message_suite_matches_yaml_oracle(testdir: Testdir, tmp_path: Path) -> None:
    payloads_by_kind = _build_feature_suite(testdir, tmp_path)
    oracle_payload_tree = load_oracle_payload_tree(ORACLE_PATH)

    missing_in_oracle = sorted(set(PAYLOAD_KINDS).difference(set(oracle_payload_tree)))
    extra_in_oracle = sorted(set(oracle_payload_tree).difference(set(PAYLOAD_KINDS)))
    assert not missing_in_oracle, f"Oracle is missing payload kinds: {missing_in_oracle}"
    assert not extra_in_oracle, f"Oracle has unknown payload kinds: {extra_in_oracle}"

    observed_tree = {
        payload_kind: build_observed_coverage_tree(oracle_payload_tree[payload_kind], payloads_by_kind[payload_kind])
        for payload_kind in PAYLOAD_KINDS
    }
    expected_tree = {
        payload_kind: build_expected_coverage_tree(oracle_payload_tree[payload_kind]) for payload_kind in PAYLOAD_KINDS
    }

    observed_path = tmp_path / "messages-model-coverage.observed.yaml"
    expected_path = tmp_path / "messages-model-coverage.expected.yaml"
    dump_yaml(observed_path, {"payloads": observed_tree})
    dump_yaml(expected_path, {"payloads": expected_tree})

    diff = DeepDiff(expected_tree, observed_tree, ignore_order=True)
    assert not diff, (
        "Message model coverage tree does not match oracle. "
        f"expected={expected_path}, observed={observed_path}, diff={diff.to_dict()}"
    )


def test_feature_driven_message_suite_covers_optional_field_depth_and_outcomes(
    testdir: Testdir,
    tmp_path: Path,
) -> None:
    payloads_by_kind = _build_feature_suite(testdir, tmp_path)

    hook_payloads = [payload for payload in payloads_by_kind["hook"] if isinstance(payload, Hook)]
    assert any(_is_populated(hook_payload.name) for hook_payload in hook_payloads)
    assert any(hook_payload.name is None for hook_payload in hook_payloads)

    attachment_payloads = [payload for payload in payloads_by_kind["attachment"] if isinstance(payload, Attachment)]
    assert any(_is_populated(attachment_payload.file_name) for attachment_payload in attachment_payloads)
    assert any(_is_populated(attachment_payload.test_step_id) for attachment_payload in attachment_payloads)

    attachment_encodings = {
        AttachmentContentEncoding(attachment_payload.content_encoding) for attachment_payload in attachment_payloads
    }
    assert AttachmentContentEncoding.identity in attachment_encodings
    assert AttachmentContentEncoding.base64 in attachment_encodings

    step_finished_payloads = [
        payload for payload in payloads_by_kind["test_step_finished"] if isinstance(payload, CucumberTestStepFinished)
    ]
    step_statuses = {
        str(getattr(payload.test_step_result, "status", "")).split(".")[-1].lower()
        for payload in step_finished_payloads
    }
    assert {"passed", "failed"}.issubset(step_statuses)

    assert is_path_populated(
        payloads_by_kind["pickle"],
        ("steps", "argument", "data_table", "rows", "cells", "value"),
    )
    assert is_path_populated(
        payloads_by_kind["pickle"],
        ("steps", "argument", "doc_string", "content"),
    )
    assert is_path_populated(
        payloads_by_kind["gherkin_document"],
        ("feature", "children", "scenario", "steps", "data_table", "rows", "cells", "value"),
    )
    assert is_path_populated(
        payloads_by_kind["gherkin_document"],
        ("feature", "children", "scenario", "steps", "doc_string", "content"),
    )
