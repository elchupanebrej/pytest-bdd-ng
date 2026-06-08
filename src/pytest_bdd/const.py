"""
Provide const helpers.

Responsibility:
    Provide const helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.const` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - PytestConfigParam: owns nested behavior below this boundary
    - Steps: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/feature_binding.py: imports or references `const`
    - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `const`
    - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `const`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `const`
    - src/pytest_bdd/steps/matcher.py: imports or references `const`

State and side effects:
    mutates LIBERAL_OPTION, TAG_PREFIX, PYTHON_REPLACE_REGEX, ALPHA_REGEX, CONTINUE_ON_COLLECTION_ERRORS; depends on re,
    pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.const` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

import re

from pytest_bdd.compatibility.enum import StrEnum

TAG_PREFIX = "@"

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


class PytestConfigParam(StrEnum):
    """
    Represent pytest config param state.

    Responsibility:
        Represent pytest config param state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.const.PytestConfigParam` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `PytestConfigParam`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `PytestConfigParam`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `PytestConfigParam`
        - src/pytest_bdd/steps/matcher.py: imports or references `PytestConfigParam`
        - src/pytest_bdd/util/other.py: imports or references `PytestConfigParam`

    State and side effects:
        mutates CONTINUE_ON_COLLECTION_ERRORS.

    Invariants:
        - `pytest_bdd.const.PytestConfigParam` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    CONTINUE_ON_COLLECTION_ERRORS = "continue_on_collection_errors"


class Steps:
    """
    Step execution configuration constants.

    Responsibility:
        Step execution configuration constants. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.const.Steps` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - Ini: owns nested behavior below this boundary
        - Cli: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `Steps`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Steps`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Steps`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Steps`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `Steps`

    State and side effects:
        mutates LIBERAL_OPTION.

    Invariants:
        - `pytest_bdd.const.Steps` keeps its documented import path, ownership boundary, and observable behavior stable
          for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    class Ini(StrEnum):
        """
        INI option names for step execution.

        Responsibility:
            INI option names for step execution. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.const.Steps.Ini` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `Ini`
            - src/pytest_bdd/model/feature_binding.py: imports or references `Ini`
            - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `Ini`
            - src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py: imports or references `Ini`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Ini`

        State and side effects:
            mutates LIBERAL_OPTION.

        Invariants:
            - `pytest_bdd.const.Steps.Ini` keeps its documented import path, ownership boundary, and observable behavior
              stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

        LIBERAL_OPTION = "liberal_steps"

    class Cli(StrEnum):
        """
        CLI option names for step execution.

        Responsibility:
            CLI option names for step execution. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.const.Steps.Cli` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `Cli`
            - src/pytest_bdd/model/feature_binding.py: imports or references `Cli`
            - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `Cli`
            - src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py: imports or references `Cli`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Cli`

        State and side effects:
            mutates LIBERAL_OPTION.

        Invariants:
            - `pytest_bdd.const.Steps.Cli` keeps its documented import path, ownership boundary, and observable behavior
              stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

        LIBERAL_OPTION = "liberal_steps"
