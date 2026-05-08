"""Provide sync messages contract schemas helpers."""

import argparse
import filecmp
import importlib
import shutil
import stat
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol, cast

SCHEMA_PATH = Path(__file__).parent.parent / "model" / "message_jsonschema"
SCHEMA_REPOSITORY_URL = "https://github.com/cucumber/messages.git"
SCHEMA_REPOSITORY_FOLDER = Path("jsonschema", "src")


class _GitRemote(Protocol):
    def fetch(self, *args: object, **kwargs: object) -> object: ...


class _GitRemotes(Protocol):
    origin: _GitRemote


class _GitGit(Protocol):
    def config(self, *args: object, **kwargs: object) -> object: ...

    def checkout(self, *args: object, **kwargs: object) -> object: ...


class _GitRepo(Protocol):
    git: _GitGit
    remotes: _GitRemotes

    @classmethod
    def init(cls, path: Path) -> "_GitRepo": ...

    def create_remote(self, name: str, url: str) -> object: ...


class _GitModule(Protocol):
    Repo: type[_GitRepo]


def copy_schema_tree(source: Path, destination: Path) -> None:
    """Handle copy schema tree."""
    if destination.exists():
        destination.chmod(destination.stat().st_mode | stat.S_IWRITE)
    shutil.rmtree(str(destination), ignore_errors=True)
    shutil.copytree(str(source), str(destination))


def fetch_schema_tree(destination: Path) -> None:
    """Handle fetch schema tree."""
    from pytest_bdd.util.packaging import get_distribution_version

    git_module = cast("_GitModule", importlib.import_module("git"))
    tag_name = f"v{get_distribution_version('cucumber_messages')}"

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "messages"
        repo_path.mkdir(parents=True)
        repo = git_module.Repo.init(repo_path)
        repo.git.config("core.sparseCheckout", "true")
        repo.create_remote("origin", SCHEMA_REPOSITORY_URL)

        sparse_checkout_file = repo_path / ".git" / "info" / "sparse-checkout"
        with sparse_checkout_file.open("w", encoding="utf-8") as f:
            f.write(f"{SCHEMA_REPOSITORY_FOLDER.as_posix()}/**\n")

        repo.remotes.origin.fetch(f"refs/tags/{tag_name}:refs/tags/{tag_name}")
        repo.git.checkout(tag_name)
        copy_schema_tree(repo_path / SCHEMA_REPOSITORY_FOLDER, destination)


def collect_schema_drift(expected: Path, actual: Path) -> tuple[str, ...]:
    """
    Collect schema drift between expected and actual schema directories.

    Args:
        expected: Expected schema directory.
        actual: Actual schema directory.

    Returns:
        Tuple of drift messages.

    """
    expected_files = {path.relative_to(expected).as_posix(): path for path in expected.rglob("*") if path.is_file()}
    actual_files = {path.relative_to(actual).as_posix(): path for path in actual.rglob("*") if path.is_file()}

    changed = [
        f"changed: {relative_path}"
        for relative_path in sorted(expected_files.keys() & actual_files.keys())
        if not filecmp.cmp(expected_files[relative_path], actual_files[relative_path], shallow=False)
    ]
    missing = [f"missing: {relative_path}" for relative_path in sorted(expected_files.keys() - actual_files.keys())]
    extra = [f"extra: {relative_path}" for relative_path in sorted(actual_files.keys() - expected_files.keys())]
    return tuple(changed + missing + extra)


def sync_schema_files(schema_path: Path = SCHEMA_PATH) -> None:
    """
    Synchronize schema files from remote repository.

    Args:
        schema_path: Target schema path.

    """
    with TemporaryDirectory() as tmpdir:
        fetched_schema_path = Path(tmpdir) / "schema"
        fetch_schema_tree(fetched_schema_path)
        copy_schema_tree(fetched_schema_path, schema_path)


def check_schema_files(schema_path: Path = SCHEMA_PATH) -> tuple[str, ...]:
    """
    Check schema files for drift.

    Args:
        schema_path: Schema path to check.

    Returns:
        Tuple of drift messages.

    """
    with TemporaryDirectory() as tmpdir:
        fetched_schema_path = Path(tmpdir) / "schema"
        fetch_schema_tree(fetched_schema_path)
        return collect_schema_drift(fetched_schema_path, schema_path)


def main(argv: list[str] | None = None) -> None:
    """
    Run main.

    Raises:
        SystemExit: If the operation cannot be completed.

    """
    parser = argparse.ArgumentParser(description="Synchronize generated Cucumber messages JSON schema assets.")
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=SCHEMA_PATH,
        help="Generated schema directory to update or check.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated schemas differ from the cucumber-messages contract version.",
    )
    args = parser.parse_args(argv)

    if args.check:
        drift = check_schema_files(args.schema_path)
        if drift:
            print("Generated Cucumber messages schemas are stale:", file=sys.stderr)  # noqa: T201
            for entry in drift:
                print(f"  {entry}", file=sys.stderr)  # noqa: T201
            raise SystemExit(1)
        return

    sync_schema_files(args.schema_path)


if __name__ == "__main__":
    main()
