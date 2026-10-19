"""Bitstamp live trades."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class BitstampDecoder(JsonDecoder):
    """`trade` events; the trade record does not name its pair, so the channel is added."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("event") == "trade" and isinstance(document.get("data"), Mapping):
            return [dict(document["data"], channel=document.get("channel"))]
        return []


class BitstampFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bitstamp",
        name="Bitstamp live trades",
        category="Finance & blockchain",
        provider="Bitstamp",
        group=Group.LOW_RATE,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws.bitstamp.net",
        docs_url="https://www.bitstamp.net/websocket/v2/",
        terms_url="https://www.bitstamp.net/websocket/v2/",
    )
    URL = "wss://ws.bitstamp.net"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"event": "bts:subscribe", "data": {"channel": "live_trades_btcusd"}},
        {"event": "bts:subscribe", "data": {"channel": "live_trades_ethusd"}},
        {"event": "bts:subscribe", "data": {"channel": "live_trades_xrpusd"}},
        {"event": "bts:subscribe", "data": {"channel": "live_trades_btceur"}},
        {"event": "bts:subscribe", "data": {"channel": "live_trades_solusd"}},
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, BitstampDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = BitstampFactory()
