"""Factories shared by several sources of the same kind.

BaseSourceFactory
├── EvmLogsFactory          eth_subscribe("logs") on a PublicNode WebSocket endpoint
├── GbfsStationsFactory     GBFS station_status, polled and diffed
├── AdsbPointFactory        readsb-style aircraft list around a point, polled and diffed
├── GtfsRealtimeFactory     GTFS-Realtime feed, polled and diffed
└── DigitrafficMqttFactory  Digitraffic (Finland) MQTT over WSS
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import ClassVar

from stream_consumers.adapters.outbound.providers.decoders import GtfsRealtimeDecoder, JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.providers.transports.mqtt import MqttSource
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import RawMessage
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies

Record = Mapping[str, object]


class EvmLogDecoder(JsonDecoder):
    """`eth_subscription` notifications: one event per log; the subscription confirmation is skipped."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Record]:
        if isinstance(document, Mapping) and document.get("method") == "eth_subscription":
            result = document.get("params", {}).get("result")  # type: ignore[union-attr]
            return [result] if isinstance(result, Mapping) else []
        return []


class EvmLogsFactory(BaseSourceFactory):
    URL: ClassVar[str]

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        subscribe = {"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {}]}
        return WebSocketSource(self.DESCRIPTOR, EvmLogDecoder(), deps.clock, self.URL, [subscribe], headers={"User-Agent": deps.user_agent})


class GbfsStationDecoder(JsonDecoder):
    """One event per station; the feed's own update time is copied onto each as `feed_last_updated`."""

    def __init__(self, updated_field: str = "last_updated") -> None:
        self._updated_field = updated_field

    def extract(self, document: object, message: RawMessage) -> Sequence[Record]:
        stations = document.get("data", {}).get("stations") if isinstance(document, Mapping) else None  # type: ignore[union-attr]
        if not isinstance(stations, list):
            return []
        updated = document.get(self._updated_field)  # type: ignore[union-attr]
        return [dict(s, feed_last_updated=updated) for s in stations if isinstance(s, Mapping)]


class GbfsStationsFactory(BaseSourceFactory):
    URL: ClassVar[str]
    INTERVAL_S: ClassVar[float] = 10.0
    UPDATED_FIELD: ClassVar[str] = "last_updated"
    """Top-level field holding the feed's update time (GBFS names it `last_updated`)."""

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["station_id"], ["last_reported", "num_bikes_available", "num_docks_available"])
        decoder = GbfsStationDecoder(self.UPDATED_FIELD)
        return HttpPollSource(self.DESCRIPTOR, decoder, deps.clock, deps.http, [self.URL], self.INTERVAL_S, detector)


class AdsbAircraftDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Record]:
        if not isinstance(document, Mapping):
            return []
        aircraft = document.get("ac") or document.get("aircraft") or []
        now = document.get("now")
        return [dict(a, feed_now=now) for a in aircraft if isinstance(a, Mapping)]


class AdsbPointFactory(BaseSourceFactory):
    URL: ClassVar[str]
    INTERVAL_S: ClassVar[float]

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["hex"], ["lat", "lon", "alt_baro", "gs", "track"])
        return HttpPollSource(self.DESCRIPTOR, AdsbAircraftDecoder(), deps.clock, deps.http, [self.URL], self.INTERVAL_S, detector)


class GtfsRealtimeFactory(BaseSourceFactory):
    URL: ClassVar[str]
    INTERVAL_S: ClassVar[float] = 15.0

    def _request(self, credentials: Credentials | None) -> tuple[str, Mapping[str, str]]:
        """URL and headers of one poll; a keyed feed overrides this to place its key."""
        return self.URL, {}

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        url, headers = self._request(credentials)
        detector = ChangeDetector(["id"])
        return HttpPollSource(
            self.DESCRIPTOR, GtfsRealtimeDecoder(), deps.clock, deps.http, [url], self.INTERVAL_S, detector, headers=headers or None
        )


class DigitrafficDecoder(JsonDecoder):
    """JSON payloads; `TOPIC_FIELDS` names topic segments to copy into the event (the
    payload of some topics omits the identifiers that the topic carries). The `<feed>/status`
    heartbeat topics are not events."""

    def __init__(self, topic_fields: Mapping[int, str]) -> None:
        self._topic_fields = dict(topic_fields)

    def extract(self, document: object, message: RawMessage) -> Sequence[Record]:
        topic = message.attributes.get("topic", "")
        if not isinstance(document, Mapping) or topic.endswith("/status"):
            return []
        segments = topic.split("/")
        extra = {name: segments[i] for i, name in self._topic_fields.items() if i < len(segments)}
        return [{**extra, **document}]


class DigitrafficMqttFactory(BaseSourceFactory):
    HOST: ClassVar[str]
    TOPICS: ClassVar[tuple[str, ...]]
    TOPIC_FIELDS: ClassVar[Mapping[int, str]] = {}

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return MqttSource(self.DESCRIPTOR, DigitrafficDecoder(self.TOPIC_FIELDS), deps.clock, self.HOST, 443, self.TOPICS)
