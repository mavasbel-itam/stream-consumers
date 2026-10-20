"""Ctrl+C (SIGINT) and SIGTERM as the operator's stop request.

The first signal asks the running use case to stop: windows end as if their time were up, outputs are
closed and reports written. A second signal quits at once, as an operator pressing Ctrl+C twice expects:
the signal's default action ends the process, so the shell sees a process killed by that signal."""

from __future__ import annotations

import asyncio
import os
import signal
import time
from collections.abc import Callable, Sequence
from types import FrameType
from typing import TextIO

from stream_consumers.ports.inbound import StopRequestPort

STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)
REPEAT_WINDOW_S = 1.0
"""A signal this soon after the first one is the same stop delivered twice, not a second request: `timeout`
signals its child and then its whole process group, and `uv run` passes the first one on, so one stop arrived
twice 0.05 ms apart (measured 2026-10-20). A person pressing Ctrl+C again does so later."""


def exit_code(reason: str) -> int:
    """The exit code a shell reports for a process ended by this signal: 128 + its number (130, 143)."""
    return 128 + signal.Signals[reason].value


class SignalStopRequest(StopRequestPort):
    """Turns the first SIGINT or SIGTERM into a stop request; a second one, at least `REPEAT_WINDOW_S` later,
    ends the process at once.

    Create it inside the running event loop and `close()` it when the run ends, which puts the previous
    handlers back when no stop was requested. A signal ignored when the program started (a job started
    with `&` by a non-interactive shell ignores SIGINT) stays ignored."""

    def __init__(
        self,
        err: TextIO,
        signals: Sequence[signal.Signals] = STOP_SIGNALS,
        kill: Callable[[int, int], object] = os.kill,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._err = err
        self._kill = kill
        self._monotonic = monotonic
        self._first_at = 0.0
        self._loop = asyncio.get_running_loop()
        self._requested = asyncio.Event()
        self._reason: str | None = None
        self._signalled = False
        self._previous: dict[signal.Signals, Callable[[int, FrameType | None], object] | int | None] = {}
        for sig in signals:
            current = signal.getsignal(sig)
            if current is signal.SIG_IGN:
                continue
            self._previous[sig] = current
            signal.signal(sig, self._on_signal)

    def reason(self) -> str | None:
        return self._reason

    async def wait(self) -> str:
        await self._requested.wait()
        assert self._reason is not None
        return self._reason

    def close(self) -> None:
        """Put the previous handlers back, unless a stop was requested: then this handler stays until the process
        ends, because a stop can be over in under a millisecond, before the repeat of the same stop arrives."""
        if not self._signalled:
            for sig, handler in self._previous.items():
                signal.signal(sig, handler)
        self._previous.clear()

    def _on_signal(self, signum: int, frame: FrameType | None) -> None:
        name = signal.Signals(signum).name
        if self._signalled:  # a process ending by this is not recorded by coverage
            if self._monotonic() - self._first_at < REPEAT_WINDOW_S:
                return  # the same stop delivered twice
            # runs between two bytecodes of whatever the program was doing: write with one system call
            os.write(2, f"stopped immediately by a second {name}; outputs may be incomplete\n".encode())
            signal.signal(signum, signal.SIG_DFL)
            self._kill(os.getpid(), signum)
            return
        self._signalled = True
        self._first_at = self._monotonic()
        # the request takes effect in the event loop, after its announcement, so every line the run writes
        # afterwards (reports, summaries) comes after it
        self._loop.call_soon_threadsafe(self._request, name)

    def _request(self, name: str) -> None:
        self._err.write(f"stopping ({name}): ending the run, closing outputs and writing reports; a second signal (Ctrl+C) quits at once\n")
        self._err.flush()
        self._reason = name
        self._requested.set()
