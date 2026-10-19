"""Polymarket CLOB market channel (prediction-market prices)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort


class PolymarketDecoder(JsonDecoder):
    """Market-channel frames (one object or a list): each `price_changes` item is one event;
    `last_trade_price` and `tick_size_change` events are kept whole. The `PONG` keep-alive answer is skipped."""

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        return [] if self.text(message) == "PONG" else super().decode(message)

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        out: list[Mapping[str, object]] = []
        for item in document if isinstance(document, list) else [document]:
            if not isinstance(item, Mapping):
                continue
            if item.get("event_type") == "price_change":
                for change in item.get("price_changes", []):
                    if isinstance(change, Mapping):
                        out.append(
                            {"market": item.get("market"), "timestamp": item.get("timestamp"), "event_type": "price_change", **change}
                        )
            elif item.get("event_type") in ("last_trade_price", "tick_size_change"):
                out.append(item)
        return out


class PolymarketSource(WebSocketSource):
    """Subscribes to the outcome tokens of the `markets` most traded markets of the last 24 h,
    looked up on the Gamma API at every (re)connection."""

    MARKETS_URL = "https://gamma-api.polymarket.com/markets?active=true&closed=false&order=volume24hr&ascending=false&limit={limit}"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        url: str,
        markets: int = 25,
        headers: Mapping[str, str] | None = None,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, url, (), headers, keepalive="PING", keepalive_s=10.0, backoff=backoff)
        self._http = http
        self._markets = markets

    async def _subscription_messages(self) -> Sequence[object]:
        response = await self._http.get(self.MARKETS_URL.format(limit=self._markets))
        if response.status != 200:
            raise TransportError(f"Gamma API HTTP {response.status}")
        tokens = [t for m in json.loads(response.body) for t in json.loads(m.get("clobTokenIds") or "[]")]
        return [{"assets_ids": tokens, "type": "market"}]


class PolymarketFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="polymarket",
        name="Polymarket CLOB market channel (prediction-market prices)",
        category="Finance & blockchain",
        provider="Polymarket",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws-subscriptions-clob.polymarket.com/ws/market",
        docs_url="https://docs.polymarket.com/developers/CLOB/websocket/market-channel",
        terms_url="https://docs.polymarket.com/developers/CLOB/websocket/market-channel",
        notes="Subscribes to the 25 markets with the highest 24 h volume.",
    )
    URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return PolymarketSource(
            self.DESCRIPTOR, PolymarketDecoder(), deps.clock, deps.http, self.URL, headers={"User-Agent": deps.user_agent}
        )


FACTORY = PolymarketFactory()
