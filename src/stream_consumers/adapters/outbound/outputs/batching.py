"""The base of the outputs that write in batches (databases, files written through a driver)."""

from __future__ import annotations

import asyncio
import contextlib
from abc import abstractmethod
from collections.abc import Sequence

from stream_consumers.adapters.outbound.outputs.sinks import BaseEventSink
from stream_consumers.domain.errors import OutputError
from stream_consumers.domain.models import Event
from stream_consumers.ports.outbound.system import ClockPort


class BatchingEventSink(BaseEventSink):
    """Hands events to `_flush` in batches: when `batch_size` events wait, when the oldest has waited
    `max_delay_s` (checked on every write and by a timer while the sink is open), and on `close`.

    A failure to connect or to flush is raised as an `OutputError` naming `label` (the destination
    without its password); a failure of a timed flush is raised by the next `write` or by `close`,
    never lost.
    """

    def __init__(self, clock: ClockPort, label: str, batch_size: int = 500, max_delay_s: float = 1.0) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if max_delay_s <= 0:
            raise ValueError("max_delay_s must be positive")
        self._clock = clock
        self._label = label
        self._batch_size = batch_size
        self._max_delay_s = max_delay_s
        self._buffer: list[Event] = []
        self._oldest: float | None = None
        self._lock = asyncio.Lock()
        self._timer: asyncio.Task[None] | None = None
        self._failure: BaseException | None = None

    @abstractmethod
    async def _connect(self) -> None: ...

    @abstractmethod
    async def _flush(self, events: Sequence[Event]) -> None: ...

    @abstractmethod
    async def _disconnect(self) -> None: ...

    async def open(self) -> None:
        try:
            await self._connect()
        except Exception as exc:
            raise OutputError(self._label, exc) from exc
        self._timer = asyncio.create_task(self._tick())

    def _due(self) -> bool:
        return self._oldest is not None and self._clock.monotonic() - self._oldest >= self._max_delay_s

    async def _tick(self) -> None:
        while True:
            await self._clock.sleep(self._max_delay_s)
            if self._due():
                try:
                    await self._flush_buffer()
                except Exception as exc:  # kept for the next write or close, which raise it
                    self._failure = exc
                    return

    async def _flush_buffer(self) -> None:
        async with self._lock:
            batch, self._buffer, self._oldest = self._buffer, [], None
            if batch:
                try:
                    await self._flush(batch)
                except Exception as exc:
                    raise OutputError(self._label, exc) from exc

    def _raise_failure(self) -> None:
        if self._failure is not None:
            raise self._failure

    async def write(self, event: Event) -> None:
        self._raise_failure()
        if not self._buffer:
            self._oldest = self._clock.monotonic()
        self._buffer.append(event)
        if len(self._buffer) >= self._batch_size or self._due():
            await self._flush_buffer()

    async def close(self) -> None:
        try:
            if self._timer is not None:
                async with self._lock:  # lets a timed flush that is under way finish first
                    self._timer.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._timer
            self._raise_failure()
            await self._flush_buffer()
        finally:
            await self._disconnect()
