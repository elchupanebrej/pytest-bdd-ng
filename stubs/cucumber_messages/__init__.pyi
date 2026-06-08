from typing import Any

class _PydanticBase:
    def __init__(self, **data: Any) -> None: ...

class Envelope(_PydanticBase):
    attachment: Any | None
    gherkin_document: Any | None
    hook: Any | None
    meta: Any | None
    parameter_type: Any | None
    parse_error: Any | None
    pickle: Any | None
    source: Any | None
    step_definition: Any | None
    suggestion: Any | None
    test_case: Any | None
    test_case_finished: Any | None
    test_case_started: Any | None
    test_run_finished: Any | None
    test_run_started: Any | None
    test_step_finished: Any | None
    test_step_started: Any | None
    undefined_parameter_type: Any | None

class GherkinDocument(_PydanticBase):
    uri: str | None
    feature: Any | None
    comments: list[Any]

class Pickle(_PydanticBase):
    id: str
    uri: str
    name: str
    language: str
    steps: list[Any]
    tags: list[Any]
    ast_node_ids: list[str]

class PickleStep(_PydanticBase):
    id: str
    text: str
    type: Any
    argument: Any | None
    ast_node_ids: list[str]

class Source(_PydanticBase):
    uri: str
    data: str
    media_type: Any

class SourceMediaType(_PydanticBase):
    text_x_cucumber_gherkin_markdown: SourceMediaType
    text_x_cucumber_gherkin_plain: SourceMediaType

class Feature(_PydanticBase): ...

class StepKeywordType(_PydanticBase):
    value: Any
    unknown: StepKeywordType
    context: StepKeywordType
    action: StepKeywordType
    outcome: StepKeywordType
    conjunction: StepKeywordType

class Rule(_PydanticBase): ...

class Scenario(_PydanticBase):
    id: str
    keyword: str
    name: str
    description: str
    location: Any
    steps: list[Any]
    examples: list[Any]
    tags: list[Any]

class Background(_PydanticBase): ...
class Examples(_PydanticBase): ...

class TableRow(_PydanticBase):
    id: str
    cells: list[Any]
    location: Any

class TableCell(_PydanticBase): ...
class Tag(_PydanticBase): ...
class Comment(_PydanticBase): ...
class DocString(_PydanticBase): ...

class DataTable(_PydanticBase):
    rows: list[Any]

class Location(_PydanticBase):
    line: int
    column: int

class PickleStepType(_PydanticBase):
    value: Any
    unknown: PickleStepType
    context: PickleStepType
    action: PickleStepType
    outcome: PickleStepType

class Hook(_PydanticBase):
    id: str
    type: Any | None
    source_reference: Any
    tag_expression: Any | None

class HookType(_PydanticBase):
    before_test_run: HookType
    after_test_run: HookType
    before_test_case: HookType
    after_test_case: HookType
    before_test_step: HookType
    after_test_step: HookType

class JavaMethod(_PydanticBase): ...
class JavaStackTraceElement(_PydanticBase): ...
class SourceReference(_PydanticBase): ...
class Attachment(_PydanticBase): ...

class AttachmentContentEncoding(_PydanticBase):
    identity: AttachmentContentEncoding
    base64: AttachmentContentEncoding

class Exception(_PydanticBase): ...
class StepDefinitionPattern(_PydanticBase): ...

class StepDefinitionPatternType(_PydanticBase):
    cucumber_expression: StepDefinitionPatternType
    regular_expression: StepDefinitionPatternType

class StepDefinition(_PydanticBase):
    id: str
    pattern: Any
    source_reference: Any

class StepMatchArgument(_PydanticBase): ...
class StepMatchArgumentsList(_PydanticBase): ...

class Group(_PydanticBase):
    children: list[Group]
    start: int | None
    value: str | None

class ParameterType(_PydanticBase): ...

class TestCase(_PydanticBase):
    id: str
    pickle_id: str
    test_steps: list[Any]

class TestStep(_PydanticBase):
    id: str
    pickle_step_id: str | None
    step_definition_ids: list[str] | None
    step_match_arguments_lists: list[Any] | None

class TestCaseStarted(_PydanticBase):
    id: str
    test_case_id: str
    timestamp: Any
    attempt: int

class TestCaseFinished(_PydanticBase):
    test_case_started_id: str
    timestamp: Any
    will_be_retried: bool

class TestStepStarted(_PydanticBase): ...
class TestStepFinished(_PydanticBase): ...
class TestStepResult(_PydanticBase): ...

class TestStepResultStatus(_PydanticBase):
    unknown: TestStepResultStatus
    passed: TestStepResultStatus
    skipped: TestStepResultStatus
    pending: TestStepResultStatus
    undefined: TestStepResultStatus
    ambiguous: TestStepResultStatus
    failed: TestStepResultStatus

class Timestamp(_PydanticBase):
    seconds: int
    nanos: int

class Duration(_PydanticBase): ...
class Snippet(_PydanticBase): ...
class Suggestion(_PydanticBase): ...
class UndefinedParameterType(_PydanticBase): ...
class NoPreviousStep(_PydanticBase): ...
class Meta(_PydanticBase): ...
class Product(_PydanticBase): ...
class Ci(_PydanticBase): ...

class TestRunStarted(_PydanticBase):
    id: str
    timestamp: Any

class TestRunFinished(_PydanticBase): ...
class TestRunHookStarted(_PydanticBase): ...
class TestRunHookFinished(_PydanticBase): ...

json_converter: Any
