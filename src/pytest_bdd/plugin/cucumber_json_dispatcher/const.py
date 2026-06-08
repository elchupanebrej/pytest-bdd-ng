"""
Provide cucumber json dispatcher constants.

Responsibility:
    Provide cucumber json dispatcher constants. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json_dispatcher.const` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - CucumberJsonDispatcher: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `const`

State and side effects:
    mutates PATH_OPTION, OPTION_ATTR, FLAG; depends on pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.plugin.cucumber_json_dispatcher.const` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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


class CucumberJsonDispatcher:
    """
    Dispatcher constants - locally duplicated to satisfy BLQ1002 cross-plugin import ban.

    WARNING: If INI/CLI option names change in cucumber_json or cucumber_json_formatter,
    update this file manually. Drift will cause silent misconfiguration.

    Responsibility:
        Dispatcher constants - locally duplicated to satisfy BLQ1002 cross-plugin import ban. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py: imports or references `CucumberJsonDispatcher`

    State and side effects:
        mutates PATH_OPTION, OPTION_ATTR, FLAG.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    class Ini(StrEnum):
        """
        INI option name for the Python JSON reporter backend.

        Responsibility:
            INI option name for the Python JSON reporter backend. It directly owns the observable contract, local
            decisions, and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher.Ini` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

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
            mutates PATH_OPTION.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher.Ini` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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

        PATH_OPTION = "cucumber_json_path"

    class Cli(StrEnum):
        """
        CLI option attribute name for the Node.js JSON formatter backend.

        Responsibility:
            CLI option attribute name for the Node.js JSON formatter backend. It directly owns the observable contract,
            local decisions, and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher.Cli` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

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
            mutates OPTION_ATTR, FLAG.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json_dispatcher.const.CucumberJsonDispatcher.Cli` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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

        OPTION_ATTR = "cucumber_js_json_path"
        FLAG = "--cucumber-json"
