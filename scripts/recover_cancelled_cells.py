"""Re-run cancelled matrix cells after a finished run, then the aggregate proof."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any

RunGh = Callable[[list[str]], str]


def _run_gh(arguments: list[str]) -> str:
    gh = shutil.which("gh")
    if gh is None:
        raise RuntimeError("the gh command is required to recover matrix runs")
    error = ""
    for delay in (0, 5, 15):
        if delay:
            time.sleep(delay)
        # The arguments are the fixed API endpoints this script owns.
        result = subprocess.run([gh, *arguments], capture_output=True, text=True, check=False)  # noqa: S603
        if not result.returncode:
            return result.stdout
        error = result.stderr.strip()
    raise RuntimeError(f"gh {' '.join(arguments)} failed: {error}")





class GithubRun:
    """Minimal GitHub Actions API surface used by recovery."""

    def __init__(self, repository: str, run_id: int, run_gh: RunGh = _run_gh) -> None:
        self.repository = repository
        self.run_id = run_id
        self._run_gh = run_gh

    def _api(self, endpoint: str, *arguments: str) -> str:
        return self._run_gh(["api", f"repos/{self.repository}/{endpoint}", *arguments])

    def status(self) -> dict[str, Any]:
        payload = json.loads(self._api(f"actions/runs/{self.run_id}"))
        if not isinstance(payload, dict):
            raise ValueError(f"run {self.run_id} did not return a JSON object")
        return payload

    def jobs(self) -> list[dict[str, Any]]:
        payload = self._api(f"actions/runs/{self.run_id}/jobs?per_page=100", "--paginate", "--jq", ".jobs[]")
        jobs = [json.loads(line) for line in payload.splitlines() if line.strip()]
        if not all(isinstance(job, dict) for job in jobs):
            raise ValueError("GitHub job listing entry is not a JSON object")
        return jobs

    def rerun_failed(self) -> None:
        self._api(f"actions/runs/{self.run_id}/rerun-failed-jobs", "--method", "POST")


def _wait_for_run(
    run: GithubRun,
    *,
    attempt_before: int,
    timeout: float,
    poll_interval: float,
    log: Callable[[str], None],
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while True:
        payload = run.status()
        if int(payload.get("run_attempt", 0)) > attempt_before and payload.get("status") == "completed":
            return run.jobs()
        if time.monotonic() >= deadline:
            raise RuntimeError(f"timed out after {timeout:.0f}s waiting for run {run.run_id}")
        log("waiting for the recovered run to complete")
        time.sleep(poll_interval)


def recover(
    run: GithubRun,
    *,
    aggregate_job: str,
    timeout: float,
    poll_interval: float,
    log: Callable[[str], None] = print,
) -> int:
    payload = run.status()
    if payload.get("status") != "completed":
        print(
            f"recover: run {run.run_id} is {payload.get('status')!r}; refusing to rerun cells before the run completes",
            file=sys.stderr,
        )
        return 2

    cancelled = [
        str(job["name"])
        for job in run.jobs()
        if job.get("status") == "completed"
        and job.get("conclusion") == "cancelled"
        and job.get("name") != aggregate_job
    ]
    if not cancelled:
        log("recover: no cancelled cells to recover")
        return 0

    # GitHub rejects a second job re-run once the new attempt starts, so recover
    # through the failed-jobs re-run. It re-runs every non-success job, which
    # covers these cells and the aggregate proof, and keeps completed outputs.
    log(f"recover: re-running {len(cancelled)} cancelled cell(s): {', '.join(cancelled)}")
    run.rerun_failed()
    jobs = _wait_for_run(
        run,
        attempt_before=int(payload.get("run_attempt", 1)),
        timeout=timeout,
        poll_interval=poll_interval,
        log=log,
    )

    by_name = {str(job.get("name")): job for job in jobs}
    failed = [name for name in cancelled if by_name.get(name, {}).get("conclusion") != "success"]
    if failed:
        print(f"recover: recovered cells did not pass: {', '.join(failed)}", file=sys.stderr)
        return 1

    aggregate = by_name.get(aggregate_job)
    if aggregate is None:
        print(f"recover: run {run.run_id} has no {aggregate_job!r} job", file=sys.stderr)
        return 1
    if aggregate.get("conclusion") != "success":
        print(f"recover: aggregate proof did not pass: {aggregate.get('conclusion')!r}", file=sys.stderr)
        return 1
    log("recover: recovery complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="owner/name of the repository holding the run")
    parser.add_argument("--run-id", required=True, type=int, help="finished workflow run to recover")
    parser.add_argument("--aggregate-job", default="aggregate-proof")
    parser.add_argument("--timeout-minutes", type=float, default=480)
    parser.add_argument("--poll-seconds", type=float, default=30)
    args = parser.parse_args()

    try:
        return recover(
            GithubRun(args.repository, args.run_id),
            aggregate_job=args.aggregate_job,
            timeout=args.timeout_minutes * 60,
            poll_interval=args.poll_seconds,
        )
    except (RuntimeError, ValueError, KeyError) as error:
        print(f"recover: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
