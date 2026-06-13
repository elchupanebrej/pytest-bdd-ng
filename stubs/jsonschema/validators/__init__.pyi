from collections.abc import Iterator
from typing import Any

from jsonschema import ValidationError

class _Validator:
    @classmethod
    def check_schema(cls, schema: Any, format_checker: Any = ...) -> None: ...
    def __init__(
        self,
        schema: Any,
        resolver: Any = ...,
        format_checker: Any | None = ...,
        *,
        registry: Any = ...,
    ) -> None: ...
    def iter_errors(self, instance: Any, _schema: Any = ...) -> Iterator[ValidationError]: ...

def validator_for(schema: Any, default: Any = ...) -> type[_Validator]: ...
