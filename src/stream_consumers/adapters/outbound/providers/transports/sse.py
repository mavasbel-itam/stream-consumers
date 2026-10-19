"""Server-Sent Events push source (read through the HTTP client port)."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort, HttpClientPort
from stream_consumers.ports.outbound.system import ClockPort


class SseSource(PushEventSource):
    """Yields one message per SSE event (`data:` lines joined); the event type is in
    the message attribute ``event``. Events whose type is not in `event_types` are
    skipped when `event_types` is given."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        url: str,
        headers: Mapping[str, str] | None = None,
        event_types: frozenset[str] | None = None,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        self._http = http
        self._url = url
        self._headers = {"Accept": "text/event-stream", **(headers or {})}
        self._event_types = event_types

    def _complete(self, event: str, data: list[str]) -> RawMessage | None:
        if not data or (self._event_types is not None and event not in self._event_types):
            return None
        return RawMessage("\n".join(data), {"event": event})

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        buffer = b""
        event, data = "message", []
        async for chunk in self._http.stream(self._url, self._headers):
            buffer += chunk
            *lines, buffer = buffer.split(b"\n")
            for raw in lines:
                line = raw.decode("utf-8", "replace").rstrip("\r")
                if not line:
                    message = self._complete(event, data)
                    event, data = "message", []
                    if message is not None:
                        yield message
                elif line.startswith(":"):
                    continue
                else:
                    name, _, value = line.partition(":")
                    value = value[1:] if value.startswith(" ") else value
                    if name == "event":
                        event = value
                    elif name == "data":
                        data.append(value)
