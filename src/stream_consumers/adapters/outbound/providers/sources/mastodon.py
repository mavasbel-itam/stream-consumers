"""Mastodon federated public timeline over server-sent events (free user account token)."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.sse import SseSource
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, Setting, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort

EVENTS = ("update", "status.update", "delete")


class MastodonStreamDecoder(BaseDecoder):
    """`update` / `status.update` carry a Status as JSON text; `delete` carries the bare status id."""

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        event = message.attributes.get("event", "")
        text = self.text(message)
        if event == "delete":
            return [{"event_type": event, "id": text.strip()}]
        if event not in EVENTS:
            return []
        try:
            status = json.loads(text)
        except ValueError as exc:
            raise DecodeError(f"invalid JSON in {event}: {exc}") from exc
        return [dict(status, event_type=event)] if isinstance(status, Mapping) else []


class MastodonSource(SseSource):
    """Finds the streaming host in the instance's `configuration.urls.streaming` (GET /api/v2/instance,
    public) before the first connection, as the streaming API documentation asks clients to do."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        instance: str,
        token: str,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, http, "", {"Authorization": f"Bearer {token}"}, frozenset(EVENTS), backoff)
        self._instance = instance

    async def _streaming_url(self) -> str:
        url = f"https://{self._instance}/api/v2/instance"
        response = await self._http.get(url)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {url}")
        try:
            streaming = json.loads(response.body)["configuration"]["urls"]["streaming"]
        except (ValueError, KeyError, TypeError) as exc:
            raise TransportError(f"{url} has no configuration.urls.streaming") from exc
        base = str(streaming).replace("wss://", "https://", 1).replace("ws://", "http://", 1).rstrip("/")
        return f"{base}/api/v1/streaming/public"

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        if not self._url:
            self._url = await self._streaming_url()
        async for message in super()._connect():
            yield message


class MastodonFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="mastodon",
        name="Mastodon federated public timeline (statuses, edits, deletions)",
        category="Games, media & social",
        provider="Mastodon (default instance social.vivaldi.net, funded by Vivaldi Technologies)",
        group=Group.FREE_KEY,
        delivery=Delivery.PUSH,
        transport=Transport.SSE,
        endpoint="https://social.vivaldi.net/api/v1/streaming/public",
        docs_url="https://docs.joinmastodon.org/methods/streaming/",
        terms_url="https://social.vivaldi.net/terms-of-service",
        credential=Credential(
            ("MASTODON_ACCESS_TOKEN",),
            "https://social.vivaldi.net/auth/sign_up",
            how_to_get=(
                "A user account on the instance, then a user access token with scope read:statuses (OAuth flow: "
                "https://docs.joinmastodon.org/client/token/; the web interface's Preferences → Development page is "
                "not described in the official docs). Since Mastodon 4.2 app-only tokens are refused."
            ),
        ),
        settings=(
            Setting(
                "MASTODON_INSTANCE",
                "social.vivaldi.net",
                "Host name of the Mastodon instance whose federated timeline is read; it must allow live feeds and issue the token.",
            ),
        ),
        personal_fields=(
            "account.*",
            "content",
            "text",
            "spoiler_text",
            "uri",
            "url",
            "mentions.*",
            "in_reply_to_account_id",
            "media_attachments.*",
            "card.*",
            "poll.*",
            "reblog.*",
            "application.*",
            "quote.*",
        ),
        notes=(
            "Statuses are written by people: account names, content and links are personal data and are masked in "
            "stored samples. The token is valid only on the instance that issued it. social.vivaldi.net allows live "
            "feeds of local and remote posts (mastodon.social has them disabled); mastodon.world was measured as a "
            "second option. The consumer only reads."
        ),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        token = (credentials or {})["MASTODON_ACCESS_TOKEN"]
        return MastodonSource(
            self.DESCRIPTOR, MastodonStreamDecoder(), deps.clock, deps.http, self.setting(deps, "MASTODON_INSTANCE"), token
        )


FACTORY = MastodonFactory()
