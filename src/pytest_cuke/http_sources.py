"""HTTP source access with credentials scoped to an exact origin."""

from __future__ import annotations

import base64
import json
import os
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

if TYPE_CHECKING:
    from collections.abc import Callable


def _origin(url: str) -> tuple[str, str, int]:
    parts = urlsplit(url)
    if (
        parts.scheme.lower() not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
    ):
        raise ValueError("HTTP source URL must have an HTTP(S) origin without embedded credentials")
    port = parts.port if parts.port is not None else (443 if parts.scheme.lower() == "https" else 80)
    return parts.scheme.lower(), parts.hostname.lower(), port


def _secret(value: Any) -> str:
    if isinstance(value, str):
        result = value
    elif isinstance(value, dict) and set(value) == {"env"} and isinstance(value["env"], str):
        name = value["env"]
        if name not in os.environ:
            raise ValueError(f"HTTP source environment variable {name!r} is not set")
        result = os.environ[name]
    else:
        raise ValueError('HTTP source credentials and headers must be strings or {"env": "NAME"}')
    if "\r" in result or "\n" in result:
        raise ValueError("HTTP source header values cannot contain line breaks")
    return result


def _rules(config: Any) -> dict[tuple[str, str, int], dict[str, str]]:
    if config is None:
        return {}
    try:
        command_line = config.getoption("cuke_http_servers")
        configured = command_line if command_line is not None else config.getini("cuke_http_servers")
    except (AttributeError, KeyError, ValueError):
        return {}
    result: dict[tuple[str, str, int], dict[str, str]] = {}
    for raw in configured or ():
        try:
            rule = json.loads(raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Each HTTP server rule must be a JSON object") from error
        if not isinstance(rule, dict) or not isinstance(rule.get("origin"), str):
            raise ValueError("Each HTTP server rule requires an origin")
        parts = urlsplit(rule["origin"])
        if parts.path not in {"", "/"} or parts.query or parts.fragment:
            raise ValueError("HTTP server origin cannot include a path, query, or fragment")
        origin = _origin(rule["origin"])
        if origin in result:
            raise ValueError("Duplicate HTTP server origin")
        if set(rule) - {"origin", "headers", "bearer", "basic"}:
            raise ValueError("Unknown HTTP server rule field")
        raw_headers = rule.get("headers", {})
        if not isinstance(raw_headers, dict) or any(not isinstance(name, str) for name in raw_headers):
            raise ValueError("HTTP server headers must be an object")
        headers = {name: _secret(value) for name, value in raw_headers.items()}
        if any(not name or "\r" in name or "\n" in name or ":" in name for name in headers):
            raise ValueError("Invalid HTTP server header name")
        if "bearer" in rule and "basic" in rule:
            raise ValueError("Choose either bearer or basic authentication per HTTP server")
        if ("bearer" in rule or "basic" in rule) and any(name.lower() == "authorization" for name in headers):
            raise ValueError("Authorization header conflicts with configured HTTP authentication")
        if "bearer" in rule:
            headers["Authorization"] = "Bearer " + _secret(rule["bearer"])
        if "basic" in rule:
            basic = rule["basic"]
            if not isinstance(basic, dict) or set(basic) != {"username", "password"}:
                raise ValueError("HTTP basic authentication requires username and password")
            credentials = f"{_secret(basic['username'])}:{_secret(basic['password'])}".encode()
            headers["Authorization"] = "Basic " + base64.b64encode(credentials).decode("ascii")
        result[origin] = headers
    return result


def _apply_headers(request: Request, rules: dict[tuple[str, str, int], dict[str, str]]) -> None:
    for name, value in rules.get(_origin(request.full_url), {}).items():
        request.add_unredirected_header(name, value)


class _ScopedRedirect(HTTPRedirectHandler):
    def __init__(self, rules: dict[tuple[str, str, int], dict[str, str]]) -> None:
        self.rules = rules
        super().__init__()

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Request | None:
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            _apply_headers(redirected, self.rules)
        return redirected


def open_http_source(config: Any, url: str, *, plain_open: Callable[..., Any] = urlopen) -> Any:
    """Open a URL using only the credentials assigned to its current origin."""
    _origin(url)
    rules = _rules(config)
    if not rules:
        return plain_open(url)
    request = Request(url)  # noqa: S310
    _apply_headers(request, rules)
    return build_opener(_ScopedRedirect(rules)).open(request)
