"""NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland (free key)."""

from __future__ import annotations

from collections.abc import Mapping

from stream_consumers.adapters.outbound.providers.sources._families import GtfsRealtimeFactory
from stream_consumers.domain.models import Credential, Delivery, Group, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials


class NtaFactory(GtfsRealtimeFactory):
    DESCRIPTOR = SourceDescriptor(
        id="nta",
        name="NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland",
        category="Transport",
        provider="National Transport Authority (NTA), Ireland",
        group=Group.FREE_KEY,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.nationaltransport.ie/gtfsr/v2/Vehicles",
        docs_url="https://developer.nationaltransport.ie/",
        terms_url="https://developer.nationaltransport.ie/usagepolicy",
        credential=Credential(
            ("NTA_API_KEY",),
            "https://developer.nationaltransport.ie/signup",
            how_to_get="Developer-portal account, then subscribe to the 'GTFS Realtime' product; a pair of keys is issued (either works).",
        ),
        min_interval_s=60.0,
        notes=(
            "The key goes in the `x-api-key` header. The usage policy allows one call every 60 seconds per token, so "
            "it is polled every 60 s. The docs do not state the default response format; the decoder reads both "
            "GTFS-Realtime protobuf and its JSON mapping. An event is a feed entity that is new or changed. A rate "
            "needs at least two polls 60 s apart, so windows are at least 150 s."
        ),
        min_window_s=150.0,
    )
    URL = "https://api.nationaltransport.ie/gtfsr/v2/Vehicles"
    INTERVAL_S = 60.0

    def _request(self, credentials: Credentials | None) -> tuple[str, Mapping[str, str]]:
        return self.URL, {"x-api-key": (credentials or {})["NTA_API_KEY"]}


FACTORY = NtaFactory()
