"""Gemini market data v1 (order-book changes + trades)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.base import MergedEventSource
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class GeminiDecoder(JsonDecoder):
    """v1 market data: each `update` carries order-book `change` and `trade` events; the URL fixes the symbol."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not (isinstance(document, Mapping) and document.get("type") == "update"):
            return []
        envelope = {k: document.get(k) for k in ("eventId", "timestampms", "socket_sequence")}
        return [dict(e, symbol=self._symbol, **envelope) for e in document.get("events", []) if isinstance(e, Mapping)]


class GeminiFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="gemini",
        name="Gemini market data v1 (order-book changes + trades)",
        category="Finance & blockchain",
        provider="Gemini Trust Company",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://api.gemini.com/v1/marketdata/{BTCUSD,ETHUSD,SOLUSD}",
        docs_url="https://developer.gemini.com/websocket/streams.md",
        terms_url="https://developer.gemini.com/websocket/streams.md",
        notes="One connection per symbol, read concurrently.",
    )
    URL = "wss://api.gemini.com/v1/marketdata/{symbol}"
    SYMBOLS = ("BTCUSD", "ETHUSD", "SOLUSD")

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        children = [
            WebSocketSource(
                self.DESCRIPTOR, GeminiDecoder(s), deps.clock, self.URL.format(symbol=s), headers={"User-Agent": deps.user_agent}
            )
            for s in self.SYMBOLS
        ]
        return MergedEventSource(self.DESCRIPTOR, children, deps.clock)


FACTORY = GeminiFactory()
