"""
Provide mimetype helpers.

Responsibility:
    Provide mimetype helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.mimetype` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - Mimetype: owns nested behavior below this boundary
    - Suffix: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `mimetype`
    - src/pytest_bdd/feature_locator.py: imports or references `mimetype`
    - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `mimetype`
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `mimetype`
    - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `mimetype`

State and side effects:
    mutates markdown, yaml, hocon, toml, json5; depends on mimetypes, pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.mimetype` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

import mimetypes

from pytest_bdd.compatibility.enum import StrEnum


class Mimetype(StrEnum):
    """
    Represent mimetype state.

    Responsibility:
        Represent mimetype state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.mimetype.Mimetype` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `Mimetype`
        - src/pytest_bdd/feature_locator.py: imports or references `Mimetype`
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `Mimetype`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `Mimetype`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Mimetype`

    State and side effects:
        mutates gherkin_plain, gherkin_markdown, struct_bdd_yaml, struct_bdd_hocon, struct_bdd_json5.

    Invariants:
        - `pytest_bdd.mimetype.Mimetype` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    gherkin_plain = "text/x.cucumber.gherkin+plain"
    gherkin_markdown = "text/x.cucumber.gherkin+markdown"
    struct_bdd_yaml = "application/x.struct_bdd+yaml"
    struct_bdd_hocon = "application/x.struct_bdd+hocon"
    struct_bdd_json5 = "application/x.struct_bdd+json5"
    struct_bdd_json = "application/x.struct_bdd+json"
    struct_bdd_hjson = "application/x.struct_bdd+hjson"
    struct_bdd_toml = "application/x.struct_bdd+toml"

    python = "text/x-python"

    markdown = "text/markdown"
    yaml = "application/x-yaml"
    hocon = "application/x-hocon"
    toml = "text/toml"
    json = "application/json"
    json5 = "application/json5"
    hjson = "application/x-hjson"


class Suffix(StrEnum):
    """
    Represent suffix state.

    Responsibility:
        Represent suffix state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.mimetype.Suffix` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `Suffix`
        - src/pytest_bdd/feature_locator.py: imports or references `Suffix`
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `Suffix`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `Suffix`
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Suffix`

    State and side effects:
        mutates gherkin, feature, struct_bdd, url, desktop.

    Invariants:
        - `pytest_bdd.mimetype.Suffix` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    gherkin = ".gherkin"
    feature = ".feature"
    struct_bdd = ".bdd"
    url = ".url"
    desktop = ".desktop"
    webloc = ".webloc"
    markdown = ".md"
    yaml = ".yaml"
    yml = ".yml"
    ndjson = ".ndjson"
    hocon = ".hocon"
    toml = ".toml"
    hjson = ".hjson"
    json5 = ".json5"


gherkin_suffixes = {Suffix.gherkin, Suffix.feature}
struct_bdd_suffixes = {Suffix.struct_bdd}
link_suffixes = {Suffix.url, Suffix.desktop, Suffix.webloc}

mimetype_suffix_pairs = [
    (Mimetype.gherkin_plain, Suffix.gherkin),
    (Mimetype.gherkin_plain, Suffix.feature),
    (Mimetype.markdown, Suffix.markdown),
    (Mimetype.yaml, Suffix.yaml),
    (Mimetype.yaml, Suffix.yml),
    (Mimetype.hocon, Suffix.hocon),
    (Mimetype.toml, Suffix.toml),
    (Mimetype.hjson, Suffix.hjson),
    (Mimetype.json5, Suffix.json5),
]

for mimetype, suffix in mimetype_suffix_pairs:
    mimetypes.add_type(str(mimetype), str(suffix))
