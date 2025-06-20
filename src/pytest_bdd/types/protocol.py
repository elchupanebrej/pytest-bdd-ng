from typing import TYPE_CHECKING, Any, Protocol, Union, runtime_checkable

if TYPE_CHECKING:
    from pytest_bdd.util.other import IdGenerator


@runtime_checkable
class PytestBDDIdGeneratorHandler(Protocol):
    pytest_bdd_id_generator: Union["IdGenerator", Any]
