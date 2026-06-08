from typing import Any

class FixtureDef:
    func: Any
    cached_result: Any

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

def call_fixture_func(*args: Any, **kwargs: Any) -> Any: ...
def fixture(*args: Any, **kwargs: Any) -> Any: ...
