"""WebSocket push source."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Mapping, Sequence

import websockets

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort
from stream_consumers.ports.outbound.system import ClockPort

Subscription = str | Mapping[str, object] | Sequence[object]


CLOSE_TIMEOUT_S = 1.0
"""How long closing waits for the server's reply. While a server keeps streaming, the client has stopped
reading the network once 16 frames are queued unread (websockets' `max_queue` high-water mark), so the reply
is never read and the close lasts this long; the library default of 10 s made every such run end 10 s late."""


class WebSocketSource(PushEventSource):
    """Connects, sends the subscription messages, then yields every frame.

    `keepalive` is an application-level ping some providers require (sent every
    `keepalive_s`); `replies` answers frames that start with a given prefix
    (IRC ``PING``); `split_lines` turns a frame into one message per line.
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        url: str,
        subscriptions: Sequence[Subscription] = (),
        headers: Mapping[str, str] | None = None,
        keepalive: Subscription | None = None,
        keepalive_s: float = 15.0,
        replies: Mapping[str, str] | None = None,
        split_lines: bool = False,
        open_timeout_s: float = 25.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        self._url = url
        self._subscriptions = tuple(subscriptions)
        self._headers = dict(headers or {})
        self._keepalive = keepalive
        self._keepalive_s = keepalive_s
        self._replies = dict(replies or {})
        self._split_lines = split_lines
        self._open_timeout_s = open_timeout_s

    @staticmethod
    def _wire(message: Subscription) -> str:
        return message if isinstance(message, str) else json.dumps(message)

    async def _subscription_messages(self) -> Sequence[Subscription]:
        """Hook for providers whose subscription must be looked up first."""
        return self._subscriptions

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        async with websockets.connect(
            self._url,
            open_timeout=self._open_timeout_s,
            close_timeout=CLOSE_TIMEOUT_S,
            max_size=2**26,
            additional_headers=self._headers,
        ) as ws:
            for message in await self._subscription_messages():
                await ws.send(self._wire(message))
            last_ping = self._clock.monotonic()
            while True:
                if self._keepalive is not None and self._clock.monotonic() - last_ping >= self._keepalive_s:
                    await ws.send(self._wire(self._keepalive))
                    last_ping = self._clock.monotonic()
                try:
                    frame = await asyncio.wait_for(ws.recv(), self._keepalive_s)
                except TimeoutError:
                    continue
                parts = frame.split("\r\n") if self._split_lines and isinstance(frame, str) else [frame]
                for part in parts:
                    if not part:
                        continue
                    reply = next((r for prefix, r in self._replies.items() if isinstance(part, str) and part.startswith(prefix)), None)
                    if reply is not None:
                        await ws.send(reply)
                        continue
                    yield RawMessage(part)
