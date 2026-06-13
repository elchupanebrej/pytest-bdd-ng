# init: no-check
"""
Serves as the Reporting layer (order 7) package init for the gherkin message reporter's Jinja2 templates sub-package.

Responsibility:
    Serves as the Reporting layer (order 7) package init for the gherkin message reporter's Jinja2 templates sub-
    package. Acts as a namespace marker that makes the templates directory discoverable as a Python package for
    `importlib.resources`-based template loading. Contains no executable code — purely structural for resource
    discovery.

Reason for existence:
    This module exists as a Python package marker to enable template file discovery. The live formatter system uses
    `importlib.resources` to find and load Jinja2 template files (.j2, .html) from a well-defined package location.
    Without this init, the directory would not be importable as a Python package.

Delegates:
    - formatters: Sub-package containing formatter-specific template files.

Cohesion:
    Purely a structural package marker with no executable logic. All template rendering logic lives in
    `live_formatter_process` and `html_report`.

Separation:
    - formatters/__init__.py: Sub-package marker for formatter-specific templates.
    - resources/__init__.py: Parent package marker for shared static resources.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process: Loads templates from this package via
    importlib.resources.files().
    - pytest_bdd.plugin.gherkin_message_reporter.html_report: Loads templates for HTML report generation.

State and side effects:
    None, keeps no persistent state. Purely a namespace marker module.

Invariants:
    - Must be importable as a Python package for template resource discovery.
    - Template file paths relative to this package must be stable across versions.

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
