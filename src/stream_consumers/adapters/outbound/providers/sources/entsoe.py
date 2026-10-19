"""ENTSO-E Transparency Platform — actual electricity generation per production type (free token)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, Setting, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort

NO_DATA = "No matching data found"
DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?$")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, *path: str) -> str | None:
    node: ET.Element | None = element
    for name in path:
        node = next((c for c in node if local(c.tag) == name), None) if node is not None else None
    return node.text.strip() if node is not None and node.text else None


def resolution(text: str | None) -> timedelta:
    match = DURATION.match(text or "")
    if not match or not any(match.groups()):
        raise DecodeError(f"unsupported ENTSO-E resolution: {text!r}")
    return timedelta(hours=int(match.group(1) or 0), minutes=int(match.group(2) or 0))


def instant(text: str | None) -> datetime:
    try:
        return datetime.strptime(text or "", "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise DecodeError(f"unsupported ENTSO-E time: {text!r}") from exc


class EntsoeGenerationDecoder(BaseDecoder):
    """GL_MarketDocument (IEC 62325-451-6): one event per TimeSeries/Period/Point, its time being
    Period start + (position - 1) x resolution. An Acknowledgement_MarketDocument saying
    "No matching data found" is an empty answer; any other acknowledgement is a refusal."""

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        try:
            root = ET.fromstring(self.raw(message))
        except ET.ParseError as exc:
            raise DecodeError(f"invalid XML: {exc}") from exc
        if local(root.tag) == "Acknowledgement_MarketDocument":
            reason = child_text(root, "Reason", "text") or ""
            if reason.startswith(NO_DATA):
                return []
            raise TransportError(f"ENTSO-E refused the request: {child_text(root, 'Reason', 'code')} {reason}")
        out: list[Mapping[str, object]] = []
        for series in (c for c in root if local(c.tag) == "TimeSeries"):
            area_in = child_text(series, "inBiddingZone_Domain.mRID")
            meta = {
                "document_mrid": child_text(root, "mRID"),
                "series_mrid": child_text(series, "mRID"),
                "business_type": child_text(series, "businessType"),
                "object_aggregation": child_text(series, "objectAggregation"),
                "area": area_in or child_text(series, "outBiddingZone_Domain.mRID"),
                "direction": "generation" if area_in else "consumption",
                "unit": child_text(series, "quantity_Measure_Unit.name"),
                "curve_type": child_text(series, "curveType"),
                "psr_type": child_text(series, "MktPSRType", "psrType"),
            }
            for period in (c for c in series if local(c.tag) == "Period"):
                start = instant(child_text(period, "timeInterval", "start"))
                step = resolution(child_text(period, "resolution"))
                for point in (c for c in period if local(c.tag) == "Point"):
                    position = int(child_text(point, "position") or "0")
                    quantity = child_text(point, "quantity")
                    out.append(
                        {
                            **meta,
                            "resolution": child_text(period, "resolution"),
                            "position": position,
                            "timestamp": (start + (position - 1) * step).strftime("%Y-%m-%dT%H:%MZ"),
                            "quantity": float(quantity) if quantity is not None else None,
                        }
                    )
        return out


class EntsoeGenerationSource(HttpPollSource):
    """One request per area for the last `window_h` hours (UTC, yyyyMMddHHmm), every poll."""

    BASE = "https://web-api.tp.entsoe.eu/api"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        token: str,
        areas: Sequence[str],
        interval_s: float,
        window_h: int = 6,
        backoff: Backoff | None = None,
    ) -> None:
        if not areas:
            raise ValueError("at least one ENTSO-E area (EIC code) is needed")
        super().__init__(
            descriptor,
            decoder,
            clock,
            http,
            [self.BASE],
            interval_s,
            ChangeDetector(["area", "direction", "psr_type", "business_type", "timestamp"], ["quantity"]),
            backoff=backoff,
        )
        self._token = token
        self._areas = tuple(areas)
        self._window = timedelta(hours=window_h)

    async def _urls_for_poll(self) -> Sequence[str]:
        end = datetime.fromtimestamp(self._clock.now(), UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        start = end - self._window
        span = f"periodStart={start:%Y%m%d%H%M}&periodEnd={end:%Y%m%d%H%M}"
        return [f"{self.BASE}?securityToken={self._token}&documentType=A75&processType=A16&in_Domain={area}&{span}" for area in self._areas]


class EntsoeFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="entsoe",
        name="ENTSO-E Transparency Platform — actual electricity generation per production type",
        category="Weather & environment",
        provider="European Network of Transmission System Operators for Electricity (ENTSO-E)",
        group=Group.LOW_RATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://web-api.tp.entsoe.eu/api?securityToken=<ENTSOE_TOKEN>&documentType=A75&processType=A16&in_Domain=<EIC>&periodStart=<yyyyMMddHHmm>&periodEnd=<yyyyMMddHHmm>",
        docs_url="https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API",
        terms_url="https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions",
        credential=Credential(
            ("ENTSOE_TOKEN",),
            "https://transparency.entsoe.eu/",
            how_to_get="Register on the Transparency Platform, then e-mail transparency@entsoe.eu asking for RESTful API access; the token is granted 'within 3 working days'.",
        ),
        settings=(
            Setting(
                "ENTSOE_AREAS",
                "10Y1001A1001A83F,10YFR-RTE------C,10YES-REE------0",
                "Comma-separated EIC codes of the areas to read (default Germany, France, Spain; list in the platform's Area List with EIC).",
            ),
        ),
        min_interval_s=300.0,
        notes=(
            "Document A75 (actual generation per type), process A16 (realised), last 6 hours, one request per area "
            "every 5 minutes (the limit is 400 requests per minute). An event is a data point (area, production "
            "type, time) that is new or whose quantity changed. Load (6.1.A), generation (16.1.B/C) and prices "
            "(12.1.D) are not in the platform's CC BY 4.0 list: reuse follows its Terms of Use (credit the source)."
        ),
    )
    INTERVAL_S = 300.0

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        areas = [a.strip() for a in self.setting(deps, "ENTSOE_AREAS").split(",") if a.strip()]
        token = (credentials or {})["ENTSOE_TOKEN"]
        return EntsoeGenerationSource(self.DESCRIPTOR, EntsoeGenerationDecoder(), deps.clock, deps.http, token, areas, self.INTERVAL_S)


FACTORY = EntsoeFactory()
