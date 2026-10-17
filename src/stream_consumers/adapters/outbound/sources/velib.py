"""Vélib' Métropole Paris bike-share station status (GBFS)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.sources._families import GbfsStationsFactory
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport


class VelibFactory(GbfsStationsFactory):
    DESCRIPTOR = SourceDescriptor(
        id="velib",
        name="Vélib' Métropole Paris bike-share station status (GBFS)",
        category="Transport",
        provider="Vélib' Métropole (Smovengo)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json",
        docs_url="https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel",
        terms_url="https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel",
        min_interval_s=10.0,
        notes=(
            "GBFS station_status polled every 10 s; an event is a station whose report time, bikes or docks changed. "
            "The feed names its update time `lastUpdatedOther` instead of GBFS's `last_updated`."
        ),
    )
    URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
    UPDATED_FIELD = "lastUpdatedOther"


FACTORY = VelibFactory()
