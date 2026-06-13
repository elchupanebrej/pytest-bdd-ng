"""
Defines the core protocol interfaces (ScenarioLocatorFeatureResolver, ScenarioLocatorReadObserver, ScenarioLocatorRes.

Responsibility:
    Defines the core protocol interfaces (ScenarioLocatorFeatureResolver, ScenarioLocatorReadObserver,
    ScenarioLocatorResolver, ScenarioLocatorHookProtocol) and the reusable ScenarioLocatorFilterMixin class that form
    the foundation of the scenario location subsystem. The protocols establish contracts for feature resolution (parse
    feature files → ParsedFeature + Source tuples), scenario resolution (resolve features → filter pickles → yield
    GherkinDocument/Pickle/Source tuples), read observation (on_source_loaded, on_feature_loaded, on_pickle_loaded
    callbacks for batch parsing integration), and hook-based customization (pytest_bdd_get_mimetype for media type
    detection, pytest_bdd_get_parser for parser selection). The filter mixin implements the common resolve() pipeline
    that chains: resolve_features → bind features → notify observer → filter scenarios → yield results.

Reason for existence:
    This module is the architectural abstraction layer that decouples "how scenarios are found" from "what to do with
    found scenarios." The protocols enable the collector layer to work with any scenario locator implementation (file-
    based, URL-based, or future database/git-based) without knowing implementation details. The filter mixin provides a
    reusable pipeline that all concrete locators inherit, avoiding code duplication between FileScenarioLocator and
    UrlScenarioLocator. The hook protocol enables plugin-based customization of mimetype detection and parser selection
    without modifying core locator logic.

Delegates:
    - cucumber_messages: Provides GherkinDocument, Pickle, and Source types — the standard cucumber-messages data model
    for Gherkin parsed documents.
    - pytest_bdd.compatibility.pytest.Config: Provides pytest configuration access for hook invocation and stash access.
    - pytest_bdd.model.run.Run: Provides from_stash() for accessing the Run model to bind features.
    - pytest_bdd.util.other.IdGenerator: Provides pickle ID generation during feature binding.
    - attrs.define: Provides the frozen/slotted class definition for the filter mixin.

Cohesion:
    All protocols and the mixin serve the same subsystem: scenario location and filtering. The protocols define the
    contracts (what must be implemented), the mixin provides common behavior (how the resolve pipeline works), and the
    type alias ScenarioLocatorFilterT defines the filter function signature. Every entity in this module is a building
    block for scenario locators.

Separation:
    - pytest_bdd.scenario_locator.file_locator.FileScenarioLocator: Kept separate because file_locator implements the
    protocol contracts for file-system-based location, while base defines the contracts — implementation vs interface.
    - pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator: Kept separate because url_locator implements protocol
    contracts for URL-based location.
    - pytest_bdd.collector: Kept separate because collector owns test collection lifecycle, while base defines the
    location interfaces that collector consumes.

Main consumers:
    - pytest_bdd.scenario_locator.file_locator: FileScenarioLocator inherits from ScenarioLocatorFilterMixin and
    implements ScenarioLocatorFeatureResolver.
    - pytest_bdd.scenario_locator.url_locator: UrlScenarioLocator inherits from ScenarioLocatorFilterMixin and
    implements ScenarioLocatorFeatureResolver.
    - pytest_bdd.collector: Uses ScenarioLocatorResolver protocol to discover scenarios during test collection.
    - Plugin entry points: Implement ScenarioLocatorHookProtocol to provide custom mimetype detection and parser selection.

State and side effects:
    None at the protocol/mixin level. The filter mixin has a stateless filter_ attribute (optional callable). The
    _bind_feature static method reads from config.stash (read-only). resolve_features is abstract (implemented by
    subclasses).

Invariants:
    - The resolve() pipeline in ScenarioLocatorFilterMixin must always: resolve features → bind each feature (creating
    pickles) → notify observer (if present) → filter scenarios → yield matched (document, pickle, source) triples.
    - filter_scenarios() must pass all pickles when filter_ is None.
    - _bind_feature must call Run.from_stash(config.stash) and ensure_pickles() with an IdGenerator from stash.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

from attrs import define, field
from cucumber_messages import GherkinDocument, Pickle, Source

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.run import Run
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from enum import Enum
    from pathlib import Path

    from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
    from pytest_bdd.mimetype import Mimetype
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    """
    Defines the runtime-checkable Protocol for the feature resolution stage of scenario location: concrete implementation.

    Responsibility:
        Defines the runtime-checkable Protocol for the feature resolution stage of scenario location: concrete
        implementations must provide resolve_features() that takes a pytest Config or HasPytestStash object and returns
        an iterable of (ParsedFeature, Source) tuples. This is the first stage of the scenario location pipeline —
        discovering and parsing feature files from their source (disk, URL, database, etc.) into parsed document +
        source metadata pairs. The parsed features are later bound to the Run model and their pickles are filtered for
        scenario collection.

    Reason for existence:
        This protocol abstracts "where features come from" away from "how scenarios are collected." Different locators
        resolve features differently: FileScenarioLocator reads from disk, UrlScenarioLocator fetches from URLs, and
        future locators might read from databases or version control. All produce the same (ParsedFeature, Source)
        output that the pipeline consumes. Without this protocol, the scenario resolution pipeline would be tightly
        coupled to the feature source, making new locator types impossible to add.

    Delegates:
        - Config | HasPytestStash: The pytest configuration/context needed for hook invocation and stash access during
        feature resolution.
        - ParsedFeature + Source: The output types representing a parsed Gherkin document with its raw source data.

    Cohesion:
        The single method resolve_features() is perfectly focused on one operation: given configuration, produce parsed
        features. The protocol is minimal by design — it defines only what's needed, leaving implementation details to
        concrete classes.

    Separation:
        - ScenarioLocatorResolver: Kept separate because ScenarioLocatorResolver defines the full resolution pipeline
        (features → pickles → filtered results), while ScenarioLocatorFeatureResolver defines only the feature discovery
        stage — feature discovery vs complete resolution.
        - ScenarioLocatorReadObserver: Kept separate because the observer protocol defines callbacks during reading,
        while this protocol defines the reading itself — notification vs action.

    Main consumers:
        - ScenarioLocatorFilterMixin.resolve(): Calls self.resolve_features(config) as the first step of the resolution
        pipeline.
        - FileScenarioLocator: Implements this protocol for file-system-based feature resolution.
        - UrlScenarioLocator: Implements this protocol for URL-based feature resolution.

    State and side effects:
        None. Protocol definition — no implementation.

    Invariants:
        - resolve_features() must return an Iterable, not a single result — feature locators may discover zero or more
        feature files.
        - The returned ParsedFeature must include gherkin_document (parsed GherkinDocument), filename, and raw_data.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def resolve_features(
        self,
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[ParsedFeature, Source]]:  # pragma: no cover
        """
        Define the contract for discovering and parsing feature files from a source: accepts pytest configuration for hook/m.

        Responsibility:
            Defines the contract for discovering and parsing feature files from a source: accepts pytest configuration
            for hook/mimetype/parser resolution, returns an iterable of fully parsed feature documents paired with their
            source metadata. This is the entry point that concrete locators (file-based, URL-based) must implement to
            feed features into the scenario resolution pipeline.

        Reason for existence:
            This is the first stage of the scenario location pipeline. It separates "finding and parsing files" from
            "binding to the runtime model and filtering pickles," enabling different feature sources to be plugged in
            without modifying the binding and filtering logic. The Config/HasPytestStash parameter provides access to
            hooks for mimetype detection, parser selection, and stash access for IdGenerator retrieval.

        Delegates:
            - Config.hook: Provides access to pytest_bdd_get_mimetype and pytest_bdd_get_parser hooks for
            mimetype/parser resolution.
            - HasPytestStash.stash: Provides access to the Run model and IdGenerator for feature binding.

        Cohesion:
            The method signature is perfectly focused on the single operation of feature discovery and parsing.

        Separation:
            - ScenarioLocatorResolver.resolve: Kept separate because resolve() is the full pipeline (features → binding
            → filtering → yielding), while resolve_features() is just the discovery stage — pipeline orchestrator vs
            stage implementation.

        Main consumers:
            - ScenarioLocatorFilterMixin.resolve(): Calls self.resolve_features(config) to kick off the pipeline.
            - Concrete locators: FileScenarioLocator and UrlScenarioLocator implement this method.

        State and side effects:
            None. Protocol definition — implementation-dependent. Concrete implementations may perform file I/O, network
            I/O, or other side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


@runtime_checkable
class ScenarioLocatorReadObserver(Protocol):
    """
    Defines the runtime-checkable Protocol for observers that receive callbacks during the scenario resolution reading pr.

    Responsibility:
        Defines the runtime-checkable Protocol for observers that receive callbacks during the scenario resolution
        reading process: on_source_loaded(gherkin_document, source) called when a source file is loaded (before
        parsing), on_feature_loaded(gherkin_document) called after a feature is fully parsed and its GherkinDocument is
        available, and on_pickle_loaded(gherkin_document, pickle) called for each pickle/scenario extracted from the
        feature. This enables batch parsers and caching systems to observe and record parsing results as they happen.

    Reason for existence:
        The FeatureBatchParser (used for caching/performance optimization) needs to observe feature loading to populate
        its cache. Without an observer pattern, the batch parser would need to intercept the locator pipeline at every
        stage, creating tight coupling. The observer protocol decouples the "what to do with loaded documents" from the
        "how to load documents," enabling the batch parser, coverage trackers, and other consumers to observe the
        pipeline without modifying locator implementations.

    Delegates:
        - GherkinDocument: The parsed Gherkin document passed in callbacks.
        - Source: The source metadata (URI, data, media_type) of the loaded feature file.
        - Pickle: The compiled pickle (executable scenario) extracted from the Gherkin document.

    Cohesion:
        All three callbacks serve the same purpose: observing the progressive loading of features. on_source_loaded
        captures raw source, on_feature_loaded captures parsed documents, on_pickle_loaded captures executable
        scenarios. Together they form a complete observation timeline.

    Separation:
        - ScenarioLocatorFeatureResolver: Kept separate because this protocol observes feature loading, while
        ScenarioLocatorFeatureResolver performs feature loading — observer vs actor pattern.
        - ScenarioLocatorResolver: Kept separate because this protocol observes individual loading events, while
        ScenarioLocatorResolver orchestrates the full pipeline — event observation vs pipeline orchestration.

    Main consumers:
        - ScenarioLocatorFilterMixin.resolve(): Calls observer methods during the resolution pipeline when observer is not None.
        - FeatureBatchParser: Implements this protocol to cache parsed GherkinDocuments for later reuse.

    State and side effects:
        None. Protocol definition. Implementations may cache documents or track coverage as side effects of the callbacks.

    Invariants:
        - on_source_loaded must be called before on_feature_loaded for the same feature.
        - on_pickle_loaded must be called after on_source_loaded and on_feature_loaded, during the pickle iteration phase.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:  # pragma: no cover
        """
        Invoke callback when a feature file source has been loaded and its content is available as a GherkinDocument, before.

        Responsibility:
            Callback invoked when a feature file source has been loaded and its content is available as a
            GherkinDocument, before any further processing (pickle extraction). Provides the parsed document and the
            source metadata (URI, data, media_type) to observers such as batch parsers that cache documents for later
            reuse.

        Reason for existence:
            The batch parser needs the GherkinDocument and Source to cache parsed results. This callback provides the
            complete parsed state at the earliest possible point in the pipeline, allowing the batch parser to store the
            document before pickles are extracted and scenarios are filtered.

        Delegates:
            - GherkinDocument: The fully parsed Gherkin AST with feature, scenarios, steps, and tags.
            - Source: Metadata about the source file including URI for later retrieval.

        Cohesion:
            The callback signature captures exactly what an observer needs at the source-loaded stage: the parsed
            document and its source identity.

        Separation:
            - on_feature_loaded: Kept separate because on_feature_loaded provides document-only context (after source
            processing is complete), while on_source_loaded provides document + source — different stages of the loading
            lifecycle.
            - on_pickle_loaded: Kept separate because on_pickle_loaded provides per-pickle granularity (after pickle
            extraction), while on_source_loaded provides per-feature granularity.

        Main consumers:
            - FeatureBatchParser: Implements this to cache GherkinDocuments in its internal storage.
            - ScenarioLocatorFilterMixin.resolve(): Calls this when observer is provided, between source loading and
            feature loading notifications.

        State and side effects:
            None. Protocol definition. Implementations typically cache or track state as a side effect.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:  # pragma: no cover
        """
        Invoke callback after a feature file has been fully parsed and its GherkinDocument is complete, after on_source_load.

        Responsibility:
            Callback invoked after a feature file has been fully parsed and its GherkinDocument is complete, after
            on_source_loaded but before pickle extraction begins. Provides just the parsed document (without Source
            metadata) to observers that only need the document content, not the source identity.

        Reason for existence:
            Some observers (coverage trackers, feature validators) only need the GherkinDocument content and don't need
            the Source metadata. This callback provides a focused notification at the feature-loaded stage, keeping the
            observer interface minimal when source information is not required.

        Delegates:
            - GherkinDocument: The fully parsed Gherkin AST.

        Cohesion:
            Simple callback: document available → notify. No extraneous parameters.

        Separation:
            - on_source_loaded: Kept separate because on_source_loaded includes Source metadata, enabling caching by
            source identity — different observer needs.
            - on_pickle_loaded: Kept separate because pickle loading is a later stage in the pipeline.

        Main consumers:
            - ScenarioLocatorFilterMixin.resolve(): Called after on_source_loaded during the resolution pipeline.

        State and side effects:
            None. Protocol definition.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:  # pragma: no cover
        """
        Invoke callback for each pickle (executable scenario) extracted from a GherkinDocument during the scenario filtering.

        Responsibility:
            Callback invoked for each pickle (executable scenario) extracted from a GherkinDocument during the scenario
            filtering phase. Provides both the parent GherkinDocument (for context/feature-level metadata) and the
            specific Pickle (for scenario-level execution). This is the most granular callback, called once per scenario
            after filtering decisions have been made.

        Reason for existence:
            Pickle-level observation enables fine-grained tracking: progress reporters can count how many scenarios have
            been loaded, coverage trackers can record scenario-level metadata, and batch parsers can cache pickle-
            specific information. The GherkinDocument parameter is included alongside the Pickle so observers can access
            feature-level context (feature name, tags, description) without maintaining their own document-to-pickle
            mapping.

        Delegates:
            - GherkinDocument: The parent feature document for context.
            - Pickle: The executable scenario with steps, tags, and source references.

        Cohesion:
            Perfectly focused: one callback per scenario, with all relevant context (document + pickle).

        Separation:
            - on_feature_loaded: Kept separate because on_feature_loaded is per-feature while on_pickle_loaded is per-
            scenario — different granularities.
            - on_source_loaded: Kept separate because on_source_loaded is per-source-file while on_pickle_loaded is per-
            pickle — file vs scenario granularity.

        Main consumers:
            - ScenarioLocatorFilterMixin.resolve(): Called inside the pickle iteration loop after filter_scenarios()
            yields each matched pickle.
            - Progress reporters and coverage trackers: Implement this to track scenario-level loading progress.

        State and side effects:
            None. Protocol definition.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    """
    Defines the runtime-checkable Protocol for the complete scenario resolution pipeline: concrete implementations must p.

    Responsibility:
        Defines the runtime-checkable Protocol for the complete scenario resolution pipeline: concrete implementations
        must provide resolve() that takes a pytest Config and an optional ScenarioLocatorReadObserver, and returns an
        iterable of (GherkinDocument, Pickle, Source) triples. This is the primary interface that the collector layer
        uses to discover scenarios — it produces the complete set of executable scenarios with their parsed feature
        documents and source metadata, ready for test item creation.

    Reason for existence:
        This protocol is the boundary between the scenario location subsystem and the test collection subsystem. The
        collector calls resolve() without knowing whether scenarios come from local files, remote URLs, databases, or
        any combination. The observer parameter enables batch parsers and progress reporters to hook into the loading
        process. Without this protocol, the collector would need to handle each locator type separately, violating the
        open-closed principle for new feature sources.

    Delegates:
        - Config | HasPytestStash: Configuration for hook invocation and stash access.
        - ScenarioLocatorReadObserver: Optional observer for tracking loading progress.
        - GherkinDocument, Pickle, Source: The output triple representing a fully resolved executable scenario.

    Cohesion:
        The single method resolve() captures the complete scenario resolution contract in one signature. All needed
        inputs (config, observer) and outputs (document, pickle, source) are specified.

    Separation:
        - ScenarioLocatorFeatureResolver: Kept separate because FeatureResolver handles only the feature discovery
        stage, while Resolver handles the complete pipeline (features → bindings → pickles → filtered results) — stage
        vs complete pipeline.
        - ScenarioLocatorFilterMixin: Kept separate because the mixin provides a reusable implementation of resolve()
        that concrete locators inherit, while this protocol defines the interface they must satisfy.

    Main consumers:
        - pytest_bdd.collector: Calls resolve() on scenario locators during test collection to discover executable scenarios.
        - pytest_bdd.scenario.scenarios(): Uses resolve() when the scenarios() function is called to dynamically load scenarios.

    State and side effects:
        None. Protocol definition. Concrete implementations may perform I/O, cache documents, and modify Run model state.

    Invariants:
        - resolve() must yield all scenarios matching any configured filters — it should not silently skip scenarios
        without a filtering reason.
        - The observer callbacks must be called in order: on_source_loaded → on_feature_loaded → on_pickle_loaded for
        each feature.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterable[tuple[GherkinDocument, Pickle, Source]]:  # pragma: no cover
        """
        Define the contract for the complete scenario resolution pipeline — the single entry point that discovers, parses, b.

        Responsibility:
            Defines the contract for the complete scenario resolution pipeline — the single entry point that discovers,
            parses, binds, filters, and yields executable scenario triples. Accepts pytest configuration and an optional
            observer for progress tracking, returns an iterable of (parsed document, executable pickle, source metadata)
            triples that the collector uses to create test items.

        Reason for existence:
            This is the main interface between scenario location and test collection. All scenario discovery flows
            through this method, regardless of the feature source. The keyword-only observer parameter keeps the
            interface clean for the common case (no observer), while allowing batch parsers to hook in when needed.

        Delegates:
            - config: Provides hook access and stash access for mimetype/parser resolution and Run model access.
            - observer: Receives callbacks during loading for caching, progress reporting, or coverage tracking.

        Cohesion:
            The signature captures the complete input/output contract for scenario resolution in a single method.

        Separation:
            - ScenarioLocatorFeatureResolver.resolve_features: Kept separate because resolve is the full pipeline while
            resolve_features is just the discovery stage.

        Main consumers:
            - pytest_bdd.collector: The primary consumer — calls resolve() to get scenarios for test collection.
            - ScenarioLocatorFilterMixin: Provides the default implementation of this method.

        State and side effects:
            None. Protocol definition. Implementation may modify Run model and perform I/O.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


class ScenarioLocatorHookProtocol(Protocol):
    """
    Defines the Protocol for pytest hook implementations that customize scenario location behavior: pytest_bdd_get_mimety.

    Responsibility:
        Defines the Protocol for pytest hook implementations that customize scenario location behavior:
        pytest_bdd_get_mimetype(config, path) determines the media type (Mimetype) for a given feature file path (used
        for parser selection), and pytest_bdd_get_parser(config, mimetype) selects the appropriate parser class for a
        given media type. This protocol enables plugins (e.g., struct_bdd) to register custom mimetypes and parsers
        without modifying the core locator logic.

    Reason for existence:
        The scenario location system needs to support pluggable file formats (Gherkin plaintext, Gherkin markdown,
        struct-BDD YAML/JSON/HOCON/TOML). This protocol defines the hook interface that plugins implement to tell the
        locator system "this file type uses this media type" and "this media type uses this parser." Without this
        protocol, the locator would need to hardcode all supported formats, making it impossible to add new formats via
        plugins.

    Delegates:
        - Config: Pytest configuration for accessing plugin options during mimetype/parser resolution.
        - Path: The file path being resolved — used by mimetype detection to check file extension or content.
        - Mimetype: The media type returned by mimetype detection, used as input to parser selection.
        - ParserProtocol: The parser class returned by parser selection.

    Cohesion:
        Both hook methods serve format detection and parser dispatch. pytest_bdd_get_mimetype answers "what format is
        this file?" and pytest_bdd_get_parser answers "which parser can handle this format?" They are the two halves of
        the format resolution puzzle.

    Separation:
        - ScenarioLocatorResolver: Kept separate because this protocol defines customization hooks (how to detect
        format, how to select parser) while ScenarioLocatorResolver defines the resolution pipeline (how to use those
        results) — customization vs orchestration.
        - pytest_bdd.mimetype.Mimetype: Kept separate because Mimetype owns the media type enum values, while this
        protocol defines the hook signatures that use them — data vs interface.

    Main consumers:
        - FileScenarioLocator.resolve_features(): Calls config.hook.pytest_bdd_get_mimetype and pytest_bdd_get_parser
        (via cast to this protocol) for each feature file.
        - UrlScenarioLocator.resolve_features(): Uses the same hook calls for URL-based feature resolution.
        - Plugin entry points (conftest.py): Implement these hooks to register custom formats.

    State and side effects:
        None. Protocol definition. Hook implementations may read file contents or configuration.

    Invariants:
        - pytest_bdd_get_mimetype may return None (format not recognized) — callers must handle this gracefully.
        - pytest_bdd_get_parser may return None (no parser registered) — callers must handle this by skipping the feature.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def pytest_bdd_get_mimetype(self, *, config: Config, path: Path) -> Mimetype | str | Enum | None:
        """
        Define hook method contract for custom mimetype detection: given a pytest Config and a file Path, returns the media type (Mi.

        Responsibility:
            Hook method contract for custom mimetype detection: given a pytest Config and a file Path, returns the media
            type (Mimetype, str, Enum, or None if unrecognized). Plugin implementations determine the format by
            inspecting file extension, content, or any other heuristic. The result is used to select the appropriate
            parser for the feature file.

        Reason for existence:
            Gherkin files come in multiple flavors (plain .feature, markdown .feature.md), struct-BDD files come in
            multiple data formats (.bdd with YAML/JSON/HOCON/TOML content), and new formats may be added by plugins.
            This hook allows format detection to be extended without modifying core locator code. The return type union
            (Mimetype | str | Enum | None) balances strict typing (Mimetype) with flexibility (str for ad-hoc types,
            Enum for plugin enums, None for unknown).

        Delegates:
            - config: Pytest configuration for accessing plugin options.
            - path: The file path to analyze for format detection.

        Cohesion:
            Single responsibility: determine the media type of a file. All parameters serve this purpose.

        Separation:
            - pytest_bdd_get_parser: Kept separate because get_mimetype detects the format while get_parser selects the
            parser for that format — detection vs dispatch.

        Main consumers:
            - FileScenarioLocator.resolve_features(): Calls this hook for each feature file to determine its media type.
            - UrlScenarioLocator.resolve_features(): Uses the same hook for URL-resolved features.

        State and side effects:
            None. Protocol definition. Implementations may read file contents.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...

    def pytest_bdd_get_parser(
        self,
        *,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        """
        Define hook method contract for parser selection: given pytest configuration and a media type (Mimetype), returns the parser.

        Responsibility:
            Hook method contract for parser selection: given pytest configuration and a media type (Mimetype), returns
            the parser class that can parse feature files of that type, or None if no parser is registered. Plugin
            implementations map media types to parser classes (e.g., Mimetype.gherkin_plain → GherkinParser,
            Mimetype.struct_bdd_yaml → StructBddYamlParser). The returned parser class is instantiated by the locator to
            parse feature files.

        Reason for existence:
            Parser registration is plugin-driven — each format plugin (gherkin, struct_bdd, etc.) registers its parser
            via this hook. The locator has zero built-in knowledge of which parser handles which format. This enables
            new format plugins to be added without modifying the core locator, following the open-closed principle. The
            return type (ParserProtocol) ensures any returned parser class satisfies the parsing contract.

        Delegates:
            - config: Pytest configuration for accessing plugin-registered parsers.
            - mimetype: The media type for which to find a parser.

        Cohesion:
            Single responsibility: map media type → parser class. All parameters serve this mapping.

        Separation:
            - pytest_bdd_get_mimetype: Kept separate because get_mimetype detects the format while get_parser selects
            the parser — format detection vs parser dispatch.

        Main consumers:
            - FileScenarioLocator.resolve_features(): Calls this hook after determining the mimetype to get the parser.
            - UrlScenarioLocator.resolve_features(): Same pattern for URL-based resolution.

        State and side effects:
            None. Protocol definition.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


ScenarioLocatorFilterT: TypeAlias = Callable[[Config | HasPytestStash, GherkinDocument, Pickle], bool]


@define
class ScenarioLocatorFilterMixin(ScenarioLocatorFeatureResolver, ScenarioLocatorResolver):
    """
    Provides the reusable scenario resolution pipeline implementation shared by all concrete locators (FileScenarioLocato.

    Responsibility:
        Provides the reusable scenario resolution pipeline implementation shared by all concrete locators
        (FileScenarioLocator, UrlScenarioLocator): resolve() orchestrates the pipeline that calls
        self.resolve_features() (abstract, implemented by subclasses) for feature discovery, _bind_feature() for
        creating FeatureRuntimeBinding objects with pickle compilation, filter_scenarios() for applying optional user-
        provided filters, and notifies an optional ScenarioLocatorReadObserver at three stages (on_source_loaded,
        on_feature_loaded, on_pickle_loaded). Also owns the _bind_feature static method that creates bindings by
        accessing Run.from_stash() and ensuring pickles are compiled via IdGenerator.from_stash().

    Reason for existence:
        Without this mixin, every concrete locator would need to reimplement the pipeline: resolve features → bind to
        Run model → notify observer → filter scenarios → yield results. This mixin provides that implementation once,
        with resolve_features() left abstract for subclasses. The filter_ attribute (optional ScenarioLocatorFilterT)
        enables user-provided filtering of which scenarios to include, applied in filter_scenarios(). The observer
        notification pattern supports batch parsers and progress reporters without coupling locators to specific
        observer implementations.

    Delegates:
        - Run.from_stash(config.stash): Retrieves the Run model for feature binding.
        - binding.ensure_pickles(IdGenerator.from_stash(config.stash)): Compiles pickles from the GherkinDocument.
        - IdGenerator.from_stash(config.stash): Provides unique ID generation for pickles.
        - ScenarioLocatorReadObserver: Optional observer receiving loading callbacks.

    Cohesion:
        Every method in this mixin serves the resolution pipeline: resolve_features discovers, _bind_feature creates
        bindings, filter_scenarios applies filters, resolve orchestrates. The filter_ attribute enables scenario-level
        filtering orthogonal to feature-level discovery.

    Separation:
        - FileScenarioLocator: Kept separate because FileScenarioLocator extends this mixin with file-system-specific
        feature resolution, while the mixin provides the pipeline logic — specialization vs infrastructure.
        - UrlScenarioLocator: Kept separate because UrlScenarioLocator extends this mixin with URL-specific feature resolution.

    Main consumers:
        - FileScenarioLocator: Inherits resolve() and extends with resolve_features() for file-based discovery.
        - UrlScenarioLocator: Inherits resolve() and extends with resolve_features() for URL-based discovery.

    State and side effects:
        filter_ attribute (optional callable) — stateless by default. resolve() creates FeatureRuntimeBinding objects
        (mutating Run model via Run.from_stash) and compiles pickles (mutating binding state). Observer callbacks may
        have side effects depending on implementation.

    Invariants:
        - filter_scenarios() must pass all pickles through when filter_ is None.
        - _bind_feature must create bindings for every parsed feature — no feature should be silently skipped.
        - Observer callbacks must be called in the canonical order: on_source_loaded → on_feature_loaded → (for each
        pickle) on_pickle_loaded.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    filter_: ScenarioLocatorFilterT | None = field(default=None, kw_only=True)

    def filter_scenarios(
        self,
        gherkin_document: GherkinDocument,
        pickles: Iterable[Pickle],
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[GherkinDocument, Pickle]]:
        """
        Filter an iterable of pickles through an optional user-provided filter function: if self.filter_ is set, each pickle.

        Responsibility:
            Filters an iterable of pickles through an optional user-provided filter function: if self.filter_ is set,
            each pickle is tested via self.filter_(config, gherkin_document, pickle) and only matching pickles are
            yielded with their parent document. If self.filter_ is None, all pickles are passed through unfiltered. This
            enables user-controlled scenario selection (e.g., by tag, by name, by custom logic) during the resolution
            pipeline.

        Reason for existence:
            The scenarios() function and plugin configuration allow users to specify scenario filters (e.g., "only run
            @smoke scenarios"). This method applies those filters during the resolution pipeline, after features are
            parsed and bound but before scenarios are yielded to the collector. The filter receives config (for option
            access), the GherkinDocument (for feature-level context like feature tags), and the Pickle (for scenario-
            level context like pickle tags and name).

        Delegates:
            - self.filter_: Optional callable implementing the filter predicate.
            - GherkinDocument + Pickle: The context objects passed to the filter for decision-making.

        Cohesion:
            The method performs one filtering operation: test each pickle → yield if passes filter or if no filter is
            set. The generator expression is a clean implementation of filter-then-yield.

        Separation:
            - resolve: Kept separate because resolve orchestrates the full pipeline (features → binding → observer →
            filter → yield), while filter_scenarios handles only the filtering stage.
            - _bind_feature: Kept separate because _bind_feature creates model bindings while filter_scenarios selects
            which scenarios to include — creation vs selection.

        Main consumers:
            - self.resolve(): Called within the resolution loop to filter pickles after observer notification.

        State and side effects:
            None beyond accessing self.filter_ (read-only). The generator expression has no persistent state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return (
            (gherkin_document, pickle)
            for pickle in pickles
            if self.filter_ is None or self.filter_(config, gherkin_document, pickle)
        )

    @staticmethod
    def _bind_feature(
        parsed: ParsedFeature,
        source: Source,
        config: Config | HasPytestStash,
    ) -> FeatureRuntimeBinding:
        """
        Provide static method that creates a FeatureRuntimeBinding for a parsed feature by: (1) retrieving the Run model from config.

        Responsibility:
            Static method that creates a FeatureRuntimeBinding for a parsed feature by: (1) retrieving the Run model
            from config.stash via Run.from_stash(), (2) calling run.ensure_feature_binding() with the parsed
            GherkinDocument, source metadata, and filename to create or retrieve a binding, (3) compiling pickles from
            the binding's GherkinDocument via binding.ensure_pickles() using an IdGenerator from config.stash. Returns
            the fully bound feature with compiled pickles ready for scenario filtering.

        Reason for existence:
            Feature binding is a common operation across all locator types — every locator needs to register parsed
            features with the Run model and compile their pickles. This static method encapsulates that logic, avoiding
            duplication between FileScenarioLocator and UrlScenarioLocator. The binding process is idempotent: if a
            binding already exists for the given GherkinDocument, ensure_feature_binding returns the existing one rather
            than creating a duplicate.

        Delegates:
            - Run.from_stash(config.stash): Retrieves the singleton Run model for the test session.
            - run.ensure_feature_binding(gherkin_document, source, filename): Creates or retrieves a FeatureRuntimeBinding.
            - binding.ensure_pickles(IdGenerator.from_stash(config.stash)): Compiles executable Pickle objects from the
            GherkinDocument's scenarios.
            - IdGenerator.from_stash(config.stash): Provides unique IDs for compiled pickles.

        Cohesion:
            The method performs a single pipeline: run.ensure_feature_binding → binding.ensure_pickles → return binding.
            Every line serves this binding creation process.

        Separation:
            - resolve: Kept separate because resolve orchestrates the full pipeline while _bind_feature handles the
            binding stage — orchestrator vs stage implementation.
            - filter_scenarios: Kept separate because filter_scenarios selects which scenarios to yield, while
            _bind_feature creates the model objects being filtered — creation vs selection.

        Main consumers:
            - self.resolve(): Called for each parsed feature during the resolution loop.

        State and side effects:
            Mutates the Run model (adding feature bindings) and FeatureRuntimeBinding state (compiling pickles). These
            are intentional side effects that populate the runtime model for scenario execution.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        run = Run.from_stash(config.stash)
        binding = run.ensure_feature_binding(
            gherkin_document=parsed.gherkin_document,
            source=source,
            filename=parsed.filename,
        )
        binding.ensure_pickles(id_generator=IdGenerator.from_stash(config.stash))
        return binding

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
        """
        Implement the ScenarioLocatorResolver.resolve() contract: orchestrates the complete scenario resolution pipeline by .

        Responsibility:
            Implements the ScenarioLocatorResolver.resolve() contract: orchestrates the complete scenario resolution
            pipeline by iterating over resolved features (from self.resolve_features()), binding each feature to the Run
            model (via _bind_feature), notifying the observer at three stages (on_source_loaded with document+source,
            on_feature_loaded with document-only, on_pickle_loaded for each matched pickle), filtering scenarios through
            self.filter_scenarios(), and yielding (GherkinDocument, Pickle, Source) triples for each matched scenario.
            This is the canonical pipeline that all concrete locators use.

        Reason for existence:
            This method is the "main loop" of scenario resolution. Without it, every locator would need to replicate the
            feature-binding-observer-filtering-yield sequence. The pipeline is carefully ordered: features must be bound
            (creating pickles) before pickles can be filtered; observer callbacks must happen before filtering so
            observers see all scenarios, not just filtered ones. The for loop with nested for loop (features → pickles)
            is the natural iteration pattern for hierarchical data (features contain scenarios).

        Delegates:
            - self.resolve_features(config): Abstract — implemented by subclasses for feature discovery.
            - self._bind_feature(parsed, source, config): Creates FeatureRuntimeBinding with compiled pickles.
            - observer.on_source_loaded / on_feature_loaded / on_pickle_loaded: Optional observer callbacks.
            - self.filter_scenarios(gherkin_document, binding.pickles, config): Applies user filters.
            - Yield: Returns (GherkinDocument, Pickle, Source) triples to the caller (collector).

        Cohesion:
            The method is a clean pipeline: for each feature → bind → notify → for each filtered pickle → notify →
            yield. Every line serves this pipeline orchestration.

        Separation:
            - resolve_features: Kept separate because resolve_features is abstract (feature discovery), while resolve is
            concrete (pipeline orchestration) — strategy vs template method pattern.
            - filter_scenarios: Kept separate because filter_scenarios is a reusable filtering component, while resolve
            is the orchestrator that calls it.

        Main consumers:
            - pytest_bdd.collector: Calls resolve() to discover scenarios for test collection.
            - pytest_bdd.scenario.scenarios(): Calls resolve() to dynamically load scenarios at runtime.
            - FileScenarioLocator and UrlScenarioLocator: Inherit this method.

        State and side effects:
            Calls _bind_feature which mutates Run model. Observer callbacks may have side effects (caching, progress
            reporting). The generator yields results without accumulating them in memory (memory-efficient for large
            feature sets).

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        for parsed, feature_source in self.resolve_features(config):
            binding = self._bind_feature(parsed, feature_source, config)
            if observer is not None:
                observer.on_source_loaded(parsed.gherkin_document, feature_source)
                observer.on_feature_loaded(parsed.gherkin_document)
            for _, pickle in self.filter_scenarios(parsed.gherkin_document, binding.pickles, config):
                if observer is not None:
                    observer.on_pickle_loaded(parsed.gherkin_document, pickle)
                yield parsed.gherkin_document, pickle, feature_source
