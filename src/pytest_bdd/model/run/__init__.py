# init: public-api  # init: no-check
"""
Run-level runtime model helpers — package re-exports.

Responsibility:
    Run-level runtime model helpers — package re-exports. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_gherkin_go/_build.py: imports or references `run`
    - src/pytest_bdd/collector_batch.py: imports or references `run`
    - src/pytest_bdd/hook.py: imports or references `run`
    - src/pytest_bdd/model/feature_binding.py: imports or references `run`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `run`

State and side effects:
    depends on __future__.annotations, pytest_bdd.model.run.lifecycle.ActiveObjectSet,
    pytest_bdd.model.run.lifecycle.ContextErrorState, pytest_bdd.model.run.lifecycle.ExternalApiCompatibilityRecord,
    pytest_bdd.model.run.lifecycle.NodeKind.

Invariants:
    - `pytest_bdd.model.run` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.model.run.lifecycle import (
    ActiveObjectSet as ActiveObjectSet,
)
from pytest_bdd.model.run.lifecycle import (
    ContextErrorState as ContextErrorState,
)
from pytest_bdd.model.run.lifecycle import (
    ExternalApiCompatibilityRecord as ExternalApiCompatibilityRecord,
)
from pytest_bdd.model.run.lifecycle import (
    NodeKind as NodeKind,
)
from pytest_bdd.model.run.lifecycle import (
    ReferenceResolverState as ReferenceResolverState,
)
from pytest_bdd.model.run.lifecycle import (
    ReportingContextSnapshot as ReportingContextSnapshot,
)
from pytest_bdd.model.run.lifecycle import (
    ReportingLifecycleState as ReportingLifecycleState,
)
from pytest_bdd.model.run.lifecycle import (
    Run as Run,
)
from pytest_bdd.model.run.lifecycle import (
    ScenarioRunResult as ScenarioRunResult,
)
from pytest_bdd.model.run.refs import (
    LifecycleKind as LifecycleKind,
)
from pytest_bdd.model.run.refs import (
    LifecycleObjectRef as LifecycleObjectRef,
)
from pytest_bdd.model.run.refs import (
    NoPreviousStep as NoPreviousStep,
)
from pytest_bdd.model.run.refs import (
    _finished_feature_ref as _finished_feature_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_previous_step_ref as _finished_previous_step_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_scenario_ref as _finished_scenario_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_step_ref as _finished_step_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_feature_ref as _inactive_feature_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_scenario_ref as _inactive_scenario_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_step_ref as _inactive_step_ref,
)
from pytest_bdd.model.run.refs import (
    _no_previous_step_ref as _no_previous_step_ref,
)
from pytest_bdd.model.run.stages import (
    HookPhase as HookPhase,
)
from pytest_bdd.model.run.stages import (
    RunStage as RunStage,
)
from pytest_bdd.model.run.stages import (
    RunStatus as RunStatus,
)
from pytest_bdd.model.run.transitions import (
    build_lifecycle_ref as build_lifecycle_ref,
)
from pytest_bdd.model.run.transitions import (
    initial_scenario_run_id as initial_scenario_run_id,
)
from pytest_bdd.model.run.transitions import (
    runtime_object_id as runtime_object_id,
)
from pytest_bdd.model.run.transitions import (
    runtime_object_name as runtime_object_name,
)
