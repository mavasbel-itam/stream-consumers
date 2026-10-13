"""Wikimedia EventStreams — recent changes on all Wikimedia wikis."""

from __future__ import annotations

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.sse import SseSource
from stream_consumers.domain.models import Delivery, Group, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class WikimediaFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="wikimedia",
        name="Wikimedia EventStreams — recent changes on all Wikimedia wikis",
        category="Internet & software",
        provider="Wikimedia Foundation",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.PUSH,
        transport=Transport.SSE,
        endpoint="https://stream.wikimedia.org/v2/stream/recentchange",
        docs_url="https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service",
        terms_url="https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use",
        personal_fields=("user", "performer.*"),
    )
    URL = "https://stream.wikimedia.org/v2/stream/recentchange"

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return SseSource(self.DESCRIPTOR, JsonDecoder(), deps.clock, deps.http, self.URL)


FACTORY = WikimediaFactory()
