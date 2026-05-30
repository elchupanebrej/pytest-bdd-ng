"""pytest-bdd missing test code generation."""

from pytest_bdd.compatibility.pytest import Config, ExitCode, Parser

from .const import CodeGeneration
from .plugin import CodeGeneratorPlugin
from .request import check_existence

_PLUGIN = CodeGeneratorPlugin()


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Generation")

    group.addoption(
        "--generate-missing",
        action="store_true",
        dest=CodeGeneration.Cli.GENERATE_MISSING_CODE.value,
        default=False,
        help="Generate missing bdd test code for given feature files and exit.",
    )

    group.addoption(
        "--generate",
        action="store_true",
        dest=CodeGeneration.Cli.GENERATE_CODE.value,
        default=False,
        help="Generate bdd test code for given feature files and exit.",
    )

    group.addoption(
        "--feature",
        metavar="FILE_OR_DIR",
        action="append",
        type=check_existence,
        dest=CodeGeneration.Cli.GENERATE_FROM_FEATURES.value,
        help="Feature file or directory to generate code for. Multiple allowed.",
    )


def pytest_cmdline_main(config: Config) -> int | ExitCode | None:
    """
    Check a config option to show missing code.

    Returns:
        Exit code or None.

    """
    return _PLUGIN.pytest_cmdline_main(config)
