"""Fink — ZTF alert livestream (free credentials on request, Kafka + Avro); LSST through the same source."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.decoders import AvroSchemaInKeyDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.kafka import KafkaSource
from stream_consumers.domain.models import Credential, Delivery, Group, Setting, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class FinkFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="fink",
        name="Fink — ZTF alert livestream (LSST with other settings)",
        category="Science & sensors",
        provider="Fink broker (CNRS/IN2P3 and partners)",
        group=Group.LOW_RATE,
        delivery=Delivery.PUSH,
        transport=Transport.KAFKA,
        endpoint="kafka://<FINK_KAFKA_SERVERS>/<FINK_TOPICS>",
        docs_url="https://doc.ztf.fink-broker.org/services/livestream/",
        terms_url="https://github.com/astrolabsoftware/fink-client",
        credential=Credential(
            ("FINK_KAFKA_SERVERS", "FINK_GROUP_ID"),
            "https://forms.gle/2td4jysT4e9pkf889",
            how_to_get=(
                "Fill the Fink subscription form; the Fink team e-mails one Kafka server address per survey (ZTF, LSST) "
                "and your group.id ('open to any scientists, but it is password protected'). Use the ZTF address."
            ),
        ),
        settings=(
            Setting(
                "FINK_TOPICS",
                "fink_sso_ztf_candidates_ztf,fink_vra_ztf,fink_blazar_ztf",
                "Comma-separated topics, one per Fink filter (ZTF list: https://doc.ztf.fink-broker.org/broker/filters/; "
                "LSST list: https://lsst.fink-portal.org/schemas).",
            ),
        ),
        notes=(
            "Messages are schemaless Avro whose writer schema travels as JSON in the message key (fink-client 12.2 "
            "reads them the same way); image cutouts become base64 text and NaN features null. Consumers connect "
            "without SASL; the broker does not check the group.id, which only keeps the read position. ZTF alerts "
            "arrive during the observing night (about 02:00-15:00 UTC) and are kept 4 days. The LSST server has "
            "carried no alert since 2026-07-14; to read LSST, set FINK_KAFKA_SERVERS to its address and FINK_TOPICS "
            "to LSST topics."
        ),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        values = credentials or {}
        topics = [t.strip() for t in self.setting(deps, "FINK_TOPICS").split(",") if t.strip()]
        return KafkaSource(
            self.DESCRIPTOR, AvroSchemaInKeyDecoder(), deps.clock, values["FINK_KAFKA_SERVERS"], topics, values["FINK_GROUP_ID"]
        )


FACTORY = FinkFactory()
