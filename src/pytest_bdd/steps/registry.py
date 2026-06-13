"""
Implements the Registry attrs class — a lazy-discovery container for step definitions backed by an OrderedSet.

Responsibility:
    Implements the Registry attrs class — a lazy-discovery container for step definitions backed by an OrderedSet. The
    `registry` cached_property scans an assigned namespace (a module or object) for StepProtocol-compliant objects and
    collects their `__pytest_bdd_step_definitions__` sets into a deduplicated, ordered collection. Supports hierarchical
    parent-child chaining for fixture-based registry resolution across pytest's conftest.py hierarchy. Provides
    `inject_registry_fixture` to bind a Registry to a namespace and create a pytest fixture, the `fixture` property that
    generates the pytest fixture function establishing parent-child links, and `__iter__` for direct iteration. Also
    defines StepProtocol and StepRegistryProtocol for duck-typing namespace objects.

Reason for existence:
    This module is the information expert for step definition storage and discovery because it owns the complete
    lifecycle of how definitions are organised: how they are lazily discovered from namespace objects (via dir() and
    isinstance checks against StepProtocol), how they are stored (OrderedSet providing insertion order and
    deduplication), how they are hierarchically chained (parent attribute set by the fixture closure), and how they are
    exposed to pytest's fixture system (inject_registry_fixture + fixture property). It is kept separate from
    definition.py (which defines individual Definition objects) and matcher.py (which searches definitions) because
    storage/discovery is a distinct concern — Registry is a container, not a data element or an algorithm. The
    cached_property ensures discovery happens at most once per Registry instance, providing stable iteration order
    within a test session.

Delegates:
    - registry (cached_property): Scans self.namespace via dir(), filters for StepProtocol instances, collects their
    __pytest_bdd_step_definitions__, and returns an OrderedSet. Falls back to self._definitions if explicitly provided
    at construction, or empty OrderedSet if namespace is None.
    - inject_registry_fixture (classmethod): Creates or retrieves a Registry from the namespace via setdefaultattr,
    calls registry.fixture to generate a pytest fixture, and attaches both the fixture and __pytest_bdd_step_registry__
    to the namespace.
    - fixture (property): Returns a pytest fixture function that, when executed, sets self.parent to the parent registry
    from the fixture parameter and returns self. Also sets __pytest_bdd_step_registry__ on the fixture function for
    protocol compliance.
    - OrderedSet: The underlying ordered, deduplicated collection used for storing definitions.

Cohesion:
    Every entity serves the definition storage and discovery concern. Registry.registry discovers and stores.
    Registry.inject_registry_fixture bridges to pytest's fixture system. Registry.fixture enables parent-child chaining.
    Registry.__iter__ provides iteration. StepProtocol and StepRegistryProtocol define the duck-typed interfaces that
    namespace objects must satisfy to participate.

Separation:
    - definition.py (Definition): Defines the elements stored in the Registry; Registry owns the container, not the element.
    - matcher.py (Matcher): Searches the Registry for matching definitions; Registry owns storage, Matcher owns search.
    - manager.py (StepDefinitionManager): Plants step definitions and injects registries into namespaces; Registry
    harvests them at collection time.

Main consumers:
    - pytest_bdd.plugin.scenario_test_collector: Creates Registry instances during test collection, uses
    inject_registry_fixture to attach them to conftest.py modules, and passes registries to Matcher for step binding.
    - pytest_bdd.steps.matcher.Matcher: Iterates Registry (via __iter__) to find matching definitions for each step.
    - pytest_bdd.steps.manager.StepDefinitionManager: References Registry as a class attribute for convenience, and
    decorator_builder plants definitions that Registry later discovers.
    - User conftest.py files: Receive injected step_registry fixtures via inject_registry_fixture.

State and side effects:
    Instance-level: self.namespace (the object scanned for definitions), self._definitions (explicit definitions if
    provided, bypassing discovery), self.parent (set by the fixture closure at fixture execution time). The registry
    cached_property caches the discovered OrderedSet. inject_registry_fixture mutates the namespace by setting
    __pytest_bdd_step_registry__ and step_registry attributes. No file/network I/O.

Invariants:
    - registry is a cached_property: once computed for an instance, it always returns the same OrderedSet. Changes to
    the namespace after first access are NOT reflected.
    - If _definitions is provided at construction, registry returns it directly without namespace scanning.
    - The parent attribute is only set when the fixture function returned by the fixture property is executed by pytest.
    - StepProtocol objects must have a __pytest_bdd_step_definitions__ attribute that is a set of Definition objects.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from collections.abc import (  # noqa: TC003  -- needed at runtime for type narrowing in attrs validators
    Callable,
    Iterator,
)
from functools import cached_property
from typing import TYPE_CHECKING, cast

import pytest
from attrs import define, field
from ordered_set import OrderedSet
from typing_extensions import Protocol, runtime_checkable

from pytest_bdd.util.toolz_extra import setdefaultattr

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition


@runtime_checkable
class StepProtocol(Protocol):
    """
    Runtime-checkable Protocol defining the structural interface that step-function objects must satisfy to be discovered.

    Responsibility:
        Runtime-checkable Protocol defining the structural interface that step-function objects must satisfy to be
        discovered by Registry.registry. Requires a single attribute: `__pytest_bdd_step_definitions__`, a set of
        Definition objects attached to the function by StepDefinitionManager.decorator_builder's inner decorator. The
        @runtime_checkable decorator enables isinstance() checks at runtime, which Registry.registry uses when scanning
        namespace attributes via dir().

    Reason for existence:
        This Protocol enables duck-typing for step function discovery: Registry does not need to know the concrete type
        of step functions, only that they carry a __pytest_bdd_step_definitions__ attribute. This allows step functions
        to be created by different decorators (@given, @when, @then, @step) or even manually constructed, as long as
        they satisfy this protocol. The runtime_checkable decorator is essential because Registry.registry uses
        isinstance(value, StepProtocol) to filter namespace members.

    Delegates:
        - No delegation: pure Protocol definition with a single attribute.

    Cohesion:
        Defined alongside Registry because it is the contract that Registry's discovery mechanism depends on.
        StepProtocol and Registry form a producer-consumer pair.

    Separation:
        - StepRegistryProtocol: Defines the interface for namespace objects that carry a Registry; this defines the
        interface for step function objects that carry Definitions.
        - Definition: The type of elements in __pytest_bdd_step_definitions__; this Protocol only requires the set, not
        what it contains.

    Main consumers:
        - Registry.registry: Uses isinstance(value, StepProtocol) to filter namespace members during lazy discovery.
        - StepDefinitionManager.decorator_builder: The inner decorator ensures decorated functions satisfy this Protocol
        by setting __pytest_bdd_step_definitions__ via setdefaultattr.

    State and side effects:
        None, pure Protocol definition.

    Invariants:
        - __pytest_bdd_step_definitions__ must be a set of Definition objects, not None or any other type.
        - Any object with this attribute is considered a step container, even if the set is empty.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    __pytest_bdd_step_definitions__: set[Definition]


@runtime_checkable
class StepRegistryProtocol(Protocol):
    """
    Runtime-checkable Protocol defining the structural interface that namespace objects (modules, classes) must satisfy t.

    Responsibility:
        Runtime-checkable Protocol defining the structural interface that namespace objects (modules, classes) must
        satisfy to carry a step registry. Requires a single attribute: `__pytest_bdd_step_registry__`, a Registry
        instance. The @runtime_checkable decorator enables isinstance() checks, and the protocol is used by
        Registry.inject_registry_fixture to set this attribute on namespace objects, and by collection code to discover
        registries from conftest modules.

    Reason for existence:
        This Protocol enables duck-typing for registry-bearing objects: collection code can discover registries from
        conftest.py modules by checking for this attribute without importing Registry. The separation from StepProtocol
        is intentional — StepProtocol identifies step functions (which carry definitions), while StepRegistryProtocol
        identifies namespace modules (which carry registries). Both are needed because the discovery system operates at
        two levels: finding step functions within a module, and finding registries across conftest hierarchy.

    Delegates:
        - No delegation: pure Protocol definition with a single attribute.

    Cohesion:
        Defined alongside Registry and StepProtocol as part of the discovery infrastructure. All three protocols/classes
        together enable the full definition storage and discovery lifecycle.

    Separation:
        - StepProtocol: Identifies step function objects carrying definitions; this identifies namespace objects
        carrying registries.
        - Registry: The type of the __pytest_bdd_step_registry__ attribute; this Protocol only requires its presence,
        not its internal structure.

    Main consumers:
        - Registry.inject_registry_fixture: Sets namespace.__pytest_bdd_step_registry__ to the Registry instance via
        setdefaultattr, after casting namespace to StepRegistryProtocol.
        - pytest_bdd.plugin.scenario_test_collector: Uses __pytest_bdd_step_registry__ attribute to discover registries
        from conftest modules during collection.

    State and side effects:
        None, pure Protocol definition.

    Invariants:
        - __pytest_bdd_step_registry__ must be a Registry instance, not None or any other type.
        - The Registry instance's namespace should typically be the same object that carries this attribute.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    __pytest_bdd_step_registry__: Registry


@define
class Registry:
    """
    Attrs-based container for step definitions that supports lazy discovery from a namespace, explicit definition sets, a.

    Responsibility:
        Attrs-based container for step definitions that supports lazy discovery from a namespace, explicit definition
        sets, and parent-child chaining for hierarchical resolution. The `registry` cached_property either returns an
        explicitly provided _definitions OrderedSet, or scans the assigned namespace for StepProtocol objects and
        collects their Definitions. The `parent` attribute enables hierarchical registry lookup (Matcher falls back to
        parent registries). The classmethod `inject_registry_fixture` bridges Registry to pytest's fixture system,
        creating a fixture that resolves the registry. The `fixture` property generates the actual pytest fixture
        function that establishes parent-child links. Supports iteration via __iter__.

    Reason for existence:
        This is the central storage abstraction of the step definition layer. It exists as a class with lazy discovery
        rather than a simple list or set because: (1) definitions are distributed across multiple functions in a module
        and need to be aggregated at collection time, not decoration time, (2) the pytest conftest hierarchy requires
        parent-child registry chaining where child registries inherit definitions from parent conftest registries, (3)
        the cached_property ensures discovery happens once and the result is stable for the test session, and (4)
        injection into pytest's fixture system requires the Registry to produce its own fixture function. The class is
        attrs-based for clean field definitions with aliases (definitions → _definitions).

    Delegates:
        - registry (cached_property): The core discovery mechanism — scans namespace via dir(), filters for
        StepProtocol, collects definitions into OrderedSet.
        - inject_registry_fixture (classmethod): Creates/retrieves Registry on namespace via setdefaultattr, then
        attaches the fixture and __pytest_bdd_step_registry__.
        - fixture (property): Returns a pytest fixture function that sets self.parent and returns self; also sets
        __pytest_bdd_step_registry__ on the fixture function for duck-typing.
        - __iter__: Delegates to iter(self.registry).
        - OrderedSet: The underlying ordered, deduplicated collection.

    Cohesion:
        Every method and property serves definition storage and discovery. The two construction paths (explicit
        _definitions vs. namespace scanning), the parent chaining, and the pytest fixture integration are all facets of
        the same container abstraction.

    Separation:
        - definition.py (Definition): The elements stored; Registry owns the container.
        - matcher.py (Matcher): Iterates Registry via __iter__; Registry does not own search logic.
        - manager.py (StepDefinitionManager): References Registry as a type; decorator_builder plants definitions that
        Registry discovers.

    Main consumers:
        - pytest_bdd.plugin.scenario_test_collector: Creates Registry instances for test modules and conftest modules,
        uses inject_registry_fixture for fixture integration.
        - pytest_bdd.steps.matcher.Matcher: Iterates Registry to find matching definitions; uses registry.parent for fallback.
        - User conftest.py: Receives injected step_registry fixtures.

    State and side effects:
        Instance attributes: namespace (optional, the object scanned for definitions), _definitions (optional, explicit
        OrderedSet bypassing discovery), parent (optional, set by fixture closure). The registry cached_property
        memoises the discovery result. inject_registry_fixture mutates namespace by setting attributes. No file/network
        I/O.

    Invariants:
        - If _definitions is provided at construction, registry returns it directly; namespace is ignored for discovery
        but may still be accessed.
        - If both _definitions and namespace are None/empty, registry returns an empty OrderedSet.
        - The registry cached_property is never invalidated; if namespace contents change after first access, those
        changes are invisible.
        - parent is only set by the inner step_registry fixture function; it is None for manually constructed registries.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    namespace: StepRegistryProtocol | None = field(default=None)
    _definitions: OrderedSet[Definition] | None = field(default=None, alias="definitions")
    parent: Registry | None = field(default=None, init=False)

    @cached_property
    def registry(self) -> OrderedSet[Definition]:
        """
        The core lazy-discovery mechanism.

        Responsibility:
            The core lazy-discovery mechanism. If self._definitions was explicitly provided at construction, returns it
            directly. Otherwise, scans self.namespace via dir() to find all StepProtocol-compliant objects (those with
            __pytest_bdd_step_definitions__), collects their definition sets, and flattens them into a single
            OrderedSet. If self.namespace is None, returns an empty OrderedSet. Results are cached via @cached_property
            so discovery runs at most once per instance.

        Reason for existence:
            This property is the bridge between decoration-time definition registration (where definitions are attached
            to functions via __pytest_bdd_step_definitions__) and collection-time definition discovery (where the
            Registry aggregates them). The cached_property decorator (not property) ensures the aggregation happens
            lazily on first access and the result is stable — critical because subsequent access during test execution
            must see the same set of definitions. The isinstance check against StepProtocol (runtime_checkable) is the
            key duck-typing mechanism that decouples Registry from knowing the concrete types of step function objects.

        Delegates:
            - dir(self.namespace): Enumerates all attributes of the namespace object.
            - getattr(self.namespace, attr): Gets each attribute value for isinstance checking.
            - isinstance(value, StepProtocol): The runtime duck-typing check that identifies step containers.
            - step_container.__pytest_bdd_step_definitions__: The set of Definition objects attached to each step function.

        Cohesion:
            Directly serves the single purpose of Registry: aggregating definitions from a namespace. Every line in this
            property is part of the discovery pipeline.

        Separation:
            - inject_registry_fixture: Attaches Registry to namespace; this property reads from it.
            - __iter__: Delegates to this property for iteration.

        Main consumers:
            - Registry.__iter__: Returns iter(self.registry), which triggers lazy discovery on first call.
            - pytest_bdd.steps.matcher.Matcher.find_step_definition_matches: Iterates Registry, triggering lazy discovery.

        State and side effects:
            Reads namespace attributes via dir() and getattr() (no mutation). The result is cached on the instance
            (mutable state assignment). No file/network I/O.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=5
            #arch-eval:locational_stability=5
        """
        if self._definitions is not None:
            return self._definitions

        if self.namespace is None:
            return OrderedSet()

        step_containers: list[StepProtocol] = [
            value
            for value in [getattr(self.namespace, attr) for attr in dir(self.namespace)]
            if isinstance(value, StepProtocol)
        ]

        return OrderedSet(
            [
                step_definition
                for step_container in step_containers
                for step_definition in step_container.__pytest_bdd_step_definitions__
            ],
        )

    @classmethod
    def inject_registry_fixture(
        cls,
        namespace: StepRegistryProtocol,
    ) -> None:
        """
        Classmethod that bridges a Registry into pytest's fixture system.

        Responsibility:
            Classmethod that bridges a Registry into pytest's fixture system. Creates or retrieves a Registry instance
            from the given namespace (via setdefaultattr with a lambda factory), then attaches both the Registry's
            fixture function (as namespace.step_registry) and the Registry itself (as
            namespace.__pytest_bdd_step_registry__). This enables conftest.py modules and test modules to expose
            step_registry as a pytest fixture, making it available for dependency injection in step functions and
            collection code.

        Reason for existence:
            This method encapsulates the complete fixture injection sequence that collection code needs to perform on
            each conftest module. It exists as a classmethod (rather than an instance method or standalone function)
            because it operates on the namespace object and produces a Registry bound to that namespace, which is a
            class-level concern. The setdefaultattr pattern ensures idempotency: if a registry fixture already exists on
            the namespace, it is reused rather than replaced.

        Delegates:
            - setdefaultattr(namespace, "__pytest_bdd_step_registry__", value_factory=lambda: Registry(namespace)):
            Creates or retrieves the Registry.
            - setdefaultattr(namespace, "step_registry", step_definition_registry.fixture): Attaches the fixture function.
            - cast("StepRegistryProtocol", ...): Type-narrowing for the namespace after setting __pytest_bdd_step_registry__.

        Cohesion:
            Directly serves the Registry → pytest fixture integration. Uses Registry.registry for construction and
            Registry.fixture for fixture function generation.

        Separation:
            - fixture (property): Generates the actual pytest fixture function; this method attaches it to the namespace.
            - pytest_bdd.plugin.scenario_test_collector: Calls this method on each conftest module during collection.

        Main consumers:
            - pytest_bdd.plugin.scenario_test_collector: Invokes Registry.inject_registry_fixture(conftest_module) to
            set up conftest-level step registries.

        State and side effects:
            Mutates the namespace object by setting two attributes: __pytest_bdd_step_registry__ (the Registry instance)
            and step_registry (the pytest fixture function). The setdefaultattr pattern ensures existing attributes are
            not overwritten.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        step_definition_registry = cast(
            "Registry",
            setdefaultattr(
                namespace,
                "__pytest_bdd_step_registry__",
                value_factory=lambda: Registry(namespace),
            ),
        )
        setdefaultattr(namespace, "step_registry", step_definition_registry.fixture)

    @property
    def fixture(self) -> Callable[[Registry], Registry]:
        """
        Generates and returns a pytest fixture function named `step_registry`.

        Responsibility:
            Generates and returns a pytest fixture function named `step_registry`. The fixture accepts a `step_registry`
            parameter (which pytest resolves from parent conftest fixtures), sets self.parent to that parent registry,
            and returns self. The fixture function also has __pytest_bdd_step_registry__ set to self, enabling duck-
            typing via StepRegistryProtocol. The fixture name is intentionally the same as the parameter name, enabling
            pytest's fixture overriding mechanism for hierarchical registries.

        Reason for existence:
            This property creates the fixture that enables hierarchical registry chaining. When pytest resolves the
            `step_registry` fixture, a child conftest's fixture receives the parent conftest's registry as its
            parameter, sets self.parent, and returns the child registry. This creates a linked list of registries that
            Matcher can traverse from child to parent. The fixture function needs to be generated per Registry instance
            (hence a property, not a static method) because each Registry needs to set its own parent reference.

        Delegates:
            - @pytest.fixture: Decorates the inner step_registry function to register it with pytest.
            - Inner step_registry function: The actual fixture implementation that sets self.parent = step_registry and
            returns self.
            - cast: Type-narrowing for setting __pytest_bdd_step_registry__ on the fixture function.

        Cohesion:
            Directly serves the Registry → pytest fixture integration. The fixture function it returns is the mechanism
            by which registries participate in pytest's dependency injection.

        Separation:
            - inject_registry_fixture: Attaches this fixture to a namespace; the fixture property creates it.
            - Matcher.find_step_definition_matches: Traverses registry.parent; this property establishes the parent link.

        Main consumers:
            - inject_registry_fixture: Calls registry.fixture and attaches the returned function as namespace.step_registry.
            - pytest's fixture resolution system: Invokes the returned fixture function during test setup.

        State and side effects:
            The returned fixture function sets self.parent when executed by pytest (mutation). The fixture function
            itself has __pytest_bdd_step_registry__ set to self (attribute mutation on the function object). No
            file/network I/O.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """

        @pytest.fixture
        def step_registry(step_registry: Registry) -> Registry:
            """
            Act as the actual pytest fixture function that establishes parent-child registry chaining.

            Responsibility:
                The actual pytest fixture function that establishes parent-child registry chaining. Receives the parent
                `step_registry` from pytest's fixture resolution (typically from a conftest.py higher in the directory
                tree), sets self.parent to that parent registry, and returns self. This enables Matcher to traverse the
                registry chain from child to parent when searching for step definitions.

            Reason for existence:
                This is the mechanism by which pytest's hierarchical fixture system is leveraged for step definition
                scoping. The fixture parameter name `step_registry` matches the fixture name, so pytest's fixture
                overriding resolves it to the parent scope's step_registry fixture. By setting self.parent =
                step_registry, the child registry links to the parent, creating the chain that
                Matcher.find_step_definition_matches traverses via recursion. The nested function captures `self` from
                the enclosing fixture property.

            Delegates:
                - No delegation: simply sets self.parent and returns self.

            Cohesion:
                The sole implementation of the fixture function; exists only to establish the parent link and return the registry.

            Separation:
                - fixture (property): Creates and returns this function; the function implements the behaviour.
                - Matcher.find_step_definition_matches: Consumes the parent chain; this function establishes it.

            Main consumers:
                - pytest's fixture resolution system: Invokes this function when resolving the `step_registry` fixture.

            State and side effects:
                Mutates self.parent (sets to the parent registry). No other side effects.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=2
                #arch-eval:cohesion=5
                #arch-eval:separation=4
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
            """
            self.parent = step_registry
            return self

        cast("StepRegistryProtocol", cast("object", step_registry)).__pytest_bdd_step_registry__ = self
        return cast("Callable[[Registry], Registry]", step_registry)

    def __iter__(self) -> Iterator[Definition]:
        """
        Enable direct iteration over the Registry, yielding Definition objects.

        Responsibility:
            Enables direct iteration over the Registry, yielding Definition objects. Delegates to iter(self.registry),
            which triggers lazy discovery on first access (via the cached_property). This allows Registry instances to
            be used directly in for loops, list comprehensions, and any context that expects an iterable of Definition
            objects.

        Reason for existence:
            Provides a clean iteration interface so that consumers (primarily Matcher.find_step_definition_matches) can
            iterate over a Registry without calling .registry explicitly. The delegation to self.registry ensures that
            lazy discovery is triggered transparently on first iteration, and subsequent iterations use the cached
            result.

        Delegates:
            - iter(self.registry): Delegates to the OrderedSet's iterator after triggering lazy discovery.

        Cohesion:
            Simple delegation method that makes Registry a proper iterable. All iteration logic is in the registry
            property; this method just wires it to __iter__.

        Separation:
            - registry (property): Owns the discovery and storage logic; __iter__ is the accessor.
            - Matcher.find_step_definition_matches: Iterates Registry via `for step_definition in registry`.

        Main consumers:
            - pytest_bdd.steps.matcher.Matcher.find_step_definition_matches: The primary consumer; iterates registry to
            test each definition against matcher predicates.
            - Any code that needs to enumerate all registered step definitions.

        State and side effects:
            Triggers lazy discovery on first call (via cached_property). No mutation on subsequent calls.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        return iter(self.registry)
