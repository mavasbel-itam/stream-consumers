"""Repeated measurement rounds on wall-clock targets."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from stream_consumers.domain.models import RunReport, SamplingRound, Verdict
from stream_consumers.domain.policy import reports_by_source, verdict
from stream_consumers.ports.inbound import ConsumeStreamUseCase, SampleSourcesUseCase, StopRequestPort
from stream_consumers.ports.outbound.outputs import EventSinkPort, ReportSinkPort
from stream_consumers.ports.outbound.system import ClockPort

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

    async def _wait_until(self, target: float, stop: StopRequestPort) -> None:
        """Sleep until `target`, or until a stop is requested."""
        while (left := target - self._clock.now()) > 0:
            if stop.reason() is not None:
                return
            sleeping = asyncio.ensure_future(self._clock.sleep(min(WAIT_STEP_S, left)))
            stopping = asyncio.ensure_future(stop.wait())
            try:
                await asyncio.wait((sleeping, stopping), return_when=asyncio.FIRST_COMPLETED)
            finally:
                sleeping.cancel()
                stopping.cancel()

    async def sample(
        self,
        source_ids: Sequence[str],
        rounds: int,
        interval_s: float,
        window_s: float,
        prior: Sequence[SamplingRound] = (),
        stop_when_settled: bool = False,
        *,
        stop: StopRequestPort,
    ) -> Sequence[SamplingRound]:
        if rounds < 1:
            raise ValueError("rounds must be at least 1")
        if interval_s <= 0 or window_s <= 0:
            raise ValueError("interval_s and window_s must be positive")
        limit = asyncio.Semaphore(self._concurrency)
        history = reports_by_source(prior)

        async def one(source_id: str) -> RunReport:
            async with limit:
                return await self._consume.consume(source_id, window_s, self._sink, mask=False, stop=stop)

        def still_open() -> list[str]:
            if not stop_when_settled:
                return list(source_ids)
            return [s for s in source_ids if verdict(history.get(s, []), rounds) is Verdict.OPEN]

        start = self._clock.now()
        done: list[SamplingRound] = []
        for offset in range(rounds - len(prior)):
            active = still_open()
            if not active:
                break
            target = start + offset * interval_s
            await self._wait_until(target, stop)
            if stop.reason() is not None:
                break
            measured = tuple(await asyncio.gather(*(one(s) for s in active)))
            if stop.reason() is not None:
                break  # the windows of this round were cut short: recording it would bias the median
            sampling_round = SamplingRound(len(prior) + offset + 1, target, measured)
            self._reports.write_round(sampling_round)
            done.append(sampling_round)
            for report in measured:
                history.setdefault(report.source_id, []).append(report)
        return done
