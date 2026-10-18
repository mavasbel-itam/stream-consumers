"""Application services wired to the real registry, with scripted sources at the edge."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pytest

import stream_consumers.application.consume_service as consume_module
from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.application.check_service import CheckService
from stream_consumers.application.consume_service import ConsumeService
from stream_consumers.application.list_service import ListService
from stream_consumers.application.profile_service import CollectingSink, ProfileService
from stream_consumers.application.sample_service import SampleService
from stream_consumers.domain.errors import TransportError, UnknownSourceError
from stream_consumers.domain.models import Credential, PublishedVolume, RateBasis, RunStatus
from stream_consumers.domain.policy import MASK, PersonalDataMasker
from stream_consumers.ports.inbound import (
    CheckSourcesUseCase,
    ConsumeStreamUseCase,
    ListSourcesUseCase,
    ProfileSourcesUseCase,
    SampleSourcesUseCase,
)
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies
from tests.support import FakeClock, ListSink, ListSinkFactory, MemoryReports, ScriptedSource, deps, descriptor


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
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 10, sink)
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
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 10, ListSink(), max_events=2)
        assert report.events == 2 and made[0].closed

    async def test_deadline_stops_a_silent_source(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [], clock, hang=True)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 0.05, ListSink())
        assert (report.status, report.events, report.rate) == (RunStatus.NO_EVENTS, 0, None)

    async def test_deadline_already_passed_reads_nothing_more(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, {"a": 2}], clock, gap=5.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 4, ListSink())
        assert report.events == 1 and report.seconds == 5.0

    async def test_a_source_minimum_window_extends_a_shorter_request_only(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}] * 4, clock, gap=5.0, min_window_s=12.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 4, ListSink())
        assert (report.events, report.seconds) == (3, 15.0)  # read for 12 s, not 4: events at 5, 10 and 15 s
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}] * 4, clock, gap=5.0, min_window_s=12.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 30, ListSink())
        assert (report.events, report.seconds) == (4, 20.0)  # a longer request is kept

    async def test_masking_is_on_by_default_and_can_be_disabled(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"user": "ana", "n": 1}], clock, personal=("user",))
        service = ConsumeService(registry(clock, factory), clock)
        masked, raw = ListSink(), ListSink()
        await service.consume("s", 5, masked)
        await service.consume("s", 5, raw, mask=False)
        assert masked.events[0].payload == {"user": MASK, "n": 1}
        assert raw.events[0].payload == {"user": "ana", "n": 1}

    async def test_failure_before_any_event_is_an_error(self) -> None:
        clock = FakeClock()
        factory, made = scripted("s", [TransportError("refused")], clock)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink())
        assert (report.status, report.rate, report.rate_basis) == (RunStatus.ERROR, None, RateBasis.UNMEASURED)
        assert report.detail == "TransportError: refused" and made[0].closed

    async def test_failure_after_events_keeps_the_measurement(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, RuntimeError("late")], clock, gap=1.0)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink())
        assert (report.status, report.events, report.rate) == (RunStatus.OK, 1, 0.5)
        assert report.detail == "RuntimeError: late"

    async def test_published_volume_is_the_rate(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}], clock, volume=PublishedVolume(900, 900.0))
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink())
        assert (report.rate, report.rate_basis) == (1.0, RateBasis.PUBLISHED)

    async def test_published_volume_without_period_is_unmeasured(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}], clock, volume=PublishedVolume(0, 0.0))
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink())
        assert (report.status, report.rate, report.rate_basis) == (RunStatus.OK, None, RateBasis.UNMEASURED)

    async def test_missing_key_is_reported_not_raised(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("k", [], clock)
        factory.DESCRIPTOR = descriptor("k", credential=Credential(("KEY",), "https://sign.up"))  # type: ignore[misc]
        report = await ConsumeService(registry(clock, factory), clock).consume("k", 5, ListSink())
        assert report.status is RunStatus.KEY_PENDING and "KEY" in report.detail and report.rate is None

    async def test_a_source_that_cannot_be_built_is_an_error(self) -> None:
        clock = FakeClock()

        def broken(d: SourceDependencies) -> EventSourcePort:
            raise ValueError("interval_s must be positive")

        report = await ConsumeService(registry(clock, Scripted("b", broken)), clock).consume("b", 5, ListSink())
        assert (report.status, report.detail) == (RunStatus.ERROR, "ValueError: interval_s must be positive")

    async def test_an_unknown_source_still_raises(self) -> None:
        clock = FakeClock()
        with pytest.raises(UnknownSourceError):
            await ConsumeService(registry(clock), clock).consume("zz", 5, ListSink())

    async def test_attributes_are_counted_on_the_first_events_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(consume_module, "ATTRIBUTE_SAMPLE", 1)
        clock = FakeClock()
        factory, _ = scripted("s", [{"a": 1}, {"a": 1, "b": 2, "c": 3}], clock)
        report = await ConsumeService(registry(clock, factory), clock).consume("s", 5, ListSink())
        assert report.events == 2 and report.attributes_median == 1.0

    @pytest.mark.parametrize("seconds, max_events", [(0, None), (-1, None), (5, 0)])
    async def test_rejects_invalid_limits(self, seconds: float, max_events: int | None) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [], clock)
        with pytest.raises(ValueError):
            await ConsumeService(registry(clock, factory), clock).consume("s", seconds, ListSink(), max_events)


class TestCheck:
    async def test_checks_every_source_and_writes_the_report(self) -> None:
        clock = FakeClock()
        good, _ = scripted("good", [{"a": 1}], clock)
        bad, _ = scripted("bad", [TransportError("x")], clock)
        reports = MemoryReports()
        service = CheckService(ConsumeService(registry(clock, good, bad), clock), ListSink(), reports, concurrency=1)
        result = await service.check(["good", "bad"], 5)
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
        rounds = await service.sample(["s"], rounds=3, interval_s=100, window_s=60)
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
        await service.sample(["s"], rounds=2, interval_s=100, window_s=60)
        assert clock.sleeps == [] and len(reports.rounds) == 2

    @pytest.mark.parametrize("rounds, interval, window", [(0, 1, 1), (1, 0, 1), (1, 1, 0)])
    async def test_rejects_invalid_parameters(self, rounds: int, interval: float, window: float) -> None:
        clock = FakeClock()
        service = SampleService(ConsumeService(registry(clock), clock), ListSink(), MemoryReports(), clock)
        with pytest.raises(ValueError):
            await service.sample([], rounds, interval, window)

    def test_rejects_zero_concurrency(self) -> None:
        clock = FakeClock()
        with pytest.raises(ValueError):
            SampleService(ConsumeService(registry(clock), clock), ListSink(), MemoryReports(), clock, concurrency=0)


class TestProfile:
    async def test_statistics_on_real_values_files_masked(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"user": "ana", "n": 1}, {"user": "beto", "n": 3}, {"n": 5}], clock, personal=("user",))
        sinks, reports = ListSinkFactory(), MemoryReports()
        reg = registry(clock, factory)
        (profile,) = await ProfileService(ConsumeService(reg, clock), sinks, reports, reg).profile(["s"], max_events=10, seconds=5)
        fields = {f.name: f for f in profile.fields}
        assert profile.events_inspected == 3 and profile.run.events == 3
        assert fields["user"].distinct == 2 and fields["user"].example == MASK
        assert fields["n"].mean == 3.0
        assert [e.payload for e in sinks.sinks["s"].events] == [{"user": MASK, "n": 1}, {"user": MASK, "n": 3}, {"n": 5}]
        assert sinks.sinks["s"].closed and reports.profiles == [[profile]]

    async def test_max_events_bounds_the_sample(self) -> None:
        clock = FakeClock()
        factory, _ = scripted("s", [{"n": i} for i in range(10)], clock)
        reg = registry(clock, factory)
        (profile,) = await ProfileService(ConsumeService(reg, clock), ListSinkFactory(), MemoryReports(), reg).profile(["s"], 4, 5)
        assert profile.events_inspected == 4

    def test_collecting_sink_masks_what_it_writes(self) -> None:
        inner = ListSink()
        sink = CollectingSink(inner, PersonalDataMasker(["u"]))
        from stream_consumers.domain.models import Event

        sink.write(Event("s", 1.0, {"u": "x"}))
        sink.close()
        assert sink.payloads == [{"u": "x"}] and inner.events[0].payload == {"u": MASK} and inner.closed

    def test_rejects_zero_concurrency(self) -> None:
        clock = FakeClock()
        reg = registry(clock)
        with pytest.raises(ValueError):
            ProfileService(ConsumeService(reg, clock), ListSinkFactory(), MemoryReports(), reg, concurrency=0)


async def test_list_is_sorted_by_id() -> None:
    clock = FakeClock()
    b, _ = scripted("b", [], clock)
    a, _ = scripted("a", [], clock)
    assert [d.id for d in ListService(registry(clock, b, a)).list_sources()] == ["a", "b"]


def test_services_implement_their_inbound_ports() -> None:
    clock = FakeClock()
    reg = registry(clock)
    consume = ConsumeService(reg, clock)
    assert isinstance(consume, ConsumeStreamUseCase)
    assert isinstance(ListService(reg), ListSourcesUseCase)
    assert isinstance(CheckService(consume, ListSink(), MemoryReports()), CheckSourcesUseCase)
    assert isinstance(SampleService(consume, ListSink(), MemoryReports(), clock), SampleSourcesUseCase)
    assert isinstance(ProfileService(consume, ListSinkFactory(), MemoryReports(), reg), ProfileSourcesUseCase)
