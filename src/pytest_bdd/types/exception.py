"""
pytest-bdd Exceptions.

Responsibility:
    pytest-bdd Exceptions. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.types.exception` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - _FeatureLike: owns nested behavior below this boundary
    - _ScenarioLike: owns nested behavior below this boundary
    - _StepLike: owns nested behavior below this boundary
    - PytestBDDStashError: owns nested behavior below this boundary
    - PytestBDDStashLookupError: owns nested behavior below this boundary
    - PytestBDDStashAlreadyInitializedError: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `exception`
    - src/pytest_bdd/model/stash_access.py: imports or references `exception`
    - src/pytest_bdd/parser.py: imports or references `exception`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `exception`
    - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `exception`

State and side effects:
    mutates keyword, line_number, uri, name, text; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.Protocol, os.PathLike.

Invariants:
    - `pytest_bdd.types.exception` keeps its documented import path, ownership boundary, and observable behavior stable
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

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from os import PathLike


class _FeatureLike(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.types.exception._FeatureLike` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception._FeatureLike` because it keeps the nearest
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
        - src/pytest_bdd/model/stash_access.py: imports or references `_FeatureLike`
        - src/pytest_bdd/parser.py: imports or references `_FeatureLike`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_FeatureLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_FeatureLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_FeatureLike`

    State and side effects:
        mutates uri.

    Invariants:
        - `pytest_bdd.types.exception._FeatureLike` keeps its documented import path, ownership boundary, and observable
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

    uri: str


class _ScenarioLike(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.types.exception._ScenarioLike` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception._ScenarioLike` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `_ScenarioLike`
        - src/pytest_bdd/parser.py: imports or references `_ScenarioLike`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_ScenarioLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_ScenarioLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_ScenarioLike`

    State and side effects:
        mutates name.

    Invariants:
        - `pytest_bdd.types.exception._ScenarioLike` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    name: str


class _StepLike(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.types.exception._StepLike` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception._StepLike` because it keeps the nearest
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
        - src/pytest_bdd/model/stash_access.py: imports or references `_StepLike`
        - src/pytest_bdd/parser.py: imports or references `_StepLike`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `_StepLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_StepLike`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `_StepLike`

    State and side effects:
        mutates text.

    Invariants:
        - `pytest_bdd.types.exception._StepLike` keeps its documented import path, ownership boundary, and observable
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

    text: str


class PytestBDDStashError(Exception):
    """
    Base class for pytest-bdd stash access failures.

    Responsibility:
        Base class for pytest-bdd stash access failures. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.PytestBDDStashError` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `PytestBDDStashError`
        - src/pytest_bdd/parser.py: imports or references `PytestBDDStashError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `PytestBDDStashError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `PytestBDDStashError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `PytestBDDStashError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.PytestBDDStashError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class PytestBDDStashLookupError(PytestBDDStashError, LookupError):
    """
    Requested pytest-bdd stash object is missing.

    Responsibility:
        Requested pytest-bdd stash object is missing. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.PytestBDDStashLookupError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `PytestBDDStashLookupError`
        - src/pytest_bdd/parser.py: imports or references `PytestBDDStashLookupError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `PytestBDDStashLookupError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `PytestBDDStashLookupError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `PytestBDDStashLookupError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.PytestBDDStashLookupError` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class PytestBDDStashAlreadyInitializedError(PytestBDDStashError):
    """
    Stash object is being initialized more than once.

    Responsibility:
        Stash object is being initialized more than once. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.PytestBDDStashAlreadyInitializedError`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `PytestBDDStashAlreadyInitializedError`
        - src/pytest_bdd/parser.py: imports or references `PytestBDDStashAlreadyInitializedError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `PytestBDDStashAlreadyInitializedError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
          `PytestBDDStashAlreadyInitializedError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references
          `PytestBDDStashAlreadyInitializedError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.PytestBDDStashAlreadyInitializedError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class PytestBDDStashTypeMismatchError(PytestBDDStashError, TypeError):
    """
    Stash key is occupied by a value of unexpected type.

    Responsibility:
        Stash key is occupied by a value of unexpected type. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.PytestBDDStashTypeMismatchError` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `PytestBDDStashTypeMismatchError`
        - src/pytest_bdd/parser.py: imports or references `PytestBDDStashTypeMismatchError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `PytestBDDStashTypeMismatchError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
          `PytestBDDStashTypeMismatchError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `PytestBDDStashTypeMismatchError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.PytestBDDStashTypeMismatchError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, *, stash_key: str, actual_type: str, expected_type: str) -> None:
        """
        Initialize the pytest bddstash type mismatch error.

        Responsibility:
            Initialize the pytest bddstash type mismatch error. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.types.exception.PytestBDDStashTypeMismatchError.__init__` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

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
        super().__init__(f"config.stash['{stash_key}'] contains {actual_type}, expected {expected_type}.")


class MessageSchemaValidationError(ValueError):
    """
    Schema-compatible emitted message does not satisfy the canonical schema.

    Responsibility:
        Schema-compatible emitted message does not satisfy the canonical schema. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.MessageSchemaValidationError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `MessageSchemaValidationError`
        - src/pytest_bdd/parser.py: imports or references `MessageSchemaValidationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `MessageSchemaValidationError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `MessageSchemaValidationError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `MessageSchemaValidationError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.MessageSchemaValidationError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, details: str) -> None:
        """
        Initialize the message schema validation error.

        Responsibility:
            Initialize the message schema validation error. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.types.exception.MessageSchemaValidationError.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

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
        super().__init__(f"Schema-compatible message emission failed: {details}")


class ScenarioIsDecoratorOnlyError(Exception):
    """
    Scenario can be only used as decorator.

    Responsibility:
        Scenario can be only used as decorator. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.ScenarioIsDecoratorOnlyError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `ScenarioIsDecoratorOnlyError`
        - src/pytest_bdd/parser.py: imports or references `ScenarioIsDecoratorOnlyError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ScenarioIsDecoratorOnlyError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ScenarioIsDecoratorOnlyError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ScenarioIsDecoratorOnlyError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.ScenarioIsDecoratorOnlyError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class ScenarioValidationError(Exception):
    """
    Base class for scenario validation.

    Responsibility:
        Base class for scenario validation. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.ScenarioValidationError` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `ScenarioValidationError`
        - src/pytest_bdd/parser.py: imports or references `ScenarioValidationError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ScenarioValidationError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ScenarioValidationError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ScenarioValidationError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.ScenarioValidationError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class ScenarioNotFoundError(ScenarioValidationError):
    """
    Scenario Not Found.

    Responsibility:
        Scenario Not Found. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.ScenarioNotFoundError` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `ScenarioNotFoundError`
        - src/pytest_bdd/parser.py: imports or references `ScenarioNotFoundError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ScenarioNotFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ScenarioNotFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ScenarioNotFoundError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.ScenarioNotFoundError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class ExamplesNotValidError(ScenarioValidationError):
    """
    Example table is not valid.

    Responsibility:
        Example table is not valid. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.ExamplesNotValidError` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `ExamplesNotValidError`
        - src/pytest_bdd/parser.py: imports or references `ExamplesNotValidError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ExamplesNotValidError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.ExamplesNotValidError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class ScenarioExamplesNotValidError(ScenarioValidationError):
    """
    Scenario steps parameters do not match declared scenario examples.

    Responsibility:
        Scenario steps parameters do not match declared scenario examples. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.ScenarioExamplesNotValidError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `ScenarioExamplesNotValidError`
        - src/pytest_bdd/parser.py: imports or references `ScenarioExamplesNotValidError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ScenarioExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ScenarioExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ScenarioExamplesNotValidError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.ScenarioExamplesNotValidError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class FeatureExamplesNotValidError(ScenarioValidationError):
    """
    Feature example table is not valid.

    Responsibility:
        Feature example table is not valid. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.FeatureExamplesNotValidError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `FeatureExamplesNotValidError`
        - src/pytest_bdd/parser.py: imports or references `FeatureExamplesNotValidError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `FeatureExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `FeatureExamplesNotValidError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `FeatureExamplesNotValidError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.FeatureExamplesNotValidError` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class StepDefinitionNotFoundError(Exception):
    """
    Step definition not found.

    Responsibility:
        Step definition not found. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.StepDefinitionNotFoundError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `StepDefinitionNotFoundError`
        - src/pytest_bdd/parser.py: imports or references `StepDefinitionNotFoundError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `StepDefinitionNotFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `StepDefinitionNotFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `StepDefinitionNotFoundError`

    State and side effects:
        mutates keyword, line_number, undefined_parameter_type, self.undefined_parameter_type.

    Invariants:
        - `pytest_bdd.types.exception.StepDefinitionNotFoundError` keeps its documented import path, ownership boundary,
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
        #arch-eval:locational_stability=4
    """

    undefined_parameter_type: tuple[str, str] | None

    def __init__(
        self,
        feature: _FeatureLike,
        scenario: _ScenarioLike,
        step: _StepLike,
        *args: object,
    ) -> None:
        """
        Initialize the step definition not found error.

        Responsibility:
            Initialize the step definition not found error. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.types.exception.StepDefinitionNotFoundError.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates keyword, line_number, self.undefined_parameter_type.

        Invariants:
            - `pytest_bdd.types.exception.StepDefinitionNotFoundError.__init__` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.undefined_parameter_type = None
        keyword = getattr(step, "keyword", getattr(step, "prefix", "<unknown>"))
        if keyword is None:
            keyword = "<unknown>"
        line_number = getattr(step, "line_number", "<unknown>")
        if line_number is None:
            line_number = "<unknown>"
        super().__init__(
            f'Step definition is not found: "{step.text}". '
            f'Step keyword: "{keyword}". '
            f"Line {line_number} "
            f'in scenario "{scenario.name}" '
            f'in the feature "{feature.uri}"',
            *args,
        )


class NoScenariosFoundError(Exception):
    """
    No scenarios found.

    Responsibility:
        No scenarios found. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.NoScenariosFoundError` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `NoScenariosFoundError`
        - src/pytest_bdd/parser.py: imports or references `NoScenariosFoundError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `NoScenariosFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `NoScenariosFoundError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `NoScenariosFoundError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.NoScenariosFoundError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """


class FeatureParseError(Exception):
    """
    Feature parse error.

    Responsibility:
        Feature parse error. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.FeatureParseError` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `FeatureParseError`
        - src/pytest_bdd/parser.py: imports or references `FeatureParseError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `FeatureParseError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `FeatureParseError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `FeatureParseError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.types.exception.FeatureParseError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, path: str | PathLike[str], *args: object) -> None:
        """
        Initialize the feature parse error.

        Responsibility:
            Initialize the feature parse error. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.types.exception.FeatureParseError.__init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

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
        super().__init__(f"Unable to parse {path}", *args)


class FeatureConcreteParseError(FeatureParseError):
    """
    Feature parse error.

    Responsibility:
        Feature parse error. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.exception.FeatureConcreteParseError` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/stash_access.py: imports or references `FeatureConcreteParseError`
        - src/pytest_bdd/parser.py: imports or references `FeatureConcreteParseError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `FeatureConcreteParseError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `FeatureConcreteParseError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `FeatureConcreteParseError`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.types.exception.FeatureConcreteParseError` keeps its documented import path, ownership boundary,
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

    def __init__(self, message: object, line_no: object, line: object, file: object, *args: object) -> None:
        """
        Initialize the feature concrete parse error.

        Responsibility:
            Initialize the feature concrete parse error. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.types.exception.FeatureConcreteParseError.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Exception.__init__: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

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
        Exception.__init__(self, message, line_no, line, file, *args)

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self) -> str:
        """
        Return the string representation.

        Returns:
            Formatted error message.

        Responsibility:
            Return the string representation. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.types.exception.FeatureConcreteParseError.__str__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.message.format: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/stash_access.py: imports or references `__str__`
            - src/pytest_bdd/parser.py: imports or references `__str__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `__str__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__str__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `__str__`

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
        return self.message.format(*self.args[:4])
