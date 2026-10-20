"""Broker outputs against real servers: each test publishes through the sink and reads back with
the broker's own client (Kafka and NATS in Docker, an amqtt broker in-process, a ZeroMQ SUB socket)."""

from __future__ import annotations

import asyncio
import json
import socket
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import nats
import pytest
import zmq
import zmq.asyncio
from aiokafka import AIOKafkaConsumer
from amqtt.broker import Broker
from amqtt.client import MQTTClient

from stream_consumers.adapters.outbound.outputs import brokers
from stream_consumers.adapters.outbound.outputs.brokers import KafkaEventSink, MqttEventSink, NatsEventSink, ZeroMqEventSink, message
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.domain.errors import OutputError
from stream_consumers.domain.models import Event
from stream_consumers.ports.outbound.outputs import EventSinkPort
from tests.servers import MqttBroker, kafka_broker, nats_server, tcp_server
from tests.unit.test_outputs import real_events

EVENTS = [*real_events("wikimedia")[:3], *real_events("coinbase")[:2]]
"""Real payloads decoded from the captured messages of two sources."""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def document(raw: bytes) -> dict[str, object]:
    return json.loads(raw.decode("utf-8"))


def expected(events: Sequence[Event]) -> list[dict[str, object]]:
    return [document(message(e)) for e in events]


async def publish(sink: EventSinkPort, events: Sequence[Event]) -> None:
    await sink.open()
    try:
        for event in events:
            await sink.write(event)
    finally:
        await sink.close()


def test_the_message_is_the_json_lines_document_without_its_line_break() -> None:
    event = Event("s", 1.5, {"a": "ñ", "b": {"c": 1}})
    assert message(event) == '{"source":"s","received_at":1.5,"payload":{"a":"ñ","b":{"c":1}}}'.encode()


class TestKafka:
    async def test_topics_per_source_keys_and_a_fixed_topic(self) -> None:
        async with kafka_broker() as bootstrap:
            await publish(KafkaEventSink([bootstrap], "stream_consumers.{source}", SystemClock(), "kafka", batch_size=2), EVENTS)
            await publish(KafkaEventSink([bootstrap], "all_events", SystemClock(), "kafka"), EVENTS)
            read = {}
            for topic in ("stream_consumers.wikimedia", "stream_consumers.coinbase", "all_events"):
                consumer = AIOKafkaConsumer(
                    topic, bootstrap_servers=bootstrap, auto_offset_reset="earliest", group_id=f"t-{uuid.uuid4().hex}"
                )
                await consumer.start()
                try:
                    records = []
                    while len(records) < sum(1 for e in EVENTS if topic == "all_events" or topic.endswith(e.source_id)):
                        batch = await consumer.getmany(timeout_ms=10_000)
                        assert batch, f"nothing read from {topic}"
                        records += [r for rs in batch.values() for r in rs]
                    read[topic] = [(r.key.decode(), document(r.value)) for r in records]
                finally:
                    await consumer.stop()
        assert read["stream_consumers.wikimedia"] == [("wikimedia", d) for d in expected(EVENTS[:3])]
        assert read["stream_consumers.coinbase"] == [("coinbase", d) for d in expected(EVENTS[3:])]
        assert read["all_events"] == [(e.source_id, d) for e, d in zip(EVENTS, expected(EVENTS), strict=True)]

    async def test_an_unreachable_broker_is_an_output_error(self) -> None:
        sink = KafkaEventSink([f"127.0.0.1:{free_port()}"], "t", SystemClock(), "kafka://here")
        with pytest.raises(OutputError, match=r"^output kafka://here failed: KafkaConnectionError"):
            await sink.open()
        await sink.close()  # nothing was opened: nothing to stop


@asynccontextmanager
async def amqtt_broker() -> AsyncIterator[int]:
    """A real MQTT broker (amqtt) in this process, on 127.0.0.1."""
    port = free_port()
    plugins = {"amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True}}  # no $SYS publisher
    broker = Broker({"listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{port}"}}, "plugins": plugins})
    await broker.start()
    try:
        yield port
    finally:
        await broker.shutdown()


class TestMqtt:
    async def test_topics_per_source_through_a_real_broker(self) -> None:
        async with amqtt_broker() as port:
            reader = MQTTClient()
            await reader.connect(f"mqtt://127.0.0.1:{port}/")
            await reader.subscribe([("stream_consumers/#", 1)])
            await publish(MqttEventSink("127.0.0.1", port, "stream_consumers/{source}", SystemClock(), "mqtt", batch_size=2), EVENTS)
            received = []
            for _ in EVENTS:
                delivered = await asyncio.wait_for(reader.deliver_message(), 10)
                received.append((delivered.topic, document(bytes(delivered.data))))
            await reader.disconnect()
        assert received == [(f"stream_consumers/{e.source_id}", d) for e, d in zip(EVENTS, expected(EVENTS), strict=True)]

    async def test_a_refused_connection(self) -> None:
        refusing = MqttBroker(connack_code=5)  # 5 = not authorised
        async with tcp_server(refusing.tcp) as port:
            sink = MqttEventSink("127.0.0.1", port, "t", SystemClock(), "mqtt://here", user="ana", password="wrong")
            with pytest.raises(OutputError, match="ConnectionRefusedError: the broker refused the connection"):
                await sink.open()
        await sink.close()

    async def test_no_connack_and_no_puback_time_out(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(brokers, "CONNECT_TIMEOUT_S", 0.5)

        async def silent(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            await reader.read(1024)
            await asyncio.sleep(1)
            writer.close()

        async with tcp_server(silent) as port:
            with pytest.raises(OutputError, match="TimeoutError"):
                await MqttEventSink("127.0.0.1", port, "t", SystemClock(), "mqtt").open()
        no_puback = MqttBroker(close_after=False)  # answers CONNECT but never acknowledges a publish
        async with tcp_server(no_puback.tcp) as port:
            sink = MqttEventSink("127.0.0.1", port, "t", SystemClock(), "mqtt")
            await sink.open()
            await sink.write(EVENTS[0])
            with pytest.raises(OutputError, match=r"TimeoutError: no PUBACK within 0\.5 s"):
                await sink.close()

    async def test_publishing_after_the_connection_is_gone(self) -> None:
        async with amqtt_broker() as port:
            sink = MqttEventSink("127.0.0.1", port, "t", SystemClock(), "mqtt")
            await sink.open()
        assert sink._client is not None
        sink._client.disconnect()
        await asyncio.sleep(0.2)
        await sink.write(EVENTS[0])
        with pytest.raises(OutputError, match="ConnectionError: The client is not currently connected"):
            await sink.close()


class TestNats:
    async def test_subjects_per_source_and_credentials(self) -> None:
        async with nats_server("--user", "ana", "--pass", "s3cret") as address:
            reader = await nats.connect(f"nats://{address}", user="ana", password="s3cret")
            subscription = await reader.subscribe("stream_consumers.>")
            await reader.flush()
            sink = NatsEventSink([f"nats://{address}"], "stream_consumers.{source}", SystemClock(), "nats", "ana", "s3cret", batch_size=2)
            await publish(sink, EVENTS)
            received = []
            for _ in EVENTS:
                delivered = await subscription.next_msg(timeout=10)
                received.append((delivered.subject, document(delivered.data)))
            await reader.close()
            with pytest.raises(OutputError, match="output nats://here failed"):
                await NatsEventSink([f"nats://{address}"], "t", SystemClock(), "nats://here", "ana", "wrong").open()
        assert received == [(f"stream_consumers.{e.source_id}", d) for e, d in zip(EVENTS, expected(EVENTS), strict=True)]

    async def test_no_server_is_an_output_error_quickly(self) -> None:
        sink = NatsEventSink([f"nats://127.0.0.1:{free_port()}"], "t", SystemClock(), "nats://here")
        with pytest.raises(OutputError, match=r"^output nats://here failed: NoServersError"):
            await asyncio.wait_for(sink.open(), 5)
        await sink.close()


class TestZeroMq:
    async def test_two_frames_per_event_to_a_connected_subscriber(self) -> None:
        port = free_port()
        sink = ZeroMqEventSink(f"tcp://127.0.0.1:{port}", "zmq")
        await sink.open()
        context = zmq.asyncio.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(f"tcp://127.0.0.1:{port}")
        subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        await asyncio.sleep(0.5)  # a subscription reaches a PUB socket asynchronously ("slow joiner")
        try:
            for event in EVENTS:
                await sink.write(event)
            received = [await asyncio.wait_for(subscriber.recv_multipart(), 10) for _ in EVENTS]
        finally:
            await sink.close()
            subscriber.close(0)
            context.term()
        assert [(s.decode(), document(d)) for s, d in received] == [(e.source_id, d) for e, d in zip(EVENTS, expected(EVENTS), strict=True)]

    async def test_an_address_in_use_and_a_closed_socket(self) -> None:
        port = free_port()
        first = ZeroMqEventSink(f"tcp://127.0.0.1:{port}", "zmq")
        await first.open()
        try:
            with pytest.raises(OutputError, match=f"^output zmq\\+tcp://127.0.0.1:{port} failed: ZMQError"):
                await ZeroMqEventSink(f"tcp://127.0.0.1:{port}", f"zmq+tcp://127.0.0.1:{port}").open()
        finally:
            await first.close()
        with pytest.raises(OutputError, match="ZMQError"):
            await first.write(EVENTS[0])
        await ZeroMqEventSink("tcp://127.0.0.1:1", "zmq").close()  # never opened
