"""Deribit perpetual futures ticker."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class DeribitDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("method") == "subscription":
            data = document.get("params", {}).get("data")
            return [data] if isinstance(data, Mapping) else []
        return []


class DeribitFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="deribit",
        name="Deribit perpetual futures ticker",
        category="Finance & blockchain",
        provider="Deribit",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://www.deribit.com/ws/api/v2",
        docs_url="https://docs.deribit.com/",
        terms_url="https://docs.deribit.com/",
    )
    URL = "wss://www.deribit.com/ws/api/v2"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "public/subscribe",
            "params": {"channels": ["ticker.BTC-PERPETUAL.100ms", "ticker.ETH-PERPETUAL.100ms"]},
        },
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, DeribitDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = DeribitFactory()
