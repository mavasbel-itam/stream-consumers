"""MTA New York City Subway GTFS-Realtime (A/C/E feed)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GtfsRealtimeFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class MtaGtfsrtFactory(GtfsRealtimeFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mta_gtfsrt",
        name="MTA New York City Subway GTFS-Realtime (A/C/E feed)",
        category="Transport",
        provider="Metropolitan Transportation Authority (MTA)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        docs_url="https://api.mta.info/",
        terms_url="https://www.mta.info/developers",
        min_interval_s=15.0,
        notes="GTFS-Realtime feed polled every 15 s; an event is a feed entity that is new or changed.",
    )
    URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"


FACTORY = MtaGtfsrtFactory()
