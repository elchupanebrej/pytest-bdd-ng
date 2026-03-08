# Contract: Runtime API Without `Feature`

## Scope

Defines the public runtime boundary for parser, collection, hooks, and fixtures after removing `src/pytest_bdd/model/gherkin_document/core.py::Feature`.

## Parser and Locator Contract

Parser outputs:
- `GherkinDocument`
- raw feature file content used to build `Source`

Collection outputs:
- `Source`
- `GherkinDocument`
- `Pickle`

Forbidden collection payloads:
- `Feature`
- any feature wrapper introduced solely for runtime/reporting convenience

## Fixture Contract

Allowed runtime fixtures:
- `gherkin_document`
- `feature_source`
- `pickle`
- `run_context`
- step-related fixtures already derived from runtime state

Forbidden runtime fixtures:
- `feature`
- executable `scenario`

## Hook Contract

Hook input contract:
- `run: Run` is the canonical runtime parameter.
- Hook implementations resolve active `ScenarioRun`, `GherkinDocument`, `Source`, `Pickle`, and steps from `run`.

Forbidden hook parameters:
- `feature: Feature`
- any parameter name that exposes a `Pickle` object under `scenario` naming

## Reporter and Serializer Contract

Reporters and serializers:
- read feature metadata and AST lookups via `Run` / `ScenarioRun` helpers;
- may emit message-model objects and serialized dict payloads;
- must not reconstruct `Feature`.

## Validation Requirements

- Compatibility tests verify no runtime fixture named `feature` is exposed.
- Hook API tests verify `Run` remains sufficient for plugin consumers.
- Collection tests verify the `Source -> GherkinDocument -> Pickle` pipeline works without `Feature`.
