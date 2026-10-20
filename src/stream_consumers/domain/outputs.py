"""Output destinations: the text of `--out` read into a value the composition root can act on."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
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
