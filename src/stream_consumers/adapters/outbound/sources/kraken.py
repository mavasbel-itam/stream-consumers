"""Kraken trades + ticker (v2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class KrakenDecoder(JsonDecoder):
    """`trade` and `ticker` updates; each carries a list of records in `data`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("channel") in ("trade", "ticker") and document.get("type") == "update":
            return [dict(d, channel=document["channel"]) for d in document.get("data", []) if isinstance(d, Mapping)]
        return []


class KrakenFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="kraken",
        name="Kraken trades + ticker (v2)",
        category="Finance & blockchain",
        provider="Kraken (Payward)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws.kraken.com/v2",
        docs_url="https://docs.kraken.com/api/docs/websocket-v2/trade",
        terms_url="https://docs.kraken.com/api/docs/websocket-v2/trade",
    )
    URL = "wss://ws.kraken.com/v2"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"method": "subscribe", "params": {"channel": "trade", "symbol": ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD"]}},
        {"method": "subscribe", "params": {"channel": "ticker", "symbol": ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD"]}},
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, KrakenDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = KrakenFactory()
