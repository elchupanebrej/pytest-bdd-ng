<!-- markdownlint-disable MD013 -->

# Hook Plugin Public API Compatibility

## Compatibility Policy

- Policy: additive-only for public hook/plugin symbols.
- Migration requirement: none expected for consumers.
- Protected runtime surface:
  - Hook parameter `run: Run`
  - `run_context` fixture and `Run.STASH_KEY` stash identity
  - Hook names and argument shapes declared by `PickleRunnerHookSpec`
  - Public decorators collected by `collect_hook_public_symbols()`

## Protected Hook Symbols

- `hook:pytest_bdd_before_scenario`
- `hook:pytest_bdd_run_scenario`
- `hook:pytest_bdd_after_scenario`
- `hook:pytest_bdd_run_step`
- `hook:pytest_bdd_before_step`
- `hook:pytest_bdd_before_step_call`
- `hook:pytest_bdd_after_step`
- `hook:pytest_bdd_step_error`
- `hook:pytest_bdd_step_func_lookup_error`
- `hook:pytest_bdd_match_step_definition_to_step`
- `hook:pytest_bdd_get_step_caller`
- `hook:pytest_bdd_get_step_dispatcher`
- `hook:pytest_bdd_attach`
- `decorator:after_mark`
- `decorator:after_tag`
- `decorator:around_mark`
- `decorator:around_tag`
- `decorator:before_mark`
- `decorator:before_tag`

## Non-Breaking Refactor Commitments

1. Internal lifecycle access may move from nullable getters to centralized lifecycle guards and dedicated Empty-State Objects, but public hook consumers continue to receive `run` in the same places.
2. The strict non-null refactor may add internal guard or Empty-State Object types, but it MUST NOT remove or rename protected hook/plugin symbols.
3. The refactor may strengthen runtime diagnostics when lifecycle misuse occurs, but it MUST preserve valid successful flows and public symbol compatibility.

## Validation Evidence

- `src/pytest_bdd/plugin/pickle_runner/api_compatibility.py`
- `tests/hook/test_run_fixture_stash.py`
- `tests/feature/test_run_hooks.py`
- `tests/contract/test_run_contract.py`
- `tests/compatibility/`
