from typing import Any

class Session:
    config: Any
    items: Any
    exitstatus: Any

def wrap_session(*args: Any, **kwargs: Any) -> Any: ...
