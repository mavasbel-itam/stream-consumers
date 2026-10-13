"""MBTA Boston GTFS-Realtime VehiclePositions."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GtfsRealtimeFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class MbtaGtfsrtFactory(GtfsRealtimeFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mbta_gtfsrt",
        name="MBTA Boston GTFS-Realtime VehiclePositions",
        category="Transport",
        provider="Massachusetts Bay Transportation Authority (MBTA)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://cdn.mbta.com/realtime/VehiclePositions.pb",
        docs_url="https://www.mbta.com/developers/gtfs-realtime",
        terms_url="https://www.mbta.com/developers/gtfs-realtime",
        min_interval_s=15.0,
        notes="GTFS-Realtime feed polled every 15 s; an event is a feed entity that is new or changed.",
    )
    URL = "https://cdn.mbta.com/realtime/VehiclePositions.pb"


FACTORY = MbtaGtfsrtFactory()
