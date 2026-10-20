"""Ctrl+C and SIGTERM as a stop request, with real signals sent to this process."""

from __future__ import annotations

import asyncio
import io
import os
import signal
from collections.abc import Iterator

import pytest

from stream_consumers.adapters.inbound.signals import REPEAT_WINDOW_S, STOP_SIGNALS, SignalStopRequest, exit_code
from stream_consumers.ports.inbound import StopRequestPort


@pytest.fixture(autouse=True)
def restore_handlers() -> Iterator[None]:
    """Each test starts with the handlers a program started from a terminal has, whatever the test run
    inherited (a run started with `&` or `nohup` from a script has SIGINT ignored), and puts them back."""
    saved = {sig: signal.getsignal(sig) for sig in STOP_SIGNALS}
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    yield
    for sig, handler in saved.items():
        signal.signal(sig, handler)


async def deliver(sig: signal.Signals) -> None:
    os.kill(os.getpid(), sig)
    for _ in range(3):  # the handler runs at the next bytecode; its announcement at the next loop turn
        await asyncio.sleep(0)


def test_exit_codes_are_what_a_shell_reports_for_the_signal() -> None:
    assert (exit_code("SIGINT"), exit_code("SIGTERM")) == (130, 143)


async def test_the_first_signal_is_a_stop_request_and_is_announced() -> None:
    err = io.StringIO()
    stop = SignalStopRequest(err)
    try:
        assert isinstance(stop, StopRequestPort) and stop.reason() is None
        waiting = asyncio.create_task(stop.wait())
        await deliver(signal.SIGTERM)
        assert stop.reason() == "SIGTERM" and await asyncio.wait_for(waiting, 1) == "SIGTERM"
        assert err.getvalue() == (
            "stopping (SIGTERM): ending the run, closing outputs and writing reports; a second signal (Ctrl+C) quits at once\n"
        )
    finally:
        stop.close()


class StepClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


async def test_a_repeat_within_a_second_is_the_same_request(capfd: pytest.CaptureFixture[str]) -> None:
    # `timeout` signals its child and then its process group, and `uv run` passes the first one on:
    # one stop arrives twice, 0.05 ms apart (measured 2026-10-20)
    clock, kills = StepClock(), []
    stop = SignalStopRequest(io.StringIO(), kill=lambda pid, sig: kills.append((pid, sig)), monotonic=clock)
    try:
        await deliver(signal.SIGTERM)
        clock.now += REPEAT_WINDOW_S - 0.001
        await deliver(signal.SIGTERM)
        assert kills == [] and stop.reason() == "SIGTERM" and capfd.readouterr().err == ""
    finally:
        stop.close()


async def test_a_second_signal_ends_the_process_by_its_default_action(capfd: pytest.CaptureFixture[str]) -> None:
    clock, kills = StepClock(), []
    stop = SignalStopRequest(io.StringIO(), kill=lambda pid, sig: kills.append((pid, sig)), monotonic=clock)
    try:
        await deliver(signal.SIGINT)
        clock.now += REPEAT_WINDOW_S
        await deliver(signal.SIGINT)
        assert kills == [(os.getpid(), signal.SIGINT)] and signal.getsignal(signal.SIGINT) is signal.SIG_DFL
        assert capfd.readouterr().err == "stopped immediately by a second SIGINT; outputs may be incomplete\n"
    finally:
        stop.close()


async def test_close_puts_the_previous_handlers_back() -> None:
    previous = {sig: signal.getsignal(sig) for sig in STOP_SIGNALS}
    stop = SignalStopRequest(io.StringIO())
    assert all(signal.getsignal(sig) is not previous[sig] for sig in STOP_SIGNALS)
    stop.close()
    stop.close()  # closing twice changes nothing
    assert {sig: signal.getsignal(sig) for sig in STOP_SIGNALS} == previous


async def test_after_a_stop_close_keeps_absorbing_repeats_until_the_process_ends(capfd: pytest.CaptureFixture[str]) -> None:
    # a stop can finish in under a millisecond, before the repeat of the same stop arrives
    clock, kills = StepClock(), []
    stop = SignalStopRequest(io.StringIO(), kill=lambda pid, sig: kills.append((pid, sig)), monotonic=clock)
    await deliver(signal.SIGTERM)
    stop.close()
    await deliver(signal.SIGTERM)
    assert kills == [] and capfd.readouterr().err == ""
    clock.now += REPEAT_WINDOW_S
    await deliver(signal.SIGTERM)
    assert kills == [(os.getpid(), signal.SIGTERM)]


async def test_a_signal_ignored_at_start_stays_ignored() -> None:
    # a job started with `&` by a non-interactive shell inherits SIGINT ignored
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    stop = SignalStopRequest(io.StringIO())
    try:
        await deliver(signal.SIGINT)
        assert stop.reason() is None and signal.getsignal(signal.SIGINT) is signal.SIG_IGN
        await deliver(signal.SIGTERM)
        assert stop.reason() == "SIGTERM"
    finally:
        stop.close()
    assert signal.getsignal(signal.SIGINT) is signal.SIG_IGN
