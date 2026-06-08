# API Reference

Auto-generated from type annotations.

```{toctree}
:maxdepth: 2

pytest_bdd
pytest_bdd.scenario
pytest_bdd.steps
pytest_bdd.parsers
pytest_bdd.model
pytest_bdd.plugin
pytest_bdd.types
pytest_bdd.hook
```

Architecture responsibility contracts for every Python module, class, function,
and method are aggregated in
[`../architecture/OBJECT_MAP.md`](../architecture/OBJECT_MAP.md), with refactor
risk zones in
[`../architecture/RESPONSIBILITY_GAPS.md`](../architecture/RESPONSIBILITY_GAPS.md).

## Public Entry Points

The package root lazily exposes the common testing API:

- `scenario`
- `scenarios`
- `given`
- `when`
- `then`
- `step`
- `not_implemented`
- `tolerant`
- `FeaturePathType`
- `PytestBDDStepDefinitionWarning`

pytest plugin entry points are declared in `pyproject.toml` under
`[project.entry-points.pytest11]`. They include the scenario test collector,
pickle runner, structured BDD plugin, code generator, Cucumber JSON reporter,
Gherkin message reporter, terminal reporter, and Cucumber formatter plugins.

Configuration and installation details are summarized in
`../guides/configuration.md`.

## Full Project Structure

Full apidoc RST output is generated under `docs/_build/api/generated/` during
local documentation builds. Generated artifacts stay outside the source tree.
