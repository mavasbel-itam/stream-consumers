"""Binance spot trades + 24 h tickers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class BinanceDecoder(JsonDecoder):
    """Combined-stream envelopes `{"stream": ..., "data": {...}}`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and isinstance(document.get("data"), Mapping):
            return [dict(document["data"], stream=document.get("stream"))]
        return []


class BinanceFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="binance",
        name="Binance spot trades + 24 h tickers",
        category="Finance & blockchain",
        provider="Binance",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade/btcusdt@ticker/ethusdt@ticker",
        docs_url="https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md",
        terms_url="https://www.binance.com/en/terms",
        notes="The terms page is served behind a JavaScript challenge (HTTP 202 to scripts) and could not be machine-verified.",
    )
    URL = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade/btcusdt@ticker/ethusdt@ticker"
    SUBSCRIPTIONS: tuple[object, ...] = ()

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, BinanceDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = BinanceFactory()
