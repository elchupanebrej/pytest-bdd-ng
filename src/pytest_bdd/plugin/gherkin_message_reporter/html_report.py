from __future__ import annotations


def escape_html_formatter_message_json(message_json: str) -> str:
    return message_json.replace("<", "\\x3C")


def render_html_report_content(
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
