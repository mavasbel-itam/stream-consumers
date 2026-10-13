"""Entur Norway real-time vehicle positions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class EnturVehiclesDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        data = document.get("data") if isinstance(document, Mapping) else None
        vehicles = data.get("vehicles") if isinstance(data, Mapping) else None
        return [v for v in vehicles if isinstance(v, Mapping)] if isinstance(vehicles, list) else []


class EnturFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="entur",
        name="Entur Norway real-time vehicle positions",
        category="Transport",
        provider="Entur AS (Norway)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.entur.io/realtime/v2/vehicles/graphql",
        docs_url="https://developer.entur.org/pages-real-time-intro",
        terms_url="https://developer.entur.org/pages-intro-setup-and-access/",
        min_interval_s=15.0,
        notes="GraphQL query polled every 15 s with the identifying ET-Client-Name header Entur requires; an event is a vehicle whose lastUpdated changed.",
    )
    URL = "https://api.entur.io/realtime/v2/vehicles/graphql"
    QUERY = (
        "{ vehicles { vehicleId lastUpdated codespace { codespaceId } line { lineRef publicCode lineName } "
        "location { latitude longitude } bearing speed delay occupancyStatus vehicleStatus inCongestion "
        "originName destinationName serviceJourney { id } operator { operatorRef } mode } }"
    )
    CLIENT_NAME = "itam-com22102-stream-consumers"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return HttpPollSource(
            self.DESCRIPTOR,
            EnturVehiclesDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            15.0,
            ChangeDetector(["vehicleId"], ["lastUpdated"]),
            headers={"ET-Client-Name": self.CLIENT_NAME},
            json_body={"query": self.QUERY},
        )


FACTORY = EnturFactory()
