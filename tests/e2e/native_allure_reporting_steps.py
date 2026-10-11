"""BDD acceptance steps for live native Allure reporting."""

from __future__ import annotations

import base64
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from pytest_cuke import given, parsers, then, when


_PYTEST_XDIST_VERSION = "3.8.0"
_ALLURE_PYTHON_COMMONS_VERSION = "2.16.2"
_TEXT_ATTACHMENT = ("native-evidence.txt", "text/plain", b"native Allure text attachment")
_BINARY_ATTACHMENT = ("native-evidence.bin", "application/octet-stream", b"\x00\x7f\xffnative")
_BINARY_ATTACHMENT_BASE64 = "AH//bmF0aXZl"
_FILE_ATTACHMENT = (
    "native-evidence-file.json",
    "application/json",
    b'{"source":"allure.attach.file"}',
)
_REPORT_SCENARIOS = (
    "Native live report scenario",
    "Native xdist report scenario one",
    "Native xdist report scenario two",
)
_LIVE_OBSERVER_SCENARIO = "Live observer sees the earlier native result"


@dataclass
class NativeAllureConsumer:
    project: Path
    environment: Path
    python: Path
    pytest: Path
    env: dict[str, str]
    artifact: Path
    run_result: subprocess.CompletedProcess[str] | None = None
    optional_adapter_installed: bool = False


def _binary_dir(environment: Path) -> Path:
    return environment / ("Scripts" if os.name == "nt" else "bin")


def _executable(environment: Path, name: str) -> Path:
    return _binary_dir(environment) / (f"{name}.exe" if os.name == "nt" else name)


def _run(command: list[str], *, cwd: Path, env: dict[str, str], purpose: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, check=False, capture_output=True, text=True, timeout=240)
    assert result.returncode == 0, (
        f"{purpose} failed with exit code {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )
    return result


def _write_feature(
    context: NativeAllureConsumer,
    scenario_names: tuple[str, ...],
    *,
    with_attachments: bool,
    with_allure_api: bool = True,
    with_live_observer: bool = False,
    with_xdist_evidence: bool = False,
    with_colliding_worker_message_ids: bool = False,
) -> None:
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    step_text = (
        "Then it attaches the native report evidence"
        if with_attachments
        else "Then it completes the native report scenario"
    )
    scenario_blocks = []
    for index, name in enumerate(scenario_names, start=1):
        if with_xdist_evidence:
            case_name = "one" if index == 1 else "two"
            scenario_blocks.append(
                f"  Scenario: {name}\n"
                "    Given the native report scenario starts\n"
                f"    When the native xdist case {case_name} performs nested reporting\n"
            )
        else:
            scenario_blocks.append(
                f"  Scenario: {name}\n"
                "    Given the native report scenario starts\n"
                "    When its reportable check succeeds\n"
                f"    {step_text}\n"
            )
    if with_live_observer:
        scenario_blocks.append(
            f"  Scenario: {_LIVE_OBSERVER_SCENARIO}\n"
            "    Given the first native report result is visible before session finish\n"
            "    When its reportable check succeeds\n"
            "    Then it completes the native report scenario\n"
        )
    allure_selection = "pytestconfig.getoption('cuke_allure') or pytestconfig.getini('cuke_allure')"
    file_attachment_code = (
        f"    if {allure_selection}:\n"
        "        import allure\n"
        f"        evidence = Path({_FILE_ATTACHMENT[0]!r})\n"
        f"        evidence.write_bytes({_FILE_ATTACHMENT[2]!r})\n"
        "        allure.attach.file(\n"
        f"            str(evidence), name={_FILE_ATTACHMENT[0]!r}, attachment_type=allure.attachment_type.JSON\n"
        "        )\n"
        if with_attachments and with_allure_api
        else ""
    )
    (feature_dir / "native-allure-samples.feature").write_text(
        "Feature: Native Allure hierarchy\n\n" + "\n".join(scenario_blocks), encoding="utf-8"
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text('pytest_plugins = ["native_report_steps"]\n', encoding="utf-8")
    xdist_step_code = (
        "@when(parsers.re(r'the native xdist case (?P<case_name>one|two) performs nested reporting'))\n"
        "def native_xdist_case_performs_nested_reporting(case_name):\n"
        "    import allure\n"
        "    with allure.step(f'Native xdist action {case_name}'):\n"
        "        allure.attach(\n"
        "            f'native xdist attachment {case_name}',\n"
        "            name=f'native-xdist-{case_name}.txt',\n"
        "            attachment_type=allure.attachment_type.TEXT,\n"
        "        )\n"
        "        with allure.step(f'Native xdist detail {case_name}'):\n"
        "            assert case_name in {'one', 'two'}\n\n\n"
        if with_xdist_evidence
        else ""
    )
    worker_message_observer = (
        "@pytest.hookimpl(trylast=True)\n"
        "def pytest_sessionstart(session):\n"
        "    if not isinstance(getattr(session.config, 'workerinput', None), dict):\n"
        "        return\n"
        "    session.config.pytest_cuke_id_generator.set_namespace('native-allure-shared-worker-local-id')\n\n\n"
        "def pytest_cuke_message(config, message):\n"
        "    del config\n"
        "    worker_id = os.environ.get('PYTEST_XDIST_WORKER')\n"
        "    if not worker_id:\n"
        "        return\n"
        "    path = Path(f'.native-allure-local-messages-{worker_id}.jsonl')\n"
        "    with path.open('a', encoding='utf-8') as stream:\n"
        "        stream.write(json.dumps(message_to_dict(message), sort_keys=True) + '\\n')\n\n\n"
        if with_colliding_worker_message_ids
        else ""
    )
    (context.project / "native_report_steps.py").write_text(
        "import json\n"
        "import os\n"
        "import pytest\n"
        "from pathlib import Path\n"
        "from pytest_cuke.model.message_types import message_to_dict\n\n"
        "from pytest_cuke import given, parsers, then, when\n\n\n"
        "@given('the native report scenario starts')\n"
        "def native_report_scenario_starts():\n"
        "    pass\n\n\n"
        "@given('the first native report result is visible before session finish')\n"
        "def first_native_report_result_is_live(pytestconfig):\n"
        f"    output_dir = pytestconfig.getoption('cuke_allure') or pytestconfig.getini('cuke_allure')\n"
        "    assert output_dir, 'the live observer needs --cuke-allure'\n"
        "    result_files = list(Path(output_dir).glob('*-result.json'))\n"
        "    results = [json.loads(path.read_text(encoding='utf-8')) for path in result_files]\n"
        "    first_results = [result for result in results if result.get('name') == 'Native live report scenario']\n"
        "    assert len(first_results) == 1, f'expected one completed first live result before session finish, found {results}'\n"
        "    assert first_results[0].get('status') == 'passed', first_results[0]\n\n\n"
        "@when('its reportable check succeeds')\n"
        "def native_reportable_check_succeeds(pytestconfig):\n"
        + (
            f"    if {allure_selection}:\n"
            "        import allure\n"
            "        with allure.step('A nested native Allure action'):\n"
            "            assert 6 * 7 == 42\n"
            "    else:\n"
            "        assert 6 * 7 == 42\n\n\n"
            if with_allure_api
            else "    assert 6 * 7 == 42\n\n\n"
        )
        + "@then('it completes the native report scenario')\n"
        "def native_report_scenario_completes():\n"
        "    assert True\n\n\n"
        "@then('it attaches the native report evidence')\n"
        "def native_report_scenario_attaches_evidence(attach, pytestconfig):\n"
        "    attach('native Allure text attachment', media_type='text/plain', file_name='native-evidence.txt')\n"
        "    attach(b'\\x00\\x7f\\xffnative', media_type='application/octet-stream', file_name='native-evidence.bin')\n"
        + file_attachment_code
        + worker_message_observer
        + xdist_step_code,
        encoding="utf-8",
    )


def _write_field_contract_feature(context: NativeAllureConsumer) -> None:
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "native-field-contract.feature").write_text(
        "@feature-native-tag\n"
        "Feature: Native profile contract\n"
        "  The feature description is preserved.\n\n"
        "  @rule-native-tag\n"
        "  Rule: Profile submission\n"
        "    The rule description is preserved.\n\n"
        "    @scenario-native-tag\n"
        "    Scenario Outline: Submit <customer> profile on <plan>\n"
        "      The outline description is preserved.\n"
        "      Given the native profile is ready\n"
        "      When the JSON profile is accepted\n"
        '        """application/json\n'
        '        {"customer": "<customer>", "active": true}\n'
        '        """\n'
        "      Then the profile fields are recorded\n"
        "        | field | value |\n"
        "        | customer | <customer> |\n"
        "        | active | true |\n\n"
        "      Examples: customer plans\n"
        "        | customer | plan |\n"
        "        | Ada | premium |\n",
        encoding="utf-8",
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        'pytest_plugins = ["native_field_contract_steps"]\n',
        encoding="utf-8",
    )
    (context.project / "native_field_contract_steps.py").write_text(
        "import json\n"
        "from pathlib import Path\n\n"
        "from pytest_cuke import given, then, when\n"
        "from pytest_cuke.model.message_types import message_to_dict\n\n\n"
        "_validated_messages = []\n\n\n"
        "def pytest_cuke_message_validated(config, message):\n"
        "    del config\n"
        "    _validated_messages.append(message_to_dict(message))\n"
        "    Path('live-message-timestamps.json').write_text(\n"
        "        json.dumps(_validated_messages, ensure_ascii=False), encoding='utf-8'\n"
        "    )\n\n\n"
        "@given('the native profile is ready')\n"
        "def native_profile_is_ready():\n"
        "    pass\n\n\n"
        "@when('the JSON profile is accepted')\n"
        "def json_profile_is_accepted(step):\n"
        "    assert step.doc_string is not None\n"
        "    assert step.doc_string.media_type == 'application/json'\n"
        '    assert step.doc_string.content == \'{"customer": "Ada", "active": true}\'\n\n\n'
        "@then('the profile fields are recorded')\n"
        "def profile_fields_are_recorded(step):\n"
        "    assert step.data_table is not None\n"
        "    rows = [[cell.value for cell in row.cells] for row in step.data_table.rows]\n"
        "    assert rows == [['field', 'value'], ['customer', 'Ada'], ['active', 'true']]\n",
        encoding="utf-8",
    )


def _write_terminal_outcomes_feature(context: NativeAllureConsumer) -> None:
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "native-terminal-outcomes.feature").write_text(
        "Feature: Native Allure terminal outcomes\n\n"
        "  Scenario: Native failed scenario preserves nested traceback\n"
        "    When a nested native Allure operation fails\n\n"
        "  Scenario: Native skipped scenario preserves its reason\n"
        "    When a native scenario requests a skip\n\n"
        "  Scenario: Native undefined scenario preserves its missing step\n"
        "    When an undefined native scenario step is requested\n",
        encoding="utf-8",
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        'pytest_plugins = ["native_terminal_outcome_steps"]\n',
        encoding="utf-8",
    )
    (context.project / "native_terminal_outcome_steps.py").write_text(
        "from pytest_cuke import when\n\n\n"
        "@when('a nested native Allure operation fails')\n"
        "def nested_native_allure_operation_fails():\n"
        "    import allure\n"
        "    with allure.step('Nested native failure action'):\n"
        "        raise AssertionError('native nested failure traceback sentinel')\n\n\n"
        "@when('a native scenario requests a skip')\n"
        "def native_scenario_requests_skip():\n"
        "    import pytest\n"
        "    pytest.skip('native skipped scenario reason sentinel')\n",
        encoding="utf-8",
    )


def _write_nested_outcome_feature(context: NativeAllureConsumer) -> None:
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "native-nested-outcomes.feature").write_text(
        "Feature: Native Allure nested terminal outcomes\n\n"
        "  Scenario: Native nested skip preserves its status\n"
        "    When a native operation skips inside a nested Allure step\n\n"
        "  Scenario: Native nested assertion failure preserves its status\n"
        "    When a native assertion fails inside a nested Allure step\n\n"
        "  Scenario: Native nested runtime error preserves its status\n"
        "    When a native runtime error occurs inside a nested Allure step\n",
        encoding="utf-8",
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        'pytest_plugins = ["native_nested_outcome_steps"]\n',
        encoding="utf-8",
    )
    (context.project / "native_nested_outcome_steps.py").write_text(
        "from pytest_cuke import when\n\n\n"
        "@when('a native operation skips inside a nested Allure step')\n"
        "def native_operation_skips_inside_nested_allure_step():\n"
        "    import allure\n"
        "    import pytest\n"
        "    with allure.step('Nested native skip action'):\n"
        "        pytest.skip('native nested skip sentinel')\n\n\n"
        "@when('a native assertion fails inside a nested Allure step')\n"
        "def native_assertion_fails_inside_nested_allure_step():\n"
        "    import allure\n"
        "    with allure.step('Nested native assertion action'):\n"
        "        raise AssertionError('native nested assertion sentinel')\n\n\n"
        "@when('a native runtime error occurs inside a nested Allure step')\n"
        "def native_runtime_error_occurs_inside_nested_allure_step():\n"
        "    import allure\n"
        "    with allure.step('Nested native runtime action'):\n"
        "        raise RuntimeError('native nested runtime sentinel')\n",
        encoding="utf-8",
    )


def _write_background_failure_feature(context: NativeAllureConsumer) -> None:
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "native-background-failure.feature").write_text(
        "Feature: Native Allure Background failure\n\n"
        "  Background:\n"
        "    Given the native Background setup fails\n\n"
        "  Scenario: A failed Background remains attached to its scenario\n"
        "    When the scenario body must not execute\n",
        encoding="utf-8",
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        'pytest_plugins = ["native_background_failure_steps"]\n',
        encoding="utf-8",
    )
    (context.project / "native_background_failure_steps.py").write_text(
        "import pytest\n\n"
        "from pytest_cuke import given, when\n\n\n"
        "@given('the native Background setup fails')\n"
        "def native_background_setup_fails():\n"
        "    pytest.fail('native live Background failure sentinel')\n\n\n"
        "@when('the scenario body must not execute')\n"
        "def scenario_body_must_not_execute():\n"
        "    pytest.fail('scenario body ran after the Background failure')\n",
        encoding="utf-8",
    )


def _write_run_hook_failure_feature(context: NativeAllureConsumer, phase: str, sentinel: str) -> None:
    hook_name = "pytest_sessionstart" if phase == "BEFORE_TEST_RUN" else "pytest_sessionfinish"
    hook_parameters = "session" if phase == "BEFORE_TEST_RUN" else "session, exitstatus"
    hookimpl_options = "hookwrapper=True, tryfirst=True"
    feature_dir = context.project / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "native-run-hook-failure.feature").write_text(
        "Feature: Native Allure run-hook failure\n\n"
        "  Scenario: The scenario passes while a run hook fails\n"
        "    Given the native run-hook scenario starts\n",
        encoding="utf-8",
    )
    (context.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        "import pytest\n\n"
        "from pytest_cuke import given\n\n\n"
        "@given('the native run-hook scenario starts')\n"
        "def native_run_hook_scenario_starts():\n"
        "    pass\n\n\n"
        f"@pytest.hookimpl({hookimpl_options})\n"
        f"def {hook_name}({hook_parameters}):\n"
        "    outcome = yield\n"
        f"    raise RuntimeError({sentinel!r})\n",
        encoding="utf-8",
    )


def _install_duplicate_worker_batch_replay(context: NativeAllureConsumer) -> None:
    (context.project / "native_allure_duplicate_batch_probe.py").write_text(
        "from copy import deepcopy\n"
        "import json\n"
        "from pathlib import Path\n"
        "import pytest\n\n"
        "_first_batch = None\n"
        "_observed_batches = Path('native-allure-observed-worker-batches.jsonl')\n"
        "_first_batch_path = Path('native-allure-first-worker-batch.json')\n\n\n"
        "@pytest.hookimpl(tryfirst=True)\n"
        "def pytest_cuke_message_batch(config, batch):\n"
        "    del config\n"
        "    global _first_batch\n"
        "    observation = {'worker_id': batch.get('worker_id'), 'sequence': batch.get('sequence')}\n"
        "    with _observed_batches.open('a', encoding='utf-8') as stream:\n"
        "        stream.write(json.dumps(observation, sort_keys=True) + '\\n')\n"
        "    if _first_batch is None:\n"
        "        _first_batch = deepcopy(batch)\n"
        "        _first_batch_path.write_text(json.dumps(_first_batch), encoding='utf-8')\n\n\n"
        "@pytest.hookimpl(tryfirst=True)\n"
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    del exitstatus\n"
        "    if isinstance(getattr(session.config, 'workerinput', None), dict):\n"
        "        return\n"
        "    if _first_batch is None:\n"
        "        raise RuntimeError('the xdist controller received no worker Messages batch to replay')\n"
        "    message_plugin = session.config.pluginmanager.get_plugin('pytest_cuke_messages')\n"
        "    replay = getattr(message_plugin, '_receive_worker_message_batch', None)\n"
        "    if not callable(replay):\n"
        "        raise RuntimeError('pytest-cuke has no worker Messages batch receiver to replay')\n"
        "    replay(deepcopy(_first_batch))\n",
        encoding="utf-8",
    )
    (context.project / "conftest.py").write_text(
        'pytest_plugins = ["native_report_steps", "native_allure_duplicate_batch_probe"]\n',
        encoding="utf-8",
    )


def _context(request: Any, tmp_path: Path) -> NativeAllureConsumer:
    artifacts = request.getfixturevalue("_pytest_cuke_artifacts")
    wheel = artifacts["paths"]["wheel"]
    uv = shutil.which("uv")
    assert uv is not None, "native Allure acceptance requires uv to create an isolated installed consumer"
    project = tmp_path / "consumer"
    project.mkdir()
    environment = tmp_path / "venv"
    create_env = subprocess.run(
        [uv, "venv", "--python", sys.executable, str(environment)],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert create_env.returncode == 0, (
        f"could not create an isolated native Allure consumer:\n{create_env.stdout}\n{create_env.stderr}"
    )
    python = _executable(environment, "python")
    _run(
        [uv, "pip", "install", "--python", str(python), str(wheel)],
        cwd=project,
        env=os.environ.copy(),
        purpose="installing pytest-cuke",
    )

    home = project / ".home"
    home.mkdir()
    env = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "MYPYPATH",
        "MYPY_CONFIG_FILE_DIR",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_CURRENT_TEST",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    ):
        env.pop(name, None)
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{_binary_dir(environment)}{os.pathsep}{os.defpath}",
            "PYTHONNOUSERSITE": "1",
        }
    )
    if os.name == "nt":
        env["USERPROFILE"] = str(home)
    return NativeAllureConsumer(project, environment, python, _executable(environment, "pytest"), env, Path(wheel))


def _consumer_path(context: NativeAllureConsumer, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("native Allure artifact paths must stay inside the consumer project")
    target = context.project.joinpath(*path.parts).resolve()
    target.relative_to(context.project.resolve())
    return target


def _run_result(context: NativeAllureConsumer) -> subprocess.CompletedProcess[str]:
    result = context.run_result
    assert result is not None, "the isolated native Allure pytest command has not run"
    return result


def _result_files(context: NativeAllureConsumer, relative_path: str) -> list[Path]:
    directory = _consumer_path(context, relative_path)
    files = sorted(directory.glob("*-result.json"))
    assert files, f"native Allure result directory has no result JSON files: {directory}"
    return files


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"expected an object in {path}, got {type(value).__name__}"
    return value


def _all_objects(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _all_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_objects(child)


def _assert_timestamps(value: dict[str, Any], description: str) -> None:
    start = value.get("start")
    stop = value.get("stop")
    assert type(start) is int and type(stop) is int, (description, value)
    assert stop >= start, (description, value)


def _message_timestamp_millis(timestamp: Any, description: str) -> int:
    assert isinstance(timestamp, dict), (description, timestamp)
    seconds = timestamp.get("seconds")
    nanos = timestamp.get("nanos")
    assert type(seconds) is int and type(nanos) is int, (description, timestamp)
    return seconds * 1_000 + nanos // 1_000_000


def _assert_result_and_step_timestamps(result: dict[str, Any]) -> None:
    _assert_timestamps(result, "Allure result")

    def assert_steps(steps: Any, parent: str) -> None:
        assert isinstance(steps, list), (parent, steps)
        for index, step in enumerate(steps):
            assert isinstance(step, dict), (parent, step)
            description = f"{parent} step {index}: {step.get('name')!r}"
            _assert_timestamps(step, description)
            nested_steps = step.get("steps")
            if nested_steps is not None:
                assert_steps(nested_steps, description)

    assert_steps(result.get("steps", []), str(result.get("name", "Allure result")))


def _assert_result_has_passed_steps(
    result: dict[str, Any],
    *,
    scenario_name: str,
    require_nested_allure_step: bool = True,
    expected_when_step: str = "When its reportable check succeeds",
) -> None:
    assert result.get("name") == scenario_name, result
    assert result.get("status") == "passed", result
    assert result.get("stage") == "finished", result
    assert isinstance(result.get("uuid"), str) and result["uuid"], result
    full_name = result.get("fullName")
    assert isinstance(full_name, str) and "native-allure-samples.feature" in full_name, result
    assert scenario_name in full_name, result
    steps = result.get("steps")
    assert isinstance(steps, list) and steps, result
    assert all(isinstance(step, dict) and step.get("status") == "passed" for step in steps), steps
    _assert_result_and_step_timestamps(result)
    step_names = {step.get("name") for step in steps if isinstance(step, dict)}
    given_step = (
        "Given the first native report result is visible before session finish"
        if scenario_name == _LIVE_OBSERVER_SCENARIO
        else "Given the native report scenario starts"
    )
    assert {given_step, expected_when_step}.issubset(step_names), steps
    if require_nested_allure_step:
        nested_steps = [
            item
            for item in _all_objects(result)
            if item.get("name") == "A nested native Allure action" and item.get("status") == "passed"
        ]
        assert len(nested_steps) == 1, result


def _attachment_refs(value: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in _all_objects(value)
        if isinstance(item.get("name"), str) and isinstance(item.get("source"), str) and "type" in item
    ]


def _assert_attachment_contents(context: NativeAllureConsumer, result_directory: str, result: dict[str, Any]) -> None:
    refs = _attachment_refs(result)
    expected = {
        _TEXT_ATTACHMENT[0]: _TEXT_ATTACHMENT,
        _BINARY_ATTACHMENT[0]: _BINARY_ATTACHMENT,
        _FILE_ATTACHMENT[0]: _FILE_ATTACHMENT,
    }
    by_name = {ref["name"]: ref for ref in refs}
    assert set(expected).issubset(by_name), refs
    output_root = _consumer_path(context, result_directory).resolve()
    for name, (_expected_name, media_type, contents) in expected.items():
        ref = by_name[name]
        assert ref["type"].split(";", 1)[0] == media_type, ref
        source = PurePosixPath(ref["source"])
        assert not source.is_absolute() and ".." not in source.parts, ref
        attachment_path = output_root.joinpath(*source.parts).resolve()
        attachment_path.relative_to(output_root)
        assert attachment_path.is_file(), ref
        actual_contents = attachment_path.read_bytes()
        assert len(actual_contents) == len(contents), (ref, actual_contents)
        expected_contents = (
            base64.b64decode(_BINARY_ATTACHMENT_BASE64, validate=True) if name == _BINARY_ATTACHMENT[0] else contents
        )
        assert actual_contents == expected_contents, (ref, actual_contents)


def _assert_session_container(context: NativeAllureConsumer, result_directory: str, result_ids: set[str]) -> None:
    directory = _consumer_path(context, result_directory)
    container_files = sorted(directory.glob("*-container.json"))
    assert container_files, f"native Allure output has no linked fixture containers in {directory}"
    containers = [_load_json(path) for path in container_files]
    shared = [container for container in containers if container.get("befores") or container.get("afters")]
    assert len(shared) == 1, containers
    per_case = [container for container in containers if container not in shared]
    assert len(per_case) == len(result_ids), containers
    per_case_children = [container.get("children") for container in per_case]
    assert all(isinstance(children, list) and len(children) == 1 for children in per_case_children), per_case
    child_ids = [
        children[0]
        for children in per_case_children
        if isinstance(children, list) and len(children) == 1 and isinstance(children[0], str)
    ]
    assert len(child_ids) == len(per_case_children), per_case
    assert set(child_ids) == result_ids, per_case
    container = shared[0]
    assert set(container.get("children", [])) == result_ids, container
    for name, key in (("pytest session start", "befores"), ("pytest session finish", "afters")):
        fixtures = container.get(key)
        assert isinstance(fixtures, list) and len(fixtures) == 1, container
        fixture = fixtures[0]
        assert isinstance(fixture, dict) and fixture.get("name") == name, fixture
        assert fixture.get("status") == "passed" and fixture.get("stage") == "finished", fixture
        _assert_timestamps(fixture, f"{name} session fixture")


@given("a fresh isolated pytest-cuke consumer is ready", target_fixture="native_allure_consumer")
def fresh_isolated_consumer(request: Any, tmp_path: Path) -> NativeAllureConsumer:
    return _context(request, tmp_path)


@given("the consumer contains one native Allure scenario with attachments")
def consumer_has_one_reportable_scenario(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(native_allure_consumer, (_REPORT_SCENARIOS[0],), with_attachments=True)


@given("the consumer contains one native Allure scenario without adapter API calls")
def consumer_has_native_scenario_without_adapter_api(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(
        native_allure_consumer,
        (_REPORT_SCENARIOS[0],),
        with_attachments=False,
        with_allure_api=False,
    )


@given("the consumer contains one live native Allure scenario with attachments")
def consumer_has_one_live_reportable_scenario(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(native_allure_consumer, (_REPORT_SCENARIOS[0],), with_attachments=True, with_live_observer=True)


@given("the consumer contains one native Allure scenario and one ordinary pytest test")
def consumer_has_native_scenario_and_ordinary_test(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(native_allure_consumer, (_REPORT_SCENARIOS[0],), with_attachments=True)
    (native_allure_consumer.project / "test_ordinary_pytest_item.py").write_text(
        "def test_ordinary_pytest_item():\n    assert 6 * 7 == 42\n",
        encoding="utf-8",
    )


@given("the consumer contains one native Allure scenario and an ordinary pytest run marker")
def consumer_has_native_scenario_and_run_marker(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(native_allure_consumer, (_REPORT_SCENARIOS[0],), with_attachments=False)
    (native_allure_consumer.project / "test_allure_run_marker.py").write_text(
        "from pathlib import Path\n\n\n"
        "def test_write_allure_run_marker():\n"
        "    Path('allure-test-run-marker').write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )


@given("the consumer contains a described native Allure outline with structured arguments")
def consumer_has_described_outline_with_arguments(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_field_contract_feature(native_allure_consumer)


@given("the consumer contains two native Allure scenarios with distinct nested steps and attachments")
def consumer_has_two_reportable_scenarios(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(
        native_allure_consumer,
        _REPORT_SCENARIOS[1:],
        with_attachments=False,
        with_xdist_evidence=True,
    )


@given("the consumer contains two native Allure scenarios with colliding worker-local Messages IDs")
def consumer_has_two_reportable_scenarios_with_colliding_ids(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_feature(
        native_allure_consumer,
        _REPORT_SCENARIOS[1:],
        with_attachments=False,
        with_xdist_evidence=True,
        with_colliding_worker_message_ids=True,
    )


@given("the consumer contains failed skipped and undefined native Allure scenarios")
def consumer_has_terminal_outcome_scenarios(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_terminal_outcomes_feature(native_allure_consumer)


@given("the consumer contains nested native Allure skip and error outcomes")
def consumer_has_nested_native_allure_outcomes(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_nested_outcome_feature(native_allure_consumer)


@given("the consumer contains a native Allure scenario with a failing Gherkin Background")
def consumer_has_failing_native_background(native_allure_consumer: NativeAllureConsumer) -> None:
    _write_background_failure_feature(native_allure_consumer)


@given(
    parsers.re(
        r"the consumer contains a scenario and a failing native run hook "
        r'"(?P<phase>BEFORE_TEST_RUN|AFTER_TEST_RUN)" with sentinel "(?P<sentinel>[^"]+)"'
    )
)
def consumer_has_failing_native_run_hook(
    phase: str,
    sentinel: str,
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    _write_run_hook_failure_feature(native_allure_consumer, phase, sentinel)


@given("the consumer installs pinned pytest-xdist")
def install_pinned_pytest_xdist(native_allure_consumer: NativeAllureConsumer) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "the xdist ownership acceptance requires uv to install its isolated test dependency"
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(native_allure_consumer.python),
            f"pytest-xdist=={_PYTEST_XDIST_VERSION}",
        ],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        purpose="installing pytest-xdist",
    )


@given("the consumer replays its first live worker batch at controller session finish")
def consumer_replays_first_live_worker_batch(native_allure_consumer: NativeAllureConsumer) -> None:
    _install_duplicate_worker_batch_replay(native_allure_consumer)


@given("the consumer installs pytest-cuke with its Allure extra")
def install_pytest_cuke_allure_extra(native_allure_consumer: NativeAllureConsumer) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "native Allure acceptance requires uv to install pytest-cuke[allure]"
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(native_allure_consumer.python),
            f"pytest-cuke[allure] @ {native_allure_consumer.artifact.resolve().as_uri()}",
        ],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        purpose="installing pytest-cuke with its Allure extra",
    )


@given("the consumer configures native Allure output in cuke_allure ini")
def configure_native_allure_ini(native_allure_consumer: NativeAllureConsumer) -> None:
    (native_allure_consumer.project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "cuke_autoload = true\n"
        "cuke_features_dir = 'features'\n"
        "cuke_allure = 'allure-results'\n",
        encoding="utf-8",
    )


@given("the consumer installs allure-python-commons without allure-pytest")
def install_native_allure_runtime_without_adapter(native_allure_consumer: NativeAllureConsumer) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "native Allure acceptance requires uv to install its isolated runtime dependency"
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(native_allure_consumer.python),
            f"allure-python-commons=={_ALLURE_PYTHON_COMMONS_VERSION}",
        ],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        purpose="installing allure-python-commons without allure-pytest",
    )
    assert_native_allure_commons_without_adapter(native_allure_consumer)


def assert_native_allure_commons_without_adapter(context: NativeAllureConsumer) -> None:
    probe = subprocess.run(
        [
            str(context.python),
            "-c",
            "from importlib.metadata import PackageNotFoundError, version\n"
            f"assert version('allure-python-commons') == '{_ALLURE_PYTHON_COMMONS_VERSION}'\n"
            "try:\n"
            "    version('allure-pytest')\n"
            "except PackageNotFoundError:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('allure-pytest must not be installed')\n",
        ],
        cwd=context.project,
        env=context.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, (
        "expected allure-python-commons at the pinned version and no allure-pytest adapter:\n"
        f"{probe.stdout}\n{probe.stderr}"
    )


@given("the consumer has allure-pytest available for its separate report")
def verify_optional_allure_pytest_available(native_allure_consumer: NativeAllureConsumer) -> None:
    probe = subprocess.run(
        [
            str(native_allure_consumer.python),
            "-c",
            "from importlib.metadata import version\nprint(version('allure-pytest'))\n",
        ],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, (
        f"allure-pytest was not installed by pytest-cuke[allure]:\n{probe.stdout}\n{probe.stderr}"
    )
    native_allure_consumer.optional_adapter_installed = True


@given("the consumer has no Allure Python adapter dependencies")
def verify_allure_adapter_absent(native_allure_consumer: NativeAllureConsumer) -> None:
    probe = subprocess.run(
        [
            str(native_allure_consumer.python),
            "-c",
            "from importlib.metadata import PackageNotFoundError, distribution\n"
            "for name in ('allure-pytest', 'allure-python-commons'):\n"
            "    try:\n"
            "        distribution(name)\n"
            "    except PackageNotFoundError:\n"
            "        continue\n"
            "    raise SystemExit(f'unexpected Allure dependency: {name}')\n",
        ],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, (
        f"native reporting unexpectedly depends on Allure Python packages:\n{probe.stdout}\n{probe.stderr}"
    )


@given(parsers.re(r'the consumer output path "(?P<relative_path>[^"]+)" is blocked by a regular file'))
def block_native_allure_output_path(relative_path: str, native_allure_consumer: NativeAllureConsumer) -> None:
    blocked_path = _consumer_path(native_allure_consumer, relative_path)
    blocked_path.write_text("This file blocks the native Allure result directory.\n", encoding="utf-8")
    assert blocked_path.is_file(), blocked_path


@when(
    parsers.re(r'I run the native Allure consumer with arguments "(?P<arguments>[^"]*)"'),
    target_fixture="native_allure_run",
)
def run_native_allure_consumer(
    arguments: str, native_allure_consumer: NativeAllureConsumer
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(native_allure_consumer.pytest), *shlex.split(arguments)],
        cwd=native_allure_consumer.project,
        env=native_allure_consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )
    native_allure_consumer.run_result = result
    return result


@when(
    parsers.re(
        r'I generate an Allure 3 report from native results in "(?P<results_path>[^"]+)" '
        r'into "(?P<report_path>[^"]+)"'
    ),
    target_fixture="native_allure_render_result",
)
def generate_native_allure_report(
    results_path: str,
    report_path: str,
    native_allure_consumer: NativeAllureConsumer,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    results_directory = _consumer_path(native_allure_consumer, results_path)
    report_directory = _consumer_path(native_allure_consumer, report_path)
    npx = shutil.which("npx")
    allure = shutil.which("allure")
    if npx:
        command = [npx, "--yes", "allure@3.20.0", "generate", str(results_directory), "-o", str(report_directory)]
    elif allure:
        version = subprocess.run([allure, "--version"], check=False, capture_output=True, text=True, timeout=30)
        version_output = f"{version.stdout}\n{version.stderr}"
        assert version.returncode == 0 and any(token.startswith("3.") for token in version_output.split()), (
            f"Allure 3 is required to render native results; installed CLI output was: {version_output}"
        )
        command = [allure, "generate", str(results_directory), "-o", str(report_directory)]
    else:
        from pytest import skip

        skip("Allure 3 CLI is not installed; add npx/Node.js or Allure 3 to PATH to generate the native HTML report")
    result = subprocess.run(
        command,
        cwd=native_allure_consumer.project,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result, report_directory


@then("the native Allure consumer should exit with code 0")
def native_allure_consumer_exits_successfully(native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    assert result.returncode == 0, f"native Allure pytest run failed:\n{result.stdout}\n{result.stderr}"


@then("the native Allure consumer should exit nonzero")
def native_allure_consumer_exits_nonzero(native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    assert result.returncode != 0, f"expected a failed pytest run, got exit code 0:\n{result.stdout}\n{result.stderr}"


@then("pytest should report an actionable native Allure dependency error")
def native_allure_dependency_error_is_actionable(native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 4, f"expected pytest UsageError exit code 4, got {result.returncode}:\n{output}"
    assert "native Allure reporting requires the optional dependency" in output, output
    assert "install pytest-cuke[allure]" in output, output


@then(parsers.re(r'pytest should report an actionable native Allure output error for "(?P<relative_path>[^"]+)"'))
def native_allure_output_error_is_actionable(relative_path: str, native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 4, f"expected pytest UsageError exit code 4, got {result.returncode}:\n{output}"
    assert "cannot initialize native Allure reporting" in output, output
    assert relative_path in output, output
    assert any(message in output.lower() for message in ("file exists", "already exists")), output


@then("pytest should reject the overlapping Allure output paths before tests run")
def native_and_adapter_output_collision_is_rejected(native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    output = f"{result.stdout}\n{result.stderr}"
    expected_message = (
        "--cuke-allure and --alluredir must use different directories when both reporting modes are enabled"
    )
    assert result.returncode == 4, f"expected pytest UsageError exit code 4, got {result.returncode}:\n{output}"
    assert expected_message in output, output
    assert not (native_allure_consumer.project / "allure-test-run-marker").exists()
    result_directory = _consumer_path(native_allure_consumer, "allure-results")
    result_files = sorted(result_directory.glob("*-result.json")) if result_directory.is_dir() else []
    assert not result_files, result_files


@then("native Allure results should preserve failed skipped and undefined cases with truthful details")
def native_allure_preserves_terminal_outcomes(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    expected_statuses = {
        "Native failed scenario preserves nested traceback": "failed",
        "Native skipped scenario preserves its reason": "skipped",
        "Native undefined scenario preserves its missing step": "broken",
    }
    assert len(results) == len(expected_statuses), results
    results_by_name = {result.get("name"): result for result in results}
    assert set(results_by_name) == set(expected_statuses), results
    for scenario_name, status in expected_statuses.items():
        result = results_by_name[scenario_name]
        assert result.get("status") == status and result.get("stage") == "finished", result
        _assert_result_and_step_timestamps(result)
        details = result.get("statusDetails")
        assert isinstance(details, dict), result
        details_text = f"{details.get('message', '')}\n{details.get('trace', '')}".lower()
        if status == "failed":
            assert "native nested failure traceback sentinel" in details_text, result
        elif status == "skipped":
            assert "native skipped scenario reason sentinel" in details_text, result
        else:
            assert "undefined native scenario step is requested" in details_text, result

    failed_result = results_by_name["Native failed scenario preserves nested traceback"]
    nested_failures = [
        item for item in _all_objects(failed_result) if item.get("name") == "Nested native failure action"
    ]
    assert len(nested_failures) == 1, failed_result
    nested_failure = nested_failures[0]
    assert nested_failure.get("status") == "failed", nested_failure
    nested_details = nested_failure.get("statusDetails")
    assert isinstance(nested_details, dict), nested_failure
    assert "native nested failure traceback sentinel" in nested_details.get("message", ""), nested_failure
    traceback_text = nested_details.get("trace")
    assert isinstance(traceback_text, str), nested_failure
    assert "AssertionError: native nested failure traceback sentinel" in traceback_text, nested_failure
    assert "native_terminal_outcome_steps.py" in traceback_text, nested_failure


@then(
    parsers.re(
        r"native Allure results should preserve matching nested skip and error statuses in "
        r'"(?P<local_path>[^"]+)" and "(?P<xdist_path>[^"]+)"'
    )
)
def native_allure_preserves_nested_outcome_parity(
    local_path: str,
    xdist_path: str,
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    expected = {
        "Native nested skip preserves its status": (
            "skipped",
            "Nested native skip action",
            "skipped",
            "native nested skip sentinel",
        ),
        "Native nested assertion failure preserves its status": (
            "failed",
            "Nested native assertion action",
            "failed",
            "native nested assertion sentinel",
        ),
        "Native nested runtime error preserves its status": (
            "failed",
            "Nested native runtime action",
            "broken",
            "native nested runtime sentinel",
        ),
    }

    def outcome_signature(relative_path: str) -> dict[str, tuple[str, str, str, str]]:
        results = [_load_json(path) for path in _result_files(native_allure_consumer, relative_path)]
        assert len(results) == len(expected), results
        signature: dict[str, tuple[str, str, str, str]] = {}
        for result in results:
            scenario_name = result.get("name")
            assert scenario_name in expected, result
            expected_case_status, nested_name, expected_nested_status, sentinel = expected[scenario_name]
            assert result.get("status") == expected_case_status and result.get("stage") == "finished", result
            nested_steps = [item for item in _all_objects(result) if item.get("name") == nested_name]
            assert len(nested_steps) == 1, result
            nested_step = nested_steps[0]
            assert nested_step.get("status") == expected_nested_status, nested_step
            details = nested_step.get("statusDetails")
            assert isinstance(details, dict) and sentinel in details.get("message", ""), nested_step
            trace = details.get("trace")
            assert isinstance(trace, str) and sentinel in trace, nested_step
            signature[scenario_name] = (
                str(result.get("status")),
                nested_name,
                str(nested_step.get("status")),
                str(details.get("message")),
            )
        assert set(signature) == set(expected), signature
        return signature

    local_signature = outcome_signature(local_path)
    xdist_signature = outcome_signature(xdist_path)
    assert local_signature == xdist_signature, (local_signature, xdist_signature)


@then("native Allure results should preserve the failed Background diagnostic")
def native_allure_preserves_failed_background(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    assert len(results) == 1, results
    result = results[0]
    assert result.get("name") == "A failed Background remains attached to its scenario", result
    assert result.get("status") == "failed" and result.get("stage") == "finished", result
    _assert_result_and_step_timestamps(result)
    result_details = result.get("statusDetails")
    assert isinstance(result_details, dict), result
    result_evidence = f"{result_details.get('message', '')}\n{result_details.get('trace', '')}"
    assert "native live Background failure sentinel" in result_evidence, result_details

    failed_background_steps = [
        step
        for step in _all_objects(result.get("steps", []))
        if step.get("name") == "Given the native Background setup fails" and step.get("status") == "failed"
    ]
    assert len(failed_background_steps) == 1, result
    step = failed_background_steps[0]
    details = step.get("statusDetails")
    assert isinstance(details, dict), step
    assert "native live Background failure sentinel" in details.get("message", ""), step
    trace = details.get("trace")
    assert isinstance(trace, str), step
    assert "native live Background failure sentinel" in trace, step
    assert "native_background_failure_steps.py" in trace, step


@then(
    parsers.re(
        r'the native Allure container should preserve the failed "(?P<phase>BEFORE_TEST_RUN|AFTER_TEST_RUN)" '
        r'fixture with sentinel "(?P<sentinel>[^"]+)"'
    )
)
def native_allure_preserves_failed_run_hook_fixture(
    phase: str,
    sentinel: str,
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    result_directory = _consumer_path(native_allure_consumer, "allure-results")
    container_files = sorted(result_directory.glob("*-container.json"))
    assert container_files, f"native Allure output has no run-hook container in {result_directory}"
    containers = [_load_json(path) for path in container_files]
    shared_containers = [container for container in containers if container.get("befores") or container.get("afters")]
    assert len(shared_containers) == 1, containers
    container = shared_containers[0]
    assert container.get("name") == "Test session", container

    fixtures_key = "befores" if phase == "BEFORE_TEST_RUN" else "afters"
    fixture_name = "pytest session start" if phase == "BEFORE_TEST_RUN" else "pytest session finish"
    fixtures = container.get(fixtures_key)
    assert isinstance(fixtures, list), container
    matching_fixtures = [fixture for fixture in fixtures if fixture.get("name") == fixture_name]
    assert len(matching_fixtures) == 1, container
    fixture = matching_fixtures[0]
    assert fixture.get("status") == "failed" and fixture.get("stage") == "finished", fixture
    _assert_timestamps(fixture, f"{phase} Allure fixture")
    details = fixture.get("statusDetails")
    assert isinstance(details, dict), fixture
    message = details.get("message")
    trace = details.get("trace")
    assert isinstance(message, str) and sentinel in message, fixture
    assert isinstance(trace, str) and sentinel in trace, fixture
    assert "RuntimeError" in trace, fixture

    results = (
        [_load_json(path) for path in sorted(result_directory.glob("*-result.json"))]
        if result_directory.is_dir()
        else []
    )
    if phase == "AFTER_TEST_RUN":
        assert len(results) == 1, results
        assert results[0].get("name") == "The scenario passes while a run hook fails", results[0]
        assert results[0].get("status") == "passed", results[0]
        _assert_result_and_step_timestamps(results[0])
        assert results[0].get("uuid") in container.get("children", []), (results[0], container)


@then(
    parsers.re(
        r"the controller-owned native Allure session container should preserve the failed "
        r'"(?P<phase>BEFORE_TEST_RUN|AFTER_TEST_RUN)" fixture with sentinel "(?P<sentinel>[^"]+)"'
    )
)
def controller_native_allure_preserves_failed_run_hook_fixture(
    phase: str,
    sentinel: str,
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    native_allure_preserves_failed_run_hook_fixture(phase, sentinel, native_allure_consumer)


@then("the native Allure 3 renderer should generate an HTML report")
def native_allure_renderer_generates_html(
    native_allure_render_result: tuple[subprocess.CompletedProcess[str], Path],
) -> None:
    result, report_directory = native_allure_render_result
    assert result.returncode == 0, f"Allure 3 renderer failed:\n{result.stdout}\n{result.stderr}"
    rendered_html = sorted(path for path in report_directory.rglob("*.html") if path.is_file())
    assert rendered_html, f"Allure 3 did not render an HTML report under {report_directory}"
    assert any(path.stat().st_size > 0 for path in rendered_html), rendered_html


@then(
    parsers.re(
        r'native Allure results in "(?P<relative_path>[^"]+)" should contain the passed scenario '
        r'"(?P<scenario_name>[^"]+)" and its steps'
    )
)
def native_allure_has_passed_scenario_and_steps(
    relative_path: str, scenario_name: str, native_allure_consumer: NativeAllureConsumer
) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, relative_path)]
    selected = [result for result in results if result.get("name") == scenario_name]
    assert len(selected) == 1, results
    _assert_result_has_passed_steps(selected[0], scenario_name=scenario_name)


@then(
    parsers.re(
        r'native Allure results in "(?P<relative_path>[^"]+)" should contain the passed scenario '
        r'"(?P<scenario_name>[^"]+)" with Gherkin steps only'
    )
)
def native_allure_has_passed_scenario_without_adapter_api_steps(
    relative_path: str,
    scenario_name: str,
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, relative_path)]
    selected = [result for result in results if result.get("name") == scenario_name]
    assert len(selected) == 1, results
    _assert_result_has_passed_steps(selected[0], scenario_name=scenario_name, require_nested_allure_step=False)
    assert not any(item.get("name") == "A nested native Allure action" for item in _all_objects(selected[0])), selected[
        0
    ]


@then("the consumer should confirm allure-pytest is absent and allure-python-commons is present")
def consumer_confirms_commons_without_adapter(native_allure_consumer: NativeAllureConsumer) -> None:
    assert_native_allure_commons_without_adapter(native_allure_consumer)


@then("native Allure results should preserve the full Gherkin field contract")
def native_allure_preserves_gherkin_field_contract(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    assert len(results) == 1, results
    result = results[0]
    expected_name = "Submit Ada profile on premium"
    assert result.get("name") == expected_name, result
    assert result.get("status") == "passed" and result.get("stage") == "finished", result
    _assert_result_and_step_timestamps(result)
    assert isinstance(result.get("uuid"), str) and result["uuid"], result
    assert isinstance(result.get("historyId"), str) and result["historyId"], result
    assert result.get("fullName") == ("file:native-field-contract.feature:Submit <customer> profile on <plan>"), result
    assert result.get("testCaseId", "").startswith("file:native-field-contract.feature:"), result
    assert result.get("description") == (
        "The feature description is preserved.\n\n"
        "The rule description is preserved.\n\n"
        "The outline description is preserved."
    ), result
    assert result.get("titlePath") == ["Native profile contract", "Profile submission", expected_name], result

    labels = result.get("labels")
    assert isinstance(labels, list), result
    label_pairs = {(label.get("name"), label.get("value")) for label in labels if isinstance(label, dict)}
    assert {
        ("feature", "Native profile contract"),
        ("parentSuite", "Native profile contract"),
        ("rule", "Profile submission"),
        ("suite", "Profile submission"),
        ("scenario", "Submit <customer> profile on <plan>"),
        ("tag", "@rule-native-tag"),
        ("tag", "@scenario-native-tag"),
    }.issubset(label_pairs), labels

    parameters = result.get("parameters")
    assert isinstance(parameters, list), result
    parameter_values = {
        parameter.get("name"): parameter.get("value") for parameter in parameters if isinstance(parameter, dict)
    }
    assert parameter_values.get("customer") == "Ada", parameters
    assert parameter_values.get("plan") == "premium", parameters
    pickle_id = parameter_values.get("pickleId")
    assert isinstance(pickle_id, str) and pickle_id.startswith("file:native-field-contract.feature#"), parameters

    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 3, result
    assert [step.get("name") for step in steps] == [
        "Given the native profile is ready",
        "When the JSON profile is accepted",
        "Then the profile fields are recorded",
    ], steps
    assert all(step.get("status") == "passed" and step.get("stage") == "finished" for step in steps), steps

    doc_string_step = steps[1]
    doc_string_content = '{"customer": "Ada", "active": true}'
    doc_string_description = f"application/json\n\n{doc_string_content}"
    assert doc_string_step.get("description") == doc_string_description, doc_string_step
    assert doc_string_step.get("descriptionHtml") == doc_string_description, doc_string_step
    assert doc_string_step.get("parameters") == [{"name": "docString", "value": doc_string_content}], doc_string_step

    data_table_step = steps[2]
    data_table_markdown = "| field | value |\n| customer | Ada |\n| active | true |"
    assert data_table_step.get("description") == data_table_markdown, data_table_step
    assert data_table_step.get("descriptionHtml") == data_table_markdown, data_table_step
    assert data_table_step.get("parameters") == [{"name": "dataTable", "value": data_table_markdown}], data_table_step

    # Feature tags are valid Gherkin metadata even though Cucumber Pickle.tags
    # only carries the rule and scenario tags for this outline.
    assert ("tag", "@feature-native-tag") in label_pairs, labels


@then("native Allure timestamps should match the live Messages timestamps")
def native_allure_timestamps_match_live_messages(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    assert len(results) == 1, results
    result = results[0]

    messages_path = _consumer_path(native_allure_consumer, "live-message-timestamps.json")
    messages = json.loads(messages_path.read_text(encoding="utf-8"))
    assert isinstance(messages, list), messages
    cases = [envelope["testCase"] for envelope in messages if isinstance(envelope, dict) and "testCase" in envelope]
    assert len(cases) == 1, cases
    test_case = cases[0]
    test_case_id = test_case.get("id")
    test_steps = test_case.get("testSteps")
    assert isinstance(test_case_id, str) and isinstance(test_steps, list), test_case
    gherkin_steps = [
        test_step
        for test_step in test_steps
        if isinstance(test_step, dict) and isinstance(test_step.get("pickleStepId"), str)
    ]
    gherkin_step_ids = [step_id for test_step in gherkin_steps if isinstance((step_id := test_step.get("id")), str)]
    assert gherkin_step_ids and len(gherkin_step_ids) == len(gherkin_steps), gherkin_steps

    case_starts = [
        envelope["testCaseStarted"]
        for envelope in messages
        if isinstance(envelope, dict)
        and isinstance(envelope.get("testCaseStarted"), dict)
        and envelope["testCaseStarted"].get("testCaseId") == test_case_id
    ]
    assert len(case_starts) == 1, case_starts
    attempt_id = case_starts[0].get("id")
    assert isinstance(attempt_id, str), case_starts[0]
    case_finishes = [
        envelope["testCaseFinished"]
        for envelope in messages
        if isinstance(envelope, dict)
        and isinstance(envelope.get("testCaseFinished"), dict)
        and envelope["testCaseFinished"].get("testCaseStartedId") == attempt_id
    ]
    assert len(case_finishes) == 1, case_finishes
    assert result.get("start") == _message_timestamp_millis(case_starts[0].get("timestamp"), "TestCaseStarted")
    assert result.get("stop") == _message_timestamp_millis(case_finishes[0].get("timestamp"), "TestCaseFinished")

    def step_timestamps(payload_name: str) -> dict[str, int]:
        events = [
            envelope[payload_name]
            for envelope in messages
            if isinstance(envelope, dict)
            and isinstance(envelope.get(payload_name), dict)
            and envelope[payload_name].get("testCaseStartedId") == attempt_id
            and envelope[payload_name].get("testStepId") in gherkin_step_ids
        ]
        event_step_ids = [event.get("testStepId") for event in events]
        assert event_step_ids == gherkin_step_ids, (payload_name, event_step_ids, gherkin_step_ids)
        return {
            step_id: _message_timestamp_millis(event.get("timestamp"), payload_name)
            for step_id, event in zip(gherkin_step_ids, events)
        }

    expected_starts = step_timestamps("testStepStarted")
    expected_finishes = step_timestamps("testStepFinished")
    allure_steps = result.get("steps")
    assert isinstance(allure_steps, list) and len(allure_steps) == len(gherkin_step_ids), result
    for index, step_id in enumerate(gherkin_step_ids):
        allure_step = allure_steps[index]
        assert isinstance(allure_step, dict), (index, allure_step)
        assert allure_step.get("start") == expected_starts[step_id], (allure_step, expected_starts[step_id])
        assert allure_step.get("stop") == expected_finishes[step_id], (allure_step, expected_finishes[step_id])


@then("native Allure results should preserve their feature hierarchy and session container")
def native_allure_preserves_hierarchy_and_session_container(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    assert len(results) == 2, results
    for result in results:
        _assert_result_has_passed_steps(result, scenario_name=str(result.get("name")))
    _assert_session_container(native_allure_consumer, "allure-results", {result["uuid"] for result in results})


@then("native Allure results should contain the text, binary, and file attachments")
def native_allure_contains_attachments(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    assert len(results) == 2, results
    selected = next((result for result in results if result.get("name") == _REPORT_SCENARIOS[0]), None)
    assert selected is not None, results
    _assert_attachment_contents(native_allure_consumer, "allure-results", selected)


@then("the native report consumer should not write a Messages NDJSON file")
def native_allure_does_not_write_ndjson(native_allure_consumer: NativeAllureConsumer) -> None:
    assert not (native_allure_consumer.project / "messages.ndjson").exists()


@then("native Allure results should contain both controller scenarios exactly once")
def native_allure_contains_two_xdist_results(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    expected_names = set(_REPORT_SCENARIOS[1:])
    actual_names = [result.get("name") for result in results]
    assert len(actual_names) == len(expected_names), results
    assert set(actual_names) == expected_names, results
    for result in results:
        case_name = "one" if result.get("name") == _REPORT_SCENARIOS[1] else "two"
        _assert_result_has_passed_steps(
            result,
            scenario_name=str(result.get("name")),
            require_nested_allure_step=False,
            expected_when_step=f"When the native xdist case {case_name} performs nested reporting",
        )


@then("native Allure results should preserve each xdist case nested steps and attachments exactly once")
def native_allure_preserves_xdist_nested_reporting(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    expected = {
        _REPORT_SCENARIOS[1]: {
            "action": "Native xdist action one",
            "detail": "Native xdist detail one",
            "attachment": "native-xdist-one.txt",
            "content": b"native xdist attachment one",
        },
        _REPORT_SCENARIOS[2]: {
            "action": "Native xdist action two",
            "detail": "Native xdist detail two",
            "attachment": "native-xdist-two.txt",
            "content": b"native xdist attachment two",
        },
    }
    assert len(results) == len(expected), results
    results_by_name = {result.get("name"): result for result in results}
    assert set(results_by_name) == set(expected), results
    output_root = _consumer_path(native_allure_consumer, "allure-results").resolve()

    for scenario_name, contract in expected.items():
        result = results_by_name[scenario_name]
        objects = list(_all_objects(result))
        action_steps = [item for item in objects if item.get("name") == contract["action"]]
        detail_steps = [item for item in objects if item.get("name") == contract["detail"]]
        other = expected[_REPORT_SCENARIOS[2] if scenario_name == _REPORT_SCENARIOS[1] else _REPORT_SCENARIOS[1]]
        assert len(action_steps) == 1, result
        assert len(detail_steps) == 1, result
        assert not any(item.get("name") in {other["action"], other["detail"]} for item in objects), result
        action = action_steps[0]
        action_descendants = list(_all_objects(action.get("steps", [])))
        assert sum(item.get("name") == contract["detail"] for item in action_descendants) == 1, action

        attachments = [item for item in _attachment_refs(result) if item.get("name") == contract["attachment"]]
        assert len(attachments) == 1, result
        assert not any(item.get("name") == other["attachment"] for item in _attachment_refs(result)), result
        attachment = attachments[0]
        assert attachment.get("type", "").split(";", 1)[0] == "text/plain", attachment
        source = PurePosixPath(attachment["source"])
        assert not source.is_absolute() and ".." not in source.parts, attachment
        attachment_path = output_root.joinpath(*source.parts).resolve()
        attachment_path.relative_to(output_root)
        assert attachment_path.is_file(), attachment
        assert attachment_path.read_bytes() == contract["content"], attachment


@then("the two xdist workers should reuse a local Messages TestCase ID for different pickles")
def xdist_workers_reuse_local_test_case_ids_for_different_pickles(native_allure_consumer: NativeAllureConsumer) -> None:
    message_files = sorted(native_allure_consumer.project.glob(".native-allure-local-messages-gw*.jsonl"))
    assert len(message_files) == 2, message_files

    structures_by_worker: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for path in message_files:
        worker_id = path.name.removeprefix(".native-allure-local-messages-").removesuffix(".jsonl")
        starts: list[dict[str, Any]] = []
        test_cases: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            envelope = json.loads(line)
            if not isinstance(envelope, dict):
                continue
            if isinstance(envelope.get("testCaseStarted"), dict):
                starts.append(envelope["testCaseStarted"])
            if isinstance(envelope.get("testCase"), dict):
                test_cases.append(envelope["testCase"])
        assert len(starts) == 1, (worker_id, starts)
        assert len(test_cases) == 1, (worker_id, test_cases)
        structures_by_worker[worker_id] = (starts[0], test_cases[0])

    assert set(structures_by_worker) == {"gw0", "gw1"}, structures_by_worker
    first_start, first_case = structures_by_worker["gw0"]
    second_start, second_case = structures_by_worker["gw1"]
    assert first_start.get("testCaseId") == first_case.get("id"), (first_start, first_case)
    assert second_start.get("testCaseId") == second_case.get("id"), (second_start, second_case)
    assert first_case.get("id") == second_case.get("id"), (first_case, second_case)

    pickle_ids = [first_case.get("pickleId"), second_case.get("pickleId")]
    assert all(isinstance(pickle_id, str) for pickle_id in pickle_ids), (first_case, second_case)
    assert pickle_ids[0] != pickle_ids[1], (first_case, second_case)
    for scenario_name in _REPORT_SCENARIOS[1:]:
        assert sum(scenario_name in pickle_id for pickle_id in pickle_ids if isinstance(pickle_id, str)) == 1, (
            scenario_name,
            pickle_ids,
        )


@then("the native Allure results should contain one shared session container for both scenarios")
def native_allure_xdist_has_one_shared_container(native_allure_consumer: NativeAllureConsumer) -> None:
    results = [_load_json(path) for path in _result_files(native_allure_consumer, "allure-results")]
    result_uuids = [result.get("uuid") for result in results]
    assert all(isinstance(result_id, str) and result_id for result_id in result_uuids), results
    result_ids = {result_id for result_id in result_uuids if isinstance(result_id, str)}
    assert len(result_ids) == len(results), results
    _assert_session_container(native_allure_consumer, "allure-results", result_ids)


@then("duplicate worker batches should be diagnosed without republishing to native Allure")
def duplicate_worker_batches_are_rejected_before_allure_publication(
    native_allure_consumer: NativeAllureConsumer,
) -> None:
    run_result = _run_result(native_allure_consumer)
    combined_output = f"{run_result.stdout}\n{run_result.stderr}"
    assert "duplicate_worker_batch" in combined_output, combined_output

    first_batch_path = _consumer_path(native_allure_consumer, "native-allure-first-worker-batch.json")
    first_batch = json.loads(first_batch_path.read_text(encoding="utf-8"))
    worker_id = first_batch.get("worker_id")
    sequence = first_batch.get("sequence")
    assert isinstance(worker_id, str) and worker_id, first_batch
    assert isinstance(sequence, int) and not isinstance(sequence, bool), first_batch

    observed_path = _consumer_path(native_allure_consumer, "native-allure-observed-worker-batches.jsonl")
    observations = [json.loads(line) for line in observed_path.read_text(encoding="utf-8").splitlines()]
    matching_observations = [
        observation
        for observation in observations
        if observation.get("worker_id") == worker_id and observation.get("sequence") == sequence
    ]

    result_directory = _consumer_path(native_allure_consumer, "allure-results")
    result_files = sorted(result_directory.glob("*-result.json")) if result_directory.is_dir() else []
    results = [_load_json(path) for path in result_files]
    expected_names = set(_REPORT_SCENARIOS[1:])
    actual_names = [result.get("name") for result in results]
    assert len(matching_observations) == 1, observations
    assert len(actual_names) == len(expected_names), results
    assert set(actual_names) == expected_names, results


@then("native and adapter Allure results should contain the exact BDD and ordinary pytest cases")
def native_and_adapter_results_have_expected_cases(native_allure_consumer: NativeAllureConsumer) -> None:
    assert native_allure_consumer.optional_adapter_installed, "allure-pytest should be installed for this scenario"
    native_directory = _consumer_path(native_allure_consumer, "native-results")
    adapter_directory = _consumer_path(native_allure_consumer, "adapter-results")
    assert native_directory.resolve() != adapter_directory.resolve()

    native_results = [_load_json(path) for path in _result_files(native_allure_consumer, "native-results")]
    native_names = [result.get("name") for result in native_results]
    assert native_names == ["Native live report scenario"], native_results
    assert native_results[0].get("status") == "passed", native_results[0]
    _assert_result_has_passed_steps(native_results[0], scenario_name="Native live report scenario")

    adapter_results = [_load_json(path) for path in _result_files(native_allure_consumer, "adapter-results")]
    adapter_names = [result.get("name") for result in adapter_results]
    expected_adapter_names = {
        "test_scenarios[file:native-allure-samples.feature-Native Allure hierarchy-Native live report scenario]",
        "test_ordinary_pytest_item",
    }
    assert len(adapter_names) == len(expected_adapter_names), adapter_results
    assert set(adapter_names) == expected_adapter_names, adapter_results
    assert all(result.get("status") == "passed" for result in adapter_results), adapter_results


@then("the consumer should have no Allure results and no Allure Python adapter dependencies")
def reporting_off_has_no_output_or_dependency(native_allure_consumer: NativeAllureConsumer) -> None:
    result = _run_result(native_allure_consumer)
    assert result.returncode == 0, f"reporting-off pytest run failed:\n{result.stdout}\n{result.stderr}"
    assert not (native_allure_consumer.project / "allure-results").exists()
    assert not (native_allure_consumer.project / "native-results").exists()
    verify_allure_adapter_absent(native_allure_consumer)
