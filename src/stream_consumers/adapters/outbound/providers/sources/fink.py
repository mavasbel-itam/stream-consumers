"""Fink — Rubin Observatory LSST and ZTF alert livestream (free credentials on request, Kafka + Avro)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.decoders import AvroSchemaInKeyDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.kafka import KafkaSource
from stream_consumers.domain.models import Credential, Delivery, Group, Setting, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class FinkFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="fink",
        name="Fink — Rubin Observatory LSST and ZTF alert livestream",
        category="Science & sensors",
        provider="Fink broker (CNRS/IN2P3 and partners)",
        group=Group.LOW_RATE,
        delivery=Delivery.PUSH,
        transport=Transport.KAFKA,
        endpoint="kafka://<FINK_KAFKA_SERVERS>/<FINK_TOPICS>",
        docs_url="https://doc.lsst.fink-broker.org/services/livestream/",
        terms_url="https://github.com/astrolabsoftware/fink-client",
        credential=Credential(
            ("FINK_KAFKA_SERVERS", "FINK_GROUP_ID"),
            "https://forms.gle/2td4jysT4e9pkf889",
            how_to_get=(
                "Fill the Fink subscription form; the Fink team e-mails the Kafka server address and your group.id "
                "('open to any scientists, but it is password protected')."
            ),
        ),
        settings=(
            Setting(
                "FINK_TOPICS",
                "fink_extragalactic_lt20mag_candidate_lsst",
                "Comma-separated topics (one per Fink filter; list at https://lsst.fink-portal.org/schemas).",
            ),
        ),
        notes=(
            "Messages are schemaless Avro whose writer schema travels as JSON in the message key (fink-client 12.2 "
            "reads them the same way); image cutouts become base64 text. Fink 12.x consumers connect without SASL. "
            "The rate depends on the topics chosen."
        ),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        values = credentials or {}
        topics = [t.strip() for t in self.setting(deps, "FINK_TOPICS").split(",") if t.strip()]
        return KafkaSource(
            self.DESCRIPTOR, AvroSchemaInKeyDecoder(), deps.clock, values["FINK_KAFKA_SERVERS"], topics, values["FINK_GROUP_ID"]
        )


FACTORY = FinkFactory()
