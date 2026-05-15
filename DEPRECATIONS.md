# Deprecations

## Removed in pytest-bdd-ng 1.0

| Feature | Replacement | Reason |
|---------|-------------|--------|
| `--cucumberjson` CLI flag | `--cucumber-json-formatter` via class-based plugin entrypoint | Replaced by class-based plugin architecture |
| Allure logger plugin | External `pytest-allure` plugin | Dead code — all implementation commented out |

## Deprecated in pytest-bdd-ng 2.x

| Feature | Replacement | Timeline |
|---------|-------------|----------|
| `example_converters` on `@scenario` | `converters` on step decorators with `parsers.parse()` | Remove in 3.0 |
| `<var>` template syntax in step strings | `{var}` with `parsers.parse()` | Remove in 3.0 |
| `pathlib2` dependency | stdlib `pathlib` (Python 3.10+) | Remove in 3.0 |
| `docopt-ng` dependency | argparse or click for CLI | Remove in 3.0 |

## Migration Notes

For detailed before/after code examples for each breaking change, see [MIGRATION.md](MIGRATION.md).

Key migration steps:
1. Replace `--cucumberjson` with `--cucumber-json-formatter`
2. Add `target_fixture` parameter to all `@given` decorators
3. Convert `<var>` step patterns to `{var}` with `parsers.parse()`
4. Move `example_converters` from `@scenario` to individual step decorators
5. Update hook signatures to use `(request, Run)` instead of `(feature, scenario)`
6. Install `pytest-allure` separately if Allure reporting is needed
