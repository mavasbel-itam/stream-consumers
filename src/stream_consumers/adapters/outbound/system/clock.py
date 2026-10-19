"""Time from the operating system."""

from __future__ import annotations

import asyncio
import time

from stream_consumers.ports.outbound.system import ClockPort


class SystemClock(ClockPort):
    def now(self) -> float:
        return time.time()

    def monotonic(self) -> float:
        return time.monotonic()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
