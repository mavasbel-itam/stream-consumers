"""Digitraffic Finland road traffic (TMS) and road-weather sensors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from stream_consumers.adapters.outbound.providers.sources._families import DigitrafficMqttFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class DtRoadFactory(DigitrafficMqttFactory):
    DESCRIPTOR = SourceDescriptor(
        id="dt_road",
        name="Digitraffic Finland road traffic (TMS) and road-weather sensors",
        category="Transport",
        provider="Fintraffic (Digitraffic)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.MQTT,
        endpoint="wss://tie.digitraffic.fi:443/mqtt",
        docs_url="https://www.digitraffic.fi/en/road-traffic/",
        terms_url="https://www.digitraffic.fi/en/terms-of-service/",
        notes="Topic segments feed, stationId, sensorId are copied into each event.",
    )
    HOST = "tie.digitraffic.fi"
    TOPICS = ("tms-v2/#", "weather-v2/#")
    TOPIC_FIELDS: ClassVar[Mapping[int, str]] = {0: "feed", 1: "stationId", 2: "sensorId"}


FACTORY = DtRoadFactory()
