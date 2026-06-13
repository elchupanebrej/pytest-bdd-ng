"""Allure3 result model types defined with attrs."""

from __future__ import annotations

from uuid import uuid4

from attrs import define, field


@define
class AllureStatusDetails:
    """Status details for an Allure result item."""

    message: str = ""
    trace: str = ""
    actual: str = ""
    expected: str = ""
    known: bool = False
    flaky: bool = False


@define
class AllureLabel:
    """A label attached to an Allure test result."""

    name: str = ""
    value: str = ""


@define
class AllureLink:
    """A link attached to an Allure test result."""

    name: str = ""
    url: str = ""
    type: str = "link"


@define
class AllureAttachment:
    """A file attachment on an Allure result item."""

    name: str = ""
    source: str = ""
    type: str = ""
    size: int = 0
    body: str | None = None
    content_encoding: str | None = None


@define
class AllureParameter:
    """A parameter on an Allure result item."""

    name: str = ""
    value: str = ""
    excluded: bool = False
    mode: str = "default"


@define
class AllureStepResult:
    """A single step within an Allure test result."""

    name: str = ""
    uuid: str = field(factory=lambda: str(uuid4()))
    status: str = "unknown"
    statusDetails: AllureStatusDetails = field(factory=AllureStatusDetails)
    stage: str = "finished"
    description: str = ""
    descriptionHtml: str = ""
    start: int = 0
    stop: int = 0
    steps: list[AllureStepResult] = field(factory=list)
    attachments: list[AllureAttachment] = field(factory=list)
    parameters: list[AllureParameter] = field(factory=list)


@define
class AllureTestResult:
    """A complete Allure3 test result (maps to *-result.json)."""

    uuid: str = field(factory=lambda: str(uuid4()))
    name: str = ""
    fullName: str = ""
    historyId: str = ""
    testCaseId: str = ""
    status: str = "unknown"
    statusDetails: AllureStatusDetails = field(factory=AllureStatusDetails)
    stage: str = "finished"
    description: str = ""
    descriptionHtml: str = ""
    labels: list[AllureLabel] = field(factory=list)
    links: list[AllureLink] = field(factory=list)
    steps: list[AllureStepResult] = field(factory=list)
    attachments: list[AllureAttachment] = field(factory=list)
    parameters: list[AllureParameter] = field(factory=list)
    start: int = 0
    stop: int = 0


@define
class AllureFixtureResult:
    """A fixture (before/after) result within a container."""

    name: str = ""
    uuid: str = field(factory=lambda: str(uuid4()))
    type: str = "before"
    testResults: list[str] = field(factory=list)
    status: str = "unknown"
    statusDetails: AllureStatusDetails = field(factory=AllureStatusDetails)
    stage: str = "finished"
    description: str = ""
    descriptionHtml: str = ""
    start: int = 0
    stop: int = 0
    steps: list[AllureStepResult] = field(factory=list)
    attachments: list[AllureAttachment] = field(factory=list)
    parameters: list[AllureParameter] = field(factory=list)


@define
class AllureContainer:
    """An Allure3 test result container (maps to *-container.json)."""

    uuid: str = field(factory=lambda: str(uuid4()))
    name: str = "Test results"
    children: list[str] = field(factory=list)
    befores: list[AllureFixtureResult] = field(factory=list)
    afters: list[AllureFixtureResult] = field(factory=list)
    links: list[AllureLink] = field(factory=list)
    start: int = 0
    stop: int = 0
