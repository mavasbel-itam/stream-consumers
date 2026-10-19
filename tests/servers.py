"""Local servers speaking each transport's protocol, for the component and end-to-end tiers."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager, suppress

import websockets
import zmq
import zmq.asyncio
from aiohttp import web


@asynccontextmanager
async def ws_server(
    handler: Callable[[websockets.ServerConnection], Awaitable[None]], subprotocols: Sequence[str] | None = None
) -> AsyncIterator[str]:
    async with websockets.serve(handler, "127.0.0.1", 0, subprotocols=subprotocols) as server:  # type: ignore[arg-type]
        port = next(iter(server.sockets)).getsockname()[1]
        yield f"ws://127.0.0.1:{port}/"


@asynccontextmanager
async def http_server(routes: Sequence[web.RouteDef]) -> AsyncIterator[str]:
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


@asynccontextmanager
async def tcp_server(handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]) -> AsyncIterator[int]:
    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        server.close()
        await server.wait_closed()


# ------------------------------------------------------------------ MQTT 3.1.1 (just enough of it)
def _remaining(n: int) -> bytes:
    out = bytearray()
    while True:
        byte, n = n % 128, n // 128
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def mqtt_publish(topic: str, payload: bytes) -> bytes:
    body = len(topic).to_bytes(2, "big") + topic.encode() + payload
    return b"\x30" + _remaining(len(body)) + body


class MqttBroker:
    """Answers CONNECT (with `connack_code`), SUBSCRIBE and PINGREQ; after the first SUBACK publishes
    `messages` (topic, payload) and then, if `close_after`, drops the connection."""

    def __init__(self, messages: Sequence[tuple[str, bytes]] = (), connack_code: int = 0, close_after: bool = True) -> None:
        self.messages = list(messages)
        self.connack_code = connack_code
        self.close_after = close_after
        self.subscriptions: list[str] = []
        self.connections = 0

    async def serve(self, read: Callable[[int], Awaitable[bytes]], write: Callable[[bytes], Awaitable[None]]) -> None:
        self.connections += 1
        while True:
            header = (await read(1))[0]
            length, shift = 0, 0
            while True:
                byte = (await read(1))[0]
                length += (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    break
            body = await read(length) if length else b""
            kind = header & 0xF0
            if kind == 0x10:
                await write(bytes([0x20, 0x02, 0x00, self.connack_code]))
                if self.connack_code:
                    return
            elif kind == 0x80:
                packet_id, rest, topics = body[:2], body[2:], []
                while rest:
                    size = int.from_bytes(rest[:2], "big")
                    topics.append(rest[2 : 2 + size].decode())
                    rest = rest[3 + size :]
                self.subscriptions.extend(topics)
                await write(bytes([0x90, 2 + len(topics)]) + packet_id + b"\x00" * len(topics))
                for topic, payload in self.messages:
                    await write(mqtt_publish(topic, payload))
                if self.close_after:
                    return
            elif kind == 0xC0:
                await write(b"\xd0\x00")
            elif kind == 0xE0:
                return

    async def tcp(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        async def write(data: bytes) -> None:
            writer.write(data)
            await writer.drain()

        try:
            await self.serve(reader.readexactly, write)
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()

    async def websocket(self, ws: websockets.ServerConnection) -> None:
        buffer = bytearray()

        async def read(n: int) -> bytes:
            while len(buffer) < n:
                buffer.extend(await ws.recv())  # type: ignore[arg-type]
            out = bytes(buffer[:n])
            del buffer[:n]
            return out

        with suppress(websockets.ConnectionClosed):
            await self.serve(read, ws.send)


# ------------------------------------------------------------------ NATS (just enough of it)
class NatsServer:
    """Sends INFO, answers PING, and on SUB delivers `payloads` on that subject, then closes if `close_after`."""

    def __init__(self, payloads: Sequence[bytes] = (), close_after: bool = True) -> None:
        self.payloads = list(payloads)
        self.close_after = close_after
        self.connect_options: list[dict[str, object]] = []

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        info = {
            "server_id": "t",
            "server_name": "t",
            "version": "2.10.0",
            "go": "go1.22",
            "host": "127.0.0.1",
            "port": 0,
            "headers": True,
            "max_payload": 1048576,
            "proto": 1,
        }
        writer.write(b"INFO " + json.dumps(info).encode() + b"\r\n")
        await writer.drain()
        try:
            while line := await reader.readline():
                text = line.decode().strip()
                if text.startswith("CONNECT "):
                    self.connect_options.append(json.loads(text[8:]))
                elif text == "PING":
                    writer.write(b"PONG\r\n")
                elif text.startswith("SUB "):
                    subject, sid = text.split()[1], text.split()[-1]
                    for payload in self.payloads:
                        writer.write(f"MSG {subject} {sid} {len(payload)}\r\n".encode() + payload + b"\r\n")
                    await writer.drain()
                    if self.close_after:
                        break
                await writer.drain()
        finally:
            writer.close()


# ------------------------------------------------------------------ ZeroMQ
@asynccontextmanager
async def zmq_publisher(frames: Sequence[bytes], every_s: float = 0.02, burst: int = 1) -> AsyncIterator[str]:
    """Publishes `frames` as one multipart message, `burst` times every `every_s` (subscribers join late).

    A high rate comes from the burst, not from a short sleep, so it does not depend on how soon a
    loaded machine wakes the loop up."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    port = socket.bind_to_random_port("tcp://127.0.0.1")

    async def loop() -> None:
        while True:
            for _ in range(burst):
                await socket.send_multipart(list(frames))
            await asyncio.sleep(every_s)

    task = asyncio.create_task(loop())
    try:
        yield f"tcp://127.0.0.1:{port}"
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        socket.close(linger=0)
        context.term()


KAFKA_IMAGE = "apache/kafka:3.9.1"


def _free_port() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@asynccontextmanager
async def kafka_broker(start_timeout_s: float = 90.0) -> AsyncIterator[str]:
    """A single-node KRaft Kafka broker in Docker (the official apache/kafka image), published on
    127.0.0.1 only. Yields its bootstrap address. Requires Docker; there is no fallback, because a
    Kafka transport tested without a broker would prove nothing."""
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaConnectionError

    port = _free_port()
    env = {
        "KAFKA_NODE_ID": "1",
        "KAFKA_PROCESS_ROLES": "broker,controller",
        "KAFKA_LISTENERS": f"PLAINTEXT://:{port},CONTROLLER://:9093",
        "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://127.0.0.1:{port}",
        "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
        "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT",
        "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@localhost:9093",
        "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
        "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
        "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
        "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": "0",
        "KAFKA_NUM_PARTITIONS": "1",
        "KAFKA_AUTO_CREATE_TOPICS_ENABLE": "true",
    }
    args = ["docker", "run", "-d", "--rm", "-p", f"127.0.0.1:{port}:{port}"]
    for name, value in env.items():
        args += ["-e", f"{name}={value}"]
    process = await asyncio.create_subprocess_exec(*args, KAFKA_IMAGE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"docker run {KAFKA_IMAGE} failed: {err.decode()}")
    container = out.decode().strip()
    bootstrap = f"127.0.0.1:{port}"
    try:
        deadline = asyncio.get_running_loop().time() + start_timeout_s
        while True:
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
            try:
                await producer.start()
                break
            except KafkaConnectionError:
                if asyncio.get_running_loop().time() > deadline:
                    raise
                await asyncio.sleep(1)
            finally:
                await producer.stop()
        yield bootstrap
    finally:
        stop = await asyncio.create_subprocess_exec(
            "docker", "rm", "-f", container, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await stop.wait()


async def kafka_produce(bootstrap: str, topic: str, messages: Sequence[tuple[bytes | None, bytes]]) -> None:
    from aiokafka import AIOKafkaProducer

    producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
    await producer.start()
    try:
        for key, value in messages:
            await producer.send_and_wait(topic, value, key=key)
    finally:
        await producer.stop()
