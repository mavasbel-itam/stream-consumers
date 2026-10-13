"""Coinbase Exchange ticker."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class CoinbaseDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        return [document] if isinstance(document, Mapping) and document.get("type") in ("ticker", "match") else []


class CoinbaseFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="coinbase",
        name="Coinbase Exchange ticker",
        category="Finance & blockchain",
        provider="Coinbase",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws-feed.exchange.coinbase.com",
        docs_url="https://docs.cdp.coinbase.com/exchange/websocket-feed/overview",
        terms_url="https://docs.cdp.coinbase.com/exchange/websocket-feed/overview",
    )
    URL = "wss://ws-feed.exchange.coinbase.com"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"type": "subscribe", "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"], "channels": ["ticker"]},
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, CoinbaseDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = CoinbaseFactory()
