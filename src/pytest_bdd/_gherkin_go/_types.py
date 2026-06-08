"""
Exception types for the Go gherkin parser bridge.

Responsibility:
    Exception types for the Go gherkin parser bridge. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._gherkin_go._types` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - GherkinGoNotAvailable: owns nested behavior below this boundary
    - GherkinParseError: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `_types`
    - src/pytest_bdd/collector_batch.py: imports or references `_types`

State and side effects:
    mutates self.reason, self.errors, messages.

Invariants:
    - `pytest_bdd._gherkin_go._types` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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


class GherkinGoNotAvailable(RuntimeError):
    """
    Raised when the Go shared library cannot be loaded.

    Responsibility:
        Raised when the Go shared library cannot be loaded. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._types.GherkinGoNotAvailable` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `GherkinGoNotAvailable`
        - src/pytest_bdd/collector_batch.py: imports or references `GherkinGoNotAvailable`

    State and side effects:
        mutates self.reason.

    Invariants:
        - `pytest_bdd._gherkin_go._types.GherkinGoNotAvailable` keeps its documented import path, ownership boundary,
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

    def __init__(self, reason: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._types.GherkinGoNotAvailable.__init__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._types.GherkinGoNotAvailable.__init__`
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
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/collector_batch.py: imports or references `__init__`

        State and side effects:
            mutates self.reason.

        Invariants:
            - `pytest_bdd._gherkin_go._types.GherkinGoNotAvailable.__init__` keeps its documented import path, ownership
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
            #arch-eval:locational_stability=4
        """
        super().__init__(f"Go gherkin parser not available: {reason}")
        self.reason = reason


class GherkinParseError(Exception):
    """
    Wraps structured parse errors from the Go parser.

    Maps to Python's CompositeParserException from gherkin.errors.

    Responsibility:
        Wraps structured parse errors from the Go parser. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._gherkin_go._types.GherkinParseError` because it keeps the
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
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `GherkinParseError`
        - src/pytest_bdd/collector_batch.py: imports or references `GherkinParseError`

    State and side effects:
        mutates self.errors, messages.

    Invariants:
        - `pytest_bdd._gherkin_go._types.GherkinParseError` keeps its documented import path, ownership boundary, and
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

    def __init__(self, errors: list[dict[str, object]]) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._gherkin_go._types.GherkinParseError.__init__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd._gherkin_go._types.GherkinParseError.__init__` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - err.get: collaborator call used by this boundary
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/collector_batch.py: imports or references `__init__`

        State and side effects:
            mutates self.errors, messages.

        Invariants:
            - `pytest_bdd._gherkin_go._types.GherkinParseError.__init__` keeps its documented import path, ownership
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
            #arch-eval:locational_stability=4
        """
        self.errors = errors
        messages = "; ".join(str(err.get("message", str(err))) for err in errors)
        super().__init__(f"Gherkin parse error(s): {messages}")
