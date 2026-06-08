from typing import Any

class Group:
    value: str
    start: int
    end: int
    children: list[Group]
    values: Any
    def __init__(self, value: str, start: int, end: int, children: list[Group]) -> None: ...
