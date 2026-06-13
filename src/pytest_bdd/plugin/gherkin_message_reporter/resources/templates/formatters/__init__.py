# init: no-check
"""
Serves as the innermost package marker for the gherkin message reporter's formatter adapter templates.

Responsibility:
    Serves as the innermost package marker for the gherkin message reporter's formatter adapter templates. Acts as a
    namespace marker that makes the formatter-specific template directory discoverable for `importlib.resources`-based
    loading of Jinja2 template files used by the live formatter adapters (e.g., cucumber-json formatter). Contains no
    executable code — purely a structural package marker with a descriptive comment.

Reason for existence:
    This module exists as a Python package marker at the leaf of the template directory hierarchy. The live formatter
    adapters require formatter-specific Jinja2 templates to be loadable via `importlib.resources.files()`. This init
    ensures the directory is a proper Python package, enabling reliable template path resolution regardless of
    installation method (editable install, wheel, etc.).

Delegates:
    - (Jinja2 template files in this directory): Contain the actual rendering templates loaded at runtime by
    live_formatter_process.

Cohesion:
    Purely a structural package marker. The single comment documents its purpose. All template rendering logic lives in
    sibling runtime modules (`live_formatter_process`, `html_report`).

Separation:
    - templates/__init__.py: Parent package marker for all templates.
    - resources/__init__.py: Grandparent package marker for all resources.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process: Loads templates from this package directory via
    importlib.resources.
    - pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer: May load formatter-specific templates from this
    package.

State and side effects:
    None, keeps no persistent state. Purely a namespace marker module.

Invariants:
    - Must be importable as a Python package for template resource discovery.
    - Formatter templates in this directory must be loadable via `importlib.resources.files()`.

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

# Package marker for formatter adapter templates.
