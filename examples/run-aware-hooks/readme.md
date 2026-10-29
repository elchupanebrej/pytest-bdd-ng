# Run-aware hooks

This runnable consumer project demonstrates how a pytest-cuke plugin can inspect
the active feature, scenario, current step, and previous step through the
session-owned `RunContext`.

The root `conftest.py` loads `run_aware_plugin` with pytest's `pytest_plugins`
discovery. The plugin uses the public `(request, run)` hook context and reads
`run.feature`, `run.scenario`, `run.step`, and `run.previous_step`. Its reduced
hook implementations show that implementations may request only the arguments
they use. Matcher, caller, and dispatcher hooks return `None`, so pytest-cuke's
default behavior continues.

From this directory, install pytest-cuke and run the example:

```sh
python -m pip install -r requirements.txt
npm install --no-save --no-package-lock "@cucumber/cucumber@13.3.0"
python -m pytest --cuke-autoload --cuke-features-dir=features --cuke-summary
```

The plugin writes ordered hook observations to
`run-aware-observations.jsonl`. The first step in each scenario has no previous
step; later steps expose the immediately preceding step. The E2E suite copies
and executes this same checked-in example from an installed consumer. The
attachment scenario calls the public `attach` fixture; the consumer's
`pytest_cuke_attach` hook records its active run context and the attachment
body, media type, and file name.
