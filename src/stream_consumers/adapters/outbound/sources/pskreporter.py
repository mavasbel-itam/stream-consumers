"""PSK Reporter amateur-radio reception reports."""

from __future__ import annotations

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.mqtt import MqttSource
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class PskreporterFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="pskreporter",
        name="PSK Reporter amateur-radio reception reports",
        category="Science & sensors",
        provider="PSK Reporter (Philip Gladstone) — MQTT feed by M0LTE",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.MQTT,
        endpoint="mqtt://mqtt.pskreporter.info:1883",
        docs_url="https://www.mqtt.pskreporter.info/",
        terms_url="https://www.mqtt.pskreporter.info/",
        personal_fields=("sc", "rc", "sl", "rl"),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return MqttSource(
            self.DESCRIPTOR, JsonDecoder(), deps.clock, "mqtt.pskreporter.info", 1883, ["pskr/filter/v2/#"], websockets=False, tls=False
        )


FACTORY = PskreporterFactory()
