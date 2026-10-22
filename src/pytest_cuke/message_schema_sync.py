"""Synchronize vendored schemas for the installed Cucumber Messages contract."""

from __future__ import annotations

import io
import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

MESSAGES_DISTRIBUTION: Final = "cucumber-messages"
UPSTREAM_REPOSITORY: Final = "cucumber/messages"
MAX_ARCHIVE_BYTES: Final = 16 * 1024 * 1024
MAX_SCHEMA_BYTES: Final = 2 * 1024 * 1024
MAX_GITHUB_RESPONSE_BYTES: Final = 64 * 1024


@dataclass(frozen=True)
class UpstreamRelease:
    """An immutable schema source and wire protocol selected for a contract version."""

    tag: str
    commit: str
    protocol_version: str


# Pin the generated official Python binding to the exact upstream schema source
# and wire protocol. The distribution's release tag is also the protocol version
# for this release.
UPSTREAM_RELEASES: Final[Mapping[str, UpstreamRelease]] = {
    "28.0.0": UpstreamRelease(
        tag="v28.0.0",
        commit="f5b1f30dc3ea234f44ea4cc6289726e7d8f2cbe0",
        protocol_version="28.0.0",
    ),
}


class SchemaSyncError(RuntimeError):
    """An actionable error while resolving, validating, or replacing schemas."""


@dataclass(frozen=True)
class SchemaDrift:
    """Sorted schema paths grouped by their difference from the source."""

    changed: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    extra: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not (self.changed or self.missing or self.extra)


@dataclass(frozen=True)
class SchemaSyncResult:
    """Version and drift details for one sync or check invocation."""

    contract_version: str
    release: UpstreamRelease
    drift: SchemaDrift
    wrote_files: bool


def resolve_upstream_release(contract_version: str | None = None) -> tuple[str, UpstreamRelease]:
    """Resolve the exact upstream release for the installed contract package."""
    if contract_version is None:
        try:
            contract_version = version(MESSAGES_DISTRIBUTION)
        except PackageNotFoundError as error:
            raise SchemaSyncError(
                f"cannot determine the installed {MESSAGES_DISTRIBUTION!r} contract version; "
                "install pytest-cuke with its runtime dependencies before syncing schemas"
            ) from error

    release = UPSTREAM_RELEASES.get(contract_version)
    if release is None:
        supported = ", ".join(sorted(UPSTREAM_RELEASES))
        raise SchemaSyncError(
            f"installed {MESSAGES_DISTRIBUTION} version {contract_version!r} has no pinned "
            f"{UPSTREAM_REPOSITORY} schema release; add an explicit mapping (currently supported: {supported})"
        )
    return contract_version, release


def compare_schema_files(source: Mapping[str, bytes], destination: Mapping[str, bytes]) -> SchemaDrift:
    """Compare normalized schema maps and return stable changed/missing/extra paths."""
    source_names = set(source)
    destination_names = set(destination)
    shared_names = source_names & destination_names
    return SchemaDrift(
        changed=tuple(sorted(name for name in shared_names if source[name] != destination[name])),
        missing=tuple(sorted(source_names - destination_names)),
        extra=tuple(sorted(destination_names - source_names)),
    )


def sync_message_schemas(
    schema_path: Path,
    *,
    check: bool = False,
    source_dir: Path | None = None,
) -> SchemaSyncResult:
    """Check or replace a dedicated schema directory from the pinned release.

    ``source_dir`` supplies a local deterministic source for tests and CI. It may
    point either at the schema root or at a checkout containing ``jsonschema/``.
    """
    contract_version, release = resolve_upstream_release()
    source = _read_local_schemas(source_dir) if source_dir is not None else _fetch_release_schemas(release)
    destination = _read_directory_schemas(schema_path, missing_ok=True, require_envelope=False)
    drift = compare_schema_files(source, destination)

    wrote_files = False
    if not check and (not drift.is_clean or _has_legacy_schema_names(schema_path)):
        _replace_schema_tree(schema_path, source)
        wrote_files = True

    return SchemaSyncResult(contract_version, release, drift, wrote_files)


def _read_local_schemas(source_dir: Path) -> dict[str, bytes]:
    if not source_dir.is_dir():
        raise SchemaSyncError(f"local schema source directory does not exist or is not a directory: {source_dir}")

    candidates = (source_dir / "jsonschema" / "src", source_dir / "jsonschema", source_dir)
    for candidate in candidates:
        if candidate.is_dir() and _contains_schema_json(candidate):
            return _read_directory_schemas(candidate)
    raise SchemaSyncError(
        f"local schema source {source_dir} contains no JSON schemas; pass the schema root or a directory "
        "containing jsonschema/"
    )


def _contains_schema_json(root: Path) -> bool:
    return any(
        path.is_file() and (path.name.endswith(".json") or path.name.endswith(".schema.json"))
        for path in root.rglob("*")
    )


def _has_legacy_schema_names(root: Path) -> bool:
    return root.is_dir() and any(
        path.is_file() and path.name.endswith(".json") and not path.name.endswith(".schema.json")
        for path in root.rglob("*")
    )


def _read_directory_schemas(
    root: Path,
    *,
    missing_ok: bool = False,
    require_envelope: bool = True,
) -> dict[str, bytes]:
    if not root.exists():
        if missing_ok:
            return {}
        raise SchemaSyncError(f"schema directory does not exist: {root}")
    if root.is_symlink() or not root.is_dir():
        raise SchemaSyncError(f"schema path must be a real directory: {root}")

    schemas: dict[str, bytes] = {}
    original_names: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise SchemaSyncError(f"schema source contains a symbolic link: {path}")
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(root).as_posix())
        normalized_name = _normalized_schema_name(relative)
        if normalized_name is None:
            continue
        previous_name = original_names.get(normalized_name)
        if previous_name is not None:
            raise SchemaSyncError(
                f"schema paths {previous_name!r} and {relative.as_posix()!r} normalize to the same name "
                f"{normalized_name!r}"
            )
        original_names[normalized_name] = relative.as_posix()
        try:
            if path.stat().st_size > MAX_SCHEMA_BYTES:
                raise SchemaSyncError(f"schema file {normalized_name!r} exceeds the {MAX_SCHEMA_BYTES} byte size limit")
            with path.open("rb") as schema_file:
                content = schema_file.read(MAX_SCHEMA_BYTES + 1)
        except OSError as error:
            raise SchemaSyncError(f"cannot read schema file {path}: {error}") from error
        schemas[normalized_name] = _validate_schema_content(normalized_name, content)

    if not schemas:
        if missing_ok:
            return {}
        raise SchemaSyncError(f"schema directory contains no .json or .schema.json files: {root}")
    if require_envelope and "Envelope.schema.json" not in schemas:
        raise SchemaSyncError(f"schema source is missing the required Envelope schema: {root}")
    return schemas


def _normalized_schema_name(path: PurePosixPath) -> str | None:
    filename = path.name
    if filename.endswith(".schema.json"):
        return path.as_posix()
    if filename.endswith(".json"):
        return path.with_name(f"{filename[:-5]}.schema.json").as_posix()
    return None


def _validate_schema_content(name: str, content: bytes) -> bytes:
    if len(content) > MAX_SCHEMA_BYTES:
        raise SchemaSyncError(f"schema file {name!r} exceeds the {MAX_SCHEMA_BYTES} byte size limit")
    try:
        schema = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SchemaSyncError(f"schema file {name!r} is not valid UTF-8 JSON: {error}") from error
    if not isinstance(schema, dict):
        raise SchemaSyncError(f"schema file {name!r} must contain a JSON object")
    return content


def _fetch_release_schemas(release: UpstreamRelease) -> dict[str, bytes]:
    _verify_upstream_tag(release)
    archive_url = f"https://codeload.github.com/{UPSTREAM_REPOSITORY}/tar.gz/{release.commit}"
    request = urllib.request.Request(archive_url, headers={"User-Agent": "pytest-cuke-schema-sync"})
    try:
        # This URL uses the fixed upstream HTTPS host and a reviewed commit pin.
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = response.read(MAX_ARCHIVE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise SchemaSyncError(
            f"could not download pinned {UPSTREAM_REPOSITORY} {release.tag} schema archive "
            f"({release.commit}): {error}; check network access and retry"
        ) from error
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise SchemaSyncError(f"pinned schema archive for {release.tag} exceeds the size limit")

    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            return _schemas_from_archive(archive, release)
    except (tarfile.TarError, OSError) as error:
        raise SchemaSyncError(f"could not read pinned schema archive for {release.tag}: {error}") from error


def _verify_upstream_tag(release: UpstreamRelease) -> None:
    """Require the named upstream tag to resolve to its reviewed immutable commit."""
    reference_url = f"https://api.github.com/repos/{UPSTREAM_REPOSITORY}/git/ref/tags/{release.tag}"
    reference = _fetch_github_json(reference_url, release)
    target = reference.get("object") if isinstance(reference, dict) else None

    for _ in range(4):
        if not isinstance(target, dict):
            raise SchemaSyncError(f"upstream tag {release.tag} returned an invalid Git reference")
        object_type = target.get("type")
        object_sha = target.get("sha")
        if not isinstance(object_sha, str) or not _is_git_sha(object_sha):
            raise SchemaSyncError(f"upstream tag {release.tag} returned an invalid Git object identifier")
        if object_type == "commit":
            if object_sha.lower() != release.commit.lower():
                raise SchemaSyncError(
                    f"upstream tag {release.tag} now resolves to {object_sha}, but the reviewed schema pin is "
                    f"{release.commit}; update the explicit release mapping after reviewing the schema change"
                )
            return
        if object_type != "tag":
            raise SchemaSyncError(
                f"upstream tag {release.tag} resolves to an unsupported Git object type: {object_type!r}"
            )
        tag_url = f"https://api.github.com/repos/{UPSTREAM_REPOSITORY}/git/tags/{object_sha}"
        tag_object = _fetch_github_json(tag_url, release)
        target = tag_object.get("object") if isinstance(tag_object, dict) else None

    raise SchemaSyncError(f"upstream tag {release.tag} exceeds the supported annotated-tag depth")


def _fetch_github_json(url: str, release: UpstreamRelease) -> object:
    # This URL is composed only from the fixed GitHub API host and the reviewed release mapping.
    request = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "pytest-cuke-schema-sync",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = response.read(MAX_GITHUB_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise SchemaSyncError(
                f"pinned upstream tag {release.tag} is missing from {UPSTREAM_REPOSITORY}; "
                "verify the release mapping before syncing schemas"
            ) from error
        raise SchemaSyncError(
            f"could not verify upstream tag {release.tag} in {UPSTREAM_REPOSITORY} "
            f"(HTTP {error.code}): {error.reason}; check GitHub availability and retry"
        ) from error
    except (OSError, urllib.error.URLError) as error:
        raise SchemaSyncError(
            f"could not verify upstream tag {release.tag} in {UPSTREAM_REPOSITORY}: {error}; "
            "check network access and retry"
        ) from error
    if len(payload) > MAX_GITHUB_RESPONSE_BYTES:
        raise SchemaSyncError(f"GitHub returned an oversized response while verifying tag {release.tag}")
    try:
        return json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SchemaSyncError(f"GitHub returned invalid JSON while verifying upstream tag {release.tag}") from error


def _is_git_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdefABCDEF" for character in value)


def _schemas_from_archive(archive: tarfile.TarFile, release: UpstreamRelease) -> dict[str, bytes]:
    direct: dict[str, bytes] = {}
    nested: dict[str, bytes] = {}
    for member in archive.getmembers():
        if not member.isfile():
            continue
        archive_path = PurePosixPath(member.name)
        parts = archive_path.parts
        if archive_path.is_absolute() or ".." in parts or "\\" in member.name or ":" in member.name:
            raise SchemaSyncError(f"pinned schema archive contains an unsafe path: {member.name!r}")
        try:
            schema_index = parts.index("jsonschema")
        except ValueError:
            continue
        relative_parts = parts[schema_index + 1 :]
        if not relative_parts:
            continue
        nested_source = relative_parts[0] == "src"
        if nested_source:
            relative_parts = relative_parts[1:]
        relative = PurePosixPath(*relative_parts)
        normalized_name = _normalized_schema_name(relative)
        if normalized_name is None:
            continue
        if member.size > MAX_SCHEMA_BYTES:
            raise SchemaSyncError(f"schema file {member.name!r} in {release.tag} exceeds the size limit")
        extracted = archive.extractfile(member)
        if extracted is None:
            raise SchemaSyncError(f"could not read schema file {member.name!r} from {release.tag}")
        content = extracted.read(MAX_SCHEMA_BYTES + 1)
        if len(content) != member.size:
            raise SchemaSyncError(f"schema file {member.name!r} in {release.tag} was truncated")
        _validate_schema_content(normalized_name, content)
        schema_map = nested if nested_source else direct
        if normalized_name in schema_map:
            raise SchemaSyncError(f"pinned schema archive has duplicate normalized schema {normalized_name!r}")
        schema_map[normalized_name] = content

    schemas = direct or nested
    if not schemas:
        raise SchemaSyncError(f"pinned {UPSTREAM_REPOSITORY} {release.tag} archive contains no JSON schemas")
    if "Envelope.schema.json" not in schemas:
        raise SchemaSyncError(f"pinned {UPSTREAM_REPOSITORY} {release.tag} archive is missing Envelope.json")
    return schemas


def _replace_schema_tree(destination: Path, schemas: Mapping[str, bytes]) -> None:
    if destination.is_symlink():
        raise SchemaSyncError(f"schema path must not be a symbolic link: {destination}")
    if destination.exists() and not destination.is_dir():
        raise SchemaSyncError(f"schema path is not a directory: {destination}")
    if not destination.name:
        raise SchemaSyncError("refusing to replace a filesystem root as the schema directory")

    parent = destination.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=parent))
    except OSError as error:
        raise SchemaSyncError(f"cannot prepare schema staging directory beside {destination}: {error}") from error

    backup: Path | None = None
    preserve_backup = False
    try:
        for name, content in sorted(schemas.items()):
            relative = PurePosixPath(name)
            parts = relative.parts
            if not parts or relative.is_absolute() or ".." in parts or "\\" in name or ":" in name:
                raise SchemaSyncError(f"refusing to write schema outside the output directory: {name!r}")
            target = stage.joinpath(*parts)
            try:
                target.relative_to(stage)
            except ValueError as error:
                raise SchemaSyncError(f"refusing to write schema outside the output directory: {name!r}") from error
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        if destination.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{destination.name}.backup-", dir=parent))
            backup.rmdir()
            os.replace(destination, backup)
        try:
            os.replace(stage, destination)
        except OSError as error:
            if backup is not None:
                try:
                    os.replace(backup, destination)
                    backup = None
                except OSError as restore_error:
                    preserve_backup = True
                    raise SchemaSyncError(
                        f"could not install synchronized schemas at {destination}: {error}; "
                        f"the previous schema tree remains at {backup} because restore failed: {restore_error}"
                    ) from error
            raise SchemaSyncError(f"could not install synchronized schemas at {destination}: {error}") from error
    except SchemaSyncError:
        raise
    except OSError as error:
        raise SchemaSyncError(f"could not stage synchronized schemas at {destination}: {error}") from error
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if not preserve_backup and backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
