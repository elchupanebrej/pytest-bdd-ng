from typing import Any

class CompositeParserException(Exception):
    errors: list[Any]
