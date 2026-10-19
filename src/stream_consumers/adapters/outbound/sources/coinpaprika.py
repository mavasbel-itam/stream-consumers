"""CoinPaprika — prices and market data of the 2,000 top-ranked crypto assets (free REST API)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class CoinpaprikaFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="coinpaprika",
        name="CoinPaprika — prices and market data of the 2,000 top-ranked crypto assets",
        category="Finance & blockchain",
        provider="CoinPaprika",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://api.coinpaprika.com/v1/tickers",
        docs_url="https://docs.coinpaprika.com/api-reference/rest-api/introduction",
        terms_url="https://docs.coinpaprika.com/api-plans",
        min_interval_s=150.0,
        notes=(
            "The keyless free plan allows 20,000 requests per month (a poll every 150 s is 17,280 per 30 days) and "
            "is for personal use; the provider refreshes all tickers together about every 5 min ('up to 10 min'). "
            "An event is a ticker whose USD price or 24-h volume changed. Windows are at least 630 s so that every "
            "round spans a refresh."
        ),
        min_window_s=630.0,
    )
    URL = "https://api.coinpaprika.com/v1/tickers"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["id"], ["last_updated", "quotes.USD.price", "quotes.USD.volume_24h"])
        return HttpPollSource(self.DESCRIPTOR, JsonDecoder(), deps.clock, deps.http, [self.URL], 150.0, detector)


FACTORY = CoinpaprikaFactory()
