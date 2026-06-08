from typing import Any

class CucumberExpression:
    expression: str
    parameter_type_registry: Any
    tree_regexp: Any
    regexp: Any
    def __init__(self, expression: str, parameter_type_registry: Any) -> None: ...
    def match(self, text: str) -> list[Any] | None: ...
