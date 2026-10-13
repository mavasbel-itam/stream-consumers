"""GH Archive — all public GitHub events (hourly files)."""

from __future__ import annotations

import zlib
from collections.abc import AsyncGenerator, Mapping
from datetime import UTC, datetime, timedelta

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.base import FileDropSource, FileLocation
from stream_consumers.domain.errors import DecodeError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound import ClockPort, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies


class GhArchiveSource(FileDropSource):
    """Hourly gzip NDJSON files of every public GitHub event. The file for hour H is published shortly
    after H+1; the newest hour treated as complete is the one that ended at least `delay` ago."""

    URL = "https://data.gharchive.org/{hour}.json.gz"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        interval_s: float = 300.0,
        delay: timedelta = timedelta(minutes=20),
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, interval_s, backoff)
        self._http = http
        self._delay = delay

    async def _locate(self) -> FileLocation:
        start = datetime.fromtimestamp(self._clock.now(), UTC) - self._delay - timedelta(hours=1)
        hour = f"{start:%Y-%m-%d}-{start.hour}"
        return FileLocation(hour, self.URL.format(hour=hour), 3600.0)

    async def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:
        inflate = zlib.decompressobj(16 + zlib.MAX_WBITS)
        pending = b""
        async for chunk in self._http.stream(location.url):
            try:
                pending += inflate.decompress(chunk)
            except zlib.error as exc:
                raise DecodeError(f"{location.url}: {exc}") from exc
            *lines, pending = pending.split(b"\n")
            for line in lines:
                if line.strip():
                    for record in self._decoder.decode(RawMessage(line)):
                        yield record
        if pending.strip():
            for record in self._decoder.decode(RawMessage(pending)):
                yield record


class GharchiveFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="gharchive",
        name="GH Archive — all public GitHub events (hourly files)",
        category="Internet & software",
        provider="GH Archive (Ilya Grigorik)",
        group=Group.KEYLESS,
        delivery=Delivery.FILE_DROP,
        transport=Transport.HTTP,
        endpoint="https://data.gharchive.org/YYYY-MM-DD-H.json.gz",
        docs_url="https://www.gharchive.org/",
        terms_url="https://www.gharchive.org/",
        personal_fields=(
            "actor.login",
            "actor.display_login",
            "actor.avatar_url",
            "actor.url",
            "actor.gravatar_id",
            "actor.id",
            "payload.*",
        ),
        notes="One file per UTC hour; rate = events in the newest complete hour / 3,600 s.",
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return GhArchiveSource(self.DESCRIPTOR, JsonDecoder(), deps.clock, deps.http)


FACTORY = GharchiveFactory()
