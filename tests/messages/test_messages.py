import json
from collections.abc import Iterable
from functools import partial
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, cast

import pytest
from cucumber_messages import (  # type:ignore[attr-defined]  # type:ignore[attr-defined]  # type:ignore[attr-defined]  # type:ignore[attr-defined]
    Attachment,
    AttachmentContentEncoding,
    GherkinDocument,
    Hook,
    HookType,
    Meta,
    ParameterType,
    Pickle,
    Source,
    StepDefinition,
)
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import (
    ParseError as _ParseError,
)
from cucumber_messages import (
    Suggestion as _Suggestion,
)
from cucumber_messages import TestCase as _TestCase  # type:ignore[attr-defined]
from cucumber_messages import TestCaseFinished as _TestCaseFinished  # type:ignore[attr-defined]
from cucumber_messages import TestCaseStarted as _TestCaseStarted  # type:ignore[attr-defined]
from cucumber_messages import TestRunFinished as _TestRunFinished  # type:ignore[attr-defined]
from cucumber_messages import TestRunStarted as _TestRunStarted  # type:ignore[attr-defined]
from cucumber_messages import TestStepFinished as _TestStepFinished  # type:ignore[attr-defined]
from cucumber_messages import TestStepStarted as _TestStepStarted  # type:ignore[attr-defined]
from cucumber_messages import (
    UndefinedParameterType as _UndefinedParameterType,
)
from pydantic import ValidationError

from pytest_bdd.model.message_converter import envelope_from_dict, message_converter
from pytest_bdd.util.toolz_extra import flip

if TYPE_CHECKING:  # pragma: nocover
    from pytest_bdd.compatibility.pytest import Testdir

samples_path = Path(__file__).parent.parent.parent / "compatibility-kit/devkit/samples"
MESSAGE_REPORTER_PLUGIN = "pytest_bdd.plugin.gherkin_message_reporter.entrypoint"
MESSAGE_REPORTER_PLUGIN_NAME = "pytest-bdd-gherkin-message-reporter"


def runpytest_with_message_reporter(testdir: "Testdir", *args: str):
    return testdir.runpytest(
        "-p",
        f"no:{MESSAGE_REPORTER_PLUGIN_NAME}",
        "-p",
        MESSAGE_REPORTER_PLUGIN,
        *args,
    )


def unfold_message(message: Message):
    unfoldable_attrs = [
        "attachment",
        "external_attachment",
        "gherkin_document",
        "hook",
        "meta",
        "parameter_type",
        "parse_error",
        "pickle",
        "source",
        "step_definition",
        "suggestion",
        "test_case",
        "test_case_finished",
        "test_case_started",
        "test_run_finished",
        "test_run_hook_finished",
        "test_run_hook_started",
        "test_run_started",
        "test_step_finished",
        "test_step_started",
        "undefined_parameter_type",
    ]

    for attr in unfoldable_attrs:
        if (unfold := getattr(message, attr)) is not None:
            return unfold
    raise ValueError("Empty message was given")  # noqa:TRY003


def list_filter_by_type(t: type | Iterable[type], items):
    return list(filter(partial(flip(isinstance), tuple(t) if isinstance(t, Iterable) else t), items))


class ParseError(RuntimeError):
    def __init__(self, errors):
        super().__init__(f"Could not parse messages: {errors}")


def parse_and_unfold_messages(lines):
    errors = []
    parsed_messages = []
    for line in lines:
        try:
            parsed_messages.append(message_converter.from_dict(json.loads(line), Message))
        except ValidationError as e:  # pragma: nocover
            errors.append(e)
        if errors:  # pragma: nocover
            raise ParseError(errors)

    return list(map(unfold_message, parsed_messages))


def test_minimal_scenario_messages(testdir: "Testdir", tmp_path):
    testdir.makefile(
        ".feature",
        # language=gherkin
        minimal=(samples_path / "minimal" / "minimal.feature").read_text(),
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given
        from parse_type.cfparse import Parser as cfparse

        @given(
            cfparse(
                "I have {cukes:Number} cukes in my belly",
                extra_types=dict(Number=int)
            )
        )
        def cukes_count(cukes):
            assert cukes
        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()
    assert "PYTEST_BDD_" not in "".join(ndjson_lines)

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    meta_messages = messages = list_filter_by_type(Meta, unfold_messages)
    assert len(meta_messages) == 1, f"Messages: {pformat(messages)}"

    source_messages = messages = list_filter_by_type(Source, unfold_messages)
    assert len(source_messages) == 1, f"Messages: {pformat(messages)}"

    gherkin_document_messages = messages = list_filter_by_type(GherkinDocument, unfold_messages)
    assert len(gherkin_document_messages) == 1, f"Messages: {pformat(messages)}"

    pickle_messages = messages = list_filter_by_type(Pickle, unfold_messages)
    assert len(pickle_messages) == 1, f"Messages: {pformat(messages)}"

    step_definition_messages = messages = list_filter_by_type(StepDefinition, unfold_messages)
    step_definitions_defined_by_pytest_bdd_ng = 3
    step_definitions_defined_by_test = 1
    assert (
        len(step_definition_messages) == step_definitions_defined_by_pytest_bdd_ng + step_definitions_defined_by_test
    ), f"Messages: {pformat(messages)}"

    test_run_started_messages = messages = list_filter_by_type(_TestRunStarted, unfold_messages)
    assert len(test_run_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_case_messages = messages = list_filter_by_type(_TestCase, unfold_messages)
    assert len(test_case_messages) == 1, f"Messages: {pformat(messages)}"
    assert test_case_messages[0].test_run_started_id == test_run_started_messages[0].id

    test_case_started_messages = messages = list_filter_by_type(_TestCaseStarted, unfold_messages)
    assert len(test_case_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_step_started_messages = messages = list_filter_by_type(_TestStepStarted, unfold_messages)
    assert len(test_step_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_step_finished_messages = messages = list_filter_by_type(_TestStepFinished, unfold_messages)
    assert len(test_step_finished_messages) == 1, f"Messages: {pformat(messages)}"

    test_case_finished_messages = messages = list_filter_by_type(_TestCaseFinished, unfold_messages)
    assert len(test_case_finished_messages) == 1, f"Messages: {pformat(messages)}"

    test_run_finished_messages = messages = list_filter_by_type(_TestRunFinished, unfold_messages)
    assert len(test_run_finished_messages) == 1, f"Messages: {pformat(messages)}"
    assert list_filter_by_type(_ParseError, unfold_messages) == []
    assert list_filter_by_type(_Suggestion, unfold_messages) == []
    assert list_filter_by_type(_UndefinedParameterType, unfold_messages) == []

    messages_ids = [m.id for m in unfold_messages if hasattr(m, "id")]
    assert len(messages_ids) == len(list(set(messages_ids)))

    test_run_lifetime_messages = list_filter_by_type((_TestRunStarted, _TestRunFinished), unfold_messages)
    assert isinstance(test_run_lifetime_messages[0], _TestRunStarted)
    assert isinstance(test_run_lifetime_messages[1], _TestRunFinished)

    test_case_lifetime_messages = list_filter_by_type((_TestCaseStarted, _TestCaseFinished), unfold_messages)
    assert isinstance(test_case_lifetime_messages[0], _TestCaseStarted)
    assert isinstance(test_case_lifetime_messages[1], _TestCaseFinished)

    test_step_lifetime_messages = list_filter_by_type((_TestStepStarted, _TestStepFinished), unfold_messages)
    assert isinstance(test_step_lifetime_messages[0], _TestStepStarted)
    assert isinstance(test_step_lifetime_messages[1], _TestStepFinished)

    test_run_case_start_lifetime_messages = list_filter_by_type((_TestRunStarted, _TestCaseStarted), unfold_messages)
    assert isinstance(test_run_case_start_lifetime_messages[0], _TestRunStarted)
    assert isinstance(test_run_case_start_lifetime_messages[1], _TestCaseStarted)

    test_case_step_start_lifetime_messages = list_filter_by_type((_TestCaseStarted, _TestStepStarted), unfold_messages)
    assert isinstance(test_case_step_start_lifetime_messages[0], _TestCaseStarted)
    assert isinstance(test_case_step_start_lifetime_messages[1], _TestStepStarted)

    test_case_step_finish_lifetime_messages = list_filter_by_type(
        (_TestCaseFinished, _TestStepFinished),
        unfold_messages,
    )
    assert isinstance(test_case_step_finish_lifetime_messages[0], _TestStepFinished)
    assert isinstance(test_case_step_finish_lifetime_messages[1], _TestCaseFinished)

    test_run_case_finish_lifetime_messages = list_filter_by_type((_TestRunFinished, _TestCaseFinished), unfold_messages)
    assert isinstance(test_run_case_finish_lifetime_messages[0], _TestCaseFinished)
    assert isinstance(test_run_case_finish_lifetime_messages[1], _TestRunFinished)


def test_parameter_type_messages(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from cucumber_expressions.parameter_type import ParameterType
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        from pytest_bdd import given
        from pytest_bdd.parsers import cucumber_expression


        class Coordinate:
            def __init__(self, x: int, y: int, z: int):
                self.x = x
                self.y = y
                self.z = z

            def __eq__(self, other):
                return (
                    isinstance(other, Coordinate)
                    and other.x == self.x
                    and self.y == other.y
                    and self.z == other.z
                )


        @pytest.fixture
        def parameter_type_registry():
            _parameter_type_registry = ParameterTypeRegistry()
            _parameter_type_registry.define_parameter_type(
                ParameterType(
                    "coordinate",
                    r"(\\d+),\\s*(\\d+),\\s*(\\d+)",
                    Coordinate,
                    lambda x, y, z: Coordinate(int(x), int(y), int(z)),
                    True,
                    False,
                )
            )

            return _parameter_type_registry


        @given(
            cucumber_expression(
                "A {int} thick line from {coordinate} to {coordinate}"
            ),
            anonymous_group_names=['thick', 'start', 'end'],
        )
        def cukes_count(thick, start, end):
            assert Coordinate(10, 20, 30) == start
            assert Coordinate(40, 50, 60) == end
            assert thick == 5

        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        balls="""
        Feature: minimal

          Scenario: Thick line
            Given A 5 thick line from 10,20,30 to 40,50,60

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    parameter_type_messages = messages = list_filter_by_type(ParameterType, unfold_messages)
    oracle_parameter_type_messages_count = 12
    assert len(parameter_type_messages) == oracle_parameter_type_messages_count, f"Messages: {pformat(messages)}"


def test_attachment_type_message_as_raw_string(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as string')
        def attach_as_string(attach, value):
            attach(value)
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "Hello world!" as string

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "Hello world!"
    assert attachment_message.media_type == "text/plain;charset=UTF-8"
    assert AttachmentContentEncoding(attachment_message.content_encoding) == AttachmentContentEncoding.identity


def test_attachment_type_messages_as_raw_string_with_content_type(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as url')
        def attach_as_url(attach, value):
            attach(value, media_type='text/uri-list')
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "http://https://example.com/" as url

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "http://https://example.com/"
    assert attachment_message.media_type == "text/uri-list"
    assert AttachmentContentEncoding(attachment_message.content_encoding) == AttachmentContentEncoding.identity


def test_attachment_type_messages_as_bytes(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as bytes')
        def attach_as_bytes(attach, value):
            attach(value.encode('utf-8'))
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "Hello world!" as bytes

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "SGVsbG8gd29ybGQh"
    assert AttachmentContentEncoding(attachment_message.content_encoding) == AttachmentContentEncoding.base64


def test_attachment_type_messages_from_text_file(testdir: "Testdir", tmp_path):
    file_path = tmp_path / "file.txt"
    (tmp_path / "file.txt").write_text("Hello world!")

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given
        from pathlib import Path

        @given('Attach text from {file_path} file', converters={'file_path': Path})
        def attach_from_file(attach, file_path: Path):
            with file_path.open(mode='r') as file:
                attach(file)
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment=f"""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach text from {file_path} file

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "Hello world!"
    assert AttachmentContentEncoding(attachment_message.content_encoding) == AttachmentContentEncoding.identity


def test_attachment_type_messages_from_binary_file(testdir: "Testdir", tmp_path):
    file_path = tmp_path / "file.txt"
    (tmp_path / "file.txt").write_text("Hello world!")

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given
        from pathlib import Path

        @given('Attach bytes from {file_path} file', converters={'file_path': Path})
        def attach_bytes_from_file(attach, file_path: Path):
            with file_path.open(mode='rb') as file:
                attach(file, file_name=file_path)
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment=f"""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach bytes from {file_path} file

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "SGVsbG8gd29ybGQh"
    assert AttachmentContentEncoding(attachment_message.content_encoding) == AttachmentContentEncoding.base64
    assert attachment_message.media_type == "application/octet-stream"
    assert Path(cast(str, attachment_message.file_name)).name == "file.txt"


def test_hook_type_messages(testdir, tmp_path):
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
        same_name="""\
            @tag
            Feature: Feature with tag
                Scenario: Scenario with tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_tag, before_mark, after_tag, around_mark
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.util.pytest_extra import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_tag('@tag', name='before')
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_mark('tag')
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_tag('@tag', name='after')
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_mark('tag', 'around')
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unfold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Hook, unfold_messages)
    oracle_attachment_messages_count = 6
    assert len(attachment_messages) == oracle_attachment_messages_count, f"Messages: {pformat(messages)}"

    assert any(message.type == HookType.before_test_run and message.name == "before-test-run" for message in messages)
    assert any(message.type == HookType.after_test_run and message.name == "after-test-run" for message in messages)

    # before_mark hook
    assert any(message.tag_expression == "tag" and message.name is None for message in attachment_messages)

    # before_tag hook
    assert any(message.tag_expression == "@tag" and message.name == "before" for message in attachment_messages)

    # after_tag hook
    assert any(message.tag_expression == "@tag" and message.name == "after" for message in attachment_messages)

    # after_tag hook
    assert any(message.tag_expression == "tag" and message.name == "around" for message in attachment_messages)
    assert all(message.type is not None for message in attachment_messages)


def test_lookup_error_emits_suggestion_and_undefined_parameter_type(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, parsers

        @given(parsers.cucumber_expression("value is {unknownParameter}"))
        def value_is_unknown_parameter():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        undefined_parameter="""
        Feature: undefined parameter type emission

          Scenario: unknown parameter type in expression
            Given value is 10
        """,
    )

    ndjson_path = tmp_path / "undefined-parameter.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(failed=1)

    unfold_messages = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())

    suggestions = list_filter_by_type(_Suggestion, unfold_messages)
    undefined_parameter_types = list_filter_by_type(_UndefinedParameterType, unfold_messages)

    assert suggestions, "Expected suggestion payload for step lookup failure"
    assert suggestions[0].pickle_step_id
    assert suggestions[0].snippets
    assert suggestions[0].snippets[0].language == "python"
    assert "NotImplementedError" in suggestions[0].snippets[0].code

    assert undefined_parameter_types, "Expected undefinedParameterType payload for undefined cucumber parameter type"
    assert undefined_parameter_types[0].name == "unknownParameter"
    assert "unknownParameter" in undefined_parameter_types[0].expression


def test_feature_parse_error_emits_parse_error_message(testdir: "Testdir", tmp_path):
    testdir.makefile(
        ".feature",
        # language=gherkin
        broken="""
        Feature broken feature

          Scenario: malformed step
            Given regular step
        """,
    )

    ndjson_path = tmp_path / "parse-error.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(errors=1)

    unfold_messages = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    parse_errors = list_filter_by_type(_ParseError, unfold_messages)

    assert parse_errors, "Expected parseError payload on feature parse failure"
    assert parse_errors[0].source is not None
    assert parse_errors[0].source.location is not None
    assert parse_errors[0].source.location.line >= 1


def test_lifecycle_count_and_order_for_pass_and_fail(testdir: "Testdir", tmp_path):
    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
        Feature: lifecycle coverage

            Scenario: pass path
                Given a passing step

            Scenario: fail path
                Given a failing step
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("a passing step")
        def pass_step():
            return "ok"

        @given("a failing step")
        def fail_step():
            raise RuntimeError("boom")
        """,
    )

    ndjson_path = tmp_path / "lifecycle.feature.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(passed=1, failed=1)

    unfold_messages = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())

    assert len(list_filter_by_type(_TestRunStarted, unfold_messages)) == 1
    assert len(list_filter_by_type(_TestRunFinished, unfold_messages)) == 1
    assert len(list_filter_by_type(_TestCaseStarted, unfold_messages)) == 2
    assert len(list_filter_by_type(_TestCaseFinished, unfold_messages)) == 2
    assert len(list_filter_by_type(_TestStepStarted, unfold_messages)) == 2
    assert len(list_filter_by_type(_TestStepFinished, unfold_messages)) == 2

    message_type_names = [type(payload).__name__ for payload in unfold_messages]
    assert message_type_names.index("TestRunStarted") < message_type_names.index("TestCaseStarted")
    assert message_type_names.index("TestCaseStarted") < message_type_names.index("TestStepStarted")
    assert message_type_names.index("TestStepFinished") < message_type_names.index("TestCaseFinished")


def test_message_converter_rejects_multi_payload_envelope_shape():
    with pytest.raises(TypeError, match="exactly one payload"):
        envelope_from_dict(
            {
                "test_run_started": {"timestamp": {"seconds": 1, "nanos": 1}},
                "test_run_finished": {"timestamp": {"seconds": 2, "nanos": 2}, "success": True},
            }
        )


def test_gherkin_document_emits_rule_background_comment_examples_docstring_and_tables(testdir: "Testdir", tmp_path):
    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
        [pytest]
        markers =
            feature_tag
            rule_tag
            scenario_tag
            top_scenario_tag
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        mandatory="""\
        # comment for gherkin document coverage
        @feature_tag
        Feature: Mandatory coverage feature
          Feature description line for coverage.

          Background: Base context
            Given a background value "from background"
            And a background table:
              | key   | value |
              | alpha | one   |

          @rule_tag
          Rule: Rule level validation

            Background: Rule background context
              Given a rule background value "rule background"

            @scenario_tag
            Scenario Outline: Rule scenario outline
              Given a number <number>
              Then result should be "<result>"

              Examples: Rule examples
                | number | result |
                | 1      | pass   |
                | 2      | pass   |

          @top_scenario_tag
          Scenario: Top level scenario with doc string and table
            Given a payload doc string:
              \"\"\"json
              {
                "message": "hello"
              }
              \"\"\"
            And a payload table:
              | left  | right |
              | one   | two   |
            Then result should be "pass"
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then, parsers

        @given(parsers.parse('a background value "{value}"'))
        def background_value(value):
            return value

        @given(parsers.parse('a rule background value "{value}"'))
        def rule_background_value(value):
            return value

        @given("a background table:")
        def background_table(step):
            assert step.data_table is not None

        @given(parsers.parse("a number {number:d}"))
        def number(number):
            return number

        @given("a payload doc string:")
        def payload_doc_string(step):
            assert step.doc_string is not None

        @given("a payload table:")
        def payload_table(step):
            assert step.data_table is not None

        @then(parsers.parse('result should be "{result}"'))
        def result(result):
            assert result == "pass"
        """,
    )

    ndjson_path = tmp_path / "gherkin-structure.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(passed=3)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    gherkin_documents = list_filter_by_type(GherkinDocument, payloads)
    assert len(gherkin_documents) == 1

    gherkin_document = gherkin_documents[0]
    assert gherkin_document.comments
    assert gherkin_document.comments[0].text.startswith("# comment")
    assert gherkin_document.comments[0].location.line >= 1
    assert gherkin_document.comments[0].location.column >= 1

    feature = gherkin_document.feature
    assert feature is not None
    assert feature.tags
    assert feature.location.line >= 1

    backgrounds = [child.background for child in feature.children if child.background is not None]
    assert backgrounds
    background = backgrounds[0]
    assert background.steps
    assert any(step.data_table is not None for step in background.steps)

    rules = [child.rule for child in feature.children if child.rule is not None]
    assert rules
    rule = rules[0]
    assert rule.tags

    rule_backgrounds = [child.background for child in rule.children if child.background is not None]
    assert rule_backgrounds
    assert rule_backgrounds[0].steps

    rule_scenarios = [child.scenario for child in rule.children if child.scenario is not None]
    assert rule_scenarios
    outline_scenario = rule_scenarios[0]
    assert outline_scenario.examples
    examples = outline_scenario.examples[0]
    assert examples.table_header is not None
    assert examples.table_body

    all_feature_level_scenarios = [child.scenario for child in feature.children if child.scenario is not None]
    top_scenarios = [
        scenario
        for scenario in [*rule_scenarios, *all_feature_level_scenarios]
        if any(step.doc_string is not None or step.data_table is not None for step in scenario.steps)
    ]
    assert top_scenarios
    top_scenario = top_scenarios[0]
    assert any(step.doc_string is not None for step in top_scenario.steps)
    assert any(step.data_table is not None for step in top_scenario.steps)
