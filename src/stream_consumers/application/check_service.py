"""Check that sources deliver decodable events."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from stream_consumers.domain.models import RunReport
from stream_consumers.ports.inbound import CheckSourcesUseCase, ConsumeStreamUseCase
from stream_consumers.ports.outbound import EventSinkPort, ReportSinkPort


class CheckService(CheckSourcesUseCase):
    def __init__(self, consume: ConsumeStreamUseCase, sink: EventSinkPort, reports: ReportSinkPort, concurrency: int = 16) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._consume = consume
        self._sink = sink
        self._reports = reports
        self._concurrency = concurrency

    async def check(self, source_ids: Sequence[str], seconds: float) -> Sequence[RunReport]:
        limit = asyncio.Semaphore(self._concurrency)

        async def one(source_id: str) -> RunReport:
            async with limit:
                return await self._consume.consume(source_id, seconds, self._sink, mask=False)

        reports = list(await asyncio.gather(*(one(s) for s in source_ids)))
        self._reports.write_check(reports)
        return reports
