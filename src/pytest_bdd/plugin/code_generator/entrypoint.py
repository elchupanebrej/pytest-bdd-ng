"""
pytest-bdd missing test code generation.

Responsibility:
    pytest-bdd missing test code generation. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.entrypoint` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addoption: owns nested behavior below this boundary
    - pytest_cmdline_main: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates _PLUGIN, group; depends on pytest_bdd.compatibility.pytest.Config, pytest_bdd.compatibility.pytest.ExitCode,
    pytest_bdd.compatibility.pytest.Parser, const.CodeGeneration, plugin.CodeGeneratorPlugin.

Invariants:
    - `pytest_bdd.plugin.code_generator.entrypoint` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from pytest_bdd.compatibility.pytest import Config, ExitCode, Parser

from .const import CodeGeneration
from .plugin import CodeGeneratorPlugin

_PLUGIN = CodeGeneratorPlugin()


def pytest_addoption(parser: Parser) -> None:
    """
    Add pytest-bdd options.

    Responsibility:
        Add pytest-bdd options. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.entrypoint.pytest_addoption` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - group.addoption: collaborator call used by this boundary
        - parser.getgroup: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates group.

    Invariants:
        - `pytest_bdd.plugin.code_generator.entrypoint.pytest_addoption` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    group = parser.getgroup("bdd", "Generation")

    group.addoption(
        "--generate",
        action="store_true",
        dest=CodeGeneration.Cli.GENERATE.value,
        default=False,
        help="Generate pytest-bdd test scaffolding for feature file(s) and exit.",
    )

    group.addoption(
        "--feature",
        action="append",
        dest=CodeGeneration.Cli.FEATURE.value,
        default=[],
        metavar="FEATURE_FILE",
        help="Feature file to use for legacy code generation commands.",
    )

    group.addoption(
        "--bind-feature",
        action="store_true",
        dest=CodeGeneration.Cli.BIND_FEATURE.value,
        default=False,
        help="Bind feature file(s) to a target pytest file and exit.",
    )

    group.addoption(
        "--target-file",
        metavar="PYTHON_FILE",
        dest=CodeGeneration.Cli.TARGET_FILE.value,
        help="Target pytest file for code-generation edits.",
    )

    group.addoption(
        "--gather-missing-steps",
        action="store_true",
        dest=CodeGeneration.Cli.GATHER_MISSING_STEPS.value,
        default=False,
        help="Emit NDJSON events for missing scenario bindings and step definitions.",
    )

    group.addoption(
        "--generate-missing",
        action="store_true",
        dest=CodeGeneration.Cli.GENERATE_MISSING.value,
        default=False,
        help="Print generated missing step skeletons for feature file(s) and exit.",
    )

    group.addoption(
        "--generate-missing-steps",
        action="store_true",
        dest=CodeGeneration.Cli.GENERATE_MISSING_STEPS.value,
        default=False,
        help="Append generated missing step skeletons to a target pytest file and exit.",
    )

    group.addoption(
        "--keep-generated-on-error",
        action="store_true",
        dest=CodeGeneration.Cli.KEEP_GENERATED_ON_ERROR.value,
        default=False,
        help="Keep edited target file when formatting or syntax validation fails.",
    )


def pytest_cmdline_main(config: Config) -> int | ExitCode | None:
    """
    Check a config option to show missing code.

    Returns:
        Exit code or None.

    Responsibility:
        Check a config option to show missing code. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.entrypoint.pytest_cmdline_main`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _PLUGIN.pytest_cmdline_main: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/xdist_worker.py: imports or references `pytest_cmdline_main`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return _PLUGIN.pytest_cmdline_main(config)
