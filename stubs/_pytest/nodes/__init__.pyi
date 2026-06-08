from typing import Any

class Collector:
    session: Any
    config: Any

class Item:
    session: Any
    parent: Any
    config: Any
    nodeid: Any
    name: str
    def add_marker(self, marker: Any) -> None: ...
    def iter_markers(self, name: str | None = ...) -> Any: ...
    def getfixturevalue(self, name: str) -> Any: ...
