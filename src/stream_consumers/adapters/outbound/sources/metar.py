"""NOAA aviationweather.gov METAR observations (global airports)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from stream_consumers.adapters.outbound.decoders import CsvDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class MetarCacheDecoder(CsvDecoder):
    """gzip CSV whose header row starts with `raw_text`; the lines before it are a preamble."""

    def __init__(self) -> None:
        super().__init__(gzipped=True)

    def prepare(self, text: str) -> str:
        start = text.find("raw_text,")
        return text[start:] if start >= 0 else ""


class MetarSource(HttpPollSource):
    """One row per station (its latest observation). Published volume: observations stamped within the last hour."""

    async def _snapshot_volume(self, records: Sequence[Mapping[str, object]]) -> PublishedVolume | None:
        now = self._clock.now()
        recent = 0
        for record in records:
            stamp = str(record.get("observation_time") or "")
            try:
                if now - datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() <= 3600:
                    recent += 1
            except ValueError:
                continue
        return PublishedVolume(recent, 3600.0)


class MetarFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="metar",
        name="NOAA aviationweather.gov METAR observations (global airports)",
        category="Weather & environment",
        provider="NOAA National Weather Service — Aviation Weather Center",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://aviationweather.gov/data/cache/metars.cache.csv.gz",
        docs_url="https://aviationweather.gov/data/api/",
        terms_url="https://aviationweather.gov/data/api/",
        min_interval_s=60.0,
        notes="Cache file of the latest METAR per station, polled every 60 s; an event is a new observation; rate = observations stamped within the last hour / 3,600 s.",
    )
    URL = "https://aviationweather.gov/data/cache/metars.cache.csv.gz"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return MetarSource(
            self.DESCRIPTOR,
            MetarCacheDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            60.0,
            ChangeDetector(["station_id"], ["observation_time"]),
        )


FACTORY = MetarFactory()
