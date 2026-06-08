"""
Provide the URL-based scenario locator.

Responsibility:
    Provide the URL-based scenario locator. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.scenario_locator.url_locator` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - UrlScenarioLocator: owns nested behavior below this boundary
    - PyPyUrlScenarioLocator: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/feature_locator.py: imports or references `url_locator`
    - src/pytest_bdd/scenario_locator/facade.py: imports or references `url_locator`

State and side effects:
    mutates responses, encoding, mimetype, parser_type, parse_args; depends on __future__.annotations, asyncio, ssl,
    urllib.request, contextlib.suppress.

Invariants:
    - `pytest_bdd.scenario_locator.url_locator` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises re-raise; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import asyncio
import ssl
import urllib.request
from contextlib import suppress
from itertools import filterfalse
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, cast
from urllib.parse import urljoin

from attrs import define, field
from cucumber_messages import Source

from pytest_bdd.mimetype import Mimetype
from pytest_bdd.scenario import Args
from pytest_bdd.types.exception import FeatureParseError
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.url import is_local_url

from .base import ScenarioLocatorFilterMixin, ScenarioLocatorHookProtocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from enum import Enum

    import aiohttp

    from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.types.protocol import HasPytestStash


@define
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    """
    Represent url scenario locator state.

    Yields:
        Generated values.

    Responsibility:
        Represent url scenario locator state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - fetch: owns nested behavior below this boundary
        - fetch_all: owns nested behavior below this boundary
        - resolve_features: owns nested behavior below this boundary
        - _build_urls: owns nested behavior below this boundary
        - _fetch_feature_responses: owns nested behavior below this boundary
        - _get_parser_type: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `UrlScenarioLocator`
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `UrlScenarioLocator`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `UrlScenarioLocator`

    State and side effects:
        mutates encoding, mimetype, parser_type, parse_args, urls; depends on certifi, aiohttp,
        pytest_bdd.const.PytestConfigParam.

    Invariants:
        - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

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

    url_paths: list[str | Path] = field()
    encoding: str | None = field(default=None)
    features_base_url: str | Callable[[Config | HasPytestStash], str | None] | None = field(default=None)
    mimetype: Mimetype | str | Enum | None = field(default=None)
    parser_type: type[ParserProtocol] | None = field(default=None)
    parse_args: Args | None = field(default=None)

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
        """
        Fetch content from URL.

        Args:
            session: aiohttp client session.
            url: URL to fetch.

        Returns:
            Tuple of (content_type, content_text).

        Responsibility:
            Fetch content from URL. It directly owns the observable contract, local decisions, and maintenance boundary
            for this async method. That boundary is intentionally stated in prose so maintainers can distinguish owned
            work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.fetch`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ssl.create_default_context: collaborator call used by this boundary
            - certifi.where: collaborator call used by this boundary
            - session.get: collaborator call used by this boundary
            - response.text: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `fetch`
            - src/pytest_bdd/script/sync_messages_contract_schemas.py: imports or references `fetch`

        State and side effects:
            mutates sslcontext; depends on certifi.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.fetch` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        import certifi  # noqa: PLC0415

        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with session.get(url, ssl=sslcontext) as response:
            return response.content_type, await response.text(encoding=self.encoding or "utf-8")

    async def fetch_all(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Fetch all URLs concurrently.

        Args:
            urls: Sequence of URLs to fetch.

        Returns:
            List of tuples (content_type, content_text) or exceptions.

        Responsibility:
            Fetch all URLs concurrently. It directly owns the observable contract, local decisions, and maintenance
            boundary for this async method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.fetch_all` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - aiohttp.ClientSession: collaborator call used by this boundary
            - asyncio.gather: collaborator call used by this boundary
            - self.fetch: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `fetch_all`

        State and side effects:
            depends on aiohttp.

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
        import aiohttp  # noqa: PLC0415

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.fetch(session, url) for url in urls], return_exceptions=True)

    def resolve_features(self, config: Config | HasPytestStash) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Resolve features.

        Yields:
            Generated values.

        Responsibility:
            Resolve features. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.resolve_features` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - self._build_urls: collaborator call used by this boundary
            - self._fetch_feature_responses: collaborator call used by this boundary
            - zip: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - Mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/base.py: imports or references `resolve_features`
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `resolve_features`

        State and side effects:
            mutates urls, responses, hook_handler, encoding, mimetype_raw.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator.resolve_features` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        urls = self._build_urls()
        if not urls:
            return
        responses = self._fetch_feature_responses(urls)
        hook_handler = cast("ScenarioLocatorHookProtocol", cast("Config", config).hook)
        encoding = self.encoding or "utf-8"

        for url, response in zip(urls, responses, strict=False):
            if isinstance(response, BaseException):
                continue

            mimetype_raw, feature_content = response
            mimetype_source = self.mimetype if self.mimetype is not None else mimetype_raw
            mimetype = Mimetype(str(mimetype_source))
            parser_type = self._get_parser_type(hook_handler, config, mimetype)
            if parser_type is None:
                break

            parser = parser_type(id_generator=IdGenerator.from_stash(config.stash))

            yield from self._parse_and_yield_feature(parser, config, url, feature_content, mimetype, encoding)

    def _build_urls(self) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._build_urls`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._build_urls` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - filterfalse: collaborator call used by this boundary
            - urls.extend: collaborator call used by this boundary
            - urljoin: collaborator call used by this boundary
            - filter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_build_urls`

        State and side effects:
            mutates urls.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._build_urls` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        urls = [str(url) for url in filterfalse(is_local_url, self.url_paths)]
        if self.features_base_url is not None:
            urls.extend(
                str(urljoin(f"{self.features_base_url}/", str(path))) for path in filter(is_local_url, self.url_paths)
            )
        return urls

    def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._fetch_feature_responses` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._fetch_feature_responses` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - loop.run_until_complete: collaborator call used by this boundary
            - asyncio.new_event_loop: collaborator call used by this boundary
            - self.fetch_all: collaborator call used by this boundary
            - asyncio.sleep: collaborator call used by this boundary
            - loop.close: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_fetch_feature_responses`

        State and side effects:
            mutates loop, responses.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._fetch_feature_responses` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        loop = asyncio.new_event_loop()
        try:
            responses = loop.run_until_complete(self.fetch_all(urls))
            # Wait 250 ms for the underlying SSL connections to close
            loop.run_until_complete(asyncio.sleep(0.250))
            return responses
        finally:
            loop.close()

    def _get_parser_type(
        self,
        hook_handler: ScenarioLocatorHookProtocol,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._get_parser_type` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._get_parser_type` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - hook_handler.pytest_bdd_get_parser: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_get_parser_type`

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
        if self.parser_type is None:
            return hook_handler.pytest_bdd_get_parser(
                config=config,
                mimetype=mimetype,
            )
        return self.parser_type

    def _parse_and_yield_feature(  # noqa: PLR0913, PLR0917
        self,
        parser: ParserProtocol,
        config: Config | HasPytestStash,
        url: str,
        feature_content: str,
        mimetype: Mimetype,
        encoding: str,
    ) -> Iterator[tuple[ParsedFeature, Source]]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_and_yield_feature` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_and_yield_feature` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - self._write_temp_feature_file: collaborator call used by this boundary
            - self._parse_temp_feature: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - Source: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_parse_and_yield_feature`

        State and side effects:
            mutates filename, parsed, media_type.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_and_yield_feature` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        filename = self._write_temp_feature_file(feature_content)
        try:
            parsed = self._parse_temp_feature(parser, config, Path(filename), url, encoding)
            if parsed is None:
                return
            media_type = str(mimetype) if mimetype is not None else "text/plain;charset=UTF-8"
            yield parsed, Source(uri=url, data=parsed.raw_data, media_type=media_type)
        finally:
            with suppress(Exception):
                Path(filename).unlink()

    @staticmethod
    def _write_temp_feature_file(feature_content: str) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._write_temp_feature_file` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._write_temp_feature_file` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - NamedTemporaryFile: collaborator call used by this boundary
            - file.write: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_write_temp_feature_file`

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
        with NamedTemporaryFile(encoding="utf-8", mode="w", delete=False) as file:
            file.write(feature_content)
            return file.name

    def _parse_temp_feature(
        self,
        parser: ParserProtocol,
        config: Config | HasPytestStash,
        path: Path,
        url: str,
        encoding: str,
    ) -> ParsedFeature | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_temp_feature` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_temp_feature` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Args: collaborator call used by this boundary
            - parser.parse: collaborator call used by this boundary
            - cast.getoption: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_parse_temp_feature`

        State and side effects:
            mutates parse_args; depends on pytest_bdd.const.PytestConfigParam.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.UrlScenarioLocator._parse_temp_feature` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises re-raise; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        from pytest_bdd.const import PytestConfigParam  # noqa: PLC0415

        try:
            parse_args = self.parse_args or Args((), {})
            return parser.parse(
                config,
                path,
                url,
                *parse_args.args,
                **{"encoding": encoding, **parse_args.kwargs},
            )
        except FeatureParseError:
            if cast("Config", config).getoption(str(PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS)):
                return None
            raise


@define
class PyPyUrlScenarioLocator(UrlScenarioLocator):
    """
    Represent url scenario locator state on PyPy runtimes, avoiding aiohttp.

    Yields:
        Generated values.

    Responsibility:
        Represent url scenario locator state on PyPy runtimes, avoiding aiohttp. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.url_locator.PyPyUrlScenarioLocator`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _fetch_feature_responses: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `PyPyUrlScenarioLocator`
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `PyPyUrlScenarioLocator`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `PyPyUrlScenarioLocator`

    State and side effects:
        mutates responses, sslcontext, content_type, content_bytes, content_text; depends on certifi.

    Invariants:
        - `pytest_bdd.scenario_locator.url_locator.PyPyUrlScenarioLocator` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

    """

    def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.scenario_locator.url_locator.PyPyUrlScenarioLocator._fetch_feature_responses` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.url_locator.PyPyUrlScenarioLocator._fetch_feature_responses` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - responses.append: collaborator call used by this boundary
            - ssl.create_default_context: collaborator call used by this boundary
            - certifi.where: collaborator call used by this boundary
            - urllib.request.urlopen: collaborator call used by this boundary
            - response.headers.get_content_type: collaborator call used by this boundary
            - response.read: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_fetch_feature_responses`

        State and side effects:
            mutates responses, sslcontext, content_type, content_bytes, content_text; depends on certifi.

        Invariants:
            - `pytest_bdd.scenario_locator.url_locator.PyPyUrlScenarioLocator._fetch_feature_responses` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        import certifi  # noqa: PLC0415

        responses: list[tuple[str, str] | BaseException] = []
        sslcontext = ssl.create_default_context(cafile=certifi.where())
        for url in urls:
            try:
                with urllib.request.urlopen(url, context=sslcontext, timeout=10) as response:  # noqa: S310
                    content_type = response.headers.get_content_type()
                    content_bytes = response.read()
                    content_text = content_bytes.decode(self.encoding or "utf-8")
                    responses.append((content_type, content_text))
            except Exception as e:  # noqa: BLE001, PERF203
                responses.append(e)
        return responses
