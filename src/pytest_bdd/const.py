"""
Owns all project-wide string constants (TAG_PREFIX), compiled regexes (PYTHON_REPLACE_REGEX, ALPHA_REGEX), and StrEnu.

Responsibility:
    Owns all project-wide string constants (TAG_PREFIX), compiled regexes (PYTHON_REPLACE_REGEX, ALPHA_REGEX), and
    StrEnum-based configuration parameter definitions (PytestConfigParam) and step definition option enums (Steps,
    Steps.Ini, Steps.Cli). This module is the single canonical source of truth for magic strings and config keys used
    across the entire plugin, ensuring no string duplication between parser, collector, locator, and runtime layers.

Reason for existence:
    Centralizes cross-cutting constants that are referenced by at least four architectural layers (foundation, parsing,
    collection, runtime). Without this module, magic strings like "@" prefix, liberal_steps option names, and
    continue_on_collection_errors would be duplicated across plugin modules, making option-renaming and refactoring
    unsafe. The regexes for Python identifier sanitization are co-located because they are the only computation
    performed on the constants and share the same consumer audience — step name generation and scenario ID construction.
    This module is placed in the foundation layer (layer 0) so it can be imported by every higher layer without creating
    cycles.

Delegates:
    - pytest_bdd.compatibility.enum.StrEnum: Provides the mixin base class for all StrEnum definitions in this module,
    abstracting away Python-version-specific enum implementation details.

Cohesion:
    All members are strongly cohesive as they all answer the question "what is the fixed vocabulary of this plugin?" The
    regexes are the only executable logic and they are directly derived from the constants (sanitizing Python
    identifiers derived from Gherkin names). The StrEnum hierarchy is nested organically: Steps is a namespace for Ini
    and Cli, which are option groups on the same logical concept (step definition configuration). No member would make
    more sense in any other module.

Separation:
    - pytest_bdd.mimetype.Mimetype: Kept separate because Mimetype enumerates IANA-style media type strings
    (text/x.cucumber.gherkin+plain) while const.py enumerates pytest CLI/INI option keys — the two serve completely
    different consumers (MIME negotiation vs pytest configuration) and evolve at different rates.
    - pytest_bdd.types: Kept separate because types.py owns Python-level type aliases and protocols, whereas const.py
    owns literal string values; mixing them would couple type-checking infrastructure to configuration default changes.

Main consumers:
    - pytest_bdd.collector_batch (as pytest_bdd.collector_batch import): Uses
    PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS to gate error-suppression behavior during feature file parsing.
    - pytest_bdd.scenario_locator.file_locator (as pytest_bdd.scenario_locator.file_locator import): Uses
    PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS for the same error-suppression gate in file-based feature
    resolution.
    - pytest_bdd.scenario_locator.url_locator (as pytest_bdd.scenario_locator.url_locator import): Uses
    PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS for error-suppression during URL-based feature resolution.
    - pytest_bdd.steps (as pytest_bdd.steps import): Uses Steps.Ini.LIBERAL_OPTION and Steps.Cli.LIBERAL_OPTION to check
    liberal_steps configuration for step matching tolerance.
    - pytest_bdd.scenario (as pytest_bdd.scenario import): Uses TAG_PREFIX, PYTHON_REPLACE_REGEX, and ALPHA_REGEX for
    scenario name sanitization and tag prefix normalization.

State and side effects:
    None, keeps no persistent state. All values are module-level immutable strings, compiled regex patterns, and StrEnum
    members. No file I/O, no pytest stash access, no network calls.

Invariants:
    - TAG_PREFIX must remain "@" — the Gherkin specification defines tag syntax with this prefix; changing it would
    break all tag-based filtering throughout the plugin.
    - PytestConfigParam members must be valid pytest option names that can be passed to config.getoption() — they are
    the bridge between pytest's configuration system and the plugin's internal logic.
    - Steps.Ini.LIBERAL_OPTION and Steps.Cli.LIBERAL_OPTION must have identical string values ("liberal_steps") since
    they represent the same configuration knob accessed through different pytest configuration channels (ini file vs CLI
    flag).

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

import re

from pytest_bdd.compatibility.enum import StrEnum

TAG_PREFIX = "@"

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


class PytestConfigParam(StrEnum):
    """
    Owns the canonical enumeration of all pytest-bdd-specific option names that are passed through pytest's config.getopt.

    Responsibility:
        Owns the canonical enumeration of all pytest-bdd-specific option names that are passed through pytest's
        config.getoption() mechanism. This class defines the single CONTINUE_ON_COLLECTION_ERRORS option which controls
        whether the plugin suppresses or re-raises FeatureParseError during collection, making this the authoritative
        lookup for any plugin code that needs to inspect pytest runtime configuration about error handling policy.

    Reason for existence:
        Extracting option name strings into a StrEnum prevents silent breakage when option names change — static
        analysis tools and grep can find all usages of PytestConfigParam members, whereas bare strings like
        "continue_on_collection_errors" scattered across multiple files are invisible to refactoring. Placing this in
        const.py alongside other string constants follows the foundation-layer pattern of co-locating all fixed
        vocabulary. The enum lives at module level rather than inside a private class because it is consumed by the
        parsing layer (collector_batch), collection layer (scenario_locator file_locator and url_locator), and
        potentially runtime layers, all of which need access without importing model internals.

    Delegates:
        - StrEnum (from pytest_bdd.compatibility.enum): Provides the string-compatible enum base class that allows
        direct comparison with raw strings (e.g.,
        config.getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS))).

    Cohesion:
        Currently contains only one member, but its cohesion score reflects the design pattern rather than current
        content: all pytest-bdd-specific option keys belong here as they are discovered. Adding a new option (e.g.,
        "strict_gherkin") would naturally extend this enum without touching any other entity. The single-responsibility
        focus on "pytest option names" makes it cohesive despite the small member count.

    Separation:
        - Steps.Ini and Steps.Cli: Kept separate because those enums own step-definition-specific option vocabulary
        (liberal_steps) while PytestConfigParam owns general plugin-wide options (continue_on_collection_errors).
        Consumers of step configuration should not have to import general plugin constants and vice versa.
        - pytest_bdd.mimetype.Mimetype: Kept separate because Mimetype owns IANA media type identifiers for content
        negotiation, while PytestConfigParam owns pytest option keys — completely different domains with different
        stability guarantees and consumers.

    Main consumers:
        - pytest_bdd.collector_batch.FeatureBatchParser.parse_worker: Casts config to
        getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)) to determine whether to suppress or re-raise
        parse errors during batch collection.
        - pytest_bdd.scenario_locator.file_locator.FileScenarioLocator.resolve_features: Uses the same pattern to gate
        error behavior during file-based feature resolution.
        - pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_temp_feature: Uses the same pattern for
        error-suppression during URL-based feature resolution.

    State and side effects:
        None, keeps no persistent state. This is a pure enumeration with no methods, no mutable data, and no I/O.

    Invariants:
        - Every member value must be a valid pytest option name accessible through config.getoption() — strings that
        don't correspond to registered pytest options would cause runtime failures.
        - Member names should use SCREAMING_SNAKE_CASE matching the pytest configuration option naming convention to
        maintain consistency across the plugin.
        - No member should duplicate a key already owned by Steps.Ini or Steps.Cli — each option has exactly one canonical home.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=3
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    CONTINUE_ON_COLLECTION_ERRORS = "continue_on_collection_errors"


class Steps:
    """
    Acts as a namespace container for two StrEnum subclasses (Ini and Cli) that enumerate the canonical option name strin.

    Responsibility:
        Acts as a namespace container for two StrEnum subclasses (Ini and Cli) that enumerate the canonical option name
        strings for step-definition-related pytest configuration. The nested Ini class owns the pytest ini-file option
        name "liberal_steps", while the nested Cli class owns the corresponding CLI flag name "liberal_steps", providing
        a single import point for all step configuration vocabulary without exposing implementation details about how
        pytest separates ini options from CLI options.

    Reason for existence:
        This class exists as a grouping mechanism rather than having behavioral methods, following the pattern
        established by pytest-bdd's Gherkin-oriented naming conventions. Without this namespace, Ini and Cli would be
        top-level StrEnum classes cluttering the module namespace. The name "Steps" mirrors the higher-level concept of
        "step definition configuration" that appears in both ini files (pytest.ini [tool:pytest_bdd.steps]) and CLI
        flags (--steps-liberal). Co-locating ini and CLI option enums under one namespace makes it obvious that they
        represent the same logical configuration dimension accessed through different pytest channels.

    Delegates:
        - Steps.Ini (StrEnum): Owns the canonical ini-file option name for liberal step matching, consumed by pytest's
        ini-file configuration reader.
        - Steps.Cli (StrEnum): Owns the canonical CLI option name for the same liberal step matching flag, consumed by
        pytest's addoption hook.

    Cohesion:
        The nested structure directly mirrors pytest's dual configuration system (ini files and CLI flags) for a single
        logical option. Both Ini and Cli represent the same configuration knob; they are nested under Steps because they
        are the "step configuration" family of options. If additional step-related options are added (e.g.,
        "strict_mode"), they would naturally become new members of both Ini and Cli, confirming the namespace design.

    Separation:
        - PytestConfigParam: Kept separate because PytestConfigParam owns general plugin-wide options
        (continue_on_collection_errors) while Steps owns step-definition-specific options — conflating them would mean
        step-definition consumers import general plugin configuration vocabulary and vice versa.
        - pytest_bdd.steps.manager.StepDefinitionManager: Kept separate because the manager implements the runtime
        behavior of step registration and matching, while Steps only declares the option name vocabulary — the manager
        reads the option values but does not own the option names.

    Main consumers:
        - pytest_bdd.steps (as pytest_bdd.steps import): Reads Steps.Ini.LIBERAL_OPTION and Steps.Cli.LIBERAL_OPTION to
        check whether liberal step matching is enabled in the current pytest configuration.

    State and side effects:
        None, keeps no persistent state. This is a pure namespace class with no methods, no instance data, and no I/O.

    Invariants:
        - Steps.Ini.LIBERAL_OPTION and Steps.Cli.LIBERAL_OPTION must have identical string values because they represent
        the same option accessed through different pytest configuration channels.
        - The class must never be instantiated — it exists solely as a namespace for its nested StrEnum classes.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    class Ini(StrEnum):
        """
        Owns the canonical enumeration of pytest-bdd step-definition-related INI-file option names.

        Responsibility:
            Owns the canonical enumeration of pytest-bdd step-definition-related INI-file option names. Currently
            defines a single member LIBERAL_OPTION with the string value "liberal_steps", which is the pytest ini option
            name used to enable tolerant/liberal step matching mode. This is the authoritative source of truth for all
            pytest-bdd INI configuration key names related to step definitions, ensuring that the string "liberal_steps"
            is never duplicated across the codebase.

        Reason for existence:
            Extracting INI option names into a StrEnum prevents typo-driven bugs when configuration keys are referenced
            across multiple modules (steps module, plugin registration, documentation). Without this, the string
            "liberal_steps" would appear in at least three places: the pytest_addoption hook in conftest, the step
            matching logic in steps.py, and the configuration documentation. A rename would require finding all three
            occurrences. With the enum, static analysis tools flag all consumers, and the compiler catches misspellings.
            Nesting under Steps follows the organizational pattern that groups ini and CLI option enums together.

        Delegates:
            - StrEnum (from pytest_bdd.compatibility.enum): Provides the string-compatible base class that allows the
            enum member to be used wherever a plain string is expected (e.g., in pytest's ini option registration).

        Cohesion:
            All members share the same purpose: declaring pytest INI-file option names for step definition
            configuration. Even though only one member exists currently, the design anticipates additional configuration
            options (strict mode, default parser, etc.) that would all be added here. No member would logically belong
            in a different enum.

        Separation:
            - Steps.Cli: Kept separate because CLI option names may differ from INI option names in format (CLI flags
            use hyphens, INI uses underscores), and pytest registers them through different hooks (pytest_addoption vs
            pytest_configure). While they currently share the same value, the separation preserves the ability for them
            to diverge.
            - PytestConfigParam: Kept separate because PytestConfigParam owns general plugin option names, not step-
            specific ones — consumers of step configuration should not depend on the general plugin option vocabulary.

        Main consumers:
            - pytest_bdd.steps: Reads Steps.Ini.LIBERAL_OPTION when checking whether liberal step matching is enabled
            via pytest ini configuration.
            - Plugin registration entry points: References this enum when registering pytest ini options via
            pytest_addoption or conftest hooks.

        State and side effects:
            None, keeps no persistent state. Pure enumeration with no methods.

        Invariants:
            - Member values must be valid pytest INI option names that pytest can parse from [tool:pytest_bdd.steps]
            sections in pyproject.toml or pytest.ini.
            - Member names should use SCREAMING_SNAKE_CASE for consistency with the rest of the codebase.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

        LIBERAL_OPTION = "liberal_steps"

    class Cli(StrEnum):
        """
        Owns the canonical enumeration of pytest-bdd step-definition-related CLI option names.

        Responsibility:
            Owns the canonical enumeration of pytest-bdd step-definition-related CLI option names. Currently defines a
            single member LIBERAL_OPTION with the string value "liberal_steps", which is the CLI flag name used to
            enable tolerant/liberal step matching mode at the command line. This is the authoritative source of truth
            for the CLI argument string, preventing duplication across plugin registration code and step matching logic.

        Reason for existence:
            Mirrors Steps.Ini as the CLI-side counterpart for the same logical configuration dimension. pytest
            distinguishes between INI-file options and CLI options as separate registration mechanisms, so the plugin
            must maintain separate enums for each channel. Without this enum, the string "liberal_steps" would be
            hardcoded in the pytest_addoption hook handler, the step matching logic, and configuration documentation.
            Centralizing it here ensures that renaming the CLI flag requires only one edit. Nesting under Steps makes
            the relationship between Ini and Cli explicit.

        Delegates:
            - StrEnum (from pytest_bdd.compatibility.enum): Provides the string-compatible base class that allows the
            enum member to be used in pytest's addoption registration as if it were a plain string.

        Cohesion:
            All members represent CLI option names for step definition configuration. Although only one member exists,
            the pattern anticipates future additions (e.g., "--steps-strict", "--steps-parser") that would naturally
            extend this enum. Every member answers the question "what CLI flags does pytest-bdd's step definition
            subsystem expose?"

        Separation:
            - Steps.Ini: Kept separate because pytest's INI and CLI option registration APIs are different, and the two
            option formats may diverge in the future (e.g., CLI uses "--liberal-steps" while INI uses "liberal_steps").
            - PytestConfigParam: Kept separate because PytestConfigParam owns general plugin options, while Cli owns
            step-definition-specific CLI flags — importing one should not bring the other's vocabulary into scope.

        Main consumers:
            - Plugin registration entry points (conftest, pytest_addoption hooks): References Steps.Cli.LIBERAL_OPTION
            when registering the --liberal-steps CLI flag with pytest.
            - pytest_bdd.steps: Reads the value to check whether liberal step matching is enabled via command-line override.

        State and side effects:
            None, keeps no persistent state. Pure enumeration with no methods.

        Invariants:
            - Member values must be valid pytest CLI option strings that can be registered via pytest_addoption without
            causing argparse conflicts.
            - The value should match the corresponding Steps.Ini member value to maintain the invariant that the same
            logical option is accessible through both channels.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

        LIBERAL_OPTION = "liberal_steps"
