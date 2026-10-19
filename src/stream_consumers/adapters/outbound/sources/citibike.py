"""Citi Bike New York bike-share station status (GBFS)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GbfsStationsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class CitibikeFactory(GbfsStationsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="citibike",
        name="Citi Bike New York bike-share station status (GBFS)",
        category="Transport",
        provider="Citi Bike (Lyft, Inc.)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json",
        docs_url="https://citibikenyc.com/system-data",
        terms_url="https://citibikenyc.com/data-sharing-policy",
        min_interval_s=10.0,
        notes=(
            "GBFS station_status (listed in https://gbfs.citibikenyc.com/gbfs/gbfs.json) polled every 10 s; an event "
            "is a station whose report time, bikes or docks changed. The licence forbids redistributing the data as "
            "a stand-alone dataset. The feed is regenerated every 60 s (ttl 60) behind a CloudFront cache, so "
            "windows are at least 150 s."
        ),
        min_window_s=150.0,
    )
    URL = "https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json"


FACTORY = CitibikeFactory()
