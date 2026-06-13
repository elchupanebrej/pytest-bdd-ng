"""
Implements the Matcher class — the step-to-definition matching engine that resolves which registered Definition shoul.

Responsibility:
    Implements the Matcher class — the step-to-definition matching engine that resolves which registered Definition
    should execute for a given PickleStep at runtime. The __call__ method accepts a FixtureRequest, Feature, Pickle,
    Step, previous Step, and Registry, then applies three matching strategies in priority order: strict_matcher (exact
    type match between step and definition), unspecified_matcher (allows PickleStepType.unknown on either side), and
    liberal_matcher (cross-type matching governed by per-definition and global liberal mode configuration). Uses
    find_step_definition_matches to iterate the registry (with parent fallback) and _parser_specificity to sort matches
    by pattern type priority. Raises MatchNotFoundError when no definition matches.

Reason for existence:
    This module is the information expert for step matching because it owns the complete matching algorithm: the three-
    strategy priority system, the liberal mode configuration resolution (from definition-level flag, CLI option, or INI
    option), the registry traversal with parent chaining, and the parser specificity scoring that breaks ties when
    multiple definitions match the same step. It is kept separate from registry.py (which owns storage and discovery)
    and definition.py (which owns the data model) because matching is a distinct algorithmic concern that depends on
    both but should not be coupled to their internal implementations. The Matcher class is instantiated per test,
    holding ephemeral state (request, feature, pickle, step, step_type_context) for the duration of a single step
    resolution.

Delegates:
    - find_step_definition_matches (static): Iterates matchers in priority order, applying each to every definition in
    the registry, sorting matches by _parser_specificity, yielding matches until one matcher produces results. Falls
    back to registry.parent when no matches found.
    - strict_matcher: Requires exact match between step_definition.type_ and the current step_type_context.
    - unspecified_matcher: Matches if either the step or definition type is PickleStepType.unknown.
    - liberal_matcher: Matches across different step types when liberal mode is enabled (resolved from
    definition.liberal, config.option.liberal_steps, or config.getini), but only if unspecified_matcher did not already
    match.
    - _parser_specificity: Scores definitions to prefer more specific parser types
    (string/parse/cfparse/cucumber_expression = 2, regex = 1, other = 0).

Cohesion:
    Every entity in this module serves the step matching algorithm. The Matcher class owns the matching lifecycle; its
    three matcher methods implement the matching strategies; MatchNotFoundError is the failure mode;
    find_step_definition_matches runs the registry iteration; _parser_specificity is the tiebreaker. All operate on the
    same data types (Definition, Registry, PickleStep).

Separation:
    - registry.py (Registry): Stores and discovers definitions; Matcher reads from Registry but does not own storage or
    discovery.
    - definition.py (Definition): The data objects being matched; Matcher reads Definition fields but does not own the
    data model.
    - manager.py (StepDefinitionManager): Registers definitions; Matcher matches them at runtime.

Main consumers:
    - pytest_bdd.plugin.pickle_runner: Creates a Matcher instance, calls it as a callable (matcher(request, feature,
    pickle, step, previous_step, registry)) to find the matching Definition for each step during scenario execution.

State and side effects:
    Instance-level mutable state: self.request, self.feature, self.pickle, self.step, self.previous_step,
    self.step_registry (set by __call__), self.step_type_context (set by __call__ and carried across calls for
    PickleStepType.unknown steps). No file/network I/O. Reads config via config.option.liberal_steps and
    config.getini(LIBERAL_OPTION).

Invariants:
    - The three matchers are tried in fixed order: strict, unspecified, liberal. This order must not change as it
    defines matching priority.
    - step_type_context persists across __call__ invocations when the current step type is PickleStepType.unknown,
    enabling context-dependent matching for steps without explicit type.
    - find_step_definition_matches must not yield matches from a parent registry if matches were found in the current
    registry.
    - MatchNotFoundError is raised only when no definition matches across all matchers and all registry levels.

Failure semantics:
    - Matcher.MatchNotFoundError (RuntimeError): Raised by __call__ when no Definition in the registry (or any parent
    registry) matches the current step. The error message includes the step text. Callers in pickle_runner should catch
    this to mark the step as undefined and generate snippets.

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

from collections.abc import (  # noqa: TC003  -- needed at runtime for isinstance checks and attrs field type validation
    Callable,
    Iterator,
    Sequence,
)
from contextlib import suppress
from typing import TYPE_CHECKING
from warnings import warn

from attrs import field
from cucumber_messages import Feature, Pickle, PickleStepType

from pytest_bdd.compatibility.pytest import Config, FixtureRequest  # noqa: TC001  -- used in runtime type annotations
from pytest_bdd.const import Steps
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition
    from pytest_bdd.steps.registry import Registry

# Import Step as alias for PickleStep
from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)


class Matcher:
    """
    Callable step-to-definition matching engine.

    Responsibility:
        Callable step-to-definition matching engine. Instantiated once per test with a pytest Config, the Matcher is
        invoked as a function (via __call__) for each PickleStep during scenario execution. It stores the current
        FixtureRequest, Feature, Pickle, Step, previous Step, and Registry as instance state, resolves the
        step_type_context (carrying forward PickleStepType.unknown across calls), then applies three matching strategies
        in fixed priority order via find_step_definition_matches: strict (exact type match), unspecified (allows unknown
        type on either side), and liberal (cross-type matching when enabled). Returns the single best Definition,
        emitting a warning if multiple matches are found. Raises MatchNotFoundError if no definition matches.

    Reason for existence:
        This class encapsulates the complete step-matching state machine. It exists as a class rather than a function
        because the matching process spans multiple calls within a scenario (each step is matched individually) and
        needs to carry forward the step_type_context for PickleStepType.unknown steps (where the type is inferred from
        the surrounding context). The three matcher methods are instance methods so they can access self.request and
        self.step without explicit parameter passing. The class is separate from Registry and Definition because
        matching is an algorithmic orchestration concern that operates on those data types without owning them.

    Delegates:
        - find_step_definition_matches (static): Iterates matchers in priority order over registry definitions, applying
        each matcher predicate, sorting by _parser_specificity, yielding matches. Falls back to registry.parent
        recursively.
        - strict_matcher: Returns True iff definition.type_ == step_type_context and
        definition.parser.is_matching(request, step.text).
        - unspecified_matcher: Returns True iff PickleStepType.unknown is in {step_type_context, definition.type_} and
        parser matches.
        - liberal_matcher: Returns True when liberal mode is active, types differ, unspecified_matcher does not match,
        and parser matches. Liberal mode is resolved from definition.liberal (per-definition),
        config.option.liberal_steps (CLI), or config.getini (INI).
        - warnings.warn: Emits PytestBDDStepDefinitionWarning when multiple definitions match the same step.

    Cohesion:
        Every method and attribute directly serves the step matching lifecycle. The three matcher methods are the
        matching predicates; find_step_definition_matches orchestrates the registry search; __call__ is the public entry
        point; MatchNotFoundError is the failure mode.

    Separation:
        - Registry: Provides the definitions to match against; Matcher does not own definition storage or discovery.
        - Definition: The data objects being matched; Matcher reads type_, parser, liberal fields but does not own the
        data model.
        - pickle_runner: The runtime layer that invokes Matcher for each step; Matcher does not own execution flow.

    Main consumers:
        - pytest_bdd.plugin.pickle_runner: Instantiates Matcher(config), then calls matcher(request, feature, pickle,
        step, previous_step, registry) for each step in the scenario.

    State and side effects:
        Instance-level mutable state: self.config (set at __init__), self.request, self.feature, self.pickle, self.step,
        self.previous_step, self.step_registry (set per __call__ invocation), self.step_type_context (carried across
        __call__ invocations for PickleStepType.unknown). Reads config via config.option and config.getini. Emits
        warnings via warnings.warn.

    Invariants:
        - Strict matcher is always tried first, then unspecified, then liberal. This priority order is critical for
        correct matching and must not change.
        - step_type_context is only carried forward when the current step type is PickleStepType.unknown and a previous
        context exists.
        - find_step_definition_matches must only fall back to parent registry when no matches are found in the current
        registry (enforced by the found_matches guard).
        - When multiple definitions match, the first one in priority order (after sorting by _parser_specificity) is returned.

    Failure semantics:
        - Matcher.MatchNotFoundError (RuntimeError): Raised by __call__ when no definition matches across all three
        matchers and all registry levels. The step text is included in the default RuntimeError message (no custom
        __init__). Callers should catch this to handle undefined steps (e.g., generate snippets, mark step as
        undefined).

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

    class MatchNotFoundError(RuntimeError):
        """
        Signals that no registered step definition matched the current PickleStep.

        Responsibility:
            Signals that no registered step definition matched the current PickleStep. Extends RuntimeError with no
            custom __init__, so the default RuntimeError behaviour applies: the step text provided as the constructor
            argument becomes the error message. This is raised by Matcher.__call__ after all three matching strategies
            and all registry levels (including parents) have been exhausted.

        Reason for existence:
            Exists as a nested class within Matcher because it is semantically part of the matching lifecycle — it is
            the failure mode of the matching process. Nesting it within Matcher makes the association explicit and
            avoids polluting the module-level namespace. Using RuntimeError as the base class means it is not caught by
            generic Exception handlers that should not suppress step matching failures, while still being catchable
            specifically.

        Delegates:
            - No delegation: inherits directly from RuntimeError with no custom behaviour.

        Cohesion:
            Tightly coupled to Matcher as its failure mode. Defined within Matcher to reinforce this coupling.

        Separation:
            - Matcher.__call__: The sole raise site; this class is the exception type raised.
            - pickle_runner: The primary catcher that handles undefined steps.

        Main consumers:
            - pytest_bdd.plugin.pickle_runner: Catches MatchNotFoundError to mark steps as undefined and generate step snippets.
            - Any code that programmatically calls Matcher and wants to handle unmatched steps.

        State and side effects:
            None beyond standard exception state (message string from RuntimeError).

        Invariants:
            - The constructor argument should be the step text that failed to match, for diagnostic purposes.
            - Must always be raised with a descriptive message, not as an empty exception.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """

    def __init__(self, config: Config) -> None:
        """
        Construct a Matcher instance bound to a specific pytest Config.

        Responsibility:
            Constructs a Matcher instance bound to a specific pytest Config. Stores the config and declares instance
            attributes (request, feature, pickle, step, previous_step, step_registry) with field(init=False)
            placeholders for mypy type narrowing — these are set later by __call__ rather than at construction time.
            Initialises step_type_context to None, which will be set on the first __call__ invocation.

        Reason for existence:
            Separates construction (binding to config, which is stable for the test session) from invocation (binding to
            the specific step being matched, which changes per __call__). The field(init=False) annotations are a mypy
            workaround: attrs does not process these fields (the class is not @define-decorated), but the annotations
            provide type information for static analysis.

        Delegates:
            - field(init=False): Used as a type-narrowing annotation convention for mypy, not for actual attrs behaviour.

        Cohesion:
            Pure initialisation: stores config, declares instance attributes with type annotations for documentation and
            static analysis.

        Separation:
            - __call__: Sets the request/feature/pickle/step/previous_step/step_registry attributes and performs
            matching; __init__ only prepares the instance.

        Main consumers:
            - pytest_bdd.plugin.pickle_runner: Creates Matcher(config) once per test, then calls it repeatedly for each step.

        State and side effects:
            Sets self.config. Declares but does not initialise self.request, self.feature, self.pickle, self.step,
            self.previous_step, self.step_registry (these getattr calls before __call__ would raise AttributeError,
            which is by design — the Matcher must be called with step context before use). Sets self.step_type_context =
            None.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        self.config: Config = config
        self.request: FixtureRequest = field(init=False)  # type narrowing workaround for mypy
        self.feature: Feature = field(init=False)  # type narrowing workaround for mypy
        self.pickle: Pickle = field(init=False)  # type narrowing workaround for mypy
        self.step: Step = field(init=False)  # type narrowing workaround for mypy
        self.previous_step: Step | None = field(init=False)  # type narrowing workaround for mypy
        self.step_registry: Registry = field(init=False)  # type narrowing workaround for mypy
        self.step_type_context: PickleStepType | None = None

    def __call__(  # noqa: PLR0913, PLR0917  -- complex call protocol inherited from step executor interface
        self,
        request: FixtureRequest,
        feature: Feature,
        pickle: Pickle,
        step: Step,
        previous_step: Step | None,
        step_registry: Registry,
    ) -> Definition:
        """
        Serve as the main entry point for step matching.

        Responsibility:
            The main entry point for step matching. Stores all contextual parameters as instance state, resolves the
            step_type_context (carrying forward from previous calls when the current step type is PickleStepType.unknown
            and a context already exists), then delegates to find_step_definition_matches with the three matching
            strategies (strict, unspecified, liberal). If exactly one definition matches, returns it; if multiple match,
            emits a PytestBDDStepDefinitionWarning and returns the first (highest priority after specificity sorting);
            if none match, raises MatchNotFoundError with the step text.

        Reason for existence:
            This is the method that ties together all the matching state and strategies into a single callable
            interface. It exists as __call__ so that Matcher instances can be used as functions, providing a clean API
            for the pickle_runner. The step_type_context resolution logic (carrying forward unknown types) is placed
            here because it depends on both the previous call's context and the current step, bridging the per-step
            matching with cross-step state.

        Delegates:
            - find_step_definition_matches: Performs the actual registry iteration with matcher predicates.
            - strict_matcher, unspecified_matcher, liberal_matcher: The three matching predicates passed to
            find_step_definition_matches.
            - warnings.warn: Emitted when multiple definitions match (len(step_definitions) > 1).

        Cohesion:
            Orchestrates the entire matching flow for a single step: state setup, context resolution, match execution,
            ambiguity detection, and result/error return.

        Separation:
            - find_step_definition_matches: Handles the registry-level iteration; __call__ handles the step-level
            orchestration and context management.
            - Individual matcher methods: Each handles one matching strategy; __call__ sequences them.

        Main consumers:
            - pytest_bdd.plugin.pickle_runner: The sole external caller; invokes matcher(request, feature, pickle, step,
            previous_step, registry) for each pickle step.

        State and side effects:
            Mutates instance attributes: self.request, self.feature, self.pickle, self.step, self.previous_step,
            self.step_registry, self.step_type_context. Emits warnings. No file/network I/O.

        Failure semantics:
            - Matcher.MatchNotFoundError: Raised when no definition matches after exhausting all matchers and registry
            levels. The step text is the error message. Callers must handle this to avoid test crashes for undefined
            steps.

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
        self.request = request
        self.feature = feature
        self.pickle = pickle
        self.step = step
        self.previous_step = previous_step
        self.step_registry = step_registry

        self.step_type_context = (
            self.step_type_context
            if self.step.type is PickleStepType.unknown and self.step_type_context is not None
            else self.step.type
        )

        step_definitions = list(
            self.find_step_definition_matches(
                self.step_registry,
                (
                    self.strict_matcher,
                    self.unspecified_matcher,
                    self.liberal_matcher,
                ),
            ),
        )

        if len(step_definitions) > 0:
            if len(step_definitions) > 1:
                warn(
                    PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {step_definitions}"),
                    stacklevel=2,
                )
            return step_definitions[0]
        raise self.MatchNotFoundError(self.step.text)

    def strict_matcher(self, step_definition: Definition) -> bool:
        """
        Implement the highest-priority matching strategy.

        Responsibility:
            The highest-priority matching strategy. Returns True only when the step_definition's type_ exactly matches
            the current step_type_context AND the definition's parser matches the step text (parser.is_matching). This
            ensures that @given-decorated definitions only match Given steps, @when only matches When steps, etc. The
            parser matching check ensures the pattern text also corresponds.

        Reason for existence:
            This is the primary, most specific matching strategy. It exists as a separate method (rather than being
            inline in __call__) to be passed as a predicate to find_step_definition_matches, enabling the matcher
            priority system. The exact type match is the default and expected behaviour for well-formed BDD test suites
            where each step type has its own dedicated definitions.

        Delegates:
            - step_definition.parser.is_matching(self.request, self.step.text): The actual pattern matching delegated to the parser.

        Cohesion:
            One of three matching strategy methods. Reads self.step_type_context (set by __call__) and
            self.request/self.step (also set by __call__).

        Separation:
            - unspecified_matcher: Allows PickleStepType.unknown; this method requires exact type match.
            - liberal_matcher: Allows cross-type matching; this method forbids it.

        Main consumers:
            - Matcher.__call__: Passes this as the first element in the matchers tuple to find_step_definition_matches.

        State and side effects:
            None, pure predicate. Reads instance state (self.step_type_context, self.request, self.step) but does not mutate.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return step_definition.type_ == self.step_type_context and step_definition.parser.is_matching(
            self.request,
            self.step.text,
        )

    def unspecified_matcher(self, step_definition: Definition) -> bool:
        """
        Implement the second-priority matching strategy.

        Responsibility:
            The second-priority matching strategy. Returns True when either the current step_type_context or the
            step_definition's type_ (or both) is PickleStepType.unknown AND the parser matches the step text. This
            handles the case where Gherkin steps lack explicit type information (e.g., steps parsed from formats that
            don't distinguish Given/When/Then) or where definitions are registered without a specific type (@step
            decorator).

        Reason for existence:
            This strategy bridges the gap between explicitly typed and untyped steps/definitions. It is tried after
            strict_matcher to catch steps that could not be matched exactly but where the type ambiguity is intentional.
            The PickleStepType.unknown sentinel on either side signals "this entity does not constrain the match by
            type."

        Delegates:
            - step_definition.parser.is_matching(self.request, self.step.text): Pattern matching delegated to the parser.

        Cohesion:
            Second of three matching strategies. Works alongside strict_matcher and liberal_matcher in the priority chain.

        Separation:
            - strict_matcher: Requires exact type match; this method allows unknown on either side.
            - liberal_matcher: Allows cross-type matching even when types are known and different; this method requires
            unknown on at least one side.

        Main consumers:
            - Matcher.__call__: Passes this as the second element in the matchers tuple to find_step_definition_matches.

        State and side effects:
            None, pure predicate. Reads instance state but does not mutate.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return (
            PickleStepType.unknown in {self.step_type_context, step_definition.type_}
        ) and step_definition.parser.is_matching(
            self.request,
            self.step.text,
        )

    def liberal_matcher(self, step_definition: Definition) -> bool:
        """
        Implement the third-priority (most permissive) matching strategy.

        Responsibility:
            The third-priority (most permissive) matching strategy. Returns True when all of the following hold: liberal
            mode is enabled for this definition, the definition's type differs from the step type (ruling out exact and
            unknown matches which are handled by earlier matchers), the parser matches the step text, and the
            unspecified_matcher did NOT already match (preventing double-matching). Liberal mode is resolved from a
            three-tier configuration: per-definition flag (definition.liberal), CLI option
            (config.option.liberal_steps), or INI option (config.getini).

        Reason for existence:
            This strategy enables cross-type step matching (e.g., a When step matching a Then definition) when
            explicitly enabled. It exists as a separate strategy because it is the most permissive and potentially
            dangerous — matching a When step to a Then definition may indicate a test design issue. The three-tier
            configuration (definition, CLI, INI) provides granular control. The `not
            self.unspecified_matcher(step_definition)` check prevents this strategy from matching steps that the
            unspecified_matcher already covers.

        Delegates:
            - self.unspecified_matcher(step_definition): Called to check if this definition would already match via the
            unspecified strategy.
            - step_definition.parser.is_matching(self.request, self.step.text): Pattern matching delegated to the parser.
            - self.config.option.liberal_steps: CLI option for global liberal mode.
            - self.config.getini(str(Steps.Ini.LIBERAL_OPTION)): INI option for global liberal mode.

        Cohesion:
            Third of three matching strategies. The most complex due to the three-tier configuration resolution.

        Separation:
            - strict_matcher: Blocks cross-type matching; this method enables it when configured.
            - unspecified_matcher: Handles unknown-type matching; this method handles known-but-different-type matching.

        Main consumers:
            - Matcher.__call__: Passes this as the third element in the matchers tuple to find_step_definition_matches.

        State and side effects:
            None, pure predicate. Reads instance state (self.config, self.request, self.step, self.step_type_context)
            but does not mutate. Reads config options (no mutation).

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
        if step_definition.liberal is None:
            if self.config.option.liberal_steps is None:
                is_step_definition_liberal = self.config.getini(str(Steps.Ini.LIBERAL_OPTION))
            else:
                is_step_definition_liberal = getattr(self.config.option, str(Steps.Cli.LIBERAL_OPTION), False)
        else:
            is_step_definition_liberal = step_definition.liberal

        return all(
            (
                not self.unspecified_matcher(step_definition),
                is_step_definition_liberal,
                step_definition.type_ != self.step_type_context,
                step_definition.parser.is_matching(self.request, self.step.text),
            ),
        )

    @staticmethod
    def find_step_definition_matches(
        registry: Registry | None,
        matchers: Sequence[Callable[[Definition], bool]],
    ) -> Iterator[Definition]:
        """
        Iterate over matcher predicates in priority order, applying each to every Definition in the given registry.

        Responsibility:
            Iterates over matcher predicates in priority order, applying each to every Definition in the given registry.
            For each matcher, collects all matching definitions, sorts them by _parser_specificity (descending, so more
            specific parsers like string/parse rank higher than regex), and yields them. If a matcher produces at least
            one match (found_matches guard), subsequent matchers are skipped. If no matcher produces a match and the
            registry has a parent, recursively searches the parent registry. Yields definitions lazily via generator.

        Reason for existence:
            This is the core search algorithm of the matching engine. It is a static method because it operates on the
            registry and matchers without needing Matcher instance state. The found_matches guard implements the
            priority system: once a stricter matcher finds matches, more permissive matchers are not tried. The parent
            recursion enables hierarchical registries (e.g., conftest.py registries as parents of test module
            registries). The _parser_specificity sort ensures deterministic selection when multiple definitions match
            under the same strategy.

        Delegates:
            - matcher(step_definition): Each matcher predicate is called for each definition; matchers are provided by
            the caller (strict, unspecified, liberal).
            - _parser_specificity(step_definition): Scores each matching definition for priority sorting.
            - Matcher.find_step_definition_matches(registry.parent, matchers): Recursive call to search parent registry.
            - suppress(AttributeError): Silently handles the case where registry.parent does not exist.

        Cohesion:
            This method is purely about searching a registry with matcher predicates. It has no knowledge of what the
            matchers do, only that they are boolean predicates over Definitions.

        Separation:
            - Matcher.__call__: Provides the matchers tuple and the initial registry; this method performs the search.
            - Individual matcher methods: The predicates applied; this method orchestrates their application.

        Main consumers:
            - Matcher.__call__: The sole caller; passes self.step_registry and (strict_matcher, unspecified_matcher,
            liberal_matcher).

        State and side effects:
            None, pure function. No mutation, no I/O. The registry iteration is read-only.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        if registry:
            found_matches = False
            for matcher in matchers:
                matching_definitions = [step_definition for step_definition in registry if matcher(step_definition)]
                matching_definitions.sort(key=_parser_specificity, reverse=True)
                for step_definition in matching_definitions:
                    found_matches = True
                    yield step_definition
                if found_matches:
                    break
            if not found_matches:
                with suppress(AttributeError):
                    yield from Matcher.find_step_definition_matches(registry.parent, matchers)


def _parser_specificity(step_definition: Definition) -> int:
    """
    Assign a specificity score to a step definition based on its parser's pattern type, used as a sort key when multiple definitions match the same step.

    Responsibility:
        Assigns a specificity score to a step definition based on its parser's pattern type, used as a sort key when
        multiple definitions match the same step. Returns 2 for high-specificity parsers (string, parse, cfparse,
        cucumber_expression), 1 for medium-specificity parsers (regular_expression variants), and 0 for everything else.
        Higher scores are sorted first (reverse=True in the caller), so string/exact matches take precedence over regex
        matches, which take precedence over catch-all parsers like heuristic.

    Reason for existence:
        This is the tie-breaking mechanism when multiple definitions match the same step under the same matching
        strategy. Without it, match order would depend on Registry iteration order (which is non-deterministic for
        OrderedSet from namespace dir()). The scoring reflects the principle that more constrained pattern types (exact
        string) are more "specific" and should be preferred over less constrained types (regex, heuristic). Extracted as
        a standalone function for testability and to keep the sorting logic out of find_step_definition_matches.

    Delegates:
        - step_definition.parser.type: The StepDefinitionPatternType (or string) used for scoring.

    Cohesion:
        Single-purpose scoring function. Operates only on a Definition's parser type.

    Separation:
        - find_step_definition_matches: Uses this as the sort key; the scoring logic is independent of the search algorithm.
        - StepDefinitionPatternType: The enum whose members determine scores; this function knows the mapping from types
        to scores.

    Main consumers:
        - Matcher.find_step_definition_matches: Uses as key function for
        matching_definitions.sort(key=_parser_specificity, reverse=True).

    State and side effects:
        None, pure function. No mutation, no I/O.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    parser_type = step_definition.parser.type
    if parser_type in {
        StepDefinitionPatternType.pytest_bdd_string_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.pytest_bdd_parse_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.pytest_bdd_cfparse_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.cucumber_expression,
    }:
        return 2
    if parser_type in {
        StepDefinitionPatternType.regular_expression,
        StepDefinitionPatternType.pytest_bdd_regular_expression,  # type: ignore[attr-defined]  # extended enum member
    }:
        return 1
    return 0
