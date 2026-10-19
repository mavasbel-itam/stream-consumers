"""Ethereum mainnet contract event logs (PublicNode RPC)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.sources._families import EvmLogsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class EthLogsFactory(EvmLogsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="eth_logs",
        name="Ethereum mainnet contract event logs (PublicNode RPC)",
        category="Finance & blockchain",
        provider="Allnodes (PublicNode RPC)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://ethereum-rpc.publicnode.com",
        docs_url="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub",
        terms_url="https://www.publicnode.com/",
    )
    URL = "wss://ethereum-rpc.publicnode.com"


FACTORY = EthLogsFactory()
