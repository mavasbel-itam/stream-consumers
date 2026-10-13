"""BNB Smart Chain contract event logs (PublicNode RPC)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import EvmLogsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class BscLogsFactory(EvmLogsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bsc_logs",
        name="BNB Smart Chain contract event logs (PublicNode RPC)",
        category="Finance & blockchain",
        provider="Allnodes (PublicNode RPC)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://bsc-rpc.publicnode.com",
        docs_url="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub",
        terms_url="https://www.publicnode.com/",
    )
    URL = "wss://bsc-rpc.publicnode.com"


FACTORY = BscLogsFactory()
