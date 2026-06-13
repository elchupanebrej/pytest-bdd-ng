"""
Define custom exception types for the Go Gherkin parser bridge: GherkinGoNotAvailable (raised when the Go shared lib.

Responsibility:
    Defines custom exception types for the Go Gherkin parser bridge: GherkinGoNotAvailable (raised when the Go shared
    library cannot be loaded) and GherkinParseError (raised when Go parser returns errors). the single primary job,
    contract, or behavior this module directly implements and owns. This defines the boundary for where changes to this
    logic belong. Must be at least 140 characters.>

Reason for existence:
    Centralizes exception type definitions for the _gherkin_go package so all modules can raise and catch the same
    specific exception types without coupling to each other. why this code is kept together in this specific module
    rather than being merged elsewhere. Why is it the information expert for this logical boundary? Analyze: imports,
    call signature, owned data, and failure knowledge. Must be at least 140 characters.>

Delegates:
    - RuntimeError: Base class for GherkinGoNotAvailable. Exception: Base class for GherkinParseError.

Cohesion:
    Two exception classes, each with a single __init__ storing structured error data. why all logic inside this entity
    belongs together. Analyze the actual source: do all functions operate on same local state? Share same imports and
    control flow? Or is it a bag of unrelated utilities?>

Separation:
    - _bridge: Kept separate because it loads the shared library (which may raise these exceptions) while _types only
    defines them.

Main consumers:
    - _gherkin_go (parse, _check_go_available): Raises these exceptions. _bridge: Imports these types.

State and side effects:
    None, keeps no persistent state. Pure exception definitions. any local mutable state, file/network I/O,
    configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
    stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
    specific data constraints, type requirements, and execution preconditions. that must always hold true for this
    entity and can never be broken. Analyze the actual source for implicit contracts.>

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""


class GherkinGoNotAvailable(RuntimeError):
    """
    RuntimeError subclass signaling that the Go gherkin parser shared library is unavailable, carrying a human-readable r.

    Responsibility:
        RuntimeError subclass signaling that the Go gherkin parser shared library is unavailable, carrying a human-
        readable reason string. the single primary job, contract, or behavior this class directly implements and owns.
        This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Provides a distinct exception type so callers can specifically catch library-availability failures. why this
        code is kept together in this specific class rather than being merged elsewhere. Why is it the information
        expert for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be
        at least 140 characters.>

    Delegates:
        - RuntimeError.__init__: Base exception initialization with formatted message.

    Cohesion:
        Single purpose: signal library unavailability with a descriptive reason. why all logic inside this entity
        belongs together. Analyze the actual source: do all functions operate on same local state? Share same imports
        and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - GherkinParseError: Kept separate because it signals parse failures rather than library unavailability.

    Main consumers:
        - _check_go_available: Raises this when gherkin_go_available() returns False. parse: Raises this when shared
        library is not found.

    State and side effects:
        None, keeps no persistent state. Exception type with reason field. any local mutable state, file/network I/O,
        configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
        stateless, specify 'None, keeps no persistent state'.>

    Invariants:
        - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
        specific data constraints, type requirements, and execution preconditions. that must always hold true for this
        entity and can never be broken. Analyze the actual source for implicit contracts.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, reason: str) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation chain.

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity,

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        super().__init__(f"Go gherkin parser not available: {reason}")
        self.reason = reason


class GherkinParseError(Exception):
    """
    RuntimeError subclass signaling that the Go gherkin parser shared library is unavailable, carrying a human-readable r.

    Responsibility:
        RuntimeError subclass signaling that the Go gherkin parser shared library is unavailable, carrying a human-
        readable reason string. the single primary job, contract, or behavior this class directly implements and owns.
        This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Provides a distinct exception type so callers can specifically catch library-availability failures. why this
        code is kept together in this specific class rather than being merged elsewhere. Why is it the information
        expert for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be
        at least 140 characters.>

    Delegates:
        - RuntimeError.__init__: Base exception initialization with formatted message.

    Cohesion:
        Single purpose: signal library unavailability with a descriptive reason. why all logic inside this entity
        belongs together. Analyze the actual source: do all functions operate on same local state? Share same imports
        and control flow? Or is it a bag of unrelated utilities?>

    Separation:
        - GherkinParseError: Kept separate because it signals parse failures rather than library unavailability.

    Main consumers:
        - _check_go_available: Raises this when gherkin_go_available() returns False. parse: Raises this when shared
        library is not found.

    State and side effects:
        None, keeps no persistent state. Exception type with reason field. any local mutable state, file/network I/O,
        configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
        stateless, specify 'None, keeps no persistent state'.>

    Invariants:
        - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
        specific data constraints, type requirements, and execution preconditions. that must always hold true for this
        entity and can never be broken. Analyze the actual source for implicit contracts.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, errors: list[dict[str, object]]) -> None:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation chain.

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity,

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.errors = errors
        messages = "; ".join(str(err.get("message", str(err))) for err in errors)
        super().__init__(f"Gherkin parse error(s): {messages}")
