# Cucumber JSON example

This consumer project uses pytest-cuke's public step decorators and autoloads
the `.feature` file from `features/`. Its feature demonstrates feature and Rule
backgrounds, a doc string, a data table, an outline, tags, and an attachment.

Install pytest-cuke, Node.js, and the pinned official formatter, then run the
feature from this directory:

```sh
python -m pip install 'pytest-cuke>=2.3.1'
npm install --no-save --no-package-lock '@cucumber/cucumber@13.3.0'
python -m pytest --cuke-json=report.json -q
```

The E2E suite copies this project into a fresh installed consumer and runs it
with the same formatter version. It also replays a checked-in fixed Messages
stream through the installed formatter catalog and compares the output exactly
with its golden artifact. The live report separately checks that step durations
are present and nonnegative.
