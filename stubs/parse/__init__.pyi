from collections.abc import Callable
from re import Pattern
from typing import Any

class Parser:
    def parse(self, string: str, evaluate_result: bool = ...) -> Result | None: ...
    _format: str
    _match_re: Pattern[str]

class Result:
    named: dict[str, Any]
    fixed: tuple[Any, ...]

class Match: ...

def parse(format: str, string: str, evaluate_result: bool = ...) -> Result: ...
def compile(format: str) -> Callable[..., Any]: ...
def findall(format: str, string: str, extra_types: Any = ...) -> list[Any]: ...
