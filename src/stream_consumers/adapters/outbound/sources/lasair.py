"""Lasair — Rubin Observatory LSST alerts that pass your saved filter (free account, Kafka)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.kafka import KafkaSource
from stream_consumers.domain.models import Credential, Delivery, Group, Setting, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class LasairFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="lasair",
        name="Lasair — Rubin Observatory LSST alerts that pass your saved filter",
        category="Science & sensors",
        provider="Lasair (Universities of Edinburgh and Belfast)",
        group=Group.LOW_RATE,
        delivery=Delivery.PUSH,
        transport=Transport.KAFKA,
        endpoint="kafka://lasair-lsst-kafka.lsst.ac.uk:9092/<LASAIR_KAFKA_TOPIC>",
        docs_url="https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html",
        terms_url="https://lasair.lsst.ac.uk/privacy",
        credential=Credential(
            ("LASAIR_KAFKA_TOPIC",),
            "https://lasair.lsst.ac.uk/",
            how_to_get=(
                "Create a Lasair account (e-mail), build and save a filter with Kafka streaming enabled; its topic is "
                "'lasair_' + your user ID + the sanitised filter name. The Kafka server itself needs no password."
            ),
        ),
        settings=(
            Setting(
                "LASAIR_KAFKA_SERVER", "lasair-lsst-kafka.lsst.ac.uk:9092", "Kafka bootstrap server (the official notebook's 'prod' value)."
            ),
            Setting(
                "LASAIR_GROUP_ID",
                "stream-consumers",
                "Kafka consumer group; Lasair remembers per group where delivery stopped, so use your own.",
            ),
        ),
        notes=(
            "JSON messages: the filter's selected fields plus UTC, optionally an `alert` object with the light curve. "
            "Lasair keeps topic messages for 7 days. The rate depends entirely on the filter you save. No terms-of-use "
            "or data licence page was found (only the privacy statement); Lasair asks users to cite Williams et al., "
            "RAS Techniques and Instruments."
        ),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return KafkaSource(
            self.DESCRIPTOR,
            JsonDecoder(),
            deps.clock,
            self.setting(deps, "LASAIR_KAFKA_SERVER"),
            [(credentials or {})["LASAIR_KAFKA_TOPIC"]],
            self.setting(deps, "LASAIR_GROUP_ID"),
        )


FACTORY = LasairFactory()
