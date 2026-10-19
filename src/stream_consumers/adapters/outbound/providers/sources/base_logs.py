"""Base (L2) contract event logs (PublicNode RPC)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.sources._families import EvmLogsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class BaseLogsFactory(EvmLogsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="base_logs",
        name="Base (L2) contract event logs (PublicNode RPC)",
        category="Finance & blockchain",
        provider="Allnodes (PublicNode RPC)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://base-rpc.publicnode.com",
        docs_url="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub",
        terms_url="https://www.publicnode.com/",
    )
    URL = "wss://base-rpc.publicnode.com"


FACTORY = BaseLogsFactory()
