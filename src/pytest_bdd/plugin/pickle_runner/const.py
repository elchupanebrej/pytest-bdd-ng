"""
Provide const helpers.

Responsibility:
    Provide const helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.const` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - Steps: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `const`

State and side effects:
    mutates LIBERAL_OPTION, MOCK_RUN, TOLERANT_STATUS, WIP_STATUS; depends on pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.const` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from pytest_bdd.compatibility.enum import StrEnum


class Steps:
    """
    Represent steps state.

    Responsibility:
        Represent steps state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.const.Steps` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Steps`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Steps`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Steps`
        - src/pytest_bdd/steps/matcher.py: imports or references `Steps`

    State and side effects:
        mutates LIBERAL_OPTION, MOCK_RUN, TOLERANT_STATUS, WIP_STATUS.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.const.Steps` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
            This entity is the information expert for `pytest_bdd.plugin.pickle_runner.const.Steps.Ini` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

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
            - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `Ini`
            - src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py: imports or references `Ini`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Ini`
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `Ini`

        State and side effects:
            mutates LIBERAL_OPTION.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.const.Steps.Ini` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

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
            This entity is the information expert for `pytest_bdd.plugin.pickle_runner.const.Steps.Cli` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

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
            - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `Cli`
            - src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py: imports or references `Cli`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Cli`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Cli`

        State and side effects:
            mutates LIBERAL_OPTION, MOCK_RUN, TOLERANT_STATUS, WIP_STATUS.

        Invariants:
            - `pytest_bdd.plugin.pickle_runner.const.Steps.Cli` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

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
        MOCK_RUN = "mock_run"
        TOLERANT_STATUS = "tolerant_status"
        WIP_STATUS = "wip_status"
