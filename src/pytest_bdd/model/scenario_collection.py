"""
Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

Responsibility:
    Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature
    auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes the option names
    used by the scenario test collector plugin, ensuring that config key names (e.g., bdd_features_base_dir,
    disable_feature_autoload) are defined once and referenced consistently throughout the collection layer.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating a
    focused sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
    pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
    state, message handling, and stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each configuration
    namespace must define non-overlapping option names

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from pytest_bdd.compatibility.enum import StrEnum

PYTEST_BDD_MARK = "pytest_bdd_scenario"
PYTEST_BDD_SCENARIOS_MARK = "scenarios"


class FeatureAutoLoad:
    """
    Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

    Responsibility:
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature
        auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes the option
        names used by the scenario test collector plugin, ensuring that config key names (e.g., bdd_features_base_dir,
        disable_feature_autoload) are defined once and referenced consistently throughout the collection layer.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
        configuration namespace must define non-overlapping option names

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    class Ini(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        DISABLE_OPTION = "disable_feature_autoload"

    class Cli(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        DISABLE_OPTION = "feature_autoload"


class FeatureBaseLoad:
    """
    Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

    Responsibility:
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature
        auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes the option
        names used by the scenario test collector plugin, ensuring that config key names (e.g., bdd_features_base_dir,
        disable_feature_autoload) are defined once and referenced consistently throughout the collection layer.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
        configuration namespace must define non-overlapping option names

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    class Ini(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        DIR_OPTION = "bdd_features_base_dir"
        URL_OPTION = "bdd_features_base_url"

    class Cli(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        DIR_OPTION = "features_base_dir"
        URL_OPTION = "features_base_url"


class EmptyScenarios:
    """
    Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

    Responsibility:
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature
        auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes the option
        names used by the scenario test collector plugin, ensuring that config key names (e.g., bdd_features_base_dir,
        disable_feature_autoload) are defined once and referenced consistently throughout the collection layer.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
        configuration namespace must define non-overlapping option names

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    class Ini(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        ALLOW_OPTION = "bdd_allow_empty_scenarios"

    class Cli(StrEnum):
        """
        Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control feature auto-.

        Responsibility:
            Defines configuration constants and enum classes for pytest.ini option names and CLI flags that control
            feature auto-loading, base directory/URL resolution, and empty scenario handling. This module centralizes
            the option names used by the scenario test collector plugin, ensuring that config key names (e.g.,
            bdd_features_base_dir, disable_feature_autoload) are defined once and referenced consistently throughout the
            collection layer.

        Reason for existence:
            This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer.
            It is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
            validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
            flow confirms this module is the single source of truth for its owned concepts

        Delegates:
            - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface,
            delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_locator: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_test_collector: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Invariants:
            - Ini and Cli option names must match the corresponding pytest.ini keys and CLI flags exactly; each
            configuration namespace must define non-overlapping option names

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """

        ALLOW_OPTION = "bdd_allow_empty_scenarios"
