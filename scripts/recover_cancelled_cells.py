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
    # The arguments are the fixed API endpoints this script owns.
    result = subprocess.run([gh, *arguments], capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode:
        raise RuntimeError(f"gh {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout


def _decode_array_documents(text: str) -> list[list[dict[str, Any]]]:
    """Decode the concatenated JSON arrays `gh api --paginate` prints."""
    decoder = json.JSONDecoder()
    documents: list[list[dict[str, Any]]] = []
    index = 0
    while True:
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            return documents
        document, index = decoder.raw_decode(text, index)
        if not isinstance(document, list):
            raise ValueError("GitHub job listing page is not a JSON array")
        documents.append(document)


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
        payload = self._api(f"actions/runs/{self.run_id}/jobs?per_page=100", "--paginate")
        return [job for page in _decode_array_documents(payload) for job in page]

    def rerun(self, job_id: int) -> None:
        self._api(f"actions/jobs/{job_id}/rerun", "--method", "POST")


def _wait_for(
    run: GithubRun,
    job_ids: set[int],
    *,
    timeout: float,
    poll_interval: float,
    log: Callable[[str], None],
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while True:
        jobs = run.jobs()
        by_id = {int(job["id"]): job for job in jobs}
        pending = [job_id for job_id in job_ids if by_id.get(job_id, {}).get("status") != "completed"]
        if not pending:
            return jobs
        if time.monotonic() >= deadline:
            names = ", ".join(str(by_id.get(job_id, {}).get("name")) for job_id in pending)
            raise RuntimeError(f"timed out after {timeout:.0f}s waiting for {names}")
        log(f"waiting for {len(pending)} recovered job(s)")
        time.sleep(poll_interval)


def recover(  # noqa: PLR0911 - each guard answers with its own recovery outcome
    run: GithubRun,
    *,
    aggregate_job: str,
    timeout: float,
    poll_interval: float,
    log: Callable[[str], None] = print,
) -> int:
    status = run.status().get("status")
    if status != "completed":
        print(
            f"recover: run {run.run_id} is {status!r}; refusing to rerun cells before the run completes",
            file=sys.stderr,
        )
        return 2

    cells = [
        job
        for job in run.jobs()
        if job.get("status") == "completed"
        and job.get("conclusion") == "cancelled"
        and job.get("name") != aggregate_job
    ]
    if not cells:
        log("recover: no cancelled cells to recover")
        return 0

    for job in cells:
        log(f"recover: re-running cancelled cell {job.get('name')!r}")
        run.rerun(int(job["id"]))
    jobs = _wait_for(run, {int(job["id"]) for job in cells}, timeout=timeout, poll_interval=poll_interval, log=log)

    by_id = {int(job["id"]): job for job in jobs}
    failed = [job["name"] for job in cells if by_id[int(job["id"])].get("conclusion") != "success"]
    if failed:
        print(f"recover: recovered cells did not pass: {', '.join(failed)}", file=sys.stderr)
        return 1

    aggregate = next((job for job in jobs if job.get("name") == aggregate_job), None)
    if aggregate is None:
        print(f"recover: run {run.run_id} has no {aggregate_job!r} job", file=sys.stderr)
        return 1
    if aggregate.get("conclusion") == "success":
        log("recover: aggregate proof already passed")
        return 0

    log(f"recover: re-running aggregate proof {aggregate_job!r}")
    run.rerun(int(aggregate["id"]))
    jobs = _wait_for(run, {int(aggregate["id"])}, timeout=timeout, poll_interval=poll_interval, log=log)
    aggregate = next(job for job in jobs if job.get("name") == aggregate_job)
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
