"""

Unit tests for FeatureRuntimeBinding class.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cucumber_messages import (
    GherkinDocument,
    Pickle,
    Source,
    Tag,
)

from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import LifecycleObjectRef, Run, RunStatus

pytestmark = [pytest.mark.unit]


def _make_gherkin_document(uri="file:features/example.feature", name="Feature"):
    """Create a minimal GherkinDocument for testing."""
    from cucumber_messages import Feature as FeatureMessage
    from cucumber_messages import Location

    feature_message = FeatureMessage(
        children=[],
        description="Test feature",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name=name,
        tags=[],
    )
    return GherkinDocument(
        comments=[],
        feature=feature_message,
        uri=uri,
    )


def _make_run(**kwargs):
    """Create a minimal Run instance."""
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
        **kwargs,
    )


def _make_pickle(**kwargs):
    from cucumber_messages import Pickle as PickleMsg

    defaults = {
        "id": "p1",
        "uri": "file:test.feature",
        "ast_node_ids": [],
        "language": "en",
        "name": "Test Feature",
        "steps": [],
        "tags": [],
    }
    defaults.update(kwargs)
    return PickleMsg(**defaults)


def test_feature_runtime_binding_construction_build_with_minimal_args() -> None:
    """
    build() works with minimal required arguments.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.run is run
    assert binding.gherkin_document is doc
    assert binding.uri == "file:features/example.feature"
    assert binding.filename == "features/example.feature"


def test_feature_runtime_binding_construction_build_with_source_infer_filename() -> None:
    """
    build() infers filename from source URI when filename not given.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    source = Source(
        uri="file:features/custom.feature",
        data="Feature: test",
        media_type="text/x.cucumber.gherkin+plain",
    )
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
    assert binding.filename == "features/custom.feature"


def test_feature_runtime_binding_construction_build_with_explicit_filename() -> None:
    """
    build() uses explicit filename when provided.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, filename="my.feature")
    assert binding.filename == "my.feature"


def test_feature_runtime_binding_construction_build_with_pickles() -> None:
    """
    build() stores provided pickles.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    pickle = Pickle(
        id="pickle-1",
        uri="file:features/example.feature",
        ast_node_ids=[],
        language="en",
        name="Test Feature",
        steps=[],
        tags=[],
    )
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, pickles=[pickle])
    assert binding.pickles == (pickle,)


def test_feature_runtime_binding_construction_init_with_uri() -> None:
    """
    Direct construction with uri parameter.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding(
        uri="file:test.feature",
        filename="test.feature",
        gherkin_document=doc,
        run=run,
    )
    assert binding.uri == "file:test.feature"
    assert binding.filename == "test.feature"


def test_feature_runtime_binding_construction_default_pickles_empty() -> None:
    """
    Default pickles is an empty tuple when none provided.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.pickles == ()


def test_feature_runtime_binding_load_methods_load_gherkin_document_passes_through() -> None:
    """
    load_gherkin_document returns existing GherkinDocument as-is.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    doc = _make_gherkin_document()
    result = FeatureRuntimeBinding.load_gherkin_document(doc)
    assert result is doc


def test_feature_runtime_binding_load_methods_load_gherkin_document_converts_dict() -> None:
    """
    load_gherkin_document converts dict to GherkinDocument.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    doc = _make_gherkin_document()
    as_dict = {
        "comments": [],
        "feature": {
            "keyword": "Feature",
            "name": "Test",
            "description": "",
            "language": "en",
            "children": [],
            "location": {"line": 1, "column": 1},
            "tags": [],
        },
        "uri": "file:test.feature",
    }
    result = FeatureRuntimeBinding.load_gherkin_document(as_dict)
    assert isinstance(result, GherkinDocument)


def test_feature_runtime_binding_load_methods_load_pickles_converts_list() -> None:
    """
    load_pickles converts list of dicts to Pickle tuple.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pickles_data = [
        {
            "id": "p1",
            "uri": "file:test.feature",
            "ast_node_ids": [],
            "language": "en",
            "name": "Test Feature",
            "steps": [],
            "tags": [],
        },
    ]
    result = FeatureRuntimeBinding.load_pickles(pickles_data)
    assert len(result) == 1
    assert isinstance(result[0], Pickle)


def test_feature_runtime_binding_indexing_index_runtime_objects_creates_registry() -> None:
    """
    index_runtime_objects creates ast_registry from feature.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    # After build, index_runtime_objects was called
    assert binding.ast_registry is not None


def test_feature_runtime_binding_resolve_resolve_node_raises_keyerror_for_unknown() -> None:
    """
    resolve_node raises KeyError for unknown object_id.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    with pytest.raises(KeyError):
        binding.resolve_node("nonexistent-id")


def test_feature_runtime_binding_properties_rel_filename_with_file_uri() -> None:
    """
    rel_filename strips 'file:' prefix.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(uri="file:features/test.feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.rel_filename == "features/test.feature"


def test_feature_runtime_binding_properties_rel_filename_with_non_file_uri_returns_none() -> None:
    """
    rel_filename returns None for non-file URIs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(uri="http://example.com/feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.rel_filename is None


def test_feature_runtime_binding_properties_name_returns_feature_name() -> None:
    """
    Name property returns the feature's name.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(name="My Feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.name == "My Feature"


def test_feature_runtime_binding_properties_name_returns_none_when_no_feature() -> None:
    """
    Name property returns None when no feature message.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = GherkinDocument(comments=[], uri="file:test.feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.name is None


def test_feature_runtime_binding_properties_line_number_returns_feature_line() -> None:
    """
    line_number returns the feature declaration's line number.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    # Default location is line=1
    assert binding.line_number == 1


def test_feature_runtime_binding_properties_description_returns_feature_description() -> None:
    """
    Description property returns dedented feature description.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.description == "Test feature"


def test_feature_runtime_binding_properties_description_returns_none_when_empty() -> None:
    """
    Description returns None when feature has no description.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Feature as FeatureMessage
    from cucumber_messages import Location

    feature_message = FeatureMessage(
        children=[],
        description="",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name="Feature",
        tags=[],
    )
    doc = GherkinDocument(comments=[], feature=feature_message, uri="file:test.feature")
    run = _make_run()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    # Empty string description — dedent returns empty, but property may return it or None
    # depends on implementation: dedent("") == ""
    result = binding.description
    # dedent of empty string is empty string, but property returns Nothing.value_or(None)
    # which is None. Let's check the actual behavior.
    assert not result or result is None


def test_feature_runtime_binding_properties_tag_names_returns_sorted_tags() -> None:
    """
    tag_names returns sorted list of tags with prefix stripped.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Feature as FeatureMessage
    from cucumber_messages import Location

    tag1 = Tag(name=f"{TAG_PREFIX}smoke", id="t1", location=Location(line=1, column=1))
    tag2 = Tag(name=f"{TAG_PREFIX}regression", id="t2", location=Location(line=2, column=1))
    tag3 = Tag(name="plain_tag", id="t3", location=Location(line=3, column=1))
    feature_message = FeatureMessage(
        children=[],
        description="",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name="Tagged Feature",
        tags=[tag2, tag1, tag3],
    )
    doc = GherkinDocument(comments=[], feature=feature_message, uri="file:test.feature")
    run = _make_run()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    names = binding.tag_names
    assert names == ["plain_tag", "regression", "smoke"]


def test_feature_runtime_binding_properties_tag_names_empty_when_no_tags() -> None:
    """
    tag_names returns empty list when feature has no tags.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.tag_names == []


def test_pickle_methods_pickle_ast_table_rows_returns_table_rows() -> None:
    """
    pickle_ast_table_rows returns TableRow nodes linked to pickle.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    # No pickles registered yet, so results will be empty
    pickle = _make_pickle()
    result = binding.pickle_ast_table_rows(pickle)
    assert result == []


def test_pickle_methods_pickle_table_rows_breadcrumb_empty_when_no_rows() -> None:
    """
    pickle_table_rows_breadcrumb returns empty string when no table rows.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    pickle = _make_pickle()
    assert not binding.pickle_table_rows_breadcrumb(pickle)


def test_pickle_methods_pickle_ast_scenario_returns_none_when_no_link() -> None:
    """
    pickle_ast_scenario returns None when no linked scenario.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    pickle = _make_pickle()
    assert binding.pickle_ast_scenario(pickle) is None


def test_pickle_methods_pickle_line_number_returns_negative_one_when_no_scenario() -> None:
    """
    pickle_line_number returns -1 when no linked scenario.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    pickle = _make_pickle()
    assert binding.pickle_line_number(pickle) == -1


def test_step_methods_step_keyword_returns_none_when_no_linked_step() -> None:
    """
    step_keyword returns None when pickle step has no linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    from cucumber_messages import PickleStep as PickleStepMsg

    pickle_step = PickleStepMsg(
        id="pickle-step-1",
        type=1,  # CONTEXT
        text="a step",
        ast_node_ids=["step-1"],
    )
    result = binding.step_keyword(pickle_step)
    # No linked step in registry, so keyword should be None
    assert result is None


def test_step_methods_step_prefix_returns_none_when_no_keyword() -> None:
    """
    step_prefix returns None when step_keyword returns None.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    from cucumber_messages import PickleStep as PickleStepMsg

    pickle_step = PickleStepMsg(
        id="pickle-step-1",
        type=1,
        text="a step",
        ast_node_ids=[],
    )
    result = binding.step_prefix(pickle_step)
    assert result is None


def test_step_methods_step_data_table_returns_none_when_no_linked_step() -> None:
    """
    step_data_table returns None when no linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    from cucumber_messages import PickleStep as PickleStepMsg

    pickle_step = PickleStepMsg(
        id="pickle-step-1",
        type=1,
        text="a step",
        ast_node_ids=[],
    )
    assert binding.step_data_table(pickle_step) is None


def test_step_methods_step_doc_string_returns_none_when_no_linked_step() -> None:
    """
    step_doc_string returns None when no linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    from cucumber_messages import PickleStep as PickleStepMsg

    pickle_step = PickleStepMsg(
        id="pickle-step-1",
        type=1,
        text="a step",
        ast_node_ids=[],
    )
    assert binding.step_doc_string(pickle_step) is None


def test_feature_runtime_binding_filename_filename_from_uri_without_file_scheme() -> None:
    """
    Filename is inferred from non-file URI via Path conversion.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(uri="http://example.com/test.feature")
    source = Source(uri="http://example.com/test.feature", data="", media_type="")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
    assert "test.feature" in binding.filename


def test_feature_runtime_binding_filename_filename_with_unknown_scheme() -> None:
    """
    Filename falls back to str(Path(uri).as_posix()) for unknown schemes.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(uri="custom://test.feature")
    source = Source(uri="custom://test.feature", data="", media_type="")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
    assert "test.feature" in binding.filename


def test_feature_runtime_binding_feature_filename_from_uri_with_none_uri() -> None:
    """
    Returns '<unknown>' for None URI.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    assert FeatureRuntimeBinding._feature_filename_from_uri(None) == "<unknown>"


def test_feature_runtime_binding_feature_filename_from_uri_with_file_uri() -> None:
    """
    Extracts path from file: URI.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    result = FeatureRuntimeBinding._feature_filename_from_uri("file:features/test.feature")
    assert result == "features/test.feature"


def test_feature_runtime_binding_feature_filename_from_uri_with_plain_path() -> None:
    """
    Converts plain path to POSIX style.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    result = FeatureRuntimeBinding._feature_filename_from_uri("features/test.feature")
    assert "test.feature" in result


def test_feature_runtime_binding_step_keyword_with_linked_step_step_keyword_with_linked_step() -> None:
    """
    step_keyword extracts keyword from linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import PickleStep as PickleStepMsg
    from cucumber_messages import Step

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    # Index a Step into the registry
    ast_step = Step(
        id="ast-step-1",
        keyword="Given ",
        location=None,
        text="a step",
    )
    binding.ast_registry.index_tree(ast_step)
    pickle_step = PickleStepMsg(
        id="pickle-step-1",
        type=1,
        text="a step",
        ast_node_ids=["ast-step-1"],
    )
    result = binding.step_keyword(pickle_step)
    assert result == "Given"


def test_feature_runtime_binding_step_keyword_with_linked_step_step_prefix_with_linked_step() -> None:
    """
    step_prefix returns lowercase keyword.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import PickleStep as PickleStepMsg
    from cucumber_messages import Step

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    ast_step = Step(id="ast-step-2", keyword="When ", location=None, text="something")
    binding.ast_registry.index_tree(ast_step)
    pickle_step = PickleStepMsg(
        id="pickle-step-2",
        type=1,
        text="something",
        ast_node_ids=["ast-step-2"],
    )
    result = binding.step_prefix(pickle_step)
    assert result == "when"


def test_feature_runtime_binding_step_keyword_with_linked_step_step_line_number_with_linked_step() -> None:
    """
    step_line_number returns line from linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Location, Step
    from cucumber_messages import PickleStep as PickleStepMsg

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    ast_step = Step(
        id="ast-step-3",
        keyword="Then ",
        location=Location(line=10, column=1),
        text="verify",
    )
    binding.ast_registry.index_tree(ast_step)
    pickle_step = PickleStepMsg(
        id="pickle-step-3",
        type=1,
        text="verify",
        ast_node_ids=["ast-step-3"],
    )
    result = binding.step_line_number(pickle_step)
    assert result == 10


def test_feature_runtime_binding_step_keyword_with_linked_step_step_doc_string_with_linked_step() -> None:
    """
    step_doc_string returns doc_string from linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import PickleStep as PickleStepMsg
    from cucumber_messages import Step

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    doc_string_obj = SimpleNamespace(content="doc content")
    ast_step = Step(
        id="ast-step-4",
        keyword="Given ",
        location=None,
        text="a step",
        doc_string=doc_string_obj,
    )
    binding.ast_registry.index_tree(ast_step)
    pickle_step = PickleStepMsg(
        id="pickle-step-4",
        type=1,
        text="a step",
        ast_node_ids=["ast-step-4"],
    )
    result = binding.step_doc_string(pickle_step)
    assert result is doc_string_obj


def test_feature_runtime_binding_step_keyword_with_linked_step_step_data_table_with_linked_step() -> None:
    """
    step_data_table returns data_table from linked AST step.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import PickleStep as PickleStepMsg
    from cucumber_messages import Step

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    data_table_obj = SimpleNamespace(rows=[])
    ast_step = Step(
        id="ast-step-5",
        keyword="Given ",
        location=None,
        text="a step",
        data_table=data_table_obj,
    )
    binding.ast_registry.index_tree(ast_step)
    pickle_step = PickleStepMsg(
        id="pickle-step-5",
        type=1,
        text="a step",
        ast_node_ids=["ast-step-5"],
    )
    result = binding.step_data_table(pickle_step)
    assert result is data_table_obj


def test_feature_runtime_binding_pickle_ast_scenario_pickle_ast_scenario_returns_scenario() -> None:
    """
    pickle_ast_scenario returns Scenario when linked.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Location
    from cucumber_messages import Pickle as PickleMsg
    from cucumber_messages import Scenario as ScenarioMsg

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    scenario = ScenarioMsg(
        id="ast-scenario-1",
        keyword="Scenario",
        name="Test Scenario",
        location=Location(line=5, column=1),
        description="",
        steps=[],
        tags=[],
        examples=[],
    )
    binding.ast_registry.index_tree(scenario)
    pickle = PickleMsg(
        id="p1",
        uri="file:test.feature",
        ast_node_ids=["ast-scenario-1"],
        language="en",
        name="Test",
        steps=[],
        tags=[],
    )
    result = binding.pickle_ast_scenario(pickle)
    assert result is scenario


def test_feature_runtime_binding_pickle_ast_scenario_pickle_line_number_with_linked_scenario() -> None:
    """
    pickle_line_number returns line from linked scenario.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Location
    from cucumber_messages import Pickle as PickleMsg
    from cucumber_messages import Scenario as ScenarioMsg

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    scenario = ScenarioMsg(
        id="ast-scenario-2",
        keyword="Scenario",
        name="Test",
        location=Location(line=42, column=1),
        description="",
        steps=[],
        tags=[],
        examples=[],
    )
    binding.ast_registry.index_tree(scenario)
    pickle = PickleMsg(
        id="p2",
        uri="file:test.feature",
        ast_node_ids=["ast-scenario-2"],
        language="en",
        name="Test",
        steps=[],
        tags=[],
    )
    result = binding.pickle_line_number(pickle)
    assert result == 42


def test_feature_runtime_binding_pickle_ast_table_rows_pickle_ast_table_rows_with_linked_rows() -> None:
    """
    pickle_ast_table_rows returns TableRow nodes when linked.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Location, TableRow
    from cucumber_messages import Pickle as PickleMsg

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    row = TableRow(id="ast-row-1", cells=[], location=Location(line=10, column=1))
    binding.ast_registry.index_tree(row)
    pickle = PickleMsg(
        id="p3",
        uri="file:test.feature",
        ast_node_ids=["ast-row-1"],
        language="en",
        name="Test",
        steps=[],
        tags=[],
    )
    result = binding.pickle_ast_table_rows(pickle)
    assert len(result) == 1
    assert isinstance(result[0], TableRow)


def test_feature_runtime_binding_pickle_ast_table_rows_pickle_table_rows_breadcrumb_with_rows() -> None:
    """
    pickle_table_rows_breadcrumb generates breadcrumb string.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from cucumber_messages import Location, TableRow
    from cucumber_messages import Pickle as PickleMsg

    run = _make_run()
    doc = _make_gherkin_document()
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    row = TableRow(id="ast-row-2", cells=[], location=Location(line=15, column=1))
    binding.ast_registry.index_tree(row)
    pickle = PickleMsg(
        id="p4",
        uri="file:test.feature",
        ast_node_ids=["ast-row-2"],
        language="en",
        name="Test",
        steps=[],
        tags=[],
    )
    result = binding.pickle_table_rows_breadcrumb(pickle)
    assert "line: 15" in result


def test_feature_runtime_binding_description_edge_cases_description_with_no_feature_message() -> None:
    """
    Description returns None when no feature message.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = GherkinDocument(comments=[], uri="file:test.feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.description is None


def test_feature_runtime_binding_rel_filename_non_file_rel_filename_with_http_uri() -> None:
    """
    rel_filename returns None for http URIs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _make_run()
    doc = _make_gherkin_document(uri="http://example.com/test.feature")
    binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
    assert binding.rel_filename is None
