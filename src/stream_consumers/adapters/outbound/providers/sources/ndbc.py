"""NOAA National Data Buoy Center — latest observation of every buoy and coastal station."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class NdbcLatestObsDecoder(BaseDecoder):
    """Whitespace-separated table: the first `#` line names the columns, the second gives units.

    One event per station row; `MM` marks a value the station did not report and is left out."""

    MISSING = "MM"

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        names: list[str] | None = None
        out: list[Mapping[str, object]] = []
        for line in self.text(message).splitlines():
            if line.startswith("#"):
                if names is None:
                    names = line[1:].split()
                continue
            values = line.split()
            if names is None or not values:
                continue
            out.append({n: v for n, v in zip(names, values, strict=False) if v != self.MISSING})
        return out


class NdbcFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ndbc",
        name="NOAA National Data Buoy Center — latest observation of every buoy and coastal station",
        category="Weather & environment",
        provider="NOAA National Data Buoy Center (NDBC)",
        group=Group.LOW_RATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt",
        docs_url="https://www.ndbc.noaa.gov/faq/rt_data_access.shtml",
        terms_url="https://www.weather.gov/disclaimer",
        min_interval_s=120.0,
        notes=(
            "The latest observation of each of about 840 stations, polled every 120 s. NDBC rewrites the file at "
            "irregular times (Last-Modified on 2026-10-19: 00:35:51, 00:50:42, 00:55:50, 01:40:26, 01:50:25 UTC; "
            "consecutive rewrites seen 14 min 51 s and 9 min 59 s apart). An event is a station whose observation "
            "time changed. Windows are at least 960 s so that a round spans a rewrite at those intervals."
        ),
        min_window_s=960.0,
    )
    URL = "https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["STN"], ["YYYY", "MM", "DD", "hh", "mm"])
        return HttpPollSource(self.DESCRIPTOR, NdbcLatestObsDecoder(), deps.clock, deps.http, [self.URL], 120.0, detector)


FACTORY = NdbcFactory()
