"""
Serves as the Pylint plugin entry point for the entire `pytest_bdd._pylint` package.

Responsibility:
    Serves as the Pylint plugin entry point for the entire `pytest_bdd._pylint` package. Its single job is to
    register all 10 custom checker classes (QualityGatesChecker, PluginPatternsChecker, TypingRulesChecker,
    FileSizeRulesChecker, LayerRulesChecker, InitRulesChecker, TestImportRulesChecker, NoqaRulesChecker,
    ResponsibilityDocsChecker, TestResponsibilityDocsChecker) with the Pylint linter via the `register()` hook,
    making them available as loadable plugin checkers under the `--load-plugins=pytest_bdd._pylint` flag.

Reason for existence:
    This module exists as the single registration surface that Pylint discovers when loading the plugin. By
    centralizing all checker registration here rather than scattering it across individual checker modules, it
    provides a one-stop configuration point: adding or removing a checker from the plugin requires changing only
    the imports and `linter.register_checker()` calls in `register()`. The 10 checkers remain independently
    loadable but are collectively activated through this module. It consumes `pylint.lint.PyLinter` as its sole
    external dependency and owns the knowledge of which checkers constitute the complete plugin suite.

Delegates:
    - FileSizeRulesChecker: Delegates file-length and responsibility-cluster validation (BLQ1201/BLQ1202).
    - InitRulesChecker: Delegates __init__.py convention enforcement (BLQ1401-BLQ1404).
    - LayerRulesChecker: Delegates architectural layer import validation (BLQ1301/BLQ1302).
    - NoqaRulesChecker: Delegates noqa comment format validation (BLQ1701/BLQ1702).
    - PluginPatternsChecker: Delegates plugin structure and cross-plugin import rules (BLQ1001-BLQ1003).
    - QualityGatesChecker: Delegates code quality gate enforcement (BLQ901-BLQ903).
    - ResponsibilityDocsChecker: Delegates architecture docstring validation (BLQ910-BLQ914).
    - TestResponsibilityDocsChecker: Delegates test docstring validation (BLQ920-BLQ923).
    - TestImportRulesChecker: Delegates test import path validation (BLQ1601).
    - TypingRulesChecker: Delegates type:ignore comment validation (BLQ1101/BLQ1102).

Cohesion:
    All logic in this module is purely registration: a single `register()` function that imports all 10 checker
    classes and calls `linter.register_checker()` for each. There is no business logic, no validation, no state
    — every checker owns its own domain rules. The module is a thin orchestration layer whose sole purpose is
    wiring checkers into Pylint.

Separation:
    - checkers/__init__.py: Kept separate as a package marker only; checkers/__init__.py defines an empty
      __all__ list and has no registration responsibility, while this module is the active plugin surface.
    - Individual checker modules: Each checker module owns its own visitor logic and message definitions;
      this module only imports and registers them, never inspecting or modifying their internal state.

Main consumers:
    - pylint CLI via `--load-plugins=pytest_bdd._pylint`: Pylint calls `register(linter)` to activate all
      custom checkers.
    - Makefile / `make custom-rules`: Invokes pylint with this plugin loaded for CI/CD enforcement.

State and side effects:
    The `register()` function mutates the passed `PyLinter` object by calling `register_checker()` 10 times,
    installing each checker into Pylint's internal checker registry. No file I/O, no persistent state, no
    network access. The module-level imports of checker classes are side-effect-free.

Invariants:
    - All 10 checker classes registered in `register()` must be importable from their respective modules.
    - The order of `register_checker()` calls does not affect linting behavior.
    - Adding a new checker requires both an import and a `register_checker()` call in `register()`.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from pylint.lint import PyLinter

from .checkers.file_size_rules import FileSizeRulesChecker
from .checkers.init_rules import InitRulesChecker
from .checkers.layer_rules import LayerRulesChecker
from .checkers.noqa_rules import NoqaRulesChecker
from .checkers.plugin_patterns import PluginPatternsChecker
from .checkers.quality_gates import QualityGatesChecker
from .checkers.responsibility_docs import ResponsibilityDocsChecker
from .checkers.test_responsibility_docs import TestResponsibilityDocsChecker
from .checkers.test_import_rules import TestImportRulesChecker
from .checkers.typing_rules import TypingRulesChecker


def register(linter: PyLinter) -> None:
    """
    Installs all 10 custom Pylint checker classes into the given `PyLinter` instance by calling
    `linter.register_checker(.

    Responsibility:
        Installs all 10 custom Pylint checker classes into the given `PyLinter` instance by calling
        `linter.register_checker()` for each one: QualityGatesChecker, PluginPatternsChecker, TypingRulesChecker,
        FileSizeRulesChecker, LayerRulesChecker, InitRulesChecker, TestImportRulesChecker, NoqaRulesChecker,
        ResponsibilityDocsChecker, and TestResponsibilityDocsChecker. This is the Pylint-standard plugin hook
        that makes the entire `pytest_bdd._pylint` checker suite active when the plugin is loaded.

    Reason for existence:
        This function exists as the singular entry point mandated by Pylint's plugin protocol. Pylint discovers
        plugins by calling `register(linter)` on the plugin package. Without this function, none of the 10 custom
        checkers would be activated. It consolidates what would otherwise be 10 separate plugin load statements
        into one, and ensures consistent initialization order. It is the information expert for which checkers
        constitute the complete pytest-bdd-ng linting suite.

    Delegates:
        - QualityGatesChecker: Registered first; handles code quality gates (BLQ901-BLQ903).
        - PluginPatternsChecker: Handles plugin structure rules (BLQ1001-BLQ1003).
        - TypingRulesChecker: Handles type:ignore comment rules (BLQ1101/BLQ1102).
        - FileSizeRulesChecker: Handles file size rules (BLQ1201/BLQ1202).
        - LayerRulesChecker: Handles architectural layer rules (BLQ1301/BLQ1302).
        - InitRulesChecker: Handles __init__.py rules (BLQ1401-BLQ1404).
        - TestImportRulesChecker: Handles test import path rules (BLQ1601).
        - NoqaRulesChecker: Handles noqa comment rules (BLQ1701/BLQ1702).
        - ResponsibilityDocsChecker: Handles architecture docstring rules (BLQ910-BLQ914).
        - TestResponsibilityDocsChecker: Handles test docstring rules (BLQ920-BLQ923).

    Cohesion:
        The function does exactly one thing: iterates through 10 checker instantiations and registers them.
        There are no conditionals, no branching logic, no configuration — pure sequential registration.

    Separation:
        - checkers/__init__.py: The package marker is passive; this function is the active registration
          surface that Pylint calls.
        - Individual checker `register()` methods: Each checker could hypothetically self-register, but this
          centralized function prevents tight coupling between checker modules and Pylint's lifecycle.

    Main consumers:
        - Pylint CLI: Invoked automatically when `--load-plugins=pytest_bdd._pylint` is specified.
        - `make custom-rules` / CI: The standard way to run all custom linting rules on the codebase.

    State and side effects:
        Mutates the `PyLinter` instance by adding 10 checker objects to its internal registry. Each checker
        receives a reference to the linter via its constructor. No file I/O, no network access. The linter
        becomes permanently modified for its lifetime.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    linter.register_checker(QualityGatesChecker(linter))
    linter.register_checker(PluginPatternsChecker(linter))
    linter.register_checker(TypingRulesChecker(linter))
    linter.register_checker(FileSizeRulesChecker(linter))
    linter.register_checker(LayerRulesChecker(linter))
    linter.register_checker(InitRulesChecker(linter))
    linter.register_checker(TestImportRulesChecker(linter))
    linter.register_checker(NoqaRulesChecker(linter))
    linter.register_checker(ResponsibilityDocsChecker(linter))
    linter.register_checker(TestResponsibilityDocsChecker(linter))
