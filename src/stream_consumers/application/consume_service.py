"""Consume one source into a sink and measure what arrived."""

from __future__ import annotations

import asyncio

from stream_consumers.domain.errors import MissingCredentialError, UnknownSourceError
from stream_consumers.domain.models import Event, RateBasis, RunReport, RunStatus
from stream_consumers.domain.policy import PersonalDataMasker, attribute_count, median, rate
from stream_consumers.ports.inbound import ConsumeStreamUseCase
from stream_consumers.ports.outbound.outputs import EventSinkPort
from stream_consumers.ports.outbound.providers import SourceRegistryPort
from stream_consumers.ports.outbound.system import ClockPort

ATTRIBUTE_SAMPLE = 1000
"""Attributes are counted on the first events only; counting every event would slow fast streams."""


class ConsumeService(ConsumeStreamUseCase):
    def __init__(self, registry: SourceRegistryPort, clock: ClockPort) -> None:
        self._registry = registry
        self._clock = clock

    async def consume(
        self,
        source_id: str,
        seconds: float,
        sink: EventSinkPort,
        max_events: int | None = None,
        mask: bool = True,
    ) -> RunReport:
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        if max_events is not None and max_events < 1:
            raise ValueError("max_events must be at least 1")
        started_at = self._clock.now()
        try:
            source = self._registry.create(source_id)
        except MissingCredentialError as exc:
            return RunReport(source_id, RunStatus.KEY_PENDING, 0, 0.0, None, RateBasis.UNMEASURED, 0.0, None, started_at, str(exc))
        except UnknownSourceError:
            raise
        except Exception as exc:  # a source that cannot be built is reported, so it cannot stop a whole check or sampling run
            return RunReport(
                source_id, RunStatus.ERROR, 0, 0.0, None, RateBasis.UNMEASURED, 0.0, None, started_at, f"{type(exc).__name__}: {exc}"[:500]
            )
        masker = PersonalDataMasker(source.descriptor.personal_fields) if mask else None
        seconds = max(seconds, source.descriptor.min_window_s)
        start = self._clock.monotonic()
        events = 0
        counts: list[int] = []
        first: float | None = None
        detail = ""
        failed = False
        iterator = source.events()
        try:
            while max_events is None or events < max_events:
                remaining = start + seconds - self._clock.monotonic()
                if remaining <= 0:
                    break
                try:
                    payload = await asyncio.wait_for(anext(iterator), remaining)
                except (TimeoutError, StopAsyncIteration):
                    break
                except Exception as exc:  # a provider failure is a measured result, never a crash
                    failed, detail = True, f"{type(exc).__name__}: {exc}"[:500]
                    break
                if first is None:
                    first = round(self._clock.monotonic() - start, 3)
                if masker is not None:
                    payload = masker.mask(payload)
                # a failing sink (a closed pipe, a full disk) is not the provider's failure: it ends the run
                sink.write(Event(source_id, self._clock.now(), payload))
                events += 1
                if len(counts) < ATTRIBUTE_SAMPLE:
                    counts.append(attribute_count(payload))
                # A source whose next record is always ready never suspends; without this turn it would hold
                # the event loop for its whole window and the sources consumed beside it would get nothing.
                await asyncio.sleep(0)
        finally:
            await iterator.aclose()
        elapsed = round(self._clock.monotonic() - start, 3)
        volume = source.published_volume()
        if volume is not None:
            value = rate(volume.events, volume.period_s)
            basis = RateBasis.PUBLISHED if value is not None else RateBasis.UNMEASURED
        else:
            value, basis = rate(events, elapsed), RateBasis.OBSERVED
        if failed and not events:
            status, value, basis = RunStatus.ERROR, None, RateBasis.UNMEASURED
        else:
            status = RunStatus.OK if events else RunStatus.NO_EVENTS
        return RunReport(source_id, status, events, elapsed, value, basis, median(counts), first, started_at, detail)
