"""ZeroMQ SUB push source."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import zmq
import zmq.asyncio

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort
from stream_consumers.ports.outbound.system import ClockPort


class ZmqSubSource(PushEventSource):
    """Multipart messages: the first frame is the envelope (attribute ``envelope``), the last is the body.

    ZeroMQ reconnects by itself and never reports a dead peer, so a silence longer
    than `silence_s` is treated as a broken connection.
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        endpoint: str,
        prefix: bytes = b"",
        silence_s: float = 120.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        self._endpoint = endpoint
        self._prefix = prefix
        self._silence_ms = int(silence_s * 1000)

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.SUB)
        try:
            socket.setsockopt(zmq.RCVTIMEO, self._silence_ms)
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(self._endpoint)
            socket.setsockopt(zmq.SUBSCRIBE, self._prefix)
            while True:
                try:
                    parts = await socket.recv_multipart()
                except zmq.Again as exc:
                    raise TransportError(f"no message for {self._silence_ms} ms from {self._endpoint}") from exc
                yield RawMessage(parts[-1], {"envelope": parts[0].decode("utf-8", "replace")})
        finally:
            socket.close()
            context.term()
