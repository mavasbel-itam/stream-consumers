"""adsb.fi open data aircraft — 250 NM around Mexico City airport."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import AdsbPointFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class AdsbFiFactory(AdsbPointFactory):
    DESCRIPTOR = SourceDescriptor(
        id="adsb_fi",
        name="adsb.fi open data aircraft — 250 NM around Mexico City airport",
        category="Transport",
        provider="adsb.fi",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250",
        docs_url="https://github.com/adsbfi/opendata",
        terms_url="https://raw.githubusercontent.com/adsbfi/opendata/main/README.md",
        min_interval_s=5.0,
        notes="Aircraft within 250 NM of Mexico City airport (AICM), polled every 5 s; an event is an aircraft whose position, altitude, speed or track changed.",
    )
    URL = "https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250"
    INTERVAL_S = 5.0


FACTORY = AdsbFiFactory()
