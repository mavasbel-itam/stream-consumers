"""HTTP polling sources (through the HTTP client port)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.transports.base import PollEventSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound import ClockPort, DecoderPort, HttpClientPort, HttpResponse


class HttpPollSource(PollEventSource):
    """GETs every URL in `urls` (or POSTs `json_body` to them) once per poll.

    A non-200 answer is a failed poll, retried with back-off.
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        urls: Sequence[str],
        interval_s: float,
        detector: ChangeDetector | None = None,
        headers: Mapping[str, str] | None = None,
        json_body: object | None = None,
        emit_initial: bool = True,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, interval_s, detector, emit_initial, backoff)
        if not urls:
            raise ValueError("urls must not be empty")
        self._http = http
        self._urls = tuple(urls)
        self._headers = dict(headers or {})
        self._json_body = json_body

    @staticmethod
    def ok(response: HttpResponse, url: str) -> bytes:
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {url}: {response.body[:200]!r}")
        return response.body

    async def _request(self, url: str) -> HttpResponse:
        if self._json_body is not None:
            return await self._http.post_json(url, self._json_body, self._headers)
        return await self._http.get(url, self._headers)

    async def _urls_for_poll(self) -> Sequence[str]:
        """Hook for providers whose URL depends on the previous poll (cursors, sequence numbers)."""
        return self._urls

    async def _fetch(self) -> Sequence[RawMessage]:
        out = []
        for url in await self._urls_for_poll():
            out.append(RawMessage(self.ok(await self._request(url), url), {"url": url}))
        return out
