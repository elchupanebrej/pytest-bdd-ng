"""
Provide const helpers.

Responsibility:
    Provide const helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json.const` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - CucumberJson: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `const`

State and side effects:
    mutates PATH_OPTION; depends on pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.plugin.cucumber_json.const` keeps its documented import path, ownership boundary, and observable
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


class CucumberJson:
    """
    Represent cucumber json state.

    Responsibility:
        Represent cucumber json state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.const.CucumberJson` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `CucumberJson`

    State and side effects:
        mutates PATH_OPTION.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.const.CucumberJson` keeps its documented import path, ownership boundary, and
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
        #arch-eval:locational_stability=3
    """

    class Ini(StrEnum):
        """
        INI option names for Cucumber JSON output.

        Responsibility:
            INI option names for Cucumber JSON output. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.cucumber_json.const.CucumberJson.Ini` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

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
            - `pytest_bdd.plugin.cucumber_json.const.CucumberJson.Ini` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        CLI option names for Cucumber JSON output.

        Responsibility:
            CLI option names for Cucumber JSON output. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.cucumber_json.const.CucumberJson.Cli` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

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
            mutates PATH_OPTION.

        Invariants:
            - `pytest_bdd.plugin.cucumber_json.const.CucumberJson.Cli` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
