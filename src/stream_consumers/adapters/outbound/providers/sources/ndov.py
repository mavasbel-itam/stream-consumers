"""NDOV Loket Netherlands public transport KV6 (all operators)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.zeromq import ZmqSubSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class Kv6Decoder(BaseDecoder):
    """gzip-compressed KV6 XML: each vehicle-journey message element becomes one event with its child fields."""

    MESSAGE = re.compile(r"<tmi8:(ONROUTE|DEPARTURE|ARRIVAL|ONSTOP|INIT|END|OFFROUTE|DELAY)>(.*?)</tmi8:\1>", re.S)
    FIELD = re.compile(r"<tmi8:([\w-]+)>([^<]*)</tmi8:\1>")

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        xml = self.gunzip(self.raw(message)).decode("utf-8", "replace")
        envelope = message.attributes.get("envelope", "")
        return [dict(self.FIELD.findall(m.group(2)), messagetype=m.group(1), envelope=envelope) for m in self.MESSAGE.finditer(xml)]


class NdovFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ndov",
        name="NDOV Loket Netherlands public transport KV6 (all operators)",
        category="Transport",
        provider="NDOV Loket (Netherlands)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.ZMQ,
        endpoint="tcp://pubsub.besteffort.ndovloket.nl:7658",
        docs_url="https://ndovloket.nl/",
        terms_url="https://ndovloket.nl/",
        notes="Best-effort relay; all operators and all envelopes.",
    )
    ENDPOINT = "tcp://pubsub.besteffort.ndovloket.nl:7658"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ZmqSubSource(self.DESCRIPTOR, Kv6Decoder(), deps.clock, self.ENDPOINT)


FACTORY = NdovFactory()
