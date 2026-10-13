"""Solana program logs (public mainnet RPC)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class SolanaDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and document.get("method") == "logsNotification":
            result = document.get("params", {}).get("result")
            return [result] if isinstance(result, Mapping) else []
        return []


class SolanaFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="solana",
        name="Solana program logs (public mainnet RPC)",
        category="Finance & blockchain",
        provider="Solana Foundation (public mainnet-beta RPC)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://api.mainnet-beta.solana.com",
        docs_url="https://solana.com/docs/rpc/websocket/logssubscribe",
        terms_url="https://solana.com/docs/references/clusters",
    )
    URL = "wss://api.mainnet-beta.solana.com"
    SUBSCRIPTIONS: tuple[object, ...] = (
        {"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe", "params": ["all", {"commitment": "confirmed"}]},
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, SolanaDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = SolanaFactory()
