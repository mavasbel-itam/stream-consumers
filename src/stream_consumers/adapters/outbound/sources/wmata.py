"""WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail (free key)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import ClassVar

from stream_consumers.adapters.outbound.decoders import GtfsRealtimeDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.base import MergedEventSource
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class FeedTaggedGtfsRealtimeDecoder(GtfsRealtimeDecoder):
    """Adds the feed name, because bus and rail entity ids are independent of each other."""

    def __init__(self, feed: str) -> None:
        self._feed = feed

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        return [dict(entity, feed=self._feed) for entity in super().decode(message)]


class WmataFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="wmata",
        name="WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail",
        category="Transport",
        provider="Washington Metropolitan Area Transit Authority (WMATA)",
        group=Group.CANDIDATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb ; https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb",
        docs_url="https://developer.wmata.com/",
        terms_url="https://developer.wmata.com/license",
        credential=Credential(
            ("WMATA_API_KEY",),
            "https://developer.wmata.com/signup",
            how_to_get="Developer account (licence consent and CAPTCHA), then subscribe to a Transit Data service tier; each subscription generates two keys.",
        ),
        min_interval_s=15.0,
        notes=(
            "The key goes in the `api_key` header. Both feeds are polled every 15 s (no numeric tier limit was found "
            "on an official page). An event is a feed entity that is new or changed; `feed` says bus or rail."
        ),
    )
    FEEDS: ClassVar[Mapping[str, str]] = {
        "bus": "https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb",
        "rail": "https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb",
    }
    INTERVAL_S = 15.0

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        headers = {"api_key": (credentials or {})["WMATA_API_KEY"]}
        children = [
            HttpPollSource(
                self.DESCRIPTOR,
                FeedTaggedGtfsRealtimeDecoder(feed),
                deps.clock,
                deps.http,
                [url],
                self.INTERVAL_S,
                ChangeDetector(["id"]),
                headers=headers,
            )
            for feed, url in self.FEEDS.items()
        ]
        return MergedEventSource(self.DESCRIPTOR, children, deps.clock)


FACTORY = WmataFactory()
