"""Bitfinex trades + ticker (public v2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class BitfinexDecoder(JsonDecoder):
    """Frames are arrays `[chanId, ...]`; the channel ids come from the `subscribed` answers, so the decoder
    keeps that mapping (one decoder per connection). Field names follow the public v2 documentation."""

    TRADE = ("ID", "MTS", "AMOUNT", "PRICE")
    TICKER = ("BID", "BID_SIZE", "ASK", "ASK_SIZE", "DAILY_CHANGE", "DAILY_CHANGE_RELATIVE", "LAST_PRICE", "VOLUME", "HIGH", "LOW")

    def __init__(self) -> None:
        self._channels: dict[int, tuple[str, str]] = {}

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping):
            if document.get("event") == "subscribed":
                self._channels[document["chanId"]] = (document["channel"], document.get("symbol", ""))
            return []
        if not (isinstance(document, list) and len(document) >= 2 and document[0] in self._channels):
            return []
        channel, symbol = self._channels[document[0]]
        if channel == "trades" and document[1] == "te" and len(document) > 2 and isinstance(document[2], list):
            return [dict(zip(self.TRADE, document[2], strict=False), symbol=symbol, channel=channel)]
        if channel == "ticker" and isinstance(document[1], list):
            return [dict(zip(self.TICKER, document[1], strict=False), symbol=symbol, channel=channel)]
        return []


class BitfinexFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bitfinex",
        name="Bitfinex trades + ticker (public v2)",
        category="Finance & blockchain",
        provider="Bitfinex",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://api-pub.bitfinex.com/ws/2",
        docs_url="https://docs.bitfinex.com/docs/ws-public",
        terms_url="https://docs.bitfinex.com/docs/ws-public",
    )
    URL = "wss://api-pub.bitfinex.com/ws/2"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"event": "subscribe", "channel": "trades", "symbol": "tBTCUSD"},
        {"event": "subscribe", "channel": "trades", "symbol": "tETHUSD"},
        {"event": "subscribe", "channel": "trades", "symbol": "tSOLUSD"},
        {"event": "subscribe", "channel": "ticker", "symbol": "tBTCUSD"},
        {"event": "subscribe", "channel": "ticker", "symbol": "tETHUSD"},
        {"event": "subscribe", "channel": "ticker", "symbol": "tSOLUSD"},
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, BitfinexDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = BitfinexFactory()
