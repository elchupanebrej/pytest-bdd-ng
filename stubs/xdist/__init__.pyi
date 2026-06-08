from typing import Any

class WorkerController:
    def send(self, name: str, **kwargs: Any) -> None: ...
    def ensure_shutdown(self) -> None: ...
    def process_from_remote(self, events: Any) -> None: ...

class Marker:
    END: Marker
    def __init__(self, name: str, kwargs: dict[str, Any] = ...) -> None: ...
    @property
    def name(self) -> str: ...

# Module `xdist.workermanage` — re-exported symbols
class workermanage:
    WorkerController: type[WorkerController]
    Marker: type[Marker]
