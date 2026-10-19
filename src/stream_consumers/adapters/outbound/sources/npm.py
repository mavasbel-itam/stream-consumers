"""npm registry replication changes."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.domain.errors import DecodeError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class NpmChangesDecoder(JsonDecoder):
    """`_changes` answers: every item of `results` is one changed package document."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        results = document.get("results") if isinstance(document, Mapping) else None
        return [r for r in results if isinstance(r, Mapping)] if isinstance(results, list) else []


class NpmChangesSource(HttpPollSource):
    """Follows the registry changes feed: starts at the current `update_seq`, then asks for changes `since`
    the last sequence received."""

    ROOT = "https://replicate.npmjs.com/registry/"
    CHANGES = "https://replicate.npmjs.com/registry/_changes?since={since}&limit=10000"

    _since: int | None = None

    async def _fetch(self) -> Sequence[RawMessage]:
        if self._since is None:
            root = json.loads(self.ok(await self._http.get(self.ROOT), self.ROOT))
            self._since = int(str(root["update_seq"]).split("-")[0])
        url = self.CHANGES.format(since=self._since)
        body = self.ok(await self._http.get(url), url)
        try:
            self._since = int(str(json.loads(body)["last_seq"]).split("-")[0])
        except (ValueError, KeyError) as exc:
            raise DecodeError(f"npm changes answer without last_seq: {exc}") from exc
        return [RawMessage(body, {"url": url})]


class NpmFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="npm",
        name="npm registry replication changes",
        category="Internet & software",
        provider="npm, Inc. (GitHub)",
        group=Group.LOW_RATE,
        delivery=Delivery.POLL,
        transport=Transport.HTTP,
        endpoint="https://replicate.npmjs.com/registry/_changes",
        docs_url="https://github.com/npm/registry-follower-tutorial",
        terms_url="https://docs.npmjs.com/policies/open-source-terms",
        min_interval_s=5.0,
        notes="Changes feed followed every 5 s. The feed returns each changed package once per request, so several updates of one package between polls count once.",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return NpmChangesSource(self.DESCRIPTOR, NpmChangesDecoder(), deps.clock, deps.http, [NpmChangesSource.ROOT], 5.0)


FACTORY = NpmFactory()
