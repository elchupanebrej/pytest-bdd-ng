"""
Provide toolz extra helpers.

Responsibility:
    Provide toolz extra helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.toolz_extra` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - DefaultMapping: owns nested behavior below this boundary
    - itemgetter_: owns nested behavior below this boundary
    - Empty: owns nested behavior below this boundary
    - getitemdefault: owns nested behavior below this boundary
    - deepattrgetter: owns nested behavior below this boundary
    - setdefaultattr: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/hook.py: imports or references `toolz_extra`
    - src/pytest_bdd/model/feature_binding.py: imports or references `toolz_extra`
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `toolz_extra`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `toolz_extra`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `toolz_extra`

State and side effects:
    mutates value, msg, items, empty, item; depends on __future__.annotations, collections.defaultdict,
    collections.abc.Callable, collections.abc.Collection, collections.abc.Mapping.

Invariants:
    - `pytest_bdd.util.toolz_extra` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises ValueError, KeyError, re-raise; callers must treat these as boundary failures.

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

from collections import defaultdict
from collections.abc import Callable, Collection, Mapping
from contextlib import nullcontext, suppress
from enum import Enum
from functools import reduce
from itertools import chain, tee
from operator import attrgetter, getitem, itemgetter
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

_MISSING = object()


class DefaultMapping(defaultdict[object, object]):
    """
    Represent default mapping state.

    Raises:
        KeyError: If the operation cannot be completed.

    Responsibility:
        Represent default mapping state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.DefaultMapping` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - __missing__: owns nested behavior below this boundary
        - warm_up: owns nested behavior below this boundary
        - instantiate_from_collection_or_bool: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `DefaultMapping`
        - src/pytest_bdd/model/feature_binding.py: imports or references `DefaultMapping`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `DefaultMapping`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `DefaultMapping`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `DefaultMapping`

    State and side effects:
        mutates value, items, Skip, intercessor, bool_or_items.

    Invariants:
        - `pytest_bdd.util.toolz_extra.DefaultMapping` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises KeyError; callers must treat these as boundary failures.

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

    Skip = object()

    def __init__(
        self,
        *args: object,
        default_factory: Callable[[], object] | None = None,
        warm_up_keys: Collection[object] = (),
        **kwargs: object,
    ) -> None:
        """
        Initialize the default mapping.

        Responsibility:
            Initialize the default mapping. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.DefaultMapping.__init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary
            - self.warm_up: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/hook.py: imports or references `__init__`

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
        super().__init__(default_factory, *args, **kwargs)
        self.warm_up(*warm_up_keys)

    def __missing__(self, key: object) -> object:
        """
        Return a fallback value for missing keys.

        Args:
            key: Missing key to look up.

        Returns:
            Fallback value for the key.

        Raises:
            KeyError: If missing-key fallback is disabled or unavailable.

        Responsibility:
            Return a fallback value for missing keys. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.DefaultMapping.__missing__` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.keys: collaborator call used by this boundary
            - KeyError: collaborator call used by this boundary
            - callable: collaborator call used by this boundary
            - intercessor: collaborator call used by this boundary
            - super.__missing__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `__missing__`
            - src/pytest_bdd/model/feature_binding.py: imports or references `__missing__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `__missing__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__missing__`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `__missing__`

        State and side effects:
            mutates value, intercessor.

        Invariants:
            - `pytest_bdd.util.toolz_extra.DefaultMapping.__missing__` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises KeyError; callers must treat these as boundary failures.

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
        if ... in self.keys():
            intercessor = self[...]
            if intercessor is self.Skip:
                raise KeyError(key)
            if callable(intercessor):
                value = intercessor(key)
            elif intercessor is ...:
                value = key
            else:
                value = intercessor
            self[key] = value
            return value
        return super().__missing__(key)

    def warm_up(self, *items: object) -> None:
        """
        Handle warm up.

        Responsibility:
            Handle warm up. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.DefaultMapping.warm_up` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - getitem: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `warm_up`
            - src/pytest_bdd/model/feature_binding.py: imports or references `warm_up`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `warm_up`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `warm_up`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `warm_up`

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
        for item in items:
            with suppress(KeyError):
                getitem(self, item)

    @classmethod
    def instantiate_from_collection_or_bool(
        cls,
        bool_or_items: object = _MISSING,
        *,
        warm_up_keys: Collection[object] = (),
    ) -> DefaultMapping:
        """
        Create a DefaultMapping from a collection or boolean.

        Args:
            bool_or_items: Collection, boolean, or missing sentinel.
            warm_up_keys: Keys to warm up on creation.

        Returns:
            New DefaultMapping instance.

        Responsibility:
            Create a DefaultMapping from a collection or boolean. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.toolz_extra.DefaultMapping.instantiate_from_collection_or_bool` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - zip: collaborator call used by this boundary
            - tee: collaborator call used by this boundary
            - iter: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `instantiate_from_collection_or_bool`
            - src/pytest_bdd/model/feature_binding.py: imports or references `instantiate_from_collection_or_bool`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `instantiate_from_collection_or_bool`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `instantiate_from_collection_or_bool`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `instantiate_from_collection_or_bool`

        State and side effects:
            mutates items, bool_or_items.

        Invariants:
            - `pytest_bdd.util.toolz_extra.DefaultMapping.instantiate_from_collection_or_bool` keeps its documented
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
        if bool_or_items is _MISSING:
            bool_or_items = True
        if isinstance(bool_or_items, Collection):
            items: object = bool_or_items
            if not isinstance(bool_or_items, Mapping):
                items = zip(*tee(iter(bool_or_items)), strict=False)
        else:
            items = cast("dict[object, object]", {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(items, warm_up_keys=warm_up_keys)


def itemgetter_(*items: object) -> Callable[[object], object]:
    """
    Create an itemgetter that handles missing items.

    Args:
        items: Items to get from object.

    Returns:
        Item getter function.

    Responsibility:
        Create an itemgetter that handles missing items. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.itemgetter_` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - func: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `itemgetter_`
        - src/pytest_bdd/model/feature_binding.py: imports or references `itemgetter_`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `itemgetter_`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `itemgetter_`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `itemgetter_`

    State and side effects:
        mutates getter, result.

    Invariants:
        - `pytest_bdd.util.toolz_extra.itemgetter_` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    getter = cast("Callable[[object], object]", itemgetter(*items))

    def func(obj: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.util.toolz_extra.itemgetter_.func` owns documented function
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.itemgetter_.func` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - getter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_bridge.py: imports or references `func`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `func`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `func`
            - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `func`
            - src/pytest_bdd/hook.py: imports or references `func`

        State and side effects:
            mutates result.

        Invariants:
            - `pytest_bdd.util.toolz_extra.itemgetter_.func` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        if len(items) == 0:
            return []
        result = getter(obj)
        if len(items) == 1:
            return [result]
        return result

    return func


class Empty(Enum):
    """
    Represent empty state.

    Responsibility:
        Represent empty state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.Empty` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `Empty`
        - src/pytest_bdd/model/feature_binding.py: imports or references `Empty`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `Empty`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `Empty`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Empty`

    State and side effects:
        mutates empty.

    Invariants:
        - `pytest_bdd.util.toolz_extra.Empty` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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

    empty = None


def getitemdefault(
    obj: object,
    index: object,
    default: object = Empty.empty,
    default_factory: Callable[[], object] | None = None,
    treat_as_empty: object = Empty.empty,
) -> object:
    """
    Get item from object with default handling.

    Args:
        obj: Object to get item from.
        index: Index/key to retrieve.
        default: Default value if key missing.
        default_factory: Factory for default value.
        treat_as_empty: Value to treat as empty.

    Returns:
        Retrieved item or default.

    Raises:
        KeyError: If the operation cannot be completed.
        ValueError: If the operation cannot be completed.

    Responsibility:
        Get item from object with default handling. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.getitemdefault` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ValueError: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - getitem_: collaborator call used by this boundary
        - default_factory: collaborator call used by this boundary
        - KeyError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `getitemdefault`
        - src/pytest_bdd/model/feature_binding.py: imports or references `getitemdefault`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `getitemdefault`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `getitemdefault`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `getitemdefault`

    State and side effects:
        mutates msg, item, getitem_.

    Invariants:
        - `pytest_bdd.util.toolz_extra.getitemdefault` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError, re-raise, KeyError; callers must treat these as boundary failures.

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
    if default is not Empty.empty:
        if default_factory is not None:
            msg = "Both 'default' and 'default_factory' were specified"
            raise ValueError(msg)

        def default_factory() -> object:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.util.toolz_extra.getitemdefault.default_factory` owns
                documented function behavior. It directly owns the observable contract, local decisions, and maintenance
                boundary for this function.

            Reason for existence:
                This entity is the information expert for `pytest_bdd.util.toolz_extra.getitemdefault.default_factory`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - None, leaf-level implementation boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/hook.py: imports or references `default_factory`
                - src/pytest_bdd/model/feature_binding.py: imports or references `default_factory`
                - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
                  `default_factory`
                - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `default_factory`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `default_factory`

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
            return default

    getitem_ = cast("Callable[[object, object], object]", getitem)

    try:
        item = getitem_(obj, index)
    except KeyError:
        if default_factory is None:
            raise
        item = default_factory()
    if item is not treat_as_empty:
        return item
    msg = f"{index}"
    raise KeyError(msg)


def deepattrgetter(*attrs: str, **kwargs: object) -> Callable[[object], tuple[object, ...]]:
    """
    Get nested attributes from an object.

    Args:
        attrs: Attribute chain to traverse.
        **kwargs: Additional keyword arguments. Accepts "default" (default value if attribute missing)
            and "skip_missing" (whether to skip missing attributes).
        default: Default value if attribute missing.
        skip_missing: Whether to skip missing attributes.

    Returns:
        Function that extracts nested attributes.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Get nested attributes from an object. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.deepattrgetter` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - fn: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `deepattrgetter`
        - src/pytest_bdd/model/feature_binding.py: imports or references `deepattrgetter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `deepattrgetter`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `deepattrgetter`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `deepattrgetter`

    State and side effects:
        mutates empty, default, skip_missing, msg, default_exception_type.

    Invariants:
        - `pytest_bdd.util.toolz_extra.deepattrgetter` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    empty = object()
    default = kwargs.pop("default", empty)
    skip_missing = bool(kwargs.pop("skip_missing", False))

    if default is not empty and skip_missing:
        msg = 'Both "default" and "skip_missing" are specified'
        raise ValueError(msg)

    default_exception_type = AttributeError if default is not empty else _NoneExceptionError
    skip_missing_context = suppress(AttributeError) if skip_missing else nullcontext()

    def fn(obj: object) -> tuple[object, ...]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.util.toolz_extra.deepattrgetter.fn` owns documented function
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.deepattrgetter.fn` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `fn`
            - src/pytest_bdd/model/feature_binding.py: imports or references `fn`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `fn`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `fn`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `fn`

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

        def _() -> Iterable[object]:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.util.toolz_extra.deepattrgetter.fn._` owns documented
                function behavior. It directly owns the observable contract, local decisions, and maintenance boundary
                for this function.

            Reason for existence:
                This entity is the information expert for `pytest_bdd.util.toolz_extra.deepattrgetter.fn._` because it
                keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - attrgetter: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
                - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
                - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
                - src/pytest_bdd/collector_batch.py: imports or references `_`
                - src/pytest_bdd/hook.py: imports or references `_`

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
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:  # noqa: PERF203
                    yield default

        return tuple(_())

    return fn


def setdefaultattr(
    obj: object,
    key: str,
    value: Literal[Empty.empty] | object = Empty.empty,
    value_factory: Callable[[], object] | None = None,
) -> object:
    """
    Set attribute with default value handling.

    Args:
        obj: Object to modify.
        key: Attribute name to set.
        value: Value to set, or Empty.empty.
        value_factory: Factory for value if not provided.

    Returns:
        The value that was set.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Set attribute with default value handling. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.setdefaultattr` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ValueError: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - value_factory: collaborator call used by this boundary
        - setattr: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `setdefaultattr`
        - src/pytest_bdd/model/feature_binding.py: imports or references `setdefaultattr`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `setdefaultattr`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `setdefaultattr`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `setdefaultattr`

    State and side effects:
        mutates msg, value.

    Invariants:
        - `pytest_bdd.util.toolz_extra.setdefaultattr` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    if value is not Empty.empty and value_factory is not None:
        msg = "Both 'value' and 'value_factory' were specified"
        raise ValueError(msg)
    with suppress(AttributeError):
        return getattr(obj, key)
    if value_factory is not None:
        value = value_factory()
    setattr(obj, key, value)
    return value


class ObjectCallable(Protocol):
    """
    Represent object callable state.

    Responsibility:
        Represent object callable state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.ObjectCallable` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `ObjectCallable`
        - src/pytest_bdd/model/feature_binding.py: imports or references `ObjectCallable`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `ObjectCallable`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ObjectCallable`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `ObjectCallable`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.util.toolz_extra.ObjectCallable` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __call__(self, *args: object, **kwargs: object) -> object:
        """
        Handle call.

        Responsibility:
            Handle call. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.ObjectCallable.__call__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `__call__`
            - src/pytest_bdd/model/feature_binding.py: imports or references `__call__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `__call__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__call__`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `__call__`

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


def compose(*funcs: ObjectCallable) -> ObjectCallable:
    """
    Compose multiple functions into one.

    Args:
        funcs: Functions to compose (applied left to right).

    Returns:
        Composed function.

    Responsibility:
        Compose multiple functions into one. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.compose` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - reduce: collaborator call used by this boundary
        - f: collaborator call used by this boundary
        - g: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `compose`
        - src/pytest_bdd/model/feature_binding.py: imports or references `compose`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `compose`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `compose`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `compose`

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
    return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)


def flip(func: ObjectCallable | Callable[..., Any]) -> ObjectCallable | Callable[..., Any]:
    """
    Flip argument order of a binary function.

    Args:
        func: Function to flip.

    Returns:
        Function with flipped arguments.

    Responsibility:
        Flip argument order of a binary function. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra.flip` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - wrapped: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `flip`
        - src/pytest_bdd/model/feature_binding.py: imports or references `flip`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `flip`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `flip`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `flip`

    State and side effects:
        mutates first, last.

    Invariants:
        - `pytest_bdd.util.toolz_extra.flip` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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

    def wrapped(*args: object, **kwargs: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.util.toolz_extra.flip.wrapped` owns documented function
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_extra.flip.wrapped` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - func: collaborator call used by this boundary
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `wrapped`
            - src/pytest_bdd/model/feature_binding.py: imports or references `wrapped`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `wrapped`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `wrapped`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `wrapped`

        State and side effects:
            mutates first, last.

        Invariants:
            - `pytest_bdd.util.toolz_extra.flip.wrapped` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        if len(args) > 1:
            first, *other, last = args
            return func(last, *other, first, **kwargs)
        return func(*args, **kwargs)

    return wrapped


class _NoneExceptionError(Exception):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.toolz_extra._NoneExceptionError` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_extra._NoneExceptionError` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `_NoneExceptionError`
        - src/pytest_bdd/model/feature_binding.py: imports or references `_NoneExceptionError`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_NoneExceptionError`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `_NoneExceptionError`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_NoneExceptionError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.util.toolz_extra._NoneExceptionError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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


chain_map: ObjectCallable = compose(cast("ObjectCallable", chain.from_iterable), cast("ObjectCallable", map))
is_of_type = flip(isinstance)
