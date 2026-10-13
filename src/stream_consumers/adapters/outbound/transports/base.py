"""Event-source class tree.

EventSourcePort
└── BaseEventSource                descriptor, clock, retry with back-off
    ├── DecodingEventSource        adds the decoder for the provider's wire format
    │   ├── PushEventSource        the provider pushes messages over one connection
    │   ├── PollEventSource        snapshots fetched on an interval, diffed into changes
    │   └── FileDropSource         the provider publishes one file per period
    └── MergedEventSource          several sources read concurrently as one
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import PublishedVolume, RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound import ClockPort, DecoderPort, EventSourcePort

Record = Mapping[str, object]
T = TypeVar("T")

MERGED_CLOSE_GRACE_S = 5.0


def raise_if_cancelling(error: BaseException) -> None:
    """Re-raise as cancellation when the current task has been asked to stop.

    Some client libraries turn a CancelledError into another exception (websockets
    15–17 raises AssertionError when recv() is cancelled while reassembling a
    fragmented message and another frame is already queued). Without this check a
    retry loop would take that error for a provider failure, reconnect, and the
    task would never stop.
    """
    task = asyncio.current_task()
    if task is not None and task.cancelling():
        raise asyncio.CancelledError() from error


class BaseEventSource(EventSourcePort):
    def __init__(self, descriptor: SourceDescriptor, clock: ClockPort, backoff: Backoff | None = None) -> None:
        self._descriptor = descriptor
        self._clock = clock
        self._backoff = backoff or Backoff()

    @property
    def descriptor(self) -> SourceDescriptor:
        return self._descriptor

    def published_volume(self) -> PublishedVolume | None:
        return None

    async def _pause_before_retry(self, attempt: int, error: BaseException) -> None:
        """Sleep before retry number `attempt`, or raise when the back-off allows no more."""
        if not self._backoff.allows(attempt):
            raise TransportError(f"{self._descriptor.id}: gave up after {attempt - 1} retries: {error}") from error
        await self._clock.sleep(self._backoff.delay(attempt))

    async def _retrying(self, operation: Callable[[], Awaitable[T]]) -> T:
        attempt = 0
        while True:
            try:
                return await operation()
            except Exception as exc:
                raise_if_cancelling(exc)
                attempt += 1
                await self._pause_before_retry(attempt, exc)


class DecodingEventSource(BaseEventSource):
    def __init__(self, descriptor: SourceDescriptor, decoder: DecoderPort, clock: ClockPort, backoff: Backoff | None = None) -> None:
        super().__init__(descriptor, clock, backoff)
        self._decoder = decoder


class PushEventSource(DecodingEventSource):
    """Reads `_connect()` and reconnects with back-off when it fails or ends.

    The attempt counter resets whenever a message arrives, so only consecutive
    failures count toward giving up.
    """

    @abstractmethod
    def _connect(self) -> AsyncGenerator[RawMessage]:
        """Open one connection and yield its messages until it closes."""

    async def events(self) -> AsyncGenerator[Record]:
        attempt = 0
        while True:
            stream = self._connect()
            error: BaseException = TransportError(f"{self._descriptor.id}: connection closed by the provider")
            try:
                async for message in stream:
                    attempt = 0
                    for record in self._decoder.decode(message):
                        yield record
            except Exception as exc:
                raise_if_cancelling(exc)
                error = exc
            finally:
                await stream.aclose()
            attempt += 1
            await self._pause_before_retry(attempt, error)


class PollEventSource(DecodingEventSource):
    """Fetches a snapshot every `interval_s`; with a ChangeDetector only new or changed records are events.

    The first snapshot is yielded when `emit_initial` is true but it is never
    counted as change: the published volume is the changes seen in later polls
    over the time between the first and the last poll.
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        interval_s: float,
        detector: ChangeDetector | None = None,
        emit_initial: bool = True,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        if interval_s <= 0:
            raise ValueError("interval_s must be positive")
        self._interval_s = interval_s
        self._detector = detector
        self._emit_initial = emit_initial
        self._polls = 0
        self._changes = 0
        self._first_poll_at: float | None = None
        self._last_poll_at: float | None = None
        self._volume: PublishedVolume | None = None

    @abstractmethod
    async def _fetch(self) -> Sequence[RawMessage]:
        """One snapshot; raise to have the poll retried with back-off."""

    async def _snapshot_volume(self, records: Sequence[Record]) -> PublishedVolume | None:
        """Hook for providers whose snapshot states its own period (e.g. "the last hour")."""
        return None

    def _decode_all(self, messages: Sequence[RawMessage]) -> list[Record]:
        return [record for message in messages for record in self._decoder.decode(message)]

    def published_volume(self) -> PublishedVolume | None:
        if self._volume is not None:
            return self._volume
        if self._detector is None:
            return None
        span = (self._last_poll_at or 0.0) - (self._first_poll_at or 0.0)
        return PublishedVolume(self._changes, span)

    async def events(self) -> AsyncGenerator[Record]:
        while True:
            started = self._clock.monotonic()
            records = await self._retrying(self._poll_once)
            for record in records:
                yield record
            await self._clock.sleep(max(0.0, self._interval_s - (self._clock.monotonic() - started)))

    async def _poll_once(self) -> list[Record]:
        records = self._decode_all(await self._fetch())
        self._polls += 1
        now = self._clock.monotonic()
        volume = await self._snapshot_volume(records)
        if volume is not None:
            self._volume = volume
        if self._detector is None:
            return records
        changed = list(self._detector.changed(records))
        if self._polls == 1:
            self._first_poll_at = now
            return changed if self._emit_initial else []
        self._last_poll_at = now
        self._changes += len(changed)
        return changed


@dataclass(frozen=True)
class FileLocation:
    """One published file: `key` identifies it, `period_s` is the time it covers."""

    key: str
    url: str
    period_s: float


class FileDropSource(DecodingEventSource):
    """Provider publishes one file per period. Each new file is read once; its record
    count over its period is the published volume."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        interval_s: float,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        if interval_s <= 0:
            raise ValueError("interval_s must be positive")
        self._interval_s = interval_s
        self._volume: PublishedVolume | None = None

    def published_volume(self) -> PublishedVolume | None:
        return self._volume or PublishedVolume(0, 0.0)

    @abstractmethod
    async def _locate(self) -> FileLocation:
        """The newest complete file."""

    @abstractmethod
    def _read(self, location: FileLocation) -> AsyncGenerator[Record]:
        """The records of one file."""

    async def events(self) -> AsyncGenerator[Record]:
        last_key: str | None = None
        while True:
            started = self._clock.monotonic()
            location = await self._retrying(self._locate)
            if location.key != last_key:
                count = 0
                reader = self._read(location)
                try:
                    async for record in reader:
                        count += 1
                        yield record
                finally:
                    await reader.aclose()
                self._volume = PublishedVolume(count, location.period_s)
                last_key = location.key
            await self._clock.sleep(max(0.0, self._interval_s - (self._clock.monotonic() - started)))


class MergedEventSource(BaseEventSource):
    """Reads several child sources concurrently; their published volumes are summed.

    Fails only when every child has failed; ends when every child has ended.
    Subclasses that discover their children at run time override `_resolve_children`.
    """

    def __init__(
        self, descriptor: SourceDescriptor, children: Sequence[EventSourcePort], clock: ClockPort, backoff: Backoff | None = None
    ) -> None:
        super().__init__(descriptor, clock, backoff)
        self._children = tuple(children)

    async def _resolve_children(self) -> Sequence[EventSourcePort]:
        return self._children

    def published_volume(self) -> PublishedVolume | None:
        known = [v for v in (c.published_volume() for c in self._children) if v is not None]
        if not known:
            return None
        return PublishedVolume(sum(v.events for v in known), max(v.period_s for v in known))

    async def events(self) -> AsyncGenerator[Record]:
        self._children = tuple(await self._resolve_children())
        if not self._children:
            raise TransportError(f"{self._descriptor.id}: no child sources")
        queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue(maxsize=10_000)

        async def pump(child: EventSourcePort) -> None:
            stream = child.events()
            try:
                async for record in stream:
                    await queue.put(("record", record))
                await queue.put(("done", None))
            except Exception as exc:
                await queue.put(("error", exc))
            finally:
                await stream.aclose()

        tasks = [asyncio.create_task(pump(c)) for c in self._children]
        finished = failed = 0
        last_error: BaseException | None = None
        try:
            while finished + failed < len(tasks):
                kind, item = await queue.get()
                if kind == "record":
                    yield item  # type: ignore[misc]
                elif kind == "done":
                    finished += 1
                else:
                    failed += 1
                    last_error = item  # type: ignore[assignment]
            if failed == len(tasks):
                raise TransportError(f"{self._descriptor.id}: every child source failed; last: {last_error}") from last_error
        finally:
            pending: set[asyncio.Task[None]] = set(tasks)
            while pending:
                for task in pending:
                    task.cancel()
                _, pending = await asyncio.wait(pending, timeout=MERGED_CLOSE_GRACE_S)
