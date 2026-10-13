"""Digitraffic Finland marine AIS vessel locations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from stream_consumers.adapters.outbound.sources._families import DigitrafficMqttFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class DtMarineFactory(DigitrafficMqttFactory):
    DESCRIPTOR = SourceDescriptor(
        id="dt_marine",
        name="Digitraffic Finland marine AIS vessel locations",
        category="Transport",
        provider="Fintraffic (Digitraffic)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.MQTT,
        endpoint="wss://meri.digitraffic.fi:443/mqtt",
        docs_url="https://www.digitraffic.fi/en/marine-traffic/",
        terms_url="https://www.digitraffic.fi/en/terms-of-service/",
        notes="Topic segments mmsi are copied into each event.",
    )
    HOST = "meri.digitraffic.fi"
    TOPICS = ("vessels-v2/+/location",)
    TOPIC_FIELDS: ClassVar[Mapping[int, str]] = {1: "mmsi"}


FACTORY = DtMarineFactory()
