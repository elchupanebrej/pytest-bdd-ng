"""
Provide live formatter node/package resolution helpers.

Responsibility:
    Provide live formatter node/package resolution helpers. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - LiveFormatterNodeMixin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
      `live_formatter_node`

State and side effects:
    mutates completed, node_executable, logger, reporter, merged_env; depends on __future__.annotations, logging, os,
    shutil, subprocess.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # noqa: S404
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
    Provide live formatter Node.js package resolution behavior.

    Responsibility:
        Provide live formatter Node.js package resolution behavior. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _prepend_node_path: owns nested behavior below this boundary
        - _build_node_execution_env: owns nested behavior below this boundary
        - _node_package_installed: owns nested behavior below this boundary
        - _resolve_global_node_modules_root: owns nested behavior below this boundary
        - _infer_node_modules_root_from_resolved_package_path: owns nested behavior below this boundary
        - _resolve_node_package_root: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `LiveFormatterNodeMixin`

    State and side effects:
        mutates completed, node_executable, reporter, merged_env, search_roots.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter

    @staticmethod
    def _prepend_node_path(env: Mapping[str, str], *node_modules_roots: Path) -> dict[str, str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._prepend_node_path`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._prepend_node_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - env.items: collaborator call used by this boundary
            - merged_env.get: collaborator call used by this boundary
            - search_roots.append: collaborator call used by this boundary
            - os.pathsep.join: collaborator call used by this boundary
            - dict.fromkeys: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_prepend_node_path`

        State and side effects:
            mutates merged_env, search_roots, existing_node_path.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._prepend_node_path`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._build_node_execution_env`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._build_node_execution_env`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls._prepend_node_path: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - Path.home: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_build_node_execution_env`

        State and side effects:
            mutates env.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._build_node_execution_env`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        env = cls._prepend_node_path(os.environ, *node_modules_roots)
        env["NPM_CONFIG_PREFIX"] = str(Path.home() / ".npm-global")
        return env

    def _node_package_installed(self, node_executable: str, package_name: str, *, env: Mapping[str, str]) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._node_package_installed`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._node_package_installed`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._resolve_node_package_root: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_node_package_installed`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return self._resolve_node_package_root(node_executable, package_name, env=env) is not None

    def _resolve_global_node_modules_root(
        self,
        npm_executable: str,
        *,
        env: Mapping[str, str],
    ) -> Path | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_global_node_modules_root`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_global_node_modules_root`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - completed.stdout.strip: collaborator call used by this boundary
            - subprocess.run: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - dict: collaborator call used by this boundary
            - Path.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_global_node_modules_root`

        State and side effects:
            mutates completed.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_global_node_modules_root`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        completed = subprocess.run(  # noqa: S603
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._infer_node_modules_root_from_resolved_package_path`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._infer_node_modules_root_from_resolved_package_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - package_name.split: collaborator call used by this boundary
            - range: collaborator call used by this boundary
            - Path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_infer_node_modules_root_from_resolved_package_path`

        State and side effects:
            mutates package_parts, resolved_parts.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._infer_node_modules_root_from_resolved_package_path`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_node_package_root`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_node_package_root`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - completed.stdout.strip: collaborator call used by this boundary
            - subprocess.run: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - dict: collaborator call used by this boundary
            - self._infer_node_modules_root_from_resolved_package_path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_node_package_root`

        State and side effects:
            mutates completed.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_node_package_root`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        completed = subprocess.run(  # noqa: S603
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._ensure_node_packages_available`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._ensure_node_packages_available`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - tuple: collaborator call used by this boundary
            - NodePackageProvisionResult: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - self._node_package_installed: collaborator call used by this boundary
            - shutil.which: collaborator call used by this boundary
            - self._build_node_execution_env: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_ensure_node_packages_available`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_ensure_node_packages_available`

        State and side effects:
            mutates node_executable, discovered_node_modules_roots, base_env, missing_from_env, npm_executable.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._ensure_node_packages_available`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
                completed = subprocess.run(  # noqa: S603
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_runnable_cucumber_formatter_requests`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_runnable_cucumber_formatter_requests`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - shutil.which: collaborator call used by this boundary
            - self._ensure_node_packages_available: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - self._build_node_execution_env: collaborator call used by this boundary
            - runnable_requests.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_resolve_runnable_cucumber_formatter_requests`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_runnable_cucumber_formatter_requests`

        State and side effects:
            mutates provision_result, node_executable, node_env, runnable_requests, missing_packages.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._resolve_runnable_cucumber_formatter_requests`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._warn_about_missing_cucumber_formatter_packages`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._warn_about_missing_cucumber_formatter_packages`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - missing_packages.items: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary
            - format_requested_cucumber_formatter_labels: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_warn_about_missing_cucumber_formatter_packages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_warn_about_missing_cucumber_formatter_packages`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._augment_node_env_for_live_terminal_stream`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._augment_node_env_for_live_terminal_stream`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - max: collaborator call used by this boundary
            - dict: collaborator call used by this boundary
            - shutil.get_terminal_size: collaborator call used by this boundary
            - sys.stdout.isatty: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_augment_node_env_for_live_terminal_stream`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_augment_node_env_for_live_terminal_stream`

        State and side effects:
            mutates augmented_env, terminal_size.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node.LiveFormatterNodeMixin._augment_node_env_for_live_terminal_stream`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        augmented_env = dict(env)
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ISATTY"] = "1" if sys.stdout.isatty() else "0"
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_COLUMNS"] = str(max(terminal_size.columns, 1))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ROWS"] = str(max(terminal_size.lines, 1))
        return augmented_env
