"""Shared BDD feature filter for E2E tests."""

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


def exclude_default_bdd_features(config, feature, pickle):  # noqa: ARG001
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
