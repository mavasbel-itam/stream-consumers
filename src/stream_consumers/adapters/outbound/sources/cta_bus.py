"""CTA Bus Tracker vehicles — every Chicago bus (free key)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.sources.cta_train import as_list
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound import ClockPort, Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies

NO_DATA = "No data found for parameter"


def bus_errors(body: Mapping[str, object]) -> list[str]:
    """Error messages of a `bustime-response`, except "No data found for parameter", which the
    Bus Tracker documentation lists as "No results were found that matched the given parameters"
    (a route with no bus on the road)."""
    messages = [str(e.get("msg", "")) for e in as_list(body.get("error")) if isinstance(e, Mapping)]
    return [m for m in messages if not m.startswith(NO_DATA)]


class CtaBusDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        body = document.get("bustime-response") if isinstance(document, Mapping) else None
        if not isinstance(body, Mapping):
            return []
        errors = bus_errors(body)
        if errors:
            raise TransportError(f"CTA Bus Tracker error: {'; '.join(errors)}")
        return [v for v in as_list(body.get("vehicle")) if isinstance(v, Mapping)]


class CtaBusSource(HttpPollSource):
    """Reads the route list once (getroutes), then asks getvehicles for at most 10 routes per request."""

    BASE = "https://www.ctabustracker.com/bustime/api/v3"
    ROUTES_PER_REQUEST = 10

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        key: str,
        interval_s: float,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(
            descriptor,
            decoder,
            clock,
            http,
            [f"{self.BASE}/getroutes?key={key}&format=json"],
            interval_s,
            ChangeDetector(["vid"], ["tmstmp", "lat", "lon"]),
            backoff=backoff,
        )
        self._key = key
        self._vehicle_urls: list[str] | None = None

    async def _urls_for_poll(self) -> Sequence[str]:
        if self._vehicle_urls is None:
            url = self._urls[0]
            document = JsonDecoder().decode(RawMessage(self.ok(await self._request(url), url)))
            body = document[0].get("bustime-response") if document else None
            if not isinstance(body, Mapping) or bus_errors(body):
                raise TransportError(f"CTA getroutes failed: {body}")
            routes = [str(r["rt"]) for r in as_list(body.get("routes")) if isinstance(r, Mapping) and r.get("rt")]
            if not routes:
                raise TransportError("CTA getroutes returned no routes")
            step = self.ROUTES_PER_REQUEST
            self._vehicle_urls = [
                f"{self.BASE}/getvehicles?key={self._key}&rt={','.join(routes[i : i + step])}&tmres=s&format=json"
                for i in range(0, len(routes), step)
            ]
        return self._vehicle_urls


class CtaBusFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="cta_bus",
        name="CTA Bus Tracker vehicles — every Chicago bus",
        category="Transport",
        provider="Chicago Transit Authority (CTA)",
        group=Group.CANDIDATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://www.ctabustracker.com/bustime/api/v3/getvehicles?key=<CTA_BUS_KEY>&rt=<up to 10 routes>&format=json",
        docs_url="https://www.transitchicago.com/developers/bustracker/",
        terms_url="https://www.transitchicago.com/developers/terms/",
        credential=Credential(
            ("CTA_BUS_KEY",),
            "https://www.ctabustracker.com/bustime/login.jsp",
            how_to_get="Create and activate a Bus Tracker account, then My Account → Developer API → apply; the key is e-mailed after approval (one key per account).",
        ),
        min_interval_s=30.0,
        notes=(
            "Reads the route list once, then polls getvehicles every 30 s with 10 routes per request (about 13 "
            "requests per poll, about 37,000 a day, under the documented 100,000). An event is a bus whose "
            "timestamp or position changed."
        ),
    )
    INTERVAL_S = 30.0

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return CtaBusSource(self.DESCRIPTOR, CtaBusDecoder(), deps.clock, deps.http, (credentials or {})["CTA_BUS_KEY"], self.INTERVAL_S)


FACTORY = CtaBusFactory()
