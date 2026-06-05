# Quick Task 260603-ssh: Fix xdist ssh test fails on the CI - Context

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Task Boundary

Fix the failing `test-xdist-remote (ubuntu-latest, ssh)` matrix cell on GitHub Actions CI.

The root cause of the failure is that the sshd running on the worker containers starts a non-interactive shell, which has a restricted default system PATH that does not include `/usr/local/bin`. Since the official `python:3.14-slim` image installs the python interpreter at `/usr/local/bin/python3.14`, calling `ssh worker1 python3.14` fails with "command not found", causing the controller's SSH readiness verification and execnet connection setup to fail.

The fix is to use the absolute path `/usr/local/bin/python3.14` instead of `python3.14` in the controller's SSH readiness check and execnet SSH gateway arguments inside `controller_entrypoint.py`.

</domain>

<decisions>
## Implementation Decisions

### Absolute Python Path for SSH
- Use the absolute path `/usr/local/bin/python3.14` for all SSH connections made from the controller container to the worker containers.
- This bypasses the restricted system PATH for non-interactive SSH shells and correctly locates the python executable.

### the agent's Discretion
- Only update controller_entrypoint.py since other modes (socket/via) do not run via SSH and inherit the container process environment where `/usr/local/bin` is already on the PATH.
- Break down long line returns in controller_entrypoint.py to prevent Ruff E501 linting errors.

</decisions>

<specifics>
## Specific Ideas

Use `/usr/local/bin/python3.14` in `tests/assets/docker/remote_xdist/controller_entrypoint.py`:
- In `ssh_ready`: `command = ["ssh", host, "/usr/local/bin/python3.14 -c 'print(1)'"]`
- In `_default_xdist_args`: `return ("--tx ssh=worker1//python=/usr/local/bin/python3.14//chdir=/app" " --tx ssh=worker2//python=/usr/local/bin/python3.14//chdir=/app")`

</specifics>

<canonical_refs>
## Canonical References

- PR #141 run 26870051920: `https://github.com/elchupanebrej/pytest-bdd-ng/actions/runs/26870051920/job/79242871796?pr=141`
- `tests/assets/docker/remote_xdist/controller_entrypoint.py`
- `tests/cases/external/support/test_docker_wsl2.py`

</canonical_refs>
