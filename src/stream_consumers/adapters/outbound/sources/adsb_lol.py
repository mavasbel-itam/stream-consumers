"""adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import AdsbPointFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class AdsbLolFactory(AdsbPointFactory):
    DESCRIPTOR = SourceDescriptor(
        id="adsb_lol",
        name="adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport",
        category="Transport",
        provider="adsb.lol",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.adsb.lol/v2/point/19.436/-99.072/250",
        docs_url="https://www.adsb.lol/docs/open-data/api/",
        terms_url="https://www.adsb.lol/docs/open-data/api/",
        min_interval_s=15.0,
        notes="Aircraft within 250 NM of Mexico City airport (AICM), polled every 15 s; an event is an aircraft whose position, altitude, speed or track changed.",
    )
    URL = "https://api.adsb.lol/v2/point/19.436/-99.072/250"
    INTERVAL_S = 15.0


FACTORY = AdsbLolFactory()
