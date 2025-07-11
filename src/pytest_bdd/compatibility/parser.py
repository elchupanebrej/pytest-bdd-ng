from pathlib import Path
from typing import TYPE_CHECKING, Optional, Protocol, Union, runtime_checkable

from attr import attrib, attrs

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestBDDIdGenerator
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model.gherkin_document import Feature


@runtime_checkable
@attrs
class ParserProtocol(Protocol):
    id_generator: Optional[IdGenerator] = attrib(default=None, kw_only=True)

    def parse(
        self,
        config: Union[Config, HasPytestBDDIdGenerator],
        path: Path,
        uri: str,
        *args,
        **kwargs,
    ) -> tuple["Feature", str]:  # pragma: no cover
        ...
