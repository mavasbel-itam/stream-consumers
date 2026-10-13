"""NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import CsvDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, PublishedVolume, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


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
        credential=Credential("FIRMS_MAP_KEY", "https://firms.modaps.eosdis.nasa.gov/api/map_key/", required=False),
        min_interval_s=900.0,
        notes="Reads the keyless public 24 h files (VIIRS NOAA-20, NOAA-21, S-NPP and MODIS), polled every 15 min; the MAP_KEY API serves the same products by area and is not used. An event is a new detection.",
    )
    URLS = (
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
        "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv",
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
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
