"""Feature legacy shim."""

from __future__ import annotations

from typing import cast

from attr import Factory, attrib, attrs


@attrs
class Feature:
    gherkin_document = attrib(default=None)
    uri: str = attrib(default="")
    filename: str = attrib(default="")

    registry: dict = attrib(default=Factory(dict))

    @property
    def name(self) -> str | None:
        if self.gherkin_document and self.gherkin_document.feature is not None:
            return cast("str", self.gherkin_document.feature.name)
        return None

    @property
    def rel_filename(self):
        file_schema = "file"
        if self.uri.startswith(file_schema):
            return self.uri[len(file_schema) + 1 :]
        return None
