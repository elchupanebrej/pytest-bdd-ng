"""
Provide message capability inventory helpers.

Responsibility:
    Provide message capability inventory helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_capability_inventory` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - CapabilitySyncResult: owns nested behavior below this boundary
    - MandatoryScopeReconciliation: owns nested behavior below this boundary
    - CoverageScopeReconciliation: owns nested behavior below this boundary
    - _to_camel_case_identifier: owns nested behavior below this boundary
    - _canonical_payload_kind: owns nested behavior below this boundary
    - _canonical_capability_id: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/coverage/inventory.py: imports or references `message_capability_inventory`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `message_capability_inventory`
    - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
      `message_capability_inventory`
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
      `message_capability_inventory`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
      `message_capability_inventory`

State and side effects:
    mutates total_relevant, total_out_of_scope, inventory_capability_ids, non_runtime_set, observed_set; depends on
    __future__.annotations, json, collections.abc.Iterable, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.message_capability_inventory` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises FileNotFoundError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
from collections.abc import Iterable  # noqa: TC003
from pathlib import Path
from typing import TYPE_CHECKING, cast

from attrs import frozen
from returns.maybe import Nothing

from .message_capability import MessageCapability, capability_is_relevant

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

SCHEMA_RELATIVE_DIR = Path("messages") / "jsonschema" / "src"
PACKAGE_SCHEMA_RELATIVE_DIR = Path("message_jsonschema")


@frozen
class CapabilitySyncResult:
    """
    Store the results of parsing and normalizing capabilities from the message schema.

    Responsibility:
        Store the results of parsing and normalizing capabilities from the message schema. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability_inventory.CapabilitySyncResult`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `CapabilitySyncResult`
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `CapabilitySyncResult`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `CapabilitySyncResult`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `CapabilitySyncResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `CapabilitySyncResult`

    State and side effects:
        mutates total_relevant, total_out_of_scope, duplicate_capability_ids, capabilities.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.CapabilitySyncResult` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    total_relevant: int
    total_out_of_scope: int
    duplicate_capability_ids: tuple[str, ...]
    capabilities: tuple[MessageCapability, ...]


@frozen
class MandatoryScopeReconciliation:
    """
    Detail the coverage comparison between the identified capabilities and those considered mandatory.

    Responsibility:
        Detail the coverage comparison between the identified capabilities and those considered mandatory. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.MandatoryScopeReconciliation` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - mandatory_total: owns nested behavior below this boundary
        - inventory_total: owns nested behavior below this boundary
        - has_missing_mandatory_capabilities: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `MandatoryScopeReconciliation`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `MandatoryScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `MandatoryScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `MandatoryScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `MandatoryScopeReconciliation`

    State and side effects:
        mutates inventory_capability_ids, mandatory_capability_ids, missing_mandatory_capability_ids.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.MandatoryScopeReconciliation` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    inventory_capability_ids: tuple[str, ...]
    mandatory_capability_ids: tuple[str, ...]
    missing_mandatory_capability_ids: tuple[str, ...]

    @property
    def mandatory_total(self) -> int:
        """
        Count the total number of capabilities that are deemed mandatory.

        Returns:
            The total number of mandatory capabilities.

        Responsibility:
            Count the total number of capabilities that are deemed mandatory. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.MandatoryScopeReconciliation.mandatory_total` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `mandatory_total`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `mandatory_total`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `mandatory_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `mandatory_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `mandatory_total`

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
            #arch-eval:locational_stability=4

        """
        return len(self.mandatory_capability_ids)

    @property
    def inventory_total(self) -> int:
        """
        Count the total number of capabilities identified in the inventory.

        Returns:
            The total number of capabilities in the inventory.

        Responsibility:
            Count the total number of capabilities identified in the inventory. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.MandatoryScopeReconciliation.inventory_total` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `inventory_total`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `inventory_total`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `inventory_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `inventory_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `inventory_total`

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
            #arch-eval:locational_stability=4

        """
        return len(self.inventory_capability_ids)

    @property
    def has_missing_mandatory_capabilities(self) -> bool:
        """
        Check if any capabilities deemed mandatory are missing from the parsed inventory.

        Returns:
            True if one or more mandatory capabilities are absent, False otherwise.

        Responsibility:
            Check if any capabilities deemed mandatory are missing from the parsed inventory. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.MandatoryScopeReconciliation.has_missing_mandatory_capabilities`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `has_missing_mandatory_capabilities`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references
              `has_missing_mandatory_capabilities`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `has_missing_mandatory_capabilities`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `has_missing_mandatory_capabilities`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `has_missing_mandatory_capabilities`

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
            #arch-eval:locational_stability=4

        """
        return bool(self.missing_mandatory_capability_ids)


@frozen
class CoverageScopeReconciliation:
    """
    Summarize how well the implemented capabilities cover the expected runtime scope.

    Responsibility:
        Summarize how well the implemented capabilities cover the expected runtime scope. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - runtime_required_total: owns nested behavior below this boundary
        - runtime_required_covered: owns nested behavior below this boundary
        - runtime_required_missing: owns nested behavior below this boundary
        - non_runtime_required_total: owns nested behavior below this boundary
        - non_runtime_covered: owns nested behavior below this boundary
        - non_runtime_classified: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `CoverageScopeReconciliation`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `CoverageScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `CoverageScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `CoverageScopeReconciliation`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `CoverageScopeReconciliation`

    State and side effects:
        mutates non_runtime_set, inventory_capability_ids, runtime_required_capability_ids, observed_capability_ids,
        classified_capability_ids.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    inventory_capability_ids: tuple[str, ...]
    runtime_required_capability_ids: tuple[str, ...]
    observed_capability_ids: tuple[str, ...]
    classified_capability_ids: tuple[str, ...]
    missing_runtime_required_capability_ids: tuple[str, ...]
    uncovered_non_runtime_unclassified_capability_ids: tuple[str, ...]

    @property
    def runtime_required_total(self) -> int:
        """
        Calculate the total number of capabilities required by the runtime.

        Returns:
            The total count of required runtime capabilities.

        Responsibility:
            Calculate the total number of capabilities required by the runtime. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.runtime_required_total` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `runtime_required_total`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `runtime_required_total`

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
            #arch-eval:locational_stability=4

        """
        return len(self.runtime_required_capability_ids)

    @property
    def runtime_required_covered(self) -> int:
        """
        Calculate the total number of required runtime capabilities that are covered.

        Returns:
            The count of covered required runtime capabilities.

        Responsibility:
            Calculate the total number of required runtime capabilities that are covered. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.runtime_required_covered` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `runtime_required_covered`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `runtime_required_covered`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `runtime_required_covered`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `runtime_required_covered`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `runtime_required_covered`

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
            #arch-eval:locational_stability=4

        """
        return self.runtime_required_total - len(self.missing_runtime_required_capability_ids)

    @property
    def runtime_required_missing(self) -> int:
        """
        Calculate the total number of required runtime capabilities that are missing.

        Returns:
            The count of missing required runtime capabilities.

        Responsibility:
            Calculate the total number of required runtime capabilities that are missing. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.runtime_required_missing` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `runtime_required_missing`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `runtime_required_missing`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `runtime_required_missing`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `runtime_required_missing`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `runtime_required_missing`

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
            #arch-eval:locational_stability=4

        """
        return len(self.missing_runtime_required_capability_ids)

    @property
    def non_runtime_required_total(self) -> int:
        """
        Calculate the total number of capabilities outside the required runtime scope.

        Returns:
            The total count of non-runtime required capabilities.

        Responsibility:
            Calculate the total number of capabilities outside the required runtime scope. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.non_runtime_required_total`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - set.difference: collaborator call used by this boundary
            - set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `non_runtime_required_total`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `non_runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `non_runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `non_runtime_required_total`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `non_runtime_required_total`

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
            #arch-eval:locational_stability=4

        """
        return len(tuple(set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)))

    @property
    def non_runtime_covered(self) -> int:
        """
        Calculate the total number of non-runtime capabilities that are covered by observed implementations.

        Returns:
            The count of covered non-runtime capabilities.

        Responsibility:
            Calculate the total number of non-runtime capabilities that are covered by observed implementations. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.non_runtime_covered` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - set: collaborator call used by this boundary
            - set.difference: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - non_runtime_set.intersection: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `non_runtime_covered`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `non_runtime_covered`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `non_runtime_covered`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `non_runtime_covered`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `non_runtime_covered`

        State and side effects:
            mutates non_runtime_set, observed_set.

        Invariants:
            - `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.non_runtime_covered` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        observed_set = set(self.observed_capability_ids)
        return len(non_runtime_set.intersection(observed_set))

    @property
    def non_runtime_classified(self) -> int:
        """
        Calculate the total number of non-runtime capabilities that have a recorded classification.

        Returns:
            The count of classified non-runtime capabilities.

        Responsibility:
            Calculate the total number of non-runtime capabilities that have a recorded classification. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.non_runtime_classified` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - set: collaborator call used by this boundary
            - set.difference: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - non_runtime_set.intersection: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `non_runtime_classified`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `non_runtime_classified`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `non_runtime_classified`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `non_runtime_classified`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `non_runtime_classified`

        State and side effects:
            mutates non_runtime_set, classified_set.

        Invariants:
            - `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.non_runtime_classified` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        classified_set = set(self.classified_capability_ids)
        return len(non_runtime_set.intersection(classified_set))

    @property
    def has_unclassified_non_runtime_gaps(self) -> bool:
        """
        Check if there are any non-runtime capabilities lacking both coverage and classification.

        Returns:
            True if there are unclassified gaps, False otherwise.

        Responsibility:
            Check if there are any non-runtime capabilities lacking both coverage and classification. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_capability_inventory.CoverageScopeReconciliation.has_unclassified_non_runtime_gaps`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `has_unclassified_non_runtime_gaps`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references
              `has_unclassified_non_runtime_gaps`
            - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
              `has_unclassified_non_runtime_gaps`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
              `has_unclassified_non_runtime_gaps`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
              `has_unclassified_non_runtime_gaps`

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
            #arch-eval:locational_stability=4

        """
        return bool(self.uncovered_non_runtime_unclassified_capability_ids)


def _to_camel_case_identifier(value: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_capability_inventory._to_camel_case_identifier` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory._to_camel_case_identifier` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - value.split: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - upper: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `_to_camel_case_identifier`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_to_camel_case_identifier`

    State and side effects:
        mutates parts.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory._to_camel_case_identifier` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _canonical_payload_kind(payload_kind: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_capability_inventory._canonical_payload_kind` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory._canonical_payload_kind` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - payload_kind.strip: collaborator call used by this boundary
        - _to_camel_case_identifier: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `_canonical_payload_kind`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_canonical_payload_kind`

    State and side effects:
        mutates payload_kind.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory._canonical_payload_kind` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    payload_kind = payload_kind.strip()
    if "_" not in payload_kind:
        return payload_kind
    return _to_camel_case_identifier(payload_kind)


def _canonical_capability_id(capability_id: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_capability_inventory._canonical_capability_id` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory._canonical_capability_id` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - _canonical_payload_kind: collaborator call used by this boundary
        - capability_id.split: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `_canonical_capability_id`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_canonical_capability_id`

    State and side effects:
        mutates payload_kind, field_path.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory._canonical_capability_id` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    if "." not in capability_id:
        return _canonical_payload_kind(capability_id)
    payload_kind, field_path = capability_id.split(".", 1)
    return f"{_canonical_payload_kind(payload_kind)}.{field_path}"


def normalize_capability_ids(capability_ids: Iterable[str]) -> tuple[str, ...]:
    """
    Normalize and deduplicate an iterable of capability identifiers.

    Returns:
        A sorted tuple of canonical capability identifiers.

    Responsibility:
        Normalize and deduplicate an iterable of capability identifiers. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.normalize_capability_ids` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - _canonical_capability_id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `normalize_capability_ids`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `normalize_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `normalize_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `normalize_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `normalize_capability_ids`

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
        #arch-eval:locational_stability=4

    """
    return tuple(sorted({_canonical_capability_id(capability_id) for capability_id in capability_ids}))


def reconcile_inventory_with_mandatory_scope(
    inventory_capability_ids: Iterable[str],
    mandatory_capability_ids: Iterable[str],
) -> MandatoryScopeReconciliation:
    """
    Compare the current capability inventory against the predefined mandatory scope.

    Returns:
        A MandatoryScopeReconciliation object detailing missing capabilities.

    Responsibility:
        Compare the current capability inventory against the predefined mandatory scope. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.reconcile_inventory_with_mandatory_scope` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_capability_ids: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - mandatory_set.difference: collaborator call used by this boundary
        - MandatoryScopeReconciliation: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `reconcile_inventory_with_mandatory_scope`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references
          `reconcile_inventory_with_mandatory_scope`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `reconcile_inventory_with_mandatory_scope`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `reconcile_inventory_with_mandatory_scope`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `reconcile_inventory_with_mandatory_scope`

    State and side effects:
        mutates normalized_inventory, normalized_mandatory, inventory_set, mandatory_set, missing.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.reconcile_inventory_with_mandatory_scope` keeps its documented
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
        #arch-eval:locational_stability=4

    """
    normalized_inventory = normalize_capability_ids(inventory_capability_ids)
    normalized_mandatory = normalize_capability_ids(mandatory_capability_ids)
    inventory_set = set(normalized_inventory)
    mandatory_set = set(normalized_mandatory)
    missing = tuple(sorted(mandatory_set.difference(inventory_set)))
    return MandatoryScopeReconciliation(
        inventory_capability_ids=normalized_inventory,
        mandatory_capability_ids=normalized_mandatory,
        missing_mandatory_capability_ids=missing,
    )


def reconcile_runtime_scope_coverage(
    *,
    inventory_capability_ids: Iterable[str],
    runtime_required_capability_ids: Iterable[str],
    observed_capability_ids: Iterable[str],
    classified_capability_ids: Iterable[str],
) -> CoverageScopeReconciliation:
    """
    Assess coverage levels of the runtime required capabilities against observed and classified lists.

    Returns:
        A CoverageScopeReconciliation object capturing gap analysis.

    Responsibility:
        Assess coverage levels of the runtime required capabilities against observed and classified lists. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.reconcile_runtime_scope_coverage` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_capability_ids: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - runtime_required_set.difference: collaborator call used by this boundary
        - inventory_set.difference: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `reconcile_runtime_scope_coverage`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `reconcile_runtime_scope_coverage`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `reconcile_runtime_scope_coverage`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `reconcile_runtime_scope_coverage`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `reconcile_runtime_scope_coverage`

    State and side effects:
        mutates inventory_ids, runtime_required_ids, observed_ids, classified_ids, inventory_set.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.reconcile_runtime_scope_coverage` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    inventory_ids = normalize_capability_ids(inventory_capability_ids)
    runtime_required_ids = normalize_capability_ids(runtime_required_capability_ids)
    observed_ids = normalize_capability_ids(observed_capability_ids)
    classified_ids = normalize_capability_ids(classified_capability_ids)

    inventory_set = set(inventory_ids)
    runtime_required_set = set(runtime_required_ids)
    observed_set = set(observed_ids)
    classified_set = set(classified_ids)

    missing_runtime_required = tuple(sorted(runtime_required_set.difference(observed_set)))
    non_runtime_ids = inventory_set.difference(runtime_required_set)
    uncovered_non_runtime = non_runtime_ids.difference(observed_set)
    uncovered_non_runtime_unclassified = tuple(sorted(uncovered_non_runtime.difference(classified_set)))

    return CoverageScopeReconciliation(
        inventory_capability_ids=inventory_ids,
        runtime_required_capability_ids=runtime_required_ids,
        observed_capability_ids=observed_ids,
        classified_capability_ids=classified_ids,
        missing_runtime_required_capability_ids=missing_runtime_required,
        uncovered_non_runtime_unclassified_capability_ids=uncovered_non_runtime_unclassified,
    )


def _envelope_path(schema_dir: Path) -> Path:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_capability_inventory._envelope_path` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability_inventory._envelope_path` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - canonical.is_file: collaborator call used by this boundary
        - alt.is_file: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `_envelope_path`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_envelope_path`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_envelope_path`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_envelope_path`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_envelope_path`

    State and side effects:
        mutates canonical, alt.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory._envelope_path` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    canonical = schema_dir / "Envelope.json"
    if canonical.is_file():
        return canonical
    alt = schema_dir / "Envelope.schema.json"
    if alt.is_file():
        return alt
    return canonical


def _schema_dir_from_git_root() -> Path | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_capability_inventory._schema_dir_from_git_root` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory._schema_dir_from_git_root` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - Path.cwd: collaborator call used by this boundary
        - Path.resolve: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - exists: collaborator call used by this boundary
        - roots.append: collaborator call used by this boundary
        - resolve: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `_schema_dir_from_git_root`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_schema_dir_from_git_root`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `_schema_dir_from_git_root`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_schema_dir_from_git_root`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_schema_dir_from_git_root`

    State and side effects:
        mutates roots, candidate.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory._schema_dir_from_git_root` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    roots: list[Path] = []
    for seed in (Path.cwd(), Path(__file__).resolve()):
        for parent in (seed, *seed.parents):
            if (parent / ".git").exists():
                roots.append(parent)
                break
    for root in roots:
        candidate = (root / SCHEMA_RELATIVE_DIR).resolve()
        if _envelope_path(candidate).is_file():
            return candidate
    return Nothing.value_or(None)


def resolve_messages_schema_dir(preferred: Path | None = None) -> Path:
    """
    Locate the directory containing the cucumber-messages schema envelope definition.

    Returns:
        A resolved Path pointing to the verified schema directory.

    Raises:
        FileNotFoundError: If no valid directory with an Envelope schema can be found.

    Responsibility:
        Locate the directory containing the cucumber-messages schema envelope definition. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.resolve_messages_schema_dir` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - candidates.append: collaborator call used by this boundary
        - Path.resolve: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - candidates.extend: collaborator call used by this boundary
        - Path.cwd: collaborator call used by this boundary
        - _schema_dir_from_git_root: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `resolve_messages_schema_dir`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `resolve_messages_schema_dir`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `resolve_messages_schema_dir`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `resolve_messages_schema_dir`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `resolve_messages_schema_dir`

    State and side effects:
        mutates candidates, package_schema_dir, git_candidate, resolved, paths.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.resolve_messages_schema_dir` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises FileNotFoundError; callers must treat these as boundary failures.

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
    candidates: list[Path] = []
    if preferred is not None:
        candidates.append(preferred)

    package_schema_dir = Path(__file__).resolve().parent / PACKAGE_SCHEMA_RELATIVE_DIR
    candidates.extend(
        (
            Path.cwd() / SCHEMA_RELATIVE_DIR,
            package_schema_dir,
            Path(__file__).resolve().parents[3] / SCHEMA_RELATIVE_DIR,
        ),
    )

    git_candidate = _schema_dir_from_git_root()
    if git_candidate is not None:
        candidates.append(git_candidate)

    for candidate in candidates:
        resolved = candidate.resolve()
        if _envelope_path(resolved).is_file():
            return resolved

    paths = ", ".join(str(path.resolve()) for path in candidates)
    msg = f"Unable to resolve messages schema directory with Envelope.json or Envelope.schema.json. Checked: {paths}"
    raise FileNotFoundError(msg)


def load_envelope_schema(schema_dir: Path | None = None) -> tuple[Path, JSONObject]:
    """
    Read and parse the main cucumber-messages Envelope schema definition into a JSON object.

    Returns:
        A tuple containing the resolved schema directory path and the parsed JSON schema payload.

    Responsibility:
        Read and parse the main cucumber-messages Envelope schema definition into a JSON object. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_capability_inventory.load_envelope_schema`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_messages_schema_dir: collaborator call used by this boundary
        - _envelope_path: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - json.loads: collaborator call used by this boundary
        - envelope_path.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `load_envelope_schema`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `load_envelope_schema`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `load_envelope_schema`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `load_envelope_schema`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `load_envelope_schema`

    State and side effects:
        mutates resolved_schema_dir, envelope_path.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.load_envelope_schema` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_path = _envelope_path(resolved_schema_dir)
    return resolved_schema_dir, cast("JSONObject", json.loads(envelope_path.read_text(encoding="utf-8")))


def sync_capability_inventory(
    baseline_release: str,
    source_entries: list[MessageCapability],
) -> CapabilitySyncResult:
    """
    Filter and merge a raw capability list into a standardized inventory format.

    Returns:
        A CapabilitySyncResult summarizing relevant capabilities, out-of-scope counts, and duplicates.

    Responsibility:
        Filter and merge a raw capability list into a standardized inventory format. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_capability_inventory.sync_capability_inventory` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - duplicates.add: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary
        - synchronized.append: collaborator call used by this boundary
        - MessageCapability: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `sync_capability_inventory`
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `sync_capability_inventory`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `sync_capability_inventory`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `sync_capability_inventory`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `sync_capability_inventory`

    State and side effects:
        mutates seen, duplicates, synchronized, total_relevant, total_out_of_scope.

    Invariants:
        - `pytest_bdd.model.message_capability_inventory.sync_capability_inventory` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    seen: set[str] = set()
    duplicates: set[str] = set()
    synchronized: list[MessageCapability] = []

    for entry in source_entries:
        if entry.capability_id in seen:
            duplicates.add(entry.capability_id)
            continue
        seen.add(entry.capability_id)
        synchronized.append(
            MessageCapability(
                capability_id=entry.capability_id,
                baseline_release=baseline_release,
                name=entry.name,
                description=entry.description,
                category=entry.category,
                affects=entry.affects,
                source_reference=entry.source_reference,
                explicit_relevance=entry.explicit_relevance,
            ),
        )

    total_relevant = sum(1 for capability in synchronized if capability_is_relevant(capability))
    total_out_of_scope = len(synchronized) - total_relevant

    return CapabilitySyncResult(
        total_relevant=total_relevant,
        total_out_of_scope=total_out_of_scope,
        duplicate_capability_ids=tuple(sorted(duplicates)),
        capabilities=tuple(synchronized),
    )
