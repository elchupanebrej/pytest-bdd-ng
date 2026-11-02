"""Callable provenance in the historical Messages source-reference representation."""

from __future__ import annotations

from inspect import getfile, getsourcelines, signature
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pytest_cuke.model.message_types import JavaMethod, JavaStackTraceElement, Location, SourceReference

if TYPE_CHECKING:
    from collections.abc import Callable


def callable_source_reference(
    function: Callable[..., Any], *, uri: str | None = None, location: Location | None = None
) -> SourceReference | None:
    """Return available Python provenance, retaining the established Java-named fields."""
    try:
        source_file = Path(getfile(function))
        source_line = getsourcelines(function)[1]
        parameter_names = list(signature(function).parameters)
        source_uri = uri if uri is not None else source_file.resolve().as_uri()
    except (OSError, TypeError, ValueError):
        return None
    module = str(getattr(function, "__module__", "pytest_cuke"))
    name = str(getattr(function, "__name__", type(function).__name__))
    return SourceReference(
        uri=source_uri,
        location=location if location is not None else Location(line=source_line, column=1),
        java_method=JavaMethod(class_name=module, method_name=name, method_parameter_types=parameter_names),
        java_stack_trace_element=JavaStackTraceElement(class_name=module, file_name=source_file.name, method_name=name),
    )
