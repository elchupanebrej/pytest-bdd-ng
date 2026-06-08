# How-To Guides

Step-by-step guides for common pytest-bdd-ng tasks. Each guide follows a
**problem → solution → example → mistakes** format so you can solve a
specific task without reading the full reference documentation.

## Extension Guides

* **Custom Gherkin Parser** — implement a domain-specific step parser
  when the seven built-in parsers are not enough.
* **Structured BDD** — write scenarios in YAML, JSON, TOML, HOCON, or
  JSON5 instead of Gherkin ``.feature`` files.
* **Parallel Execution with xdist** — distribute hundreds of scenarios
  across CPU cores while keeping reporting coherent.
* **Custom Formatter Plugin** — create a new output format (Slack,
  Datadog, dashboards) using the Cucumber Messages protocol.

## Migration

* **Migration from pytest-bdd v1** — breaking changes checklist,
  step-by-step migration path, and before/after code comparisons.

```{toctree}
:maxdepth: 1

01-custom-gherkin-parser
02-structured-bdd-yaml-json
03-parallel-execution-xdist
04-custom-formatter-plugin
05-migration-from-v1
```
