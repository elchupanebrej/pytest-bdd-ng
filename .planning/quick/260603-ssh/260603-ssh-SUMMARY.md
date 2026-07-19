---
status: complete
plan: 260603-ssh
date: 2026-06-03
---

# Quick Task 260603-ssh: Fix xdist ssh test fails on the CI - Summary

## Fix Status

| Area | Status | Details |
|------|--------|---------|
| SSH python path | FIXED | Updated `controller_entrypoint.py` to use `/usr/local/bin/python3.14` |
| Code quality | PASSED | Linted and formatted using `ruff` |
| Local tests | PASSED | `test_docker_wsl2.py` and local remote xdist tests (socket/via) pass |

## Verification Details

1. **Ruff checks:**
   `uv run ruff check tests/assets/docker/remote_xdist/controller_entrypoint.py` returned `All checks passed!`.
2. **Ruff formatting:**
   `uv run ruff format --check tests/assets/docker/remote_xdist/controller_entrypoint.py` confirmed the file is already formatted.
3. **WSL2 Docker support tests:**
   `uv run pytest tests/cases/external/support/test_docker_wsl2.py` executed and all 54 tests passed.
4. **Local remote xdist aggregation tests:**
   `uv run pytest tests/cases/external/e2e/test_xdist_remote_message_aggregation.py -k "socket or via"` executed and all 6 tests passed.

## Lessons Learned

- **SSH Non-Interactive Shell PATH:** When SSH executes commands non-interactively (e.g. `ssh host command`), it does not source `/etc/profile` or `.bashrc` where `/usr/local/bin` is added to the PATH by Docker. Since the official Python Docker image installs python under `/usr/local/bin`, it is not visible on the default system path during SSH handshakes. Specifying the absolute path `/usr/local/bin/python3.14` is the correct and robust fix.
