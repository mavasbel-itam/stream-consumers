"""Registry, sinks, clock and secrets."""

from __future__ import annotations

import io
import json
import time
from pathlib import Path

import pytest

from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sinks import (
    JsonlFileEventSink,
    JsonlFileSinkFactory,
    JsonReportSink,
    NullEventSink,
    TextStreamEventSink,
)
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.system import EnvSecretProvider, SystemClock
from stream_consumers.domain.errors import UnknownSourceError
from stream_consumers.domain.models import (
    Event,
    FieldProfile,
    RateBasis,
    RunReport,
    RunStatus,
    SamplingRound,
    SourceProfile,
)
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies
from tests.support import FakeClock, ScriptedSource, deps, descriptor


class _Factory(BaseSourceFactory):
    def __init__(self, source_id: str) -> None:
        self.DESCRIPTOR = descriptor(source_id)  # type: ignore[misc]

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [], deps.clock)  # type: ignore[arg-type]


class TestRegistry:
    def test_lists_describes_and_creates(self) -> None:
        registry = FactoryRegistry([_Factory("a"), _Factory("b")], deps())
        assert [d.id for d in registry.descriptors()] == ["a", "b"]
        assert registry.descriptor("b").id == "b"
        assert registry.create("a").descriptor.id == "a"

    def test_unknown_ids_raise(self) -> None:
        registry = FactoryRegistry([_Factory("a")], deps())
        with pytest.raises(UnknownSourceError):
            registry.descriptor("zz")
        with pytest.raises(UnknownSourceError):
            registry.create("zz")

    def test_duplicate_ids_are_rejected(self) -> None:
        with pytest.raises(ValueError):
            FactoryRegistry([_Factory("a"), _Factory("a")], deps())


EVENT = Event("s", 1.5, {"a": "ñ", "b": {"c": 1}})
REPORT = RunReport("s", RunStatus.OK, 3, 2.0, 1.5, RateBasis.OBSERVED, 4.0, 0.2, 10.0, "")


class TestEventSinks:
    def test_null_sink_discards(self) -> None:
        sink = NullEventSink()
        sink.write(EVENT)
        sink.close()

    def test_text_stream_sink_writes_json_lines_and_flushes(self) -> None:
        stream = io.StringIO()
        sink = TextStreamEventSink(stream)
        sink.write(EVENT)
        sink.close()
        assert json.loads(stream.getvalue()) == {"source": "s", "received_at": 1.5, "payload": {"a": "ñ", "b": {"c": 1}}}
        assert not stream.closed

    def test_file_sink_creates_directories_and_closes(self, tmp_path: Path) -> None:
        sink = JsonlFileEventSink(tmp_path / "x" / "s.jsonl")
        sink.write(EVENT)
        sink.write(EVENT)
        sink.close()
        assert len((tmp_path / "x" / "s.jsonl").read_text(encoding="utf-8").splitlines()) == 2

    def test_factory_names_files_after_the_source(self, tmp_path: Path) -> None:
        sink = JsonlFileSinkFactory(tmp_path).open("abc")
        sink.close()
        assert (tmp_path / "abc.jsonl").exists()


class TestReportSink:
    def test_writes_dated_json_files(self, tmp_path: Path) -> None:
        clock = FakeClock(start=0.0)
        sink = JsonReportSink(tmp_path / "r", clock)
        sink.write_check([REPORT])
        sink.write_round(SamplingRound(2, 0.0, (REPORT,)))
        field = FieldProfile("a", 1.0, 1, ("number",), 1.0, 1.0, 1.0, "1")
        sink.write_profiles([SourceProfile(REPORT, 1, (field,))])
        names = sorted(p.name for p in (tmp_path / "r").iterdir())
        assert names == ["check-19700101T000000Z.json", "profiles-19700101T000000Z.json", "round-02-19700101T000000Z.json"]
        check = json.loads((tmp_path / "r" / names[0]).read_text())
        assert check[0]["status"] == "ok" and check[0]["rate_basis"] == "observed"
        profile = json.loads((tmp_path / "r" / names[1]).read_text())
        assert profile[0]["fields"][0]["kinds"] == ["number"]
        assert json.loads((tmp_path / "r" / names[2]).read_text())["reports"][0]["source_id"] == "s"


class TestSystem:
    async def test_clock(self) -> None:
        clock = SystemClock()
        assert abs(clock.now() - time.time()) < 5
        before = clock.monotonic()
        await clock.sleep(0.01)
        assert clock.monotonic() > before

    def test_environment_wins_over_the_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("# keys\n\nA=from-file\nB = 'quoted'\nC=\"double\"\nD=\nnot a pair\nE='\n", encoding="utf-8")
        secrets = EnvSecretProvider({"A": "from-env", "Z": ""}, env)
        assert secrets.get("A") == "from-env"
        assert secrets.get("B") == "quoted" and secrets.get("C") == "double"
        assert secrets.get("D") is None and secrets.get("Z") is None and secrets.get("missing") is None
        assert secrets.get("E") == "'"

    def test_missing_file_is_fine(self, tmp_path: Path) -> None:
        assert EnvSecretProvider({}, tmp_path / "absent").get("A") is None
        assert EnvSecretProvider({"A": "1"}, None).get("A") == "1"
