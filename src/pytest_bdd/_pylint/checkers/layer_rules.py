"""
Enforces the 8-layer directed acyclic graph (DAG) architecture defined in `docs/architecture/layers.toml`
by validati.

Responsibility:
    Enforces the 8-layer directed acyclic graph (DAG) architecture defined in `docs/architecture/layers.toml`
    by validating all Python imports in the pytest-bdd-ng codebase. Two rules are enforced: BLQ1301
    (downward-import) fires when a module imports from a layer with equal or higher order that is not in its
    `allowed_imports` list, preventing circular dependencies; BLQ1302 (horizontal-import) fires when a
    `pytest_bdd.plugin.*` module imports from a different plugin within the same layer (e.g., reporting
    plugin importing from another reporting plugin). Configured exceptions from `layers.toml` are honored.
    Only imports within the `pytest_bdd` namespace are checked; third-party and stdlib imports are ignored.

Reason for existence:
    This module is the programmatic enforcement mechanism for the architectural layer model documented in
    `LAYERS.md`. Without it, layer violations would only be caught during code review. The checker reads
    `layers.toml` at startup via `_LayerConfig`, constructing an in-memory lookup table that maps module
    prefixes to layer names, orders, and allowed imports. This TOML-driven approach means layer boundaries
    can be updated without modifying the checker code. The module is co-located with `_LayerConfig` because
    the config class is an implementation detail of the checker — no other module needs to parse layers.toml.
    The resolution logic (longest-prefix matching for module-to-layer mapping, exception matching with
    submodule support) is non-trivial and warrants dedicated encapsulation.

Delegates:
    - _LayerConfig: Parses `layers.toml`, builds the module-to-layer prefix map, and provides lookup
      methods (`layer_for_module`, `order_for_layer`, `allowed_imports_for_layer`, `is_exception`,
      `module_prefixes`).
    - tomllib/tomli: Parses the TOML configuration file (Python 3.11+ uses stdlib tomllib, older uses tomli).
    - self._check_node_imports: Entry point that resolves the current module's layer and dispatches each
      imported module to `_check_import`.
    - self._check_import: Performs the actual layer comparison (horizontal vs downward) and emits messages.
    - self._resolve_package: Resolves a module name to its nearest configured package prefix using
      longest-prefix matching.
    - self._resolve_imported_modules: Converts `Import` and `ImportFrom` AST nodes into absolute module
      name strings, handling relative imports.
    - self._is_pytest_bdd_module: Guards that only `pytest_bdd.*` modules are checked.

Cohesion:
    All logic in this module serves a single purpose: validating that imports respect the layer DAG. The
    `_LayerConfig` helper handles TOML parsing and lookup, while `LayerRulesChecker` handles AST traversal
    and rule enforcement. Internal methods form a clear pipeline: `visit_import`/`visit_importfrom` →
    `_check_node_imports` → `_check_import`, with `_resolve_package`, `_resolve_imported_modules`, and
    `_is_pytest_bdd_module` as supporting utilities. No method has a purpose outside layer enforcement.

Separation:
    - plugin_patterns.py: PluginPatternsChecker handles plugin structural rules (required files, stash
      access) and also checks cross-plugin imports, but at the plugin-name level, not the architectural
      layer level. LayerRulesChecker provides the formal DAG-based enforcement.
    - test_import_rules.py: TestImportRulesChecker validates test imports are under test paths; this module
      validates architectural layer boundaries for all imports.
    - quality_gates.py: QualityGatesChecker handles code patterns; this module handles import architecture.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `LayerRulesChecker` into Pylint during plugin startup.
    - Pylint's import visitors: Calls `visit_import` and `visit_importfrom` during AST traversal.
    - CI/CD via `make custom-rules`: Runs layer enforcement as part of the pre-commit/CI pipeline.

State and side effects:
    Holds a mutable `self._config: _LayerConfig | None` attribute populated during `__init__` by
    `_init_config()`. The config is loaded once by reading `docs/architecture/layers.toml` from disk
    (with fallback directory walking to find it). If parsing fails, `_config` is set to `None` and all
    checks are silently skipped. No other persistent state. `visit_import` and `visit_importfrom` call
    `self.add_message()` to emit diagnostics.

Invariants:
    - `_config` is `None` if `layers.toml` cannot be found or parsed; all checks are skipped in that case.
    - Module-to-layer resolution uses longest-prefix matching: if a module matches multiple configured
      prefixes, the longest (most specific) wins.
    - Exception matching supports submodules: if `(a, b)` is an exception, `(a.sub, b.sub)` also matches.
    - Same-package submodule imports (where `_resolve_package` returns the same prefix) are always allowed.
    - Horizontal import detection (BLQ1302) only fires for `pytest_bdd.plugin.*` modules importing from
      a different `pytest_bdd.plugin.*` module — same-plugin internal imports are allowed.
    - Only modules starting with `pytest_bdd` or exactly `pytest_bdd` are checked.

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

# init: allow
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from astroid import nodes
from pylint.checkers import BaseChecker

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]  # fallback for python < 3.11

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class _LayerConfig:
    """
    Parse the `docs/architecture/layers.toml` configuration file and provides an in-memory lookup API
    for the LayerRules.

    Responsibility:
        Parses the `docs/architecture/layers.toml` configuration file and provides an in-memory lookup API
        for the LayerRulesChecker. Builds three internal data structures: `_layers` (raw TOML layer
        definitions keyed by layer name), `_exceptions` (set of `(from_module, to_module)` exception
        tuples), and `_module_to_layer` (dict mapping module prefix strings to layer names, sorted by
        prefix length for longest-match resolution). Provides five query methods: `layer_for_module`
        (longest-prefix lookup), `order_for_layer`, `allowed_imports_for_layer`, `is_exception` (with
        submodule support), and `module_prefixes`.

    Reason for existence:
        This class exists to decouple TOML parsing and data access from the checker's AST-walking logic.
        Without it, `LayerRulesChecker` would need to embed TOML parsing, prefix-matching, and exception
        resolution inline, making the checker class bloated and hard to test. The `_LayerConfig` is a pure
        data-access object with no Pylint dependencies — it only knows about `layers.toml` structure and
        module name resolution. It uses longest-prefix matching (sorting prefixes by length descending)
        to handle the fact that `pytest_bdd.plugin.cucumber_json` should match `pytest_bdd.plugin.cucumber_json`
        before `pytest_bdd.plugin`. The prefix underscore marks it as an implementation detail.

    Delegates:
        - tomllib/tomli.loads: Parses the TOML content string into a Python dict.
        - Path.read_text: Reads the layers.toml file from disk (called by the constructor's caller).

    Cohesion:
        Every method in this class serves data access for layer enforcement. `__init__` parses and indexes,
        `layer_for_module` performs prefix matching, `order_for_layer` and `allowed_imports_for_layer`
        are simple dict lookups with casts, `is_exception` implements the submodule-aware exception
        matching, and `module_prefixes` exposes the raw prefix map. All methods operate on the same three
        instance attributes and share the same domain vocabulary (layers, orders, modules, exceptions).

    Separation:
        - LayerRulesChecker: The checker owns Pylint integration, AST traversal, and message emission;
          _LayerConfig owns TOML data access. The checker never touches TOML directly.
        - Individual checker modules: No other checker needs layer configuration data; _LayerConfig is
          specific to layer enforcement.

    Main consumers:
        - LayerRulesChecker.__init__: Instantiates `_LayerConfig` with the resolved layers.toml path.
        - LayerRulesChecker._check_import: Calls `layer_for_module`, `order_for_layer`,
          `allowed_imports_for_layer`, and `is_exception` for each import being validated.
        - LayerRulesChecker._resolve_package: Calls `module_prefixes` for package resolution.

    State and side effects:
        Holds immutable parsed data in `_layers`, `_exceptions`, and `_module_to_layer` after construction.
        All query methods are read-only. The class does no I/O after `__init__`. No mutation of external
        state.

    Invariants:
        - `_module_to_layer` is sorted by prefix length descending to ensure longest-match-first resolution.
        - `_exceptions` tuples support submodule matching: `(a, b)` also matches `(a.sub, b.sub)`.
        - `layer_for_module` returns `None` if no configured prefix matches.
        - `order_for_layer` and `allowed_imports_for_layer` assume the layer key exists; KeyError if not.

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

    def __init__(self, layers_toml_path: Path) -> None:
        """
        Initialize the layer configuration by reading and parsing a TOML file from the given path.

        Responsibility:
            Initializes the layer configuration by reading and parsing a TOML file from the given path.
            Extracts the `[layers]` table into `_layers`, builds the `_exceptions` set from the
            `[[exceptions]]` array of tables, and constructs the `_module_to_layer` prefix map by
            collecting all `modules` lists from each layer definition, sorting by prefix length descending
            for longest-match resolution in `layer_for_module`.

        Reason for existence:
            This constructor is the single point where `layers.toml` data enters the system. All downstream
            lookups depend on the data structures built here. The prefix sorting (longest first) is critical
            for correct module-to-layer resolution: `pytest_bdd.plugin.cucumber_json` must match before
            `pytest_bdd.plugin`. Without this initialization step, the `_LayerConfig` would have no data
            to serve.

        Delegates:
            - tomllib.loads: Parses the raw TOML text into Python dicts/lists.
            - Path.read_text: Reads the TOML file content from disk (encoding=utf-8).

        Cohesion:
            This method does three tightly related things: parse TOML, extract exceptions, build prefix map.
            All three serve the single goal of preparing the layer configuration for query use.

        Separation:
            - LayerRulesChecker._init_config: Locates the layers.toml file on disk and calls this
              constructor; it handles the "where is the file" concern while this method handles "parse it".

        Main consumers:
            - LayerRulesChecker._init_config: The sole instantiation site for `_LayerConfig`.

        State and side effects:
            Populates `_layers`, `_exceptions`, and `_module_to_layer` on the instance. Reads a file from
            disk via `layers_toml_path.read_text()`. No other side effects.

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
        raw = tomllib.loads(layers_toml_path.read_text(encoding="utf-8"))
        self._layers: dict[str, dict[str, object]] = raw["layers"]
        self._exceptions: set[tuple[str, str]] = set()
        for exc in raw.get("exceptions", []):
            self._exceptions.add((exc["from_module"], exc["to_module"]))
        self._module_to_layer: dict[str, str] = {}
        sorted_modules = sorted(
            ((m, name) for name, ldef in self._layers.items() for m in ldef["modules"]),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for mod_prefix, layer_name in sorted_modules:
            self._module_to_layer[mod_prefix] = layer_name

    def layer_for_module(self, module: str) -> str | None:
        """
        Resolve a dotted Python module name to its architectural layer name using longest-prefix
        matching against the `_modu.

        Responsibility:
            Resolves a dotted Python module name to its architectural layer name using longest-prefix
            matching against the `_module_to_layer` map. Returns the layer name (e.g., `"reporting"`,
            `"parsing"`) if the module matches or starts with a configured prefix followed by a dot;
            returns `None` if no configured prefix matches. The `_module_to_layer` dict is pre-sorted
            by prefix length descending, so the first match found is the most specific.

        Reason for existence:
            This method is the primary lookup in the entire layer enforcement system. Every import check
            depends on correctly resolving the current module and the imported module to their respective
            layers. Longest-prefix matching is essential because module paths are hierarchical
            (e.g., `pytest_bdd.plugin.cucumber_json` is more specific than `pytest_bdd.plugin`), and the
            most specific layer assignment must win.

        Delegates:
            - (none): Pure in-memory dict iteration; no further delegation.

        Cohesion:
            This method does exactly one thing: find the best-matching layer name for a module string.
            It has no side effects and no knowledge of what the layer name will be used for.

        Separation:
            - order_for_layer / allowed_imports_for_layer: These methods take a layer name (output of this
              method) and return layer metadata; they operate at a different abstraction level.
            - is_exception: Operates on module pairs, not single module resolution.

        Main consumers:
            - LayerRulesChecker._check_node_imports: Resolves the current module's layer.
            - LayerRulesChecker._check_import: Resolves the imported module's layer.

        State and side effects:
            None, read-only method. Iterates over `_module_to_layer` dict and returns a string or None.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        for prefix, layer_name in self._module_to_layer.items():
            if module == prefix or module.startswith(prefix + "."):
                return layer_name
        return None

    def order_for_layer(self, layer: str) -> int:
        """
        Return the numeric order (0-8) for a given layer name by looking up the `"order"` key in the
        layer's TOML definition.

        Responsibility:
            Returns the numeric order (0-8) for a given layer name by looking up the `"order"` key in the
            layer's TOML definition. The order determines the layer's position in the DAG: higher-order
            layers may import from lower-order layers, but not vice versa. Uses `typing.cast` to assert
            the TOML value is an int.

        Reason for existence:
            This method provides the ordering information needed for BLQ1301 downward-import detection.
            An import is "downward" (forbidden) if the imported layer's order is >= the current layer's
            order. Exists as a separate method rather than inline dict access to encapsulate the cast
            and to provide a clear, self-documenting API for the checker.

        Delegates:
            - (none): Direct dict lookup with a cast.

        Cohesion:
            This method does exactly one thing: return the order integer for a layer name. Pure accessor.

        Separation:
            - layer_for_module: Resolves module name → layer name; this resolves layer name → order.
              They operate at different resolution stages.

        Main consumers:
            - LayerRulesChecker._check_import: Compares current and imported layer orders.

        State and side effects:
            None, read-only method. Assumes the layer key exists; raises KeyError if not.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return cast("int", self._layers[layer]["order"])

    def allowed_imports_for_layer(self, layer: str) -> list[str]:
        """
        Return the list of layer names that a given layer is allowed to import from, as defined in
        the `allowed_imports` key.

        Responsibility:
            Returns the list of layer names that a given layer is allowed to import from, as defined in
            the `allowed_imports` key of the layer's TOML definition. For example, the `"collection"`
            layer (order 5) returns `["foundation", "utility", "parsing", "model", "step_definition"]`.
            Uses `typing.cast` to assert the TOML value is a list of strings.

        Reason for existence:
            This method provides the allowlist used in BLQ1301 enforcement. If an imported layer is NOT
            in this list and its order is >= the current layer's order, the import is a violation (unless
            covered by an exception). Exists as a separate accessor to keep the TOML structure knowledge
            encapsulated within `_LayerConfig`.

        Delegates:
            - (none): Direct dict lookup with a cast.

        Cohesion:
            Pure accessor method with a single responsibility: return the allowed imports list for a layer.

        Separation:
            - layer_for_module / order_for_layer: These methods resolve different aspects of layer metadata;
              this method resolves the import allowlist.

        Main consumers:
            - LayerRulesChecker._check_import: Checks if the imported layer is in the current layer's
              allowed imports list.

        State and side effects:
            None, read-only method. Assumes the layer key exists; raises KeyError if not.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return cast("list[str]", self._layers[layer]["allowed_imports"])

    def is_exception(self, from_module: str, to_module: str) -> bool:
        """
        Determine whether a specific import pair is covered by a configured exception in
        `layers.toml`.

        Responsibility:
            Determines whether a specific import pair is covered by a configured exception in
            `layers.toml`. Matches both exact module names and submodules: if `(a, b)` is an exception,
            then `(a.sub, b.sub)` also matches (using `startswith` with a dot suffix). Returns `True`
            if any exception tuple matches, `False` otherwise.

        Reason for existence:
            This method implements the exception mechanism that allows legitimate cross-layer imports
            (e.g., `pytest_bdd.model` importing from `pytest_bdd.parser` for pickle compilation) without
            triggering BLQ1301. The submodule matching (using `startswith(exc_from + ".")`) is important
            because exceptions are defined at the top-level module granularity but need to cover all
            submodules. This logic is centralized here rather than duplicated in the checker.

        Delegates:
            - (none): Iterates over `_exceptions` set and performs string comparisons.

        Cohesion:
            This method does exactly one thing: check if a module pair is in the exceptions set. The
            submodule matching logic is an integral part of that check.

        Separation:
            - _check_import: Calls this method as part of the violation decision; the checker doesn't
              know how exceptions are stored or matched.

        Main consumers:
            - LayerRulesChecker._check_import: Called before emitting BLQ1301 to check if the import
              is a known exception.

        State and side effects:
            None, read-only method. Iterates over `_exceptions` set. No mutations.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        for exc_from, exc_to in self._exceptions:
            if (from_module == exc_from or from_module.startswith(exc_from + ".")) and (
                to_module == exc_to or to_module.startswith(exc_to + ".")
            ):
                return True
        return False

    def module_prefixes(self) -> dict[str, str]:
        """
        Return the complete `_module_to_layer` dict mapping module prefix strings to layer names.

        Responsibility:
            Returns the complete `_module_to_layer` dict mapping module prefix strings to layer names.
            Used by `LayerRulesChecker._resolve_package` to determine the nearest configured package
            prefix for a given module name by iterating over all known prefixes and performing
            longest-prefix matching.

        Reason for existence:
            This method exposes the prefix map as a read-only view for package resolution. Without it,
            `_resolve_package` would need direct access to the private `_module_to_layer` attribute,
            breaking encapsulation. The method exists to provide controlled access to what is otherwise
            an internal data structure.

        Delegates:
            - (none): Returns a reference to the internal dict.

        Cohesion:
            Pure accessor. Returns the data needed for package resolution, which is a supporting concern
            of layer enforcement.

        Separation:
            - layer_for_module: Uses the prefix map for layer resolution; this method exposes it for
              package resolution, which is a different use case (finding the package boundary, not the
              layer assignment).

        Main consumers:
            - LayerRulesChecker._resolve_package: Iterates over the returned dict to find the best
              matching package prefix for a module.

        State and side effects:
            None, read-only. Returns a reference to internal state (the dict could theoretically be
            mutated by the caller, but the checker treats it as read-only).

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return self._module_to_layer


class LayerRulesChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that enforces the project's 8-layer architectural DAG by validating all
    `import` and `from .

    Responsibility:
        A Pylint `BaseChecker` that enforces the project's 8-layer architectural DAG by validating all
        `import` and `from ... import` statements against `docs/architecture/layers.toml`. It detects
        two violation types: BLQ1301 (downward-import) when a module imports from a layer with equal or
        higher order not in its `allowed_imports`, and BLQ1302 (horizontal-import) when a plugin module
        imports from a different plugin within the same layer. Configured exceptions and same-package
        submodule imports are allowed. The checker loads its configuration once during `__init__` via
        `_init_config()`, which locates `layers.toml` and delegates parsing to `_LayerConfig`.

    Reason for existence:
        This checker is the runtime enforcement of the architectural rules documented in `LAYERS.md`.
        The 8-layer DAG (foundation → utility → parsing → model → step_definition → collection →
        runtime → reporting → extra_plugins) prevents circular dependencies and maintains a strict
        import direction. Without automated enforcement, layer violations would accumulate unnoticed.
        The checker design separates concerns cleanly: `_LayerConfig` handles TOML parsing and data
        access, while `LayerRulesChecker` handles Pylint integration, AST traversal, and message
        emission. The horizontal-import rule (BLQ1302) has a narrower scope than the general layer
        model — it only fires for `pytest_bdd.plugin.*` cross-plugin imports — because within-layer
        imports between non-plugin modules are architecturally acceptable.

    Delegates:
        - _LayerConfig: Provides all layer data (module-to-layer mapping, orders, allowed imports,
          exceptions, prefix list).
        - self._init_config: Locates and loads `layers.toml` at construction time.
        - self._check_node_imports: Entry point for import validation; resolves current module's layer
          and dispatches each import to `_check_import`.
        - self._check_import: Performs the actual layer violation check (horizontal and downward).
        - self._resolve_package: Resolves a module to its nearest configured package prefix for
          same-package exemption logic.
        - self._resolve_imported_modules: Converts AST import nodes to absolute module name strings.
        - self._is_pytest_bdd_module: Filters out non-pytest_bdd imports.

    Cohesion:
        Every method in this class contributes to the single goal of import-layer validation. The visitor
        methods (`visit_import`, `visit_importfrom`) are thin adapters that delegate to
        `_check_node_imports`. The pipeline flows: visitor → `_check_node_imports` (filter, resolve
        layer) → `_check_import` (compare layers, emit message). Supporting methods handle module name
        resolution, package resolution, and namespace filtering. No method has extraneous concerns.

    Separation:
        - PluginPatternsChecker: Also checks cross-plugin imports but via plugin name comparison
          (BLQ1002), not via the formal layer DAG. Its scope is plugin structure, not architecture.
        - TestImportRulesChecker: Validates test import paths (BLQ1601); this checker validates
          architectural layer boundaries.
        - QualityGatesChecker: Handles code-pattern quality rules; unrelated to import architecture.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker with Pylint.
        - Pylint import visitors: Calls `visit_import` and `visit_importfrom` for every import.
        - CI/CD: Runs via `make custom-rules` for pre-commit and CI enforcement.

    State and side effects:
        Holds `self._config: _LayerConfig | None` loaded once during `__init__`. If `layers.toml` is
        not found or fails to parse, `_config` is `None` and all checks silently pass. Visitor methods
        call `self.add_message()` to emit BLQ1301/BLQ1302 diagnostics. No other persistent state or
        file I/O after initialization.

    Invariants:
        - `_config` is `None` if `layers.toml` cannot be loaded; all checks are no-ops in that state.
        - Only modules under the `pytest_bdd` namespace are checked (`_is_pytest_bdd_module`).
        - Same-package submodule imports (resolved via `_resolve_package`) are always allowed.
        - Horizontal imports (BLQ1302) only fire when BOTH modules are under `pytest_bdd.plugin.*`
          AND they belong to different plugin packages.
        - Downward imports (BLQ1302) fire when the imported layer's order >= current layer's order
          AND the imported layer is not in the current layer's `allowed_imports` AND no exception covers it.
        - Exception matching supports submodules (e.g., `(pytest_bdd.model, pytest_bdd.parser)` also
          covers `pytest_bdd.model.sub` importing `pytest_bdd.parser.sub`).

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

    name = "layer-rules"

    msgs = {
        "E9041": (
            "BLQ1301: downward import — module %s (layer %s, order %s) imports "
            "%s (layer %s, order %s). Allowed imports: %s.",
            "downward-import",
            "BLQ1301: Downward layer imports are forbidden.",
        ),
        "E9042": (
            "BLQ1302: horizontal import — module %s (layer %s) imports %s from "
            "same layer. Cross-module imports within layer %s are forbidden.",
            "horizontal-import",
            "BLQ1302: Horizontal layer imports are forbidden.",
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        """
        Initialize the checker by calling the parent `BaseChecker.__init__` and then loading the
        layer configuration from di.

        Responsibility:
            Initializes the checker by calling the parent `BaseChecker.__init__` and then loading the
            layer configuration from disk via `_init_config()`. Sets `self._config` to either a valid
            `_LayerConfig` instance or `None` (if `layers.toml` cannot be found or parsed). The config
            loading is best-effort: if it fails, the checker silently disables itself rather than
            crashing Pylint.

        Reason for existence:
            This constructor bridges Pylint's checker lifecycle with the TOML-driven layer configuration.
            The two-phase initialization (parent init → config load) ensures the checker is always in a
            valid state even if `layers.toml` is missing. The `_config` attribute being `None` serves as
            a graceful degradation signal that all visitor methods check before performing any validation.

        Delegates:
            - super().__init__: Standard Pylint BaseChecker initialization.
            - self._init_config: Locates `layers.toml` on disk and creates the `_LayerConfig` instance.

        Cohesion:
            This method does exactly two necessary startup steps: Pylint integration and config loading.
            Nothing else.

        Separation:
            - _init_config: Handles the "where is the file" concern; this method handles the "when to
              load it" concern (at construction time).

        Main consumers:
            - pytest_bdd._pylint.register(): Instantiates `LayerRulesChecker(linter)` during plugin
              registration.

        State and side effects:
            Sets `self._config` (mutable instance attribute). Calls `_init_config()` which reads
            `layers.toml` from disk. No other side effects.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        super().__init__(linter)
        self._config: _LayerConfig | None = None
        self._init_config()

    def _init_config(self) -> None:
        """
        Locates the `docs/architecture/layers.toml` file by first trying the relative path from the
        current working directory.

        Responsibility:
            Locates the `docs/architecture/layers.toml` file by first trying the relative path from the
            current working directory, then walking up parent directories to find it. If found, creates a
            `_LayerConfig` instance and assigns it to `self._config`. If the file is not found or parsing
            fails (any `Exception`), sets `self._config = None` to gracefully disable the checker.

        Reason for existence:
            This method handles the "find the config file" problem. Pylint may be run from different
            working directories (project root, subdirectory, or via tox in a temp dir), so the simple
            relative path `docs/architecture/layers.toml` may not always resolve. The fallback parent-
            directory walk ensures the config is found as long as the user is somewhere within the
            project tree. The broad exception handling ensures a malformed TOML file doesn't crash
            Pylint — the checker simply disables itself.

        Delegates:
            - Path.exists / Path.resolve: Filesystem operations to locate the config file.
            - _LayerConfig.__init__: Parses the TOML file into the in-memory config object.

        Cohesion:
            This method does one thing: find and load the config. It has no knowledge of how the config
            data is used — it just ensures `self._config` is populated or set to `None`.

        Separation:
            - LayerRulesChecker.__init__: Calls `_init_config` at construction time; the constructor
              doesn't know how config loading works.
            - _LayerConfig: Handles parsing; `_init_config` handles file location.

        Main consumers:
            - LayerRulesChecker.__init__: The sole caller, invoked once during checker construction.

        State and side effects:
            Mutates `self._config` from `None` to either a `_LayerConfig` instance or remains `None`.
            Performs filesystem reads and directory traversal via `Path.exists()`. No other side effects.

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
        # Find docs/architecture/layers.toml relative to repository root
        layers_toml = Path("docs/architecture/layers.toml")
        if not layers_toml.exists():
            # Try walking up from current directory to find it
            current = Path().resolve()
            for parent in [current] + list(current.parents):
                candidate = parent / "docs" / "architecture" / "layers.toml"
                if candidate.exists():
                    layers_toml = candidate
                    break

        if layers_toml.exists():
            try:
                self._config = _LayerConfig(layers_toml)
            except Exception:  # noqa: BLE001  -- layers.toml parse failure is non-fatal; checker disables itself gracefully
                self._config = None

    def visit_import(self, node: nodes.Import) -> None:
        """
        Pylint visitor for `import x` and `import x.y` statements.

        Responsibility:
            Pylint visitor for `import x` and `import x.y` statements. Delegates directly to
            `_check_node_imports(node)` which handles current-module resolution, import resolution,
            layer lookup, and violation emission. This method is a thin adapter between Pylint's
            visitor dispatch and the checker's validation logic.

        Reason for existence:
            This method exists because Pylint's visitor pattern dispatches on AST node type.
            `visit_import` handles `nodes.Import` while `visit_importfrom` handles `nodes.ImportFrom`.
            Both delegate to the same `_check_node_imports` method, keeping the dispatch concern
            separate from the validation concern.

        Delegates:
            - self._check_node_imports: Performs all validation logic for the import node.

        Cohesion:
            Single-line delegation method. Its sole purpose is to connect Pylint's `visit_import`
            hook to the shared validation logic.

        Separation:
            - visit_importfrom: Handles the `from x import y` form; structurally identical but
              dispatches a different AST node type.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `Import` node.

        State and side effects:
            None directly; delegates to `_check_node_imports` which may call `self.add_message()`.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self._check_node_imports(node)

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Pylint visitor for `from x import y` and `from x.y import z` statements.

        Responsibility:
            Pylint visitor for `from x import y` and `from x.y import z` statements. Delegates directly
            to `_check_node_imports(node)` which handles current-module resolution, import resolution,
            layer lookup, and violation emission. This method is a thin adapter between Pylint's
            visitor dispatch and the checker's validation logic.

        Reason for existence:
            Exists because Pylint dispatches `Import` and `ImportFrom` to different visitor methods,
            but both need identical layer validation. The delegation pattern avoids duplicating the
            validation pipeline while respecting Pylint's visitor contract.

        Delegates:
            - self._check_node_imports: Performs all validation logic for the import node.

        Cohesion:
            Single-line delegation method. Connects Pylint's `visit_importfrom` hook to shared logic.

        Separation:
            - visit_import: Handles the `import x` form; structurally identical but dispatches a
              different AST node type.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `ImportFrom` node.

        State and side effects:
            None directly; delegates to `_check_node_imports` which may call `self.add_message()`.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self._check_node_imports(node)

    def _check_node_imports(self, node: nodes.Import | nodes.ImportFrom) -> None:
        """
        Provide the central dispatch point for import validation.

        Responsibility:
            The central dispatch point for import validation. Checks if the checker is configured
            (`self._config` is not None), resolves the current file's module name and layer, filters
            out non-`pytest_bdd` modules, resolves the imported module names via
            `_resolve_imported_modules`, and passes each `(current_module, current_layer, imported_module)`
            triple to `_check_import`. Returns early if any precondition fails (no config, no module
            name, not a pytest_bdd module, no layer found).

        Reason for existence:
            This method encapsulates all the precondition checking and data preparation that both
            `visit_import` and `visit_importfrom` need. Without it, the filtering logic (config check,
            namespace check, layer resolution) would be duplicated in both visitor methods. It also
            handles the import resolution differently for `Import` vs `ImportFrom` nodes via
            `_resolve_imported_modules`.

        Delegates:
            - self._config.layer_for_module: Resolves the current module to its layer.
            - self._is_pytest_bdd_module: Filters out non-project imports.
            - self._resolve_imported_modules: Converts AST import nodes to absolute module name strings.
            - self._check_import: Performs the actual violation check for each imported module.

        Cohesion:
            This method orchestrates the validation pipeline: check preconditions → resolve current
            layer → resolve imported modules → dispatch to per-import check. It doesn't perform any
            of the actual layer comparison or message emission — that's delegated to `_check_import`.

        Separation:
            - _check_import: Handles the layer comparison logic; this method handles the pipeline
              orchestration and precondition filtering.
            - _resolve_imported_modules: Handles AST-to-string conversion; this method handles the
              dispatch loop.

        Main consumers:
            - LayerRulesChecker.visit_import / visit_importfrom: Both visitor methods delegate here.

        State and side effects:
            Reads `self._config`. Calls `self.add_message()` indirectly through `_check_import`.
            No direct file I/O or state mutation.

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
        if not self._config:
            return

        current_module = node.root().name
        if not current_module or not self._is_pytest_bdd_module(current_module):
            return

        current_layer = self._config.layer_for_module(current_module)
        if not current_layer:
            return

        resolved = self._resolve_imported_modules(node, current_module)
        for imported_module in resolved:
            if not self._is_pytest_bdd_module(imported_module):
                continue
            self._check_import(node, current_module, current_layer, imported_module)

    def _check_import(
        self,
        node: nodes.NodeNG,
        current_module: str,
        current_layer: str,
        imported_module: str,
    ) -> None:
        """
        Perform the actual layer violation check for a single import pair.

        Responsibility:
            Performs the actual layer violation check for a single import pair. Resolves the imported
            module's layer via `_LayerConfig.layer_for_module`. Then checks two conditions: (1) BLQ1302
            horizontal import — fires only when both modules are under `pytest_bdd.plugin.*` but belong
            to different plugin packages within the same layer; (2) BLQ1301 downward import — fires when
            the imported layer's order is >= the current layer's order AND the imported layer is not in
            the current layer's `allowed_imports` AND the pair is not a configured exception. Same-package
            submodule imports (resolved via `_resolve_package`) are always allowed. If the imported module
            has no configured layer, the check is skipped.

        Reason for existence:
            This method is the core decision engine of the layer enforcement system. It implements the
            three-tier check: (a) skip if same package, (b) check horizontal imports for plugins,
            (c) check downward imports with order comparison, allowlist, and exceptions. The ordering
            of checks matters: horizontal check comes before downward check, and same-package check
            comes before both. The method exists separately from `_check_node_imports` to keep the
            per-import decision logic testable in isolation.

        Delegates:
            - self._config.layer_for_module: Resolves imported module to its layer.
            - self._resolve_package: Resolves both modules to their package prefixes.
            - self._config.allowed_imports_for_layer: Gets the current layer's allowlist.
            - self._config.order_for_layer: Gets numeric orders for both layers.
            - self._config.is_exception: Checks if the pair is a configured exception.
            - self.add_message: Emits BLQ1301 or BLQ1302 when violations are found.

        Cohesion:
            Every line in this method contributes to the single decision: is this import allowed? The
            conditions are evaluated in a clear precedence order (same-package → horizontal → downward),
            and each branch either returns early or emits a message.

        Separation:
            - _check_node_imports: Handles the outer loop and precondition filtering; this method
              handles the per-import decision logic.
            - _resolve_package: Handles prefix matching; this method uses its result for same-package
              exemption.

        Main consumers:
            - LayerRulesChecker._check_node_imports: Called once per imported module in the dispatch loop.

        State and side effects:
            Reads from `self._config` (read-only after initialization). Calls `self.add_message()` to
            emit linting diagnostics. No direct file I/O or state mutation.

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
        config = self._config
        if not config:
            return

        imported_layer = config.layer_for_module(imported_module)
        if not imported_layer:
            return

        imported_package = self._resolve_package(imported_module)
        current_package = self._resolve_package(current_module)

        # BLQ1302: horizontal import (only between different plugins)
        if imported_layer == current_layer:
            is_plugin_import = current_module.startswith("pytest_bdd.plugin.") and imported_module.startswith(
                "pytest_bdd.plugin."
            )
            if is_plugin_import and imported_package != current_package:
                self.add_message(
                    "horizontal-import",
                    node=node,
                    args=(current_module, current_layer, imported_module, imported_layer),
                )
            return

        # If they are in the same package (e.g. submodules), it's allowed
        if imported_package is not None and imported_package == current_package:
            return

        # Check allowed imports
        allowed = config.allowed_imports_for_layer(current_layer)
        if imported_layer in allowed:
            return

        # Check orders
        imported_order = config.order_for_layer(imported_layer)
        current_order = config.order_for_layer(current_layer)

        if imported_order >= current_order:
            if config.is_exception(current_module, imported_module):
                return
            allowed_str = ", ".join(allowed) if allowed else "none"
            self.add_message(
                "downward-import",
                node=node,
                args=(
                    current_module,
                    current_layer,
                    current_order,
                    imported_module,
                    imported_layer,
                    imported_order,
                    allowed_str,
                ),
            )

    def _resolve_package(self, module: str) -> str | None:
        """
        Resolve a dotted module name to its nearest configured package prefix by iterating over
        all known module prefixes fr.

        Responsibility:
            Resolves a dotted module name to its nearest configured package prefix by iterating over
            all known module prefixes from `_LayerConfig.module_prefixes()` and performing longest-
            prefix matching: for each candidate prefix, checks if the module's dotted parts match the
            candidate's parts, and returns the longest matching prefix. Returns `None` if no prefix
            matches or if `_config` is `None`.

        Reason for existence:
            This method provides the package-level grouping used for two purposes: (1) same-package
            exemption — submodule imports within the same package are always allowed regardless of
            layer rules; (2) horizontal import detection — cross-plugin imports are only flagged when
            the two modules resolve to different package prefixes. The longest-prefix matching ensures
            that `pytest_bdd.plugin.cucumber_json` resolves to `pytest_bdd.plugin.cucumber_json` rather
            than the shorter `pytest_bdd.plugin`.

        Delegates:
            - self._config.module_prefixes: Returns the dict of all known module prefixes.
            - (none): Performs the prefix matching inline with simple string/list comparisons.

        Cohesion:
            This method does exactly one thing: find the best matching package prefix for a module
            string. It is used by `_check_import` for both same-package and horizontal-import logic.

        Separation:
            - _LayerConfig.layer_for_module: Resolves module → layer; this method resolves module →
              package prefix. They operate at different granularities (layer vs package).
            - _resolve_imported_modules: Resolves AST nodes → module strings; this method resolves
              module strings → package prefixes.

        Main consumers:
            - LayerRulesChecker._check_import: Called twice per import pair (once for current module,
              once for imported module).

        State and side effects:
            None, pure function given `self._config`. No mutations, no I/O.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if not self._config:
            return None
        parts = module.split(".")
        best: str | None = None
        best_len = 0
        for candidate in self._config.module_prefixes():
            candidate_parts = candidate.split(".")
            if len(candidate_parts) <= len(parts):
                match = True
                for i, cp in enumerate(candidate_parts):
                    if parts[i] != cp:
                        match = False
                        break
                if match and len(candidate_parts) > best_len:
                    best = candidate
                    best_len = len(candidate_parts)
        return best

    def _is_pytest_bdd_module(self, module: str) -> bool:
        """
        Return `True` if the given module name is exactly `"pytest_bdd"` or starts with
        `"pytest_bdd."`, indicating it belon.

        Responsibility:
            Returns `True` if the given module name is exactly `"pytest_bdd"` or starts with
            `"pytest_bdd."`, indicating it belongs to the project's namespace and should be subject
            to layer validation. Returns `False` for all other modules (stdlib, third-party, test
            packages), which are silently ignored by the layer checker.

        Reason for existence:
            This method acts as a namespace filter to prevent the layer checker from analyzing every
            import in the Python ecosystem. Without it, every `import os`, `import pytest`, or
            `from typing import ...` statement would trigger layer resolution attempts, wasting
            computation and potentially producing false positives if a third-party package happens
            to match a configured prefix.

        Delegates:
            - (none): Pure string comparison with no external dependencies.

        Cohesion:
            This method does exactly one thing: check if a module name is in the pytest_bdd namespace.
            It has no knowledge of layers, orders, or violations.

        Separation:
            - _LayerConfig.layer_for_module: Resolves the module to a layer name; this method is the
              gatekeeper that determines whether layer resolution should even be attempted.
            - _check_node_imports: Calls this method as a precondition for both current and imported
              modules.

        Main consumers:
            - LayerRulesChecker._check_node_imports: Called twice — once for the current module and
              once for each imported module.

        State and side effects:
            None, pure function. No I/O, no state access beyond the string parameter.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        return module == "pytest_bdd" or module.startswith("pytest_bdd.")

    def _resolve_imported_modules(
        self,
        node: nodes.Import | nodes.ImportFrom,
        current_file_module: str,
    ) -> list[str]:
        """
        Convert an AST import node into a list of absolute dotted module name strings.

        Responsibility:
            Converts an AST import node into a list of absolute dotted module name strings. For
            `ImportFrom` nodes: extracts the base module name from `node.modname`, handles relative
            imports by resolving `node.level` against `current_file_module` (popping parts for each
            level), and returns a single-element list. For `Import` nodes: returns the list of
            imported module names from `node.names` directly (they are already absolute). Returns
            an empty list if `node.modname` is `None` for an `ImportFrom`.

        Reason for existence:
            This method bridges the gap between AST representation (where imports can be relative or
            split across `modname` + `names`) and the checker's need for absolute module name strings.
            Without it, `_check_node_imports` would need to handle the `Import` vs `ImportFrom`
            structural differences inline. The relative import resolution logic (popping parts based
            on `node.level`) is non-trivial and deserves encapsulation.

        Delegates:
            - (none): Performs string manipulation and list construction inline.

        Cohesion:
            This method does exactly one thing: convert import AST nodes to absolute module name
            strings. The two branches (Import vs ImportFrom) handle the structural differences
            between the two import forms.

        Separation:
            - _check_node_imports: Calls this method to get module name strings, then iterates over
              them for validation. The conversion concern is separate from the validation concern.
            - _resolve_package: Operates on already-resolved module strings; this method produces them.

        Main consumers:
            - LayerRulesChecker._check_node_imports: Called once per import node to get the list of
              imported modules.

        State and side effects:
            None, pure function. Takes AST nodes and a string, returns a list of strings. No I/O,
            no state mutation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if isinstance(node, nodes.ImportFrom):
            if node.modname is None:
                return []
            module = node.modname
            if node.level and node.level > 0:
                parts = current_file_module.split(".")
                for _ in range(node.level - (1 if module else 0)):
                    if parts:
                        parts.pop()
                if module:
                    parts.append(module)
                module = ".".join(parts)
            return [module]
        return [alias[0] for alias in node.names]
