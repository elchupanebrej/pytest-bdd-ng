from typing import Any

class Metafunc:
    config: Any
    definition: Any
    function: Any
    fixturenames: Any
    def parametrize(self, *args: Any, **kwargs: Any) -> None: ...
