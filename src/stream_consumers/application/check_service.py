"""Check that sources deliver decodable events."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from stream_consumers.domain.models import RunReport
from stream_consumers.ports.inbound import CheckSourcesUseCase, ConsumeStreamUseCase, StopRequestPort
from stream_consumers.ports.outbound.outputs import EventSinkPort, ReportSinkPort


class CheckService(CheckSourcesUseCase):
    def __init__(self, consume: ConsumeStreamUseCase, sink: EventSinkPort, reports: ReportSinkPort, concurrency: int = 16) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._consume = consume
        self._sink = sink
        self._reports = reports
        self._concurrency = concurrency

    async def check(self, source_ids: Sequence[str], seconds: float, *, stop: StopRequestPort) -> Sequence[RunReport]:
        limit = asyncio.Semaphore(self._concurrency)

        async def one(source_id: str) -> RunReport | None:
            async with limit:
                if stop.reason() is not None:
                    return None
                return await self._consume.consume(source_id, seconds, self._sink, mask=False, stop=stop)

        reports = [r for r in await asyncio.gather(*(one(s) for s in source_ids)) if r is not None]
        self._reports.write_check(reports)
        return reports
