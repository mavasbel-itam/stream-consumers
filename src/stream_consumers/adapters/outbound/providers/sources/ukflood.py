"""Environment Agency (England) — real-time flood-monitoring readings: river level, flow, rainfall, tide."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class FloodReadingsDecoder(JsonDecoder):
    """`items` of a readings answer: one event per reading (with `_view=full`, its measure and station inline)."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        items = document.get("items") if isinstance(document, Mapping) else None
        return [i for i in items if isinstance(i, Mapping)] if isinstance(items, list) else []


class UkfloodFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ukflood",
        name="Environment Agency (England) — real-time flood-monitoring readings: river level, flow, rainfall, tide",
        category="Weather & environment",
        provider="Environment Agency (England)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://environment.data.gov.uk/flood-monitoring/data/readings?latest&_view=full",
        docs_url="https://environment.data.gov.uk/flood-monitoring/doc/reference",
        terms_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        min_interval_s=900.0,
        notes=(
            "The latest reading of every measure (about 5,400), polled every 15 min as the documentation advises "
            "('issue a single call every 15 mins'); an event is a new reading of a measure. Open Government Licence; "
            "attribution: 'this uses Environment Agency flood and river level data from the real-time data API (Beta)'. "
            "Windows are at least 960 s so that every round has two polls."
        ),
        min_window_s=960.0,
    )
    URL = "https://environment.data.gov.uk/flood-monitoring/data/readings?latest&_view=full"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["measure.@id"], ["dateTime"])
        return HttpPollSource(self.DESCRIPTOR, FloodReadingsDecoder(), deps.clock, deps.http, [self.URL], 900.0, detector)


FACTORY = UkfloodFactory()
