"""Crossref scholarly metadata (works indexed per day)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound import ClockPort, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies


class CrossrefWorksDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        msg = document.get("message") if isinstance(document, Mapping) else None
        items = msg.get("items") if isinstance(msg, Mapping) else None
        return [i for i in items if isinstance(i, Mapping)] if isinstance(items, list) else []


class CrossrefIndexedSource(HttpPollSource):
    """Polls the works most recently (re)indexed today; an event is a DOI whose `indexed` time changed.
    The published volume is the number of works indexed on the previous UTC day over 86,400 s."""

    WORKS = "https://api.crossref.org/works?filter=from-index-date:{day}&sort=indexed&order=desc&rows=1000{mailto}"
    COUNT = "https://api.crossref.org/works?filter=from-index-date:{day},until-index-date:{day}&rows=0{mailto}"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        interval_s: float,
        mailto: str | None,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(
            descriptor, decoder, clock, http, [self.WORKS], interval_s, ChangeDetector(["DOI"], ["indexed.date-time"]), backoff=backoff
        )
        self._mailto = f"&mailto={quote(mailto)}" if mailto else ""
        self._daily: tuple[str, PublishedVolume] | None = None

    def _day(self, days_ago: int) -> str:
        return (datetime.fromtimestamp(self._clock.now(), UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    async def _urls_for_poll(self) -> Sequence[str]:
        return [self.WORKS.format(day=self._day(0), mailto=self._mailto)]

    async def _snapshot_volume(self, records: Sequence[Mapping[str, object]]) -> PublishedVolume | None:
        day = self._day(1)
        if self._daily is None or self._daily[0] != day:
            url = self.COUNT.format(day=day, mailto=self._mailto)
            total = json.loads(self.ok(await self._http.get(url), url))["message"]["total-results"]
            self._daily = (day, PublishedVolume(int(total), 86_400.0))
        return self._daily[1]


class CrossrefFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="crossref",
        name="Crossref scholarly metadata (works indexed per day)",
        category="Science & sensors",
        provider="Crossref",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.crossref.org/works?filter=from-index-date:<today>&sort=indexed&order=desc",
        docs_url="https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        terms_url="https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        min_interval_s=60.0,
        personal_fields=("author", "editor"),
        notes="Rate = works (re)indexed on the previous UTC day / 86,400 s; most are updates of existing records, not new publications. Set CROSSREF_MAILTO to join Crossref's polite pool.",
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return CrossrefIndexedSource(
            self.DESCRIPTOR, CrossrefWorksDecoder(), deps.clock, deps.http, 60.0, deps.secrets.get("CROSSREF_MAILTO")
        )


FACTORY = CrossrefFactory()
