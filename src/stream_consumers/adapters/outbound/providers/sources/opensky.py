"""OpenSky Network state vectors — aircraft over Mexico."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.auth import OAuthClientCredentials
from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, Setting, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class OpenSkyStatesDecoder(JsonDecoder):
    """`states` is a list of arrays; positions follow the REST API documentation."""

    FIELDS = (
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "on_ground",
        "velocity",
        "true_track",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
        "category",
    )

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not isinstance(document, Mapping):
            return []
        return [
            dict(zip(self.FIELDS, s, strict=False), time=document.get("time")) for s in document.get("states") or [] if isinstance(s, list)
        ]


class OpenskyFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="opensky",
        name="OpenSky Network state vectors — aircraft over Mexico",
        category="Transport",
        provider="OpenSky Network",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86",
        docs_url="https://openskynetwork.github.io/opensky-api/rest.html",
        terms_url="https://opensky-network.org/about/terms-of-use",
        credential=Credential(
            ("OPENSKY_CLIENT_ID", "OPENSKY_CLIENT_SECRET"),
            "https://opensky-network.org/my-opensky/account",
            required=False,
            how_to_get="OpenSky account → Account page → create an API client (its id ends in -api-client) and copy client_id and client_secret.",
        ),
        settings=(
            Setting(
                "OPENSKY_POLL_SECONDS",
                "30",
                "Seconds between requests. This box costs 4 credits per request: anonymous 400 credits/day, standard account 4,000/day.",
            ),
        ),
        min_interval_s=30.0,
        notes=(
            "Without credentials: anonymous access, 400 credits per day. With an API client: OAuth 2 client "
            "credentials (token valid 30 minutes) and 4,000 credits per day. This bounding box (19° x 32° = 608 sq°) "
            "costs 4 credits per request, so polling every 30 s suits short sampling windows only; continuous "
            "reading needs OPENSKY_POLL_SECONDS of about 90 (account) or 870 (anonymous). An event is an aircraft "
            "whose position time or last contact changed. The terms require a written agreement for 'operational' "
            "REST API use, including automated systems, even non-profit ones."
        ),
    )
    TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    URL = "https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        auth = None
        if credentials:
            auth = OAuthClientCredentials(
                deps.http, deps.clock, self.TOKEN_URL, credentials["OPENSKY_CLIENT_ID"], credentials["OPENSKY_CLIENT_SECRET"]
            )
        return HttpPollSource(
            self.DESCRIPTOR,
            OpenSkyStatesDecoder(),
            deps.clock,
            deps.http,
            [self.URL],
            float(self.setting(deps, "OPENSKY_POLL_SECONDS")),
            ChangeDetector(["icao24"], ["time_position", "last_contact"]),
            auth=auth,
        )


FACTORY = OpenskyFactory()
