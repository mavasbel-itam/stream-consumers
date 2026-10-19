"""RIPE Atlas measurement results stream (ping)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class AtlasDecoder(JsonDecoder):
    """Frames are `["atlas_result", {...}]`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, list) and len(document) > 1 and document[0] == "atlas_result" and isinstance(document[1], Mapping):
            return [document[1]]
        return []


class AtlasFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="atlas",
        name="RIPE Atlas measurement results stream (ping)",
        category="Internet & software",
        provider="RIPE NCC",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://atlas-stream.ripe.net/stream/?client=itam-com22102-stream-consumers",
        docs_url="https://atlas.ripe.net/docs/apis/streaming-api",
        terms_url="https://atlas.ripe.net/legal/terms-conditions/",
    )
    URL = "wss://atlas-stream.ripe.net/stream/?client=itam-com22102-stream-consumers"
    SUBSCRIPTIONS: tuple[object, ...] = (["atlas_subscribe", {"streamType": "result", "type": "ping"}],)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, AtlasDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = AtlasFactory()
