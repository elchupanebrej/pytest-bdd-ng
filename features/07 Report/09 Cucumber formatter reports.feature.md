# Feature: Cucumber formatter reports
  This feature documents how pytest-bdd-ng reuses cucumber-js formatters for
  console output, file output, and post-processing from an existing canonical
  NDJSON message stream. During a pytest run, every active formatter request
  consumes the live incremental message stream; during `pytest-xdist` runs,
  workers forward messages to the controller/main process and only that central
  authority renders formatter output.

## Background:
* Given File "reporting.feature" with content:

    ```gherkin
    Feature: Reporting sample
      Scenario: Passing scenario
        Given a passing step

      Scenario: Failing scenario
        Given a failing step
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("a passing step")
    def _pass():
        return "pass"


    @given("a failing step")
    def _fail():
        raise RuntimeError("boom")
    ```

* And File "test_report.py" with content:

    ```python
    from pytest_bdd import scenarios

    test_report = scenarios("reporting.feature")
    ```

## Scenario: Console formatter flags can be rendered during the pytest run

The following stdout formatters are supported:
`--cucumber-summary`, `--cucumber-progress`, `--cucumber-progress-bar`,
`--cucumber-snippets`, `--cucumber-pretty`, and `--cucumber-usage`.
Only one terminal-output formatter may be active in a single run, so this
example uses one representative formatter command. The formatter consumes the
same live stream that feeds any other active formatter requests. When one of
these terminal formatter flags is present, pytest-bdd-ng automatically disables
pytest capture for the run so the formatter owns terminal output without
requiring an extra `-s`.

* When run pytest

    | cli_args   | --cucumber-summary | -k | test_report.py |
    |------------|--------------------|----|----------------|
    | subprocess | true               |    |                |

* Then pytest exits with test failures

* And the renderer terminal output includes:

    | *Summary: 2 scenarios (1 passed, 1 failed)* |
    |---------------------------------------------|

## Scenario: File formatter flags can be rendered during the pytest run

The following file-oriented outputs are supported:
`--cucumber-json`, `--cucumber-junit`, `--cucumber-usage=<path>`, and
`--cucumber-usage-json`. These outputs are attached to the live stream during
the run and finalize their files when the formatter session closes.

* When run pytest

    | cli_args   | --cucumber-json=report.json | --cucumber-junit=report.xml | --cucumber-usage=usage.txt | --cucumber-usage-json=usage.json | -k | test_report.py |
    |------------|-----------------------------|-----------------------------|----------------------------|----------------------------------|----|----------------|
    | subprocess | true                        |                             |                            |                                  |    |                |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

* And File "report.json" is not empty
* And File "report.xml" is not empty
* And File "usage.txt" is not empty
* And File "usage.json" is not empty
* And File "report.json" contains the line "JSON formatter payload"
* And File "report.xml" contains the line "testsuite"
* And File "usage.txt" contains the line "Usage: Given a passing step x1; Given a failing step x1"
* And File "usage.json" contains the line "formatter"

## Scenario: Multiple cucumber formatter outputs can be requested in one run

One pytest execution may request a mix of console and file outputs from the
same live message stream, with file artifacts and terminal output remaining
consistent with the final canonical NDJSON report.

* When run pytest

    | cli_args   | --cucumber-summary | --cucumber-json=report.json | --cucumber-usage-json=usage.json | -k | test_report.py |
    |------------|--------------------|-----------------------------|----------------------------------|----|----------------|
    | subprocess | true               |                             |                                  |    |                |

* Then pytest exits with test failures

* And the renderer terminal output includes:

    | *Summary: 2 scenarios (1 passed, 1 failed)* |
    |---------------------------------------------|

* And File "report.json" is not empty
* And File "usage.json" is not empty
* And File "report.json" contains the line "JSON formatter payload"
* And File "usage.json" contains the line "formatter"

## Scenario: Existing NDJSON can be post-processed into formatter outputs

An already generated canonical `messages.ndjson` report can be reused later
without rerunning pytest. The replay path uses the standalone rendering
service and the canonical standalone formatter catalog rather than rebuilding
a fake in-process pytest runtime.

* When run pytest

    | cli_args   | --messages-ndjson=messages.ndjson | -k | test_report.py |
    |------------|-----------------------------------|----|----------------|
    | subprocess | true                              |    |                |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

* And Report "messages.ndjson" parsable into messages

* When run `python -m pytest_bdd.script.render_cucumber_formatters --messages-ndjson messages.ndjson --cucumber-summary --cucumber-json=standalone.json --cucumber-usage-json=standalone-usage.json`

* Then the renderer terminal output includes:

    | Summary: 2 scenarios (1 passed, 1 failed) |
    |-------------------------------------------|

* Then File "standalone.json" is not empty
* And File "standalone-usage.json" is not empty
* And File "standalone.json" contains the line "JSON formatter payload"
* And File "standalone-usage.json" contains the line "formatter"

## Scenario: Missing formatter packages are auto-installed on demand

* When run pytest

    | cli_args   | --cucumber-progress | -k | test_report.py |
    |------------|---------------------|----|----------------|
    | subprocess | true                |    |                |

* Then pytest exits with test failures
* And the renderer terminal output includes:

    | Installing missing global npm package(s) for cucumber formatter rendering (--cucumber-progress): @cucumber/cucumber |
    | Progress: .F |
