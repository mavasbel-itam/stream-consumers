"""Digitraffic Finland train GPS locations."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.sources._families import DigitrafficMqttFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class DtRailFactory(DigitrafficMqttFactory):
    DESCRIPTOR = SourceDescriptor(
        id="dt_rail",
        name="Digitraffic Finland train GPS locations",
        category="Transport",
        provider="Fintraffic (Digitraffic)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.MQTT,
        endpoint="wss://rata.digitraffic.fi:443/mqtt",
        docs_url="https://www.digitraffic.fi/en/railway-traffic/",
        terms_url="https://www.digitraffic.fi/en/terms-of-service/",
    )
    HOST = "rata.digitraffic.fi"
    TOPICS = ("train-locations/#",)


FACTORY = DtRailFactory()
