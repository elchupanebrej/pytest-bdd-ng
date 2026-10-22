from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit


@dataclass(frozen=True)
class FeatureSourceConfiguration:
    """Resolved feature roots for one pytest configuration and optional binding."""

    features_base_dir: Path
    features_base_url: str | None


class FeatureSourceError(OSError):
    """A requested feature source could not be resolved, loaded, or parsed."""


def resolve_feature_sources(
    config: Any = None,
    *,
    features_base_dir: Any = None,
    features_base_url: Any = None,
) -> FeatureSourceConfiguration:
    """Resolve binding, CLI, INI, and default feature sources for one pytest run.

    Relative local roots are anchored at pytest's root path so a command launched
    from another working directory resolves the same feature files. Callable
    binding overrides receive the live pytest config once during resolution.
    """
    root = _pytest_root(config)
    configured_dir = _resolve_override(features_base_dir, config)
    if configured_dir is None:
        configured_dir = _directory_setting(_option(config, "cuke_features_dir"))
    if configured_dir is None:
        configured_dir = _directory_setting(_ini(config, "cuke_features_dir"))
    directory = _resolve_local_root(configured_dir, root)

    configured_url = _resolve_override(features_base_url, config)
    if configured_url is None:
        configured_url = _string_setting(_option(config, "cuke_features_base_url"))
    if configured_url is None:
        configured_url = _string_setting(_ini(config, "cuke_features_base_url"))
    base_url = normalize_features_base_url(configured_url) if configured_url else None

    return FeatureSourceConfiguration(features_base_dir=directory, features_base_url=base_url)


def normalize_features_base_url(value: Any) -> str:
    """Validate and normalize a run-level HTTP(S) base, without its trailing slash."""
    text = str(value).strip()
    try:
        parsed = urlsplit(text)
        _ = parsed.port
    except ValueError as error:
        raise _invalid_base_url(text) from error

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or parsed.hostname is None
        or any(character.isspace() for character in text)
        or parsed.query
        or parsed.fragment
    ):
        raise _invalid_base_url(text)

    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path.rstrip("/"), "", ""))


def resolve_feature_url(feature_path: str, base_url: str | None) -> str:
    """Resolve a relative feature path below its URL base while preserving prefixes."""
    if urlsplit(feature_path).scheme:
        return feature_path
    if base_url is None:
        raise FeatureSourceError(
            f"Relative URL feature path {feature_path!r} requires --cuke-features-base-url or cuke_features_base_url."
        )

    normalized_base = normalize_features_base_url(base_url)
    return urljoin(f"{normalized_base}/", feature_path.lstrip("/"))


def _resolve_override(value: Any, config: Any) -> Any:
    return value(config) if callable(value) else value


def _resolve_local_root(value: Any, root: Path) -> Path:
    if value is None or str(value) == "":
        return root
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _pytest_root(config: Any) -> Path:
    if config is None:
        return Path.cwd().resolve()
    root = getattr(config, "rootpath", getattr(config, "rootdir", None))
    return (Path(root) if isinstance(root, (str, PathLike)) else Path.cwd()).expanduser().resolve()


def _directory_setting(value: Any) -> str | PathLike[str] | None:
    return value if isinstance(value, (str, PathLike)) else None


def _string_setting(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _option(config: Any, name: str) -> Any:
    getter = getattr(config, "getoption", None)
    if getter is None:
        return None
    try:
        return getter(name, default=None)
    except TypeError:
        try:
            return getter(name)
        except (AttributeError, KeyError, ValueError):
            return None
    except (AttributeError, KeyError, ValueError):
        return None


def _ini(config: Any, name: str) -> Any:
    getter = getattr(config, "getini", None)
    if getter is None:
        return None
    try:
        return getter(name)
    except (AttributeError, KeyError, ValueError):
        return None


def _invalid_base_url(value: str) -> ValueError:
    return ValueError(
        "--cuke-features-base-url / cuke_features_base_url must be an absolute HTTP(S) URL "
        f"with a host and no query or fragment; got {value!r}."
    )
