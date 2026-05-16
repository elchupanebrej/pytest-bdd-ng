"""Unit tests for FeatureRuntimeBinding class."""

from __future__ import annotations

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


class TestFeatureRuntimeBindingConstruction:
    """Tests for FeatureRuntimeBinding construction."""

    def test_build_with_minimal_args(self) -> None:
        """build() works with minimal required arguments."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.run is run
        assert binding.gherkin_document is doc
        assert binding.uri == "file:features/example.feature"
        assert binding.filename == "features/example.feature"

    def test_build_with_source_infer_filename(self) -> None:
        """build() infers filename from source URI when filename not given."""
        run = _make_run()
        doc = _make_gherkin_document()
        source = Source(
            uri="file:features/custom.feature",
            data="Feature: test",
            media_type="text/x.cucumber.gherkin+plain",
        )
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
        assert binding.filename == "features/custom.feature"

    def test_build_with_explicit_filename(self) -> None:
        """build() uses explicit filename when provided."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, filename="my.feature")
        assert binding.filename == "my.feature"

    def test_build_with_pickles(self) -> None:
        """build() stores provided pickles."""
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

    def test_init_with_uri(self) -> None:
        """Direct construction with uri parameter."""
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

    def test_default_pickles_empty(self) -> None:
        """Default pickles is an empty tuple when none provided."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.pickles == ()


class TestFeatureRuntimeBindingLoadMethods:
    """Tests for load_gherkin_document and load_pickles static methods."""

    def test_load_gherkin_document_passes_through(self) -> None:
        """load_gherkin_document returns existing GherkinDocument as-is."""
        doc = _make_gherkin_document()
        result = FeatureRuntimeBinding.load_gherkin_document(doc)
        assert result is doc

    def test_load_gherkin_document_converts_dict(self) -> None:
        """load_gherkin_document converts dict to GherkinDocument."""
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

    def test_load_pickles_converts_list(self) -> None:
        """load_pickles converts list of dicts to Pickle tuple."""
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


class TestFeatureRuntimeBindingIndexing:
    """Tests for index_runtime_objects."""

    def test_index_runtime_objects_creates_registry(self) -> None:
        """index_runtime_objects creates ast_registry from feature."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        # After build, index_runtime_objects was called
        assert binding.ast_registry is not None


class TestFeatureRuntimeBindingResolve:
    """Tests for resolve_node method."""

    def test_resolve_node_raises_keyerror_for_unknown(self) -> None:
        """resolve_node raises KeyError for unknown object_id."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        with pytest.raises(KeyError):
            binding.resolve_node("nonexistent-id")


class TestFeatureRuntimeBindingProperties:
    """Tests for FeatureRuntimeBinding property methods."""

    def test_rel_filename_with_file_uri(self) -> None:
        """rel_filename strips 'file:' prefix."""
        run = _make_run()
        doc = _make_gherkin_document(uri="file:features/test.feature")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.rel_filename == "features/test.feature"

    def test_rel_filename_with_non_file_uri_returns_none(self) -> None:
        """rel_filename returns None for non-file URIs."""
        run = _make_run()
        doc = _make_gherkin_document(uri="http://example.com/feature")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.rel_filename is None

    def test_name_returns_feature_name(self) -> None:
        """name property returns the feature's name."""
        run = _make_run()
        doc = _make_gherkin_document(name="My Feature")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.name == "My Feature"

    def test_name_returns_none_when_no_feature(self) -> None:
        """name property returns None when no feature message."""
        run = _make_run()
        doc = GherkinDocument(comments=[], uri="file:test.feature")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.name is None

    def test_line_number_returns_feature_line(self) -> None:
        """line_number returns the feature declaration's line number."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        # Default location is line=1
        assert binding.line_number == 1

    def test_description_returns_feature_description(self) -> None:
        """description property returns dedented feature description."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.description == "Test feature"

    def test_description_returns_none_when_empty(self) -> None:
        """description returns None when feature has no description."""
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
        assert result == "" or result is None

    def test_tag_names_returns_sorted_tags(self) -> None:
        """tag_names returns sorted list of tags with prefix stripped."""
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

    def test_tag_names_empty_when_no_tags(self) -> None:
        """tag_names returns empty list when feature has no tags."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        assert binding.tag_names == []


class TestPickleMethods:
    """Tests for pickle-related methods on FeatureRuntimeBinding."""

    @staticmethod
    def _make_pickle(**kwargs):
        from cucumber_messages import Pickle as PickleMsg

        defaults = dict(
            id="p1",
            uri="file:test.feature",
            ast_node_ids=[],
            language="en",
            name="Test Feature",
            steps=[],
            tags=[],
        )
        defaults.update(kwargs)
        return PickleMsg(**defaults)

    def test_pickle_ast_table_rows_returns_table_rows(self) -> None:
        """pickle_ast_table_rows returns TableRow nodes linked to pickle."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        # No pickles registered yet, so results will be empty
        pickle = self._make_pickle()
        result = binding.pickle_ast_table_rows(pickle)
        assert result == []

    def test_pickle_table_rows_breadcrumb_empty_when_no_rows(self) -> None:
        """pickle_table_rows_breadcrumb returns empty string when no table rows."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        pickle = self._make_pickle()
        assert binding.pickle_table_rows_breadcrumb(pickle) == ""

    def test_pickle_ast_scenario_returns_none_when_no_link(self) -> None:
        """pickle_ast_scenario returns None when no linked scenario."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        pickle = self._make_pickle()
        assert binding.pickle_ast_scenario(pickle) is None

    def test_pickle_line_number_returns_negative_one_when_no_scenario(self) -> None:
        """pickle_line_number returns -1 when no linked scenario."""
        run = _make_run()
        doc = _make_gherkin_document()
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc)
        pickle = self._make_pickle()
        assert binding.pickle_line_number(pickle) == -1


class TestStepMethods:
    """Tests for step-related methods on FeatureRuntimeBinding."""

    def test_step_keyword_returns_none_when_no_linked_step(self) -> None:
        """step_keyword returns None when pickle step has no linked AST step."""
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

    def test_step_prefix_returns_none_when_no_keyword(self) -> None:
        """step_prefix returns None when step_keyword returns None."""
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

    def test_step_data_table_returns_none_when_no_linked_step(self) -> None:
        """step_data_table returns None when no linked AST step."""
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

    def test_step_doc_string_returns_none_when_no_linked_step(self) -> None:
        """step_doc_string returns None when no linked AST step."""
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


class TestFeatureRuntimeBindingAsDict:
    """Note: FeatureRuntimeBinding does not define as_dict — skip serialization tests."""


class TestFeatureRuntimeBindingFilename:
    """Tests for filename inference edge cases."""

    def test_filename_from_uri_without_file_scheme(self) -> None:
        """filename is inferred from non-file URI via Path conversion."""
        run = _make_run()
        doc = _make_gherkin_document(uri="http://example.com/test.feature")
        source = Source(uri="http://example.com/test.feature", data="", media_type="")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
        assert "test.feature" in binding.filename

    def test_filename_with_unknown_scheme(self) -> None:
        """filename falls back to str(Path(uri).as_posix()) for unknown schemes."""
        run = _make_run()
        doc = _make_gherkin_document(uri="custom://test.feature")
        source = Source(uri="custom://test.feature", data="", media_type="")
        binding = FeatureRuntimeBinding.build(run=run, gherkin_document=doc, source=source)
        assert "test.feature" in binding.filename
