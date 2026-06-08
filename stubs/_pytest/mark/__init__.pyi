from typing import Any

class Mark:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

class MarkDecorator: ...

class MarkMatcher:
    @staticmethod
    def from_markers(*markers: Any) -> MarkMatcher: ...
