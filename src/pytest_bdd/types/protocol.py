from typing import Any, Protocol, Union, runtime_checkable

from pytest_bdd.util.other import IdGenerator


@runtime_checkable
class PytestBDDIdGeneratorHandler(Protocol):
    pytest_bdd_id_generator: Union["IdGenerator", Any]
