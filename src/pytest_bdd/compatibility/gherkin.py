from typing import Optional

from gherkin.parser_types import GherkinDocument as BaseGherkinDocument


class GherkinDocument(BaseGherkinDocument):
    uri: Optional[str]
