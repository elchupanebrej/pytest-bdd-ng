# Quickstart: Distributed Reporting Stream

## Preconditions

- Repository root: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng`
- Branch: `011-merge-xdist-reporting`
- Python environment: `conda` env `pytest-bdd-ng-py314`

> Current workflow:
> - Python environment: repository synced with `uv sync --extra test --extra testenv --extra testtypes`

- Docker Engine or Docker Desktop available for remote-worker acceptance coverage
- GitHub CI entrypoint: `.github/workflows/main.yml` installs `tox` and can execute the Linux remote acceptance environments defined in `tox.ini`

## 1. Validate contract and transport-shape rules

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/messages/test_xdist_remote_transport.py \
#   tests/messages/test_xdist_message_consolidation.py \
#   tests/messages/test_message_validation.py \
#   tests/contract/test_xdist_consolidated_stream_contract.py \
#   tests/contract/test_xdist_worker_controller_boundary_contract.py -q
uv run python -m pytest \
  tests/messages/test_xdist_remote_transport.py \
  tests/messages/test_xdist_message_consolidation.py \
  tests/messages/test_message_validation.py \
  tests/contract/test_xdist_consolidated_stream_contract.py \
  tests/contract/test_xdist_worker_controller_boundary_contract.py -q
```

Expected:
- worker/controller transfers are expressed as execnet-serializable xdist events;
- structural duplicates are suppressed without removing real runtime attempts;
- manifest handling distinguishes complete and interrupted workers;
- canonical ID remapping prevents orphaned lifecycle references.
- the same validation path remains suitable for GitHub CI execution through repository-supported `tox` entrypoints.

## 2. Validate local xdist `popen` regression

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/messages/test_messages_feature_suite.py \
#   tests/e2e/test_xdist_message_aggregation.py -q
uv run python -m pytest \
  tests/messages/test_messages_feature_suite.py \
  tests/e2e/test_xdist_message_aggregation.py -q
```

Expected:
- local `-n` execution still produces exactly one final NDJSON artifact;
- controller and worker structural duplicates collapse to one canonical structure;
- runtime worker participation remains traceable in the final stream.

## 3. Validate remote `socket` worker aggregation

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_xdist_remote_message_aggregation.py -k socket -q
uv run python -m pytest \
  tests/e2e/test_xdist_remote_message_aggregation.py -k socket -q
```

Expected:
- controller and workers run in isolated containers or remote processes;
- no worker-local path is read by the controller;
- reporting chunks arrive only through xdist/execnet-managed communication;
- exactly one final NDJSON stream is written by the controller.

## 4. Validate proxy `via` gateway aggregation

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_xdist_remote_message_aggregation.py -k via -q
uv run python -m pytest \
  tests/e2e/test_xdist_remote_message_aggregation.py -k via -q
```

Expected:
- the run succeeds when workers are routed through an xdist proxy gateway;
- no direct reporter-managed socket from worker to controller is required;
- deterministic consolidation still holds when event arrival order differs across routed workers.

## 5. Validate remote `ssh` aggregation

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/e2e/test_xdist_remote_message_aggregation.py -k ssh -q
uv run python -m pytest \
  tests/e2e/test_xdist_remote_message_aggregation.py -k ssh -q
```

Expected:
- reporting works through xdist's SSH gateway family without relying on `rsync`;
- the final stream remains controller-owned and validator-compatible;
- worker interruption still yields explicit partial-run diagnostics when applicable.

## 6. Validate fail-fast compatibility handling

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/messages/test_xdist_remote_transport.py -k incompat -q
uv run python -m pytest \
  tests/messages/test_xdist_remote_transport.py -k incompat -q
```

Expected:
- unsupported xdist versions or channel capabilities produce an explicit diagnostic;
- the reporter does not silently fall back to a side-channel TCP listener or worker-local file reads.

## 7. Validate single-process regression

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest \
#   tests/messages/test_messages.py \
#   tests/messages/test_message_attachments.py \
#   tests/feature/test_report.py -q
uv run python -m pytest \
  tests/messages/test_messages.py \
  tests/messages/test_message_attachments.py \
  tests/feature/test_report.py -q
```

Expected:
- non-xdist reporting behavior remains unchanged;
- the xdist-specific channel adapter path stays inactive outside distributed runs.

## 8. Validate GitHub CI-aligned tox entrypoints

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-xdist-remote-socket-lin
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-xdist-remote-via-lin
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-xdist-remote-ssh-lin
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-lin
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-via-lin
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-ssh-lin
```

Expected:
- each environment invokes the repository-supported remote acceptance coverage through `tox`;
- the Linux GitHub CI path can call the same entrypoints instead of maintaining workflow-only test commands;
- remote acceptance remains split by gateway mode for clearer CI diagnostics.

## 9. Helper implementation boundary

- Keep orchestration and report verification logic in Python modules under `tests/` wherever practical.
- Retain bash only for thin shell-specific container entrypoints such as `tests/e2e/fixtures/remote_xdist/controller-entrypoint.sh` and `tests/e2e/fixtures/remote_xdist/worker-entrypoint.sh`.
- Prefer extending `tests/e2e/test_xdist_remote_message_aggregation.py` and `tests/e2e/fixtures/remote_xdist/verify_report.py` before adding new multi-step bash helpers.
