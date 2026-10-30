Tag conversion protocol models
==============================

``pytest_cuke_convert_tag_to_marks`` accepts implementations using either the
pytest-cuke ``feature`` and ``scenario`` models or the official Messages
``gherkin_document`` and ``pickle`` models. Implementations request the arguments
they need; existing model-based hooks retain their signature and behavior.

For example, a migrated protocol consumer can define::

    import pytest

    def pytest_cuke_convert_tag_to_marks(gherkin_document, pickle, tag):
        if gherkin_document.feature.name == "Checkout" and tag == "smoke":
            return [pytest.mark.smoke]

``tag`` remains the clean tag name used by the current API. The compiled
``pickle.tags`` retain the source ``@`` names and inherited Feature, Rule,
Scenario and Examples tags. Outline rows have distinct pickle identities.
These hooks run during collection, with or without a Messages reporter.

Protocol projections are created only when a registered implementation requests
them. The GherkinDocument is shared across a feature's scenarios within one
parametrization; each scenario's pickle is shared across its tag callbacks.
These are observation models, not an interface for modifying collection.
