"""Sensor.Community citizen air-quality sensors."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class SensorCommunityDecoder(JsonDecoder):
    """A list of measurements; each `sensordatavalues` entry becomes a field `value.<value_type>`."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        out = []
        for item in document if isinstance(document, list) else []:
            if isinstance(item, Mapping):
                record = {k: v for k, v in item.items() if k != "sensordatavalues"}
                for v in item.get("sensordatavalues") or []:
                    record[f"value.{v.get('value_type')}"] = v.get("value")
                out.append(record)
        return out


class SensorCommunitySource(HttpPollSource):
    """The file holds the measurements of the last 5 minutes: published volume = its rows over 300 s."""

    async def _snapshot_volume(self, records: Sequence[Mapping[str, object]]) -> PublishedVolume | None:
        return PublishedVolume(len(records), 300.0)


class SensorcommFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="sensorcomm",
        name="Sensor.Community citizen air-quality sensors",
        category="Science & sensors",
        provider="Sensor.Community (OK Lab Stuttgart / Code for Germany)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://data.sensor.community/static/v2/data.json",
        docs_url="https://github.com/opendata-stuttgart/meta/wiki/EN-APIs",
        terms_url="https://sensor.community/en/",
        min_interval_s=150.0,
        notes="All sensors, last 5 minutes, polled every 150 s; an event is a new measurement id.",
    )
    URL = "https://data.sensor.community/static/v2/data.json"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return SensorCommunitySource(
            self.DESCRIPTOR, SensorCommunityDecoder(), deps.clock, deps.http, [self.URL], 150.0, ChangeDetector(["id"])
        )


FACTORY = SensorcommFactory()
