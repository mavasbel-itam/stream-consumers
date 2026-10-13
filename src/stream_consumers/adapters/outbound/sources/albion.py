"""Albion Online Data Project market orders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.nats import NatsSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class AlbionOrdersDecoder(JsonDecoder):
    """A message is one order, a list of orders, or an object with an `Orders` list."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and isinstance(document.get("Orders"), list):
            document = document["Orders"]
        return super().extract(document, message)


class AlbionFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="albion",
        name="Albion Online Data Project market orders",
        category="Games, media & social",
        provider="Albion Online Data Project (community)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.NATS,
        endpoint="nats://nats.albion-online-data.com:4222",
        docs_url="https://www.albion-online-data.com/",
        terms_url="https://github.com/ao-data/albiondata-client",
        notes="Public credentials published by the project (user public).",
    )
    SERVER = "nats://nats.albion-online-data.com:4222"
    SUBJECT = "marketorders.deduped"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return NatsSource(
            self.DESCRIPTOR, AlbionOrdersDecoder(), deps.clock, self.SERVER, self.SUBJECT, user="public", password="thenewalbiondata"
        )


FACTORY = AlbionFactory()
