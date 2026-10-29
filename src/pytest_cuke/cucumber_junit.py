"""Selection and pytest configuration for the message-driven Cucumber JUnit XML report."""

from __future__ import annotations

from argparse import ArgumentTypeError
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config as BaseConfig
    from pytest_cuke.compatibility.pytest import Parser


DEFAULT_CUCUMBER_JUNIT_PATH = "cucumber.xml"


def add_options(parser: Parser) -> None:
    """Add the canonical optional-path JUnit XML selection and INI setting."""
    group = parser.getgroup("cuke", "Cucumber JUnit XML")
    group.addoption(
        "--cuke-junit",
        action="store",
        nargs="?",
        const=DEFAULT_CUCUMBER_JUNIT_PATH,
        dest="cuke_junit",
        metavar="PATH",
        default=None,
        type=_required_output_path,
        help="write the message-driven Cucumber JUnit XML report to PATH (default: cucumber.xml)",
    )
    parser.addini("cuke_junit", "Cucumber JUnit XML report path.", default="", type="string")


def configured_cucumber_junit_output_value(config: BaseConfig) -> str | None:
    """Return the selected JUnit XML destination, if either CLI or INI enabled it."""
    option = getattr(getattr(config, "option", None), "cuke_junit", None)
    if option is None:
        getini = getattr(config, "getini", None)
        option = getini("cuke_junit") if callable(getini) else None
    if not isinstance(option, (str, Path)) or not option:
        return None
    return str(option)


def _required_output_path(value: str) -> str:
    if not value:
        raise ArgumentTypeError("Cucumber JUnit XML output path must not be empty")
    return value


__all__ = ["DEFAULT_CUCUMBER_JUNIT_PATH", "add_options", "configured_cucumber_junit_output_value"]
