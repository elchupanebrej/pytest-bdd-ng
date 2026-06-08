"""
Provide sync messages contract schemas helpers.

Responsibility:
    Provide sync messages contract schemas helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _GitRemote: owns nested behavior below this boundary
    - _GitRemotes: owns nested behavior below this boundary
    - _GitGit: owns nested behavior below this boundary
    - _GitRepo: owns nested behavior below this boundary
    - _GitModule: owns nested behavior below this boundary
    - copy_schema_tree: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates fetched_schema_path, SCHEMA_PATH, SCHEMA_REPOSITORY_URL, SCHEMA_REPOSITORY_FOLDER, origin; depends on
    argparse, filecmp, importlib, shutil, stat.

Invariants:
    - `pytest_bdd.script.sync_messages_contract_schemas` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises SystemExit; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

import argparse
import filecmp
import importlib
import shutil
import stat
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol, cast

from pytest_bdd.util.packaging import get_distribution_version

SCHEMA_PATH = Path(__file__).parent.parent / "model" / "message_jsonschema"
SCHEMA_REPOSITORY_URL = "https://github.com/cucumber/messages.git"
SCHEMA_REPOSITORY_FOLDER = Path("jsonschema", "src")


class _GitRemote(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRemote` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitRemote` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - fetch: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._GitRemote` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def fetch(self, *args: object, **kwargs: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRemote.fetch` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.script.sync_messages_contract_schemas._GitRemote.fetch` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `fetch`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...


class _GitRemotes(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRemotes` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitRemotes` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates origin.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._GitRemotes` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    origin: _GitRemote


class _GitGit(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitGit` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitGit` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - config: owns nested behavior below this boundary
        - checkout: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._GitGit` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def config(self, *args: object, **kwargs: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitGit.config` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitGit.config`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `config`
            - src/pytest_bdd/collector.py: imports or references `config`
            - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `config`
            - src/pytest_bdd/feature_locator.py: imports or references `config`
            - src/pytest_bdd/hook.py: imports or references `config`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...

    def checkout(self, *args: object, **kwargs: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitGit.checkout` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.script.sync_messages_contract_schemas._GitGit.checkout` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


class _GitRepo(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRepo` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitRepo` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - init: owns nested behavior below this boundary
        - create_remote: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates git, remotes.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._GitRepo` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    git: _GitGit
    remotes: _GitRemotes

    @classmethod
    def init(cls, path: Path) -> "_GitRepo":
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRepo.init` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitRepo.init`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...

    def create_remote(self, name: str, url: str) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitRepo.create_remote`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.script.sync_messages_contract_schemas._GitRepo.create_remote` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


class _GitModule(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.sync_messages_contract_schemas._GitModule` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._GitModule` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates Repo.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._GitModule` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    Repo: type[_GitRepo]


def copy_schema_tree(source: Path, destination: Path) -> None:
    """
    Handle copy schema tree.

    Responsibility:
        Handle copy schema tree. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas.copy_schema_tree`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - destination.exists: collaborator call used by this boundary
        - destination.chmod: collaborator call used by this boundary
        - destination.stat: collaborator call used by this boundary
        - shutil.rmtree: collaborator call used by this boundary
        - shutil.copytree: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if destination.exists():
        destination.chmod(destination.stat().st_mode | stat.S_IWRITE)
    shutil.rmtree(str(destination), ignore_errors=True)
    shutil.copytree(str(source), str(destination))


def fetch_schema_tree(destination: Path) -> None:
    """
    Handle fetch schema tree.

    Responsibility:
        Handle fetch schema tree. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas.fetch_schema_tree`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - importlib.import_module: collaborator call used by this boundary
        - get_distribution_version: collaborator call used by this boundary
        - TemporaryDirectory: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - repo_path.mkdir: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates git_module, tag_name, repo_path, repo, sparse_checkout_file.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas.fetch_schema_tree` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
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


def _are_files_equal(file1: Path, file2: Path) -> bool:
    """
    Compare two files, ignoring line endings and trailing whitespaces.

    Args:
        file1: First file path.
        file2: Second file path.

    Returns:
        True if the normalized contents are equal, False otherwise.

    Responsibility:
        Compare two files, ignoring line endings and trailing whitespaces. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas._are_files_equal`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - file1.read_text.replace.rstrip: collaborator call used by this boundary
        - file1.read_text.replace: collaborator call used by this boundary
        - file1.read_text: collaborator call used by this boundary
        - file2.read_text.replace.rstrip: collaborator call used by this boundary
        - file2.read_text.replace: collaborator call used by this boundary
        - file2.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates content1, content2.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas._are_files_equal` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    try:
        content1 = file1.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
        content2 = file2.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
    except (OSError, UnicodeDecodeError):
        return filecmp.cmp(file1, file2, shallow=False)
    else:
        return content1 == content2


def collect_schema_drift(expected: Path, actual: Path) -> tuple[str, ...]:
    """
    Collect schema drift between expected and actual schema directories.

    Args:
        expected: Expected schema directory.
        actual: Actual schema directory.

    Returns:
        Tuple of drift messages.

    Responsibility:
        Collect schema drift between expected and actual schema directories. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.sync_messages_contract_schemas.collect_schema_drift` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - sorted: collaborator call used by this boundary
        - expected_files.keys: collaborator call used by this boundary
        - actual_files.keys: collaborator call used by this boundary
        - path.relative_to.as_posix: collaborator call used by this boundary
        - path.relative_to: collaborator call used by this boundary
        - path.is_file: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates expected_files, actual_files, changed, missing, extra.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas.collect_schema_drift` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    expected_files = {path.relative_to(expected).as_posix(): path for path in expected.rglob("*") if path.is_file()}
    actual_files = {path.relative_to(actual).as_posix(): path for path in actual.rglob("*") if path.is_file()}

    changed = [
        f"changed: {relative_path}"
        for relative_path in sorted(expected_files.keys() & actual_files.keys())
        if not _are_files_equal(expected_files[relative_path], actual_files[relative_path])
    ]
    missing = [f"missing: {relative_path}" for relative_path in sorted(expected_files.keys() - actual_files.keys())]
    extra = [f"extra: {relative_path}" for relative_path in sorted(actual_files.keys() - expected_files.keys())]
    return tuple(changed + missing + extra)


def sync_schema_files(schema_path: Path = SCHEMA_PATH) -> None:
    """
    Synchronize schema files from remote repository.

    Args:
        schema_path: Target schema path.

    Responsibility:
        Synchronize schema files from remote repository. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas.sync_schema_files`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - TemporaryDirectory: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - fetch_schema_tree: collaborator call used by this boundary
        - copy_schema_tree: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates fetched_schema_path.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas.sync_schema_files` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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

    Responsibility:
        Check schema files for drift. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas.check_schema_files`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - TemporaryDirectory: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - fetch_schema_tree: collaborator call used by this boundary
        - collect_schema_drift: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates fetched_schema_path.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas.check_schema_files` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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

    Responsibility:
        Run main. It directly owns the observable contract, local decisions, and maintenance boundary for this function.
        That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
        before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.sync_messages_contract_schemas.main` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.add_argument: collaborator call used by this boundary
        - print: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary
        - parser.parse_args: collaborator call used by this boundary
        - check_schema_files: collaborator call used by this boundary
        - SystemExit: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `main`
        - src/pytest_bdd/script/__init__.py: imports or references `main`
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__main__.py: imports or references `main`

    State and side effects:
        mutates parser, args, drift.

    Invariants:
        - `pytest_bdd.script.sync_messages_contract_schemas.main` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises SystemExit; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
