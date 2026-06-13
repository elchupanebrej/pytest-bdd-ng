"""
Builds ScenarioLocator instances from pytest marker arguments and user configuration.

Responsibility:
    Builds ScenarioLocator instances from pytest marker arguments and user configuration. Defines
    ScenarioLocatorBuilder, the central class that constructs FileScenarioLocator and UrlScenarioLocator objects by
    resolving feature paths, base directories, base URLs, path types, and scenario filters from a combination of pytest
    CLI options, INI configuration, and per-marker arguments. Also defines FeatureLocatorArgs (a TypedDict for the
    parsed marker arguments) and enrich_feature_locator_args (a function that extracts bound arguments from a pytest
    Mark using inspect.signature).

Reason for existence:
    This module is the bridge between pytest's configuration system and the scenario locator subsystem. pytest markers
    carry keyword arguments that describe what features to collect, but those arguments are raw and unvalidated.
    ScenarioLocatorBuilder is the information expert for "how to interpret pytest marker arguments as scenario locator
    construction parameters." It resolves defaults from pytest config (features_base_dir, features_base_url via
    CLI/INI), normalizes FeaturePathType from strings or enums, builds scenario filters from strings or callables, and
    dispatches to FileScenarioLocator or UrlScenarioLocator constructors. Without this module, every consumer of
    scenario locators would need to duplicate config resolution logic.

Delegates:
    - enrich_feature_locator_args: Unpacks pytest Mark.args and Mark.kwargs using inspect.signature(scenarios).bind() to
    produce a typed FeatureLocatorArgs dict.
    - ScenarioLocatorBuilder.resolve_features_base_dir: Resolves the base directory from args, callables, or pytest
    config (CLI/INI), returning an absolute Path.
    - ScenarioLocatorBuilder.resolve_features_base_url: Resolves the base URL from args, callables, or pytest config,
    returning a Maybe[str].
    - ScenarioLocatorBuilder.resolve_features_path_type: Normalizes a FeaturePathType enum, string, or None into a
    canonical FeaturePathType.
    - ScenarioLocatorBuilder._create_file_locator: Constructs a FileScenarioLocator if the path type and feature paths
    warrant it.
    - ScenarioLocatorBuilder._create_url_locator: Constructs a UrlScenarioLocator (or PyPyUrlScenarioLocator on PyPy) if
    the path type and feature paths warrant it.
    - ScenarioLocatorBuilder.build_scenario_filter: Converts a filter string or callable into a ScenarioLocatorFilterT
    callable.
    - pytest_bdd.scenario.scenarios: Used as the signature template for binding mark arguments.

Cohesion:
    All entities in this module serve the single concern of "turn pytest mark arguments into scenario locators." The
    FeatureLocatorArgs TypedDict defines the argument schema. enrich_feature_locator_args extracts arguments from marks.
    ScenarioLocatorBuilder owns the entire construction pipeline: resolve defaults → normalize types → filter features →
    create locators. The separation into multiple methods is purely organizational — each method handles one aspect of
    the resolution/construction process.

Separation:
    - pytest_bdd.scenario_locator: Owns the actual locator classes (FileScenarioLocator, UrlScenarioLocator) and their
    parsing/collection logic. This module only constructs them — it does not own how they walk directories or fetch
    URLs.
    - pytest_bdd.scenario: Owns the scenarios() function signature and the FeaturePathType enum. This module imports
    them for signature binding and type resolution, but does not own their definition.
    - pytest_bdd.collector.FeatureFileModule: Uses scenario()/scenarios() directly without going through
    ScenarioLocatorBuilder. The builder is the indirect path (via pytest marks), while FeatureFileModule is the direct
    path (via file system collection).

Main consumers:
    - pytest_bdd.plugin.scenario_test_collector: Calls ScenarioLocatorBuilder to convert pytest marker arguments into
    locator instances during autoload/test generation.
    - pytest_bdd.scenario.scenarios: Imports ScenarioLocatorBuilder? No — actually scenarios() creates pytest marks, and
    the plugin later uses the builder to consume those marks. The builder is consumed by the collection/autoload
    pipeline, not by scenarios() directly.

State and side effects:
    ScenarioLocatorBuilder holds a reference to pytest Config. Its methods read from config.getoption() (CLI options),
    config.getini() (INI config), and config.rootpath (the pytest root directory). These are read-only accesses. No
    mutable instance state beyond the config reference. No file I/O directly — file I/O happens in the
    FileScenarioLocator/UrlScenarioLocator that this builder constructs.

Invariants:
    - If both features_base_dir and features_base_url are provided, scenarios() raises ValueError before the builder is
    invoked — the builder itself does not need to check this.
    - The resolve_features_path_type method must raise ValueError for unrecognized string values that cannot be
    converted to FeaturePathType enum.
    - On PyPy, UrlScenarioLocator is replaced with PyPyUrlScenarioLocator to avoid known PyPy compatibility issues.

Failure semantics:
    ScenarioLocatorBuilder.resolve_features_path_type raises ValueError with "Unknown feature path type" if the provided
    value is not a recognized FeaturePathType enum member or string. Other methods use Maybe/Nothing to signal absence
    rather than raising exceptions.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

import platform
from collections.abc import Callable, Iterable
from contextlib import suppress
from inspect import signature
from pathlib import Path
from typing import cast

from attrs import define
from cucumber_messages import (  # upstream library missing type stubs
    GherkinDocument,
    Pickle,  # library has no type stubs
)
from pathvalidate import is_valid_filepath
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result
from typing_extensions import TypedDict

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config, Mark
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_collection import FeatureBaseLoad
from pytest_bdd.scenario import Args, FeaturePathType, scenarios
from pytest_bdd.scenario_locator import (
    FileScenarioLocator,
    PyPyUrlScenarioLocator,
    ScenarioLocatorFilterT,
    UrlScenarioLocator,
)
from pytest_bdd.types.failure_reasons import FeatureLocatorFailure
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import StringRepresentable
from pytest_bdd.util.url import is_url_parsable

FileLocatorResult = Result[FileScenarioLocator, FeatureLocatorFailure]


class FeatureLocatorArgs(TypedDict):
    """
    Typed dictionary defining the complete argument schema for scenario locator construction, matching the parameter list.

    Responsibility:
        Typed dictionary defining the complete argument schema for scenario locator construction, matching the parameter
        list of the scenarios() function. Fields include: feature_paths (list of paths), filter_ (callable/string
        filter), return_test_decorator (bool), encoding (str), features_base_dir (path/config callback),
        features_base_url (str), features_path_type (enum/string), features_mimetype (Mimetype/string), parser_type
        (ParserProtocol subclass), parse_args (Args named tuple), and locators (iterable of pre-built locator objects).
        Serves as the contract between pytest mark argument extraction and locator construction.

    Reason for existence:
        This TypedDict formalizes the loosely-typed keyword arguments that pytest passes through marks into a
        statically-checkable schema. It is the information expert for "what arguments do scenario locators need?"
        Without it, each consumer (enrich_feature_locator_args, ScenarioLocatorBuilder methods) would access raw dict
        keys with string literals, making the contract implicit and fragile. All fields are optional (with None
        defaults) because not all arguments apply to all locator types.

    Delegates:
        - None. This is a pure data schema with no behavior.

    Cohesion:
        All fields are parameters that directly influence scenario locator construction. There are no unrelated
        configuration options or metadata fields.

    Separation:
        - pytest_bdd.scenario.Args: A NamedTuple for parse_args specifically (args + kwargs). FeatureLocatorArgs is the
        broader schema that includes Args as one field.
        - pytest_bdd.scenario_locator.ScenarioLocatorOptions: The locator-level options type. FeatureLocatorArgs is the
        higher-level argument schema from which locator options are derived.

    Main consumers:
        - enrich_feature_locator_args: Returns a FeatureLocatorArgs instance by binding pytest Mark arguments to the
        scenarios() signature.
        - ScenarioLocatorBuilder methods: Read fields from FeatureLocatorArgs to resolve defaults and construct locators.

    State and side effects:
        None, keeps no persistent state. TypedDict is a type-checking construct with no runtime behavior.

    Invariants:
        - All fields default to None or empty collections, making the dict always constructible without arguments.
        - The field names must match the parameter names of scenarios() for enrich_feature_locator_args to work correctly.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    feature_paths: list[Path | str]  # List of paths to features
    filter_: ScenarioLocatorFilterT | str | StringRepresentable | None  # Callable or string filter
    return_test_decorator: bool | None
    encoding: str | None
    features_base_dir: Path | str | None
    features_base_url: str | None
    features_path_type: FeaturePathType | str | None  # Enum or string
    features_mimetype: Mimetype | str | None
    parser_type: type[ParserProtocol] | None
    parse_args: Args | None
    locators: Iterable[object] | None  # Iterable for locators


def enrich_feature_locator_args(mark: Mark) -> FeatureLocatorArgs:
    """
    Extract and validates keyword arguments from a pytest Mark object by binding them to the scenarios() function signat.

    Responsibility:
        Extracts and validates keyword arguments from a pytest Mark object by binding them to the scenarios() function
        signature using inspect.signature.bind(). This transforms raw mark.args and mark.kwargs into a typed
        FeatureLocatorArgs dict with all default values applied, ensuring that missing arguments are filled with their
        documented defaults rather than remaining as None. The resulting dict is the canonical argument representation
        consumed by ScenarioLocatorBuilder.

    Reason for existence:
        pytest marks carry arguments as (args, kwargs) tuples that have no intrinsic schema. This function uses the
        scenarios() function signature as the schema template — by binding the mark's arguments to scenarios()'s
        signature, it validates that the argument names match and fills in defaults. This is the information expert for
        "how to interpret a pytest mark as a set of scenario locator arguments." It is a standalone function (not a
        ScenarioLocatorBuilder method) because it only depends on the scenarios() signature, not on builder state.

    Delegates:
        - inspect.signature(scenarios): Retrieves the function signature used as the binding template.
        - signature.bind(*mark.args, **mark.kwargs): Binds the mark's positional and keyword arguments to the signature.
        - bound_arguments.apply_defaults(): Fills in default values for any unbound parameters.
        - cast(): Converts the bound arguments.arguments dict to FeatureLocatorArgs type.

    Cohesion:
        Single-purpose: extract typed arguments from a mark. Three lines of logic, no branching.

    Separation:
        - ScenarioLocatorBuilder.build_for_pytest_mark: Calls enrich_feature_locator_args and then delegates to
        build_for_feature_locator_args. The extraction and construction concerns are separated.

    Main consumers:
        - ScenarioLocatorBuilder.build_for_pytest_mark: Calls this function to convert a Mark into FeatureLocatorArgs
        before building locators.

    State and side effects:
        None. Pure function with no I/O, no mutation, no config access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    return cast("FeatureLocatorArgs", raw_mark_arguments.arguments)


@define(slots=False)
class ScenarioLocatorBuilder:
    """
    Centralized builder that constructs FileScenarioLocator and UrlScenarioLocator instances from resolved configuration.

    Responsibility:
    Centralized builder that constructs FileScenarioLocator and UrlScenarioLocator instances from resolved
    configuration. Holds a reference to pytest Config and provides a pipeline: resolve defaults from CLI/INI
    configuration → normalize argument types → build scenario filters → create file and/or URL locators. Exposes two
    entry points: build_for_pytest_mark (for pytest mark processing) and build_for_feature_locator_args (for direct
    FeatureLocatorArgs). On PyPy, automatically selects PyPyUrlScenarioLocator instead of UrlScenarioLocator.

    Reason for existence:
        Without this builder, every consumer that needs scenario locators would duplicate the logic of reading pytest
        config options, resolving base directories, normalizing path types, and selecting the appropriate locator class.
        ScenarioLocatorBuilder is the information expert for "how to produce the correct scenario locators from this
        pytest session's configuration." It centralizes config resolution (features_base_dir from CLI option --feature-
        base-dir or INI option feature_base_dir; features_base_url similarly) so that locator construction is consistent
        regardless of entry point.

    Delegates:
        - default_features_base_dir (property): Reads features_base_dir from pytest CLI/INI config, falling back to ".".
        - default_features_base_url (property): Reads features_base_url from pytest CLI/INI config, returning Maybe.
        - resolve_features_base_dir: Resolves the base directory from explicit args, callables, or the default property,
        returning an absolute Path.
        - resolve_features_base_url: Resolves the base URL from explicit args, callables, or the default property,
        returning Maybe[str].
        - resolve_features_path_type: Normalizes the FeaturePathType enum value from various input types.
        - build_scenario_filter: Converts filter specifications (string or callable) into a filter callable.
        - _create_file_locator: Constructs a FileScenarioLocator for file-based feature paths.
        - _create_url_locator: Constructs a UrlScenarioLocator (or PyPyUrlScenarioLocator) for URL-based feature paths.

    Cohesion:
        Every method in this class participates in the locator construction pipeline. The entry points (build_for_*)
        delegate to the same core methods (resolve_*, _create_*). The properties (default_features_base_dir,
        default_features_base_url) encapsulate config reading. There is no logic unrelated to "construct scenario
        locators from configuration."

    Separation:
        - pytest_bdd.scenario_locator.FileScenarioLocator / UrlScenarioLocator: Own the actual locator behavior (file
        walking, URL fetching, caching). The builder only constructs them — it does not own their lifecycle.
        - pytest_bdd.collector.FeatureFileModule: Takes a different path to test generation (directly calling
        scenarios()). The builder is used by the plugin/autoload path, not by FeatureFileModule.

    Main consumers:
        - pytest_bdd.plugin.scenario_test_collector: Calls build_for_pytest_mark during autoload to convert feature-file
        marks into concrete locators.
        - Any code that needs to programmatically construct scenario locators from FeatureLocatorArgs.

    State and side effects:
        Holds config: Config — a reference to the pytest configuration. All methods read from config (getoption, getini,
        rootpath) but do not mutate it. The config reference is set once at construction time and never changed. No
        other mutable state.

    Invariants:
        - The config attribute must be a valid pytest Config with accessible getoption/getini methods.
        - On PyPy, _create_url_locator must substitute PyPyUrlScenarioLocator for UrlScenarioLocator.
        - resolve_features_path_type must raise ValueError for unrecognized string values.

    Failure semantics:
        resolve_features_path_type raises ValueError with "Unknown feature path type" for values that are neither None,
        str, nor FeaturePathType. Other methods use Maybe/Nothing to handle optional values gracefully without
        exceptions.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    config: Config

    @property
    def default_features_base_dir(self) -> str:
        """
        Reads the default features base directory from pytest configuration, checking the CLI option (--feature-base-dir) fir.

        Responsibility:
            Reads the default features base directory from pytest configuration, checking the CLI option (--feature-
            base-dir) first, then the INI option (feature_base_dir), falling back to "." if neither is set. Uses
            contextlib.suppress to silently handle missing options or configuration errors. Returns the resolved
            directory as a string.

        Reason for existence:
            The base directory is a global configuration value that applies to all feature locators in a test session.
            This property centralizes the config-reading logic so that resolve_features_base_dir doesn't need to know
            about CLI vs INI option names or the FeatureBaseLoad enum constants. It is a property (not a method) because
            it represents a derived attribute of the builder's config state.

        Delegates:
            - self.config.getoption: Reads CLI option values.
            - self.config.getini: Reads INI configuration values.
            - FeatureBaseLoad.Cli.DIR_OPTION / FeatureBaseLoad.Ini.DIR_OPTION: String option names used as keys.
            - contextlib.suppress: Silently catches ValueError and KeyError if options are not configured.

        Cohesion:
            Single-purpose: read and resolve the default base directory from config.

        Separation:
            - resolve_features_base_dir: Uses this property as a fallback when no explicit base_dir is provided. The
            property is the "what is the default?" answer; resolve_features_base_dir is the "what is the final value
            after considering explicit args and callables?" answer.

        Main consumers:
            - resolve_features_base_dir: Called when features_base_dir is None (not explicitly provided).

        State and side effects:
            Reads from config.getoption and config.getini. No mutation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        with suppress(ValueError, KeyError):
            base_dir_cli = self.config.getoption(str(FeatureBaseLoad.Cli.DIR_OPTION))
            base_dir_ini = self.config.getini(str(FeatureBaseLoad.Ini.DIR_OPTION))
            if bool(base_dir := base_dir_cli or base_dir_ini):
                return str(base_dir)
        return "."

    @property
    def default_features_base_url(self) -> Maybe[str]:
        """
        Reads the default features base URL from pytest configuration, checking the CLI option (--feature-base-url) first, th.

        Responsibility:
            Reads the default features base URL from pytest configuration, checking the CLI option (--feature-base-url)
            first, then the INI option (feature_base_url), returning Some(url) if either is set, or Nothing if neither
            is configured. Uses contextlib.suppress to silently handle missing options or configuration errors.

        Reason for existence:
            The base URL, like the base directory, is a global configuration value. This property mirrors
            default_features_base_dir but for URL-based feature locations. It returns Maybe instead of a plain string
            because a base URL is genuinely optional — many projects only use local feature files and should not be
            forced to configure a URL. The Maybe type makes the optionality explicit.

        Delegates:
            - self.config.getoption: Reads CLI option values.
            - self.config.getini: Reads INI configuration values.
            - FeatureBaseLoad.Cli.URL_OPTION / FeatureBaseLoad.Ini.URL_OPTION: String option names used as keys.
            - contextlib.suppress: Silently catches ValueError and KeyError.

        Cohesion:
            Single-purpose: read and resolve the default base URL from config. Mirrors default_features_base_dir in structure.

        Separation:
            - resolve_features_base_url: Uses this property as a fallback, then wraps the result in Maybe.

        Main consumers:
            - resolve_features_base_url: Called when features_base_url is None.

        State and side effects:
            Reads from config.getoption and config.getini. No mutation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        with suppress(ValueError, KeyError):
            base_url_cli = self.config.getoption(str(FeatureBaseLoad.Cli.URL_OPTION))
            base_url_ini = self.config.getini(str(FeatureBaseLoad.Ini.URL_OPTION))
            if bool(base_url := base_url_cli or base_url_ini):
                return Some(str(base_url))
        return Nothing

    def build_for_pytest_mark(self, mark: Mark) -> Iterable[object]:
        """
        Entry point for converting a pytest Mark into an iterable of scenario locator objects.

        Responsibility:
            Entry point for converting a pytest Mark into an iterable of scenario locator objects. Delegates to
            enrich_feature_locator_args to extract typed arguments from the mark, then yields all locators produced by
            build_for_feature_locator_args. The yield-from pattern allows the method to produce zero, one, or two
            locators (file + URL) depending on the mark's arguments.

        Reason for existence:
            This is the primary entry point used by the scenario_test_collector plugin during autoload. It bridges the
            pytest mark system (which uses Mark objects with raw args/kwargs) to the typed FeatureLocatorArgs system
            used by the rest of the builder. It exists as a thin adapter method rather than being inlined in the plugin
            to keep the mark-to-args conversion logic in the builder family.

        Delegates:
            - enrich_feature_locator_args: Converts Mark → FeatureLocatorArgs.
            - build_for_feature_locator_args: Converts FeatureLocatorArgs → Iterable[locator].

        Cohesion:
            Single-purpose adapter: Mark → locators. Two lines of logic.

        Separation:
            - build_for_feature_locator_args: The core construction method. build_for_pytest_mark is a thin mark-aware wrapper.

        Main consumers:
            - pytest_bdd.plugin.scenario_test_collector: Called during autoload to process feature-file marks.

        State and side effects:
            None beyond what build_for_feature_locator_args triggers. No direct config access (that happens downstream).

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        yield from self.build_for_feature_locator_args(enrich_feature_locator_args(mark))

    def build_for_feature_locator_args(self, feature_locator_args: FeatureLocatorArgs) -> Iterable[object]:
        """
        Core construction method that builds scenario locators from a typed FeatureLocatorArgs dict.

        Responsibility:
            Core construction method that builds scenario locators from a typed FeatureLocatorArgs dict. First yields
            any pre-built locators provided in the "locators" field. Then resolves the base directory, base URL, and
            path type from the args (with config fallbacks). Builds a scenario filter from the filter_ field. Constructs
            a FileScenarioLocator (via _create_file_locator) if the path type and feature paths justify it, and a
            UrlScenarioLocator (via _create_url_locator) similarly. Yields all constructed locators.

        Reason for existence:
            This is the main orchestrator of the locator construction pipeline. It sequences the resolution and
            construction steps in the correct order, ensuring dependencies are satisfied (e.g., the base directory is
            resolved before the file locator is created). It is the information expert for "given these feature locator
            arguments, what locators should be produced?"

        Delegates:
            - resolve_features_base_dir: Resolves the base directory.
            - resolve_features_base_url: Resolves the base URL.
            - resolve_features_path_type: Normalizes the path type.
            - build_scenario_filter: Constructs the filter callable.
            - _create_file_locator: Builds a FileScenarioLocator if applicable.
            - _create_url_locator: Builds a UrlScenarioLocator if applicable.

        Cohesion:
            The method is a linear pipeline: yield pre-built → resolve config → create file locator → create URL
            locator. Every step serves the construction goal.

        Separation:
            - build_for_pytest_mark: The mark-aware entry point that delegates to this method.
            - The individual _create_* and resolve_* methods: Each handles one aspect of resolution or construction.

        Main consumers:
            - build_for_pytest_mark: The primary caller.
            - Any code with a pre-built FeatureLocatorArgs dict.

        State and side effects:
            Resolves paths against config.rootpath. May access config options. No mutation of instance state beyond config reads.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        yield from feature_locator_args.get("locators") or []
        features_base_dir = self.resolve_features_base_dir(feature_locator_args.get("features_base_dir"))
        features_base_url = self.resolve_features_base_url(feature_locator_args.get("features_base_url")).value_or(None)
        features_path_type = self.resolve_features_path_type(feature_locator_args.get("features_path_type"))
        filter_ = self.build_scenario_filter(feature_locator_args.get("filter_")).value_or(None)

        if file_locator := self._create_file_locator(
            feature_locator_args,
            filter_,
            features_base_dir,
            features_path_type,
        ).value_or(None):
            yield file_locator
        if url_locator := self._create_url_locator(
            feature_locator_args,
            filter_,
            features_base_url,
            features_path_type,
        ).value_or(None):
            yield url_locator

    def resolve_features_base_dir(self, features_base_dir: str | Path | Callable[[Config], str] | None) -> Path:
        """
        Resolve the features base directory to an absolute Path.

        Responsibility:
            Resolves the features base directory to an absolute Path. Accepts a string, Path, callable (receiving Config
            and returning str), or None. If None, falls back to self.default_features_base_dir. If callable, invokes it
            with self.config. If the resulting path is relative, resolves it against config.rootpath. Returns the
            absolute Path.

        Reason for existence:
            The base directory can come from multiple sources: explicit argument, a callable (for dynamic resolution),
            or pytest config defaults. This method is the single resolution point that handles all three cases and
            guarantees an absolute Path output. It is separate from default_features_base_dir (which only handles config
            defaults) to keep the fallback chain clean.

        Delegates:
            - self.default_features_base_dir: Provides the default value when features_base_dir is None.
            - self.config.rootpath: Used as the base for resolving relative paths.
            - Path().is_absolute(): Determines whether path resolution is needed.
            - Path().resolve(): Resolves the path to absolute form.

        Cohesion:
            Single-purpose: resolve base directory to absolute Path. The if/elif/else chain handles the three input types.

        Separation:
            - resolve_features_base_url: Mirrors this method for URL resolution.

        Main consumers:
            - build_for_feature_locator_args: Passes the resolved base dir to _create_file_locator.

        State and side effects:
            Reads config.rootpath. No mutation.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        resolved_features_base_dir: str
        if features_base_dir is None:
            resolved_features_base_dir = self.default_features_base_dir
        elif callable(features_base_dir):
            resolved_features_base_dir = features_base_dir(self.config)
        else:
            resolved_features_base_dir = str(features_base_dir)

        if (resolved_path := Path(resolved_features_base_dir)).is_absolute():
            return resolved_path

        return cast("Path", (self.config.rootpath / resolved_features_base_dir).resolve())

    def resolve_features_base_url(self, features_base_url: str | Path | Callable[[Config], str] | None) -> Maybe[str]:
        """
        Resolve the features base URL, returning a Maybe[str].

        Responsibility:
            Resolves the features base URL, returning a Maybe[str]. Accepts a string, Path, callable, or None. If None,
            falls back to self.default_features_base_url (which returns Maybe). If callable, invokes it with
            self.config. Returns Nothing if the final value is None (no base URL configured), or Some(url) if a URL is
            available.

        Reason for existence:
            Like resolve_features_base_dir, this method centralizes the resolution of a configuration value that can
            come from multiple sources. It uses Maybe instead of a plain string to make the optionality of base URLs
            explicit — file-only projects should not need a base URL, and downstream code
            (build_for_feature_locator_args, _create_url_locator) uses .value_or(None) to handle the None case cleanly.

        Delegates:
            - self.default_features_base_url: Provides the default Maybe[str] when features_base_url is None.
            - callable invocation: If features_base_url is a callable, calls it with self.config.

        Cohesion:
            Single-purpose: resolve base URL to Maybe[str]. Mirrors resolve_features_base_dir.

        Separation:
            - resolve_features_base_dir: Path-based counterpart.

        Main consumers:
            - build_for_feature_locator_args: Passes the resolved base URL to _create_url_locator.

        State and side effects:
            Reads config via default_features_base_url (which calls getoption/getini). No mutation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if features_base_url is None:
            features_base_url = self.default_features_base_url.value_or(None)
        if callable(features_base_url):
            features_base_url = features_base_url(self.config)
        return Nothing if features_base_url is None else Some(str(features_base_url))

    @staticmethod
    def resolve_features_path_type(feature_path_type: FeaturePathType | str | None = None) -> FeaturePathType:
        """
        Normaliz a FeaturePathType specification into a canonical FeaturePathType enum value.

        Responsibility:
            Normalizes a FeaturePathType specification into a canonical FeaturePathType enum value. Accepts None
            (returns UNDEFINED), a FeaturePathType enum value (returns as-is), or a string (converts via FeaturePathType
            constructor). Raises ValueError for unrecognized string values that cannot be converted to a valid enum
            member.

        Reason for existence:
            FeaturePathType can be specified as a string (e.g., in INI config or CLI options), as an enum value (in
            Python code), or omitted entirely. This static method handles all three cases and guarantees a valid enum
            output. It is static because it has no dependency on config or instance state — it's a pure type conversion
            utility.

        Delegates:
            - isinstance checks: Determine the input type.
            - FeaturePathType(str): Converts a string to the enum member.

        Cohesion:
            Single-purpose: normalize path type to enum. The if/elif chain covers the three input variants.

        Separation:
            - pytest_bdd.scenario.FeaturePathType: Owns the enum definition. This method only normalizes/converts.

        Main consumers:
            - build_for_feature_locator_args: Resolves the path type before dispatching to _create_file_locator /
            _create_url_locator.

        State and side effects:
            None. Pure function.

        Failure semantics:
            Raises ValueError with "Unknown feature path type" if the input is not None, not a string, and not a
            FeaturePathType instance.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if feature_path_type is None:
            return FeaturePathType.UNDEFINED
        if isinstance(feature_path_type, str):
            return FeaturePathType(feature_path_type)
        if isinstance(feature_path_type, FeaturePathType):
            return feature_path_type
        msg = "Unknown feature path type"
        raise ValueError(msg)

    @staticmethod
    def _create_file_locator(
        feature_locator_args: FeatureLocatorArgs,
        filter_: ScenarioLocatorFilterT | None,
        features_base_dir: Path,
        features_path_type: FeaturePathType,
    ) -> Maybe[FileScenarioLocator]:
        """
        Construct a FileScenarioLocator from the given arguments, but only if the feature_path_type and feature_paths justif.

        Responsibility:
            Constructs a FileScenarioLocator from the given arguments, but only if the feature_path_type and
            feature_paths justify file-based location. Extracts feature_paths from the args, filters them based on
            path_type (PATH matches all, UNDEFINED matches paths that pass is_valid_filepath, other types get empty
            list), and returns Nothing if no valid file paths remain. Otherwise returns Some(FileScenarioLocator) with
            the filtered paths, filter, base_dir, encoding, mimetype, parser_type, and parse_args.

        Reason for existence:
            Not all feature locator arguments produce file locators — some produce URL locators, some produce both, some
            produce neither. This static method encapsulates the decision of "should a FileScenarioLocator be created?"
            along with the construction logic. It is static because it needs only the arguments, not the builder's
            config state (the base_dir has already been resolved by build_for_feature_locator_args).

        Delegates:
            - is_valid_filepath: Validates that a path string is a valid file path on the current platform.
            - FileScenarioLocator constructor: Creates the actual locator instance.

        Cohesion:
            The method does two things: filter paths for file compatibility, then construct the locator. Both serve the
            single goal of "produce a FileScenarioLocator if appropriate."

        Separation:
            - _create_url_locator: The URL counterpart with parallel structure but different path filtering
            (is_url_parsable) and different locator class.

        Main consumers:
            - build_for_feature_locator_args: Called for the file locator branch.

        State and side effects:
            None. Static method with no I/O, no config access.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        feature_paths = list(feature_locator_args.get("feature_paths", []) or [])
        if features_path_type is FeaturePathType.PATH:
            file_locator_feature_paths = feature_paths
        elif features_path_type is FeaturePathType.UNDEFINED:
            file_locator_feature_paths = [p for p in feature_paths if is_valid_filepath(Path(p), platform="auto")]
        else:
            file_locator_feature_paths = []

        if not file_locator_feature_paths:
            return Nothing

        return Some(
            FileScenarioLocator(
                feature_paths=file_locator_feature_paths,
                filter_=filter_,
                features_base_dir=features_base_dir,
                encoding=feature_locator_args.get("encoding"),
                mimetype=feature_locator_args.get("features_mimetype"),
                parser_type=feature_locator_args.get("parser_type"),
                parse_args=feature_locator_args.get("parse_args"),
            ),
        )

    @staticmethod
    def _create_url_locator(
        feature_locator_args: FeatureLocatorArgs,
        filter_: ScenarioLocatorFilterT | None,
        features_base_url: str | None,
        features_path_type: FeaturePathType,
    ) -> Maybe[UrlScenarioLocator]:
        """
        Construct a UrlScenarioLocator (or PyPyUrlScenarioLocator on PyPy) from the given arguments, but only if the feature.

        Responsibility:
            Constructs a UrlScenarioLocator (or PyPyUrlScenarioLocator on PyPy) from the given arguments, but only if
            the feature_path_type and feature_paths justify URL-based location. Extracts feature_paths from the args,
            filters them based on path_type (URL matches all, UNDEFINED matches paths that pass is_url_parsable, other
            types get empty list), and returns Nothing if no valid URL paths remain. On PyPy, selects
            PyPyUrlScenarioLocator to avoid known PyPy compatibility issues with standard URL fetching. Returns
            Some(locator) with url_paths, filter, encoding, features_base_url, mimetype, parser_type, and parse_args.

        Reason for existence:
            The URL locator construction mirrors _create_file_locator but with URL-specific path filtering and PyPy-
            awareness. The PyPy conditional (platform.python_implementation() == "PyPy") is encapsulated here rather
            than leaked to callers. This static method isolates URL-locator-specific decisions from the rest of the
            builder.

        Delegates:
            - is_url_parsable: Validates that a path string is a valid URL.
            - UrlScenarioLocator or PyPyUrlScenarioLocator constructor: Creates the actual locator instance.
            - platform.python_implementation(): Detects PyPy for locator class selection.

        Cohesion:
            The method filters paths for URL compatibility, selects the appropriate locator class, and constructs it.
            All steps serve the single goal of "produce a UrlScenarioLocator if appropriate."

        Separation:
            - _create_file_locator: The file counterpart. Parallel structure but distinct filtering and class selection.

        Main consumers:
            - build_for_feature_locator_args: Called for the URL locator branch.

        State and side effects:
            None. Static method with no I/O, no config access. Calls platform.python_implementation().

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        feature_paths = list(feature_locator_args.get("feature_paths", []) or [])

        if features_path_type is FeaturePathType.URL:
            url_locator_feature_paths = feature_paths
        elif features_path_type is FeaturePathType.UNDEFINED:
            url_locator_feature_paths = [p for p in feature_paths if is_url_parsable(p)]
        else:
            url_locator_feature_paths = []

        if not url_locator_feature_paths:
            return Nothing

        if platform.python_implementation() == "PyPy":
            locator_class: type[UrlScenarioLocator] = PyPyUrlScenarioLocator
        else:
            locator_class = UrlScenarioLocator

        return Some(
            locator_class(  # pydantic v1 compatibility in pydantic v2
                url_paths=url_locator_feature_paths,
                filter_=filter_,
                encoding=feature_locator_args.get("encoding"),
                features_base_url=features_base_url,
                mimetype=feature_locator_args.get("features_mimetype"),
                parser_type=feature_locator_args.get("parser_type"),
                parse_args=feature_locator_args.get("parse_args"),
            ),
        )

    @staticmethod
    def build_scenario_filter(
        filter_: ScenarioLocatorFilterT | str | StringRepresentable | None,
    ) -> Maybe[ScenarioLocatorFilterT]:
        """
        Convert a scenario filter specification into a callable filter function.

        Responsibility:
            Converts a scenario filter specification into a callable filter function. Accepts a callable (returned as-
            is, wrapped in Some), None (returns Nothing, no filtering), a string (creates a filter that matches
            pickle.name against the string), or a StringRepresentable (converts to string first, then creates the same
            name-matching filter). The generated filter function has the standard ScenarioLocatorFilterT signature:
            (config, gherkin_document, pickle) -> bool.

        Reason for existence:
            pytest marks accept scenario filters as strings or callables, but locators require callables. This static
            method handles the conversion, including the creation of an inner function (updated_filter) that closes over
            the filter string. The string-to-callable conversion allows users to write @scenarios("features/",
            filter_="my scenario name") without writing a lambda.

        Delegates:
            - updated_filter (inner function): A closure that compares pickle.name against the captured filter string.

        Cohesion:
            Single-purpose: normalize filter specification to Maybe[callable]. The if/elif chain handles the three input types.

        Separation:
            - ScenarioLocatorFilterT: The type alias for the filter callable, defined in scenario_locator. This method
            produces values of that type.

        Main consumers:
            - build_for_feature_locator_args: Calls this to resolve the filter before passing it to _create_file_locator
            and _create_url_locator.

        State and side effects:
            None. Static method. When a string filter is provided, creates a closure (updated_filter) that captures the
            string value.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if callable(filter_):
            return Some(filter_)

        if filter_ is None:
            return Nothing

        if not isinstance(filter_, str):
            filter_ = str(filter_)

        def updated_filter(
            config: Config | HasPytestStash,  # noqa: ARG001 typecheck
            gherkin_document: GherkinDocument,  # noqa: ARG001 typecheck
            pickle: Pickle,
        ) -> bool:
            """
            Closure-based scenario filter that matches a pickle's name against a captured filter string.

            Responsibility:
                Closure-based scenario filter that matches a pickle's name against a captured filter string. Takes the
                standard filter signature (config, gherkin_document, pickle) but only uses pickle.name for comparison —
                the other arguments are accepted for interface compatibility. Returns True if pickle.name equals the
                filter string, False otherwise.

            Reason for existence:
                When a user provides a string filter like `filter_="Successful login"`, the builder needs to convert it
                into a callable. This inner function is created for each string filter, closing over the filter string
                value. It exists as a nested function rather than a lambda because the function body is a single
                expression and benefits from a descriptive name and docstring.

            Delegates:
                - pickle.name: The scenario name attribute used for comparison.

            Cohesion:
                Single-purpose predicate: does this pickle's name match the filter? Two lines of logic.

            Separation:
                - The outer build_scenario_filter: Creates this function. The separation between "decide what filter to
                create" and "the filter function itself" follows the strategy pattern.

            Main consumers:
                - FileScenarioLocator and UrlScenarioLocator: Call the filter function for each discovered scenario to
                decide whether to include it.

            State and side effects:
                None. The closure captures the filter string immutably. The function is stateless.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=5
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
            """
            return bool(filter_ == pickle.name)

        return Some(updated_filter)
