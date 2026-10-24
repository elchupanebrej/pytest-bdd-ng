"""Step definitions for the runnable run-aware hook example."""

from pathlib import Path

from pytest_cuke import given, parsers, then, when

pytest_plugins = ["run_aware_plugin"]


def _record_effect(label: str) -> None:
    with Path("run-aware-effects.log").open("a", encoding="utf-8") as stream:
        stream.write(label + "\n")


@given(parsers.parse('the first hook step records "{label}"'))
def first_hook_step(label: str) -> str:
    _record_effect(label)
    return label


@when(parsers.parse('the next hook step records "{label}"'))
def next_hook_step(label: str) -> str:
    _record_effect(label)
    return label


@then(parsers.parse('the final hook step records "{label}"'))
def final_hook_step(label: str) -> str:
    _record_effect(label)
    return label


@then("the example attaches a report")
def example_attaches_report(attach) -> None:
    attach(
        "run-aware attachment sentinel",
        media_type="text/plain",
        file_name="run-aware-report.txt",
    )
