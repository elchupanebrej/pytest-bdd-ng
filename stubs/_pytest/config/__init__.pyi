from typing import Any

class Config:
    stash: Any
    option: Any
    pluginmanager: Any
    hook: Any
    rootpath: Any
    invocation_params: Any
    args: Any
    _inicache: Any
    def getoption(self, name: str, default: Any = ...) -> Any: ...
    def getini(self, name: str) -> Any: ...
    def addinivalue_line(self, name: str, line: str) -> None: ...

class ExitCode:
    OK: Any
    TESTS_FAILED: Any
    INTERRUPTED: Any
    INTERNAL_ERROR: Any
    USAGE_ERROR: Any
    NO_TESTS_COLLECTED: Any

class PytestPluginManager:
    hook: Any
    def register(self, plugin: Any, name: str | None = ...) -> Any: ...
    def unregister(self, plugin: Any, name: str | None = ...) -> Any: ...
    def add_hookspecs(self, module_or_class: Any) -> None: ...

def _prepareconfig(*args: Any, **kwargs: Any) -> Any: ...
