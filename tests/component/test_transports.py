"""Every transport against a local server that speaks its protocol."""

from __future__ import annotations

import asyncio
import gzip
import json
import socket
from collections.abc import AsyncGenerator, Mapping, Sequence

import pytest
import websockets
from aiohttp import web

from stream_consumers.adapters.outbound.providers.decoders import JsonDecoder, LineDecoder
from stream_consumers.adapters.outbound.providers.http import AiohttpClient
from stream_consumers.adapters.outbound.providers.transports.base import (
    FileDropSource,
    FileLocation,
    MergedEventSource,
    PushEventSource,
)
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.providers.transports.mqtt import MqttSource
from stream_consumers.adapters.outbound.providers.transports.nats import NatsSource
from stream_consumers.adapters.outbound.providers.transports.sse import SseSource
from stream_consumers.adapters.outbound.providers.transports.tcp import TcpLineSource, TcpRecordSource
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.adapters.outbound.providers.transports.zeromq import ZmqSubSource
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import PublishedVolume, RawMessage
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound.providers import EventSourcePort
from tests.servers import MqttBroker, NatsServer, http_server, tcp_server, ws_server, zmq_publisher
from tests.support import FakeClock, FakeHttp, ScriptedSource, descriptor, ok

FAST = Backoff(initial_s=0.01, factor=1, max_s=0.01, max_attempts=2)
D = descriptor()


async def take(source: EventSourcePort, n: int, timeout: float = 10.0) -> list[Mapping[str, object]]:
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


async def failure(source: EventSourcePort, timeout: float = 10.0) -> BaseException:
    stream = source.events()
    try:
        async with asyncio.timeout(timeout):
            async for _ in stream:
                pass
    except TransportError as exc:
        return exc
    finally:
        await stream.aclose()
    raise AssertionError("the source did not fail")


class Lines(LineDecoder):
    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        return {"line": line, **message.attributes}


class Raw(JsonDecoder):
    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        body = message.body
        return [{"bytes": body if isinstance(body, bytes) else body.encode(), **message.attributes}]


# ------------------------------------------------------------------ WebSocket
class TestWebSocket:
    async def test_subscribes_keeps_alive_replies_and_splits_lines(self) -> None:
        received: list[str] = []

        async def handler(ws: websockets.ServerConnection) -> None:
            received.append(str(ws.request.headers.get("User-Agent")))
            received.append(await ws.recv())  # type: ignore[arg-type]
            received.append(await ws.recv())  # type: ignore[arg-type]
            await ws.send("PING :tmi.twitch.tv\r\na\r\n\r\nb")
            received.append(await ws.recv())  # type: ignore[arg-type]  (PONG)
            received.append(await ws.recv())  # type: ignore[arg-type]  (keep-alive)
            await ws.send(b"c")
            await ws.wait_closed()

        async with ws_server(handler) as url:
            source = WebSocketSource(
                D,
                Lines(),
                SystemClock(),
                url,
                ["hello", {"op": "sub"}],
                headers={"User-Agent": "t"},
                keepalive={"op": "ping"},
                keepalive_s=0.05,
                replies={"PING": "PONG :tmi.twitch.tv"},
                split_lines=True,
            )
            events = await take(source, 3)
        assert [e["line"] for e in events] == ["a", "b", "c"]
        assert received == ["t", "hello", '{"op": "sub"}', "PONG :tmi.twitch.tv", '{"op": "ping"}']

    async def test_reconnects_after_the_server_closes_then_gives_up(self) -> None:
        connections = 0

        async def handler(ws: websockets.ServerConnection) -> None:
            nonlocal connections
            connections += 1
            if connections == 1:
                await ws.send('{"n": 1}')

        async with ws_server(handler) as url:
            source = WebSocketSource(D, JsonDecoder(), SystemClock(), url, backoff=FAST)
            events: list[Mapping[str, object]] = []
            stream = source.events()
            with pytest.raises(TransportError, match="gave up after 2 retries"):
                async for event in stream:
                    events.append(event)
        assert events == [{"n": 1}] and connections == 3

    async def test_unreachable_server_fails(self) -> None:
        source = WebSocketSource(D, JsonDecoder(), SystemClock(), "ws://127.0.0.1:9/", open_timeout_s=1, backoff=FAST)
        assert "gave up" in str(await failure(source))
        assert source.published_volume() is None


class Once(PushEventSource):
    """A connection that delivers one message and then ends normally."""

    def __init__(self) -> None:
        super().__init__(D, JsonDecoder(), FakeClock(), FAST)
        self.connections = 0

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        self.connections += 1
        if self.connections == 1:
            yield RawMessage('{"n": 1}')


async def test_a_connection_that_ends_is_reopened_until_the_back_off_gives_up() -> None:
    source = Once()
    events: list[Mapping[str, object]] = []
    with pytest.raises(TransportError, match="connection closed by the provider"):
        async for event in source.events():
            events.append(event)
    assert events == [{"n": 1}] and source.connections == 3


# ------------------------------------------------------------------ SSE over the aiohttp client
class TestSse:
    async def test_events_types_comments_and_multiline_data(self) -> None:
        async def stream(request: web.Request) -> web.StreamResponse:
            assert request.headers["Accept"] == "text/event-stream" and request.headers["X-T"] == "1"
            response = web.StreamResponse()
            await response.prepare(request)
            for chunk in (
                b": comment\n",
                b'event: skip\ndata: {"no": 1}\n\n',
                b'data: {"a":\ndata: 1}\n\n',
                b'id: 7\nevent: keep\r\ndata:{"b": 2}\r\n\r\n',
                b"event: keep\n\n",
            ):
                await response.write(chunk)
            await asyncio.sleep(1)
            return response

        async with http_server([web.get("/s", stream)]) as base:
            http = AiohttpClient("t")
            try:
                source = SseSource(
                    D, Raw(), SystemClock(), http, base + "/s", headers={"X-T": "1"}, event_types=frozenset({"message", "keep"})
                )
                events = await take(source, 2)
            finally:
                await http.close()
        assert [json.loads(e["bytes"]) for e in events] == [{"a": 1}, {"b": 2}]
        assert [e["event"] for e in events] == ["message", "keep"]

    async def test_without_a_filter_every_event_counts(self) -> None:
        async def stream(request: web.Request) -> web.StreamResponse:
            response = web.StreamResponse()
            await response.prepare(request)
            await response.write(b"event: x\ndata: {}\n\n")
            await asyncio.sleep(1)
            return response

        async with http_server([web.get("/s", stream)]) as base:
            http = AiohttpClient("t")
            try:
                assert len(await take(SseSource(D, JsonDecoder(), SystemClock(), http, base + "/s"), 1)) == 1
            finally:
                await http.close()

    async def test_a_stream_that_ends_is_reopened(self) -> None:
        async def short(request: web.Request) -> web.StreamResponse:
            response = web.StreamResponse()
            await response.prepare(request)
            await response.write(b'data: {"a": 1}\n\n')
            await response.write(b'data: {"a": 2}\n\n')
            return response

        async with http_server([web.get("/s", short)]) as base:
            http = AiohttpClient("t")
            try:
                events = await take(SseSource(D, JsonDecoder(), SystemClock(), http, base + "/s", backoff=FAST), 4)
            finally:
                await http.close()
        assert events == [{"a": 1}, {"a": 2}, {"a": 1}, {"a": 2}]

    async def test_non_200_is_retried_then_fails(self) -> None:
        async def refuse(request: web.Request) -> web.Response:
            return web.Response(status=406, text="no")

        async with http_server([web.get("/s", refuse)]) as base:
            http = AiohttpClient("t")
            try:
                error = await failure(SseSource(D, JsonDecoder(), SystemClock(), http, base + "/s", backoff=FAST))
            finally:
                await http.close()
        assert "HTTP 406" in str(error.__cause__)


class TestAiohttpClient:
    async def test_get_post_and_reopening_after_close(self) -> None:
        async def echo(request: web.Request) -> web.Response:
            body = await request.text()
            return web.json_response({"ua": request.headers["User-Agent"], "h": request.headers.get("X-H"), "body": body}, status=201)

        async with http_server([web.get("/e", echo), web.post("/e", echo)]) as base:
            http = AiohttpClient("agent/1")
            got = await http.get(base + "/e", {"X-H": "v"})
            posted = await http.post_json(base + "/e", {"q": 1})
            await http.close()
            await http.close()
            again = await http.get(base + "/e")
            await http.close()
        assert got.status == 201 and json.loads(got.body) == {"ua": "agent/1", "h": "v", "body": ""}
        assert json.loads(posted.body)["body"] == '{"q": 1}' and posted.headers["Content-Type"].startswith("application/json")
        assert again.status == 201

    async def test_stream_yields_the_whole_body(self) -> None:
        async def big(request: web.Request) -> web.Response:
            return web.Response(body=b"x" * 300_000)

        async with http_server([web.get("/b", big)]) as base:
            http = AiohttpClient("t")
            try:
                assert b"".join([c async for c in http.stream(base + "/b")]) == b"x" * 300_000
                with pytest.raises(TransportError, match="HTTP 404"):
                    [c async for c in http.stream(base + "/missing")]
            finally:
                await http.close()

    async def test_close_before_use(self) -> None:
        await AiohttpClient("t").close()

    async def test_a_slow_body_that_keeps_arriving_outlasts_the_wait_timeout(self) -> None:
        async def trickle(request: web.Request) -> web.StreamResponse:
            response = web.StreamResponse()
            await response.prepare(request)
            for _ in range(6):
                await response.write(b"x" * 10)
                await asyncio.sleep(0.1)
            await response.write_eof()
            return response

        async with http_server([web.get("/t", trickle)]) as base:
            http = AiohttpClient("t", timeout_s=0.4, total_s=5)
            try:
                got = await http.get(base + "/t")
            finally:
                await http.close()
        assert got.body == b"x" * 60

    @pytest.mark.parametrize(("timeout_s", "total_s"), [(0.2, 5.0), (5.0, 0.2)])
    async def test_a_stalled_body_or_an_overlong_transfer_times_out(self, timeout_s: float, total_s: float) -> None:
        async def stall(request: web.Request) -> web.StreamResponse:
            response = web.StreamResponse()
            await response.prepare(request)
            await response.write(b"x")
            await asyncio.sleep(2)
            return response

        async with http_server([web.get("/s", stall)]) as base:
            http = AiohttpClient("t", timeout_s=timeout_s, total_s=total_s)
            try:
                with pytest.raises(asyncio.TimeoutError):
                    await http.get(base + "/s")
            finally:
                await http.close()


# ------------------------------------------------------------------ MQTT
class TestMqtt:
    async def test_tcp_subscribe_and_receive_then_reconnect(self) -> None:
        broker = MqttBroker([("a/1", b'{"n": 1}'), ("a/2", b'{"n": 2}')])
        async with tcp_server(broker.tcp) as port:
            source = MqttSource(D, Raw(), SystemClock(), "127.0.0.1", port, ["a/#", "b"], websockets=False, tls=False, backoff=FAST)
            events = await take(source, 3)
        assert [(e["topic"], e["bytes"]) for e in events] == [("a/1", b'{"n": 1}'), ("a/2", b'{"n": 2}'), ("a/1", b'{"n": 1}')]
        assert broker.subscriptions[0] == "a/#" and broker.connections >= 2

    async def test_websocket_transport(self) -> None:
        broker = MqttBroker([("t", b"{}")], close_after=False)
        async with ws_server(broker.websocket, subprotocols=["mqtt"]) as url:
            port = int(url.rsplit(":", 1)[1].strip("/"))
            source = MqttSource(D, JsonDecoder(), SystemClock(), "127.0.0.1", port, ["t"], websockets=True, tls=False, path="/mqtt")
            assert await take(source, 1) == [{}]

    async def test_refused_connection_fails(self) -> None:
        broker = MqttBroker(connack_code=5)
        async with tcp_server(broker.tcp) as port:
            source = MqttSource(D, JsonDecoder(), SystemClock(), "127.0.0.1", port, ["t"], websockets=False, tls=False, backoff=FAST)
            error = await failure(source)
        assert "refused" in str(error.__cause__) or "disconnected" in str(error.__cause__)

    async def test_tls_handshake_failure_fails(self) -> None:
        async def hang_up(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.close()

        async with tcp_server(hang_up) as port:
            source = MqttSource(D, JsonDecoder(), SystemClock(), "127.0.0.1", port, ["t"], websockets=False, tls=True, backoff=FAST)
            await failure(source)

    async def test_full_queue_drops_instead_of_blocking(self) -> None:
        broker = MqttBroker([("t", b"{}")] * 5, close_after=False)
        async with tcp_server(broker.tcp) as port:
            source = MqttSource(D, JsonDecoder(), SystemClock(), "127.0.0.1", port, ["t"], websockets=False, tls=False, queue_size=1)
            stream = source.events()
            first = await anext(stream)
            await asyncio.sleep(0.3)
            await stream.aclose()
        assert first == {}

    def test_requires_topics(self) -> None:
        with pytest.raises(ValueError):
            MqttSource(D, JsonDecoder(), SystemClock(), "h", 1, [])


# ------------------------------------------------------------------ NATS
class TestNats:
    async def test_subscribes_with_credentials_and_receives(self) -> None:
        server = NatsServer([b'{"a": 1}', b'{"a": 2}'], close_after=False)
        async with tcp_server(server.handle) as port:
            source = NatsSource(D, Raw(), SystemClock(), f"nats://127.0.0.1:{port}", "orders", user="u", password="p", poll_s=0.05)
            events = await take(source, 2)
        assert [(e["subject"], e["bytes"]) for e in events] == [("orders", b'{"a": 1}'), ("orders", b'{"a": 2}')]
        assert server.connect_options[0]["user"] == "u"

    async def test_silence_is_a_failure(self) -> None:
        server = NatsServer([], close_after=False)
        async with tcp_server(server.handle) as port:
            source = NatsSource(D, JsonDecoder(), SystemClock(), f"nats://127.0.0.1:{port}", "s", silence_s=0.1, poll_s=0.05, backoff=FAST)
            error = await failure(source)
        assert "no NATS message" in str(error.__cause__)

    async def test_an_unreachable_server_is_a_failure_not_a_silent_wait(self) -> None:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        source = NatsSource(D, JsonDecoder(), SystemClock(), f"nats://127.0.0.1:{port}", "s", backoff=FAST)
        error = await failure(source, timeout=5)
        assert "NoServersError" in repr(error.__cause__)

    async def test_a_closed_connection_is_a_failure(self) -> None:
        server = NatsServer([], close_after=True)
        async with tcp_server(server.handle) as port:
            source = NatsSource(D, JsonDecoder(), SystemClock(), f"nats://127.0.0.1:{port}", "s", silence_s=5, poll_s=0.05, backoff=FAST)
            await failure(source)


# ------------------------------------------------------------------ ZeroMQ
class TestZeroMq:
    async def test_receives_envelope_and_body(self) -> None:
        async with zmq_publisher([b"/env/x", gzip.compress(b"body")]) as endpoint:
            source = ZmqSubSource(D, Raw(), SystemClock(), endpoint)
            (event,) = await take(source, 1)
        assert event["envelope"] == "/env/x" and gzip.decompress(event["bytes"]) == b"body"  # type: ignore[arg-type]

    async def test_silence_is_a_failure(self) -> None:
        source = ZmqSubSource(D, JsonDecoder(), SystemClock(), "tcp://127.0.0.1:9", silence_s=0.05, backoff=FAST)
        assert "no message" in str((await failure(source)).__cause__)


# ------------------------------------------------------------------ TCP
class TestTcp:
    async def test_lines_after_the_greeting_then_reconnect_on_close(self) -> None:
        greetings: list[bytes] = []

        async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            greetings.append(await reader.readline())
            writer.write(b"one\r\ntwo\n")
            await writer.drain()
            writer.close()

        async with tcp_server(handler) as port:
            source = TcpLineSource(D, Lines(), SystemClock(), "127.0.0.1", port, greeting=["CALL"], backoff=FAST)
            events = await take(source, 3)
        assert [e["line"] for e in events] == ["one", "two", "one"] and greetings[0] == b"CALL\r\n"

    async def test_silence_is_a_failure(self) -> None:
        async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            await reader.read()

        async with tcp_server(handler) as port:
            source = TcpLineSource(D, Lines(), SystemClock(), "127.0.0.1", port, silence_s=0.05, backoff=FAST)
            assert "no data" in str((await failure(source)).__cause__)

    async def test_fixed_size_records(self) -> None:
        async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.write(b"abcdefg")
            await writer.drain()
            writer.close()

        async with tcp_server(handler) as port:
            source = TcpRecordSource(D, Raw(), SystemClock(), "127.0.0.1", port, record_size=3, backoff=FAST)
            assert [e["bytes"] for e in await take(source, 2)] == [b"abc", b"def"]

    async def test_a_truncated_record_is_a_failure(self) -> None:
        async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.write(b"a")
            await writer.drain()
            writer.close()

        async with tcp_server(handler) as port:
            source = TcpRecordSource(D, Raw(), SystemClock(), "127.0.0.1", port, record_size=3, backoff=FAST)
            assert "closed the connection" in str((await failure(source)).__cause__)

    def test_record_size_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            TcpRecordSource(D, Raw(), SystemClock(), "h", 1, record_size=0)


# ------------------------------------------------------------------ HTTP polling (fake HTTP port, virtual time)
class TestHttpPoll:
    async def test_get_detects_changes_and_measures_them(self) -> None:
        clock = FakeClock()
        snapshots = [
            ok([{"id": 1, "v": 1}, {"id": 2, "v": 1}]),
            ok([{"id": 1, "v": 2}, {"id": 2, "v": 1}]),
            ok([{"id": 1, "v": 3}, {"id": 2, "v": 2}]),
        ]
        http = FakeHttp({"u": snapshots})
        source = HttpPollSource(D, JsonDecoder(), clock, http, ["u"], 10.0, ChangeDetector(["id"], ["v"]), headers={"H": "1"})
        assert source.published_volume() == PublishedVolume(0, 0.0)
        events = await take(source, 5)
        assert events == [{"id": 1, "v": 1}, {"id": 2, "v": 1}, {"id": 1, "v": 2}, {"id": 1, "v": 3}, {"id": 2, "v": 2}]
        assert source.published_volume() == PublishedVolume(3, 20.0)
        assert http.calls[0] == ("GET", "u", {"H": "1"}) and clock.sleeps[:2] == [10.0, 10.0]

    async def test_post_without_detector_or_initial_snapshot(self) -> None:
        clock = FakeClock()
        http = FakeHttp({"u": ok({"a": 1})})
        source = HttpPollSource(D, JsonDecoder(), clock, http, ["u"], 5.0, json_body={"q": 1})
        assert await take(source, 2) == [{"a": 1}, {"a": 1}]
        assert source.published_volume() is None and http.calls[0] == ("POST", "u", {"q": 1})

    async def test_initial_snapshot_can_be_suppressed(self) -> None:
        clock = FakeClock()
        http = FakeHttp({"u": [ok([{"id": 1, "v": 1}]), ok([{"id": 1, "v": 2}])]})
        source = HttpPollSource(D, JsonDecoder(), clock, http, ["u"], 5.0, ChangeDetector(["id"], ["v"]), emit_initial=False)
        assert await take(source, 1) == [{"id": 1, "v": 2}]

    async def test_failed_polls_are_retried_then_give_up(self) -> None:
        clock = FakeClock()
        http = FakeHttp({"u": [ok("x", 500), ok([{"a": 1}])]})
        source = HttpPollSource(D, JsonDecoder(), clock, http, ["u"], 5.0, backoff=FAST)
        assert await take(source, 1) == [{"a": 1}]
        source = HttpPollSource(D, JsonDecoder(), clock, FakeHttp(), ["missing"], 5.0, backoff=FAST)
        assert "HTTP 404" in str((await failure(source)).__cause__)

    def test_rejects_bad_configuration(self) -> None:
        with pytest.raises(ValueError):
            HttpPollSource(D, JsonDecoder(), FakeClock(), FakeHttp(), [], 5.0)
        with pytest.raises(ValueError):
            HttpPollSource(D, JsonDecoder(), FakeClock(), FakeHttp(), ["u"], 0)


class Files(FileDropSource):
    def __init__(self, clock: FakeClock, keys: list[str]) -> None:
        super().__init__(D, JsonDecoder(), clock, 60.0, backoff=FAST)
        self.keys = keys

    async def _locate(self) -> FileLocation:
        key = self.keys.pop(0) if len(self.keys) > 1 else self.keys[0]
        if key == "fail":
            raise TransportError("index unavailable")
        return FileLocation(key, f"https://x/{key}", 900.0)

    async def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:
        for n in range(2):
            yield {"file": location.key, "n": n}


class TestFileDrop:
    async def test_each_file_is_read_once_and_measured(self) -> None:
        clock = FakeClock()
        source = Files(clock, ["fail", "a", "a", "b"])
        assert source.published_volume() == PublishedVolume(0, 0.0)
        events = await take(source, 4)
        assert [(e["file"], e["n"]) for e in events] == [("a", 0), ("a", 1), ("b", 0), ("b", 1)]
        assert source.published_volume() == PublishedVolume(2, 900.0)

    def test_interval_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            Files.__bases__[0].__init__(Files(FakeClock(), ["a"]), D, JsonDecoder(), FakeClock(), 0)  # type: ignore[arg-type]


# ------------------------------------------------------------------ merged
class TestMerged:
    async def test_merges_children_and_sums_volumes(self) -> None:
        clock = FakeClock()
        a = ScriptedSource(D, [{"s": "a"}], clock, volume=PublishedVolume(10, 100.0))
        b = ScriptedSource(D, [{"s": "b"}], clock, volume=PublishedVolume(5, 50.0))
        merged = MergedEventSource(D, [a, b], clock)
        assert sorted(e["s"] for e in await take(merged, 2)) == ["a", "b"]  # type: ignore[type-var]
        assert merged.published_volume() == PublishedVolume(15, 100.0)

    async def test_ends_when_every_child_ends_and_survives_one_failure(self) -> None:
        clock = FakeClock()
        merged = MergedEventSource(D, [ScriptedSource(D, [{"a": 1}], clock), ScriptedSource(D, [TransportError("x")], clock)], clock)
        assert [e async for e in merged.events()] == [{"a": 1}]
        assert merged.published_volume() is None

    async def test_fails_when_every_child_fails(self) -> None:
        clock = FakeClock()
        merged = MergedEventSource(
            D, [ScriptedSource(D, [TransportError("x")], clock), ScriptedSource(D, [TransportError("y")], clock)], clock
        )
        assert "every child source failed" in str(await failure(merged))

    async def test_requires_children(self) -> None:
        assert "no child sources" in str(await failure(MergedEventSource(D, [], FakeClock())))


# ------------------------------------------------------------------ cancellation that a library disguises
class ConvertsCancellation(PushEventSource):
    """Yields one message, then waits; a cancellation surfaces as AssertionError, as
    websockets 15–17 does when recv() is cancelled while reassembling a fragmented message."""

    def __init__(self) -> None:
        super().__init__(D, JsonDecoder(), FakeClock(), FAST)
        self.connections = 0

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        self.connections += 1
        yield RawMessage('{"n": 1}')
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise AssertionError("cannot reset() while queue isn't empty") from None


async def consume_until_cancelled(stream: AsyncGenerator[Mapping[str, object]], first: asyncio.Event) -> None:
    async for _ in stream:
        first.set()


class TestCancellationIsNeverRetried:
    async def test_push_reconnect_loop_stops_when_its_task_is_cancelled(self) -> None:
        source, first = ConvertsCancellation(), asyncio.Event()
        task = asyncio.create_task(consume_until_cancelled(source.events(), first))
        await first.wait()
        task.cancel()
        done, _ = await asyncio.wait([task], timeout=2)
        assert task in done and task.cancelled() and source.connections == 1

    async def test_poll_retry_loop_stops_when_its_task_is_cancelled(self) -> None:
        class Poll(HttpPollSource):
            fetches = 0

            async def _fetch(self) -> Sequence[RawMessage]:
                Poll.fetches += 1
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    raise OSError("library turned the cancellation into an I/O error") from None
                return []  # pragma: no cover - the wait above never ends on its own

        source = Poll(D, JsonDecoder(), FakeClock(), FakeHttp({}), ["http://x"], 1.0, backoff=FAST)
        task = asyncio.create_task(consume_until_cancelled(source.events(), asyncio.Event()))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        task.cancel()
        done, _ = await asyncio.wait([task], timeout=2)
        assert task in done and task.cancelled() and Poll.fetches == 1

    async def test_an_ordinary_failure_is_still_retried(self) -> None:
        source = Once()
        with pytest.raises(TransportError, match="gave up after 2 retries"):
            async for _ in source.events():
                pass
        assert source.connections == 3


class Stubborn(EventSourcePort):
    """A child that ignores the first cancellation (as a buggy library could) and honours the second."""

    def __init__(self) -> None:
        self.cancels = 0

    @property
    def descriptor(self):  # type: ignore[no-untyped-def]
        return D

    def published_volume(self) -> PublishedVolume | None:
        return None

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        yield {"n": 1}
        while True:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancels += 1
                if self.cancels > 1:
                    raise


async def test_merged_close_cancels_again_until_every_child_has_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    import stream_consumers.adapters.outbound.providers.transports.base as base

    monkeypatch.setattr(base, "MERGED_CLOSE_GRACE_S", 0.05)
    child = Stubborn()
    merged = MergedEventSource(D, [child], FakeClock())
    stream = merged.events()
    assert await anext(stream) == {"n": 1}
    await asyncio.wait_for(stream.aclose(), 2)
    assert child.cancels == 2


async def test_websocket_cancelled_mid_fragmented_message_stops_instead_of_reconnecting(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reproduces the websockets race with the real library: the continuation frame of a
    fragmented message is queued and the reading task is cancelled before it resumes, so
    `Assembler.get` raises AssertionError("cannot reset() while queue isn't empty")."""
    from websockets.asyncio import messages
    from websockets.frames import Opcode

    connections = 0

    async def handler(ws: websockets.ServerConnection) -> None:
        nonlocal connections
        connections += 1

        async def fragments() -> AsyncGenerator[str]:
            yield '{"part": '
            await asyncio.sleep(0.05)
            yield "1}"

        await ws.send('{"whole": 1}')
        await ws.send(fragments())
        await ws.wait_closed()

    reader: asyncio.Task[None] | None = None
    original_put = messages.Assembler.put

    def put_then_cancel(self: messages.Assembler, frame: object) -> None:
        original_put(self, frame)  # type: ignore[arg-type]
        if getattr(frame, "opcode", None) is Opcode.CONT and reader is not None:
            reader.cancel()

    monkeypatch.setattr(messages.Assembler, "put", put_then_cancel)
    first = asyncio.Event()
    async with ws_server(handler) as url:
        source = WebSocketSource(D, JsonDecoder(), SystemClock(), url, backoff=FAST)
        reader = asyncio.create_task(consume_until_cancelled(source.events(), first))
        done, _ = await asyncio.wait([reader], timeout=3)
    assert reader in done and reader.cancelled() and first.is_set() and connections == 1
