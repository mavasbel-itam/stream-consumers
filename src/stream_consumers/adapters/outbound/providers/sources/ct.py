"""Certificate Transparency logs (RFC 6962), read directly."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from cryptography import x509
from cryptography.x509.oid import ExtensionOID, NameOID

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.base import MergedEventSource, PollEventSource
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort


def _name(name: x509.Name, oid: x509.ObjectIdentifier) -> str | None:
    values = name.get_attributes_for_oid(oid)
    return str(values[0].value) if values else None


class CtEntryDecoder(JsonDecoder):
    """`get-entries` answers (RFC 6962 §4.6): each entry's leaf certificate is parsed (X.509 or pre-certificate)."""

    def __init__(self, log: str) -> None:
        self._log = log

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        entries = document.get("entries") if isinstance(document, Mapping) else None
        start = int(message.attributes.get("start", "0"))
        return [self.entry(e, start + n) for n, e in enumerate(entries or []) if isinstance(e, Mapping)]

    def entry(self, entry: Mapping[str, object], index: int) -> Mapping[str, object]:
        try:
            leaf = base64.b64decode(str(entry["leaf_input"]))
            extra = base64.b64decode(str(entry["extra_data"]))
            entry_type = int.from_bytes(leaf[10:12], "big")
            if entry_type == 0:
                length = int.from_bytes(leaf[12:15], "big")
                der = leaf[15 : 15 + length]
            else:
                length = int.from_bytes(extra[0:3], "big")
                der = extra[3 : 3 + length]
            cert = x509.load_der_x509_certificate(der)
        except (KeyError, ValueError) as exc:
            raise DecodeError(f"CT entry {index}: {exc}") from exc
        try:
            names = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value.get_values_for_type(x509.DNSName)
        except x509.ExtensionNotFound:
            names = []
        key = cert.public_key()
        return {
            "log": self._log,
            "index": index,
            "timestamp_ms": int.from_bytes(leaf[2:10], "big"),
            "entry_type": "precert" if entry_type == 1 else "x509",
            "serial": format(cert.serial_number, "x"),
            "subject_cn": _name(cert.subject, NameOID.COMMON_NAME),
            "subject_o": _name(cert.subject, NameOID.ORGANIZATION_NAME),
            "issuer_cn": _name(cert.issuer, NameOID.COMMON_NAME),
            "issuer_o": _name(cert.issuer, NameOID.ORGANIZATION_NAME),
            "issuer_c": _name(cert.issuer, NameOID.COUNTRY_NAME),
            "not_before": cert.not_valid_before_utc.isoformat(),
            "not_after": cert.not_valid_after_utc.isoformat(),
            "san_count": len(names),
            "san_first": names[0] if names else None,
            "key_type": type(key).__name__,
            "key_size": getattr(key, "key_size", None) or getattr(getattr(key, "curve", None), "key_size", None),
            "signature_algorithm": cert.signature_algorithm_oid._name,
            "extensions": len(cert.extensions),
        }


class CtLogPollSource(PollEventSource):
    """One RFC 6962 log: polls `get-sth`; new leaves are fetched with `get-entries` (at most `requests`
    requests of `batch` entries per poll; a log growing faster is skipped ahead). The published volume is the
    tree growth between the first and the last poll."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        url: str,
        interval_s: float = 10.0,
        batch: int = 256,
        requests: int = 4,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, interval_s, backoff=backoff)
        self._http = http
        self._url = url.rstrip("/")
        self._batch = batch
        self._requests = requests
        self._first: tuple[int, float] | None = None
        self._last: tuple[int, float] | None = None
        self._next = 0

    def published_volume(self) -> PublishedVolume | None:
        if self._first is None or self._last is None:
            return PublishedVolume(0, 0.0)
        return PublishedVolume(self._last[0] - self._first[0], self._last[1] - self._first[1])

    async def _get(self, path: str) -> bytes:
        response = await self._http.get(self._url + path)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {self._url + path}")
        return response.body

    async def _fetch(self) -> Sequence[RawMessage]:
        size = int(json.loads(await self._get("/ct/v1/get-sth"))["tree_size"])
        now = self._clock.monotonic()
        if self._first is None:
            self._first, self._next = (size, now), size
        self._last = (size, now)
        if size - self._next > self._batch * self._requests:
            self._next = size - self._batch * self._requests
        out = []
        while self._next < size and len(out) < self._requests:
            end = min(size, self._next + self._batch) - 1
            body = await self._get(f"/ct/v1/get-entries?start={self._next}&end={end}")
            received = len(json.loads(body).get("entries", []))
            if received == 0:
                break
            out.append(RawMessage(body, {"start": str(self._next)}))
            self._next += received
        return out


class CtLogsSource(MergedEventSource):
    """Every RFC 6962 log the browser log list marks usable for the current certificate period, read concurrently."""

    LOG_LIST = "https://www.gstatic.com/ct/log_list/v3/log_list.json"

    def __init__(self, descriptor: SourceDescriptor, clock: ClockPort, http: HttpClientPort, backoff: Backoff | None = None) -> None:
        super().__init__(descriptor, (), clock, backoff)
        self._http = http

    def published_volume(self) -> PublishedVolume | None:
        return super().published_volume() or PublishedVolume(0, 0.0)

    async def _logs(self) -> list[tuple[str, str]]:
        response = await self._http.get(self.LOG_LIST)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {self.LOG_LIST}")
        now = datetime.fromtimestamp(self._clock.now(), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        logs = []
        for operator in json.loads(response.body).get("operators", []):
            for log in operator.get("logs", []):
                interval = log.get("temporal_interval", {})
                if "usable" in log.get("state", {}) and interval.get("start_inclusive", "") <= now < interval.get("end_exclusive", ""):
                    logs.append((log["description"], log["url"]))
        if not logs:
            raise TransportError("the CT log list has no usable RFC 6962 log for the current period")
        return logs

    async def _resolve_children(self) -> Sequence[EventSourcePort]:
        logs = await self._retrying(self._logs)
        return [CtLogPollSource(self._descriptor, CtEntryDecoder(name), self._clock, self._http, url) for name, url in logs]


class CtFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ct",
        name="Certificate Transparency logs (RFC 6962), read directly",
        category="Internet & software",
        provider="Certificate Transparency log operators (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt, TrustAsia)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="<log url>/ct/v1/get-sth, /ct/v1/get-entries (log list https://www.gstatic.com/ct/log_list/v3/log_list.json)",
        docs_url="https://www.rfc-editor.org/rfc/rfc6962",
        terms_url="https://www.rfc-editor.org/rfc/rfc6962",
        notes="Rate = growth of all usable RFC 6962 logs (static-CT logs are not read). Events are the parsed certificates; a log growing faster than 1,024 entries per 10 s poll is skipped ahead.",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return CtLogsSource(self.DESCRIPTOR, deps.clock, deps.http)


FACTORY = CtFactory()
