"""
Dispatcher plugin that bridges INI and CLI cucumber-json configuration paths.

INI path (cucumber_json_path) activates the Python-written JSON reporter (legacy format).
CLI path (--cucumber-json) activates the Node.js @cucumber/cucumber JSON formatter
(Cucumber-spec format). These produce intentionally different JSON structures.

This dispatcher reads both options and enforces CLI-wins precedence by suppressing
the INI backend when both are simultaneously active.
"""
