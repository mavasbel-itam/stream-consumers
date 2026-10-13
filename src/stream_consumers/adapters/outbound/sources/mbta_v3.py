"""MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.transports.sse import SseSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class JsonApiDataDecoder(JsonDecoder):
    """JSON:API documents: every resource object in `data` is one event."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        data = document.get("data") if isinstance(document, Mapping) else None
        return [d for d in data if isinstance(d, Mapping)] if isinstance(data, list) else []


class MbtaStreamDecoder(JsonDecoder):
    """V3 API streaming events: `reset` carries every resource (a list), `add` and `update` one
    resource, `remove` a resource identifier. Each event keeps its type in `event_type`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        event = message.attributes.get("event", "")
        items = document if isinstance(document, list) else [document]
        return [dict(item, event_type=event) for item in items if isinstance(item, Mapping)]


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
        credential=Credential(
            ("MBTA_API_KEY",),
            "https://api-v3.mbta.com/register",
            required=False,
            how_to_get="V3 API portal account; request a key per application ('Getting a key might take a day').",
        ),
        min_interval_s=20.0,
        notes=(
            "Without a key: polled every 20 s (20 requests per minute); an event is a vehicle whose updated_at "
            "changed. With MBTA_API_KEY: the vehicles stream over server-sent events (streaming requires a key; a "
            "stream counts once against the 1,000 requests per minute); events are reset, add, update and remove."
        ),
    )
    URL = "https://api-v3.mbta.com/vehicles"
    STREAM_EVENTS = ("reset", "add", "update", "remove")

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        if credentials:
            headers = {"x-api-key": credentials["MBTA_API_KEY"]}
            return SseSource(self.DESCRIPTOR, MbtaStreamDecoder(), deps.clock, deps.http, self.URL, headers, frozenset(self.STREAM_EVENTS))
        return HttpPollSource(
            self.DESCRIPTOR,
            JsonApiDataDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            20.0,
            ChangeDetector(["id"], ["attributes.updated_at"]),
        )


FACTORY = MbtaV3Factory()
