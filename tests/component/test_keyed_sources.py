"""Key-gated sources and their infrastructure: Kafka against a real broker, OAuth, and the
providers whose request URLs depend on time or on a first lookup."""

from __future__ import annotations

import asyncio
import io
import json
from collections.abc import Mapping

import fastavro
import pytest
from aiohttp import web
from google.protobuf.json_format import MessageToJson
from google.transit import gtfs_realtime_pb2

from stream_consumers.adapters.outbound.auth import OAuthClientCredentials
from stream_consumers.adapters.outbound.decoders import AvroSchemaInKeyDecoder, GtfsRealtimeDecoder, JsonDecoder
from stream_consumers.adapters.outbound.http import AiohttpClient
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.sources.cta_bus import CtaBusDecoder, CtaBusSource
from stream_consumers.adapters.outbound.sources.mastodon import MastodonSource, MastodonStreamDecoder
from stream_consumers.adapters.outbound.sources.wmata import FeedTaggedGtfsRealtimeDecoder
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.transports.kafka import KafkaSource
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import RawMessage
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound import EventSourcePort, HttpResponse
from tests.servers import http_server, kafka_broker, kafka_produce
from tests.support import FakeClock, FakeHttp, deps, descriptor, messages, ok

FAST = Backoff(initial_s=0.01, factor=1, max_s=0.01, max_attempts=2)
D = descriptor()
BY_ID = {f.descriptor.id: f for f in FACTORIES}


async def take(source: EventSourcePort, n: int, timeout: float = 30.0) -> list[Mapping[str, object]]:
    out: list[Mapping[str, object]] = []
    stream = source.events()
    try:
        async with asyncio.timeout(timeout):
            async for event in stream:
                out.append(event)
                if len(out) >= n:
                    break
    finally:
        await stream.aclose()
    return out


# ------------------------------------------------------------------ Kafka, against a real broker
AVRO_SCHEMA = {
    "type": "record",
    "name": "alert",
    "fields": [
        {"name": "objectId", "type": "string"},
        {"name": "candidate", "type": {"type": "record", "name": "c", "fields": [{"name": "magpsf", "type": "float"}]}},
        {"name": "cutouts", "type": {"type": "array", "items": "bytes"}},
        {"name": "flags", "type": {"type": "map", "values": "int"}},
    ],
}


def avro_value(record: Mapping[str, object]) -> bytes:
    buffer = io.BytesIO()
    fastavro.schemaless_writer(buffer, fastavro.parse_schema(AVRO_SCHEMA), record)
    return buffer.getvalue()


async def test_kafka_json_and_avro_messages_from_a_real_broker() -> None:
    async with kafka_broker() as bootstrap:
        await kafka_produce(bootstrap, "json_topic", [(None, b'{"diaObjectId": 1, "UTC": "2026-01-29 11:40:14"}'), (b"k", b'{"n": 2}')])
        record = {"objectId": "ZTF1", "candidate": {"magpsf": 18.5}, "cutouts": [b"\x00\x01"], "flags": {"a": 1}}
        await kafka_produce(bootstrap, "avro_topic", [(json.dumps(AVRO_SCHEMA).encode(), avro_value(record))])
        plain = KafkaSource(D, JsonDecoder(), FakeClock(), bootstrap, ["json_topic"], "g1", start_at="earliest")
        assert await take(plain, 2) == [{"diaObjectId": 1, "UTC": "2026-01-29 11:40:14"}, {"n": 2}]
        avro = KafkaSource(D, AvroSchemaInKeyDecoder(), FakeClock(), bootstrap, ["avro_topic"], "g2", start_at="earliest")
        assert await take(avro, 1) == [{"objectId": "ZTF1", "candidate": {"magpsf": 18.5}, "cutouts": ["AAE="], "flags": {"a": 1}}]


def test_kafka_source_rejects_bad_arguments() -> None:
    with pytest.raises(ValueError, match="topics"):
        KafkaSource(D, JsonDecoder(), FakeClock(), "h:1", [], "g")
    with pytest.raises(ValueError, match="start_at"):
        KafkaSource(D, JsonDecoder(), FakeClock(), "h:1", ["t"], "g", start_at="smallest")


# ------------------------------------------------------------------ Avro with the schema in the key
class TestAvroSchemaInKey:
    def test_schema_is_parsed_once_per_key(self) -> None:
        decoder = AvroSchemaInKeyDecoder()
        key = json.dumps(AVRO_SCHEMA)
        record = {"objectId": "a", "candidate": {"magpsf": 1.0}, "cutouts": [], "flags": {}}
        for _ in range(2):
            assert decoder.decode(RawMessage(avro_value(record), {"key": key})) == [record]
        assert list(decoder._schemas) == [key]

    def test_rejections(self) -> None:
        decoder = AvroSchemaInKeyDecoder()
        with pytest.raises(DecodeError, match="without a schema"):
            decoder.decode(RawMessage(b"\x00"))
        with pytest.raises(DecodeError, match="not an Avro schema"):
            decoder.decode(RawMessage(b"\x00", {"key": "{not json"}))
        with pytest.raises(DecodeError, match="not an Avro schema"):
            decoder.decode(RawMessage(b"\x00", {"key": '{"type": "record", "name": "x", "fields": [{"name": "a", "type": "nope"}]}'}))
        with pytest.raises(DecodeError, match="does not match"):
            decoder.decode(RawMessage(b"\x02", {"key": json.dumps(AVRO_SCHEMA)}))

    def test_a_non_record_schema_yields_no_event(self) -> None:
        buffer = io.BytesIO()
        fastavro.schemaless_writer(buffer, fastavro.parse_schema({"type": "string"}), "x")
        assert AvroSchemaInKeyDecoder().decode(RawMessage(buffer.getvalue(), {"key": '{"type": "string"}'})) == []


# ------------------------------------------------------------------ GTFS-Realtime as JSON, from a real captured feed
def test_gtfs_realtime_json_mapping_decodes_like_the_protobuf() -> None:
    (message,) = messages("mta_gtfsrt")
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(message.body)  # type: ignore[arg-type]
    decoder = GtfsRealtimeDecoder()
    expected = decoder.decode(message)
    assert decoder.decode(RawMessage(MessageToJson(feed))) == expected
    assert decoder.decode(RawMessage(MessageToJson(feed, preserving_proto_field_name=True))) == expected
    with pytest.raises(DecodeError, match="JSON feed"):
        decoder.decode(RawMessage('{"header": 5}'))
    tagged = FeedTaggedGtfsRealtimeDecoder("rail").decode(message)
    assert tagged == [dict(e, feed="rail") for e in expected]


# ------------------------------------------------------------------ OAuth 2 client credentials
TOKEN_URL = "https://auth.example/token"


class TestOAuthClientCredentials:
    async def test_requests_once_and_renews_before_expiry_or_after_invalidate(self) -> None:
        tokens = iter(["t1", "t2", "t3"])
        http = FakeHttp({TOKEN_URL: lambda url: ok({"access_token": next(tokens), "expires_in": 1800})})
        clock = FakeClock()
        auth = OAuthClientCredentials(http, clock, TOKEN_URL, "id", "secret")
        assert await auth.headers() == {"Authorization": "Bearer t1"}
        assert await auth.headers() == {"Authorization": "Bearer t1"}
        clock.advance(1800 - 60)
        assert await auth.headers() == {"Authorization": "Bearer t2"}
        auth.invalidate()
        assert await auth.headers() == {"Authorization": "Bearer t3"}
        assert http.calls[0] == ("FORM", TOKEN_URL, {"grant_type": "client_credentials", "client_id": "id", "client_secret": "secret"})
        assert len(http.calls) == 3

    async def test_lifetime_defaults_to_five_minutes(self) -> None:
        http = FakeHttp({TOKEN_URL: ok({"access_token": "t"})})
        clock = FakeClock()
        auth = OAuthClientCredentials(http, clock, TOKEN_URL, "i", "s", margin_s=0)
        await auth.headers()
        clock.advance(299)
        await auth.headers()
        clock.advance(1)
        await auth.headers()
        assert len(http.calls) == 2

    @pytest.mark.parametrize(
        ("response", "message"),
        [
            (ok({"error": "invalid_client"}, 401), "refused: HTTP 401"),
            (ok("not json"), "without access_token"),
            (ok({"token_type": "Bearer"}), "without access_token"),
            (ok({"access_token": "t", "expires_in": "soon"}), "without access_token"),
            (ok({"access_token": ""}), "empty access_token"),
        ],
    )
    async def test_rejected_or_malformed_token_responses(self, response: HttpResponse, message: str) -> None:
        auth = OAuthClientCredentials(FakeHttp({TOKEN_URL: response}), FakeClock(), TOKEN_URL, "i", "s")
        with pytest.raises(TransportError, match=message):
            await auth.headers()

    async def test_poll_source_sends_the_token_and_renews_it_after_401(self) -> None:
        tokens = iter(["old", "new"])
        data_url = "https://api.example/states"

        def data(url: str) -> HttpResponse:
            return ok({"states": [1]}) if http.calls[-1][2]["Authorization"] == "Bearer new" else ok("expired", 401)  # type: ignore[index]

        http = FakeHttp({TOKEN_URL: lambda url: ok({"access_token": next(tokens)}), data_url: data})
        auth = OAuthClientCredentials(http, FakeClock(), TOKEN_URL, "i", "s")
        source = HttpPollSource(D, JsonDecoder(), FakeClock(), http, [data_url], 1.0, headers={"X": "1"}, auth=auth, backoff=FAST)
        assert await take(source, 1) == [{"states": [1]}]
        gets = [c for c in http.calls if c[0] == "GET"]
        assert [c[2] for c in gets] == [{"X": "1", "Authorization": "Bearer old"}, {"X": "1", "Authorization": "Bearer new"}]


async def test_aiohttp_post_form_sends_urlencoded_fields() -> None:
    received: list[tuple[str, dict[str, str]]] = []

    async def token(request: web.Request) -> web.Response:
        received.append((request.content_type, dict(await request.post())))  # type: ignore[arg-type]
        return web.json_response({"access_token": "t"})

    async with http_server([web.post("/token", token)]) as base:
        client = AiohttpClient("tests/1.0")
        try:
            response = await client.post_form(f"{base}/token", {"grant_type": "client_credentials", "client_id": "a b"})
        finally:
            await client.close()
    assert response.status == 200 and json.loads(response.body) == {"access_token": "t"}
    assert received == [("application/x-www-form-urlencoded", {"grant_type": "client_credentials", "client_id": "a b"})]


# ------------------------------------------------------------------ CTA Bus Tracker: routes first, then vehicles
BUS = "https://www.ctabustracker.com/bustime/api/v3"


class TestCtaBus:
    async def test_routes_then_vehicles_in_batches_of_ten(self) -> None:
        routes_msg, vehicles_msg = messages("cta_bus")
        routes = json.loads(routes_msg.body)  # type: ignore[arg-type]
        routes["bustime-response"]["routes"] = [{"rt": str(n)} for n in range(1, 13)] + [{"rtnm": "no rt"}]
        http = FakeHttp(
            {
                f"{BUS}/getroutes?key=k&format=json": ok(routes),
                f"{BUS}/getvehicles?key=k&rt=1,2,3,4,5,6,7,8,9,10&tmres=s&format=json": ok(vehicles_msg.body),
                f"{BUS}/getvehicles?key=k&rt=11,12&tmres=s&format=json": ok(
                    {"bustime-response": {"error": [{"msg": "No data found for parameter"}]}}
                ),
            }
        )
        source = CtaBusSource(D, CtaBusDecoder(), FakeClock(), http, "k", 30.0, FAST)
        assert [e["vid"] for e in await take(source, 3)] == ["8678", "7963", "8683"]
        assert [c[1].split("/")[-1].split("?")[0] for c in http.calls] == ["getroutes", "getvehicles", "getvehicles"]
        assert len(await source._urls_for_poll()) == 2 and len(http.calls) == 3  # the route list is read once

    @pytest.mark.parametrize(
        "routes",
        [
            {"bustime-response": {"error": [{"msg": "Invalid API access key supplied"}]}},
            {"other": 1},
            {"bustime-response": {"routes": []}},
        ],
    )
    async def test_route_lookup_failures(self, routes: object) -> None:
        http = FakeHttp({f"{BUS}/getroutes?key=k&format=json": ok(routes)})
        source = CtaBusSource(D, CtaBusDecoder(), FakeClock(), http, "k", 30.0, FAST)
        with pytest.raises(TransportError, match="getroutes"):
            await take(source, 1)


# ------------------------------------------------------------------ request windows computed from the clock
async def test_entsoe_requests_the_last_six_hours_per_area() -> None:
    clock = FakeClock(start=1_760_356_800.0 + 25 * 60)  # 2025-10-13T12:25Z
    source = BY_ID["entsoe"].create(deps(clock=clock, secrets={"ENTSOE_TOKEN": "t", "ENTSOE_AREAS": "A, B"}))
    assert await source._urls_for_poll() == [  # type: ignore[attr-defined]
        "https://web-api.tp.entsoe.eu/api?securityToken=t&documentType=A75&processType=A16&in_Domain=A"
        "&periodStart=202510130700&periodEnd=202510131300",
        "https://web-api.tp.entsoe.eu/api?securityToken=t&documentType=A75&processType=A16&in_Domain=B"
        "&periodStart=202510130700&periodEnd=202510131300",
    ]


# ------------------------------------------------------------------ Mastodon: streaming host discovery, then SSE
INSTANCE = "https://example.social/api/v2/instance"
STREAM = "https://streaming.example.social/api/v1/streaming/public"


class TestMastodon:
    async def test_discovers_the_streaming_host_then_reads_events(self) -> None:
        update, delete = messages("mastodon")
        body = f"event: update\ndata: {update.body}\n\n:thump\n\nevent: delete\ndata: {delete.body}\n\n"
        http = FakeHttp({INSTANCE: ok({"configuration": {"urls": {"streaming": "wss://streaming.example.social/"}}}), STREAM: ok(body)})
        secrets = {"MASTODON_ACCESS_TOKEN": "tok", "MASTODON_INSTANCE": "example.social"}
        source = BY_ID["mastodon"].create(deps(http=http, secrets=secrets))
        events = await take(source, 2)
        assert [e["event_type"] for e in events] == ["update", "delete"]
        assert http.calls[1] == ("STREAM", STREAM, {"Accept": "text/event-stream", "Authorization": "Bearer tok"})

    async def test_reconnects_without_looking_the_host_up_again(self) -> None:
        (update, _) = messages("mastodon")
        http = FakeHttp(
            {
                INSTANCE: ok({"configuration": {"urls": {"streaming": "wss://streaming.example.social"}}}),
                STREAM: [ok(f"event: update\ndata: {update.body}\n\n"), ok("")],
            }
        )
        source = MastodonSource(D, MastodonStreamDecoder(), FakeClock(), http, "example.social", "t", FAST)
        stream = source.events()
        events = []
        with pytest.raises(TransportError, match="gave up after 2 retries"):
            async for event in stream:
                events.append(event)
        assert len(events) == 1 and [c[0] for c in http.calls] == ["GET", "STREAM", "STREAM", "STREAM"]

    async def test_plain_ws_streaming_url_becomes_http(self) -> None:
        http = FakeHttp({INSTANCE: ok({"configuration": {"urls": {"streaming": "ws://streaming.example.social"}}})})
        source = BY_ID["mastodon"].create(deps(http=http, secrets={"MASTODON_ACCESS_TOKEN": "t", "MASTODON_INSTANCE": "example.social"}))
        assert await source._streaming_url() == "http://streaming.example.social/api/v1/streaming/public"  # type: ignore[attr-defined]

    @pytest.mark.parametrize(("response", "message"), [(ok("down", 503), "HTTP 503"), (ok({"configuration": {}}), "urls.streaming")])
    async def test_discovery_failures(self, response: HttpResponse, message: str) -> None:
        source = BY_ID["mastodon"].create(
            deps(http=FakeHttp({INSTANCE: response}), secrets={"MASTODON_ACCESS_TOKEN": "t", "MASTODON_INSTANCE": "example.social"})
        )
        with pytest.raises(TransportError, match=message):
            await source._streaming_url()  # type: ignore[attr-defined]
