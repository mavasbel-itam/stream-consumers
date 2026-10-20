"""Output destinations, text formats, text sinks, batching and SQLite."""

from __future__ import annotations

import asyncio
import contextlib
import csv
import io
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

import pytest

from stream_consumers.adapters.outbound.outputs.batching import BatchingEventSink
from stream_consumers.adapters.outbound.outputs.formats import (
    EXTRA,
    CsvFormat,
    DelimitedEncoder,
    JsonArrayFormat,
    JsonLinesFormat,
    PrettyJsonFormat,
    TsvFormat,
    event_document,
)
from stream_consumers.adapters.outbound.outputs.sinks import (
    NullEventSink,
    TextFileEventSink,
    TextFileSinkFactory,
    TextStreamEventSink,
)
from stream_consumers.adapters.outbound.outputs.sqlite import SqliteEventSink
from stream_consumers.domain.errors import OutputError, OutputTargetError
from stream_consumers.domain.models import Event
from stream_consumers.domain.outputs import FILE, TERMINAL, parse_target
from stream_consumers.domain.policy import flatten
from stream_consumers.ports.outbound.outputs import EventFormatPort
from tests.support import FakeClock, messages
from tests.unit.test_sources import EXPECTED, decoder_of

EVENT = Event("s", 1.5, {"a": "ñ", "b": {"c": 1}})
FORMATS: tuple[EventFormatPort, ...] = (JsonLinesFormat(), CsvFormat(), TsvFormat(), JsonArrayFormat(), PrettyJsonFormat())
WITH_FIXTURES = sorted(EXPECTED)
"""Every source whose captured real messages decode through its own decoder (test_sources.py)."""


def real_events(source_id: str) -> list[Event]:
    """The payloads a source decodes from its captured real messages."""
    decoder = decoder_of(source_id)
    return [Event(source_id, 1_760_000_000.0 + i, p) for i, p in enumerate(e for m in messages(source_id) for e in decoder.decode(m))]


def encode(event_format: EventFormatPort, events: Sequence[Event]) -> str:
    encoder = event_format.encoder()
    return "".join(encoder.encode(e) for e in events) + encoder.finish()


def plain(value: object) -> object:
    """What a JSON round trip gives back (non-JSON values such as bytes are written as text)."""
    return json.loads(json.dumps(value, default=str))


class TestParseTarget:
    def test_terminal_files_and_paths_that_only_look_like_schemes(self) -> None:
        assert parse_target("-", {"sqlite"}).scheme == TERMINAL
        for text in ("data/x.csv", "x", "C:\\data\\x.csv", "notes:today.txt", "./kafka://x"):
            target = parse_target(text, {"sqlite"})
            assert (target.scheme, target.location) == (FILE, text)

    def test_a_scheme_without_authority(self) -> None:
        target = parse_target("sqlite:data/events.db", {"sqlite"})
        assert (target.scheme, target.location, target.hosts) == ("sqlite", "data/events.db", ())
        with pytest.raises(OutputTargetError, match="missing location after sqlite:"):
            parse_target("sqlite:", {"sqlite"})

    def test_an_unknown_scheme_with_authority_is_an_error_not_a_file(self) -> None:
        with pytest.raises(OutputTargetError, match="unknown output scheme 'kafka' \\(known: mqtt, sqlite\\)"):
            parse_target("kafka://h:9092/t", {"sqlite", "mqtt"})

    def test_authority_hosts_path_user_password_and_options(self) -> None:
        text = "kafka://ana:p%40ss@h1:9092,[::1]:9093,h3/top%2Fic/x?acks=all&empty="
        target = parse_target(text, {"kafka"})
        assert target.hosts == (("h1", 9092), ("::1", 9093), ("h3", None))
        assert (target.path, target.user, target.password) == ("top/ic/x", "ana", "p@ss")
        assert target.options == {"acks": "all", "empty": ""}
        assert target.display == "kafka://ana:***@h1:9092,[::1]:9093,h3/top%2Fic/x?acks=all&empty="
        assert target.text == text and target.location == text[len("kafka://") :]

    def test_user_without_password_and_no_path(self) -> None:
        target = parse_target("redis://ana@h", {"redis"})
        assert (target.user, target.password, target.path, target.options, target.hosts) == ("ana", None, "", {}, (("h", None),))
        assert target.display == "redis://ana@h"
        assert parse_target("redis://h?db=1", {"redis"}).options == {"db": "1"}
        assert parse_target("redis://:secret@h", {"redis"}).user is None

    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("kafka:///topic", "missing host in kafka:///topic"),
            ("kafka://u:pw@/topic", "missing host in kafka://u:\\*\\*\\*@/topic"),
            ("kafka://h1,:9092", "missing host"),
            ("kafka://h:0", "invalid port '0'"),
            ("kafka://h:65536", "invalid port '65536'"),
            ("kafka://h:x1", "invalid port 'x1'"),
            ("kafka://[::1", "malformed host"),
            ("kafka://[::1]9092", "malformed host"),
            ("kafka://h/?flag", "malformed options"),
        ],
    )
    def test_malformed_targets(self, text: str, message: str) -> None:
        with pytest.raises(OutputTargetError, match=message):
            parse_target(text, {"kafka"})


class TestFormats:
    def test_names_and_extensions(self) -> None:
        assert [(f.name, f.extension) for f in FORMATS] == [
            ("jsonl", ".jsonl"),
            ("csv", ".csv"),
            ("tsv", ".tsv"),
            ("json", ".json"),
            ("pretty", ".txt"),
        ]

    def test_json_lines_pretty_and_array(self) -> None:
        document = {"source": "s", "received_at": 1.5, "payload": {"a": "ñ", "b": {"c": 1}}}
        assert encode(JsonLinesFormat(), [EVENT]) == json.dumps(document, ensure_ascii=False) + "\n"
        assert encode(PrettyJsonFormat(), [EVENT, EVENT]) == (json.dumps(document, ensure_ascii=False, indent=2) + "\n") * 2
        assert json.loads(encode(JsonArrayFormat(), [EVENT, EVENT])) == [document, document]
        assert encode(JsonArrayFormat(), []) == "[]\n"
        assert encode(JsonLinesFormat(), []) == ""

    def test_csv_header_from_the_first_event_and_later_fields_in_extra(self) -> None:
        events = [
            Event("s", 1.5, {"a": 1, "b": {"c": "x,y"}, "n": None}),
            Event("s", 2.0, {"a": True, "d": [1, 2], "e": {}, "f": 0.25}),
        ]
        rows = list(csv.reader(io.StringIO(encode(CsvFormat(), events))))
        assert rows == [
            ["source", "received_at", "payload.a", "payload.b.c", "payload.n", EXTRA],
            ["s", "1.5", "1", "x,y", "", ""],
            ["s", "2.0", "true", "", "", '{"payload.d": [1, 2], "payload.e": {}, "payload.f": 0.25}'],
        ]
        assert encode(CsvFormat(), []) == ""

    def test_tsv_uses_tabs(self) -> None:
        assert encode(TsvFormat(), [EVENT]).splitlines() == ["source\treceived_at\tpayload.a\tpayload.b.c\textra", "s\t1.5\tñ\t1\t"]

    @pytest.mark.parametrize("source_id", WITH_FIXTURES)
    def test_every_format_round_trips_the_real_payloads_of_every_source(self, source_id: str) -> None:
        events = real_events(source_id)
        documents = [plain(event_document(e)) for e in events]
        assert [json.loads(line) for line in encode(JsonLinesFormat(), events).splitlines()] == documents
        assert json.loads(encode(JsonArrayFormat(), events)) == documents
        text, decoder, pretty, at = encode(PrettyJsonFormat(), events), json.JSONDecoder(), [], 0
        while at < len(text):
            document, at = decoder.raw_decode(text, at)
            pretty.append(document)
            at += 1
        assert pretty == documents
        for event_format, delimiter in ((CsvFormat(), ","), (TsvFormat(), "\t")):
            header, *rows = list(csv.reader(io.StringIO(encode(event_format, events)), delimiter=delimiter))
            assert header[-1] == EXTRA and len(rows) == len(events)
            for event, row in zip(events, rows, strict=True):
                expected = flatten(event_document(event))
                assert row[:-1] == [DelimitedEncoder._cell(expected.get(column)) for column in header[:-1]]
                assert (json.loads(row[-1]) if row[-1] else {}) == plain({k: v for k, v in expected.items() if k not in header})


class FlushRecorder(BatchingEventSink):
    def __init__(self, clock: FakeClock, batch_size: int = 3, max_delay_s: float = 1.0, fail: bool = False) -> None:
        super().__init__(clock, "recorder", batch_size, max_delay_s)
        self.batches: list[list[str]] = []
        self.calls: list[str] = []
        self.fail = fail

    async def _connect(self) -> None:
        self.calls.append("connect")

    async def _flush(self, events: Sequence[Event]) -> None:
        if self.fail:
            raise ConnectionError("down")
        self.batches.append([str(e.payload["n"]) for e in events])

    async def _disconnect(self) -> None:
        self.calls.append("disconnect")


def numbered(n: int) -> Event:
    return Event("s", float(n), {"n": n})


class TestSinks:
    async def test_null_sink_discards(self) -> None:
        sink = NullEventSink()
        await sink.open()
        await sink.write(EVENT)
        await sink.close()

    async def test_text_stream_sink_writes_the_format_and_leaves_the_stream_open(self) -> None:
        stream = io.StringIO()
        sink = TextStreamEventSink(stream, JsonArrayFormat())
        await sink.open()
        await sink.write(EVENT)
        await sink.close()
        assert json.loads(stream.getvalue())[0]["payload"] == {"a": "ñ", "b": {"c": 1}} and not stream.closed

    @pytest.mark.parametrize("flush_each", [True, False])
    async def test_text_stream_sink_hands_each_event_on_at_once_only_when_asked(self, flush_each: bool) -> None:
        class CountingStream(io.StringIO):
            flushes = 0

            def flush(self) -> None:
                self.flushes += 1
                super().flush()

        stream = CountingStream()
        sink = TextStreamEventSink(stream, JsonLinesFormat(), flush_each=flush_each)
        await sink.write(EVENT)
        await sink.write(EVENT)
        assert stream.flushes == (2 if flush_each else 0)
        await sink.close()
        assert stream.flushes == (3 if flush_each else 1)

    async def test_text_file_sink_creates_directories_on_open_and_keeps_line_ends(self, tmp_path: Path) -> None:
        path = tmp_path / "x" / "s.csv"
        sink = TextFileEventSink(path, CsvFormat())
        assert not path.parent.exists()
        await sink.open()
        await sink.write(Event("s", 1.0, {"text": "two\nlines"}))
        await sink.close()
        assert path.read_bytes() == b'source,received_at,payload.text,extra\ns,1.0,"two\nlines",\n'

    async def test_factory_names_files_after_the_source_and_the_format(self, tmp_path: Path) -> None:
        for event_format in FORMATS:
            sink = TextFileSinkFactory(tmp_path, event_format).create("abc")
            await sink.open()
            await sink.close()
            assert (tmp_path / f"abc{event_format.extension}").exists()


class TestBatching:
    def test_rejects_bad_limits(self) -> None:
        with pytest.raises(ValueError, match="batch_size"):
            FlushRecorder(FakeClock(), batch_size=0)
        with pytest.raises(ValueError, match="max_delay_s"):
            FlushRecorder(FakeClock(), max_delay_s=0)

    async def test_flushes_by_size_then_the_rest_on_close(self) -> None:
        sink = FlushRecorder(FakeClock(), batch_size=3, max_delay_s=1000)
        await sink.open()
        for n in range(7):
            await sink.write(numbered(n))
        assert sink.batches == [["0", "1", "2"], ["3", "4", "5"]]
        await sink.close()
        assert sink.batches[-1] == ["6"] and sink.calls == ["connect", "disconnect"]

    async def test_flushes_on_write_once_the_oldest_event_is_due(self) -> None:
        clock = FakeClock()
        sink = FlushRecorder(clock, batch_size=100, max_delay_s=1.0)
        await sink.write(numbered(1))
        clock.advance(0.5)
        await sink.write(numbered(2))
        assert sink.batches == []
        clock.advance(0.5)
        await sink.write(numbered(3))
        assert sink.batches == [["1", "2", "3"]]
        await sink.close()  # never opened: no timer to stop, nothing left to flush
        assert sink.batches == [["1", "2", "3"]] and sink.calls == ["disconnect"]

    async def test_the_timer_flushes_a_quiet_buffer(self) -> None:
        clock = FakeClock()
        sink = FlushRecorder(clock, batch_size=100, max_delay_s=1.0)
        await sink.open()
        await sink.write(numbered(1))
        for _ in range(5):
            await asyncio.sleep(0)
        assert sink.batches == [["1"]]
        await sink.close()
        assert sink.batches == [["1"]]

    async def test_a_failed_timed_flush_is_raised_by_the_next_write_and_by_close(self) -> None:
        clock = FakeClock()
        sink = FlushRecorder(clock, batch_size=100, max_delay_s=1.0, fail=True)
        await sink.open()
        await sink.write(numbered(1))
        for _ in range(5):
            await asyncio.sleep(0)
        with pytest.raises(OutputError, match=r"^output recorder failed: ConnectionError: down$"):
            await sink.write(numbered(2))
        with pytest.raises(OutputError, match="ConnectionError: down"):
            await sink.close()
        assert sink.calls == ["connect", "disconnect"]

    async def test_close_disconnects_even_when_the_last_flush_fails(self) -> None:
        sink = FlushRecorder(FakeClock(), batch_size=100, max_delay_s=1000, fail=True)
        await sink.open()
        await sink.write(numbered(1))
        with pytest.raises(OutputError) as error:
            await sink.close()
        assert sink.calls == ["connect", "disconnect"] and isinstance(error.value.__cause__, ConnectionError)
        assert error.value.output == "recorder"

    async def test_a_failed_connection_is_an_output_error_and_starts_no_timer(self) -> None:
        sink = FlushRecorder(FakeClock(), fail=True)

        async def refuse() -> None:
            raise ConnectionRefusedError("no server")

        sink._connect = refuse  # type: ignore[method-assign]
        with pytest.raises(OutputError, match=r"^output recorder failed: ConnectionRefusedError: no server$"):
            await sink.open()
        assert sink._timer is None


def rows(path: Path, table: str) -> list[tuple[float, object]]:
    with contextlib.closing(sqlite3.connect(path)) as db:
        return [(t, json.loads(p)) for t, p in db.execute(f'SELECT received_at, payload FROM "{table}" ORDER BY seq')]


class TestSqlite:
    async def test_one_table_per_source_in_arrival_order(self, tmp_path: Path) -> None:
        path = tmp_path / "db" / "events.db"
        sink = SqliteEventSink(path, FakeClock(), batch_size=2)
        await sink.open()
        for event in (Event("a", 1.0, {"n": 1}), Event('we"ird', 2.0, {"n": 2}), Event("a", 3.0, {"n": 3, "t": "ñ"})):
            await sink.write(event)
        await sink.close()
        assert rows(path, "a") == [(1.0, {"n": 1}), (3.0, {"n": 3, "t": "ñ"})]
        assert rows(path, 'we""ird') == [(2.0, {"n": 2})]

    async def test_appends_to_an_existing_file_and_answers_json_queries(self, tmp_path: Path) -> None:
        path = tmp_path / "events.db"
        for n in (1, 2):
            sink = SqliteEventSink(path, FakeClock())
            await sink.open()
            await sink.write(Event("a", float(n), {"price": {"usd": n * 10}}))
            await sink.close()
        with contextlib.closing(sqlite3.connect(path)) as db:
            assert db.execute("SELECT payload ->> '$.price.usd' FROM a ORDER BY seq").fetchall() == [(10,), (20,)]

    async def test_close_without_open_does_nothing(self, tmp_path: Path) -> None:
        await SqliteEventSink(tmp_path / "never.db", FakeClock()).close()
        assert not (tmp_path / "never.db").exists()

    @pytest.mark.parametrize("source_id", WITH_FIXTURES)
    async def test_stores_the_real_payloads_of_every_source(self, source_id: str, tmp_path: Path) -> None:
        events = real_events(source_id)
        sink = SqliteEventSink(tmp_path / "e.db", FakeClock())
        await sink.open()
        for event in events:
            await sink.write(event)
        await sink.close()
        assert rows(tmp_path / "e.db", source_id) == [(e.received_at, plain(e.payload)) for e in events]


class TestDatabaseRules:
    def test_integers_outside_64_bits_become_text_everything_else_is_kept(self) -> None:
        from stream_consumers.domain.outputs import storable

        value = {"a": [2**63, 2**63 - 1, -(2**63), -(2**63) - 1], "b": (True, 1.5, None, "x"), "c": {"d": 10**30}}
        assert storable(value) == {
            "a": [str(2**63), 2**63 - 1, -(2**63), str(-(2**63) - 1)],
            "b": [True, 1.5, None, "x"],
            "c": {"d": str(10**30)},
        }
        assert all(storable(e.payload) == e.payload for s in WITH_FIXTURES for e in real_events(s))  # no captured payload needs it

    def test_a_password_from_elsewhere_is_marked_and_never_shown(self) -> None:
        target = parse_target("cassandra://ana@c:9042", {"cassandra"})
        assert target.with_password(None) is target
        given = target.with_password("s3cret")
        assert (given.password, given.password_from_env, given.display) == ("s3cret", True, "cassandra://ana@c:9042")
        assert parse_target("cassandra://ana:pw@c", {"cassandra"}).password_from_env is False

    def test_cassandra_nodes_are_reached_at_the_host_given_for_their_port(self) -> None:
        from cassandra.cluster import Cluster
        from cassandra.connection import DefaultEndPoint

        from stream_consumers.adapters.outbound.outputs.databases import PortMappedEndPointFactory

        factory = PortMappedEndPointFactory({9041: "127.0.0.1", 9043: "lab.example"})
        Cluster(contact_points=[DefaultEndPoint("127.0.0.1", 9041)], endpoint_factory=factory)  # configures it; connects nowhere
        mapped = factory.create({"native_port": 9043, "rpc_address": "172.20.0.4", "peer": "172.20.0.4"})
        assert mapped == DefaultEndPoint("lab.example", 9043)
        unmapped = factory.create({"native_port": 9050, "rpc_address": "10.0.0.7", "peer": "10.0.0.7"})
        assert (unmapped.address, unmapped.port) == ("10.0.0.7", 9050)
