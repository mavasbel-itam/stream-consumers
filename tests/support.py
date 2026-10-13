"""Test doubles. Each extends the port it stands in for, so a port change breaks them at import time."""

from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from pathlib import Path

from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import (
    Delivery,
    Event,
    Group,
    PublishedVolume,
    RawMessage,
    RunReport,
    SamplingRound,
    SourceDescriptor,
    SourceProfile,
    Transport,
)
from stream_consumers.ports.outbound import (
    ClockPort,
    EventSinkFactoryPort,
    EventSinkPort,
    EventSourcePort,
    HttpClientPort,
    HttpResponse,
    ReportSinkPort,
    SecretProviderPort,
    SourceDependencies,
)

FIXTURES = Path(__file__).parent / "fixtures" / "raw"


def descriptor(source_id: str = "fake", personal: tuple[str, ...] = (), **overrides: object) -> SourceDescriptor:
    values: dict[str, object] = dict(
        id=source_id,
        name="Fake source",
        category="Test",
        provider="Tests",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://example.invalid",
        docs_url="https://example.invalid/docs",
        terms_url="https://example.invalid/terms",
        personal_fields=personal,
    )
    values.update(overrides)
    return SourceDescriptor(**values)  # type: ignore[arg-type]


class FakeClock(ClockPort):
    """Virtual time: `sleep` advances both clocks at once (and yields to the loop)."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.wall = start
        self.mono = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.wall

    def monotonic(self) -> float:
        return self.mono

    def advance(self, seconds: float) -> None:
        self.wall += seconds
        self.mono += seconds

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.advance(seconds)
        await asyncio.sleep(0)


class FakeSecrets(SecretProviderPort):
    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values = dict(values or {})

    def get(self, name: str) -> str | None:
        return self._values.get(name)


Responder = Callable[[str], HttpResponse]


class FakeHttp(HttpClientPort):
    """Answers by URL. A value may be one response, a list consumed in order (last one repeats),
    or a callable. `stream` yields the body in chunks of `chunk` bytes."""

    def __init__(self, routes: Mapping[str, object] | None = None, chunk: int = 7) -> None:
        self.routes: dict[str, object] = dict(routes or {})
        self.calls: list[tuple[str, str, object]] = []
        self.closed = False
        self._chunk = chunk

    def _answer(self, url: str) -> HttpResponse:
        route = self.routes.get(url)
        if route is None:
            return HttpResponse(404, b"not found")
        if callable(route):
            return route(url)
        if isinstance(route, list):
            return route.pop(0) if len(route) > 1 else route[0]
        return route  # type: ignore[return-value]

    async def get(self, url: str, headers: Mapping[str, str] | None = None) -> HttpResponse:
        self.calls.append(("GET", url, dict(headers or {})))
        return self._answer(url)

    async def post_json(self, url: str, body: object, headers: Mapping[str, str] | None = None) -> HttpResponse:
        self.calls.append(("POST", url, body))
        return self._answer(url)

    async def stream(self, url: str, headers: Mapping[str, str] | None = None) -> AsyncIterator[bytes]:
        self.calls.append(("STREAM", url, dict(headers or {})))
        response = self._answer(url)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {url}")
        for i in range(0, len(response.body), self._chunk):
            yield response.body[i : i + self._chunk]

    async def close(self) -> None:
        self.closed = True


def ok(body: bytes | str | object, status: int = 200) -> HttpResponse:
    if isinstance(body, str):
        body = body.encode()
    elif not isinstance(body, bytes):
        body = json.dumps(body).encode()
    return HttpResponse(status, body)


def deps(
    http: HttpClientPort | None = None, secrets: Mapping[str, str] | None = None, clock: ClockPort | None = None
) -> SourceDependencies:
    return SourceDependencies(http or FakeHttp(), FakeSecrets(secrets), clock or FakeClock(), "tests/1.0")


class ScriptedSource(EventSourcePort):
    """Yields `payloads` (an exception item is raised), sleeping `gap` virtual seconds before each."""

    def __init__(
        self,
        desc: SourceDescriptor,
        payloads: Sequence[object],
        clock: FakeClock,
        gap: float = 0.0,
        volume: PublishedVolume | None = None,
        hang: bool = False,
    ) -> None:
        self._descriptor = desc
        self._payloads = list(payloads)
        self._clock = clock
        self._gap = gap
        self._volume = volume
        self._hang = hang
        self.closed = False

    @property
    def descriptor(self) -> SourceDescriptor:
        return self._descriptor

    def published_volume(self) -> PublishedVolume | None:
        return self._volume

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        try:
            for item in self._payloads:
                if self._gap:
                    await self._clock.sleep(self._gap)
                if isinstance(item, BaseException):
                    raise item
                yield item  # type: ignore[misc]
            if self._hang:
                await asyncio.Event().wait()
        finally:
            self.closed = True


class ListSink(EventSinkPort):
    def __init__(self) -> None:
        self.events: list[Event] = []
        self.closed = False

    def write(self, event: Event) -> None:
        self.events.append(event)

    def close(self) -> None:
        self.closed = True


class ListSinkFactory(EventSinkFactoryPort):
    def __init__(self) -> None:
        self.sinks: dict[str, ListSink] = {}

    def open(self, source_id: str) -> EventSinkPort:
        self.sinks[source_id] = ListSink()
        return self.sinks[source_id]


class MemoryReports(ReportSinkPort):
    def __init__(self) -> None:
        self.checks: list[Sequence[RunReport]] = []
        self.rounds: list[SamplingRound] = []
        self.profiles: list[Sequence[SourceProfile]] = []

    def write_check(self, reports: Sequence[RunReport]) -> None:
        self.checks.append(reports)

    def write_round(self, sampling_round: SamplingRound) -> None:
        self.rounds.append(sampling_round)

    def write_profiles(self, profiles: Sequence[SourceProfile]) -> None:
        self.profiles.append(profiles)


def fixture(source_id: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{source_id}.json").read_text(encoding="utf-8"))


def messages(source_id: str) -> list[RawMessage]:
    """The captured raw messages of a source, as the transport delivered them."""
    out = []
    for m in fixture(source_id)["messages"]:  # type: ignore[union-attr]
        if "body_b64" in m:
            body: bytes | str = base64.b64decode(m["body_b64"])
        elif m.get("bytes"):
            body = m["body_text"].encode("utf-8")
        else:
            body = m["body_text"]
        out.append(RawMessage(body, dict(m.get("attributes") or {})))
    return out


def http_for(source_id: str, urls: Sequence[str]) -> FakeHttp:
    """FakeHttp answering `urls` (in order) with the captured bodies of a polled source."""
    return FakeHttp(
        {
            url: HttpResponse(200, m.body if isinstance(m.body, bytes) else m.body.encode())
            for url, m in zip(urls, messages(source_id), strict=False)
        }
    )
