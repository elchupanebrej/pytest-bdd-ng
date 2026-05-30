# Gap Proposal Document

## Existing Feature File Audit
| File | Status | Issues |
|------|--------|--------|
| features/01 Tutorial/01 Launch.feature.md | pass | None |
| features/02 Feature/01 Non-strict gherkin.feature.md | pass | None |
| features/02 Feature/02 Tag conversion.feature.md | pass | None |
| features/02 Feature/03 Markdown parsing.feature.md | pass | None |
| features/02 Feature/04 Localization.feature.md | fail | Missing '# Feature:' heading |
| features/02 Feature/05 Rule.feature.md | pass | None |
| features/02 Feature/06 Tag.feature.md | fail | Missing '## Scenario:' subheading |
| features/02 Feature/07 Description.feature.md | pass | None |
| features/02 Feature/08 Error reporting.feature.md | pass | None |
| features/02 Feature/09 Load/01 Scenario without steps.feature.md | pass | None |
| features/02 Feature/09 Load/02 Scenario search from base url.feature.md | fail | Missing '# Feature:' heading |
| features/02 Feature/09 Load/03 Scenario function loader.feature.md | pass | None |
| features/02 Feature/09 Load/04 HTTP feature loading.feature.md | pass | None |
| features/02 Feature/09 Load/05 Autoload.feature.md | fail | Missing '## Scenario:' subheading |
| features/02 Feature/09 Load/06 Feature base directory resolution.feature.md | fail | Missing '## Scenario:' subheading |
| features/02 Feature/09 Load/07 Scenario search from base directory.feature.md | pass | None |
| features/02 Feature/09 Load/08 Batch collection.feature.md | fail | Missing '## Scenario:' subheading |
| features/03 Scenario/01 Scenario binding.feature.md | pass | None |
| features/03 Scenario/02 Tag.feature.md | pass | None |
| features/03 Scenario/03 Description.feature.md | pass | None |
| features/03 Scenario/04 Tag filtering.feature.md | pass | None |
| features/03 Scenario/05 Alias.feature.md | pass | None |
| features/03 Scenario/06 Scenarios loader.feature.md | pass | None |
| features/03 Scenario/07 Background.feature.md | pass | None |
| features/03 Scenario/08 Outline/01 Runtime expansion.feature.md | pass | None |
| features/03 Scenario/08 Outline/02 Examples Tag.feature.md | fail | Missing '## Scenario:' subheading |
| features/03 Scenario/08 Outline/03 Empty values.feature.md | pass | None |
| features/04 Step/01 Doc string.feature.md | pass | None |
| features/04 Step/02 Data table.feature.md | pass | None |
| features/04 Step/03 Step definition bounding.feature.md | pass | None |
| features/04 Step/04 Step lifecycle and errors.feature.md | pass | None |
| features/05 Step definition/01 Pytest fixtures substitution.feature.md | pass | None |
| features/05 Step definition/02 Target fixtures specification.feature.md | pass | None |
| features/05 Step definition/03 Parameters/01 Conversion.feature.md | pass | None |
| features/05 Step definition/03 Parameters/02 Parsing by custom parser.feature.md | pass | None |
| features/05 Step definition/03 Parameters/03 Injection as fixtures.feature.md | pass | None |
| features/05 Step definition/03 Parameters/04 Parsing.feature.md | fail | Missing '## Scenario:' subheading |
| features/05 Step definition/03 Parameters/05 Defaults.feature.md | pass | None |
| features/06 StructBDD/01 Steps.feature.md | pass | None |
| features/07 Report/01 Gherkin terminal reporter.feature.md | pass | None |
| features/07 Report/02 Gathering.feature.md | pass | None |
| features/07 Report/03 Allure scenario.feature.md | pass | None |
| features/07 Report/04 Allure outline.feature.md | pass | None |
| features/07 Report/05 Cucumber JSON reporter.feature.md | pass | None |
| features/07 Report/07 xdist HTML reporting.feature.md | pass | None |
| features/07 Report/08 xdist remote network reporting.feature.md | pass | None |
| features/07 Report/09 Cucumber formatter reports.feature.md | pass | None |

## Duplicate Scenarios
No duplicate scenarios found.

## Missing Step Definitions
- And File "Passing.feature" with content:
- And File "conftest.py" with content:
- And File "no_strict_scenario.feature" with content:
- And File "out.html" is not empty
- And File "out.json" is not empty
- And File "pytest.ini" with content:
- And File "report.json" contains the line "JSON formatter payload"
- And File "report.json" is not empty
- And File "report.xml" contains the line "JUnit formatter payload"
- And File "report.xml" is not empty
- And File "standalone-usage.json" contains the line "Usage JSON formatter payload"
- And File "standalone-usage.json" is not empty
- And File "standalone.json" contains the line "JSON formatter payload"
- And File "subfolder_test.feature" with content:
- And File "tags.feature" with content:
- And File "tags_after_background.feature" with content:
- And File "test.feature" with content:
- And File "test_alias.py" with content:
- And File "test_background.py" with content:
- And File "test_cukes.py" with content:
- And File "test_feature.py" with content:
- And File "test_http.py" with fixture templated content:
- And File "test_no_strict.py" with content:
- And File "test_not_found.py" with content:
- And File "test_outline.py" with content:
- And File "test_report.py" with content:
- And File "test_sample.py" with content:
- And File "test_scenario_load.py" with fixture templated content:
- And File "test_scenarios.py" with content:
- And File "test_simple.py" with content:
- And File "usage.json" contains the line "Usage JSON formatter payload"
- And File "usage.json" is not empty
- And File "usage.txt" contains the line "Usage: Given a passing step x1; Given a failing step x1"
- And File "usage.txt" is not empty
- And I append 2 to the list
- And I append 3 to the list
- And JSON file "out.json" jq query ".[0].elements[0].steps[0].result.status" returns "passed"
- And JSON file "out.json" jq query ".[0].elements[1].steps[0].result.status" returns "failed"
- And Report "messages.ndjson" parsable into messages
- And there is a list
- But the list should be [1, 2, 3]
- Failing step
- Given File "Another.passing.feature" with content:
- Given File "Another.passing.feature.md" with content:
- Given File "Both.feature" with content:
- Given File "Cucumber.feature" with content:
- Given File "Description.feature" with content:
- Given File "Example.feature" with content:
- Given File "Failed.feature" with content:
- Given File "Freshness.feature" with content:
- Given File "Localized.feature" with content:
- Given File "Parametrized.feature" with content:
- Given File "Passed.feature" with content:
- Given File "Passing.feature" in the temporary path with content:
- Given File "Passing.feature" with content:
- Given File "Steps.feature" with content:
- Given File "Third.passing.feature" with content:
- Given File "alias.feature" with content:
- Given File "background.feature" with content:
- Given File "conftest.py" with content:
- Given File "missing.feature" with content:
- Given File "no_strict_background.feature" with content:
- Given File "not_found.feature" with content:
- Given File "outline.feature" with content:
- Given File "pytest.ini" with content:
- Given File "pytest.ini" with fixture templated content:
- Given File "reporting.feature" with content:
- Given File "rule.feature" with content:
- Given File "simple.feature" with content:
- Given File "steps.bdd.yaml" with content:
- Given File "steps.feature" with content:
- Given File "steps.feature.md" with content:
- Given File "test.feature" with content:
- Given File "test_explicit.py" with content:
- Given File "test_freshness.py" with content:
- Given File "test_none.py" with content:
- Given File "wrong.feature" with content:
- Given I have a foo fixture with value "foo"
- Given Localserver endpoint "/feature" responding content:
- Given Localserver endpoint "/features/Passing.feature" responding content:
- Given Passing step
- I check feature description
- I check pocket I found cucumber there
- I check scenario description
- I check step datatable
- I check step docstring
- I do boom (alias of crash)
- I do crash (which is 2)
- I do nothing
- I do nothing again
- I do something else with A
- I do something else with B
- I do something with A
- I eat {var} cucumbers
- I have 42 cukes in my belly
- I have 6 Euro
- I have A
- I have B
- I have a bar
- I have a baz
- I have a cucumber
- I have a failing bar
- I have a fresh cucumber
- I have a pickle
- I have a rotten cucumber
- I have a salted cucumber
- I have a wallet
- I have an empty list
- I have an old pickle
- I have bar (alias of foo) in my list
- I have foo (which is 1) in my list
- I lose 3 Euro
- I lost everything
- I make no mistakes
- I make no mistakes again
- I pay 2 Euro
- I produce failed test
- I produce passed test
- I produce {var} test
- I should have 1 Euro
- I should have 999999 Euro
- I should have {var} cucumbers
- Passing step
- Step counter
- Step is executed by aliased step decorator
- Step is executed by given step decorator
- Step is executed by liberal given decorator
- Step is executed by liberal step decorator
- Step is executed by liberal then decorator
- Step is executed by liberal when decorator
- Step is executed by plain step decorator
- Step is executed by then step decorator
- Step is executed by when step decorator
- Taste of cucumber is salt
- Then File "out.html" is not empty
- Then File "out.ndjson" has at least "15" lines
- Then File "standalone.json" is not empty
- Then Report "out.ndjson" parsable into messages
- Then foo should have value "foo"
- When I append 1 to the list
- When run `python -m pytest_bdd.script.render_cucumber_formatters --messages-ndjson messages.ndjson --cucumber-summary --cucumber-json=standalone.json --cucumber-usage-json=standalone-usage.json`
- a
- a background step with multiple lines:
- a failing step
- a passing step
- ab
- b
- bar
- baz
- c
- caa
- cab
- ca{var}
- fb
- foo
- foo has a value "bar"
- foo has a value "dummy"
- foo has no value "bar"
- foo has not a value "baz"
- foo is not boolean
- foo should have value "bar"
- foo should have value "dummy"
- foo should not have value "bar"
- found
- my list should be [1, 1, 2, 2]
- something about B
- something else about A and B
- something else about B
- the bar is accessed
- there are "16" passed liberal steps
- there are "4" passed aliased steps
- there are 10 cucumbers
- there are passed steps by kind:
- there are {var} cucumbers
- there is a bar
- there is a foo with value 42
- there is a second foo with value 43
- undefined step
- world explodes

## Coverage Gaps by Sub-Phase

### 8a (Core)
Missing coverage for:
- Go parser
- Tag expressions
- Heading validation
- Mimetype
- StructBDD edge cases

### 8b (Formatters)
Missing coverage for:
- cucumber_junit
- cucumber_progress
- cucumber_progress_bar
- cucumber_snippets
- cucumber_summary
- cucumber_usage
- cucumber_usage_json

### 8c (Plugins)
Missing coverage for:
- code_generator
- scenario_reporter
- compatibility layer behaviors
- collector_batch edge cases

## Proposed Step Definition Files

The following step definition files need to be created with their respective step patterns:

- `tests/e2e/steps_go_parser.py`: "Go parser shared library is built", "Go parser is not available", "Go parser version is logged"
- `tests/e2e/steps_tag_expressions.py`: "Tag expression evaluates to true/false for marks", "Complex boolean tag expression"
- `tests/e2e/steps_heading_validation.py`: "Feature has empty heading", "Heading validation policy is enforced"
- `tests/e2e/steps_mimetype.py`: "File extension resolves to mimetype", "Mimetype is {value}"
- `tests/e2e/steps_struct_bdd.py`: "StructBDD format is {yaml|json|hocon|toml}", "StructBDD parse error occurs"
- `tests/e2e/steps_formatters.py`: "Cucumber formatters are available", "File contains the line {pattern}", "Formatter output contains {element}"
- `tests/e2e/steps_code_generator.py`: "Code generator produces output", "Generated code contains"
- `tests/e2e/steps_scenario_reporter.py`: "Scenario reporter outputs", "Attachment is recorded"
- `tests/e2e/steps_compatibility.py`: "Python version is {version}", "Pytest version compatibility"
- `tests/e2e/steps_batch_collection.py`: "Batch collection cache is used", "Batch collection flag is set"

## Proposed New Feature Files

The following directories and files will be created:

- `features/08 Go Parser/01 Go parser backend.feature.md`
- `features/09 Tag Expressions/01 Tag expression evaluation.feature.md`
- `features/10 Heading Validation/01 Heading validation.feature.md`
- `features/11 Mimetype/01 Mimetype detection.feature.md`
- `features/06 StructBDD/02 StructBDD edge cases.feature.md`
- `features/12 Formatters/01 JUnit XML reporter.feature.md`
- `features/12 Formatters/02 Progress formatters.feature.md`
- `features/12 Formatters/03 Snippets formatter.feature.md`
- `features/12 Formatters/04 Summary formatter.feature.md`
- `features/12 Formatters/05 Usage statistics.feature.md`
- `features/13 Code Generator/01 Code generation.feature.md`
- `features/14 Scenario Reporter/01 Scenario reporting.feature.md`
- `features/15 Compatibility/01 Python version compatibility.feature.md`
- `features/16 Batch Collection/01 Batch collection edge cases.feature.md`

## Execution Order

1. Audit existing feature files and produce gap proposal
2. Generate step definition stubs in `tests/e2e/`
3. Write new `.feature.md` files
4. Run full test suite to ensure zero failures


## Applied Fixes
- `features/02 Feature/04 Localization.feature.md`: Added missing `# Feature:` heading
- `features/02 Feature/06 Tag.feature.md`: Added missing `## Scenario:` subheading
- `features/02 Feature/09 Load/02 Scenario search from base url.feature.md`: Added missing `# Feature:` heading
- `features/02 Feature/09 Load/05 Autoload.feature.md`: Added missing `## Scenario:` subheading
- `features/02 Feature/09 Load/06 Feature base directory resolution.feature.md`: Added missing `## Scenario:` subheading
- `features/02 Feature/09 Load/08 Batch collection.feature.md`: Added missing `## Scenario:` subheading
- `features/03 Scenario/08 Outline/02 Examples Tag.feature.md`: Added missing `## Scenario:` subheading
- `features/05 Step definition/03 Parameters/04 Parsing.feature.md`: Added missing `## Scenario:` subheading
