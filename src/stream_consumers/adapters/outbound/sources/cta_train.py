"""CTA Train Tracker locations — every Chicago 'L' train (free key)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


def as_list(value: object) -> list[object]:
    """A JSON element that holds one item as an object and several as an array."""
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


class CtaTrainDecoder(JsonDecoder):
    """`ctatt.route[].train[]`; the route name is the `@name` attribute. CTA answers errors with
    HTTP 200 and a non-zero `errCd` (Train Tracker API documentation, Appendix E)."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        body = document.get("ctatt") if isinstance(document, Mapping) else None
        if not isinstance(body, Mapping):
            return []
        if str(body.get("errCd", "0")) != "0":
            raise TransportError(f"CTA Train Tracker error {body.get('errCd')}: {body.get('errNm')}")
        out: list[Mapping[str, object]] = []
        for route in as_list(body.get("route")):
            if isinstance(route, Mapping):
                name = route.get("@name")
                out += [dict(t, route=name, tmst=body.get("tmst")) for t in as_list(route.get("train")) if isinstance(t, Mapping)]
        return out


class CtaTrainFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="cta_train",
        name="CTA Train Tracker locations — every Chicago 'L' train",
        category="Transport",
        provider="Chicago Transit Authority (CTA)",
        group=Group.FREE_KEY,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=<CTA_TRAIN_KEY>&rt=<line>&outputType=JSON",
        docs_url="https://www.transitchicago.com/developers/traintracker/",
        terms_url="https://www.transitchicago.com/developers/terms/",
        credential=Credential(
            ("CTA_TRAIN_KEY",),
            "https://www.transitchicago.com/developers/traintrackerapply/",
            how_to_get="Application form (name, address, e-mail, phone, purpose); CTA reviews it and replies.",
        ),
        min_interval_s=30.0,
        notes=(
            "One request per line (Red, Blue, Brn, G, Org, P, Pink, Y) every 30 s = 23,040 requests a day, under the "
            "documented 50,000. An event is a train (route + run number) whose prediction time or position changed."
        ),
    )
    URL = "https://lapi.transitchicago.com/api/1.0/ttpositions.aspx"
    LINES = ("Red", "Blue", "Brn", "G", "Org", "P", "Pink", "Y")
    INTERVAL_S = 30.0

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        key = (credentials or {})["CTA_TRAIN_KEY"]
        urls = [f"{self.URL}?key={key}&rt={line}&outputType=JSON" for line in self.LINES]
        detector = ChangeDetector(["route", "rn"], ["prdt", "lat", "lon"])
        return HttpPollSource(self.DESCRIPTOR, CtaTrainDecoder(), deps.clock, deps.http, urls, self.INTERVAL_S, detector)


FACTORY = CtaTrainFactory()
