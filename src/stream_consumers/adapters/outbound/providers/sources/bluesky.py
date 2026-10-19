"""Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class BlueskyDecoder(JsonDecoder):
    """Jetstream messages; `commit` messages are repository writes (posts, likes, follows, reposts...)."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        return [document] if isinstance(document, Mapping) and document.get("kind") == "commit" else []


class BlueskyFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="bluesky",
        name="Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts)",
        category="Games, media & social",
        provider="Bluesky Social PBC",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://jetstream2.us-east.bsky.network/subscribe",
        docs_url="https://github.com/bluesky-social/jetstream",
        terms_url="https://bsky.social/about/support/tos",
        personal_fields=(
            "did",
            "commit.record.text",
            "commit.record.subject*",
            "commit.record.reply.*",
            "commit.record.displayName",
            "commit.record.description",
            "commit.record.embed*",
            "commit.record.facets",
        ),
    )
    URL = "wss://jetstream2.us-east.bsky.network/subscribe"
    SUBSCRIPTIONS: tuple[object, ...] = ()

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return WebSocketSource(
            self.DESCRIPTOR, BlueskyDecoder(), deps.clock, self.URL, self.SUBSCRIPTIONS, headers={"User-Agent": deps.user_agent}
        )


FACTORY = BlueskyFactory()
