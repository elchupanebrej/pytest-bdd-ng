"""
Backward-compatible re-exports of all public message stream validation symbols.

Responsibility:
    Backward-compatible re-exports of all public message stream validation symbols. It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.message_stream_validation.facade` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/__init__.py: imports or references `facade`
    - src/pytest_bdd/model/message_stream_validation.py: imports or references `facade`

State and side effects:
    depends on __future__.annotations, pytest_bdd.message_stream_validation.pipeline.ALLOWED_IMPLEMENTATION_STATUSES,
    pytest_bdd.message_stream_validation.pipeline.collect_observed_capability_ids,
    pytest_bdd.message_stream_validation.pipeline.validate_message_stream,
    pytest_bdd.message_stream_validation.status.collect_observed_outcomes.

Invariants:
    - `pytest_bdd.message_stream_validation.facade` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from pytest_bdd.message_stream_validation.pipeline import (  # noqa: F401
    ALLOWED_IMPLEMENTATION_STATUSES,
    collect_observed_capability_ids,
    validate_message_stream,
)
from pytest_bdd.message_stream_validation.status import (  # noqa: F401
    collect_observed_outcomes,
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
)
