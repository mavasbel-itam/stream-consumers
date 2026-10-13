"""Global Fishing Watch events API — fishing, encounter, loitering and port-visit events (free token)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, Setting, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound import ClockPort, Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies


class GfwEntriesDecoder(JsonDecoder):
    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        entries = document.get("entries") if isinstance(document, Mapping) else None
        return [e for e in entries if isinstance(e, Mapping)] if isinstance(entries, list) else []


class GfwEventsSource(HttpPollSource):
    """Pages of events that started in the last `lookback_days` days (start-date inclusive,
    end-date exclusive, YYYY-MM-DD), recomputed at every poll."""

    BASE = "https://gateway.api.globalfishingwatch.org/v3/events"
    PAGE = 100

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        token: str,
        dataset: str,
        lookback_days: int,
        pages: int,
        interval_s: float,
        backoff: Backoff | None = None,
    ) -> None:
        if lookback_days < 1 or pages < 1:
            raise ValueError("lookback_days and pages must be at least 1")
        super().__init__(
            descriptor,
            decoder,
            clock,
            http,
            [self.BASE],
            interval_s,
            ChangeDetector(["id"]),
            headers={"Authorization": f"Bearer {token}"},
            backoff=backoff,
        )
        self._dataset = dataset
        self._lookback = timedelta(days=lookback_days)
        self._pages = pages

    async def _urls_for_poll(self) -> Sequence[str]:
        today = datetime.fromtimestamp(self._clock.now(), UTC).date()
        start, end = today - self._lookback, today + timedelta(days=1)
        query = f"datasets[0]={quote(self._dataset)}&start-date={start}&end-date={end}&limit={self.PAGE}"
        return [f"{self.BASE}?{query}&offset={page * self.PAGE}" for page in range(self._pages)]


class GfwFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="gfw",
        name="Global Fishing Watch events API — fishing, encounter, loitering and port-visit events",
        category="Transport",
        provider="Global Fishing Watch",
        group=Group.CANDIDATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest&start-date=<YYYY-MM-DD>&end-date=<YYYY-MM-DD>&limit=100&offset=<n>",
        docs_url="https://globalfishingwatch.org/our-apis/documentation",
        terms_url="https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits",
        credential=Credential(
            ("GFW_API_TOKEN",),
            "https://globalfishingwatch.org/our-apis/",
            how_to_get="Global Fishing Watch account, then request an API token (self-service; up to 5 tokens, they do not expire). Non-commercial use only.",
        ),
        settings=(
            Setting(
                "GFW_DATASET", "public-global-fishing-events:latest", "Events dataset (fishing, encounters, loitering or port visits)."
            ),
            Setting("GFW_LOOKBACK_DAYS", "7", "Days back from today whose events are read at every poll."),
            Setting("GFW_PAGES", "5", "Pages of 100 events read at every poll."),
        ),
        min_interval_s=900.0,
        notes=(
            "A query API, not a push stream: events are derived from AIS and published after processing, so new "
            "events appear in batches. Polled every 15 min (limits: 50,000 requests a day, 1,500,000 a month per "
            "user). Data licence CC BY-NC 4.0; tokens must not be shared."
        ),
    )
    INTERVAL_S = 900.0

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return GfwEventsSource(
            self.DESCRIPTOR,
            GfwEntriesDecoder(),
            deps.clock,
            deps.http,
            (credentials or {})["GFW_API_TOKEN"],
            self.setting(deps, "GFW_DATASET"),
            int(self.setting(deps, "GFW_LOOKBACK_DAYS")),
            int(self.setting(deps, "GFW_PAGES")),
            self.INTERVAL_S,
        )


FACTORY = GfwFactory()
