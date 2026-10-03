from __future__ import annotations

import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from attrs import define, evolve, field

from pytest_cuke.compatibility.pytest import Config
from pytest_cuke.gherkin_builder import build_feature_from_dict
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model import Feature
from pytest_cuke.types.protocol import HasPytestStash
from pytest_cuke.utils import IdGenerator

if TYPE_CHECKING:
    from messages import GherkinDocument


@define
class ParsedFeature:
    gherkin_document: GherkinDocument
    filename: str
    raw_data: str


@runtime_checkable
class ParserProtocol(Protocol):
    id_generator: IdGenerator | None = None

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature: ...


@define
class LegacyParserAdapter:
    """Adapt the historical config-aware parser protocol to pytest-cuke's Feature API."""

    parser: Any
    config: Any
    identity: str = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.identity = _parser_identity(self.parser)

    @property
    def cache_identity(self) -> str:
        """Distinguish different adapted providers in the session feature cache."""
        return f"{self.identity}@{id(self.parser):x}"

    def parse(
        self,
        path: Path | str,
        uri: str | None = None,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> Feature:
        source_path = Path(path)
        resolved_uri = uri or source_path.as_posix()
        parse_args = kwargs.pop("_pytest_cuke_parse_args", None)
        positional_args, explicit_kwargs = _parse_args_parts(parse_args, self.identity, source_path)
        legacy_kwargs: dict[str, Any] = {"encoding": encoding, **kwargs}
        # Historical calls were equivalent to {"encoding": encoding, **parse_args.kwargs}.
        # Explicit values from parse_args therefore win over the locator's encoding.
        legacy_kwargs.update(explicit_kwargs)

        id_generator = _get_config_id_generator(self.config)
        try:
            self.parser.id_generator = id_generator
        except (AttributeError, TypeError) as error:
            raise _contract_error(
                self.identity,
                source_path,
                "the parser does not allow its required id_generator to be attached",
            ) from error

        # Do not catch or retry exceptions here. In particular, a TypeError raised inside
        # user code must keep its original type and traceback.
        result = self.parser.parse(
            self.config,
            source_path,
            resolved_uri,
            *positional_args,
            **legacy_kwargs,
        )
        return _feature_from_legacy_result(result, self.identity, source_path, resolved_uri)

    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature:
        raise TypeError(
            f"Legacy parser {self.identity} reads a source path through parse(config, path, uri, ...); "
            "it cannot parse in-memory text through parse_text()."
        )


def _parse_args_parts(parse_args: Any, parser_identity: str, path: Path) -> tuple[tuple[Any, ...], dict[str, Any]]:
    if parse_args is None:
        return (), {}
    args = getattr(parse_args, "args", ())
    kwargs = getattr(parse_args, "kwargs", {})
    if not isinstance(args, tuple | list) or not isinstance(kwargs, Mapping):
        raise _contract_error(
            parser_identity,
            path,
            "parse_args must expose positional args and a mapping of keyword args",
        )
    return tuple(args), dict(kwargs)


def _get_config_id_generator(config: Any) -> IdGenerator:
    stash = getattr(config, "stash", None)
    if stash is not None:
        return IdGenerator.from_stash(stash)
    generator = getattr(config, "pytest_cuke_id_generator", None)
    if generator is None:
        generator = IdGenerator()
        try:
            config.pytest_cuke_id_generator = generator
        except (AttributeError, TypeError):
            pass
    return generator


def _feature_from_legacy_result(result: Any, parser_identity: str, path: Path, uri: str) -> Feature:
    if result is None or not all(hasattr(result, name) for name in ("gherkin_document", "filename", "raw_data")):
        raise _contract_error(
            parser_identity,
            path,
            "the parser must return ParsedFeature(gherkin_document, filename, raw_data)",
        )

    document = result.gherkin_document
    if document is None:
        raise _contract_error(parser_identity, path, "ParsedFeature.gherkin_document is missing")
    filename = result.filename
    if not isinstance(filename, str) or not filename:
        raise _contract_error(parser_identity, path, "ParsedFeature.filename must be a non-empty string")
    raw_data = result.raw_data
    if not isinstance(raw_data, str):
        raise _contract_error(parser_identity, path, "ParsedFeature.raw_data must be decoded source text")

    try:
        _reject_unsupported_schema_metadata(document)
        document_data = _document_to_dict(document)
        _reject_unsupported_schema_metadata(document_data)
        from messages import GherkinDocument  # noqa: PLC0415  -- Generated messages load only for legacy parsing.

        validated_document = GherkinDocument.model_validate(document_data)
        normalized_data = validated_document.model_dump(mode="json", exclude_none=True, by_alias=True)
        feature_data = normalized_data.get("feature")
        if not isinstance(feature_data, dict):
            raise ValueError("GherkinDocument.feature must contain a Feature")
        source_media_type = mimetypes.guess_type(filename)[0] or Mimetype.gherkin_plain.value
        feature = build_feature_from_dict({"feature": feature_data}, uri=uri, filename=filename)
        return evolve(feature, source_content=raw_data, source_media_type=source_media_type)
    except LegacyParserContractError:
        raise
    except Exception as error:
        raise _contract_error(
            parser_identity,
            path,
            f"the returned GherkinDocument is malformed or uses an unsupported message schema: {error}",
        ) from error


def _document_to_dict(document: Any) -> dict[str, Any]:
    if isinstance(document, Mapping):
        raw = dict(document)
    elif callable(getattr(document, "model_dump", None)):
        raw = document.model_dump(mode="json", exclude_none=True, by_alias=True)
    elif callable(getattr(document, "dict", None)):
        raw = document.dict(exclude_none=True, by_alias=True)
    else:
        raise ValueError("gherkin_document must be a messages.GherkinDocument model or mapping")
    if not isinstance(raw, dict):
        raise ValueError("gherkin_document serialization must produce an object")
    return raw


def _reject_unsupported_schema_metadata(document: Any) -> None:
    version_fields = {"schema_version", "schemaVersion", "protocol_version", "protocolVersion"}
    if isinstance(document, Mapping):
        unsupported = version_fields.intersection(document)
        version_details = {key: document[key] for key in unsupported}
    else:
        version_details = {
            key: getattr(document, key)
            for key in version_fields
            if hasattr(document, key)
        }
        unsupported = set(version_details)
    if unsupported:
        field_name = sorted(unsupported)[0]
        raise ValueError(
            f"unsupported GherkinDocument schema version metadata {field_name}={version_details[field_name]!r}; "
            "return a GherkinDocument using the installed cucumber messages model"
        )


class LegacyParserContractError(ValueError):
    """A legacy extension returned a result that cannot become a native Feature."""


def _parser_identity(parser: Any) -> str:
    parser_type = parser if isinstance(parser, type) else type(parser)
    return f"{parser_type.__module__}.{parser_type.__qualname__}"


def _contract_error(parser_identity: str, path: Path, problem: str) -> LegacyParserContractError:
    return LegacyParserContractError(
        f"Legacy parser {parser_identity} returned an invalid result for '{path}': {problem}. "
        "Register it explicitly with ParserRegistration.legacy(provider) and return the installed "
        "messages.GherkinDocument model."
    )


__all__ = ["LegacyParserAdapter", "LegacyParserContractError", "ParsedFeature", "ParserProtocol"]
