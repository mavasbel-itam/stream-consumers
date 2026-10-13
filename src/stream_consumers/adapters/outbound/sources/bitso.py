"""Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class BitsoDecoder(JsonDecoder):
    """`trades` and `diff-orders` messages carry a list in `payload`; keep-alives (`ka`) have none."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and isinstance(document.get("payload"), list):
            return [dict(p, book=document.get("book"), type=document.get("type")) for p in document["payload"] if isinstance(p, Mapping)]
        return []


class BitsoFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bitso",
        name="Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)",
        category="Finance & blockchain",
        provider="Bitso (Mexico)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws.bitso.com",
        docs_url="https://docs.bitso.com/bitso-api/docs",
        terms_url="https://docs.bitso.com/bitso-api/docs",
    )
    URL = "wss://ws.bitso.com"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"action": "subscribe", "book": "btc_mxn", "type": "trades"},
        {"action": "subscribe", "book": "btc_mxn", "type": "diff-orders"},
        {"action": "subscribe", "book": "usd_mxn", "type": "trades"},
        {"action": "subscribe", "book": "usd_mxn", "type": "diff-orders"},
        {"action": "subscribe", "book": "eth_mxn", "type": "trades"},
        {"action": "subscribe", "book": "eth_mxn", "type": "diff-orders"},
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, BitsoDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = BitsoFactory()
