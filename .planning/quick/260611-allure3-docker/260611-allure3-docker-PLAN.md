---
phase: quick
plan: 260611-allure3-docker
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pytest_bdd/testing/docker.py
  - tests/cases/contract/allure/test_allure_consumption_ui.py
  - tests/cases/contract/cck/conftest.py
  - tests/cases/e2e/steps_allure_converter.py
  - tests/cases/e2e/steps_cck_allure.py
  - features/17 Allure Converter/1 Allure converter.feature.md
autonomous: true
requirements: []
user_setup: []
must_haves:
  truths:
    - "Local allure3-local:latest Docker image is built from tests/assets/docker/allure3/Dockerfile"
    - "The docker command in tests resolves allure3-local:latest and specifies /allure-results as input"
  artifacts:
    - path: "tests/assets/docker/allure3/Dockerfile"
      provides: "Dockerfile for local Allure 3 image"
---

<objective>
Replace the Allure 2 docker image frankescobar/allure-docker-service:2.27.0 with a custom local Node-based Allure 3 Docker image.
</objective>

<execution_context>
@C:/Users/bulky/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/bulky/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/260611-allure3-docker/260611-allure3-docker-CONTEXT.md
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create allure3 Dockerfile and add ensure_allure3_image utility</name>
  <files>
    tests/assets/docker/allure3/Dockerfile
    src/pytest_bdd/testing/docker.py
  </files>
  <action>
    1. Create tests/assets/docker/allure3/Dockerfile that installs allure globally.
    2. Add ensure_allure3_image() to src/pytest_bdd/testing/docker.py to build allure3-local:latest.
  </action>
  <verify>
    <automated>uv run python -c "from pytest_bdd.testing.docker import ensure_allure3_image; print('import OK')"</automated>
  </verify>
  <done>
    - Dockerfile created.
    - ensure_allure3_image function added to src/pytest_bdd/testing/docker.py.
  </done>
</task>

<task type="auto">
  <name>Task 2: Replace Docker image references in test files</name>
  <files>
    tests/cases/contract/allure/test_allure_consumption_ui.py
    tests/cases/contract/cck/conftest.py
    tests/cases/e2e/steps_allure_converter.py
    tests/cases/e2e/steps_cck_allure.py
    features/17 Allure Converter/1 Allure converter.feature.md
  </files>
  <action>
    1. Modify conftest.py and test_allure_consumption_ui.py to use allure3-local:latest and call ensure_allure3_image().
    2. Modify steps_allure_converter.py and steps_cck_allure.py to build/use allure3-local:latest and pass /allure-results as input.
    3. Modify features/17 Allure Converter/1 Allure converter.feature.md to match the new image name and command.
  </action>
  <verify>
    <automated>uv run ruff check tests/cases/contract/allure/test_allure_consumption_ui.py tests/cases/contract/cck/conftest.py tests/cases/e2e/steps_allure_converter.py tests/cases/e2e/steps_cck_allure.py</automated>
  </verify>
  <done>
    - All files modified to use allure3-local:latest.
    - Input results directory passed correctly.
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify Allure tests pass</name>
  <files>
    tests/cases/contract/allure/test_allure_consumption_ui.py
  </files>
  <action>
    Run contract tests to verify everything is green.
  </action>
  <verify>
    <automated>uv run pytest tests/cases/contract/allure/test_schema_validation.py</automated>
  </verify>
  <done>
    - Tests run successfully.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries
N/A
</threat_model>

<verification>
- pytest run: `uv run pytest tests/cases/contract/allure/test_schema_validation.py`
</verification>

<success_criteria>
- All tests are green.
- allure3-local:latest image is built and used.
</success_criteria>

<output>
Create .planning/quick/260611-allure3-docker/260611-allure3-docker-SUMMARY.md when done.
</output>
