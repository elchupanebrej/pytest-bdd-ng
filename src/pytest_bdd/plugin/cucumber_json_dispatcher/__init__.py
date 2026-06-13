# init: no-check
"""
Serves as the Reporting layer (order 7) package init for the cucumber JSON dispatcher plugin.

Responsibility:
    Serves as the Reporting layer (order 7) package init for the cucumber JSON dispatcher plugin. Acts as a namespace
    marker for the sub-package containing the JSON output dispatch mechanism that routes cucumber JSON reports to file
    or stdout. The actual implementation lives in the plugin, hook, entrypoint, and const modules within this package.

Reason for existence:
    This module exists to establish the Python package boundary for the cucumber_json_dispatcher plugin. It separates
    the JSON dispatch concern from the cucumber_json plugin (which generates the JSON content) and other reporting
    plugins. The dispatcher is a distinct reporting sub-system that owns the output routing decision (file vs stdout)
    independently of JSON content generation.

Delegates:
    - plugin: Contains the actual plugin class that implements dispatch to file/stdout.
    - hook: Defines hook specifications for the dispatcher's pytest hook namespace.
    - entrypoint: Registers the plugin and CLI options via pytest_configure and pytest_addoption.
    - const: Defines constants used by the dispatcher (formatter kind, output paths).

Cohesion:
    Purely a structural package marker with no executable logic. The actual dispatch functionality is distributed across
    the plugin, hook, and entrypoint modules.

Separation:
    - cucumber_json.plugin: Generates the JSON content but does NOT handle output dispatch — that's this package's
    responsibility.
    - cucumber_json_formatter: Handles formatter-specific JSON output — distinct from the general dispatcher.

Main consumers:
    - pytest: Registers the dispatcher plugin via setuptools entry_points or conftest import.
    - pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint: Imports from sibling modules within this package.

State and side effects:
    None, keeps no persistent state. Purely a namespace marker module.

Invariants:
    - Must be importable as a Python package for plugin discovery.
    - The dispatcher's file/stdout routing must be independent of JSON content generation.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""
