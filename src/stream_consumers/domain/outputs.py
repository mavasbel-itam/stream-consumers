"""Output destinations: the text of `--out` read into a value the composition root can act on."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field, replace
from urllib.parse import parse_qsl, unquote

from stream_consumers.domain.errors import OutputTargetError

TERMINAL = "terminal"
FILE = "file"
_SCHEME = re.compile(r"([a-z][a-z0-9+.-]+):(.*)", re.DOTALL)
_PASSWORD = re.compile(r"(//[^/?#@]*?:)[^/?#@]*@")


@dataclass(frozen=True)
class OutputTarget:
    """Where events go. `scheme` is `terminal`, `file` or a URI scheme (`sqlite`, `kafka`, ...);
    `text` is what the user wrote; for `scheme://` targets the authority, path and query are split out."""

    scheme: str
    text: str
    location: str = ""
    hosts: tuple[tuple[str, int | None], ...] = ()
    path: str = ""
    user: str | None = None
    password: str | None = None
    options: Mapping[str, str] = field(default_factory=dict)
    password_from_env: bool = False
    """True when `password` was not in `text` but read from the environment (`with_password`)."""

    def with_password(self, password: str | None) -> OutputTarget:
        """This target with `password` from elsewhere than `text`; unchanged when `password` is None."""
        return self if password is None else replace(self, password=password, password_from_env=True)

    @property
    def display(self) -> str:
        """The target as written, with any password replaced by `***`."""
        return _PASSWORD.sub(r"\1***@", self.text)


def _host(text: str, target: str) -> tuple[str, int | None]:
    if text.startswith("["):
        host, sep, rest = text[1:].partition("]")
        if not sep or (rest and not rest.startswith(":")):
            raise OutputTargetError(f"malformed host {text!r} in {target}")
        port_text = rest[1:]
    else:
        host, _, port_text = text.partition(":")
    if not host:
        raise OutputTargetError(f"missing host in {target}")
    if not port_text:
        return host, None
    if not port_text.isdigit() or not 0 < int(port_text) < 65536:
        raise OutputTargetError(f"invalid port {port_text!r} in {target}")
    return host, int(port_text)


def _authority(scheme: str, text: str, rest: str) -> OutputTarget:
    shown = OutputTarget(scheme, text).display
    cut = re.search(r"[/?]", rest)
    netloc, tail = (rest[: cut.start()], rest[cut.start() :]) if cut else (rest, "")
    userinfo, at, hostlist = netloc.rpartition("@")
    user = password = None
    if at:
        name, colon, secret = userinfo.partition(":")
        user = unquote(name) or None
        password = unquote(secret) if colon else None
    if not hostlist:
        raise OutputTargetError(f"missing host in {shown}")
    hosts = tuple(_host(h, shown) for h in hostlist.split(","))
    path, _, query = tail.partition("?")
    try:
        options = dict(parse_qsl(query, keep_blank_values=True, strict_parsing=True)) if query else {}
    except ValueError as exc:
        raise OutputTargetError(f"malformed options in {shown}") from exc
    return OutputTarget(scheme, text, rest, hosts, unquote(path.lstrip("/")), user, password, options)


def parse_target(text: str, schemes: Collection[str]) -> OutputTarget:
    """Read `--out`: `-` is the terminal, `<scheme>:...` with a known scheme is that destination,
    anything else is a file path. An unknown `<scheme>://` is an error rather than a file name."""
    if text == "-":
        return OutputTarget(TERMINAL, text)
    match = _SCHEME.fullmatch(text)
    if match is None:
        return OutputTarget(FILE, text, text)
    scheme, rest = match[1], match[2]
    if scheme not in schemes:
        if rest.startswith("//"):
            raise OutputTargetError(f"unknown output scheme {scheme!r} (known: {', '.join(sorted(schemes))})")
        return OutputTarget(FILE, text, text)
    if rest.startswith("//"):
        return _authority(scheme, text, rest[2:])
    if not rest:
        raise OutputTargetError(f"missing location after {scheme}:")
    return OutputTarget(scheme, text, rest)


SOURCE_PLACEHOLDER = "{source}"
"""Replaced by the source id in a topic, subject, database or table name taken from `--out`."""


def for_source(template: str, source_id: str) -> str:
    return template.replace(SOURCE_PLACEHOLDER, source_id)


def endpoints(target: OutputTarget, default_port: int) -> tuple[tuple[str, int], ...]:
    """The hosts of a `scheme://` target, each with `default_port` where the target gives none."""
    return tuple((host, default_port if port is None else port) for host, port in target.hosts)


def check_target(target: OutputTarget, *, credentials: bool = False, one_host: bool = False, options: Collection[str] = ()) -> None:
    """Refuse what a destination does not support, so nothing written in `--out` is silently ignored."""
    shown = target.display
    if not target.hosts:
        raise OutputTargetError(f"{target.scheme} needs {target.scheme}://host:port..., got {shown}")
    if not credentials and (target.user is not None or target.password is not None):
        raise OutputTargetError(f"{target.scheme} output takes no user or password: {shown}")
    if one_host and len(target.hosts) != 1:
        raise OutputTargetError(f"{target.scheme} output takes exactly one host:port: {shown}")
    unknown = sorted(set(target.options) - set(options))
    if unknown:
        raise OutputTargetError(f"unknown option(s) {', '.join(unknown)} for {target.scheme} (known: {', '.join(options) or 'none'})")


NAMESPACE = "stream_consumers"
"""The name every database output writes under (database, keyspace, key prefix, index prefix)."""

INT64 = range(-(2**63), 2**63)


def storable(value: object) -> object:
    """`value` with every integer outside 64 bits written as its decimal text: JSON allows integers
    of any size, BSON (MongoDB) stores at most 64 bits and refuses the whole batch otherwise."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value if value in INT64 else str(value)
    if isinstance(value, Mapping):
        return {key: storable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [storable(item) for item in value]
    return value
