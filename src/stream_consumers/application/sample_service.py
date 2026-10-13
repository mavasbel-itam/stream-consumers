"""Repeated measurement rounds on wall-clock targets."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from stream_consumers.domain.models import RunReport, SamplingRound
from stream_consumers.ports.inbound import ConsumeStreamUseCase, SampleSourcesUseCase
from stream_consumers.ports.outbound import ClockPort, EventSinkPort, ReportSinkPort

WAIT_STEP_S = 30.0
"""Waits are split into short sleeps so a round missed while the host slept starts as soon as it wakes."""


class SampleService(SampleSourcesUseCase):
    def __init__(
        self,
        consume: ConsumeStreamUseCase,
        sink: EventSinkPort,
        reports: ReportSinkPort,
        clock: ClockPort,
        concurrency: int = 64,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._consume = consume
        self._sink = sink
        self._reports = reports
        self._clock = clock
        self._concurrency = concurrency

    async def _wait_until(self, target: float) -> None:
        while (left := target - self._clock.now()) > 0:
            await self._clock.sleep(min(WAIT_STEP_S, left))

    async def sample(self, source_ids: Sequence[str], rounds: int, interval_s: float, window_s: float) -> Sequence[SamplingRound]:
        if rounds < 1:
            raise ValueError("rounds must be at least 1")
        if interval_s <= 0 or window_s <= 0:
            raise ValueError("interval_s and window_s must be positive")
        limit = asyncio.Semaphore(self._concurrency)

        async def one(source_id: str) -> RunReport:
            async with limit:
                return await self._consume.consume(source_id, window_s, self._sink, mask=False)

        start = self._clock.now()
        done = []
        for number in range(1, rounds + 1):
            target = start + (number - 1) * interval_s
            await self._wait_until(target)
            sampling_round = SamplingRound(number, target, tuple(await asyncio.gather(*(one(s) for s in source_ids))))
            self._reports.write_round(sampling_round)
            done.append(sampling_round)
        return done
