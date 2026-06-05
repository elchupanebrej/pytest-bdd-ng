---
phase: quick
plan: 260603-ssh
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/assets/docker/remote_xdist/controller_entrypoint.py
autonomous: true
requirements: []
user_setup: []
must_haves:
  truths:
    - "Using absolute Python path (/usr/local/bin/python3.14) for SSH readiness checks in controller_entrypoint.py"
    - "Using absolute Python path (/usr/local/bin/python3.14) for execnet SSH arguments in controller_entrypoint.py"
    - "Formatting is compliant with ruff rules (no E501 line length violations)"
  artifacts:
    - path: "tests/assets/docker/remote_xdist/controller_entrypoint.py"
      provides: "Updated Python path for SSH connections"
  key_links:
    - from: "tests/assets/docker/remote_xdist/controller_entrypoint.py"
      to: "docker compose"
      via: "ssh python interpreter path resolution"
---

<objective>
Fix the failing GHA CI matrix cell `test-xdist-remote (ubuntu-latest, ssh)` by updating `tests/assets/docker/remote_xdist/controller_entrypoint.py` to use `/usr/local/bin/python3.14` for all SSH executions. This prevents PATH resolution errors in non-interactive SSH shells where `/usr/local/bin` is not on the default path.
</objective>

<execution_context>
@C:/Users/bulky/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/bulky/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/260603-ssh/260603-ssh-CONTEXT.md
@.planning/STATE.md
@tests/assets/docker/remote_xdist/controller_entrypoint.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update controller_entrypoint.py to use absolute python path for SSH</name>
  <files>
    tests/assets/docker/remote_xdist/controller_entrypoint.py
  </files>
  <action>
Modify tests/assets/docker/remote_xdist/controller_entrypoint.py to specify the absolute path `/usr/local/bin/python3.14` in both `ssh_ready` (line 49) and `_default_xdist_args` for the `ssh` mode (line 103). Ensure formatting is ruff-compliant by splitting the long line returned for SSH mode.

Command:
None (apply file replacement edit).
  </action>
  <verify>
    <automated>uv run ruff check tests/assets/docker/remote_xdist/controller_entrypoint.py; uv run ruff format --check tests/assets/docker/remote_xdist/controller_entrypoint.py</automated>
  </verify>
  <done>
- Absolute Python path used in controller_entrypoint.py
- Ruff check passes (no E501 errors)
- Ruff format check passes
  </done>
</task>

<task type="auto">
  <name>Task 2: Verify local tests pass</name>
  <files>
    tests/cases/external/support/test_docker_wsl2.py
    tests/cases/external/e2e/test_xdist_remote_message_aggregation.py
  </files>
  <action>
Run wsl2 docker tests and non-Docker xdist tests to verify the changes do not cause regression.

Commands:
1. `uv run pytest tests/cases/external/support/test_docker_wsl2.py`
2. `uv run pytest tests/cases/external/e2e/test_xdist_remote_message_aggregation.py -k "socket or via"`
  </action>
  <verify>
    <automated>uv run pytest tests/cases/external/support/test_docker_wsl2.py</automated>
  </verify>
  <done>
- WSL2 docker mock tests pass
- Local socket/via remote xdist tests pass
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| container -> worker | SSH connection from controller to worker containers must succeed |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-quick-01 | Tampering | Incorrect path breaks local execution | mitigate | Absolute path `/usr/local/bin/python3.14` matches exact standard path in `python:3.14-slim` container |
</threat_model>

<verification>
- Ruff checks: `uv run ruff check tests/assets/docker/remote_xdist/controller_entrypoint.py`
- Format checks: `uv run ruff format --check tests/assets/docker/remote_xdist/controller_entrypoint.py`
- Test run 1: `uv run pytest tests/cases/external/support/test_docker_wsl2.py`
- Test run 2: `uv run pytest tests/cases/external/e2e/test_xdist_remote_message_aggregation.py -k "socket or via"`
</verification>

<success_criteria>
- SSH connections use the absolute python path `/usr/local/bin/python3.14`.
- Modified code is fully linted and formatted.
- Local tests pass.
</success_criteria>

<output>
Create `.planning/quick/260603-ssh/260603-ssh-SUMMARY.md` when done.
</output>
