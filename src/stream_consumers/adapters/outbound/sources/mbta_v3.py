"""MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class JsonApiDataDecoder(JsonDecoder):
    """JSON:API documents: every resource object in `data` is one event."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        data = document.get("data") if isinstance(document, Mapping) else None
        return [d for d in data if isinstance(d, Mapping)] if isinstance(data, list) else []


class MbtaV3Factory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mbta_v3",
        name="MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)",
        category="Transport",
        provider="Massachusetts Bay Transportation Authority (MBTA)",
        group=Group.FREE_KEY,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api-v3.mbta.com/vehicles",
        docs_url="https://www.mbta.com/developers/v3-api",
        terms_url="https://www.mbta.com/developers/v3-api",
        credential=Credential("MBTA_API_KEY", "https://api-v3.mbta.com/register", required=False),
        min_interval_s=20.0,
        notes="Works without a key at 20 requests per minute (polled every 20 s); MBTA_API_KEY raises the limit to 1,000 per minute and the poll to every 5 s. An event is a vehicle whose updated_at changed.",
    )
    URL = "https://api-v3.mbta.com/vehicles"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return HttpPollSource(
            self.DESCRIPTOR,
            JsonApiDataDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            5.0 if key else 20.0,
            ChangeDetector(["id"], ["attributes.updated_at"]),
            headers={"x-api-key": key} if key else None,
        )


FACTORY = MbtaV3Factory()
