from typing import Any

class ValidationError(Exception):
    message: str
    absolute_path: tuple[Any, ...]
    absolute_schema_path: tuple[Any, ...]
    validator: str | None
    json_path: str
    path: tuple[Any, ...]
    schema_path: tuple[Any, ...]
    relative_path: tuple[Any, ...]
    relative_schema_path: tuple[Any, ...]
    instance: Any
    schema: Any
    context: list[ValidationError]
    validator_value: Any
