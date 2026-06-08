"""
Provide html report helpers.

Responsibility:
    Provide html report helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.html_report` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - escape_html_formatter_message_json: owns nested behavior below this boundary
    - render_html_report_content: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `html_report`

State and side effects:
    mutates rendered, escaped_messages; depends on __future__.annotations.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.html_report` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations


def escape_html_formatter_message_json(message_json: str) -> str:
    """
    Escape HTML formatter message JSON.

    Returns:
        Escaped message JSON.

    Responsibility:
        Escape HTML formatter message JSON. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.html_report.escape_html_formatter_message_json` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - message_json.replace: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `escape_html_formatter_message_json`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return message_json.replace("<", "\\x3C")


def render_html_report_content(  # noqa: PLR0913
    *,
    template: str,
    title: str,
    icon: str,
    css: str,
    custom_css: str,
    messages: tuple[str, ...],
    script: str,
    custom_script: str,
) -> str:
    """
    Render HTML report content.

    Returns:
        Rendered HTML report.

    Responsibility:
        Render HTML report content. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.html_report.render_html_report_content` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary
        - escape_html_formatter_message_json: collaborator call used by this boundary
        - rendered.replace: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `render_html_report_content`

    State and side effects:
        mutates rendered, escaped_messages.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.html_report.render_html_report_content` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    escaped_messages = ",".join(escape_html_formatter_message_json(message_json) for message_json in messages)
    rendered = template
    for placeholder, value in (
        ("{{title}}", title),
        ("{{icon}}", icon),
        ("{{css}}", css),
        ("{{custom_css}}", custom_css),
        ("{{messages}}", escaped_messages),
        ("{{script}}", script),
        ("{{custom_script}}", custom_script),
    ):
        rendered = rendered.replace(placeholder, value)
    return rendered
