"""MQTT push source (paho runs its network loop in a thread; messages cross into asyncio)."""

from __future__ import annotations

import asyncio
import ssl
import threading
from collections.abc import AsyncGenerator, Sequence

import paho.mqtt.client as mqtt

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort
from stream_consumers.ports.outbound.system import ClockPort


class MqttSource(PushEventSource):
    """Subscribes to `topics`; each PUBLISH becomes a message with attribute ``topic``."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        host: str,
        port: int,
        topics: Sequence[str],
        websockets: bool = True,
        tls: bool = True,
        path: str = "/mqtt",
        queue_size: int = 50_000,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        if not topics:
            raise ValueError("topics must not be empty")
        self._host = host
        self._port = port
        self._topics = tuple(topics)
        self._websockets = websockets
        self._tls = tls
        self._path = path
        self._queue_size = queue_size

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[RawMessage | BaseException] = asyncio.Queue(self._queue_size)

        def offer(item: RawMessage | BaseException) -> None:
            if not queue.full():
                queue.put_nowait(item)

        def on_connect(client: mqtt.Client, userdata: object, flags: object, reason: mqtt.ReasonCode, properties: object = None) -> None:
            if reason.is_failure:
                loop.call_soon_threadsafe(offer, TransportError(f"MQTT connect refused: {reason}"))
                return
            for topic in self._topics:
                client.subscribe(topic)

        def on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
            loop.call_soon_threadsafe(offer, RawMessage(bytes(msg.payload), {"topic": msg.topic}))

        def on_disconnect(client: mqtt.Client, userdata: object, flags: object, reason: mqtt.ReasonCode, properties: object = None) -> None:
            loop.call_soon_threadsafe(offer, TransportError(f"MQTT disconnected: {reason}"))

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets" if self._websockets else "tcp")
        if self._websockets:
            client.ws_set_options(path=self._path)
        if self._tls:
            client.tls_set_context(ssl.create_default_context())
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        stop = threading.Event()

        def network() -> None:
            # paho's own loop_start() reconnects by itself and sleeps between attempts, which makes
            # stopping slow; this loop stops within one `loop()` timeout and leaves reconnection to the back-off.
            while not stop.is_set():
                code = client.loop(timeout=0.1)
                if code != mqtt.MQTT_ERR_SUCCESS:
                    loop.call_soon_threadsafe(offer, TransportError(f"MQTT network loop ended: {mqtt.error_string(code)}"))
                    return

        thread = threading.Thread(target=network, name=f"mqtt-{self._host}", daemon=True)
        try:
            await asyncio.to_thread(client.connect, self._host, self._port, 30)
            thread.start()
            while True:
                item = await queue.get()
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            stop.set()
            if thread.is_alive():
                await asyncio.to_thread(thread.join)
            client.disconnect()
