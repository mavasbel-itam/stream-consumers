"""USGS Water Services instantaneous values (river gauges)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, PublishedVolume, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class WaterMlDecoder(JsonDecoder):
    """WaterML-JSON: every value of every time series is one event, with its site and variable."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        value = document.get("value") if isinstance(document, Mapping) else None
        out: list[Mapping[str, object]] = []
        for series in (value or {}).get("timeSeries", []) if isinstance(value, Mapping) else []:
            site = series.get("sourceInfo", {})
            variable = series.get("variable", {})
            for block in series.get("values", []):
                for point in block.get("value", []):
                    out.append({"site": site, "variable": variable, **point})
        return out


class UsgsSource(HttpPollSource):
    """Published volume: values in the last-hour window the request asks for."""

    async def _snapshot_volume(self, records: Sequence[Mapping[str, object]]) -> PublishedVolume | None:
        return PublishedVolume(len(records), 3600.0)


class UsgsWaterFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="usgs_water",
        name="USGS Water Services instantaneous values (river gauges)",
        category="Science & sensors",
        provider="U.S. Geological Survey (USGS)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H&siteStatus=active",
        docs_url="https://waterservices.usgs.gov/",
        terms_url="https://waterservices.usgs.gov/",
        min_interval_s=300.0,
        notes="Texas only. Values of the last hour, polled every 5 min; an event is a new value. The provider announces this legacy service retires on 2027-02-22.",
    )
    URL = "https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H&siteStatus=active"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return UsgsSource(
            self.DESCRIPTOR,
            WaterMlDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            300.0,
            ChangeDetector(["site.siteCode", "variable.variableCode", "dateTime"], ["value"]),
        )


FACTORY = UsgsWaterFactory()
