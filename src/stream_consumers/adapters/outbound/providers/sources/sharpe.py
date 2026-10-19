"""Sharpe — perpetual-futures funding rates of 37 derivatives exchanges (free REST API)."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport
from stream_consumers.domain.policy import ChangeDetector
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class SharpeFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="sharpe",
        name="Sharpe — perpetual-futures funding rates of 37 derivatives exchanges",
        category="Finance & blockchain",
        provider="Sharpe AI (Sharpe Terminal)",
        group=Group.KEYLESS,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://www.sharpe.ai/api/funding/rates?type=current",
        docs_url="https://www.sharpe.ai/docs/free-api",
        terms_url="https://www.sharpe.ai/docs/free-api",
        min_interval_s=120.0,
        notes=(
            "Keyless, cache-backed endpoint (protective limit 120 requests/min per server instance), polled every "
            "120 s; the snapshot (about 13,600 exchange/symbol rows, about 9 MB) is refreshed about every 5 min "
            "(freshness SLA 600 s). An event is a row whose funding rate, predicted rate, mark price or open interest "
            "changed. Windows are at least 630 s so that every round spans a refresh."
        ),
        min_window_s=630.0,
    )
    URL = "https://www.sharpe.ai/api/funding/rates?type=current"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        detector = ChangeDetector(["exchange", "symbol"], ["rate", "predicted_rate", "mark_price", "open_interest"])
        return HttpPollSource(self.DESCRIPTOR, JsonDecoder(), deps.clock, deps.http, [self.URL], 120.0, detector)


FACTORY = SharpeFactory()
