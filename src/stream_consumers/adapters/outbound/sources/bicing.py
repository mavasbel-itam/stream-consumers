"""Bicing Barcelona bike-share station status (GBFS)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GbfsStationsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class BicingFactory(GbfsStationsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bicing",
        name="Bicing Barcelona bike-share station status (GBFS)",
        category="Transport",
        provider="Barcelona City Council (Bicing)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status",
        docs_url="https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing",
        terms_url="https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing",
        min_interval_s=10.0,
        notes="GBFS station_status polled every 10 s; an event is a station whose report time, bikes or docks changed.",
    )
    URL = "https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status"


FACTORY = BicingFactory()
