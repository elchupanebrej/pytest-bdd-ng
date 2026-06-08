"""
Provide const helpers.

Responsibility:
    Provide const helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.scenario_collection` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - FeatureAutoLoad: owns nested behavior below this boundary
    - FeatureBaseLoad: owns nested behavior below this boundary
    - EmptyScenarios: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/feature_locator.py: imports or references `scenario_collection`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `scenario_collection`
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `scenario_collection`
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `scenario_collection`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `scenario_collection`

State and side effects:
    mutates DISABLE_OPTION, DIR_OPTION, URL_OPTION, ALLOW_OPTION, PYTEST_BDD_MARK; depends on
    pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.model.scenario_collection` keeps its documented import path, ownership boundary, and observable
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
    #arch-eval:locational_stability=4
"""

from pytest_bdd.compatibility.enum import StrEnum

PYTEST_BDD_MARK = "pytest_bdd_scenario"
PYTEST_BDD_SCENARIOS_MARK = "scenarios"


class FeatureAutoLoad:
    """
    Represent feature auto load state.

    Responsibility:
        Represent feature auto load state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureAutoLoad` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/feature_locator.py: imports or references `FeatureAutoLoad`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `FeatureAutoLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `FeatureAutoLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `FeatureAutoLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `FeatureAutoLoad`

    State and side effects:
        mutates DISABLE_OPTION.

    Invariants:
        - `pytest_bdd.model.scenario_collection.FeatureAutoLoad` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
        INI option names for feature autoload.

        Responsibility:
            INI option names for feature autoload. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureAutoLoad.Ini` because
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Ini`

        State and side effects:
            mutates DISABLE_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.FeatureAutoLoad.Ini` keeps its documented import path, ownership
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

        DISABLE_OPTION = "disable_feature_autoload"

    class Cli(StrEnum):
        """
        CLI option names for feature autoload.

        Responsibility:
            CLI option names for feature autoload. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureAutoLoad.Cli` because
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
            mutates DISABLE_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.FeatureAutoLoad.Cli` keeps its documented import path, ownership
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

        DISABLE_OPTION = "feature_autoload"


class FeatureBaseLoad:
    """
    Represent feature base load state.

    Responsibility:
        Represent feature base load state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureBaseLoad` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/feature_locator.py: imports or references `FeatureBaseLoad`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `FeatureBaseLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `FeatureBaseLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `FeatureBaseLoad`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `FeatureBaseLoad`

    State and side effects:
        mutates DIR_OPTION, URL_OPTION.

    Invariants:
        - `pytest_bdd.model.scenario_collection.FeatureBaseLoad` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
        INI option names for feature base loading.

        Responsibility:
            INI option names for feature base loading. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureBaseLoad.Ini` because
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Ini`

        State and side effects:
            mutates DIR_OPTION, URL_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.FeatureBaseLoad.Ini` keeps its documented import path, ownership
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

        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"

    class Cli(StrEnum):
        """
        CLI option names for feature base loading.

        Responsibility:
            CLI option names for feature base loading. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.FeatureBaseLoad.Cli` because
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
            mutates DIR_OPTION, URL_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.FeatureBaseLoad.Cli` keeps its documented import path, ownership
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

        DIR_OPTION = "features_base_dir"
        URL_OPTION = "features_base_url"


class EmptyScenarios:
    """
    Represent empty scenario handling state.

    Responsibility:
        Represent empty scenario handling state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_collection.EmptyScenarios` because it keeps
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
        - src/pytest_bdd/feature_locator.py: imports or references `EmptyScenarios`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `EmptyScenarios`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `EmptyScenarios`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `EmptyScenarios`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `EmptyScenarios`

    State and side effects:
        mutates ALLOW_OPTION.

    Invariants:
        - `pytest_bdd.model.scenario_collection.EmptyScenarios` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
        INI option names for empty scenario handling.

        Responsibility:
            INI option names for empty scenario handling. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.EmptyScenarios.Ini` because
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
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Ini`

        State and side effects:
            mutates ALLOW_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.EmptyScenarios.Ini` keeps its documented import path, ownership
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

        ALLOW_OPTION = "bdd_allow_empty_scenarios"

    class Cli(StrEnum):
        """
        CLI option names for empty scenario handling.

        Responsibility:
            CLI option names for empty scenario handling. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_collection.EmptyScenarios.Cli` because
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
            mutates ALLOW_OPTION.

        Invariants:
            - `pytest_bdd.model.scenario_collection.EmptyScenarios.Cli` keeps its documented import path, ownership
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

        ALLOW_OPTION = "bdd_allow_empty_scenarios"
