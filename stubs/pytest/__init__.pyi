from collections.abc import Callable
from typing import Any, NoReturn

from pluggy import HookimplMarker, HookspecMarker

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

class Stash: ...

class Item:
    session: Any
    parent: Any
    config: Any
    nodeid: Any
    name: str
    def add_marker(self, marker: Any) -> None: ...
    def iter_markers(self, name: str | None = ...) -> Any: ...
    def getfixturevalue(self, name: str) -> Any: ...

class Metafunc:
    config: Any
    definition: Any
    function: Any
    fixturenames: Any
    def parametrize(self, *args: Any, **kwargs: Any) -> None: ...

class Function: ...

class Parser:
    def addini(self, name: str, help: str, type: str | None = ..., default: Any = ...) -> Any: ...

class Session:
    config: Any
    items: Any
    exitstatus: Any

class Collector:
    session: Any
    config: Any

class FixtureDef:
    func: Any
    cached_result: Any
    def __init__(self, *args: Any, _ispytest: bool = ..., **kwargs: Any) -> None: ...

class FixtureLookupError(Exception): ...

class FixtureRequest:
    config: Any
    session: Any
    node: Any
    _fixturemanager: Any
    _fixture_defs: Any
    _pyfuncitem: Any
    fixturenames: Any
    def getfixturevalue(self, name: str) -> Any: ...
    def addfinalizer(self, func: Any) -> None: ...

class Mark:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    def __init__(
        self,
        name: str,
        args: tuple[Any, ...] = ...,
        kwargs: dict[str, Any] = ...,
        _ispytest: bool = ...,
    ) -> None: ...

class MarkDecorator:
    mark: Mark
    def __init__(self, mark: Mark, _ispytest: bool = ...) -> None: ...
    def with_args(self, *args: Any, **kwargs: Any) -> MarkDecorator: ...
    usefixtures: Callable[..., Any]
    skip: Callable[..., Any]

class MarkMatcher:
    @staticmethod
    def from_markers(*markers: Any) -> MarkMatcher: ...

class MarkMatcherFunction: ...

class RunResult:
    stdout: Any
    stderr: Any
    ret: Any

class TestReport:
    when: Any
    failed: Any
    skipped: Any
    passed: Any
    scenario: Any
    item: Any
    nodeid: Any
    outcome: Any
    longrepr: Any
    head_line: Any
    caplog: Any
    capstderr: Any
    capstdout: Any
    duration: Any
    keywords: Any

class CallInfo:
    when: Any
    excinfo: ExceptionInfo | None

class TerminalReporter:
    config: Any
    verbosity: int
    stats: dict[str, list[Any]]
    _tw: Any
    def ensure_newline(self) -> None: ...
    def write_sep(self, sep: str, title: str | None = ..., **kwargs: Any) -> None: ...
    def write(self, s: str, **kwargs: Any) -> None: ...
    def write_line(self, s: str, **kwargs: Any) -> None: ...
    def section(self, title: str, sep: str = ..., **kwargs: Any) -> None: ...
    def line(self, s: str, **kwargs: Any) -> None: ...
    def flush(self) -> None: ...

class NotSetType: ...

class PytestPluginManager:
    hook: Any
    def register(self, plugin: Any, name: str | None = ...) -> Any: ...
    def unregister(self, plugin: Any) -> Any: ...
    def add_hookspecs(self, module_or_class: Any) -> None: ...

class Scope: ...
class _ScopeName: ...
class Testdir: ...

class Module:
    obj: Any
    config: Any
    session: Any
    fspath: Any
    path: Any
    @classmethod
    def from_parent(cls, parent: Any, *, path: Any) -> Module: ...
    @staticmethod
    def skip(reason: str) -> NoReturn: ...

class UsageError(Exception): ...

class ExceptionInfo:
    type: Any
    value: Any
    traceback: Any
    @staticmethod
    def from_current() -> ExceptionInfo: ...

hookimpl: HookimplMarker  # re-exported from pluggy
hookspec: HookspecMarker  # re-exported from pluggy

def fixture(*args: Any, **kwargs: Any) -> Any: ...
def mark(*args: Any, **kwargs: Any) -> MarkDecorator: ...
def call_fixture_func(*args: Any, **kwargs: Any) -> Any: ...
def wrap_session(*args: Any, **kwargs: Any) -> Any: ...
def _prepareconfig(*args: Any, **kwargs: Any) -> Any: ...
def fail(reason: str, *, pytrace: bool = True) -> NoReturn: ...
def skip(*args: Any, **kwargs: Any) -> NoReturn: ...
def exit(msg: str, returncode: int = ...) -> NoReturn: ...
def set_trace() -> None: ...
def param(*args: Any, **kwargs: Any) -> Any: ...
