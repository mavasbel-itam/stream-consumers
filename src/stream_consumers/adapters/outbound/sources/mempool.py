"""mempool.space — Bitcoin transactions entering the mempool."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class MempoolDecoder(JsonDecoder):
    """`mempool-transactions` deltas: each transaction in `added` is one event."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        delta = document.get("mempool-transactions") if isinstance(document, Mapping) else None
        if not isinstance(delta, Mapping):
            return []
        return [t for t in delta.get("added") or [] if isinstance(t, Mapping)]


class MempoolFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mempool",
        name="mempool.space — Bitcoin transactions entering the mempool",
        category="Finance & blockchain",
        provider="The Mempool Open Source Project (mempool.space)",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://mempool.space/api/v1/ws",
        docs_url="https://mempool.space/docs/api/websocket",
        terms_url="https://mempool.space/terms-of-service",
    )
    URL = "wss://mempool.space/api/v1/ws"
    SUBSCRIPTIONS: tuple[object, ...] = ({"track-mempool": True},)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, MempoolDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = MempoolFactory()
