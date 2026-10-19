"""Bybit spot tickers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class BybitDecoder(JsonDecoder):
    """Ticker pushes: `topic` tickers.<symbol>, record in `data`; subscription and ping answers have no topic."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if (
            isinstance(document, Mapping)
            and str(document.get("topic", "")).startswith("tickers.")
            and isinstance(document.get("data"), Mapping)
        ):
            return [dict(document["data"], ts=document.get("ts"), cs=document.get("cs"), type=document.get("type"))]
        return []


class BybitFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bybit",
        name="Bybit spot tickers",
        category="Finance & blockchain",
        provider="Bybit",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://stream.bybit.com/v5/public/spot",
        docs_url="https://bybit-exchange.github.io/docs/v5/websocket/public/ticker",
        terms_url="https://bybit-exchange.github.io/docs/v5/websocket/public/ticker",
    )
    URL = "wss://stream.bybit.com/v5/public/spot"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"op": "subscribe", "args": ["tickers.BTCUSDT", "tickers.ETHUSDT", "tickers.SOLUSDT", "tickers.XRPUSDT", "tickers.DOGEUSDT"]},
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR,
            BybitDecoder(),
            deps.clock,
            self.URL,
            self.SUBSCRIPTIONS,
            headers={"User-Agent": deps.user_agent},
            keepalive={"op": "ping"},
        )


FACTORY = BybitFactory()
