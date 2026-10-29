# Reporting Context

This glossary distinguishes saved Cucumber Messages conversion from Allure results produced during a live pytest run.

## Cucumber and Allure reporting

**Cucumber Messages stream**:
An ordered NDJSON record of Cucumber test structure and execution events.
_Avoid_: event log, report file

**Saved-stream conversion**:
Allure result artifacts created from a completed Cucumber Messages stream without collecting or executing its tests.
_Avoid_: replay, import run

**Native Allure reporting**:
Allure results created as pytest executes scenarios and emits their Cucumber Messages events.
_Avoid_: saved-stream conversion
