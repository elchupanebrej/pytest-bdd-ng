from typing import Any

class Compiler:
    def __init__(self, id_generator: Any | None = None) -> None: ...
    def compile(self, gherkin_document: Any) -> list[Any]: ...

class GherkinDocumentWithURI:
    gherkin_document: Any
    uri: str
