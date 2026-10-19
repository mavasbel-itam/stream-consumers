"""NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import CsvDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class FirmsSource(HttpPollSource):
    """Public global 24 h files of four sensors: published volume = detections in them over 86,400 s."""

    async def _snapshot_volume(self, records: Sequence[Mapping[str, object]]) -> PublishedVolume | None:
        return PublishedVolume(len(records), 86_400.0)


class FirmsFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="firms",
        name="NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files",
        category="Weather & environment",
        provider="NASA Earth Science Data Systems (LANCE FIRMS)",
        group=Group.FREE_KEY,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://firms.modaps.eosdis.nasa.gov/data/active_fire/<sensor>/csv/<file>_Global_24h.csv",
        docs_url="https://firms.modaps.eosdis.nasa.gov/active_fire/",
        terms_url="https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance",
        min_interval_s=900.0,
        notes=(
            "Reads the keyless public 24 h files (VIIRS NOAA-20, NOAA-21, S-NPP and MODIS), polled every 15 min; "
            "the MAP_KEY API serves the same products by area and is not needed. An event is a new detection. The "
            "files (1.1-8.7 MB each) must arrive whole before the first event: up to 73 s in the rounds of "
            "2026-10-17/18, 462 s and 297 s in two 600-s checks on 2026-10-19 (NASA's server sent 0.09 MB/s), so "
            "windows are at least 600 s."
        ),
        min_window_s=600.0,
    )
    URLS = (
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return FirmsSource(
            self.DESCRIPTOR,
            CsvDecoder(),
            deps.clock,
            deps.http,
            self.URLS,
            900.0,
            ChangeDetector(["latitude", "longitude", "acq_date", "acq_time", "satellite"]),
        )


FACTORY = FirmsFactory()
