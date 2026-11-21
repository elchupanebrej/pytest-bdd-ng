import json
from pathlib import Path

from pytest_cuke import html_report, message_plugin


class _Option:
    cuke_html = ""


class _Config:
    option = _Option()
    hook = object()
    rootpath = Path(".")

    def getini(self, name):
        return ""


def _plugin(messages_path: Path, html_path: Path, monkeypatch) -> message_plugin.MessagePlugin:
    # The unit target is HTML rendering, not the npm preflight.
    monkeypatch.setattr(message_plugin, "check_npm", lambda: True)
    monkeypatch.setattr(message_plugin, "check_npm_package", lambda *args, **kwargs: True)
    _Option.cuke_html = str(html_path)
    plugin = message_plugin.MessagePlugin(config=_Config())
    plugin.is_disabled = False
    plugin.messages_file_path = messages_path
    return plugin


def _resolver(files: dict[str, Path]):
    # Resource lookups join with the platform separator; compare in one form.
    normalized = {key.replace("\\", "/"): value for key, value in files.items()}

    def find_resource(package_name, resource_path):
        path = normalized.get(resource_path.replace("\\", "/"))
        return iter([str(path)] if path is not None else [])

    return find_resource


def test_html_report_prefers_the_package_mustache_template(tmp_path, monkeypatch):
    # The report path is process-local; keep it independent of xdist worker state.
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.setattr(message_plugin, "_worker_id_from_config", lambda config: None)
    template = tmp_path / "index.mustache"
    template.write_text('<style>{{css}}</style><div id="content"></div>{{script}}{{messages}}', encoding="utf-8")
    script = tmp_path / "main.js"
    script.write_text("FORMATTER_SCRIPT", encoding="utf-8")
    css = tmp_path / "main.css"
    css.write_text("FORMATTER_CSS", encoding="utf-8")
    messages = tmp_path / "messages.ndjson"
    messages.write_text(json.dumps({"testRunStarted": {"timestamp": "0"}}) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        html_report,
        "find_resource",
        _resolver({"src/index.mustache": template, "dist/main.js": script, "dist/main.css": css}),
    )

    output = tmp_path / "report.html"
    plugin = _plugin(messages, output, monkeypatch)
    plugin.generate_html_report()

    html = output.read_text(encoding="utf-8")
    assert "FORMATTER_SCRIPT" in html
    assert "FORMATTER_CSS" in html
    assert html.index('<div id="content"></div>') < html.index("FORMATTER_SCRIPT")
    assert "testRunStarted" in html


def test_html_report_keeps_a_closing_script_tag_inside_the_messages_data(monkeypatch):
    monkeypatch.setattr(html_report, "find_resource", _resolver({}))
    feature_line = json.dumps(
        {"testRunStarted": {"timestamp": "0"}, "testRunHookStarted": {"id": "</script><script>alert(1)</script>"}}
    )

    html = html_report.render_cucumber_html(feature_line)

    embedded = html.split("window.CUCUMBER_MESSAGES = [", 1)[1].split("];", 1)[0]
    assert "</script><script>" not in embedded
    assert json.loads(embedded) == json.loads(feature_line)
    assert html.count("</script>") == 2


def test_html_report_fallback_mounts_before_starting_the_formatter(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.setattr(message_plugin, "_worker_id_from_config", lambda config: None)
    messages = tmp_path / "messages.ndjson"
    messages.write_text(json.dumps({"testRunStarted": {"timestamp": "0"}}) + "\n", encoding="utf-8")
    script = tmp_path / "main.js"
    script.write_text("FORMATTER_SCRIPT", encoding="utf-8")
    monkeypatch.setattr(html_report, "find_resource", _resolver({"dist/main.js": script}))

    output = tmp_path / "report.html"
    plugin = _plugin(messages, output, monkeypatch)
    plugin.generate_html_report()

    html = output.read_text(encoding="utf-8")
    assert html.index('<div id="content"></div>') < html.index("window.CUCUMBER_MESSAGES")
    assert html.index("window.CUCUMBER_MESSAGES") < html.index("FORMATTER_SCRIPT")
