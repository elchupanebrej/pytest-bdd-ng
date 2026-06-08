"""
CI detection helpers for the lifecycle runtime — static utility functions.

Responsibility:
    CI detection helpers for the lifecycle runtime — static utility functions. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _build_ci_message: owns nested behavior below this boundary
    - _enrich_ci_payload: owns nested behavior below this boundary
    - _resolve_ci_branch: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates ci_payload, enriched_payload, payload, git_payload_raw, git_payload; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.cast, ci_environment.detect_ci_environment, cucumber_messages.Ci.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci` keeps its documented import path, ownership
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

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ci_environment import detect_ci_environment
from cucumber_messages import Ci  # upstream library missing type stubs

from pytest_bdd.model.message_converter import message_converter

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.types.json import JSONObject


def _build_ci_message(env: Mapping[str, str]) -> Ci | None:
    """
    Build a CI metadata message from environment variables.

    Returns:
        Ci payload or None if no CI environment detected.

    Responsibility:
        Build a CI metadata message from environment variables. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._build_ci_message` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - detect_ci_environment: collaborator call used by this boundary
        - _enrich_ci_payload: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - message_converter.from_dict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_build_ci_message`

    State and side effects:
        mutates ci_payload, enriched_payload.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._build_ci_message` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    ci_payload = detect_ci_environment(env)
    if ci_payload is None:
        return None
    enriched_payload = _enrich_ci_payload(ci_payload, env)
    return cast("Ci", message_converter.from_dict(enriched_payload, Ci))


def _enrich_ci_payload(ci_payload: JSONObject, env: Mapping[str, str]) -> JSONObject:
    """
    Patch CI payload with branch when detector omits it for PR-style builds.

    ``ci_environment`` provides a solid baseline payload, but some providers
    expose branch only via platform-specific env vars in merge-request
    pipelines. We enrich only the missing branch field to keep emitted
    metadata stable without overriding detector-provided values.

    Returns:
        Enriched CI payload.

    Responsibility:
        Patch CI payload with branch when detector omits it for PR-style builds. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._enrich_ci_payload` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - dict: collaborator call used by this boundary
        - payload.get: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - git_payload.get: collaborator call used by this boundary
        - _resolve_ci_branch: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates payload, git_payload_raw, git_payload, branch.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._enrich_ci_payload` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    payload = dict(ci_payload)
    git_payload_raw = payload.get("git")
    git_payload = dict(git_payload_raw) if isinstance(git_payload_raw, dict) else {}
    if not git_payload.get("branch"):
        branch = _resolve_ci_branch(env)
        if branch:
            git_payload["branch"] = branch
    if git_payload:
        payload["git"] = git_payload
    return payload


def _resolve_ci_branch(env: Mapping[str, str]) -> str | None:
    """
    Resolve VCS branch name from common CI env var conventions.

    Returns:
        Branch name or None.

    Responsibility:
        Resolve VCS branch name from common CI env var conventions. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._resolve_ci_branch` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - strip: collaborator call used by this boundary
        - env.get: collaborator call used by this boundary
        - strip.lower: collaborator call used by this boundary
        - github_ref.startswith: collaborator call used by this boundary
        - github_ref.removeprefix: collaborator call used by this boundary
        - value.removeprefix: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates github_ref_type, github_ref, github_ref_name, github_head_ref, value.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._ci._resolve_ci_branch` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    github_ref_type = (env.get("GITHUB_REF_TYPE") or "").strip().lower()
    github_ref = (env.get("GITHUB_REF") or "").strip()
    github_ref_name = (env.get("GITHUB_REF_NAME") or "").strip()
    github_head_ref = (env.get("GITHUB_HEAD_REF") or "").strip()
    if github_ref_type == "branch" and github_ref_name:
        return github_ref_name
    if github_ref.startswith("refs/heads/"):
        return github_ref.removeprefix("refs/heads/")
    if github_head_ref:
        return github_head_ref

    for name in (
        "CI_COMMIT_BRANCH",
        "CI_COMMIT_REF_NAME",
        "GIT_BRANCH",
        "BRANCH_NAME",
        "BUILD_SOURCEBRANCHNAME",
    ):
        value = (env.get(name) or "").strip()
        if value:
            return value.removeprefix("refs/heads/")
    return None
