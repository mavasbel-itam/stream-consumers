"""Blockchain.com — unconfirmed Bitcoin transactions (WebSocket API)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class BlockchainTransactionDecoder(JsonDecoder):
    """`{"op": "utx", "x": {...}}`: each unconfirmed transaction `x` is one event; other operations are not."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not isinstance(document, Mapping) or document.get("op") != "utx":
            return []
        transaction = document.get("x")
        return [transaction] if isinstance(transaction, Mapping) else []


class BlockchainFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="blockchain",
        name="Blockchain.com — unconfirmed Bitcoin transactions",
        category="Finance & blockchain",
        provider="Blockchain.com",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ws.blockchain.info/inv",
        docs_url="https://www.blockchain.com/api/api_websocket",
        terms_url="https://www.blockchain.com/legal/api-terms",
        notes='Subscribes with {"op": "unconfirmed_sub"}; an event is one transaction entering the mempool.',
    )
    URL = "wss://ws.blockchain.info/inv"
    SUBSCRIPTIONS: tuple[object, ...] = ({"op": "unconfirmed_sub"},)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR,
            BlockchainTransactionDecoder(),
            deps.clock,
            self.URL,
            self.SUBSCRIPTIONS,
            headers={"User-Agent": deps.user_agent},
            keepalive={"op": "ping"},
            keepalive_s=30.0,
        )


FACTORY = BlockchainFactory()
