from __future__ import annotations

try:
    import pydantic as _pydantic  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "pydantic":
        raise
    raise ImportError("Structured BDD support requires Pydantic; install pytest-cuke[struct-bdd]") from error
