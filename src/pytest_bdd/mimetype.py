"""
Owns the canonical StrEnum catalog of all MIME types (Mimetype) and file suffixes (Suffix) used throughout pytest-bdd.

Responsibility:
    Owns the canonical StrEnum catalog of all MIME types (Mimetype) and file suffixes (Suffix) used throughout pytest-
    bdd for content-type negotiation, feature file detection, and parser dispatch. Additionally maintains the cross-
    reference tables (gherkin_suffixes, struct_bdd_suffixes, link_suffixes, mimetype_suffix_pairs) and registers all
    mimetype-to-suffix mappings with Python's standard library mimetypes module so that file-type detection works
    correctly for Gherkin (.gherkin, .feature) and struct-BDD (.bdd) files.

Reason for existence:
    This module is the single source of truth for all media type identification in the plugin. Without it, mimetype
    strings like "text/x.cucumber.gherkin+plain" and suffix strings like ".gherkin" would be duplicated across at least
    four layers: the parser layer (choosing GherkinParser vs MarkdownGherkinParser), the scenario locator layer
    (detecting feature files on disk), the struct_bdd plugin (handling YAML/JSON/HOCON/TOML BDD files), and URL-based
    feature loading (content-type negotiation). The mimetypes.add_type() calls in this module are critical side effects
    that configure Python's standard mimetypes.guess_type() to recognize pytest-bdd's custom file extensions — without
    these, file-type detection would fail silently.

Delegates:
    - mimetypes (stdlib): Registers the custom mimetype-to-suffix mappings so that Python's standard file type detection
    can identify pytest-bdd feature files.
    - pytest_bdd.compatibility.enum.StrEnum: Provides the string-compatible enum base class for both Mimetype and Suffix
    enumerations.

Cohesion:
    All members are strongly cohesive because they all answer the question "what file types does pytest-bdd work with?"
    The Mimetype enum maps human-readable type identifiers, the Suffix enum maps file extensions, and the cross-
    reference sets and lists define which suffixes belong to which semantic category (Gherkin, struct-BDD, link files).
    The mimetypes.add_type() loop at module bottom is a natural initialization step that uses the exact same data. No
    member is unrelated to file-type identification.

Separation:
    - pytest_bdd.const: Kept separate because const.py owns pytest-specific option name strings (CLI flags, INI keys)
    while mimetype.py owns IANA-style media type identifiers — these serve completely different consumers (pytest
    configuration vs file-type detection) and change at different rates (option names change with plugin API, MIME types
    are stable by specification).
    - pytest_bdd.parser: Kept separate because the parser module owns the parsing logic (how to parse a feature file
    given its content) while mimetype.py only owns the type identification (what type of file is this?) — the parser
    consumes mimetype information but does not own it.

Main consumers:
    - pytest_bdd.scenario_locator.file_locator.FileScenarioLocator.resolve_features: Uses Mimetype and the hook protocol
    to determine which parser class to instantiate for a given feature file based on its detected media type.
    - pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.resolve_features: Uses Mimetype to determine parser
    type from URL response content-type headers.
    - pytest_bdd.plugin.struct_bdd: Uses struct_bdd-specific Mimetype and Suffix values to detect and parse
    YAML/JSON/HOCON/TOML BDD feature files.
    - pytest_bdd.parser (GherkinParser, MarkdownGherkinParser): Uses Mimetype.gherkin_plain and
    Mimetype.gherkin_markdown to register parser classes for their respective media types.

State and side effects:
    Side effects at import time: calls mimetypes.add_type() for nine mimetype-suffix pairs, modifying Python's global
    mimetypes registry. This is intentional and necessary for stdlib file-type detection to recognize custom pytest-bdd
    file extensions. No mutable state after initialization; all enums and sets are immutable.

Invariants:
    - Every Mimetype member representing a Gherkin variant must have at least one corresponding Suffix member and a
    registration in mimetypes via the mimetype_suffix_pairs table, otherwise file-type detection would fail for that
    format.
    - The gherkin_suffixes set must include Suffix.gherkin and Suffix.feature since both ".gherkin" and ".feature" are
    valid Gherkin file extensions.
    - struct_bdd_suffixes must include Suffix.struct_bdd since ".bdd" files are the primary container format for struct-
    BDD documents.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

import mimetypes

from pytest_bdd.compatibility.enum import StrEnum


class Mimetype(StrEnum):
    """
    Owns the canonical enumeration of all IANA-style media type strings recognized by pytest-bdd for feature file format .

    Responsibility:
        Owns the canonical enumeration of all IANA-style media type strings recognized by pytest-bdd for feature file
        format identification. Defines three families: Gherkin variants (gherkin_plain for plaintext .feature,
        gherkin_markdown for .feature.md markdown), struct-BDD variants (yaml, hocon, json5, json, hjson, toml), and
        general-purpose types (python, markdown, yaml, hocon, toml, json, json5, hjson). This enum is the authoritative
        lookup for every plugin component that needs to answer "what format is this feature file in?"

    Reason for existence:
        Centralizing all media type strings into a single StrEnum prevents format-detection bugs caused by typo'd
        strings scattered across multiple modules. When a new format is added (e.g., struct_bdd_hocon), only this enum
        and its corresponding Suffix member need updating — all consumers that pattern-match on Mimetype values
        automatically pick up the new format. The StrEnum base allows these values to be used directly in comparisons
        and as dictionary keys without .value boilerplate, while still providing IDE autocompletion. Without this enum,
        format string matching would rely on bare strings like "text/x.cucumber.gherkin+plain" appearing in parser
        selection logic, scenario locator hooks, and struct-BDD plugin code — a typo in any of those locations would
        silently break format detection.

    Delegates:
        - StrEnum (from pytest_bdd.compatibility.enum): Provides the string-mixin base class that allows Mimetype
        members to participate in string comparisons and dictionary lookups without explicit .value access.

    Cohesion:
        Every member represents a media type that pytest-bdd can either produce, consume, or use for parser dispatch.
        The three families (Gherkin, struct-BDD, general-purpose) are all within the same domain of "file format
        identification for BDD testing." The general-purpose types (python, markdown, yaml, etc.) are included because
        they serve as default/fallback types or as basis formats for the struct-BDD variants. No member represents a
        non-format concept.

    Separation:
        - Suffix: Kept separate as a peer enum because suffixes and mimetypes answer different questions — "what is the
        file extension?" vs "what is the content format?" They are cross-referenced (via mimetype_suffix_pairs) but can
        evolve independently (e.g., a new suffix could map to an existing mimetype).
        - pytest_bdd.const: Kept separate because const.py owns pytest option name strings while Mimetype owns content-
        type identifiers — these are unrelated domains.

    Main consumers:
        - pytest_bdd.scenario_locator.file_locator.FileScenarioLocator.resolve_features: Uses Mimetype values to
        determine which parser class to instantiate when resolving feature files from disk.
        - pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.resolve_features: Uses Mimetype values from URL
        response content-type headers to determine parser dispatch.
        - pytest_bdd.plugin.struct_bdd: Uses struct-BDD-specific Mimetype members to register and dispatch struct-BDD parsers.
        - pytest_bdd.parser (GherkinParser, MarkdownGherkinParser): Associates themselves with specific Mimetype values
        during parser registration.

    State and side effects:
        None, keeps no persistent state. Pure enumeration with no methods.

    Invariants:
        - All member values must be syntactically valid IANA-style media type strings (type "/" subtype, with optional
        "+" structured suffix).
        - Every Gherkin variant member must have a corresponding entry in the mimetype_suffix_pairs list for proper
        file-type detection.
        - Member naming convention must use lowercase_with_underscores for consistency across the codebase.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    gherkin_plain = "text/x.cucumber.gherkin+plain"
    gherkin_markdown = "text/x.cucumber.gherkin+markdown"
    struct_bdd_yaml = "application/x.struct_bdd+yaml"
    struct_bdd_hocon = "application/x.struct_bdd+hocon"
    struct_bdd_json5 = "application/x.struct_bdd+json5"
    struct_bdd_json = "application/x.struct_bdd+json"
    struct_bdd_hjson = "application/x.struct_bdd+hjson"
    struct_bdd_toml = "application/x.struct_bdd+toml"

    python = "text/x-python"

    markdown = "text/markdown"
    yaml = "application/x-yaml"
    hocon = "application/x-hocon"
    toml = "text/toml"
    json = "application/json"
    json5 = "application/json5"
    hjson = "application/x-hjson"


class Suffix(StrEnum):
    """
    Owns the canonical enumeration of all file extensions recognized by pytest-bdd for feature file discovery, including .

    Responsibility:
        Owns the canonical enumeration of all file extensions recognized by pytest-bdd for feature file discovery,
        including Gherkin extensions (.gherkin, .feature), struct-BDD container extensions (.bdd), link/shortcut file
        extensions (.url, .desktop, .webloc), markdown (.md), and data format extensions (.yaml, .yml, .ndjson, .hocon,
        .toml, .hjson, .json5). This enum is the authoritative source of truth for every file extension that the
        scenario locator and file-type detection systems must recognize.

    Reason for existence:
        Centralizing file extension strings prevents discovery bugs where one module looks for ".feature" while another
        expects ".gherkin". When a new file format is added to the plugin, only this enum needs updating — the cross-
        reference sets (gherkin_suffixes, struct_bdd_suffixes, link_suffixes) and the mimetype_suffix_pairs table
        automatically propagate the change to all consumers. Without this enum, file extension strings would be
        duplicated across scenario locators, file globs, and parser selection logic, making format additions error-prone
        and requiring manual synchronization across multiple files.

    Delegates:
        - StrEnum (from pytest_bdd.compatibility.enum): Provides the string-mixin base class that allows Suffix members
        to be used directly in path suffixes, glob patterns, and set membership checks.

    Cohesion:
        Every member represents a file extension that pytest-bdd's feature discovery system may encounter. The members
        group naturally into categories: Gherkin extensions (.gherkin, .feature), struct-BDD container (.bdd), link
        files (.url, .desktop, .webloc), and data formats (.yaml, .yml, .ndjson, etc.). All members serve the same
        purpose: mapping file extensions to content types for parser dispatch.

    Separation:
        - Mimetype: Kept separate because suffixes and mimetypes answer different questions — "what is the file
        extension?" vs "what is the content format?" They form a many-to-one relationship (e.g., both .gherkin and
        .feature map to gherkin_plain mimetype) and evolve at different rates.
        - pytest_bdd.const: Kept separate because const.py owns pytest configuration option names, while Suffix owns
        file extension strings — completely different domains.

    Main consumers:
        - pytest_bdd.scenario_locator.file_locator.FileScenarioLocator._resolved_feature_paths: Uses suffix information
        indirectly through file glob patterns when discovering feature files on disk.
        - pytest_bdd.mimetype (module-level mimetype_suffix_pairs): The cross-reference list maps Suffix members to
        Mimetype members for registration with Python's stdlib mimetypes module.
        - pytest_bdd.plugin.struct_bdd: Uses struct_bdd_suffixes to detect .bdd files for struct-BDD processing.

    State and side effects:
        None, keeps no persistent state. Pure enumeration with no methods.

    Invariants:
        - Every Suffix member must start with a dot (".") following standard file extension convention.
        - The gherkin_suffixes set must include at least Suffix.gherkin and Suffix.feature for complete Gherkin file discovery.
        - Suffix members used in link_suffixes must correspond to actual operating system shortcut/link file formats
        recognized by the URL locator.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    gherkin = ".gherkin"
    feature = ".feature"
    struct_bdd = ".bdd"
    url = ".url"
    desktop = ".desktop"
    webloc = ".webloc"
    markdown = ".md"
    yaml = ".yaml"
    yml = ".yml"
    ndjson = ".ndjson"
    hocon = ".hocon"
    toml = ".toml"
    hjson = ".hjson"
    json5 = ".json5"


gherkin_suffixes = {Suffix.gherkin, Suffix.feature}
struct_bdd_suffixes = {Suffix.struct_bdd}
link_suffixes = {Suffix.url, Suffix.desktop, Suffix.webloc}

mimetype_suffix_pairs = [
    (Mimetype.gherkin_plain, Suffix.gherkin),
    (Mimetype.gherkin_plain, Suffix.feature),
    (Mimetype.markdown, Suffix.markdown),
    (Mimetype.yaml, Suffix.yaml),
    (Mimetype.yaml, Suffix.yml),
    (Mimetype.hocon, Suffix.hocon),
    (Mimetype.toml, Suffix.toml),
    (Mimetype.hjson, Suffix.hjson),
    (Mimetype.json5, Suffix.json5),
]

for mimetype, suffix in mimetype_suffix_pairs:
    mimetypes.add_type(str(mimetype), str(suffix))
