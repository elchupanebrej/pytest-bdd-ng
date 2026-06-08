from collections.abc import Callable
from typing import Any

def function_decorator(*args: Any, **kwargs: Any) -> Callable[..., Any]: ...
