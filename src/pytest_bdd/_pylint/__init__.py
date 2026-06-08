"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint` owns documented module behavior. It directly owns the
    observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - register: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    depends on pylint.lint.PyLinter, checkers.file_size_rules.FileSizeRulesChecker,
    checkers.init_rules.InitRulesChecker, checkers.layer_rules.LayerRulesChecker, checkers.noqa_rules.NoqaRulesChecker.

Invariants:
    - `pytest_bdd._pylint` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
"""

# init: package-marker
from pylint.lint import PyLinter

from .checkers.file_size_rules import FileSizeRulesChecker
from .checkers.init_rules import InitRulesChecker
from .checkers.layer_rules import LayerRulesChecker
from .checkers.noqa_rules import NoqaRulesChecker
from .checkers.plugin_patterns import PluginPatternsChecker
from .checkers.quality_gates import QualityGatesChecker
from .checkers.responsibility_docs import ResponsibilityDocsChecker
from .checkers.test_import_rules import TestImportRulesChecker
from .checkers.typing_rules import TypingRulesChecker


def register(linter: PyLinter) -> None:
    """
    Register all custom Pylint checkers.

    Responsibility:
        Register all custom Pylint checkers. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.register` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - linter.register_checker: collaborator call used by this boundary
        - QualityGatesChecker: collaborator call used by this boundary
        - PluginPatternsChecker: collaborator call used by this boundary
        - TypingRulesChecker: collaborator call used by this boundary
        - FileSizeRulesChecker: collaborator call used by this boundary
        - LayerRulesChecker: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `register`
        - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `register`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `register`
        - src/pytest_bdd/parsers/re_parser.py: imports or references `register`
        - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `register`

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
        #arch-eval:locational_stability=4
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
