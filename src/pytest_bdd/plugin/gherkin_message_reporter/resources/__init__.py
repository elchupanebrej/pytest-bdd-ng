# init: no-check
"""
Serves as the Reporting layer (order 7) package init for the gherkin message reporter's resources sub-package.

Responsibility:
    Serves as the Reporting layer (order 7) package init for the gherkin message reporter's resources sub-package. Acts
    as a namespace marker and package boundary for template and static resource files used by the HTML report generation
    and formatter adapters within the live NDJSON reporting system. Contains no executable code — purely structural.

Reason for existence:
    This module exists as a Python package marker to enable template discovery via `pkg_resources` or
    `importlib.resources`. The live formatter system needs to find and load Jinja2 templates and static assets from a
    well-defined package location. This init makes `resources` addressable as a Python package for resource loading.

Delegates:
    - templates: Sub-package containing Jinja2 template files used by formatter adapters.

Cohesion:
    Purely a structural package marker with no executable logic. All functionality related to resources (template
    loading, formatter rendering) lives in sibling runtime modules.

Separation:
    - live_formatter_process: Contains the actual rendering logic that loads templates from this package.
    - standalone_renderer: Independent rendering utility that may load templates from this package.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process: Loads templates from this package via
    importlib.resources.
    - pytest_bdd.plugin.gherkin_message_reporter.html_report: Loads templates and static assets from this package.

State and side effects:
    None, keeps no persistent state. Purely a namespace marker module.

Invariants:
    - Must be importable as a Python package for resource discovery mechanisms.
    - Template and resource paths relative to this package must be stable.

Architecture score:
    #arch-eval:reason_for_existence=2
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""
