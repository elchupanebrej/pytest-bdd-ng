"""E2E step definitions for code generator feature coverage."""

from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path

from pytest_bdd import given, parsers, then, when


def _write_feature(testdir, *, name: str, content: str):
    feature = testdir.tmpdir.join(name)
    feature.write(textwrap.dedent(content))
    return feature


def _generated_python_module(pytest_result) -> ast.Module:
    stdout = pytest_result.stdout.str()
    code_lines = [
        line for line in stdout.splitlines() if line.startswith(("from ", "import ", "@", "def ", "    ", "raise "))
    ]
    code = "\n".join(code_lines)
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        message = f"Generated output is not valid Python:\n{stdout}"
        raise AssertionError(message) from exc


def _step_decorators(module: ast.Module) -> list[tuple[str, str]]:
    decorators: list[tuple[str, str]] = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name):
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            decorators.append((decorator.func.id, str(decorator.args[0].value)))
    return decorators


def _read_attachment_payloads(ndjson_path: Path, media_type: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for raw_line in ndjson_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        attachment = json.loads(raw_line).get("attachment")
        if not isinstance(attachment, dict):
            continue
        if attachment.get("mediaType") != media_type:
            continue
        body = attachment.get("body")
        if isinstance(body, str):
            payloads.append(json.loads(body))
    return payloads


@given("a BDD module with one missing scenario binding and one missing step", target_fixture="codegen_case")
def bdd_module_with_missing_artifacts(testdir):
    """Create a fixture project with one bound scenario and one unbound scenario."""
    feature = _write_feature(
        testdir,
        name="generation.feature",
        content="""\
        Feature: Missing code generation

            Scenario: Bound scenario with a missing step
                Given I have a bar
                Then I have a custom bar

            Scenario: Unbound scenario
                Given I have a bar
        """,
    )
    testdir.makepyfile(
        f"""\
        from pathlib import Path

        from pytest_bdd import given, scenario


        @given("I have a bar")
        def i_have_a_bar():
            return "bar"


        @scenario(Path(r"{feature}"), "Bound scenario with a missing step")
        def test_bound():
            pass
        """,
    )
    return {"feature": feature, "target": testdir.tmpdir.join("test_generated.py")}


@when("I gather missing code-generation events", target_fixture="codegen_events")
def gather_missing_codegen_events(testdir, codegen_case):
    """Run gather command and parse emitted NDJSON."""
    result = testdir.runpytest_inprocess("--gather-missing-steps", str(codegen_case["feature"]))
    assert result.ret == 100
    assert not result.stderr.str()
    return [json.loads(line) for line in result.stdout.str().splitlines() if line.strip()]


@then("the missing-code NDJSON includes binding and step-definition events")
def missing_code_ndjson_includes_binding_and_step_events(codegen_events):
    event_types = {event["type"] for event in codegen_events}
    assert "missing_scenario_binding" in event_types
    assert "missing_step_definition" in event_types
    assert any(event.get("scenario") == "Unbound scenario" for event in codegen_events)
    assert any(event.get("text") == "I have a custom bar" for event in codegen_events)


@when("I bind the feature to a target file twice", target_fixture="bind_result")
def bind_feature_to_target_file_twice(testdir, codegen_case):
    """Run bind-feature twice and keep before/after bytes."""
    target = codegen_case["target"]
    first = testdir.runpytest_inprocess("--bind-feature", "--target-file", str(target), str(codegen_case["feature"]))
    assert first.ret == 0
    after_first = target.read()
    second = testdir.runpytest_inprocess("--bind-feature", "--target-file", str(target), str(codegen_case["feature"]))
    assert second.ret == 0
    return {"target": target, "after_first": after_first, "after_second": target.read()}


@then("the target file has one idempotent scenarios binding")
def target_file_has_one_idempotent_scenarios_binding(bind_result):
    content = bind_result["after_second"]
    assert bind_result["after_first"] == bind_result["after_second"]
    assert "from pytest_bdd import scenarios" in content
    assert content.count("scenarios(") == 1
    assert "generation.feature" in content


@when("I generate missing step skeletons into a target file", target_fixture="generated_target")
def generate_missing_step_skeletons(testdir, codegen_case):
    """Run missing-step target authoring."""
    target = codegen_case["target"]
    result = testdir.runpytest_inprocess(
        "--generate-missing-steps",
        "--target-file",
        str(target),
        str(codegen_case["feature"]),
    )
    assert result.ret == 100
    return target


@then("the target file contains inert underscore step skeletons")
def target_file_contains_inert_underscore_step_skeletons(generated_target):
    content = generated_target.read()
    assert "@not_implemented" in content
    assert "@then(" in content
    assert "def _():" in content
    assert "raise NotImplementedError" in content


@given("a scenario with hook and body probes", target_fixture="probe_case")
def scenario_with_hook_and_body_probes(testdir):
    """Create a scenario where normal execution would write probe files."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    feature = _write_feature(
        testdir,
        name="probe.feature",
        content="""\
        Feature: Mock run

            Scenario: Probe scenario
                Given a body probe
        """,
    )
    testdir.makepyfile(
        f"""\
        from pathlib import Path

        import pytest

        from pytest_bdd import given, scenario


        @scenario(Path(r"{feature}"), "Probe scenario")
        def test_probe():
            pass


        def pytest_bdd_before_scenario():
            Path("hook.txt").write_text("hook", encoding="utf-8")


        @given("a body probe")
        def body_probe():
            Path("body.txt").write_text("body", encoding="utf-8")
        """,
    )
    return {"feature": feature}


@given("an IDE bootstrap scenario with launch and binding probes", target_fixture="ide_bootstrap_case")
def ide_bootstrap_scenario_with_launch_and_binding_probes(testdir):
    """Create a mock-run project that should emit launch and step-binding attachments."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    feature = _write_feature(
        testdir,
        name="ide_bootstrap.feature",
        content="""\
        Feature: IDE bootstrap

            Scenario: Bootstrap scenario
                Given a body probe
        """,
    )
    testdir.makepyfile(
        f"""\
        from pathlib import Path

        from pytest_bdd import given, scenario


        @scenario(Path(r"{feature}"), "Bootstrap scenario")
        def test_bootstrap():
            pass


        def pytest_bdd_before_scenario(request, run):
            Path("hook.txt").write_text("hook", encoding="utf-8")


        @given("a body probe")
        def body_probe():
            Path("body.txt").write_text("body", encoding="utf-8")
        """,
    )
    return {"ndjson": Path(str(testdir.tmpdir)) / "ide-bootstrap.ndjson"}


@given(
    "an IDE bootstrap scenario with a missing step and one available definition",
    target_fixture="ide_bootstrap_case",
)
def ide_bootstrap_scenario_with_missing_step(testdir):
    """Create a mock-run project that should emit missing-step diagnostics."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    feature = _write_feature(
        testdir,
        name="ide_missing.feature",
        content="""\
        Feature: IDE missing step

            Scenario: Missing authoring
                Given this step is missing
        """,
    )
    testdir.makepyfile(
        f"""\
        from pathlib import Path

        from pytest_bdd import given, scenario


        @scenario(Path(r"{feature}"), "Missing authoring")
        def test_missing_authoring():
            pass


        @given("other available step")
        def other_available_step():
            pass
        """,
    )
    return {"ndjson": Path(str(testdir.tmpdir)) / "ide-missing.ndjson"}


@given("an IDE bootstrap scenario bound from two pytest modules", target_fixture="ide_bootstrap_case")
def ide_bootstrap_scenario_bound_from_two_modules(testdir):
    """Create a mock-run project that should emit duplicate source binding diagnostics."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    feature = _write_feature(
        testdir,
        name="ide_duplicate.feature",
        content="""\
        Feature: IDE duplicate binding

            Scenario: Duplicate source
                Given a shared step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given


        @given("a shared step")
        def shared_step():
            pass
        """,
    )
    scenario_binding = f"""\
    from pathlib import Path

    from pytest_bdd import scenario


    @scenario(Path(r"{feature}"), "Duplicate source")
    def test_duplicate_source():
        pass
    """
    testdir.makepyfile(test_duplicate_a=scenario_binding, test_duplicate_b=scenario_binding)
    return {"ndjson": Path(str(testdir.tmpdir)) / "ide-duplicate.ndjson"}


@when("I run pytest in mock-run mode", target_fixture="mock_result")
def run_pytest_in_mock_run_mode(testdir):
    return testdir.runpytest_inprocess("--mock-run")


@when("I run pytest mock-run with message reporting", target_fixture="ide_bootstrap_result")
def run_pytest_mock_run_with_message_reporting(testdir, ide_bootstrap_case):
    return testdir.runpytest_inprocess(
        "--mock-run",
        "--messages-ndjson",
        str(ide_bootstrap_case["ndjson"]),
    )


@then("mock-run passes without executing hooks or step bodies")
def mock_run_passes_without_executing_hooks_or_bodies(testdir, mock_result):
    mock_result.assert_outcomes(passed=1)
    assert not testdir.tmpdir.join("hook.txt").check()
    assert not testdir.tmpdir.join("body.txt").check()


@then("IDE bootstrap messages include launch handles, source identities, matched step bindings, and no probes")
def ide_bootstrap_messages_include_launch_and_bindings(testdir, ide_bootstrap_case, ide_bootstrap_result):
    ide_bootstrap_result.assert_outcomes(passed=1)
    assert not testdir.tmpdir.join("hook.txt").check()
    assert not testdir.tmpdir.join("body.txt").check()

    launch_payloads = _read_attachment_payloads(
        ide_bootstrap_case["ndjson"],
        "application/vnd.pytest-bdd.launch+json",
    )
    binding_payloads = _read_attachment_payloads(
        ide_bootstrap_case["ndjson"],
        "application/vnd.pytest-bdd.step-binding+json",
    )

    assert len(launch_payloads) == 1
    launch_payload = launch_payloads[0]
    assert launch_payload["nodeid"]
    assert launch_payload["testCaseId"]
    assert launch_payload["pickleId"]
    assert isinstance(launch_payload["sourceIdentity"], dict)
    assert len(binding_payloads) == 1
    assert binding_payloads[0]["testCaseId"] == launch_payload["testCaseId"]
    assert binding_payloads[0]["sourceReference"]


@then("IDE bootstrap diagnostics include the missing step and scoped available definitions")
def ide_bootstrap_diagnostics_include_missing_step(ide_bootstrap_case, ide_bootstrap_result):
    assert ide_bootstrap_result.ret != 0
    diagnostics = _read_attachment_payloads(
        ide_bootstrap_case["ndjson"],
        "application/vnd.pytest-bdd.diagnostic+json",
    )
    missing = [payload for payload in diagnostics if payload.get("kind") == "missing-step"]
    assert len(missing) == 1
    assert missing[0]["unmatchedStepText"] == "this step is missing"
    available = missing[0]["availableStepDefinitions"]
    assert isinstance(available, list)
    assert any("other available step" in item.get("pattern", "") for item in available)


@then("IDE bootstrap diagnostics include one duplicate binding warning grouped by source identity")
def ide_bootstrap_diagnostics_include_duplicate_binding_warning(ide_bootstrap_case, ide_bootstrap_result):
    ide_bootstrap_result.assert_outcomes(passed=2)
    diagnostics = _read_attachment_payloads(
        ide_bootstrap_case["ndjson"],
        "application/vnd.pytest-bdd.diagnostic+json",
    )
    duplicates = [payload for payload in diagnostics if payload.get("kind") == "duplicate-bindings"]
    assert len(duplicates) == 1
    assert duplicates[0]["severity"] == "warning"
    assert isinstance(duplicates[0]["sourceIdentity"], dict)
    assert len(duplicates[0]["bindings"]) == 2
    assert all(binding["nodeid"] and binding["testCaseId"] for binding in duplicates[0]["bindings"])


@given("a not implemented step scenario", target_fixture="wip_case")
def not_implemented_step_scenario(testdir):
    """Create a scenario with a public not_implemented step."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        wip=textwrap.dedent(
            """\
            Feature: WIP steps

                Scenario: Pending step
                    Given a pending step
            """,
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, not_implemented, scenario


            @scenario("wip.feature", "Pending step")
            def test_pending():
                pass


            @given("a pending step")
            @not_implemented
            def pending_step():
                raise NotImplementedError
            """,
        ),
    )


@when(parsers.parse("I run pytest with WIP status {status}"), target_fixture="wip_result")
def run_pytest_with_wip_status(testdir, status):
    return testdir.runpytest_inprocess("--wip-status", status)


@then("the not implemented scenario passes without executing the step body")
def not_implemented_scenario_passes(wip_result):
    wip_result.assert_outcomes(passed=1)


@given("a tolerant step scenario", target_fixture="tolerant_case")
def tolerant_step_scenario(testdir):
    """Create a tolerant step scenario where a later step proves continuation."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        tolerant=textwrap.dedent(
            """\
            Feature: Tolerant steps

                Scenario: Tolerant failure
                    Given a tolerant step fails
                    Then a later step runs
            """,
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pathlib import Path

            from pytest_bdd import given, scenario, then, tolerant


            @scenario("tolerant.feature", "Tolerant failure")
            def test_tolerant_failure():
                pass


            @tolerant
            @given("a tolerant step fails")
            def tolerant_step():
                raise AssertionError("soft failure")


            @then("a later step runs")
            def later_step():
                Path("later.txt").write_text("ran", encoding="utf-8")
            """,
        ),
    )


@when("I run pytest with ignored tolerant status", target_fixture="tolerant_result")
def run_pytest_with_ignored_tolerant_status(testdir):
    return testdir.runpytest_inprocess("--tolerant-status", "ignored")


@then("the tolerant scenario passes and later steps still run")
def tolerant_scenario_passes_and_later_steps_run(testdir, tolerant_result):
    tolerant_result.assert_outcomes(passed=1)
    assert testdir.tmpdir.join("later.txt").read() == "ran"


@then("generated Python code matches oracle:")
def generated_python_code_matches_oracle(pytest_result, step):
    actual = _generated_python_module(pytest_result)
    expected = ast.parse(step.argument.doc_string.content)

    assert sorted(_step_decorators(actual)) == sorted(_step_decorators(expected))


@then("generated Python code defines functions:")
def generated_python_code_defines_functions(pytest_result, step):
    module = _generated_python_module(pytest_result)
    expected = [row.cells[0].value for row in step.argument.data_table.rows[1:]]
    actual = [node.name for node in module.body if isinstance(node, ast.FunctionDef)]
    assert actual == expected


@then("Generated code is printed to stdout")
def generated_code_is_printed(pytest_result):
    assert pytest_result.ret == 0
    assert _generated_python_module(pytest_result).body
