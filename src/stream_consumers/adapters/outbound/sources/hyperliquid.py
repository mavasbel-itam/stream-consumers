"""Hyperliquid trades."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class HyperliquidDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("channel") == "trades":
            return [d for d in document.get("data", []) if isinstance(d, Mapping)]
        return []


class HyperliquidFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="hyperliquid",
        name="Hyperliquid trades",
        category="Finance & blockchain",
        provider="Hyperliquid",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://api.hyperliquid.xyz/ws",
        docs_url="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions",
        terms_url="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions",
        personal_fields=("users",),
    )
    URL = "wss://api.hyperliquid.xyz/ws"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"method": "subscribe", "subscription": {"type": "trades", "coin": "BTC"}},
        {"method": "subscribe", "subscription": {"type": "trades", "coin": "ETH"}},
        {"method": "subscribe", "subscription": {"type": "trades", "coin": "SOL"}},
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, HyperliquidDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = HyperliquidFactory()
