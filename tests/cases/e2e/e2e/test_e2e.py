"""Provide test e2e helpers."""

from types import SimpleNamespace

from contract.messages.message_capability_fixtures import make_mapping_rule

from pytest_bdd import scenarios
from pytest_bdd.model.message_outcome_mapping import ObservedOutcome, validate_outcome_mappings

_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}
_EXCLUDED_FEATURE_URI_FRAGMENTS = ("07 report/08 xdist remote network reporting.feature.md",)
_EXCLUDED_FEATURE_SCENARIOS = {
    (
        "07 report/02 gathering.feature.md",
        "html report could be produced on the feature run",
    ),
}


def _iter_tag_names(feature, pickle):
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(getattr(feature, "feature", None), "tags", ()))
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(pickle, "tags", ()))


def _exclude_default_bdd_features(config, feature, pickle):  # noqa: ARG001
    feature_uri = str(getattr(feature, "uri", "")).lower()
    feature_name = str(getattr(getattr(feature, "feature", None), "name", "")).lower()
    scenario_name = str(getattr(pickle, "name", "")).lower()
    tag_names = set(_iter_tag_names(feature, pickle))
    return (
        "allure" not in feature_uri
        and not feature_name.startswith("allure ")
        and not any(fragment in feature_uri for fragment in _EXCLUDED_FEATURE_URI_FRAGMENTS)
        and not any(
            fragment in feature_uri and scenario == scenario_name for fragment, scenario in _EXCLUDED_FEATURE_SCENARIOS
        )
        and tag_names.isdisjoint(_EXCLUDED_TAGS)
    )


test_feature_001 = scenarios(
    "../../../../features/01 Tutorial/01 Launch.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_002 = scenarios(
    "../../../../features/02 Feature/01 Non-strict gherkin.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_003 = scenarios(
    "../../../../features/02 Feature/02 Tag conversion.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_004 = scenarios(
    "../../../../features/02 Feature/03 Markdown parsing.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_005 = scenarios(
    "../../../../features/02 Feature/04 Localization.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_006 = scenarios(
    "../../../../features/02 Feature/05 Rule.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_007 = scenarios("../../../../features/02 Feature/06 Tag.feature.md", filter_=_exclude_default_bdd_features)
test_feature_008 = scenarios(
    "../../../../features/02 Feature/07 Description.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_009 = scenarios(
    "../../../../features/02 Feature/08 Error reporting.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_010 = scenarios(
    "../../../../features/02 Feature/09 Load/01 Scenario without steps.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_011 = scenarios(
    "../../../../features/02 Feature/09 Load/02 Scenario search from base url.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_012 = scenarios(
    "../../../../features/02 Feature/09 Load/03 Scenario function loader.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_013 = scenarios(
    "../../../../features/02 Feature/09 Load/04 HTTP feature loading.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_014 = scenarios(
    "../../../../features/02 Feature/09 Load/05 Autoload.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_015 = scenarios(
    "../../../../features/02 Feature/09 Load/06 Feature base directory resolution.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_016 = scenarios(
    "../../../../features/02 Feature/09 Load/07 Scenario search from base directory.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_017 = scenarios(
    "../../../../features/02 Feature/09 Load/08 Batch collection.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_018 = scenarios(
    "../../../../features/03 Scenario/01 Scenario binding.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_019 = scenarios(
    "../../../../features/03 Scenario/02 Tag.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_020 = scenarios(
    "../../../../features/03 Scenario/03 Description.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_021 = scenarios(
    "../../../../features/03 Scenario/04 Tag filtering.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_022 = scenarios(
    "../../../../features/03 Scenario/05 Alias.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_023 = scenarios(
    "../../../../features/03 Scenario/06 Scenarios loader.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_024 = scenarios(
    "../../../../features/03 Scenario/07 Background.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_025 = scenarios(
    "../../../../features/03 Scenario/08 Outline/01 Runtime expansion.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_026 = scenarios(
    "../../../../features/03 Scenario/08 Outline/02 Examples Tag.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_027 = scenarios(
    "../../../../features/03 Scenario/08 Outline/03 Empty values.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_028 = scenarios(
    "../../../../features/04 Step/01 Doc string.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_029 = scenarios(
    "../../../../features/04 Step/02 Data table.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_030 = scenarios(
    "../../../../features/04 Step/03 Step definition bounding.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_031 = scenarios(
    "../../../../features/04 Step/04 Step lifecycle and errors.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_032 = scenarios(
    "../../../../features/05 Step definition/01 Pytest fixtures substitution.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_033 = scenarios(
    "../../../../features/05 Step definition/02 Target fixtures specification.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_034 = scenarios(
    "../../../../features/05 Step definition/03 Parameters/01 Conversion.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_035 = scenarios(
    "../../../../features/05 Step definition/03 Parameters/02 Parsing by custom parser.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_036 = scenarios(
    "../../../../features/05 Step definition/03 Parameters/03 Injection as fixtures.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_037 = scenarios(
    "../../../../features/05 Step definition/03 Parameters/04 Parsing.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_038 = scenarios(
    "../../../../features/05 Step definition/03 Parameters/05 Defaults.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_039 = scenarios(
    "../../../../features/06 StructBDD/01 Steps.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_040 = scenarios(
    "../../../../features/06 StructBDD/02 StructBDD edge cases.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_041 = scenarios(
    "../../../../features/07 Report/01 Gherkin terminal reporter.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_042 = scenarios(
    "../../../../features/07 Report/02 Gathering.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_043 = scenarios(
    "../../../../features/07 Report/03 Allure scenario.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_044 = scenarios(
    "../../../../features/07 Report/04 Allure outline.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_045 = scenarios(
    "../../../../features/07 Report/05 Cucumber JSON reporter.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_046 = scenarios(
    "../../../../features/07 Report/07 xdist HTML reporting.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_047 = scenarios(
    "../../../../features/07 Report/08 xdist remote network reporting.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_048 = scenarios(
    "../../../../features/07 Report/09 Cucumber formatter reports.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_049 = scenarios(
    "../../../../features/08 Go Parser/01 Go parser backend.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_050 = scenarios(
    "../../../../features/09 Tag Expressions/01 Tag expression evaluation.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_051 = scenarios(
    "../../../../features/10 Heading Validation/01 Heading validation.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_052 = scenarios(
    "../../../../features/11 Mimetype/01 Mimetype detection.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_053 = scenarios(
    "../../../../features/12 Formatters/01 JUnit XML reporter.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_054 = scenarios(
    "../../../../features/12 Formatters/02 Progress formatters.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_055 = scenarios(
    "../../../../features/12 Formatters/03 Snippets formatter.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_056 = scenarios(
    "../../../../features/12 Formatters/04 Summary formatter.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_057 = scenarios(
    "../../../../features/12 Formatters/05 Usage statistics.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_058 = scenarios(
    "../../../../features/13 Code Generator/01 Code generation.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_059 = scenarios(
    "../../../../features/14 Scenario Reporter/01 Scenario reporting.feature.md", filter_=_exclude_default_bdd_features
)
test_feature_060 = scenarios(
    "../../../../features/15 Compatibility/01 Python version compatibility.feature.md",
    filter_=_exclude_default_bdd_features,
)
test_feature_061 = scenarios(
    "../../../../features/16 Batch Collection/01 Batch collection edge cases.feature.md",
    filter_=_exclude_default_bdd_features,
)

pytest_plugins = [
    "tests.e2e.steps_go_parser",
    "tests.e2e.steps_tag_expressions",
    "tests.e2e.steps_heading_validation",
    "tests.e2e.steps_mimetype",
    "tests.e2e.steps_struct_bdd",
    "tests.e2e.steps_formatters",
    "tests.e2e.steps_code_generator",
    "tests.e2e.steps_scenario_reporter",
    "tests.e2e.steps_compatibility",
    "tests.e2e.steps_batch_collection",
]


def _fixed_rules():
    return [
        make_mapping_rule(
            "rule-passed",
            outcome_scope="scenario",
            outcome_status="passed",
            capability_ids=("cap-pass",),
        ),
        make_mapping_rule(
            "rule-failed",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-fail",),
        ),
        make_mapping_rule(
            "rule-skipped",
            outcome_scope="scenario",
            outcome_status="skipped",
            capability_ids=("cap-skip",),
        ),
        make_mapping_rule(
            "rule-undefined",
            outcome_scope="scenario",
            outcome_status="undefined",
            capability_ids=("cap-undef",),
        ),
        make_mapping_rule(
            "rule-interrupted",
            outcome_scope="scenario",
            outcome_status="interrupted",
            capability_ids=("cap-interrupt",),
        ),
    ]


def test_messages_fixed_release_readiness_matrix_is_valid() -> None:
    """Verify messages fixed release readiness matrix is valid."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed", is_parallel_worker=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]

    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)

    assert result.status == "pass"


def test_messages_fixed_release_readiness_matrix_rejects_missing_parallel_worker_scenario() -> None:
    """Verify messages fixed release readiness matrix rejects missing parallel worker scenario."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]

    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)

    assert result.status == "fail"
    assert "missing_parallel_worker_scenario" in result.missing_required_matrix_cases


def test_default_bdd_filter_excludes_tagged_slow_scenarios() -> None:
    """Verify default bdd filter excludes tagged slow scenarios."""

    def _tag(name: str):
        return SimpleNamespace(name=name)

    def _document(*, name: str, tags: list[str], uri: str = "file:test.feature"):
        return SimpleNamespace(
            uri=uri,
            feature=SimpleNamespace(
                name=name,
                tags=[_tag(tag) for tag in tags],
            ),
        )

    def _pickle(*tags: str):
        return SimpleNamespace(tags=[_tag(tag) for tag in tags])

    assert (
        _exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=["@xdist"]),
            _pickle(),
        )
        is False
    )
    assert (
        _exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=[]),
            _pickle("@docker"),
        )
        is False
    )
    assert (
        _exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=[]),
            _pickle(),
        )
        is True
    )
    assert (
        _exclude_default_bdd_features(
            None,
            _document(
                name="xdist html reporting",
                tags=[],
                uri="file:07 Report/07 xdist HTML reporting.feature.md",
            ),
            _pickle(),
        )
        is True
    )
    assert (
        _exclude_default_bdd_features(
            None,
            _document(
                name="report gathering outputs",
                tags=[],
                uri="file:07 Report/02 Gathering.feature.md",
            ),
            SimpleNamespace(
                name="HTML report could be produced on the feature run",
                tags=[],
            ),
        )
        is False
    )
    assert (
        _exclude_default_bdd_features(
            None,
            _document(
                name="cucumber formatter reports",
                tags=[],
                uri="file:07 Report/09 Cucumber formatter reports.feature.md",
            ),
            _pickle(),
        )
        is True
    )
