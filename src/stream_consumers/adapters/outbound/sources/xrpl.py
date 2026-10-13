"""XRP Ledger transactions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class XrplDecoder(JsonDecoder):
    """`transaction` messages: the transaction plus its ledger, validation flag and result code."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not (isinstance(document, Mapping) and document.get("type") == "transaction"):
            return []
        tx = dict(document.get("tx_json") or document.get("transaction") or {})
        meta = document.get("meta") if isinstance(document.get("meta"), Mapping) else {}
        tx.update(
            ledger_index=document.get("ledger_index"),
            validated=document.get("validated"),
            close_time_iso=document.get("close_time_iso"),
            TransactionResult=meta.get("TransactionResult"),
        )
        return [tx]


class XrplFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="xrpl",
        name="XRP Ledger transactions",
        category="Finance & blockchain",
        provider="XRP Ledger Foundation (public cluster xrplcluster.com)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://xrplcluster.com/",
        docs_url="https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe",
        terms_url="https://xrpl.org/docs/tutorials/public-servers",
    )
    URL = "wss://xrplcluster.com/"
    SUBSCRIPTIONS: tuple[object, ...] = ({"command": "subscribe", "streams": ["transactions"]},)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, XrplDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = XrplFactory()
