"""OKX public tickers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class OkxDecoder(JsonDecoder):
    """Ticker pushes carry records in `data`; the `pong` answer to the keep-alive is not JSON and is skipped."""

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        return [] if self.text(message) == "pong" else super().decode(message)

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and isinstance(document.get("data"), list):
            return [d for d in document["data"] if isinstance(d, Mapping)]
        return []


class OkxFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="okx",
        name="OKX public tickers",
        category="Finance & blockchain",
        provider="OKX",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws.okx.com:8443/ws/v5/public",
        docs_url="https://www.okx.com/docs-v5/en/",
        terms_url="https://www.okx.com/docs-v5/en/",
    )
    URL = "wss://ws.okx.com:8443/ws/v5/public"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {
            "op": "subscribe",
            "args": [
                {"channel": "tickers", "instId": "BTC-USDT"},
                {"channel": "tickers", "instId": "ETH-USDT"},
                {"channel": "tickers", "instId": "SOL-USDT"},
                {"channel": "tickers", "instId": "XRP-USDT"},
                {"channel": "tickers", "instId": "DOGE-USDT"},
            ],
        },
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR,
            OkxDecoder(),
            deps.clock,
            self.URL,
            self.SUBSCRIPTIONS,
            headers={"User-Agent": deps.user_agent},
            keepalive="ping",
        )


FACTORY = OkxFactory()
