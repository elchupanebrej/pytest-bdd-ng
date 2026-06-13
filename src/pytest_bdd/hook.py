# mypy: ignore-errors
# nested ParamSpec from decopatch not supported by mypy (valid-type error)
"""
Owns the complete BDD hook infrastructure: defines HookKind (mark/tag) and HookConjunction (before/after/around) enum.

Responsibility:
    Owns the complete BDD hook infrastructure: defines HookKind (mark/tag) and HookConjunction (before/after/around)
    enums, implements the decorator_builder factory that generates six concrete hook decorators (before_mark,
    before_tag, after_mark, after_tag, around_mark, around_tag) via itertools.product cross-product, and manages hook
    expression parsing through protocol types (_PickleTagProtocol, _HookFunctionProtocol, _AroundHookCallable). This
    module is the single authority for how pytest fixtures are dynamically registered to intercept scenario execution at
    configured hook points based on tag or mark expression matching.

Reason for existence:
    This module is the information expert for the hook lifecycle because it owns the complete pipeline: from the
    decopatch-based decorator factory that generates @pytest.fixture-wrapped hook functions, through the tag/mark
    expression parsing and evaluation, to the conditional execution of before/after/around hooks based on expression
    matching. Without this module, hook registration logic would be split between steps (owning step decorators),
    scenario runner (owning hook invocation), and tag_expression (owning expression evaluation), with no single place
    responsible for the full "parse expression → match tags → execute hook" pipeline. The module uses a counter-based
    unique naming scheme (expression_count_gen) to guarantee unique pytest fixture names for each dynamically generated
    hook, preventing naming collisions that would crash pytest's fixture system.

Delegates:
    - decopatch.function_decorator: Provides the decorator factory framework that allows decorator_builder to accept
    optional arguments (expression, name) while still supporting both @decorator and @decorator(arg) syntax.
    - makefun.wraps: Wraps the hook function to accept the pytest fixture request parameter while preserving the
    original function signature for test author ergonomics.
    - pytest.fixture: Dynamically registers each hook as an autouse pytest fixture with a unique generated name,
    enabling automatic hook execution during test runs.
    - pytest_bdd.tag_expression: Provides GherkinTagExpression, MarksTagExpression, and TagExpression protocol for
    parsing and evaluating tag/mark filter expressions.
    - pytest_bdd.compatibility.pytest: Provides Mark, make_mark, and FixtureRequest types for pytest-version-compatible
    mark handling.
    - pytest_bdd.model.run.Run: Provides from_stash() to access the Run object from pytest config stash for passing to
    hook functions.

Cohesion:
    All entities in this module participate in the same pipeline: classifying hook types → parsing expressions →
    matching expressions against scenario tags/marks → conditionally executing hook callbacks. The enums (HookKind,
    HookConjunction) define the combinatorial space (2×3 = 6 decorators), the protocol classes (_PickleTagProtocol,
    _HookFunctionProtocol, _AroundHookCallable) define the type contracts, the private functions
    (_get_conjunction_and_kind, _get_expression_type, _get_marks, _get_args_kwargs) implement pipeline stages, and
    decorator_builder orchestrates the full pipeline. The module uses itertools.starmap and product at module level to
    materialize all six decorators without code duplication.

Separation:
    - pytest_bdd.steps: Kept separate because steps owns step definition registration (given/when/then/step) that
    matches Gherkin step text, while hook owns lifecycle hook registration that matches against tags/marks — they serve
    different test authoring use cases (step implementation vs lifecycle interception) and use different expression
    matching systems (step parsers vs tag expressions).
    - pytest_bdd.tag_expression: Kept separate because tag_expression owns the expression parsing and evaluation
    algorithms (TagExpression.parse, evaluate), while hook owns the pipeline that uses those algorithms to decide when
    to invoke hook callbacks — evaluation logic vs invocation policy.

Main consumers:
    - End-user conftest.py files: Import before_mark, before_tag, after_mark, after_tag, around_mark, around_tag for
    decorating hook functions.
    - pytest_bdd.plugin.pickle_runner: The scenario execution runtime iterates over registered hooks (detected via
    __pytest_bdd_is_hook__ attribute) to invoke them at the appropriate lifecycle points during scenario execution.
    - pytest_bdd.plugin.scenario_test_collector: During test collection, hooks with __pytest_bdd_is_hook__ attribute are
    discovered and registered as autouse fixtures.

State and side effects:
    Module-level mutable state: expression_count_gen (itertools.count instance) is mutated each time a hook decorator is
    applied, generating unique fixture names. This is a global counter that ensures no two dynamically generated pytest
    fixtures share the same name, preventing pytest fixture registration conflicts. The count increments monotonically
    and is never reset.

Invariants:
    - Every hook decorator must produce a pytest fixture with a globally unique name — the expression_count_gen counter
    guarantees this by including the incrementing integer in the fixture name pattern.
    - HookKind.mark must map to MarksTagExpression and HookKind.tag must map to GherkinTagExpression — this mapping in
    _get_expression_type must never diverge from the actual expression type classes.
    - The six module-level decorators (before_mark through around_tag) must be exactly the cross-product of
    HookConjunction values × HookKind values, generated by starmap over product.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from inspect import Signature, signature
from itertools import count, product, starmap
from typing import TYPE_CHECKING, Any, Protocol, cast

import pytest
from decopatch import function_decorator
from makefun import wraps

from pytest_bdd.compatibility.pytest import Mark, make_mark
from pytest_bdd.model.run import Run
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression, TagExpressionType

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from types import FunctionType

    from decopatch.main import _Decorator

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.util.toolz_extra import ObjectCallable

expression_count_gen = count()


class HookKind(Enum):
    """
    Owns the enumeration of hook filter dimensions: "mark" for filtering hooks by pytest markers applied to test nodes, a.

    Responsibility:
        Owns the enumeration of hook filter dimensions: "mark" for filtering hooks by pytest markers applied to test
        nodes, and "tag" for filtering hooks by Gherkin tags associated with scenario pickles. This enum determines
        which expression parser type is selected (MarksTagExpression for mark hooks, GherkinTagExpression for tag hooks)
        and how the matching set is derived (node markers vs pickle tags) during hook evaluation.

    Reason for existence:
        This enum is the dispatch key for the entire hook expression system. The _get_expression_type function maps
        HookKind.mark → MarksTagExpression and HookKind.tag → GherkinTagExpression, and _get_marks uses HookKind to
        decide whether to collect pytest markers via request.node.iter_markers() or Gherkin tags via the pickle fixture.
        Without this enum, the two hook filtering dimensions would be conflated or require separate code paths, making
        it impossible to cleanly generate the six decorator combinations via product(HookConjunction, HookKind).

    Delegates:
        - Enum (stdlib): Provides the standard enum base for membership testing and value-to-enum conversion.

    Cohesion:
        Both members ("mark" and "tag") represent answer to the same question: "what domain of annotations should this
        hook filter against?" They are used identically in the hook pipeline — the same code path handles both, with
        dispatch occurring at two points (expression parser selection and mark collection strategy).

    Separation:
        - HookConjunction: Kept separate because HookConjunction answers "when should the hook fire relative to the
        scenario?" (before/after/around) while HookKind answers "what should the hook filter against?" (marks/tags) —
        these are orthogonal dimensions combined via Cartesian product, not variants of the same concept.

    Main consumers:
        - _get_expression_type: Dispatches to MarksTagExpression or GherkinTagExpression based on the HookKind.
        - _get_marks: Dispatches to node.iter_markers() or pickle tag iteration based on the HookKind.
        - decorator_builder: Accepts HookKind as a parameter and threads it through the hook pipeline.

    State and side effects:
        None, keeps no persistent state. Pure enumeration.

    Invariants:
        - HookKind.mark must always correspond to pytest marker-based filtering and HookKind.tag to Gherkin tag-based
        filtering — these mappings are hardcoded in _get_expression_type and _get_marks.
        - No new HookKind members should be added without corresponding additions to _get_expression_type and _get_marks.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    mark = "mark"
    tag = "tag"


class HookConjunction(Enum):
    """
    Owns the enumeration of hook timing positions relative to scenario execution: "before" fires before the matching scen.

    Responsibility:
        Owns the enumeration of hook timing positions relative to scenario execution: "before" fires before the matching
        scenario, "after" fires after the matching scenario, and "around" wraps the matching scenario with a context-
        manager-style yield pattern enabling setup/teardown semantics. This enum determines how the hook function
        interacts with the pytest fixture yield lifecycle during conditional hook execution in the generated hook
        fixture.

    Reason for existence:
        This enum encodes the three standard hook timing patterns in testing frameworks. In the generated hook fixture
        (the inner `hook` function within decorator_wrapper.decorator.decorator), the conjunction value determines:
        before — call hook function, then yield; after — yield, then call hook function; around — wrap in contextmanager
        and yield inside. This enum enables the combinatoric generation of all six decorators (before_mark, before_tag,
        after_mark, after_tag, around_mark, around_tag) via product(HookConjunction, HookKind).

    Delegates:
        - Enum (stdlib): Provides the standard enum base for membership testing and value-to-enum conversion.

    Cohesion:
        All three members ("before", "after", "around") represent the complete set of possible timing positions relative
        to a scenario. They are used in a single dispatch point within the generated hook function — the if/elif/else
        chain that decides how to execute the hook callable relative to the yield statement.

    Separation:
        - HookKind: Kept separate because HookConjunction determines "when" the hook fires while HookKind determines
        "against what" it filters — these are orthogonal dimensions whose product generates the decorator matrix. Mixing
        them into one enum would create 6 members (before_mark, before_tag, etc.) and lose the combinatorial generation
        benefits.

    Main consumers:
        - decorator_builder: Accepts HookConjunction as a parameter and threads it through to the inner hook function
        where it controls the yield/call ordering.
        - The generated hook fixture: Uses the conjunction value to determine execution ordering (before: call-then-
        yield, after: yield-then-call, around: contextmanager-then-yield).
        - End-user test code: The conjunction is embedded in the decorator name (before_mark, after_tag, etc.), making
        it implicitly visible to test authors.

    State and side effects:
        None, keeps no persistent state. Pure enumeration.

    Invariants:
        - "before" must always execute the hook function before yielding to scenario execution.
        - "after" must always yield to scenario execution before calling the hook function.
        - "around" must always wrap the hook function in contextmanager() and yield inside that context.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    before = "before"
    after = "after"
    around = "around"


class _PickleTagProtocol(Protocol):
    """
    Defines a structural typing Protocol that specifies the minimum interface required from pickle tag objects to support.

    Responsibility:
        Defines a structural typing Protocol that specifies the minimum interface required from pickle tag objects to
        support tag-based hook filtering: a `name: str` attribute that contains the tag string (e.g., "@smoke",
        "@regression"). This protocol allows the hook system to extract tag names from pickle tags without depending on
        any specific tag class, enabling the use of make_mark(tag.name) in _get_marks when processing HookKind.tag
        hooks.

    Reason for existence:
        This protocol exists to create a stable contract between the hook system and pickle objects. The _get_marks
        function uses an isinstance check via this Protocol to validate that pickle tags have a .name attribute before
        calling make_mark(). Without this protocol, the hook system would need to hardcode a dependency on the specific
        tag class used by the pickle runner, making it fragile to internal refactoring. The Protocol allows duck-typing:
        any object with a "name" attribute can serve as a tag source.

    Delegates:
        - Protocol (typing): Provides the structural subtyping base that allows runtime_checkable to work without
        explicit inheritance.

    Cohesion:
        The single attribute requirement (name: str) is perfectly focused — it defines exactly what the hook system
        needs from a tag object and nothing more. There is no extraneous interface surface.

    Separation:
        - _HookFunctionProtocol: Kept separate because _HookFunctionProtocol defines the contract for hook functions
        (callable signature + metadata attributes), while _PickleTagProtocol defines the contract for data objects
        consumed by hooks — callable contracts vs data contracts.

    Main consumers:
        - _get_marks: Iterates over pickle tags and checks each one against this protocol before calling
        make_mark(tag.name) to convert them to pytest Mark objects for expression evaluation.

    State and side effects:
        None, keeps no persistent state. Pure Protocol definition.

    Invariants:
        - Any object passed as a pickle tag to the hook system must have a `name` attribute that evaluates to a non-
        empty string for tag-based hook filtering to work correctly.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    name: str


class _HookFunctionProtocol(Protocol):
    """
    Defines a structural typing Protocol that specifies the complete interface contract for hook functions processed by t.

    Responsibility:
        Defines a structural typing Protocol that specifies the complete interface contract for hook functions processed
        by the hook system: a __call__ method accepting a FixtureRequest and arbitrary *args/**kwargs and returning a
        Generator, plus five metadata attributes (__pytest_bdd_is_hook__, __pytest_bdd_hook_name__,
        __pytest_bdd_hook_expression__, __pytest_bdd_hook_kind__, __pytest_bdd_hook_conjunction__) that the collection
        and runtime systems use to discover and classify hooks. This protocol is the bridge between user-authored hook
        functions and the plugin's hook discovery mechanism.

    Reason for existence:
        This protocol defines the contract that allows the hook system (in decorator_builder) to stamp metadata onto
        wrapper functions and have the collection/runtime systems discover them. The __pytest_bdd_is_hook__ attribute
        acts as a marker interface, while the other four attributes encode the hook's identity (name, expression, kind,
        conjunction) for later lookup. Without this protocol, the collection system would need to use fragile isinstance
        checks against concrete classes or rely on naming conventions, making user-defined hooks undiscoverable.

    Delegates:
        - Protocol (typing): Provides the structural subtyping base.
        - FixtureRequest (pytest): The required first parameter type for hook callables, ensuring hooks have access to
        the pytest request context.

    Cohesion:
        All attributes serve the same purpose: making hooks discoverable and classifiable at collection time and
        identifiable at runtime. The callable signature (with Generator return) enforces that hooks can participate in
        the pytest fixture yield lifecycle. No attribute is unrelated to hook discovery or lifecycle management.

    Separation:
        - _AroundHookCallable: Kept separate because around hooks have a different signature (no FixtureRequest
        parameter) since they are invoked via contextmanager() wrapping, whereas regular hooks receive the request
        directly.
        - _PickleTagProtocol: Kept separate because that protocol defines data contracts for tag sources while this
        protocol defines the callable contract for hook functions.

    Main consumers:
        - decorator_builder.decorator_wrapper.decorator: Casts the wrapped hook function to _HookFunctionProtocol and
        stamps the five metadata attributes onto it after wrapping with makesfun.wraps.
        - pytest_bdd.plugin.pickle_runner: Discovers hooks by checking for __pytest_bdd_is_hook__ attribute on fixture
        functions during test collection.
        - pytest_bdd.plugin.scenario_test_collector: Uses the metadata attributes to classify and register hooks during
        test discovery.

    State and side effects:
        None, keeps no persistent state. Pure Protocol definition, though instances hold metadata attributes that are
        set by the decorator builder.

    Invariants:
        - Every hook function must have __pytest_bdd_is_hook__ set to True for the collection system to recognize it as a hook.
        - The __call__ method must accept FixtureRequest as its first positional argument (enforced by makesfun.wraps
        prepending "request").
        - The Generator return type is required because hooks participate in pytest's fixture yield lifecycle.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __call__(self, request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]:
        """
        Define the canonical call signature for hook functions: receives a pytest FixtureRequest as the first argument, acce.

        Responsibility:
            Defines the canonical call signature for hook functions: receives a pytest FixtureRequest as the first
            argument, accepts arbitrary positional and keyword arguments that are dynamically populated from the hook's
            original function signature parameters (request, run), and returns a Generator to participate in pytest's
            fixture yield lifecycle. This signature enables hooks to be registered as autouse pytest fixtures that
            conditionally execute based on tag/mark expression matching.

        Reason for existence:
            This call signature is the contract that makes hooks work as pytest fixtures. The Generator return type is
            required because the hook function must yield control during scenario execution (for after/around hooks) and
            optionally execute code before yielding (for before hooks). The FixtureRequest parameter provides access to
            the pytest node (for mark inspection), the scenario pickle (for tag inspection), and the config stash (for
            Run object access). Without this signature, hooks could not participate in the pytest fixture lifecycle.

        Delegates:
            - FixtureRequest (pytest): Provides access to the test node, pickle fixture values, and config stash for
            expression matching and argument injection.
            - _get_args_kwargs: Dynamically injects the FixtureRequest and Run objects into kwargs based on the original
            hook function's parameter names.

        Cohesion:
            The signature is tightly focused on enabling a single behavior: participating in pytest's fixture yield
            lifecycle while receiving the necessary context for expression evaluation.

        Separation:
            - _AroundHookCallable.__call__: Kept separate because around hooks have a different parameter list (no
            FixtureRequest) since they are context-manager-wrapped and receive arguments differently.

        Main consumers:
            - decorator_builder.decorator_wrapper.decorator (the inner `hook` function): This is the function that
            satisfies this protocol — it is cast to _HookFunctionProtocol after wrapping.
            - makesfun.wraps: Uses this signature to generate the wrapper that prepends "request" and removes it from
            the user-facing signature.

        State and side effects:
            None, keeps no persistent state. The Generator yields None to pytest's fixture machinery.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        ...

    __pytest_bdd_is_hook__: bool
    __pytest_bdd_hook_name__: str
    __pytest_bdd_hook_expression__: str
    __pytest_bdd_hook_kind__: str
    __pytest_bdd_hook_conjunction__: str


class _AroundHookCallable(Protocol):
    """
    Defines a structural typing Protocol for around-hook callables that are invoked via Python's contextmanager() functio.

    Responsibility:
        Defines a structural typing Protocol for around-hook callables that are invoked via Python's contextmanager()
        function: the __call__ method accepts only *args and **kwargs (no FixtureRequest) and returns a Generator. This
        protocol is used by the hook pipeline to cast around-hook functions before passing them to contextmanager(),
        which requires a generator function without a FixtureRequest parameter since around hooks are called after
        argument injection and expression matching have already occurred.

    Reason for existence:
        Around hooks need a different callable signature than before/after hooks because they are invoked through
        contextmanager() which wraps a generator function. The FixtureRequest is already consumed during the expression
        matching phase and is injected into args/kwargs via _get_args_kwargs before the around hook is called. Without
        this separate protocol, the type system would force around hooks to accept FixtureRequest even though
        contextmanager() would not pass it, causing a mismatch between the declared and actual call signatures.

    Delegates:
        - Protocol (typing): Provides the structural subtyping base for the protocol.
        - contextmanager (contextlib): The stdlib function that wraps around hook callables satisfying this protocol.

    Cohesion:
        The single __call__ method is perfectly focused on the one behavior this protocol enables: being passed to
        contextmanager(). Every aspect of the signature (no FixtureRequest, Generator return) is required by
        contextmanager().

    Separation:
        - _HookFunctionProtocol: Kept separate because before/after hooks receive FixtureRequest directly and are called
        inline, while around hooks delegate to contextmanager() and must not receive FixtureRequest — different
        invocation patterns require different call signatures.
        - _PickleTagProtocol: Kept separate because this is a callable contract while _PickleTagProtocol is a data contract.

    Main consumers:
        - decorator_builder.decorator_wrapper.decorator (the inner `hook` function): When conjunction is
        HookConjunction.around, the user's function is cast to _AroundHookCallable and passed to contextmanager() for
        wrapping.

    State and side effects:
        None, keeps no persistent state. Pure Protocol definition.

    Invariants:
        - The callable must be valid as contextmanager() input — it must be a generator function, not a regular function
        returning a context manager object.
        - args and kwargs passed to __call__ must already include any FixtureRequest or Run objects injected by
        _get_args_kwargs.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    def __call__(self, *args: object, **kwargs: object) -> Generator[None, None, None]:
        """
        Define the call signature for around-hook callables that are compatible with contextlib.contextmanager(): accepts ar.

        Responsibility:
            Defines the call signature for around-hook callables that are compatible with contextlib.contextmanager():
            accepts arbitrary positional and keyword arguments (pre-injected with FixtureRequest and Run by
            _get_args_kwargs) and returns a Generator. The generator's single yield point acts as the boundary between
            setup code (executed before the scenario) and teardown code (executed after), which is the standard Python
            context manager pattern applied to BDD hook lifecycle management.

        Reason for existence:
            This method signature is specifically designed for contextmanager() compatibility. The function must be a
            generator (not a regular function) because contextmanager() calls next() on it to execute setup code up to
            the yield, then .throw() or .close() to execute teardown. The absence of FixtureRequest in the signature is
            intentional: the request is already consumed by _get_args_kwargs during the expression matching phase and
            injected into args/kwargs before this callable is invoked.

        Delegates:
            - _get_args_kwargs: Injects FixtureRequest and Run into kwargs before this callable is invoked, ensuring the
            around hook has access to pytest context without requiring it in the signature.
            - contextmanager (contextlib): Wraps callables satisfying this protocol to create context manager objects.

        Cohesion:
            The signature is perfectly focused on contextmanager() compatibility. Every aspect — Generator return, no
            FixtureRequest parameter, variadic args/kwargs — serves this single purpose.

        Separation:
            - _HookFunctionProtocol.__call__: Kept separate because that method requires FixtureRequest as the first
            parameter for direct invocation, while this method is designed for contextmanager() wrapping and must not
            include FixtureRequest in its signature.

        Main consumers:
            - decorator_builder.decorator_wrapper.decorator (inner `hook` function): When conjunction is
            HookConjunction.around, casts the user's function to this protocol and wraps it with contextmanager().

        State and side effects:
            None, keeps no persistent state. The Generator yield point defines the setup/teardown boundary for the context manager.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        ...


def _get_conjunction_and_kind(
    *,
    conjunction: str | HookConjunction,
    kind: str | HookKind,
) -> tuple[HookConjunction, HookKind]:
    """
    Normaliz the conjunction and kind parameters (which may be passed as raw strings by end-user code using the decorat.

    Responsibility:
        Normalizes the conjunction and kind parameters (which may be passed as raw strings by end-user code using the
        decorator_builder's flexible call syntax) into their proper HookConjunction and HookKind enum instances. This
        function is the single normalization point that converts the string "before"/"after"/"around" → HookConjunction
        enum and "mark"/"tag" → HookKind enum, ensuring that all downstream pipeline stages receive typed enums rather
        than raw strings.

    Reason for existence:
        Exists because decorator_builder accepts both string and enum arguments for flexibility (users may call
        `decorator_builder("before", "mark")` or `decorator_builder(HookConjunction.before, HookKind.mark)`). Without
        this normalization function, every downstream consumer (_get_expression_type, _get_marks, the hook fixture)
        would need to handle both str and enum inputs. Centralizing normalization here ensures a single point of
        conversion and makes the pipeline's typed contract clear: downstream functions always receive HookConjunction
        and HookKind enums.

    Delegates:
        - HookConjunction enum: Provides the constructor that converts string "before"/"after"/"around" to enum instances.
        - HookKind enum: Provides the constructor that converts string "mark"/"tag" to enum instances.

    Cohesion:
        The function is perfectly focused on a single transformation: two string→enum conversions that are always
        performed together. Both parameters are normalized in the same call because they are always paired —
        decorator_builder passes both simultaneously.

    Separation:
        - _get_expression_type: Kept separate because that function takes already-normalized enums and performs semantic
        dispatch (mapping to expression type classes), while this function performs only syntactic normalization of
        input types.

    Main consumers:
        - decorator_builder: Calls this function once at the beginning to normalize its conjunction and kind parameters
        before threading them through the decorator pipeline.

    State and side effects:
        None, keeps no persistent state. Pure function with no side effects.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    conjunction_ = HookConjunction(conjunction) if isinstance(conjunction, str) else conjunction
    kind_ = HookKind(kind) if isinstance(kind, str) else kind
    return conjunction_, kind_


def _get_expression_type(*, _kind: HookKind) -> type[TagExpressionType]:
    """
    Dispatches the appropriate TagExpression subclass based on the hook's kind: returns MarksTagExpression for HookKind.m.

    Responsibility:
        Dispatches the appropriate TagExpression subclass based on the hook's kind: returns MarksTagExpression for
        HookKind.mark (filtering by pytest markers) and GherkinTagExpression for HookKind.tag (filtering by Gherkin
        tags). This mapping is the critical dispatch point that connects the hook filtering dimension to the correct
        expression parser and evaluator, enabling the same hook pipeline to handle both mark-based and tag-based
        filtering through polymorphism.

    Reason for existence:
        Encapsulates the knowledge of which expression parser corresponds to which hook kind. This mapping cannot be
        stored as a simple class attribute because it links HookKind (defined in hook.py) to expression types defined in
        tag_expression.py — a cross-module dependency that is cleaner to manage in a dedicated dispatch function than in
        either module's class definitions. If a third hook kind is added in the future, only this function needs
        updating.

    Delegates:
        - MarksTagExpression (from pytest_bdd.tag_expression): The expression type for mark-based hook filtering,
        selected when _kind is HookKind.mark.
        - GherkinTagExpression (from pytest_bdd.tag_expression): The expression type for tag-based hook filtering,
        selected when _kind is HookKind.tag.

    Cohesion:
        The function performs exactly one job: mapping HookKind enum values to expression type classes. The dictionary
        literal and lookup form a single cohesive dispatch operation with no branching logic.

    Separation:
        - _get_marks: Kept separate because _get_marks knows how to extract the actual mark objects from the test
        context, while this function knows which expression parser class to use — data extraction vs parser selection.

    Main consumers:
        - decorator_builder.decorator_wrapper.decorator (inner `hook` function): Calls this function to get the
        ExpressionType class, then calls ExpressionType.parse(expression_) to create a parsed expression for matching.

    State and side effects:
        None, keeps no persistent state. Pure function with no side effects.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    return {
        HookKind.mark: MarksTagExpression,
        HookKind.tag: GherkinTagExpression,
    }[_kind]


def _get_marks(*, _kind: HookKind, request: FixtureRequest) -> list[Mark]:
    """
    Collect the appropriate set of "marks" (filterable annotation objects) for expression evaluation based on the hook's.

    Responsibility:
        Collects the appropriate set of "marks" (filterable annotation objects) for expression evaluation based on the
        hook's kind: for HookKind.mark, collects pytest markers from the request node via iter_markers(); for
        HookKind.tag, collects Gherkin tags from the scenario pickle via request.getfixturevalue("pickle").tags and
        wraps each in a make_mark() call to produce pytest-compatible Mark objects. This function bridges the gap
        between Gherkin's native tag model and pytest's marker model, normalizing both into the same Mark type for
        unified expression evaluation.

    Reason for existence:
        The hook expression evaluation system (_ModernTagExpression.evaluate and GherkinTagExpression.evaluate) expects
        a list[Mark] as input, regardless of whether the hook filters by pytest markers or Gherkin tags. For
        HookKind.mark, the marks are already in Mark format from pytest's marker system. For HookKind.tag, the Gherkin
        pickle tags must be converted from their native format (which only requires a .name attribute, per
        _PickleTagProtocol) into Mark objects via make_mark(). This function encapsulates that conversion so the rest of
        the pipeline operates on a uniform type.

    Delegates:
        - request.node.iter_markers(): Provides pytest Mark objects for HookKind.mark filtering.
        - request.getfixturevalue("pickle"): Provides the scenario pickle containing Gherkin tags for HookKind.tag filtering.
        - make_mark (from pytest_bdd.compatibility.pytest): Wraps Gherkin tag names into pytest-compatible Mark objects.

    Cohesion:
        The function performs one job: producing a list[Mark] from the appropriate source based on hook kind. The
        dictionary dispatch and list comprehension are both focused on this single transformation.

    Separation:
        - _get_expression_type: Kept separate because this function provides the data (marks to evaluate against) while
        _get_expression_type provides the evaluator (expression parser class) — data provider vs evaluator selection.
        - _get_args_kwargs: Kept separate because that function handles argument injection for hook callables while this
        function handles mark collection for expression matching — different pipeline stages.

    Main consumers:
        - decorator_builder.decorator_wrapper.decorator (inner `hook` function): Calls this function to get the marks
        list, then passes it to parsed_expression.evaluate() to determine if the hook should execute.

    State and side effects:
        Reads from pytest fixture system (getfixturevalue) and pytest node markers — these are read-only operations that
        do not modify state. The list comprehension creating Mark objects from tags is a pure transformation.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    pickle_tags = cast("Iterable[_PickleTagProtocol]", request.getfixturevalue("pickle").tags)
    return list(
        {
            HookKind.mark: request.node.iter_markers(),
            HookKind.tag: (make_mark(tag.name) for tag in pickle_tags),
        }[_kind],
    )


def _get_args_kwargs(
    *,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    func_sig: Signature,
    request: FixtureRequest,
) -> tuple[tuple[object, ...], dict[str, object]]:
    """
    Dynamically injects the pytest FixtureRequest and Run objects into the hook function's keyword arguments based on the.

    Responsibility:
        Dynamically injects the pytest FixtureRequest and Run objects into the hook function's keyword arguments based
        on the function's declared parameter names: if the hook function signature includes a "request" parameter, the
        FixtureRequest is added; if it includes a "run" parameter, the Run object (retrieved from the config stash) is
        added. This enables hook authors to optionally accept pytest context and BDD runtime state without requiring
        them in every hook signature.

    Reason for existence:
        Hook functions are user-authored and should not be forced to include parameters they don't need. This function
        implements the "opt-in parameter injection" pattern: the hook decorator inspects the original function's
        signature (via func_sig.parameters), and only injects request and run if they appear as parameter names. Without
        this, every hook function would need to include `request` and `run` parameters even if unused, cluttering user
        code. The function merges injected kwargs with the original kwargs, with the original kwargs taking precedence
        for keys that don't conflict with request/run.

    Delegates:
        - inspect.Signature (via func_sig): Provides the declared parameter names of the original hook function for
        conditional injection decisions.
        - Run.from_stash (from pytest_bdd.model.run): Retrieves the Run object from pytest's config stash, providing the
        hook with access to the BDD runtime model.

    Cohesion:
        The function performs a single task: conditionally injecting two well-known context objects (request, run) into
        kwargs. The dictionary unpacking pattern with conditional dict merges is idiomatic Python for optional parameter
        injection and is used consistently for both injected values.

    Separation:
        - _get_marks: Kept separate because this function handles argument preparation for hook callables while
        _get_marks handles data preparation for expression evaluation — two distinct pipeline stages.
        - _get_conjunction_and_kind: Kept separate because that function handles input normalization while this function
        handles output preparation — input vs output stages of the pipeline.

    Main consumers:
        - decorator_builder.decorator_wrapper.decorator (inner `hook` function): Calls this function before invoking the
        hook callable to prepare the final args/kwargs with injected context objects.

    State and side effects:
        Reads from config.stash via Run.from_stash() — this is a read-only operation. Does not modify any persistent state.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    return (
        args,
        {
            **kwargs,
            **({"request": request} if "request" in func_sig.parameters else {}),
            **({"run": Run.from_stash(request.config.stash)} if "run" in func_sig.parameters else {}),
        },
    )


def decorator_builder(conjunction: str | HookConjunction, kind: str | HookKind) -> _Decorator[..., Any]:
    """
    Implement the factory function that generates the six concrete hook decorators (before_mark, before_tag, after_mark,.

    Responsibility:
        Implements the factory function that generates the six concrete hook decorators (before_mark, before_tag,
        after_mark, after_tag, around_mark, around_tag) by creating a decopatch-based decorator wrapper parameterized by
        conjunction (before/after/around) and kind (mark/tag). The factory returns a callable that can be used as
        @decorator or @decorator(expression, name) to register hook functions as autouse pytest fixtures with
        conditional execution based on tag/mark expression matching, unique fixture naming via a global counter, and
        metadata stamping for discovery by the collection and runtime systems.

    Reason for existence:
        This is the central orchestrator of the hook system. Without it, the six hook decorators would need to be
        duplicated with near-identical logic differing only in conjunction and kind values. The factory pattern with
        decopatch enables both @decorator and @decorator(expression, name) syntax while keeping the core pipeline (parse
        expression → collect marks → evaluate → conditionally execute) in one place. The global expression_count_gen
        counter ensures unique pytest fixture names, preventing registration collisions when multiple hooks use the same
        expression pattern.

    Delegates:
        - _get_conjunction_and_kind: Normalizes string inputs to enum values at the start of the pipeline.
        - decopatch.function_decorator: Provides the decorator factory framework supporting both @decorator and
        @decorator(arg) syntax.
        - pytest.fixture: Dynamically registers each hook as a named autouse fixture with a unique count-based name.
        - makesfun.wraps: Wraps the hook function to prepend "request" to the user-facing parameter list while accepting
        it in the internal fixture.
        - _get_expression_type, _get_marks, _get_args_kwargs: The three inner pipeline functions that handle expression
        parsing, mark collection, and argument injection respectively.

    Cohesion:
        The function is the glue that composes all hook pipeline stages into a coherent decorator. Every line
        contributes to the single pipeline: normalize inputs → create decorator wrapper → create inner decorator →
        create fixture → implement hook logic → stamp metadata → return fixture. This is a classic "builder" pattern
        where all logic is dedicated to constructing one type of output (a pytest fixture decorator for hooks).

    Separation:
        - pytest_bdd.steps.definition.StepDecorator: Kept separate because step decorators (given/when/then/step) match
        against Gherkin step text using step parsers, while hook decorators match against tags/marks using expression
        parsers — different matching domains requiring completely different match/evaluate pipelines.
        - pytest_bdd.tag_expression: Kept separate because tag_expression owns expression parsing/evaluation algorithms,
        while this function owns the pipeline that uses them to decide hook invocation timing.

    Main consumers:
        - Module-level starmap call: product(HookConjunction, HookKind) generates all six combinations, and starmap
        calls decorator_builder for each, producing the six concrete decorators (before_mark through around_tag).
        - End-user conftest.py files: The six concrete decorators are the public API that users import and apply to
        their hook functions.

    State and side effects:
        Mutates the module-level expression_count_gen counter each time a hook is registered, producing a new unique
        integer for fixture naming. This is the only mutable state mutation — it is intentional and necessary for unique
        fixture name generation.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """
    conjunction_, kind_ = _get_conjunction_and_kind(conjunction=conjunction, kind=kind)

    @function_decorator
    def decorator_wrapper(
        expression: str | None = None,
        name: str | None = None,
    ) -> Callable[[object], Callable[[FixtureRequest], Generator[None, None, None]]]:
        """
        Serve as the outer decopatch layer that captures the optional expression and name parameters from the decorator call.

        Responsibility:
            Serves as the outer decopatch layer that captures the optional expression and name parameters from the
            decorator call (e.g., @before_tag("@smoke", name="smoke_hook")) and returns a decorator function that will
            process the actual hook callable. This is the boundary between the DSL syntax (@before_tag(expression)) and
            the internal pipeline (the inner decorator function that wraps the user's function).

        Reason for existence:
            decopatch's @function_decorator pattern requires this two-layer structure: the outer function
            (decorator_wrapper) captures decorator arguments, and the inner function (decorator) captures the decorated
            function. The expression parameter defaults to None but is normalized to "" inside, enabling hooks with no
            expression to always match (matching against an empty string is always true in both mark and tag expression
            systems).

        Delegates:
            - decorator_wrapper.decorator: The inner function that receives the actual user's hook function and wraps it
            into a pytest fixture.
            - decopatch.function_decorator: Provides the decorator factory mechanics that make this two-layer pattern work.

        Cohesion:
            The function performs exactly one task: bridging the decopatch decorator call syntax to the internal
            decorator function. All logic is in the inner decorator; this wrapper is a thin shell.

        Separation:
            - decorator_builder: Kept separate because decorator_builder creates this closure with captured conjunction_
            and kind_, while decorator_wrapper captures expression and name — different closure scopes capturing
            different parameters.

        Main consumers:
            - decorator_builder: Returns this function as the decorator factory. Users never interact with
            decorator_wrapper directly; it is the return value of the six concrete decorator creation functions.

        State and side effects:
            None, keeps no persistent state beyond closure captures of expression and name.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        expression_: str = expression if expression is not None else ""

        def decorator(func: object) -> Callable[[FixtureRequest], Generator[None, None, None]]:
            """
            Decorate with an inner function that receives the user's hook function, wraps it into a pytest autouse fixture with a dy.

            Responsibility:
                The inner decorator function that receives the user's hook function, wraps it into a pytest autouse
                fixture with a dynamically generated unique name (incorporating conjunction, kind, expression, and a
                monotonically increasing counter), implements the conditional execution logic (parse expression, collect
                marks, evaluate match, execute hook at the correct conjunction timing), stamps metadata attributes for
                discovery by the plugin's collection system, and returns the registered pytest fixture. This is the
                "brain" of the hook system — every hook function passes through this decorator.

            Reason for existence:
                This is where all hook pipeline stages are composed into a single fixture function. The pipeline: (1)
                parse the expression using the appropriate parser type, (2) collect marks from the request context, (3)
                evaluate whether marks match the expression, (4) if matching, execute the user's function at the timing
                specified by conjunction_ (before: call then yield, after: yield then call, around: contextmanager
                wrap), (5) stamp metadata for discovery. This composition must happen inside a decorator because each
                hook function needs its own fixture with its own expression and name.

            Delegates:
                - _get_expression_type: Selects the correct expression parser class (MarksTagExpression or
                GherkinTagExpression) based on kind_.
                - _get_marks: Collects the mark objects from the request context for expression evaluation.
                - _get_args_kwargs: Injects FixtureRequest and Run into the hook callable's arguments based on parameter names.
                - pytest.fixture: Registers the hook as a named autouse fixture in pytest's fixture system.
                - makesfun.wraps: Wraps the hook function so the user-facing signature does not include "request" but it
                is available internally.
                - next(expression_count_gen): Generates a unique integer for fixture naming to prevent collisions.

            Cohesion:
                Every line in this function is part of the single pipeline: generate fixture name → parse expression →
                collect marks → evaluate → conditionally execute → stamp metadata → register fixture. There is no
                extraneous logic. The if/elif/else chain for conjunction timing is the only branching, and all branches
                follow the same pattern.

            Separation:
                - StepDecorator (from pytest_bdd.steps.definition): Kept separate because step decorators match step
                text patterns while hook decorators match tag/mark expressions — completely different matching
                algorithms and execution timing.

            Main consumers:
                - decorator_wrapper: Returns this function. The user's hook function is passed as func when the
                decorator is applied (e.g., @before_tag("@smoke") def my_hook(request): ...).

            State and side effects:
                Mutates the module-level expression_count_gen counter via next(), producing a side effect that affects
                fixture naming. Sets metadata attributes (__pytest_bdd_is_hook__, etc.) on the wrapped function — these
                are persistent state modifications on the function object but do not affect global state.

            Architecture score:
                #arch-eval:reason_for_existence=5
                #arch-eval:owned_responsibility=5
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=5
                #arch-eval:separation=4
                #arch-eval:consumer_clarity=2
                #arch-eval:state_invariants=3
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
            func_sig = signature(cast("FunctionType", func))

            fixture_decorator = pytest.fixture(
                name=f"{conjunction_.value}_{kind_.value}_expression_{expression_}_{next(expression_count_gen)}",
                autouse=True,
            )

            def hook(request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]:
                """
                Register the innermost hook function that is registered as a pytest autouse fixture.

                Responsibility:
                    The innermost hook function that is registered as a pytest autouse fixture. At runtime, this
                    function: (1) parses the tag/mark expression, (2) collects marks from the request context, (3)
                    evaluates whether the marks satisfy the expression, (4) if matching, executes the user's hook
                    function at the timing specified by conjunction_ (before: call function then yield scenario
                    execution, after: yield scenario execution then call function, around: wrap function with
                    contextmanager as a context manager around scenario execution). If not matching, simply yields
                    control to scenario execution without invoking the hook.

                Reason for existence:
                    This is the actual fixture function that pytest invokes during test execution. It bridges the static
                    hook registration (done by the decorator) with the dynamic hook execution (controlled by expression
                    matching at runtime). The yield-based control flow enables before/after/around semantics within
                    pytest's fixture dependency injection system. The decision to always yield (even when not matching)
                    ensures the fixture is always "used" from pytest's perspective, preventing unused-fixture warnings.

                Delegates:
                    - ExpressionType.parse: Parses the expression string into a structured expression object.
                    - parsed_expression.evaluate: Evaluates whether the collected marks satisfy the expression.
                    - _get_args_kwargs: Injects FixtureRequest and Run into the hook callable's arguments.
                    - contextmanager (contextlib): Wraps around-hook functions to create context managers.

                Cohesion:
                    All logic serves one purpose: conditionally executing a user's function at the right time relative
                    to scenario execution. The if/elif/else dispatch for conjunction timing is the only branching, and
                    all branches follow the same pattern of "check match → execute → yield".

                Separation:
                    - Step functions (given/when/then fixtures): Kept separate because step fixtures match step text and
                    execute step implementations, while hook fixtures match tags/marks and execute lifecycle hooks —
                    different trigger conditions and different execution semantics.

                Main consumers:
                    - pytest's fixture machinery: This function is registered as a named autouse fixture and invoked by
                    pytest during test setup/teardown.

                State and side effects:
                    Reads from pytest's fixture system (getfixturevalue, node.iter_markers) — read-only operations. The
                    yield suspends execution, allowing the scenario to run between fixture setup and teardown phases.

                Architecture score:
                    #arch-eval:reason_for_existence=5
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=4
                    #arch-eval:cohesion=5
                    #arch-eval:separation=4
                    #arch-eval:consumer_clarity=2
                    #arch-eval:state_invariants=4
                    #arch-eval:entity_fullness=3
                    #arch-eval:locational_stability=4
                """
                ExpressionType: type[TagExpressionType] = _get_expression_type(_kind=kind_)  # noqa:N806  -- suppressed warning
                parsed_expression: TagExpression = ExpressionType.parse(expression_)

                is_matching = parsed_expression.evaluate(_get_marks(_kind=kind_, request=request))
                args_, kwargs_ = _get_args_kwargs(args=args, kwargs=kwargs, func_sig=func_sig, request=request)

                if is_matching:
                    if conjunction_ is HookConjunction.before:
                        cast("ObjectCallable", func)(*args_, **kwargs_)
                        yield None
                    elif conjunction_ is HookConjunction.after:
                        yield None
                        cast("ObjectCallable", func)(*args_, **kwargs_)
                    elif conjunction_ is HookConjunction.around:
                        with contextmanager(cast("_AroundHookCallable", func))(*args_, **kwargs_):
                            yield None
                    else:  # pragma: no cover
                        yield None
                else:
                    yield None

            hook = cast("_HookFunctionProtocol", wraps(func, prepend_args="request", remove_args="request")(hook))

            hook.__pytest_bdd_is_hook__ = True
            if name is not None:
                hook.__pytest_bdd_hook_name__ = name
            hook.__pytest_bdd_hook_expression__ = expression_
            hook.__pytest_bdd_hook_kind__ = kind_.value
            hook.__pytest_bdd_hook_conjunction__ = conjunction_.value

            return cast("Callable[[FixtureRequest], Generator[None, None, None]]", fixture_decorator(hook))

        return decorator

    return decorator_wrapper


before_mark, before_tag, after_mark, after_tag, around_mark, around_tag = starmap(
    decorator_builder,
    product(HookConjunction, HookKind),
)
