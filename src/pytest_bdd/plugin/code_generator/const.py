"""
Provide const helpers.

Responsibility:
    Provide const helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.code_generator.const` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - CodeGeneration: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `const`

State and side effects:
    mutates BIND_FEATURE, GENERATE, GENERATE_MISSING, FEATURE, TARGET_FILE; depends on enum.Enum.

Invariants:
    - `pytest_bdd.plugin.code_generator.const` keeps its documented import path, ownership boundary, and observable
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

from enum import Enum


class CodeGeneration:
    """
    Represent code generation state.

    Responsibility:
        Represent code generation state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.code_generator.const.CodeGeneration` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Cli: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `CodeGeneration`

    State and side effects:
        mutates BIND_FEATURE, GENERATE, GENERATE_MISSING, FEATURE, TARGET_FILE.

    Invariants:
        - `pytest_bdd.plugin.code_generator.const.CodeGeneration` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    class Cli(Enum):
        """
        CLI option values for code generation.

        Responsibility:
            CLI option values for code generation. It directly owns the observable contract, local decisions, and
            maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.code_generator.const.CodeGeneration.Cli`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

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
            mutates BIND_FEATURE, GENERATE, GENERATE_MISSING, FEATURE, TARGET_FILE.

        Invariants:
            - `pytest_bdd.plugin.code_generator.const.CodeGeneration.Cli` keeps its documented import path, ownership
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

        BIND_FEATURE = "bind_feature"
        GENERATE = "generate"
        GENERATE_MISSING = "generate_missing"
        FEATURE = "feature"
        TARGET_FILE = "target_file"
        GATHER_MISSING_STEPS = "gather_missing_steps"
        GENERATE_MISSING_STEPS = "generate_missing_steps"
        KEEP_GENERATED_ON_ERROR = "keep_generated_on_error"
