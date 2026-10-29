# Tolerant step failures

This standalone example shows a decorated step whose ordinary assertion failure
is ignored by policy while the following step runs. The failed step remains
visible in Cucumber Messages and Cucumber JSON.

Install the example dependencies, then run it from this directory:

```sh
python -m pip install -r requirements.txt
python -m pytest --cuke-messages-ndjson=messages.ndjson --cuke-json=cucumber.json
```

The pytest configuration selects the `ignored` policy. Only definitions marked
with `@tolerant` use that policy. Skips and missing step definitions keep their
normal outcomes.
