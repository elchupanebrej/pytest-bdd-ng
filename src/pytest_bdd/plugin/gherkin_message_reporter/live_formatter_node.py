"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # noqa: S404  -- suppressed warning
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from filelock import FileLock

from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest, NodePackageProvisionResult
from pytest_bdd.plugin.gherkin_message_reporter.session import format_requested_cucumber_formatter_labels

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter

logger = logging.getLogger(__name__)


class LiveFormatterNodeMixin:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter

    @staticmethod
    def _prepend_node_path(env: Mapping[str, str], *node_modules_roots: Path) -> dict[str, str]:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        merged_env = {key: str(value) for key, value in env.items()}
        search_roots = [str(path) for path in node_modules_roots if str(path)]
        existing_node_path = merged_env.get("NODE_PATH")
        if existing_node_path:
            search_roots.append(existing_node_path)
        if search_roots:
            merged_env["NODE_PATH"] = os.pathsep.join(dict.fromkeys(search_roots))
        return merged_env

    @classmethod
    def _build_node_execution_env(cls, *node_modules_roots: Path) -> dict[str, str]:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        env = cls._prepend_node_path(os.environ, *node_modules_roots)
        env["NPM_CONFIG_PREFIX"] = str(Path.home() / ".npm-global")
        return env

    def _node_package_installed(self, node_executable: str, package_name: str, *, env: Mapping[str, str]) -> bool:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        return self._resolve_node_package_root(node_executable, package_name, env=env) is not None

    def _resolve_global_node_modules_root(
        self,
        npm_executable: str,
        *,
        env: Mapping[str, str],
    ) -> Path | None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        completed = subprocess.run(  # noqa: S603  -- suppressed warning
            [npm_executable, "root", "-g"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(Path(self.reporter.config.rootpath)),
            env=dict(env),
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return None
        return Path(completed.stdout.strip()).resolve()

    @staticmethod
    def _infer_node_modules_root_from_resolved_package_path(
        resolved_package_path: Path,
        package_name: str,
    ) -> Path | None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        package_parts = tuple(package_name.split("/"))
        resolved_parts = resolved_package_path.parts
        for index in range(len(resolved_parts) - len(package_parts) + 1):
            if resolved_parts[index : index + len(package_parts)] == package_parts:
                return Path(*resolved_parts[:index])
        return None

    def _resolve_node_package_root(
        self,
        node_executable: str,
        package_name: str,
        *,
        env: Mapping[str, str],
    ) -> Path | None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        completed = subprocess.run(  # noqa: S603  -- suppressed warning
            [node_executable, "-e", "process.stdout.write(require.resolve(process.argv[1]))", package_name],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(Path(self.reporter.config.rootpath)),
            env=dict(env),
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return None
        return self._infer_node_modules_root_from_resolved_package_path(
            Path(completed.stdout.strip()).resolve(),
            package_name,
        )

    def _ensure_node_packages_available(
        self,
        package_names: tuple[str, ...],
        *,
        purpose: str,
    ) -> NodePackageProvisionResult:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        node_executable = shutil.which("node") or shutil.which("nodejs")
        if node_executable is None:
            return NodePackageProvisionResult(env={}, missing_packages=tuple(sorted(package_names)), missing_node=True)

        discovered_node_modules_roots = tuple(
            dict.fromkeys(
                filter(
                    None,
                    (
                        self._resolve_node_package_root(
                            node_executable,
                            package_name,
                            env=self._build_node_execution_env(),
                        )
                        for package_name in package_names
                    ),
                ),
            ),
        )
        base_env = self._build_node_execution_env(*discovered_node_modules_roots)
        missing_from_env = tuple(
            sorted(
                package_name
                for package_name in package_names
                if not self._node_package_installed(node_executable, package_name, env=base_env)
            ),
        )
        if not missing_from_env:
            return NodePackageProvisionResult(env=base_env, node_modules_roots=discovered_node_modules_roots)

        npm_executable = shutil.which("npm")
        if npm_executable is None:
            return NodePackageProvisionResult(
                env=base_env,
                missing_packages=missing_from_env,
                node_modules_roots=discovered_node_modules_roots,
                missing_npm=True,
            )

        global_node_modules_root = self._resolve_global_node_modules_root(npm_executable, env=base_env)
        if global_node_modules_root is None:
            return NodePackageProvisionResult(
                env=base_env,
                missing_packages=missing_from_env,
                node_modules_roots=discovered_node_modules_roots,
                missing_npm=True,
            )

        global_env = self._build_node_execution_env(*discovered_node_modules_roots, global_node_modules_root)
        missing_from_global = tuple(
            sorted(
                package_name
                for package_name in missing_from_env
                if not self._node_package_installed(node_executable, package_name, env=global_env)
            ),
        )
        if not missing_from_global:
            return NodePackageProvisionResult(
                env=global_env,
                node_modules_roots=(*discovered_node_modules_roots, global_node_modules_root),
            )

        lock = FileLock(str(Path(tempfile.gettempdir()) / "pytest-bdd-ng-global-npm-install.lock"))
        install_env = dict(global_env)
        install_env.setdefault("npm_config_audit", "false")
        install_env.setdefault("npm_config_fund", "false")
        install_env.setdefault("npm_config_update_notifier", "false")

        with lock:
            packages_to_install = tuple(
                sorted(
                    package_name
                    for package_name in missing_from_global
                    if not self._node_package_installed(node_executable, package_name, env=global_env)
                ),
            )
            if packages_to_install:
                sys.stderr.write(
                    f"Installing missing global npm package(s) for {purpose}: {', '.join(packages_to_install)}\n",
                )
                sys.stderr.flush()
                completed = subprocess.run(  # noqa: S603  -- suppressed warning
                    [
                        npm_executable,
                        "install",
                        "-g",
                        "--silent",
                        "--ignore-scripts",
                        "--no-audit",
                        "--no-fund",
                        *packages_to_install,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=str(Path(self.reporter.config.rootpath)),
                    env=install_env,
                )
                if completed.stderr:
                    sys.stderr.write(completed.stderr)
                    sys.stderr.flush()
                if completed.returncode != 0:
                    logger.warning(
                        "Automatic npm installation failed for %s while %s with exit code %s.",
                        ", ".join(packages_to_install),
                        purpose,
                        completed.returncode,
                    )

        final_missing_packages = tuple(
            sorted(
                package_name
                for package_name in missing_from_env
                if not self._node_package_installed(node_executable, package_name, env=global_env)
            ),
        )
        installed_packages = tuple(sorted(set(missing_from_env) - set(final_missing_packages)))
        return NodePackageProvisionResult(
            env=global_env,
            missing_packages=final_missing_packages,
            installed_packages=installed_packages,
            node_modules_roots=(*discovered_node_modules_roots, global_node_modules_root),
        )

    def _resolve_runnable_cucumber_formatter_requests(
        self,
        *,
        formatter_labels: str,
    ) -> tuple[
        str | None,
        dict[str, str],
        list[CucumberFormatterRequest],
        dict[str, list[CucumberFormatterRequest]],
        tuple[str, ...],
    ]:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        provision_result = self._ensure_node_packages_available(
            tuple(
                sorted(
                    {
                        "@cucumber/cucumber",
                        *(request.package_name for request in self.reporter.requested_cucumber_formatters),
                    },
                ),
            ),
            purpose=f"cucumber formatter rendering ({formatter_labels})",
        )
        if provision_result.missing_node:
            return None, {}, [], {}, ()

        node_executable = shutil.which("node") or shutil.which("nodejs")
        if node_executable is None:
            return None, {}, [], {}, ()

        node_env = provision_result.env or self._build_node_execution_env()
        runnable_requests: list[CucumberFormatterRequest] = []
        missing_packages: dict[str, list[CucumberFormatterRequest]] = {}
        for formatter_request in self.reporter.requested_cucumber_formatters:
            if (
                "@cucumber/cucumber" not in provision_result.missing_packages
                and formatter_request.package_name not in provision_result.missing_packages
            ):
                runnable_requests.append(formatter_request)
            else:
                missing_packages.setdefault(formatter_request.package_name, []).append(formatter_request)

        return node_executable, node_env, runnable_requests, missing_packages, provision_result.missing_packages

    @staticmethod
    def _warn_about_missing_cucumber_formatter_packages(
        missing_packages: dict[str, list[CucumberFormatterRequest]],
    ) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        for package_name, formatter_requests in missing_packages.items():
            logger.warning(
                "Skipping cucumber formatter rendering for %s because npm package '%s' is unavailable. "
                "Install it manually with `npm install --save-dev %s` if auto-provisioning is not possible.",
                format_requested_cucumber_formatter_labels(formatter_requests),
                package_name,
                package_name,
            )

    @staticmethod
    def _augment_node_env_for_live_terminal_stream(env: dict[str, str]) -> dict[str, str]:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        augmented_env = dict(env)
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ISATTY"] = "1" if sys.stdout.isatty() else "0"
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_COLUMNS"] = str(max(terminal_size.columns, 1))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ROWS"] = str(max(terminal_size.lines, 1))
        return augmented_env
