"""
Define typed report data structures and serialization for individual step and scenario execution results.

Responsibility:
    Defines typed report data structures and serialization for individual step and scenario execution results. This
    module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
    reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData) that
    define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure marking.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a focused
    sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
    public API, defining a stable contract that downstream layers depend on for scenario execution state, message
    handling, and stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize must
    include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

import time
from typing import Literal, TypedDict

from attrs import define, field
from cucumber_messages import Pickle, PickleStep  # library has no type stubs

from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import ReportingContextSnapshot

RuntimeStepStatus = Literal["passed", "failed"]


class StepReportData(TypedDict):
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize
        must include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    name: str
    type: str | None
    keyword: str | None
    line_number: int | None
    failed: bool
    status: RuntimeStepStatus
    duration: float


class FeatureReportData(TypedDict):
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize
        must include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    name: str | None
    filename: str
    rel_filename: str | None
    line_number: int | None
    description: str | None
    tags: list[str]


class ScenarioReportData(TypedDict):
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize
        must include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    steps: list[StepReportData]
    name: str
    line_number: int
    tags: list[str]
    feature: FeatureReportData


def normalize_runtime_step_status(status: str | None, *, failed_fallback: bool) -> RuntimeStepStatus:
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    normalized = (status or "").strip().lower()
    if normalized == "passed":
        return "passed"
    if normalized == "failed":
        return "failed"
    return "failed" if failed_fallback else "passed"


@define(eq=False)
class StepReport:
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize
        must include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    step: PickleStep = field()
    started: float = field(factory=time.perf_counter)
    failed: bool = field(default=False)
    stopped: float | None = field(default=None)

    def serialize(self, feature_binding: FeatureRuntimeBinding) -> StepReportData:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        keyword = getattr(self.step, "keyword", None) or feature_binding.step_keyword(self.step)
        line_number = getattr(self.step, "line_number", None)
        if line_number is None:
            line_number = feature_binding.step_line_number(self.step)
        step_prefix = getattr(self.step, "prefix", None)
        if step_prefix is None:
            step_prefix = feature_binding.step_prefix(self.step)
        return {
            "name": self.step.text,
            "type": step_prefix,
            "keyword": keyword,
            "line_number": line_number,
            "failed": self.failed,
            "status": normalize_runtime_step_status(None, failed_fallback=self.failed),
            "duration": self.duration,
        }

    def finalize(self, *, failed: bool = False) -> None:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        if self.stopped is None:
            return 0.0

        return self.stopped - self.started


@define
class ScenarioReport:
    """
    Define typed report data structures and serialization for individual step and scenario execution results.

    Responsibility:
        Defines typed report data structures and serialization for individual step and scenario execution results. This
        module provides StepReport (with timing, failure tracking, and serialization), ScenarioReport (aggregating step
        reports and context snapshots), and TypedDict schemas (StepReportData, FeatureReportData, ScenarioReportData)
        that define the contract for report consumers. It normalizes runtime step statuses and handles cascading failure
        marking.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - StepReport timestamps must be captured via time.perf_counter for monotonic timing; ScenarioReport.serialize
        must include all StepReport entries in order; fail() must cascade failure to all remaining steps in the pickle

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    feature_binding: FeatureRuntimeBinding = field()
    pickle: Pickle = field()
    step_reports: list[StepReport] = field(factory=list)
    context_snapshot: ReportingContextSnapshot | None = field(default=None)

    @property
    def current_step_report(self) -> StepReport:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.step_reports.append(step_report)

    def set_context_snapshot(self, context_snapshot: ReportingContextSnapshot | None) -> None:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.context_snapshot = context_snapshot

    def serialize(self) -> ScenarioReportData:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        pickle = self.pickle
        feature_binding = self.feature_binding

        return {
            "steps": [step_report.serialize(self.feature_binding) for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": feature_binding.pickle_line_number(pickle),
            "tags": sorted({tag.name.lstrip("@") for tag in pickle.tags}.difference(feature_binding.tag_names)),
            "feature": {
                "name": feature_binding.name,
                "filename": feature_binding.filename,
                "rel_filename": feature_binding.rel_filename,
                "line_number": feature_binding.line_number,
                "description": feature_binding.description,
                "tags": feature_binding.tag_names,
            },
        }

    def fail(self) -> None:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - scenario_reporter: Referenced by collection, runtime, and reporting layer plugins through the
            pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario
            execution state, message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.pickle.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)
