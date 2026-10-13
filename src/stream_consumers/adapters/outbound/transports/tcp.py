"""Plain TCP push sources: newline-delimited text and fixed-size binary records."""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from collections.abc import AsyncGenerator, Sequence

from stream_consumers.adapters.outbound.transports.base import PushEventSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound import ClockPort, DecoderPort


class TcpSource(PushEventSource):
    """Opens a TCP connection, sends `greeting` lines, runs `_handshake`, then reads `_frames()`."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        host: str,
        port: int,
        greeting: Sequence[str] = (),
        connect_timeout_s: float = 25.0,
        silence_s: float = 120.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        self._host = host
        self._port = port
        self._greeting = tuple(greeting)
        self._connect_timeout_s = connect_timeout_s
        self._silence_s = silence_s

    async def _open(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(self._host, self._port), self._connect_timeout_s)
        try:
            for line in self._greeting:
                writer.write((line + "\r\n").encode())
            await writer.drain()
            await self._handshake(reader, writer)
        except BaseException:
            writer.close()
            raise
        return reader, writer

    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Hook for protocols that negotiate before data flows; the connection is closed if it raises."""

    async def _timed(self, read: asyncio.Future[bytes] | object) -> bytes:
        try:
            return await asyncio.wait_for(read, self._silence_s)  # type: ignore[arg-type]
        except TimeoutError as exc:
            raise TransportError(f"no data for {self._silence_s} s from {self._host}:{self._port}") from exc

    @abstractmethod
    def _frames(self, reader: asyncio.StreamReader) -> AsyncGenerator[RawMessage]: ...

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        reader, writer = await self._open()
        frames = self._frames(reader)
        try:
            async for frame in frames:
                yield frame
        finally:
            await frames.aclose()
            writer.close()


class TcpLineSource(TcpSource):
    """One message per line; the connection ending is reported as a failure."""

    async def _frames(self, reader: asyncio.StreamReader) -> AsyncGenerator[RawMessage]:
        while True:
            line = await self._timed(reader.readline())
            if not line:
                raise TransportError(f"{self._host}:{self._port} closed the connection")
            yield RawMessage(line.decode("utf-8", "replace").rstrip("\r\n"))


class TcpRecordSource(TcpSource):
    """Fixed-size binary records of `record_size` bytes."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        host: str,
        port: int,
        record_size: int,
        greeting: Sequence[str] = (),
        connect_timeout_s: float = 25.0,
        silence_s: float = 120.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, host, port, greeting, connect_timeout_s, silence_s, backoff)
        if record_size < 1:
            raise ValueError("record_size must be positive")
        self._record_size = record_size

    async def _frames(self, reader: asyncio.StreamReader) -> AsyncGenerator[RawMessage]:
        while True:
            try:
                record = await self._timed(reader.readexactly(self._record_size))
            except asyncio.IncompleteReadError as exc:
                raise TransportError(f"{self._host}:{self._port} closed the connection") from exc
            yield RawMessage(record)
