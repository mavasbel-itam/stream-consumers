"""OpenSky Network state vectors — aircraft over Mexico."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class OpenSkyStatesDecoder(JsonDecoder):
    """`states` is a list of arrays; positions follow the REST API documentation."""

    FIELDS = (
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "on_ground",
        "velocity",
        "true_track",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
        "category",
    )

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not isinstance(document, Mapping):
            return []
        return [
            dict(zip(self.FIELDS, s, strict=False), time=document.get("time")) for s in document.get("states") or [] if isinstance(s, list)
        ]


class OpenskyFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="opensky",
        name="OpenSky Network state vectors — aircraft over Mexico",
        category="Transport",
        provider="OpenSky Network",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86",
        docs_url="https://openskynetwork.github.io/opensky-api/rest.html",
        terms_url="https://opensky-network.org/about/terms-of-use",
        min_interval_s=30.0,
        notes="Anonymous access: 400 credits per day; this bounding box (19° x 32° = 608 sq°) costs 4 credits per request, so it is polled every 30 s (a 60 s sampling window uses at most 12 credits). An event is an aircraft whose position time or last contact changed.",
    )
    URL = "https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return HttpPollSource(
            self.DESCRIPTOR,
            OpenSkyStatesDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            30.0,
            ChangeDetector(["icao24"], ["time_position", "last_contact"]),
        )


FACTORY = OpenskyFactory()
