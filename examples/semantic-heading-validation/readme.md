# Semantic heading validation example

This standalone project runs one normal autoloaded scenario and keeps a second
feature file with an empty Scenario title for CLI validation examples.

Install the checkout and pytest from this directory, then run the example:

```sh
python -m pip install -r requirements.txt
python -m pytest
cuke validate features --json
```

The valid feature is discovered recursively by the validator. The invalid
sample is kept in a separate directory so the normal example passes:

```sh
cuke validate invalid-features --json
cuke validate invalid-features --baseline-audit --json
cuke validate invalid-features --no-fail-on-violation --json
```

The first command returns non-zero and identifies `blank-scenario.feature` with
`EMPTY_HEADING_TITLE`. The baseline audit returns non-zero with the policy/run
IDs, violation count, and compliance result. Advisory mode reports the same
finding with a zero exit status. To enforce the policy during pytest
collection, run:

```sh
python -m pytest --cuke-autoload --cuke-features-dir=invalid-features --cuke-strict
```

Strict mode rejects the parsed heading during collection before any scenario
step executes.
