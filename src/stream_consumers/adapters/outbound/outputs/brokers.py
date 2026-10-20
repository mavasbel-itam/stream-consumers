"""Events published to message brokers: Kafka (aiokafka), MQTT (paho), NATS (nats-py), ZeroMQ (pyzmq).

Every message is the event document `{"source", "received_at", "payload"}` as compact UTF-8 JSON,
the same text as one JSON-lines line without its line break.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Sequence

import nats
import paho.mqtt.client as mqtt
import zmq
import zmq.asyncio
from aiokafka import AIOKafkaProducer
from nats.aio.client import Client as NatsClient

from stream_consumers.adapters.outbound.outputs.batching import BatchingEventSink
from stream_consumers.adapters.outbound.outputs.formats import event_document
from stream_consumers.adapters.outbound.outputs.sinks import BaseEventSink
from stream_consumers.domain.errors import OutputError
from stream_consumers.domain.models import Event
from stream_consumers.domain.outputs import for_source
from stream_consumers.ports.outbound.system import ClockPort

CONNECT_TIMEOUT_S = 10.0


def message(event: Event) -> bytes:
    return json.dumps(event_document(event), ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")


class BrokerEventSink(BatchingEventSink):
    """A broker output publishing each event to `template` with `{source}` replaced by its source id."""

    def __init__(self, clock: ClockPort, label: str, template: str, batch_size: int = 500, max_delay_s: float = 1.0) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._template = template

    def _destination(self, event: Event) -> str:
        return for_source(self._template, event.source_id)


class KafkaEventSink(BrokerEventSink):
    """Key = source id, value = the event document; `close` waits until the broker acknowledged every batch."""

    def __init__(
        self, bootstrap: Sequence[str], topic: str, clock: ClockPort, label: str, batch_size: int = 500, max_delay_s: float = 1.0
    ) -> None:
        super().__init__(clock, label, topic, batch_size, max_delay_s)
        self._bootstrap = list(bootstrap)
        self._producer: AIOKafkaProducer | None = None

    async def _connect(self) -> None:
        producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap, request_timeout_ms=int(CONNECT_TIMEOUT_S * 1000))
        try:
            await producer.start()
        except BaseException:
            await producer.stop()
            raise
        self._producer = producer

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._producer is not None, "open() first"
        sent = [await self._producer.send(self._destination(e), message(e), key=e.source_id.encode("utf-8")) for e in events]
        await asyncio.gather(*sent)

    async def _disconnect(self) -> None:
        if self._producer is not None:
            await self._producer.stop()


class MqttEventSink(BrokerEventSink):
    """Publishes with QoS 1 (at least once) and waits for the broker's PUBACK of every message of a batch.

    paho runs its network loop in its own thread; waiting for acknowledgements happens in a worker
    thread, never on the event loop.
    """

    def __init__(
        self,
        host: str,
        port: int,
        topic: str,
        clock: ClockPort,
        label: str,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, topic, batch_size, max_delay_s)
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._client: mqtt.Client | None = None

    async def _connect(self) -> None:
        loop = asyncio.get_running_loop()
        answered = asyncio.Event()
        reasons: list[mqtt.ReasonCode] = []

        def on_connect(client: mqtt.Client, userdata: object, flags: object, reason: mqtt.ReasonCode, properties: object = None) -> None:
            reasons.append(reason)
            loop.call_soon_threadsafe(answered.set)

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"stream-consumers-{uuid.uuid4().hex[:12]}")
        if self._user is not None:
            client.username_pw_set(self._user, self._password)
        client.on_connect = on_connect
        await asyncio.to_thread(client.connect, self._host, self._port, 30)
        client.loop_start()
        try:
            await asyncio.wait_for(answered.wait(), CONNECT_TIMEOUT_S)
            if reasons[0].is_failure:
                raise ConnectionRefusedError(f"the broker refused the connection: {reasons[0]}")
        except BaseException:
            client.disconnect()
            client.loop_stop()
            raise
        self._client = client

    @staticmethod
    def _acknowledged(sent: Sequence[mqtt.MQTTMessageInfo]) -> None:
        for info in sent:
            info.wait_for_publish(CONNECT_TIMEOUT_S)
            if not info.is_published():
                raise TimeoutError(f"no PUBACK within {CONNECT_TIMEOUT_S:g} s")

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._client is not None, "open() first"
        sent = [self._client.publish(self._destination(e), message(e), qos=1) for e in events]
        for info in sent:
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                raise ConnectionError(mqtt.error_string(info.rc))
        await asyncio.to_thread(self._acknowledged, sent)

    async def _disconnect(self) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client.loop_stop()


class NatsEventSink(BrokerEventSink):
    """Core NATS publish; every batch ends with a round trip to the server (`flush`), so a lost
    connection is reported instead of silently dropping events."""

    def __init__(
        self,
        servers: Sequence[str],
        subject: str,
        clock: ClockPort,
        label: str,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, subject, batch_size, max_delay_s)
        self._servers = list(servers)
        self._user = user
        self._password = password
        self._client: NatsClient | None = None

    async def _connect(self) -> None:
        async def reported_by_the_exception(error: Exception) -> None:  # instead of nats-py's own error log
            return None

        # nats-py retries the first connection forever when max_reconnect_attempts is 0; with 1 every
        # server is tried twice and then NoServersError (or the server's refusal) ends the attempt
        self._client = await asyncio.wait_for(
            nats.connect(
                servers=self._servers,
                user=self._user,
                password=self._password,
                connect_timeout=CONNECT_TIMEOUT_S,
                allow_reconnect=False,
                max_reconnect_attempts=1,
                reconnect_time_wait=0.1,
                error_cb=reported_by_the_exception,
            ),
            3 * CONNECT_TIMEOUT_S,
        )

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._client is not None, "open() first"
        for event in events:
            await self._client.publish(self._destination(event), message(event))
        await self._client.flush(timeout=CONNECT_TIMEOUT_S)

    async def _disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()


class ZeroMqEventSink(BaseEventSink):
    """A PUB socket bound to `endpoint`; each event is two frames, source id and event document.

    ZeroMQ publish/subscribe delivers only to subscribers connected at the time of sending: events
    published before a subscriber connects, or while none is, are dropped by design. `close` keeps
    the socket up to `linger_ms` to deliver what is queued.
    """

    def __init__(self, endpoint: str, label: str, linger_ms: int = 1000) -> None:
        self._endpoint = endpoint
        self._label = label
        self._linger_ms = linger_ms
        self._context: zmq.asyncio.Context | None = None
        self._socket: zmq.asyncio.Socket | None = None

    async def open(self) -> None:
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.PUB)
        socket.setsockopt(zmq.LINGER, self._linger_ms)
        try:
            socket.bind(self._endpoint)
        except zmq.ZMQError as exc:
            socket.close(0)
            context.term()
            raise OutputError(self._label, exc) from exc
        self._context, self._socket = context, socket

    async def write(self, event: Event) -> None:
        assert self._socket is not None, "open() first"
        try:
            await self._socket.send_multipart([event.source_id.encode("utf-8"), message(event)])
        except zmq.ZMQError as exc:
            raise OutputError(self._label, exc) from exc

    async def close(self) -> None:
        if self._socket is not None and self._context is not None:
            self._socket.close()
            await asyncio.to_thread(self._context.term)  # waits up to linger_ms for queued messages
