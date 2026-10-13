"""EcoBici CDMX bike-share station status (GBFS)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GbfsStationsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class EcobiciFactory(GbfsStationsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ecobici",
        name="EcoBici CDMX bike-share station status (GBFS)",
        category="Transport",
        provider="Gobierno de la Ciudad de México (EcoBici, operated by Lyft)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json",
        docs_url="https://ecobici.cdmx.gob.mx/datos-abiertos/",
        terms_url="https://ecobici.cdmx.gob.mx/datos-abiertos/",
        min_interval_s=10.0,
        notes="GBFS station_status polled every 10 s; an event is a station whose report time, bikes or docks changed.",
    )
    URL = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json"


FACTORY = EcobiciFactory()
