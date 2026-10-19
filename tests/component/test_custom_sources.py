"""Sources with their own fetching logic, fed with captured provider answers (fake HTTP port, virtual time)."""

from __future__ import annotations

import asyncio
import base64
import datetime as dt
import gzip
import io
import json
import zipfile
from collections.abc import Mapping

import pytest
import websockets
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from stream_consumers.adapters.outbound.providers.sources import FACTORIES
from stream_consumers.adapters.outbound.providers.sources.ct import CtEntryDecoder, CtLogPollSource
from stream_consumers.adapters.outbound.providers.sources.firms import FirmsFactory
from stream_consumers.adapters.outbound.providers.sources.gdelt import GDELT_EVENT_FIELDS, GdeltExportDecoder
from stream_consumers.adapters.outbound.providers.sources.polymarket import PolymarketDecoder, PolymarketSource
from stream_consumers.adapters.outbound.providers.sources.seedlink import MiniSeedHeaderDecoder, SeedLinkSource
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import PublishedVolume, RawMessage
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import EventSourcePort, HttpResponse
from tests.servers import tcp_server, ws_server
from tests.support import FakeClock, FakeHttp, deps, descriptor, messages, ok

BY_ID = {f.descriptor.id: f for f in FACTORIES}
FAST = Backoff(initial_s=0.01, factor=1, max_s=0.01, max_attempts=2)
CAPTURE_TIME = 1_791_875_000.0  # 2026-10-13T07:03:20Z, when the fixtures were captured


def body(source_id: str, index: int = 0) -> bytes:
    raw = messages(source_id)[index].body
    return raw if isinstance(raw, bytes) else raw.encode()


async def take(source: EventSourcePort, n: int) -> list[Mapping[str, object]]:
    out: list[Mapping[str, object]] = []
    stream = source.events()
    try:
        async with asyncio.timeout(10):
            async for event in stream:
                out.append(event)
                if len(out) >= n:
                    break
    finally:
        await stream.aclose()
    return out


async def through_file(source: EventSourcePort, n: int) -> list[Mapping[str, object]]:
    """Takes `n` events, then asks for one more so the source finishes the file (and records its volume)."""
    out: list[Mapping[str, object]] = []
    stream = source.events()
    try:
        async with asyncio.timeout(10):
            for _ in range(n):
                out.append(await anext(stream))
        try:
            async with asyncio.timeout(0.2):
                await anext(stream)
        except (TimeoutError, TransportError):
            pass
    finally:
        await stream.aclose()
    return out


async def failure(source: EventSourcePort) -> BaseException:
    stream = source.events()
    try:
        async with asyncio.timeout(10):
            async for _ in stream:
                pass
    except (TransportError, DecodeError) as exc:
        return exc
    finally:
        await stream.aclose()
    raise AssertionError("no failure")


def build(source_id: str, http: FakeHttp, clock: FakeClock, **secrets: str) -> EventSourcePort:
    source = BY_ID[source_id].create(deps(http=http, clock=clock, secrets=secrets))
    if hasattr(source, "_backoff"):
        source._backoff = FAST  # type: ignore[attr-defined]
    return source


class TestNpm:
    async def test_follows_the_changes_feed_from_the_current_sequence(self) -> None:
        changes = json.loads(body("npm"))
        http = FakeHttp(
            {
                "https://replicate.npmjs.com/registry/": ok({"update_seq": "100-abc"}),
                "https://replicate.npmjs.com/registry/_changes?since=100&limit=10000": ok(changes),
                f"https://replicate.npmjs.com/registry/_changes?since={changes['last_seq']}&limit=10000": ok(
                    {"results": [], "last_seq": changes["last_seq"]}
                ),
            }
        )
        source = build("npm", http, FakeClock())
        events = await take(source, 3)
        assert [e["id"] for e in events] == [r["id"] for r in changes["results"]]
        assert source.published_volume() is None

    async def test_an_answer_without_last_seq_fails(self) -> None:
        http = FakeHttp(
            {
                "https://replicate.npmjs.com/registry/": ok({"update_seq": 1}),
                "https://replicate.npmjs.com/registry/_changes?since=1&limit=10000": ok({"results": []}),
            }
        )
        assert "last_seq" in str((await failure(build("npm", http, FakeClock()))).__cause__)


class TestCrossref:
    async def test_polls_today_and_measures_yesterday(self) -> None:
        clock = FakeClock()  # 2023-11-14
        works = "https://api.crossref.org/works?filter=from-index-date:2023-11-14&sort=indexed&order=desc&rows=1000&mailto=a%40b.org"
        count = "https://api.crossref.org/works?filter=from-index-date:2023-11-13,until-index-date:2023-11-13&rows=0&mailto=a%40b.org"
        http = FakeHttp({works: ok(body("crossref")), count: ok({"message": {"total-results": 172800}})})
        source = build("crossref", http, clock, CROSSREF_MAILTO="a@b.org")
        assert len(await take(source, 3)) == 3
        assert source.published_volume() == PublishedVolume(172800, 86400.0)
        assert await source._poll_once() == []  # type: ignore[attr-defined]
        assert sum(1 for c in http.calls if c[1] == count) == 1

    async def test_without_contact_no_mailto(self) -> None:
        clock = FakeClock()
        works = "https://api.crossref.org/works?filter=from-index-date:2023-11-14&sort=indexed&order=desc&rows=1000"
        count = "https://api.crossref.org/works?filter=from-index-date:2023-11-13,until-index-date:2023-11-13&rows=0"
        http = FakeHttp({works: ok(body("crossref")), count: ok({"message": {"total-results": 1}})})
        assert len(await take(build("crossref", http, clock), 1)) == 1


class TestSnapshotVolumes:
    async def test_metar_counts_observations_of_the_last_hour(self) -> None:
        url = "https://aviationweather.gov/data/cache/metars.cache.csv.gz"
        source = build("metar", FakeHttp({url: ok(body("metar"))}), FakeClock(start=CAPTURE_TIME))
        events = await take(source, 3)
        assert all(e["station_id"] for e in events) and "sky_cover_2" in events[0]
        volume = source.published_volume()
        assert volume is not None and volume.period_s == 3600.0 and 0 <= volume.events <= 3

    async def test_metar_skips_unparsable_times(self) -> None:
        csv_body = gzip.compress(
            b"raw_text,station_id,observation_time\nX,AAAA,2026-10-13T07:00:00Z\nY,BBBB,garbage\nZ,CCCC,2026-10-13T01:00:00Z\n"
        )
        url = "https://aviationweather.gov/data/cache/metars.cache.csv.gz"
        source = build("metar", FakeHttp({url: ok(csv_body)}), FakeClock(start=dt.datetime(2026, 10, 13, 7, 30, tzinfo=dt.UTC).timestamp()))
        await take(source, 3)
        assert source.published_volume() == PublishedVolume(1, 3600.0)

    @pytest.mark.parametrize(
        "source_id, url, period",
        [
            ("usgs_water", "https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H&siteStatus=active", 3600.0),
            ("sensorcomm", "https://data.sensor.community/static/v2/data.json", 300.0),
        ],
    )
    async def test_snapshot_rows_over_the_stated_period(self, source_id: str, url: str, period: float) -> None:
        source = build(source_id, FakeHttp({url: ok(body(source_id))}), FakeClock())
        assert len(await take(source, 3)) == 3
        assert source.published_volume() == PublishedVolume(3, period)

    async def test_firms_reads_the_four_sensor_files(self) -> None:
        urls = FirmsFactory.URLS
        http = FakeHttp({u: ok(body("firms", i)) for i, u in enumerate(urls)})
        source = build("firms", http, FakeClock())
        events = await take(source, 12)
        assert {e["satellite"] for e in events} == {"N20", "N21", "N", "T"}
        assert source.published_volume() == PublishedVolume(12, 86400.0)


class TestGhArchive:
    URL = "https://data.gharchive.org/2026-10-13-5.json.gz"

    async def test_streams_the_newest_complete_hour(self) -> None:
        clock = FakeClock(start=dt.datetime(2026, 10, 13, 6, 30, tzinfo=dt.UTC).timestamp())
        source = build("gharchive", FakeHttp({self.URL: ok(body("gharchive"))}), clock)
        events = await through_file(source, 3)
        assert len(events) == 3 and all(e["type"] and e["actor"]["login"] == "<masked>" for e in events)  # type: ignore[index]
        assert source.published_volume() == PublishedVolume(3, 3600.0)

    async def test_a_last_line_without_newline_is_read(self) -> None:
        clock = FakeClock(start=dt.datetime(2026, 10, 13, 6, 30, tzinfo=dt.UTC).timestamp())
        source = build("gharchive", FakeHttp({self.URL: ok(gzip.compress(b'{"a": 1}\n\n{"b": 2}'))}), clock)
        assert await through_file(source, 2) == [{"a": 1}, {"b": 2}]
        assert source.published_volume() == PublishedVolume(2, 3600.0)

    async def test_corrupt_gzip_fails(self) -> None:
        clock = FakeClock(start=dt.datetime(2026, 10, 13, 6, 30, tzinfo=dt.UTC).timestamp())
        source = build("gharchive", FakeHttp({self.URL: ok(b"\x1f\x8b\x08\x00garbage-garbage")}), clock)
        assert isinstance(await failure(source), DecodeError)


class TestOsm:
    STATE = "https://planet.openstreetmap.org/replication/minute/state.txt"
    DIFF = "https://planet.openstreetmap.org/replication/minute/007/326/851.osc.gz"

    async def test_reads_the_newest_minute(self) -> None:
        source = build("osm", FakeHttp({self.STATE: ok(body("osm", 0)), self.DIFF: ok(body("osm", 1))}), FakeClock())
        events = await through_file(source, 5)
        assert source.published_volume() == PublishedVolume(5, 60.0)
        assert {e["element"] for e in events} <= {"node", "way", "relation"} and events[0]["action"] == "create"
        assert events[0]["user"] == "<masked>" and events[0]["uid"] == "<masked>"

    async def test_missing_sequence_or_file_fails(self) -> None:
        assert "sequenceNumber" in str((await failure(build("osm", FakeHttp({self.STATE: ok("nothing")}), FakeClock()))).__cause__)
        error = await failure(build("osm", FakeHttp({self.STATE: ok(body("osm", 0))}), FakeClock()))
        assert "HTTP 404" in str(error)


class TestGdelt:
    INDEX = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    EXPORT = "http://data.gdeltproject.org/gdeltv2/20261013071500.export.CSV.zip"

    async def test_reads_the_newest_export_with_codebook_names(self) -> None:
        source = build("gdelt", FakeHttp({self.INDEX: ok(body("gdelt", 0)), self.EXPORT: ok(body("gdelt", 1))}), FakeClock())
        events = await through_file(source, 3)
        assert len(GDELT_EVENT_FIELDS) == 61 and list(events[0]) == list(GDELT_EVENT_FIELDS)
        assert source.published_volume() == PublishedVolume(3, 900.0)

    async def test_failures(self) -> None:
        assert "no event export" in str(
            (await failure(build("gdelt", FakeHttp({self.INDEX: ok("1 2 x.mentions.CSV.zip")}), FakeClock()))).__cause__
        )
        assert "HTTP 404" in str(await failure(build("gdelt", FakeHttp({self.INDEX: ok(body("gdelt", 0))}), FakeClock())))
        with pytest.raises(DecodeError):
            GdeltExportDecoder().decode(RawMessage(b"not a zip"))
        empty = io.BytesIO()
        zipfile.ZipFile(empty, "w").close()
        with pytest.raises(DecodeError):
            GdeltExportDecoder().decode(RawMessage(empty.getvalue()))


class TestCertificateTransparency:
    LIST = "https://www.gstatic.com/ct/log_list/v3/log_list.json"
    LOG = "https://ct.googleapis.com/logs/us1/argon2026h2"

    def sth(self, size: int) -> HttpResponse:
        return ok({"tree_size": size})

    async def test_reads_new_entries_and_measures_tree_growth(self) -> None:
        clock = FakeClock(start=CAPTURE_TIME)
        entries = json.loads(body("ct", 2))
        http = FakeHttp(
            {
                self.LIST: ok(body("ct", 0)),
                f"{self.LOG}/ct/v1/get-sth": [self.sth(1000), self.sth(1003), self.sth(1003)],
                f"{self.LOG}/ct/v1/get-entries?start=1000&end=1002": ok(entries),
            }
        )
        source = build("ct", http, clock)
        assert source.published_volume() == PublishedVolume(0, 0.0)
        events = await take(source, 3)
        assert [e["index"] for e in events] == [1000, 1001, 1002]
        assert {e["entry_type"] for e in events} == {"x509", "precert"} and all(e["san_count"] >= 0 for e in events)
        assert source.published_volume() == PublishedVolume(3, 10.0)

    async def test_a_log_growing_too_fast_is_skipped_ahead_and_empty_answers_stop(self) -> None:
        clock = FakeClock()
        http = FakeHttp(
            {
                f"{self.LOG}/ct/v1/get-sth": [self.sth(0), self.sth(10_000)],
                f"{self.LOG}/ct/v1/get-entries?start=8976&end=9231": ok({"entries": []}),
            }
        )
        log = CtLogPollSource(descriptor(), CtEntryDecoder("L"), clock, http, self.LOG + "/")
        assert log.published_volume() == PublishedVolume(0, 0.0)
        await log._fetch()
        assert await log._fetch() == []
        assert log.published_volume() == PublishedVolume(10_000, 0.0)

    async def test_failures(self) -> None:
        clock = FakeClock(start=CAPTURE_TIME)
        no_list = build("ct", FakeHttp(), clock)
        assert "HTTP 404" in str((await failure(no_list)).__cause__)
        old = build("ct", FakeHttp({self.LIST: ok(body("ct", 0))}), FakeClock(start=0.0))
        assert "no usable" in str((await failure(old)).__cause__)
        log = CtLogPollSource(descriptor(), CtEntryDecoder("L"), clock, FakeHttp(), self.LOG, backoff=FAST)
        with pytest.raises(TransportError):
            await log._fetch()

    def test_decoder_handles_both_entry_types_and_rejects_garbage(self) -> None:
        decoder = CtEntryDecoder("L")
        precert = json.loads(body("ct", 2))["entries"][0]
        extra = base64.b64decode(precert["extra_data"])
        der = extra[3 : 3 + int.from_bytes(extra[0:3], "big")]
        leaf = bytes(2) + (123).to_bytes(8, "big") + (0).to_bytes(2, "big") + len(der).to_bytes(3, "big") + der
        (event,) = decoder.decode(RawMessage(json.dumps({"entries": [{"leaf_input": base64.b64encode(leaf).decode(), "extra_data": ""}]})))
        assert event["entry_type"] == "x509" and event["timestamp_ms"] == 123 and event["index"] == 0
        with pytest.raises(DecodeError):
            decoder.decode(RawMessage(json.dumps({"entries": [{"leaf_input": "AAAA"}]})))
        assert decoder.decode(RawMessage(json.dumps({"other": 1}))) == []

    def test_certificate_without_names(self) -> None:
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "t")])
        now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(1)
            .not_valid_before(now)
            .not_valid_after(now + dt.timedelta(days=1))
            .sign(key, hashes.SHA256())
        )
        der = cert.public_bytes(serialization.Encoding.DER)
        leaf = bytes(2) + bytes(8) + bytes(2) + len(der).to_bytes(3, "big") + der
        (event,) = CtEntryDecoder("L").decode(
            RawMessage(json.dumps({"entries": [{"leaf_input": base64.b64encode(leaf).decode(), "extra_data": ""}]}))
        )
        assert event["san_count"] == 0 and event["san_first"] is None and event["issuer_o"] is None and event["key_size"] == 256


class TestPolymarket:
    async def test_subscribes_to_the_most_traded_markets(self) -> None:
        received: list[object] = []

        async def handler(ws: websockets.ServerConnection) -> None:
            received.append(json.loads(await ws.recv()))
            await ws.send(json.dumps({"event_type": "last_trade_price", "price": "0.5"}))
            await ws.wait_closed()

        gamma = PolymarketSource.MARKETS_URL.format(limit=2)
        http = FakeHttp({gamma: ok([{"clobTokenIds": '["a", "b"]'}, {"clobTokenIds": None}])})
        async with ws_server(handler) as url:
            source = PolymarketSource(descriptor(), PolymarketDecoder(), SystemClock(), http, url, markets=2)
            assert await take(source, 1) == [{"event_type": "last_trade_price", "price": "0.5"}]
        assert received == [{"assets_ids": ["a", "b"], "type": "market"}]

    async def test_gamma_failure_fails(self) -> None:
        async def handler(ws: websockets.ServerConnection) -> None:
            await ws.wait_closed()

        async with ws_server(handler) as url:
            source = PolymarketSource(descriptor(), PolymarketDecoder(), SystemClock(), FakeHttp(), url, backoff=FAST)
            assert "Gamma API HTTP 404" in str((await failure(source)).__cause__)


class TestSeedLink:
    async def test_handshake_then_packets(self) -> None:
        commands: list[str] = []
        packets = [body("seedlink", i) for i in range(2)]

        async def server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            while (line := (await reader.readline()).decode().strip()) != "END":
                commands.append(line)
                writer.write(b"SeedLink v3.1\r\nTest DMC\r\n" if line == "HELLO" else b"OK\r\n")
            for packet in packets:
                writer.write(packet)
            await writer.drain()
            await reader.read()

        async with tcp_server(server) as port:
            source = SeedLinkSource(descriptor(), MiniSeedHeaderDecoder(), SystemClock(), "127.0.0.1", port, [("IU", "ANMO")], "BHZ")
            events = await take(source, 2)
        assert commands == ["HELLO", "STATION ANMO IU", "SELECT BHZ", "DATA"]
        assert all(e["network"] == "IU" for e in events)

    async def test_refused_station_fails(self) -> None:
        async def server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            while line := (await reader.readline()).decode().strip():
                writer.write(b"a\r\nb\r\n" if line == "HELLO" else b"ERROR\r\n")

        async with tcp_server(server) as port:
            source = SeedLinkSource(
                descriptor(), MiniSeedHeaderDecoder(), SystemClock(), "127.0.0.1", port, [("XX", "NONE")], "BHZ", backoff=FAST
            )
            assert "refused" in str((await failure(source)).__cause__)
