"""HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.mqtt import MqttSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class HslDecoder(JsonDecoder):
    """High-frequency positioning payloads are wrapped in one key naming the event type (`VP`, `DOO`, ...)."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if isinstance(document, Mapping) and len(document) == 1:
            ((event_type, body),) = document.items()
            if isinstance(body, Mapping):
                return [dict(body, event_type=event_type)]
        return []


class HslFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="hsl",
        name="HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)",
        category="Transport",
        provider="Helsinki Regional Transport Authority (HSL)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.MQTT,
        endpoint="wss://mqtt.hsl.fi:443/",
        docs_url="https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md",
        terms_url="https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return MqttSource(self.DESCRIPTOR, HslDecoder(), deps.clock, "mqtt.hsl.fi", 443, ["/hfp/v2/journey/ongoing/vp/#"], path="/")


FACTORY = HslFactory()
