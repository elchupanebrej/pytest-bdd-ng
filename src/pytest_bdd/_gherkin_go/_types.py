"""Exception types for the Go gherkin parser bridge."""


class GherkinGoNotAvailable(RuntimeError):
    """Raised when the Go shared library cannot be loaded."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Go gherkin parser not available: {reason}")
        self.reason = reason


class GherkinParseError(Exception):
    """
    Wraps structured parse errors from the Go parser.

    Maps to Python's CompositeParserException from gherkin.errors.
    """

    def __init__(self, errors: list[dict]) -> None:
        self.errors = errors
        messages = "; ".join(err.get("message", str(err)) for err in errors)
        super().__init__(f"Gherkin parse error(s): {messages}")
