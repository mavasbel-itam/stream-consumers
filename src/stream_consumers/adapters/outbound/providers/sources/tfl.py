"""Transport for London Unified API — Tube arrival predictions."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class TflFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="tfl",
        name="Transport for London Unified API — Tube arrival predictions",
        category="Transport",
        provider="Transport for London (TfL)",
        group=Group.FREE_KEY,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.tfl.gov.uk/Mode/tube/Arrivals",
        docs_url="https://api-portal.tfl.gov.uk/",
        terms_url="https://api-portal.tfl.gov.uk/",
        credential=Credential(
            ("TFL_APP_KEY",),
            "https://api-portal.tfl.gov.uk/signup",
            required=False,
            how_to_get="API portal account, then subscribe to the product '500 Requests per min' (500 requests per minute).",
        ),
        min_interval_s=30.0,
        notes=(
            "Answers without a key (measured 2026-10-13); TFL_APP_KEY is sent as app_key when set. Polled every 30 s; "
            "an event is an arrival prediction that is new or whose expected arrival or current location changed. A "
            "shared cache serves each answer for up to 60 s (Cache-Control s-maxage=60, X-Cache HIT measured "
            "2026-10-18), so a 60-s window can see one answer twice and no change; windows are at least 150 s."
        ),
        min_window_s=150.0,
    )
    URL = "https://api.tfl.gov.uk/Mode/tube/Arrivals"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        url = f"{self.URL}?app_key={credentials['TFL_APP_KEY']}" if credentials else self.URL
        return HttpPollSource(
            self.DESCRIPTOR,
            JsonDecoder(),
            deps.clock,
            deps.http,
            [url],
            30.0,
            ChangeDetector(["id"], ["expectedArrival", "currentLocation"]),
        )


FACTORY = TflFactory()
