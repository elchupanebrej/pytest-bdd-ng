"""
Owns Jinja2 template rendering infrastructure for generating documentation, reports, and boilerplate code from pytest.

Responsibility:
    Owns Jinja2 template rendering infrastructure for generating documentation, reports, and boilerplate code from
    pytest-bdd runtime data models. This package provides template loading, rendering, and output formatting for
    artifacts such as feature documentation (RST/Markdown generated from Gherkin .feature.md files), cucumber JSON
    reports, usage reports, and any other template-driven output consumed by the documentation and reporting plugins.
    This is the canonical template engine abstraction layer that isolates rendering concerns from data collection logic.

Reason for existence:
    Centralizes all Jinja2 template management into a single package so that reporting plugins (cucumber_json,
    cucumber_usage, cucumber_pretty, etc.) do not need to manage their own template loading, caching, or rendering
    logic. Without this package, each reporting plugin would duplicate template path resolution, Jinja2 environment
    setup, and rendering error handling. The template package provides a consistent rendering interface that allows
    plugins to focus on data preparation while the template engine handles formatting and output. It is placed at the
    top level of pytest_bdd because it serves plugins across multiple architectural layers (reporting, documentation
    generation, struct_bdd).

Delegates:
    - Jinja2 (third-party library): Provides the actual template language, compilation, and rendering engine — this
    package wraps Jinja2 to provide pytest-bdd-specific template resolution, default contexts, and output conventions.
    - pypandoc (third-party library, optional): Used for format conversion between Markdown and RST when generating
    documentation artifacts from feature files.

Cohesion:
    All members share the same concern: transforming structured data (run results, feature documents, usage statistics)
    into formatted text output through templates. The package provides template discovery, loading, context preparation,
    and rendering in a unified pipeline. Any template-driven output in the plugin should flow through this package
    rather than having its own ad-hoc rendering.

Separation:
    - pytest_bdd.plugin.*: Reporting plugins (cucumber_json, cucumber_pretty, etc.) consume the template package for
    output formatting but own the data collection and message generation logic — templates format data that plugins
    prepare, they do not collect it.
    - pytest_bdd.parser: Kept separate because the parser package owns Gherkin document parsing (text to AST), while the
    template package owns rendering (AST to formatted output) — these are inverse operations at different ends of the
    pipeline.

Main consumers:
    - pytest_bdd.plugin.cucumber_json: Uses the template package to render cucumber JSON report templates from execution
    results.
    - Documentation generation pipeline: Uses the template package to convert Gherkin .feature.md files into .rst
    documentation files under docs/features/.
    - pytest_bdd.plugin.cucumber_usage: Uses the template package to render step usage statistics and reports.

State and side effects:
    None, keeps no persistent state. Template objects are created and rendered on demand; Jinja2 environments may cache
    compiled templates in memory but this is managed by the Jinja2 library, not by this package directly.

Invariants:
    - All template rendering must go through this package's rendering interface, never through direct Jinja2 API calls
    from plugin code — this ensures consistent error handling and template resolution.
    - Template file paths should be discoverable through a consistent naming convention and directory structure managed
    by this package.

Architecture score:
    #arch-eval:reason_for_existence=2
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

__all__ = []  # template package — public API populated by submodules
