"""RIPE NCC RIS Live — global BGP routing updates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class RisDecoder(JsonDecoder):
    """`ris_message` envelopes carry one BGP UPDATE in `data`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("type") == "ris_message" and isinstance(document.get("data"), Mapping):
            return [document["data"]]
        return []


class RisFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ris",
        name="RIPE NCC RIS Live — global BGP routing updates",
        category="Internet & software",
        provider="RIPE NCC",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ris-live.ripe.net/v1/ws/?client=itam-com22102-stream-consumers",
        docs_url="https://ris-live.ripe.net/manual/",
        terms_url="https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions",
    )
    URL = "wss://ris-live.ripe.net/v1/ws/?client=itam-com22102-stream-consumers"
    SUBSCRIPTIONS: tuple[object, ...] = ({"type": "ris_subscribe", "data": {"type": "UPDATE"}},)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, RisDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = RisFactory()
