"""Application services wired to the real registry, with scripted sources at the edge."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Mapping, Sequence

import pytest

import stream_consumers.application.consume_service as consume_module
from stream_consumers.adapters.outbound.providers.registry import FactoryRegistry
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.base import BaseEventSource
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.application.check_service import CheckService
from stream_consumers.application.consume_service import ConsumeService
from stream_consumers.application.list_service import ListService
from stream_consumers.application.profile_service import CollectingSink, ProfileService
from stream_consumers.application.sample_service import SampleService
from stream_consumers.application.verdict_service import VerdictService
from stream_consumers.domain.errors import TransportError, UnknownSourceError
from stream_consumers.domain.models import (
    Credential,
    Event,
    FieldClass,
    Group,
    PublishedVolume,
    RateBasis,
    RateVerdict,
    RunReport,
    RunStatus,
    SamplingRound,
    Verdict,
)
from stream_consumers.domain.policy import MASK, PersonalDataMasker
from stream_consumers.ports.inbound import (
    CheckSourcesUseCase,
    ConsumeStreamUseCase,
    JudgeSamplingUseCase,
    ListSourcesUseCase,
    ProfileSourcesUseCase,
    SampleSourcesUseCase,
)
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies
from tests.support import (
    FakeClock,
    ListSink,
    ListSinkFactory,
    ManualStop,
    MemoryReports,
    ScriptedSource,
    StoppingSink,
    deps,
    descriptor,
)


class Scripted(BaseSourceFactory):
    def __init__(self, source_id: str, make: Callable[[SourceDependencies], EventSourcePort], **desc: object) -> None:
        self.DESCRIPTOR = descriptor(source_id, **desc)  # type: ignore[misc,arg-type]
        self._make = make

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return self._make(deps)


def registry(clock: FakeClock, *factories: Scripted) -> FactoryRegistry:
    return FactoryRegistry(factories, deps(clock=clock))


def scripted(source_id: str, payloads: Sequence[object], clock: FakeClock, **kwargs: object) -> tuple[Scripted, list[ScriptedSource]]:
    made: list[ScriptedSource] = []
    personal = kwargs.pop("personal", ())
    min_window_s = kwargs.pop("min_window_s", 0.0)

    def make(d: SourceDependencies) -> EventSourcePort:
        desc = descriptor(source_id, personal=personal, min_window_s=min_window_s)  # type: ignore[arg-type]
        source = ScriptedSource(desc, payloads, clock, **kwargs)  # type: ignore[arg-type]
        made.append(source)
        return source

    return Scripted(source_id, make, personal=personal, min_window_s=min_window_s), made


class TestConsume:
    async def test_observed_rate_and_first_event(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"a": 1}, {"a": 2, "b": {"c": 3}}, {"a": 3}], clock, gap=1.0)
        sink = ListSink()
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 10, sink, stop=ManualStop())
        assert (report.status, report.events, report.seconds, report.rate, report.rate_basis) == (
            RunStatus.OK,
            3,
            3.0,
            1.0,
            RateBasis.OBSERVED,
        )
        assert report.first_event_s == 1.0 and report.attributes_median == 1.0 and report.started_at == 1_700_000_000.0
        assert [e.payload for e in sink.events] == [{"a": 1}, {"a": 2, "b.c": 3}, {"a": 3}]
        assert made[0].closed

    async def test_max_events_stops_early(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"a": 1}] * 5, clock)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 10, ListSink(), max_events=2, stop=ManualStop())
        assert report.events == 2 and made[0].closed

    async def test_deadline_stops_a_silent_source(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [], clock, hang=True)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 0.05, ListSink(), stop=ManualStop())
        assert (report.status, report.events, report.rate) == (RunStatus.NO_EVENTS, 0, None)

    async def test_deadline_already_passed_reads_nothing_more(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, {"a": 2}], clock, gap=5.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 4, ListSink(), stop=ManualStop())
        assert report.events == 1 and report.seconds == 5.0

    async def test_a_source_minimum_window_extends_a_shorter_request_only(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}] * 4, clock, gap=5.0, min_window_s=12.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 4, ListSink(), stop=ManualStop())
        assert (report.events, report.seconds) == (3, 15.0)  # read for 12 s, not 4: events at 5, 10 and 15 s
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}] * 4, clock, gap=5.0, min_window_s=12.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 30, ListSink(), stop=ManualStop())
        assert (report.events, report.seconds) == (4, 20.0)  # a longer request is kept

    async def test_masking_is_on_by_default_and_can_be_disabled(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"user": "ana", "n": 1}], clock, personal=("user",))
        service = ConsumeService(registry(clock, factory), clock)
        masked, raw = ListSink(), ListSink()
        await service.consume("s", 5, masked, stop=ManualStop())
        await service.consume("s", 5, raw, mask=False, stop=ManualStop())
        assert masked.events[0].payload == {"user": MASK, "n": 1}
        assert raw.events[0].payload == {"user": "ana", "n": 1}

    async def test_failure_before_any_event_is_an_error(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [TransportError("refused")], clock)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink(), stop=ManualStop())
        assert (report.status, report.rate, report.rate_basis) == (RunStatus.ERROR, None, RateBasis.UNMEASURED)
        assert report.detail == "TransportError: refused" and made[0].closed

    async def test_failure_after_events_keeps_the_measurement(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, RuntimeError("late")], clock, gap=1.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink(), stop=ManualStop())
        assert (report.status, report.events, report.rate) == (RunStatus.OK, 1, 0.5)
        assert report.detail == "RuntimeError: late"

    async def test_published_volume_is_the_rate(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}], clock, volume=PublishedVolume(900, 900.0))
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink(), stop=ManualStop())
        assert (report.rate, report.rate_basis) == (1.0, RateBasis.PUBLISHED)

    async def test_published_volume_without_period_is_unmeasured(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}], clock, volume=PublishedVolume(0, 0.0))
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink(), stop=ManualStop())
        assert (report.status, report.rate, report.rate_basis) == (RunStatus.OK, None, RateBasis.UNMEASURED)

    async def test_missing_key_is_reported_not_raised(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("k", [], clock)
        factory.DESCRIPTOR = descriptor("k", credential=Credential(("KEY",), "https://sign.up"))  # type: ignore[misc]
        report = await ConsumeService(registry(clock, factory), clock).consume("k", 5, ListSink(), stop=ManualStop())
        assert report.status is RunStatus.KEY_PENDING and "KEY" in report.detail and report.rate is None

    async def test_a_source_that_cannot_be_built_is_an_error(self) -> None:
        clock = FakeClock()

        def broken(d: SourceDependencies) -> EventSourcePort:
            raise ValueError("interval_s must be positive")

        report = await ConsumeService(registry(clock, Scripted("b", broken)), clock).consume("b", 5, ListSink(), stop=ManualStop())
        assert (report.status, report.detail) == (RunStatus.ERROR, "ValueError: interval_s must be positive")

    async def test_an_unknown_source_still_raises(self) -> None:
        clock = FakeClock()
        with pytest.raises(UnknownSourceError):
            await ConsumeService(registry(clock), clock).consume("zz", 5, ListSink(), stop=ManualStop())

    async def test_attributes_are_counted_on_the_first_events_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(consume_module, "ATTRIBUTE_SAMPLE", 1)
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, {"a": 1, "b": 2, "c": 3}], clock)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink(), stop=ManualStop())
        assert report.events == 2 and report.attributes_median == 1.0

    async def test_a_failing_sink_ends_the_run_and_is_not_reported_as_a_provider_failure(self) -> None:
        class ClosedPipe(ListSink):
            def write(self, event: Event) -> None:
                raise BrokenPipeError(32, "Broken pipe")

        clock = FakeClock()
        factory, made = scripted("s", [{"a": 1}, {"a": 2}], clock)
        with pytest.raises(BrokenPipeError):
            await ConsumeService(registry(clock, factory), clock).consume("s", 5, ClosedPipe(), stop=ManualStop())
        assert made[0].closed

    @pytest.mark.parametrize("seconds, max_events", [(0, None), (-1, None), (5, 0)])
    async def test_rejects_invalid_limits(self, seconds: float, max_events: int | None) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [], clock)
        with pytest.raises(ValueError):
            await ConsumeService(registry(clock, factory), clock).consume("s", seconds, ListSink(), max_events, stop=ManualStop())


class AlwaysReady(BaseEventSource):
    """Has its next record ready at every request, so reading it never suspends."""

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        while True:
            yield {"n": 1}


class Paced(BaseEventSource):
    """One record every 10 ms of real time."""

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        while True:
            await asyncio.sleep(0.01)
            yield {"n": 1}


class TestFairness:
    async def test_a_source_that_is_always_ready_does_not_starve_the_others(self) -> None:
        clock = SystemClock()
        factories = (
            Scripted("paced", lambda d: Paced(descriptor("paced"), d.clock)),
            Scripted("ready", lambda d: AlwaysReady(descriptor("ready"), d.clock)),
        )
        service = ConsumeService(FactoryRegistry(factories, deps(clock=clock)), clock)
        paced, ready = await asyncio.gather(
            service.consume("paced", 0.5, ListSink(), stop=ManualStop()), service.consume("ready", 0.5, ListSink(), stop=ManualStop())
        )
        assert ready.events > 1000 and paced.events >= 20  # 10 ms apart: about 50 in 0.5 s when it gets its turns


class TestCheck:
    async def test_checks_every_source_and_writes_the_report(self) -> None:
        clock = FakeClock()
        good, _ = scripted("good", [{"a": 1}], clock)
        bad, _ = scripted("bad", [TransportError("x")], clock)
        reports = MemoryReports()
        service = CheckService(ConsumeService(registry(clock, good, bad), clock), ListSink(), reports, concurrency=1)
        result = await service.check(["good", "bad"], 5, stop=ManualStop())
        assert [r.status for r in result] == [RunStatus.OK, RunStatus.ERROR]
        assert reports.checks == [result]

    def test_rejects_zero_concurrency(self) -> None:
        clock = FakeClock()
        with pytest.raises(ValueError):
            CheckService(ConsumeService(registry(clock), clock), ListSink(), MemoryReports(), concurrency=0)


class TestSample:
    async def test_rounds_start_on_wall_clock_targets(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"a": 1}, {"a": 2}], clock, gap=10.0)
        reports = MemoryReports()
        service = SampleService(ConsumeService(registry(clock, factory), clock), ListSink(), reports, clock)
        rounds = await service.sample(["s"], rounds=3, interval_s=100, window_s=60, stop=ManualStop())
        assert [r.number for r in rounds] == [1, 2, 3] and reports.rounds == list(rounds)
        assert [r.scheduled_at - clock.wall + 220 for r in rounds] == [0.0, 100.0, 200.0]
        assert all(r.reports[0].events == 2 for r in rounds) and len(made) == 3
        assert max(clock.sleeps) <= 30.0

    async def test_a_missed_round_starts_immediately(self) -> None:
        clock = FakeClock()

        def slow(d: SourceDependencies) -> EventSourcePort:
            clock.advance(250)  # the host "slept" through the next two targets
            return ScriptedSource(descriptor("s"), [{"a": 1}], clock)

        reports = MemoryReports()
        service = SampleService(ConsumeService(registry(clock, Scripted("s", slow)), clock), ListSink(), reports, clock)
        await service.sample(["s"], rounds=2, interval_s=100, window_s=60, stop=ManualStop())
        assert clock.sleeps == [] and len(reports.rounds) == 2

    @pytest.mark.parametrize("rounds, interval, window", [(0, 1, 1), (1, 0, 1), (1, 1, 0)])
    async def test_rejects_invalid_parameters(self, rounds: int, interval: float, window: float) -> None:
        clock = FakeClock()
        service = SampleService(ConsumeService(registry(clock), clock), ListSink(), MemoryReports(), clock)
        with pytest.raises(ValueError):
            await service.sample([], rounds, interval, window, stop=ManualStop())

    async def test_settled_sources_stop_and_sampling_ends_when_none_is_open(self) -> None:
        clock = FakeClock()
        fast, fast_made = scripted("fast", [{"a": 1}] * 10, clock, gap=1.0)  # 10 events/s in a 1 s window
        silent, _ = scripted("silent", [], clock, hang=True)  # no events: 0 events/s
        keyed, keyed_made = scripted("keyed", [], clock)
        keyed.DESCRIPTOR = descriptor("keyed", credential=Credential(("KEY",), "https://sign.up"))  # type: ignore[misc]
        reports = MemoryReports()
        service = SampleService(ConsumeService(registry(clock, fast, silent, keyed), clock), ListSink(), reports, clock)
        rounds = await service.sample(
            ["fast", "silent", "keyed"], rounds=5, interval_s=100, window_s=1, stop_when_settled=True, stop=ManualStop()
        )
        assert [[r.source_id for r in sampling_round.reports] for sampling_round in rounds] == [
            ["fast", "silent", "keyed"],
            ["fast", "silent", "keyed"],
            ["fast", "silent", "keyed"],  # fast passes and silent fails after 3 of 5
            ["keyed"],  # key pending: nothing measured, open until the plan ends
            ["keyed"],
        ]
        assert len(fast_made) == 3 and len(keyed_made) == 0 and reports.rounds == list(rounds)

    async def test_without_the_option_every_round_reads_every_source(self) -> None:
        """Negative control: a settled source is read in every planned round by default."""
        clock = FakeClock()
        fast, fast_made = scripted("fast", [{"a": 1}] * 10, clock, gap=0.1)
        service = SampleService(ConsumeService(registry(clock, fast), clock), ListSink(), MemoryReports(), clock)
        rounds = await service.sample(["fast"], rounds=4, interval_s=100, window_s=1, stop=ManualStop())
        assert len(rounds) == 4 and len(fast_made) == 4

    async def test_an_interrupted_run_continues_with_the_missing_rounds(self) -> None:
        clock = FakeClock()
        fast, fast_made = scripted("fast", [{"a": 1}] * 10, clock, gap=0.1)
        service = SampleService(ConsumeService(registry(clock, fast), clock), ListSink(), MemoryReports(), clock)
        earlier = await service.sample(["fast"], rounds=2, interval_s=100, window_s=1, stop=ManualStop())
        rounds = await service.sample(["fast"], rounds=5, interval_s=100, window_s=1, prior=earlier, stop=ManualStop())
        assert [r.number for r in rounds] == [3, 4, 5] and len(fast_made) == 5
        assert await service.sample(["fast"], rounds=5, interval_s=100, window_s=1, prior=[*earlier, *rounds], stop=ManualStop()) == []

    async def test_sources_settled_before_the_interruption_are_not_read_again(self) -> None:
        clock = FakeClock()
        fast, fast_made = scripted("fast", [{"a": 1}] * 10, clock, gap=0.1)
        slow, slow_made = scripted("slow", [{"a": 1}] * 10, clock, gap=0.1)
        service = SampleService(ConsumeService(registry(clock, fast, slow), clock), ListSink(), MemoryReports(), clock)
        passed = RunReport("fast", RunStatus.OK, 50, 5.0, 10.0, RateBasis.OBSERVED, 1.0, 0.1, 0.0)
        earlier = [SamplingRound(n, float(n), (passed,)) for n in (1, 2, 3)]
        rounds = await service.sample(
            ["fast", "slow"], rounds=5, interval_s=100, window_s=1, prior=earlier, stop_when_settled=True, stop=ManualStop()
        )
        assert [[r.source_id for r in sampling_round.reports] for sampling_round in rounds] == [["slow"], ["slow"]]
        assert len(fast_made) == 0 and len(slow_made) == 2

    def test_rejects_zero_concurrency(self) -> None:
        clock = FakeClock()
        with pytest.raises(ValueError):
            SampleService(ConsumeService(registry(clock), clock), ListSink(), MemoryReports(), clock, concurrency=0)


class TestVerdicts:
    def ok(self, source_id: str, value: float) -> RunReport:
        return RunReport(source_id, RunStatus.OK, 1, 1.0, value, RateBasis.OBSERVED, 1.0, 0.1, 0.0)

    def test_every_source_in_the_rounds_by_default_sorted(self) -> None:
        rounds = [SamplingRound(n, float(n), (self.ok("b", 0.5), self.ok("a", 3.0))) for n in (1, 2, 3)]
        assert list(VerdictService().verdicts(rounds, 3)) == [
            RateVerdict("a", 3, 3, 3.0, Verdict.PASSES),
            RateVerdict("b", 3, 3, 0.5, Verdict.FAILS),
        ]

    def test_selected_sources_including_one_never_measured(self) -> None:
        rounds = [SamplingRound(1, 1.0, (self.ok("a", 3.0),))]
        assert list(VerdictService().verdicts(rounds, 24, ["new", "a"])) == [
            RateVerdict("new", 0, 24, None, Verdict.OPEN),
            RateVerdict("a", 1, 24, 3.0, Verdict.OPEN),
        ]

    def test_the_plan_needs_a_round(self) -> None:
        with pytest.raises(ValueError):
            VerdictService().verdicts([], 0)


class TestProfile:
    async def test_statistics_on_real_values_files_masked(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"user": "ana", "n": 1}, {"user": "beto", "n": 3}, {"n": 5}], clock, personal=("user",))
        sinks, reports = ListSinkFactory(), MemoryReports()
        reg = registry(clock, factory)
        (profile,) = await ProfileService(ConsumeService(reg, clock), sinks, reports, reg).profile(
            ["s"], max_events=10, seconds=5, stop=ManualStop()
        )
        fields = {f.name: f for f in profile.fields}
        assert profile.events_inspected == 3 and profile.run.events == 3
        assert fields["user"].distinct == 2 and fields["user"].example == MASK
        assert fields["n"].mean == 3.0 and fields["n"].field_class is FieldClass.NUMBER
        assert profile.natural_key == ("n",) and profile.duplicate_ratio == 0.0 and profile.bytes_p95 is not None
        assert [e.payload for e in sinks.sinks["s"].events] == [{"user": MASK, "n": 1}, {"user": MASK, "n": 3}, {"n": 5}]
        assert sinks.sinks["s"].closed and reports.profiles == [[profile]]

    async def test_max_events_bounds_the_sample(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"n": i} for i in range(10)], clock)
        reg = registry(clock, factory)
        (profile,) = await ProfileService(ConsumeService(reg, clock), ListSinkFactory(), MemoryReports(), reg).profile(
            ["s"], 4, 5, stop=ManualStop()
        )
        assert profile.events_inspected == 4

    async def test_collecting_sink_masks_what_it_writes_and_opens_and_closes_the_inner_sink(self) -> None:
        inner = ListSink()
        sink = CollectingSink(inner, PersonalDataMasker(["u"]))
        from stream_consumers.domain.models import Event

        await sink.open()
        await sink.write(Event("s", 1.0, {"u": "x"}))
        await sink.close()
        assert sink.payloads == [{"u": "x"}] and inner.events[0].payload == {"u": MASK} and inner.opened and inner.closed

    async def test_each_source_sink_is_opened_before_and_closed_after_its_run(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"n": 1}], clock)
        reg = registry(clock, factory)
        sinks = ListSinkFactory()
        await ProfileService(ConsumeService(reg, clock), sinks, MemoryReports(), reg).profile(["s"], 4, 5, stop=ManualStop())
        assert sinks.sinks["s"].opened and sinks.sinks["s"].closed and len(sinks.sinks["s"].events) == 1

    def test_rejects_zero_concurrency(self) -> None:
        clock = FakeClock()
        reg = registry(clock)
        with pytest.raises(ValueError):
            ProfileService(ConsumeService(reg, clock), ListSinkFactory(), MemoryReports(), reg, concurrency=0)


def stop_later(stop: ManualStop, seconds: float, reason: str = "SIGINT") -> None:
    asyncio.get_running_loop().call_later(seconds, stop.request, reason)


class TestStop:
    """A stop request ends a run as the end of its window would, and every service keeps what finished."""

    async def test_a_stop_ends_the_wait_for_the_next_event_at_once(self) -> None:
        clock = SystemClock()
        factory = Scripted("s", lambda d: Paced(descriptor("s"), d.clock))
        stop = ManualStop()
        stop_later(stop, 0.2, "SIGTERM")
        report = await ConsumeService(FactoryRegistry((factory,), deps(clock=clock)), clock).consume("s", 30, ListSink(), stop=stop)
        assert report.status is RunStatus.OK and report.events >= 5 and report.seconds < 1
        assert report.detail == f"stopped by SIGTERM after {report.seconds:g} of 30 s"

    async def test_a_silent_source_is_stopped_and_closed(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [], clock, hang=True)
        stop = ManualStop()
        stop_later(stop, 0.05)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 3600, ListSink(), stop=stop)
        assert (report.status, report.events, report.detail) == (RunStatus.NO_EVENTS, 0, "stopped by SIGINT after 0 of 3600 s")
        assert made[0].closed

    async def test_the_event_being_written_when_the_stop_comes_is_kept(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"n": i} for i in range(10)], clock, gap=1.0)
        stop = ManualStop()
        sink = StoppingSink(stop, after=3)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 60, sink, stop=stop)
        assert [e.payload for e in sink.events] == [{"n": 0}, {"n": 1}, {"n": 2}] and report.events == 3
        assert report.detail == "stopped by SIGINT after 3 of 60 s" and made[0].closed

    async def test_a_stop_requested_before_the_start_reads_nothing(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"n": 1}], clock)
        stop = ManualStop()
        stop.request()
        sink = ListSink()
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 10, sink, stop=stop)
        assert (report.status, report.events, report.detail) == (RunStatus.NO_EVENTS, 0, "stopped by SIGINT after 0 of 10 s")
        assert sink.events == [] and not made[0].closed  # never started, so there was nothing to close

    async def test_a_run_that_had_already_finished_is_not_marked_stopped(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"n": i} for i in range(5)], clock, gap=1.0)
        stop = ManualStop()
        report = await ConsumeService(registry(clock, factory), clock).consume(
            "s", 60, StoppingSink(stop, after=2), max_events=2, stop=stop
        )
        assert stop.reason() == "SIGINT" and report.events == 2 and report.detail == ""

    async def test_a_provider_failure_keeps_its_own_detail(self) -> None:
        clock = FakeClock()
        stop = ManualStop()

        class FailsAsTheStopComes(BaseEventSource):
            async def events(self) -> AsyncGenerator[Mapping[str, object]]:
                yield {"n": 1}
                stop.request()
                raise TransportError("gone")

        factory = Scripted("s", lambda d: FailsAsTheStopComes(descriptor("s"), d.clock))
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 60, ListSink(), stop=stop)
        assert report.events == 1 and report.detail == "TransportError: gone"

    async def test_a_window_that_ran_out_as_the_stop_came_is_left_to_end(self) -> None:
        stop = ManualStop()
        stop.request()
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0) as scope:
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    assert scope.expired()
                    await ConsumeService._end_waits_on_stop(stop, [scope])  # must not reschedule an expiring timeout
                    raise

    async def test_check_starts_no_source_after_the_stop_and_reports_the_started_ones(self) -> None:
        clock = FakeClock()
        first, _ = scripted("first", [], clock, hang=True)
        second, made = scripted("second", [{"n": 1}], clock)
        reports, stop = MemoryReports(), ManualStop()
        stop_later(stop, 0.05)
        service = CheckService(ConsumeService(registry(clock, first, second), clock), ListSink(), reports, concurrency=1)
        result = await service.check(["first", "second"], 60, stop=stop)
        assert [r.source_id for r in result] == ["first"] and result[0].detail.startswith("stopped by SIGINT")
        assert reports.checks == [result] and made == []

    async def test_profile_starts_no_source_after_the_stop_and_keeps_what_arrived(self) -> None:
        clock = FakeClock()
        first, _ = scripted("first", [{"n": 1}, {"n": 2}], clock, hang=True)
        second, made = scripted("second", [{"n": 1}], clock)
        reg = registry(clock, first, second)
        sinks, reports, stop = ListSinkFactory(), MemoryReports(), ManualStop()
        stop_later(stop, 0.05)
        profiles = await ProfileService(ConsumeService(reg, clock), sinks, reports, reg, concurrency=1).profile(
            ["first", "second"], 10, 60, stop=stop
        )
        assert [p.run.source_id for p in profiles] == ["first"] and profiles[0].events_inspected == 2
        assert sinks.sinks["first"].closed and "second" not in sinks.sinks and made == [] and reports.profiles == [profiles]

    async def test_sample_stopped_while_waiting_for_the_next_round_keeps_the_finished_rounds(self) -> None:
        clock = SystemClock()
        factory = Scripted("s", lambda d: Paced(descriptor("s"), d.clock))
        reports, stop = MemoryReports(), ManualStop()
        stop_later(stop, 0.3)
        service = SampleService(ConsumeService(FactoryRegistry((factory,), deps(clock=clock)), clock), ListSink(), reports, clock)
        started = clock.monotonic()
        rounds = await service.sample(["s"], rounds=3, interval_s=60, window_s=0.1, stop=stop)
        assert [r.number for r in rounds] == [1] and reports.rounds == list(rounds) and rounds[0].reports[0].detail == ""
        assert clock.monotonic() - started < 2

    async def test_sample_does_not_record_the_round_the_stop_cut_short(self) -> None:
        clock = SystemClock()
        factory = Scripted("s", lambda d: Paced(descriptor("s"), d.clock))
        reports, stop = MemoryReports(), ManualStop()
        stop_later(stop, 0.4)
        service = SampleService(ConsumeService(FactoryRegistry((factory,), deps(clock=clock)), clock), ListSink(), reports, clock)
        rounds = await service.sample(["s"], rounds=3, interval_s=0.3, window_s=0.2, stop=stop)
        assert [r.number for r in rounds] == [1] and reports.rounds == list(rounds)

    async def test_sample_stopped_before_its_first_round_records_nothing(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [{"n": 1}], clock)
        reports, stop = MemoryReports(), ManualStop()
        stop.request()
        rounds = await SampleService(ConsumeService(registry(clock, factory), clock), ListSink(), reports, clock).sample(
            ["s"], rounds=2, interval_s=60, window_s=5, stop=stop
        )
        assert rounds == [] and reports.rounds == [] and made == []

    async def test_sample_stopped_between_rounds_while_the_clock_is_virtual(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"n": 1}], clock)
        stop = ManualStop()

        class StopAfterFirstRound(MemoryReports):
            def write_round(self, sampling_round: SamplingRound) -> None:
                super().write_round(sampling_round)
                stop.request()

        reports = StopAfterFirstRound()
        rounds = await SampleService(ConsumeService(registry(clock, factory), clock), ListSink(), reports, clock).sample(
            ["s"], rounds=3, interval_s=100, window_s=5, stop=stop
        )
        assert [r.number for r in rounds] == [1] and reports.rounds == list(rounds)


async def test_list_is_sorted_by_id() -> None:
    clock = FakeClock()
    b, _ = scripted("b", [], clock)
    a, _ = scripted("a", [], clock)
    assert [d.id for d in ListService(registry(clock, b, a)).list_sources()] == ["a", "b"]


def test_default_sources_leave_out_the_low_rate_group_only_and_keep_catalog_order() -> None:
    clock = FakeClock()
    factories = [Scripted(g.name.lower(), lambda d: ScriptedSource(descriptor(), [], clock), group=g) for g in Group]
    service = ListService(registry(clock, *factories))
    assert [d.id for d in service.list_sources()] == ["candidate", "free_key", "keyless", "low_rate", "project_document"]
    assert [d.id for d in service.default_sources()] == ["keyless", "project_document", "free_key", "candidate"]


def test_services_implement_their_inbound_ports() -> None:
    clock = FakeClock()
    reg = registry(clock)
    consume = ConsumeService(reg, clock)
    assert isinstance(consume, ConsumeStreamUseCase)
    assert isinstance(ListService(reg), ListSourcesUseCase)
    assert isinstance(CheckService(consume, ListSink(), MemoryReports()), CheckSourcesUseCase)
    assert isinstance(SampleService(consume, ListSink(), MemoryReports(), clock), SampleSourcesUseCase)
    assert isinstance(VerdictService(), JudgeSamplingUseCase)
    assert isinstance(ProfileService(consume, ListSinkFactory(), MemoryReports(), reg), ProfileSourcesUseCase)
