"""Catalog of sources pointed at local servers, for running the real CLI end to end.

The test starts the servers and passes their addresses in the environment variable
STREAM_CONSUMERS_E2E (JSON: name → port or URL). Every transport is used, in working and failing setups.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import AsyncGenerator, Callable, Mapping
from dataclasses import replace

from stream_consumers.adapters.outbound.providers.auth import OAuthClientCredentials
from stream_consumers.adapters.outbound.providers.decoders import AvroSchemaInKeyDecoder, CsvDecoder, JsonDecoder, LineDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.base import BaseEventSource, FileDropSource, FileLocation, MergedEventSource
from stream_consumers.adapters.outbound.providers.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.providers.transports.kafka import KafkaSource
from stream_consumers.adapters.outbound.providers.transports.mqtt import MqttSource
from stream_consumers.adapters.outbound.providers.transports.nats import NatsSource
from stream_consumers.adapters.outbound.providers.transports.sse import SseSource
from stream_consumers.adapters.outbound.providers.transports.tcp import TcpLineSource, TcpRecordSource
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.adapters.outbound.providers.transports.zeromq import ZmqSubSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import (
    Credential,
    Delivery,
    Group,
    HeldKey,
    PublishedVolume,
    RawMessage,
    Setting,
    SourceDescriptor,
    Transport,
)
from stream_consumers.domain.policy import Backoff, ChangeDetector
from stream_consumers.ports.outbound.providers import (
    Credentials,
    DecoderPort,
    EventSourcePort,
    HttpClientPort,
    SourceDependencies,
    SourceFactoryPort,
)
from stream_consumers.ports.outbound.system import ClockPort

FAST = Backoff(initial_s=0.05, factor=1, max_s=0.05, max_attempts=2)


def endpoint(name: str) -> object:
    return json.loads(os.environ["STREAM_CONSUMERS_E2E"])[name]


def describe(source_id: str, transport: Transport, delivery: Delivery = Delivery.PUSH) -> SourceDescriptor:
    return SourceDescriptor(
        id=source_id,
        name=f"local {source_id}",
        category="Test",
        provider="tests",
        group=Group.KEYLESS,
        delivery=delivery,
        transport=transport,
        endpoint="local",
        docs_url="https://example.invalid/docs",
        terms_url="https://example.invalid/terms",
        personal_fields=("user",),
    )


class Lines(LineDecoder):
    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        return {"line": line, **message.attributes}


class Bytes(JsonDecoder):
    def decode(self, message: RawMessage):  # type: ignore[no-untyped-def]
        return [{"size": len(self.raw(message)), **message.attributes}]


class Refusing(TcpLineSource):
    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        raise TransportError("handshake refused")


class FileDropInterval(FileDropSource):
    """Misconfigured on purpose: a zero interval."""

    def __init__(self, descriptor: SourceDescriptor, decoder: DecoderPort, clock: ClockPort) -> None:
        super().__init__(descriptor, decoder, clock, 0)

    async def _locate(self) -> FileLocation:  # pragma: no cover - never reached, the constructor refuses
        raise NotImplementedError

    def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:  # pragma: no cover
        raise NotImplementedError


class LocalFiles(FileDropSource):
    def __init__(self, descriptor: SourceDescriptor, decoder: DecoderPort, clock: ClockPort, http: HttpClientPort, base: str) -> None:
        super().__init__(descriptor, decoder, clock, 0.2, FAST)
        self._http = http
        self._base = base

    async def _locate(self) -> FileLocation:
        response = await self._http.get(self._base + "/index")
        if response.status != 200:
            raise TransportError(f"index HTTP {response.status}")
        name = response.body.decode().strip()
        return FileLocation(name, f"{self._base}/{name}", 60.0)

    async def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:
        body = b"".join([chunk async for chunk in self._http.stream(location.url)])
        for record in self._decoder.decode(RawMessage(body)):
            yield record


class Snapshot(HttpPollSource):
    """A provider whose snapshot states its own period."""

    async def _snapshot_volume(self, records):  # type: ignore[no-untyped-def]
        return PublishedVolume(len(records), 10.0)


class Replay(BaseEventSource):
    """A finite source: replays fixed records, then ends."""

    def __init__(self, descriptor: SourceDescriptor, clock: ClockPort, records: list[Mapping[str, object]]) -> None:
        super().__init__(descriptor, clock)
        self._records = records

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        for record in self._records:
            yield record


class Stalling(BaseEventSource):
    """Blocks the event loop for `stall_s` before each record (no await), so a record can arrive after the
    consumer's deadline: the deterministic way to reach the "deadline already passed" path."""

    def __init__(self, descriptor: SourceDescriptor, clock: ClockPort, stall_s: float) -> None:
        super().__init__(descriptor, clock)
        self._stall_s = stall_s

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        for n in range(5):
            time.sleep(self._stall_s)
            yield {"n": n}


class DisguisedCancellation(BaseEventSource):
    """Yields one record, then waits; when cancelled it raises AssertionError the way websockets
    15–17 does mid fragmented message. The retry loop must stop instead of reconnecting forever."""

    def __init__(self, descriptor: SourceDescriptor, clock: ClockPort) -> None:
        super().__init__(descriptor, clock, FAST)

    async def _once(self) -> Mapping[str, object]:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise AssertionError("cannot reset() while queue isn't empty") from None
        return {}  # pragma: no cover - the wait above never ends on its own

    async def events(self) -> AsyncGenerator[Mapping[str, object]]:
        yield {"n": 0}
        yield await self._retrying(self._once)


Builder = Callable[[SourceDescriptor, SourceDependencies], EventSourcePort]


def _oauth(d: SourceDescriptor, deps: SourceDependencies, token_path: str) -> EventSourcePort:
    auth = OAuthClientCredentials(deps.http, deps.clock, f"{endpoint('http')}{token_path}", "e2e-id", "e2e-secret")
    return HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [f"{endpoint('http')}/protected"], 0.2, auth=auth, backoff=FAST)


def _ws(path: str, **kw: object) -> Builder:
    return lambda d, deps: WebSocketSource(d, Lines(), deps.clock, f"{endpoint('ws')}{path}", backoff=FAST, **kw)  # type: ignore[arg-type]


def _http(path: str) -> str:
    return f"{endpoint('http')}{path}"


BUILDERS: dict[str, tuple[Transport, Delivery, Builder]] = {
    "ws_ok": (
        Transport.WEBSOCKET,
        Delivery.PUSH,
        _ws("ok", subscriptions=["hello", {"op": "sub"}], keepalive="ka", keepalive_s=0.05, replies={"PING": "PONG"}, split_lines=True),
    ),
    "ws_refused": (
        Transport.WEBSOCKET,
        Delivery.PUSH,
        lambda d, deps: WebSocketSource(d, JsonDecoder(), deps.clock, "ws://127.0.0.1:9/", open_timeout_s=1, backoff=FAST),
    ),
    "sse_ok": (
        Transport.SSE,
        Delivery.PUSH,
        lambda d, deps: SseSource(
            d, JsonDecoder(), deps.clock, deps.http, _http("/sse"), event_types=frozenset({"message", "keep"}), backoff=FAST
        ),
    ),
    "sse_all": (
        Transport.SSE,
        Delivery.PUSH,
        lambda d, deps: SseSource(d, JsonDecoder(), deps.clock, deps.http, _http("/sse"), backoff=FAST),
    ),
    "sse_406": (
        Transport.SSE,
        Delivery.PUSH,
        lambda d, deps: SseSource(d, JsonDecoder(), deps.clock, deps.http, _http("/refuse"), backoff=FAST),
    ),
    "mqtt_tcp": (
        Transport.MQTT,
        Delivery.PUSH,
        lambda d, deps: MqttSource(
            d,
            JsonDecoder(),
            deps.clock,
            "127.0.0.1",
            endpoint("mqtt_tcp"),  # type: ignore[arg-type]
            ["a/#"],
            websockets=False,
            tls=False,
            backoff=FAST,
        ),
    ),
    "mqtt_ws": (
        Transport.MQTT,
        Delivery.PUSH,
        lambda d, deps: MqttSource(
            d,
            JsonDecoder(),
            deps.clock,
            "127.0.0.1",
            endpoint("mqtt_ws"),  # type: ignore[arg-type]
            ["t"],
            websockets=True,
            tls=False,
            path="/mqtt",
            backoff=FAST,
        ),
    ),
    "mqtt_queue": (
        Transport.MQTT,
        Delivery.PUSH,
        lambda d, deps: MqttSource(
            d,
            JsonDecoder(),
            deps.clock,
            "127.0.0.1",
            endpoint("mqtt_burst"),  # type: ignore[arg-type]
            ["t"],
            websockets=False,
            tls=False,
            queue_size=1,
            backoff=FAST,
        ),
    ),
    "mqtt_refused": (
        Transport.MQTT,
        Delivery.PUSH,
        lambda d, deps: MqttSource(
            d,
            JsonDecoder(),
            deps.clock,
            "127.0.0.1",
            endpoint("mqtt_refuse"),  # type: ignore[arg-type]
            ["t"],
            websockets=False,
            tls=False,
            backoff=FAST,
        ),
    ),
    "mqtt_tls": (
        Transport.MQTT,
        Delivery.PUSH,
        lambda d, deps: MqttSource(
            d,
            JsonDecoder(),
            deps.clock,
            "127.0.0.1",
            endpoint("hangup"),  # type: ignore[arg-type]
            ["t"],
            websockets=False,
            tls=True,
            backoff=FAST,
        ),
    ),
    "nats_ok": (
        Transport.NATS,
        Delivery.PUSH,
        lambda d, deps: NatsSource(
            d, Bytes(), deps.clock, f"nats://127.0.0.1:{endpoint('nats')}", "orders", user="u", password="p", poll_s=0.05, backoff=FAST
        ),
    ),
    "nats_silent": (
        Transport.NATS,
        Delivery.PUSH,
        lambda d, deps: NatsSource(
            d, Bytes(), deps.clock, f"nats://127.0.0.1:{endpoint('nats_silent')}", "s", silence_s=0.1, poll_s=0.05, backoff=FAST
        ),
    ),
    "nats_refused": (
        Transport.NATS,
        Delivery.PUSH,
        lambda d, deps: NatsSource(d, Bytes(), deps.clock, "nats://127.0.0.1:9", "s", backoff=FAST),
    ),
    "zmq_ok": (Transport.ZMQ, Delivery.PUSH, lambda d, deps: ZmqSubSource(d, Bytes(), deps.clock, endpoint("zmq"), backoff=FAST)),  # type: ignore[arg-type]
    "zmq_silent": (
        Transport.ZMQ,
        Delivery.PUSH,
        lambda d, deps: ZmqSubSource(d, Bytes(), deps.clock, "tcp://127.0.0.1:9", silence_s=0.05, backoff=FAST),
    ),
    "tcp_lines": (
        Transport.TCP,
        Delivery.PUSH,
        lambda d, deps: TcpLineSource(
            d,
            Lines(),
            deps.clock,
            "127.0.0.1",
            endpoint("tcp_lines"),  # type: ignore[arg-type]
            greeting=["CALL"],
            backoff=FAST,
        ),
    ),
    "tcp_silent": (
        Transport.TCP,
        Delivery.PUSH,
        lambda d, deps: TcpLineSource(
            d,
            Lines(),
            deps.clock,
            "127.0.0.1",
            endpoint("tcp_silent"),  # type: ignore[arg-type]
            silence_s=0.05,
            backoff=FAST,
        ),
    ),
    "tcp_records": (
        Transport.TCP,
        Delivery.PUSH,
        lambda d, deps: TcpRecordSource(
            d,
            Bytes(),
            deps.clock,
            "127.0.0.1",
            endpoint("tcp_records"),  # type: ignore[arg-type]
            record_size=3,
            backoff=FAST,
        ),
    ),
    "tcp_truncated": (
        Transport.TCP,
        Delivery.PUSH,
        lambda d, deps: TcpRecordSource(
            d,
            Bytes(),
            deps.clock,
            "127.0.0.1",
            endpoint("tcp_truncated"),  # type: ignore[arg-type]
            record_size=3,
            backoff=FAST,
        ),
    ),
    "tcp_handshake": (
        Transport.TCP,
        Delivery.PUSH,
        lambda d, deps: Refusing(
            d,
            Lines(),
            deps.clock,
            "127.0.0.1",
            endpoint("tcp_lines"),  # type: ignore[arg-type]
            backoff=FAST,
        ),
    ),
    "poll_get": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: HttpPollSource(
            d,
            JsonDecoder(),
            deps.clock,
            deps.http,
            [_http("/snapshot")],
            0.2,
            ChangeDetector(["id"], ["v"]),
            headers={"X-T": "1"},
            backoff=FAST,
        ),
    ),
    "poll_post": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: HttpPollSource(
            d, JsonDecoder(), deps.clock, deps.http, [_http("/graphql")], 0.2, json_body={"query": "q"}, emit_initial=False, backoff=FAST
        ),
    ),
    "poll_404": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [_http("/missing")], 0.2, backoff=FAST),
    ),
    "files": (Transport.HTTP, Delivery.FILE_DROP, lambda d, deps: LocalFiles(d, CsvDecoder(), deps.clock, deps.http, _http("/files"))),
    "files_404": (
        Transport.HTTP,
        Delivery.FILE_DROP,
        lambda d, deps: LocalFiles(d, CsvDecoder(), deps.clock, deps.http, _http("/nofiles")),
    ),
    "files_gone": (Transport.HTTP, Delivery.FILE_DROP, lambda d, deps: LocalFiles(d, CsvDecoder(), deps.clock, deps.http, _http("/gone"))),
    "merged": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: MergedEventSource(
            d,
            [
                HttpPollSource(
                    d, JsonDecoder(), deps.clock, deps.http, [_http("/snapshot")], 0.2, ChangeDetector(["id"], ["v"]), backoff=FAST
                ),
                HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [_http("/missing")], 0.2, backoff=FAST),
            ],
            deps.clock,
        ),
    ),
    "poll_snapshot": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: Snapshot(
            d, JsonDecoder(), deps.clock, deps.http, [_http("/snapshot")], 0.2, ChangeDetector(["id"], ["v"]), backoff=FAST
        ),
    ),
    "zmq_fast": (Transport.ZMQ, Delivery.PUSH, lambda d, deps: ZmqSubSource(d, Bytes(), deps.clock, endpoint("zmq_fast"), backoff=FAST)),  # type: ignore[arg-type]
    "merged_finite": (
        Transport.HTTP,
        Delivery.PUSH,
        lambda d, deps: MergedEventSource(d, [Replay(d, deps.clock, [{"a": 1}]), Replay(d, deps.clock, [{"b": 2}])], deps.clock),
    ),
    "merged_empty": (Transport.HTTP, Delivery.PUSH, lambda d, deps: MergedEventSource(d, [], deps.clock)),
    "keyed": (Transport.HTTP, Delivery.PUSH, lambda d, deps: Replay(d, deps.clock, [{"key": "used"}])),
    "stalling": (Transport.HTTP, Delivery.PUSH, lambda d, deps: Stalling(d, deps.clock, 0.3)),
    "disguised_cancel": (Transport.HTTP, Delivery.PUSH, lambda d, deps: DisguisedCancellation(d, deps.clock)),
    # each Kafka source has its own consumer group: in a shared group a consumer that joins later waits
    # for a rebalance (up to the 3 s heartbeat) and its 2 s check window can end before its first message
    "kafka_json": (
        Transport.KAFKA,
        Delivery.PUSH,
        lambda d, deps: KafkaSource(d, JsonDecoder(), deps.clock, str(endpoint("kafka")), ["e2e_json"], "e2e_json", start_at="earliest"),
    ),
    "kafka_avro": (
        Transport.KAFKA,
        Delivery.PUSH,
        lambda d, deps: KafkaSource(
            d, AvroSchemaInKeyDecoder(), deps.clock, str(endpoint("kafka")), ["e2e_avro"], "e2e_avro", start_at="earliest"
        ),
    ),
    "kafka_refused": (
        Transport.KAFKA,
        Delivery.PUSH,
        lambda d, deps: KafkaSource(d, JsonDecoder(), deps.clock, "127.0.0.1:9", ["t"], "e2e", backoff=FAST),
    ),
    "kafka_no_topics": (
        Transport.KAFKA,
        Delivery.PUSH,
        lambda d, deps: KafkaSource(d, JsonDecoder(), deps.clock, "127.0.0.1:9", [], "e2e"),
    ),
    "kafka_bad_start": (
        Transport.KAFKA,
        Delivery.PUSH,
        lambda d, deps: KafkaSource(d, JsonDecoder(), deps.clock, "127.0.0.1:9", ["t"], "e2e", start_at="smallest"),
    ),
    "oauth_poll": (Transport.HTTP, Delivery.POLL, lambda d, deps: _oauth(d, deps, "/token")),
    "oauth_denied": (Transport.HTTP, Delivery.POLL, lambda d, deps: _oauth(d, deps, "/token_denied")),
    "oauth_garbage": (Transport.HTTP, Delivery.POLL, lambda d, deps: _oauth(d, deps, "/token_garbage")),
    "oauth_empty": (Transport.HTTP, Delivery.POLL, lambda d, deps: _oauth(d, deps, "/token_empty")),
    "configured": (Transport.HTTP, Delivery.PUSH, lambda d, deps: Replay(d, deps.clock, [{"configured": True}])),
    "settings_only": (Transport.HTTP, Delivery.PUSH, lambda d, deps: Replay(d, deps.clock, [{"settings": True}])),
    "bad_interval": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [_http("/snapshot")], 0),
    ),
    "bad_urls": (Transport.HTTP, Delivery.POLL, lambda d, deps: HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [], 1.0)),
    "bad_topics": (Transport.MQTT, Delivery.PUSH, lambda d, deps: MqttSource(d, JsonDecoder(), deps.clock, "127.0.0.1", 1, [])),
    "bad_record": (Transport.TCP, Delivery.PUSH, lambda d, deps: TcpRecordSource(d, Bytes(), deps.clock, "127.0.0.1", 1, record_size=0)),
    "bad_files": (Transport.HTTP, Delivery.FILE_DROP, lambda d, deps: FileDropInterval(d, CsvDecoder(), deps.clock)),
    "merged_dead": (
        Transport.HTTP,
        Delivery.POLL,
        lambda d, deps: MergedEventSource(
            d,
            [
                HttpPollSource(d, JsonDecoder(), deps.clock, deps.http, [_http("/missing")], 0.2, backoff=FAST),
            ],
            deps.clock,
        ),
    ),
}


class Local(BaseSourceFactory):
    def __init__(self, source_id: str) -> None:
        transport, delivery, self._builder = BUILDERS[source_id]
        self.DESCRIPTOR = describe(source_id, transport, delivery)  # type: ignore[misc]
        if source_id == "keyed":
            self.DESCRIPTOR = replace(self.DESCRIPTOR, credential=Credential(("E2E_KEY",), "https://sign.up/e2e"))  # type: ignore[misc]
        if source_id == "configured":
            self.DESCRIPTOR = replace(  # type: ignore[misc]
                self.DESCRIPTOR,
                credential=Credential(("E2E_ID", "E2E_SECRET"), "https://sign.up/pair", required=False, how_to_get="Form; e-mailed."),
                settings=(Setting("E2E_REGION", "eu", "Region to read."),),
            )
        if source_id == "settings_only":
            self.DESCRIPTOR = replace(self.DESCRIPTOR, settings=(Setting("E2E_CONTACT", "", "Contact e-mail."),))  # type: ignore[misc]

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return self._builder(self.DESCRIPTOR, deps)


# stalling blocks the event loop on purpose, so it has its own catalog (stalling_catalog.py)
FACTORIES: tuple[SourceFactoryPort, ...] = tuple(Local(source_id) for source_id in BUILDERS if source_id != "stalling")
HELD_KEYS = (HeldKey("keyed", ("E2E_SPARE_KEY",), "Local provider", "Second key of the account.", "https://sign.up/e2e"),)
