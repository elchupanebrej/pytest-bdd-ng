"""
Provide url helpers.

Responsibility:
    Provide url helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.url` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - is_local_url: owns nested behavior below this boundary
    - is_url_parsable: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector.py: imports or references `url`
    - src/pytest_bdd/feature_locator.py: imports or references `url`
    - src/pytest_bdd/mimetype.py: imports or references `url`
    - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `url`
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `url`

State and side effects:
    depends on __future__.annotations, operator.attrgetter, urllib.parse.urlparse.

Invariants:
    - `pytest_bdd.util.url` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from operator import attrgetter
from urllib.parse import urlparse


def is_local_url(urllike: object) -> bool:
    """
    Check if URL is a local file URL.

    Args:
        urllike: URL string or path-like object.

    Returns:
        True if URL is local (no scheme or netloc).

    Responsibility:
        Check if URL is a local file URL. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.url.is_local_url` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - attrgetter: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - any: collaborator call used by this boundary
        - urlparse: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `is_local_url`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `is_local_url`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    try:
        if not isinstance(urllike, (str, bytes, bytearray)):
            return False
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:  # noqa: BLE001 intentional
        return False


def is_url_parsable(urllike: object) -> bool:
    """
    Check if URL can be parsed.

    Args:
        urllike: URL string or path-like object.

    Returns:
        True if URL is parsable.

    Responsibility:
        Check if URL can be parsed. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.url.is_url_parsable` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - urlparse: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `is_url_parsable`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `is_url_parsable`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    try:
        urlparse(str(urllike))
    except ValueError:
        return False
    else:
        return True
