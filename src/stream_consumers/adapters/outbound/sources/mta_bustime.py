"""MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus (free key)."""

from __future__ import annotations

from collections.abc import Mapping

from stream_consumers.adapters.outbound.sources._families import GtfsRealtimeFactory
from stream_consumers.domain.models import Credential, Delivery, Group, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials


class MtaBustimeFactory(GtfsRealtimeFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mta_bustime",
        name="MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus",
        category="Transport",
        provider="Metropolitan Transportation Authority (MTA)",
        group=Group.CANDIDATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://gtfsrt.prod.obanyc.com/vehiclePositions?key=<MTA_BUSTIME_KEY>",
        docs_url="https://bustime.mta.info/developers/gtfs-realtime/",
        terms_url="https://www.mta.info/developers/terms-and-conditions",
        credential=Credential(
            ("MTA_BUSTIME_KEY",),
            "https://register.developer.obanyc.com/",
            how_to_get="Web form (name, e-mail, project); the key arrives by e-mail 'within half an hour'.",
        ),
        min_interval_s=30.0,
        notes=(
            "The key goes in the `key` query parameter. Polled every 30 s: the Bus Time docs warn that repeated "
            "requests for all vehicles 'at less than 30 second intervals' may get the key revoked. An event is a "
            "feed entity that is new or changed."
        ),
    )
    URL = "https://gtfsrt.prod.obanyc.com/vehiclePositions"
    INTERVAL_S = 30.0

    def _request(self, credentials: Credentials | None) -> tuple[str, Mapping[str, str]]:
        return f"{self.URL}?key={(credentials or {})['MTA_BUSTIME_KEY']}", {}


FACTORY = MtaBustimeFactory()
