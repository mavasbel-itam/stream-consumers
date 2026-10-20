"""Keep a bounded, masked sample of events per source and describe their fields."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence

from stream_consumers.domain.models import Event, SourceProfile
from stream_consumers.domain.policy import PersonalDataMasker, profile_sample
from stream_consumers.ports.inbound import ConsumeStreamUseCase, ProfileSourcesUseCase, StopRequestPort
from stream_consumers.ports.outbound.outputs import EventSinkFactoryPort, EventSinkPort, ReportSinkPort
from stream_consumers.ports.outbound.providers import SourceRegistryPort


class CollectingSink(EventSinkPort):
    """Keeps the real payloads for the field statistics and writes masked copies through to another sink."""

    def __init__(self, inner: EventSinkPort, masker: PersonalDataMasker) -> None:
        self._inner = inner
        self._masker = masker
        self.payloads: list[Mapping[str, object]] = []

    async def open(self) -> None:
        await self._inner.open()

    async def write(self, event: Event) -> None:
        self.payloads.append(event.payload)
        await self._inner.write(Event(event.source_id, event.received_at, self._masker.mask(event.payload)))

    async def close(self) -> None:
        await self._inner.close()


class ProfileService(ProfileSourcesUseCase):
    def __init__(
        self,
        consume: ConsumeStreamUseCase,
        sinks: EventSinkFactoryPort,
        reports: ReportSinkPort,
        registry: SourceRegistryPort,
        concurrency: int = 64,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._consume = consume
        self._sinks = sinks
        self._reports = reports
        self._registry = registry
        self._concurrency = concurrency

    async def profile(
        self, source_ids: Sequence[str], max_events: int, seconds: float, *, stop: StopRequestPort
    ) -> Sequence[SourceProfile]:
        limit = asyncio.Semaphore(self._concurrency)

        async def one(source_id: str) -> SourceProfile | None:
            masker = PersonalDataMasker(self._registry.descriptor(source_id).personal_fields)
            async with limit:
                if stop.reason() is not None:
                    return None
                sink = CollectingSink(self._sinks.create(source_id), masker)
                await sink.open()
                try:
                    run = await self._consume.consume(source_id, seconds, sink, max_events=max_events, mask=False, stop=stop)
                finally:
                    await sink.close()
            return profile_sample(run, sink.payloads, masker)

        profiles = [p for p in await asyncio.gather(*(one(s) for s in source_ids)) if p is not None]
        self._reports.write_profiles(profiles)
        return profiles
