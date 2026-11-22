"""Render a Cucumber HTML document from serialized Messages JSON."""

from __future__ import annotations

import re
from pathlib import Path

import chevron

from pytest_cuke.npm_resource import find_resource


def render_cucumber_html(messages: str, package: str = "@cucumber/html-formatter") -> str:
    """Inline the installed formatter resources around the saved Messages."""
    script_content = ""
    for candidate in (Path("dist") / "main.js", Path("main.js"), Path("dist") / "cucumber-html.js"):
        found = list(find_resource(package, str(candidate)))
        if found:
            script_content = Path(found[0]).read_text(encoding="utf-8")
            break

    css_content = ""
    for candidate in (Path("dist") / "main.css", Path("main.css"), Path("dist") / "cucumber-html.css"):
        found = list(find_resource(package, str(candidate)))
        if found:
            css_content = Path(found[0]).read_text(encoding="utf-8")
            break

    template = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '    <meta charset="UTF-8">\n'
        "    <style>{{&css}}</style>\n"
        "</head>\n"
        "<body>\n"
        '    <div id="content"></div>\n'
        "    <script>\n"
        "        window.CUCUMBER_MESSAGES = [{{&messages}}];\n"
        "    </script>\n"
        "    <script>{{&script}}</script>\n"
        "</body>\n"
        "</html>\n"
    )
    for candidate in (
        Path("src") / "index.mustache.html",
        Path("src") / "index.mustache",
        Path("index.mustache.html"),
        Path("index.mustache"),
        Path("dist") / "index.mustache.html",
        Path("templates") / "index.mustache.html",
    ):
        found = list(find_resource(package, str(candidate)))
        if found:
            raw = Path(found[0]).read_text(encoding="utf-8")
            template = re.sub(r"\{\{", "{{&", raw)
            break

    rendered: str = chevron.render(
        template,
        {
            "css": css_content,
            "script": script_content,
            "messages": _script_safe_json(messages),
        },
    )
    return rendered


def _script_safe_json(content: str) -> str:
    """Keep inline JSON from closing the script element or breaking JavaScript."""
    return content.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


__all__ = ["render_cucumber_html"]
