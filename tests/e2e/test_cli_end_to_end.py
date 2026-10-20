"""The installed CLI, run as a subprocess under coverage, against local servers for every transport."""

from __future__ import annotations

import asyncio
import contextlib
import csv
import io
import json
import os
import select
import shlex
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import ClassVar

import fastavro
import pytest
import websockets
from aiohttp import web
from amqtt.plugins.authentication import BaseAuthPlugin
from amqtt.session import Session

from stream_consumers.application.consume_service import ATTRIBUTE_SAMPLE
from tests.servers import (
    MqttBroker,
    NatsServer,
    http_server,
    kafka_broker,
    kafka_produce,
    nats_server,
    tcp_server,
    ws_server,
    zmq_publisher,
)

AVRO_SCHEMA = {"type": "record", "name": "alert", "fields": [{"name": "objectId", "type": "string"}, {"name": "cutout", "type": "bytes"}]}


def _avro_value() -> bytes:
    buffer = io.BytesIO()
    fastavro.schemaless_writer(buffer, fastavro.parse_schema(AVRO_SCHEMA), {"objectId": "ZTF1", "cutout": b"\x00\x01"})
    return buffer.getvalue()


AVRO_VALUE = _avro_value()

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[2]


async def ws_handler(ws: websockets.ServerConnection) -> None:
    await ws.recv()
    await ws.recv()
    await ws.send("PING\r\nline 1\r\n\r\nline 2")

    async def drain() -> None:
        async for _ in ws:
            pass

    reader = asyncio.create_task(drain())
    try:
        await asyncio.sleep(0.2)  # silence longer than the keep-alive interval
        for n in range(3, 200):
            await ws.send(f"line {n}")
            await asyncio.sleep(0.02)
    except websockets.ConnectionClosed:
        pass
    finally:
        reader.cancel()


def http_routes() -> list[web.RouteDef]:
    polls = {"n": 0}

    async def sse(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse()
        await response.prepare(request)
        for chunk in (
            b": hi\n",
            b'event: skip\ndata: {"user": "ana", "n": 0}\n\n',
            b'data: {"user": "ana",\ndata: "n": 1}\n\n',
            b'id: 7\nevent: keep\r\ndata: {"user": "beto", "n": 2}\r\n\r\n',
        ):
            await response.write(chunk)
        return response

    async def refuse(request: web.Request) -> web.Response:
        return web.Response(status=406, text="not acceptable")

    async def snapshot(request: web.Request) -> web.Response:
        assert request.headers.get("X-T") in ("1", None)
        polls["n"] += 1
        return web.json_response([{"id": 1, "v": polls["n"]}, {"id": 2, "v": 0}])

    async def graphql(request: web.Request) -> web.Response:
        return web.json_response({"data": await request.json()})

    async def index(request: web.Request) -> web.Response:
        return web.Response(text="f1.csv\n")

    async def file(request: web.Request) -> web.Response:
        return web.Response(text="a,b\n1,2\n3,4\n")

    async def missing_index(request: web.Request) -> web.Response:
        return web.Response(text="missing.csv")

    tokens = {"n": 0}

    async def token(request: web.Request) -> web.Response:
        form = await request.post()
        assert (form["grant_type"], form["client_id"], form["client_secret"]) == ("client_credentials", "e2e-id", "e2e-secret")
        tokens["n"] += 1
        return web.json_response({"access_token": f"token-{tokens['n']}", "expires_in": 61})

    async def token_denied(request: web.Request) -> web.Response:
        return web.json_response({"error": "invalid_client"}, status=401)

    async def token_garbage(request: web.Request) -> web.Response:
        return web.Response(text="<html>")

    async def token_empty(request: web.Request) -> web.Response:
        return web.json_response({"access_token": ""})

    async def protected(request: web.Request) -> web.Response:
        if request.headers.get("Authorization") in (None, "Bearer token-1"):
            return web.Response(status=401, text="expired")
        polls["n"] += 1
        return web.json_response([{"id": 1, "v": polls["n"], "token": request.headers["Authorization"]}])

    return [
        web.get("/sse", sse),
        web.get("/refuse", refuse),
        web.get("/snapshot", snapshot),
        web.post("/graphql", graphql),
        web.get("/files/index", index),
        web.get("/files/f1.csv", file),
        web.get("/gone/index", missing_index),
        web.post("/token", token),
        web.post("/token_denied", token_denied),
        web.post("/token_garbage", token_garbage),
        web.post("/token_empty", token_empty),
        web.get("/protected", protected),
    ]


async def tcp_lines(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    await reader.readline()
    writer.write(b"one\r\ntwo\n")
    await writer.drain()
    writer.close()


async def hold(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    await reader.read()
    writer.close()


async def hang_up(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    writer.close()


def sends(data: bytes):  # type: ignore[no-untyped-def]
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        writer.write(data)
        await writer.drain()
        writer.close()

    return handler


@asynccontextmanager
async def environment() -> AsyncIterator[dict[str, object]]:
    async with AsyncExitStack() as stack:
        addresses: dict[str, object] = {}
        addresses["ws"] = await stack.enter_async_context(ws_server(ws_handler))
        addresses["http"] = await stack.enter_async_context(http_server(http_routes()))
        addresses["mqtt_tcp"] = await stack.enter_async_context(tcp_server(MqttBroker([("a/1", b'{"n": 1}'), ("a/2", b'{"n": 2}')]).tcp))
        ws_broker = MqttBroker([("t", b'{"n": 1}')], close_after=False)
        addresses["mqtt_ws"] = int(
            (await stack.enter_async_context(ws_server(ws_broker.websocket, subprotocols=["mqtt"]))).rsplit(":", 1)[1].strip("/")
        )
        addresses["mqtt_burst"] = await stack.enter_async_context(tcp_server(MqttBroker([("t", b"{}")] * 200, close_after=False).tcp))
        addresses["mqtt_refuse"] = await stack.enter_async_context(tcp_server(MqttBroker(connack_code=5).tcp))
        addresses["hangup"] = await stack.enter_async_context(tcp_server(hang_up))
        addresses["nats"] = await stack.enter_async_context(tcp_server(NatsServer([b'{"a": 1}', b'{"a": 2}'], close_after=False).handle))
        addresses["nats_silent"] = await stack.enter_async_context(tcp_server(NatsServer([], close_after=False).handle))
        addresses["zmq"] = await stack.enter_async_context(zmq_publisher([b"/env", b"body"]))
        addresses["zmq_fast"] = await stack.enter_async_context(zmq_publisher([b"/fast", b"x"], every_s=0.01, burst=100))
        addresses["tcp_lines"] = await stack.enter_async_context(tcp_server(tcp_lines))
        addresses["tcp_silent"] = await stack.enter_async_context(tcp_server(hold))
        addresses["tcp_records"] = await stack.enter_async_context(tcp_server(sends(b"abcdefg")))
        addresses["tcp_truncated"] = await stack.enter_async_context(tcp_server(sends(b"a")))
        addresses["kafka"] = await stack.enter_async_context(kafka_broker())
        await kafka_produce(str(addresses["kafka"]), "e2e_json", [(None, b'{"n": 1, "user": "ana"}'), (b"k", b'{"n": 2}')])
        await kafka_produce(str(addresses["kafka"]), "e2e_avro", [(json.dumps(AVRO_SCHEMA).encode(), AVRO_VALUE)])
        yield addresses


async def cli(addresses: dict[str, object], *argv: str) -> tuple[int, str, str]:
    env = dict(os.environ, STREAM_CONSUMERS_E2E=json.dumps(addresses))
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--rcfile",
        str(ROOT / ".coveragerc.e2e"),
        "-m",
        "stream_consumers",
        "--catalog",
        "tests.e2e.local_catalog",
        "--env-file",
        "/nonexistent/.env",
        *argv,
        cwd=ROOT,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await asyncio.wait_for(process.communicate(), 120)
    return process.returncode or 0, out.decode(), err.decode()


EXPECTED = {
    "ws_ok": "ok",
    "ws_refused": "error",
    "sse_ok": "ok",
    "sse_all": "ok",
    "sse_406": "error",
    "mqtt_tcp": "ok",
    "mqtt_ws": "ok",
    "mqtt_queue": "ok",
    "mqtt_refused": "error",
    "mqtt_tls": "error",
    "nats_ok": "ok",
    "nats_silent": "error",
    "nats_refused": "error",
    "zmq_ok": "ok",
    "zmq_silent": "error",
    "tcp_lines": "ok",
    "tcp_silent": "error",
    "tcp_records": "ok",
    "tcp_truncated": "error",
    "tcp_handshake": "error",
    "poll_get": "ok",
    "poll_post": "ok",
    "poll_404": "error",
    "files": "ok",
    "files_404": "error",
    "files_gone": "error",
    "merged": "ok",
    "merged_dead": "error",
    "poll_snapshot": "ok",
    "zmq_fast": "ok",
    "merged_finite": "ok",
    "merged_empty": "error",
    "keyed": "key-pending",
    "disguised_cancel": "ok",
    "kafka_json": "ok",
    "kafka_avro": "ok",
    "kafka_refused": "error",
    "kafka_no_topics": "error",
    "kafka_bad_start": "error",
    "oauth_poll": "ok",
    "oauth_denied": "error",
    "oauth_garbage": "error",
    "oauth_empty": "error",
    "configured": "ok",
    "settings_only": "ok",
    "bad_interval": "error",
    "bad_urls": "error",
    "bad_topics": "error",
    "bad_record": "error",
    "bad_files": "error",
}


async def test_check_every_transport(tmp_path: Path) -> None:
    async with environment() as addresses:
        code, out, err = await cli(addresses, "check", "--seconds", "2", "--reports", str(tmp_path))
    assert code == 1, err
    statuses = {line.split()[0]: line.split()[1] for line in out.splitlines()[:-1]}
    assert statuses == EXPECTED
    failed = sum(1 for s in EXPECTED.values() if s == "error")
    assert "missing API credentials E2E_KEY" in out
    assert out.splitlines()[-1] == f"{len(EXPECTED)} sources, {len(EXPECTED) - failed} delivered or key pending, {failed} failed"
    (report,) = tmp_path.glob("check-*.json")
    rows = {r["source_id"]: r for r in json.loads(report.read_text())}
    assert rows["files"]["rate_basis"] == "published" and rows["files"]["rate"] == round(2 / 60, 3)
    assert rows["poll_get"]["rate_basis"] == "published" and rows["sse_ok"]["rate_basis"] == "observed"
    assert "gave up" in rows["poll_404"]["detail"] and "every child source failed" in rows["merged_dead"]["detail"]
    assert rows["poll_snapshot"]["rate_basis"] == "published" and rows["bad_interval"]["detail"].startswith("ValueError")
    assert rows["zmq_fast"]["events"] > ATTRIBUTE_SAMPLE and rows["merged_finite"]["events"] == 2
    assert rows["kafka_json"]["events"] == 2 and rows["kafka_avro"]["events"] == 1
    assert "topics must not be empty" in rows["kafka_no_topics"]["detail"] and "start_at" in rows["kafka_bad_start"]["detail"]
    assert "token request refused: HTTP 401" in rows["oauth_denied"]["detail"]
    assert "without access_token" in rows["oauth_garbage"]["detail"] and "empty access_token" in rows["oauth_empty"]["detail"]


async def test_oauth_token_is_renewed_before_it_expires_and_after_a_401() -> None:
    async with environment() as addresses:
        code, out, err = await cli(addresses, "consume", "oauth_poll", "--seconds", "2.5")
    assert code == 0, err
    tokens = [json.loads(line)["payload"]["token"] for line in out.splitlines()]
    assert tokens[0] == "Bearer token-2" and len(set(tokens)) >= 2  # token-1 refused with 401; renewed after ~1 s


async def test_kafka_avro_cutouts_arrive_as_base64() -> None:
    async with environment() as addresses:
        code, out, err = await cli(addresses, "consume", "kafka_avro", "--seconds", "15", "--max-events", "1")
    assert code == 0, err
    assert json.loads(out)["payload"] == {"objectId": "ZTF1", "cutout": "AAE="}


async def test_consume_into_every_text_format_and_sqlite(tmp_path: Path) -> None:
    expected = [{"user": "<masked>", "n": 1}, {"user": "<masked>", "n": 2}]
    async with environment() as addresses:
        texts = {}
        for name in ("jsonl", "csv", "tsv", "json", "pretty"):
            target = tmp_path / f"events.{name}"
            code, out, _ = await cli(
                addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--format", name, "--out", str(target)
            )
            assert code == 0 and out == ""
            texts[name] = target.read_text(encoding="utf-8")
        code, _, _ = await cli(
            addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--out", f"sqlite:{tmp_path / 'events.db'}"
        )
        assert code == 0
    assert [json.loads(line)["payload"] for line in texts["jsonl"].splitlines()] == expected
    assert [e["payload"] for e in json.loads(texts["json"])] == expected
    pretty, at = [], 0
    while at < len(texts["pretty"]):
        document, at = json.JSONDecoder().raw_decode(texts["pretty"], at)
        pretty.append(document["payload"])
        at += 1  # the newline after each document
    assert pretty == expected and texts["pretty"].count("\n  ") > 2
    for name, delimiter in (("csv", ","), ("tsv", "\t")):
        rows = list(csv.DictReader(io.StringIO(texts[name]), delimiter=delimiter))
        assert [(r["payload.user"], r["payload.n"]) for r in rows] == [("<masked>", "1"), ("<masked>", "2")]
    with contextlib.closing(sqlite3.connect(tmp_path / "events.db")) as db:
        assert [json.loads(p) for (p,) in db.execute("SELECT payload FROM sse_ok ORDER BY seq")] == expected


class RecordingAuth(BaseAuthPlugin):
    """Lets every client in and records the user name and password each one presented."""

    seen: ClassVar[list[tuple[str | None, str | None]]] = []

    async def authenticate(self, *, session: Session) -> bool:
        RecordingAuth.seen.append((session.username, session.password))
        return True


async def test_consume_into_a_real_mqtt_broker_with_the_password_from_the_env_file(tmp_path: Path) -> None:
    from amqtt.broker import Broker
    from amqtt.client import MQTTClient

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env_file = tmp_path / ".env"
    env_file.write_text("STREAM_CONSUMERS_OUTPUT_PASSWORD=pw-from-env\n", encoding="utf-8")
    plugins = {f"{__name__}.RecordingAuth": {}}
    broker = Broker({"listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{port}"}}, "plugins": plugins})
    await broker.start()
    try:
        reader = MQTTClient()
        await reader.connect(f"mqtt://127.0.0.1:{port}/")
        await reader.subscribe([("e2e/#", 1)])
        async with environment() as addresses:
            destination = f"mqtt://e2e@127.0.0.1:{port}/e2e/{{source}}"
            argv = ("--env-file", str(env_file), "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--out", destination)
            code, out, err = await cli(addresses, *argv)
        assert code == 0 and out == "" and json.loads(err)["events"] == 2 and "pw-from-env" not in err
        assert ("e2e", "pw-from-env") in RecordingAuth.seen
        received = [await asyncio.wait_for(reader.deliver_message(), 10) for _ in range(2)]
        assert [(m.topic, json.loads(bytes(m.data))["payload"]) for m in received] == [
            ("e2e/sse_ok", {"user": "<masked>", "n": 1}),
            ("e2e/sse_ok", {"user": "<masked>", "n": 2}),
        ]
        await reader.disconnect()
    finally:
        await broker.shutdown()


async def test_consume_into_kafka_nats_and_zeromq_and_an_unreachable_output() -> None:
    import nats
    import zmq
    import zmq.asyncio
    from aiokafka import AIOKafkaConsumer

    def free_port() -> int:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return int(s.getsockname()[1])

    async with environment() as addresses, nats_server() as nats_address:
        bootstrap = str(addresses["kafka"])
        code, out, err = await cli(addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--out", f"kafka://{bootstrap}")
        assert code == 0 and out == "" and json.loads(err.splitlines()[-1])["events"] == 2
        consumer = AIOKafkaConsumer(
            "stream_consumers.sse_ok", bootstrap_servers=bootstrap, auto_offset_reset="earliest", group_id="e2e_out"
        )
        await consumer.start()
        try:
            records: list[object] = []
            while len(records) < 2:
                batch = await consumer.getmany(timeout_ms=10_000)
                assert batch, "nothing arrived in Kafka"
                records += [r for rs in batch.values() for r in rs]
        finally:
            await consumer.stop()
        assert [(r.key, json.loads(r.value)["payload"]) for r in records] == [  # type: ignore[attr-defined]
            (b"sse_ok", {"user": "<masked>", "n": 1}),
            (b"sse_ok", {"user": "<masked>", "n": 2}),
        ]

        reader = await nats.connect(f"nats://{nats_address}")
        subscription = await reader.subscribe("e2e.>")
        await reader.flush()
        code, out, err = await cli(
            addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--out", f"nats://{nats_address}/e2e.{{source}}"
        )
        assert code == 0 and out == ""
        delivered = [await subscription.next_msg(timeout=10) for _ in range(2)]
        assert [(m.subject, json.loads(m.data)["payload"]["n"]) for m in delivered] == [("e2e.sse_ok", 1), ("e2e.sse_ok", 2)]
        await reader.close()

        # ZeroMQ drops what is sent before a subscriber is connected: the subscriber connects first
        # (ZeroMQ retries until the CLI binds) and a source that never pauses keeps sending
        port = free_port()
        context = zmq.asyncio.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(f"tcp://127.0.0.1:{port}")
        subscriber.setsockopt(zmq.SUBSCRIBE, b"zmq_fast")
        try:
            run = asyncio.create_task(cli(addresses, "consume", "zmq_fast", "--seconds", "3", "--out", f"zmq+tcp://127.0.0.1:{port}"))
            frames = await asyncio.wait_for(subscriber.recv_multipart(), 15)
            code, out, err = await run
        finally:
            subscriber.close(0)
            context.term()
        assert code == 0 and out == "" and frames[0] == b"zmq_fast" and json.loads(frames[1])["source"] == "zmq_fast"

        unreachable = f"nats://127.0.0.1:{free_port()}"
        code, out, err = await cli(addresses, "consume", "sse_ok", "--seconds", "1", "--out", unreachable)
        assert (code, out) == (1, "") and err.endswith(
            f"error: output {unreachable} failed: NoServersError: nats: no servers available for connection\n"
        )


async def test_every_database_destination_that_nobody_answers_ends_the_run_with_exit_1() -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]  # closed again: nothing listens there
    destinations = [
        f"mongodb://127.0.0.1:{port}/",
        f"cassandra://127.0.0.1:{port}",
        f"redis://127.0.0.1:{port}",
        f"redis+cluster://127.0.0.1:{port}",
        f"bolt://127.0.0.1:{port}",
        f"neo4j://127.0.0.1:{port}",
        f"opensearch://127.0.0.1:{port}",
        f"opensearch://127.0.0.1:{port}?tls=1&verify=0",
    ]
    async with environment() as addresses:
        started = time.monotonic()
        runs = await asyncio.gather(*(cli(addresses, "consume", "sse_ok", "--seconds", "3", "--out", d) for d in destinations))
        elapsed = time.monotonic() - started
    for destination, (code, out, err) in zip(destinations, runs, strict=True):
        assert code == 1 and out == "" and f"error: output {destination} failed: " in err, (destination, err)
    assert elapsed < 60  # MongoDB waits its 10 s server selection; the others give up within seconds


@pytest.mark.databases
async def test_consume_into_mongodb_and_redis_with_the_password_from_the_env_file(tmp_path: Path) -> None:
    import redis
    from pymongo import MongoClient

    from tests import databases as db

    env_file = tmp_path / ".env"
    env_file.write_text(f"STREAM_CONSUMERS_OUTPUT_PASSWORD={db.PASSWORD}\n", encoding="utf-8")
    mongo, store = db.mongo(), db.redis()
    with db.running([mongo, store]):
        mongo_port, redis_port = db.host_port(mongo), db.host_port(store)
        uri = f"mongodb://{db.USER}:{db.PASSWORD}@127.0.0.1:{mongo_port}/?authSource=admin"
        db.wait(mongo, lambda: MongoClient(uri, serverSelectionTimeoutMS=2000).admin.command("ping"), 120)
        db.wait(store, lambda: redis.Redis(port=redis_port, password=db.PASSWORD).ping(), 60)
        async with environment() as addresses:
            for out in (f"mongodb://{db.USER}@127.0.0.1:{mongo_port}/e2e?authSource=admin", f"redis://default@127.0.0.1:{redis_port}/1"):
                code, stdout, err = await cli(
                    addresses, "--env-file", str(env_file), "consume", "sse_ok", "--seconds", "3", "--max-events", "2", "--out", out
                )
                assert code == 0 and stdout == "" and json.loads(err.splitlines()[-1])["events"] == 2 and db.PASSWORD not in err
            code, _, err = await cli(addresses, "consume", "sse_ok", "--seconds", "1", "--out", f"redis://default@127.0.0.1:{redis_port}")
            assert code == 1 and "error: output redis://default@127.0.0.1:" in err and "AuthenticationError" in err
        with MongoClient(uri) as client:
            stored = [d["payload"] for d in client["e2e"]["sse_ok"].find({}, {"_id": 0}).sort("_id", 1)]
        entries = redis.Redis(port=redis_port, db=1, password=db.PASSWORD).xrange("stream_consumers:sse_ok")
    expected = [{"user": "<masked>", "n": 1}, {"user": "<masked>", "n": 2}]
    assert stored == expected and [json.loads(f[b"payload"]) for _, f in entries] == expected


async def test_list_consume_sample_profile_and_errors(tmp_path: Path) -> None:
    async with environment() as addresses:
        code, out, _ = await cli(addresses, "list")
        assert code == 0 and len(out.splitlines()) == len(EXPECTED)

        code, out, err = await cli(addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "2")
        assert code == 0 and [json.loads(line)["payload"] for line in out.splitlines()] == [
            {"user": "<masked>", "n": 1},
            {"user": "<masked>", "n": 2},
        ]
        assert json.loads(err)["events"] == 2

        target = tmp_path / "raw.jsonl"
        code, _, _ = await cli(addresses, "consume", "sse_ok", "--seconds", "3", "--max-events", "1", "--raw", "--out", str(target))
        assert code == 0 and json.loads(target.read_text())["payload"]["user"] == "ana"

        code, _, err = await cli(addresses, "consume", "poll_404", "--seconds", "2")
        assert code == 1 and json.loads(err)["status"] == "error"

        code, _, err = await cli(addresses, "--catalog", "tests.e2e.stalling_catalog", "consume", "stalling", "--seconds", "0.5")
        assert code == 0 and json.loads(err)["events"] == 2

        code, _, err = await cli(addresses, "consume", "nope")
        assert code == 2 and "unknown source: nope" in err

        code, out, _ = await cli(
            addresses,
            "sample",
            "poll_get",
            "ws_ok",
            "--rounds",
            "2",
            "--interval",
            "1",
            "--window",
            "0.6",
            "--reports",
            str(tmp_path / "rounds"),
        )
        assert code == 0 and len(list((tmp_path / "rounds").glob("round-*.json"))) == 2

        code, out, _ = await cli(addresses, "verdict", str(tmp_path / "rounds"), "--planned", "2")
        assert code == 0 and [line.split()[0] for line in out.splitlines()[:2]] == ["poll_get", "ws_ok"]
        assert all("rounds=  2/2" in line for line in out.splitlines()[:2]) and "open" not in out.splitlines()[0]

        more = tmp_path / "rounds" / "more"
        code, out, _ = await cli(
            addresses,
            "sample",
            "ws_ok",
            "sse_ok",
            "--rounds",
            "3",
            "--interval",
            "1",
            "--window",
            "0.6",
            "--reports",
            str(more),
            "--continue-from",
            str(tmp_path / "rounds"),
            "--stop-when-settled",
        )
        # ws_ok has 2 of 3 rounds already; sse_ok none, so it is read in round 3 only and stays open
        assert [json.loads(p.read_text())["number"] for p in more.glob("round-*.json")] == [3]
        assert any(line.startswith("sse_ok") and "rounds=  1/3" in line and line.endswith("open") for line in out.splitlines())

        settled = tmp_path / "settled"
        code, out, _ = await cli(
            addresses,
            "sample",
            "poll_404",
            "--rounds",
            "3",
            "--interval",
            "1",
            "--window",
            "0.3",
            "--reports",
            str(settled),
            "--stop-when-settled",
        )
        # an unreachable source scores 0 events/s: after 2 of 3 rounds its median cannot reach 1, so round 3 is skipped
        assert code == 1 and len(list(settled.glob("round-*.json"))) == 2 and out.splitlines()[-1] == "0 passes, 1 fails, 0 open"

        code, _, err = await cli(addresses, "verdict", str(tmp_path / "nowhere"))
        assert code == 2 and "no such reports directory" in err

        code, _, _ = await cli(
            addresses,
            "profile",
            "sse_all",
            "--max-events",
            "3",
            "--seconds",
            "2",
            "--out",
            str(tmp_path / "profile"),
            "--reports",
            str(tmp_path / "profile"),
        )
        assert code == 0
        (profiles,) = (tmp_path / "profile").glob("profiles-*.json")
        fields = {f["name"]: f for f in json.loads(profiles.read_text())[0]["fields"]}
        assert fields["user"]["example"] == "<masked>" and fields["n"]["kinds"] == ["number"]
        assert fields["n"]["field_class"] == "number" and json.loads(profiles.read_text())[0]["bytes_mean"] > 0


async def test_keys_from_an_env_file_and_rejected_arguments(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("# keys\n\nE2E_KEY='e2e-value-123'\nE2E_SPARE_KEY=spare-456\nOTHER=plain\nnot a pair\n", encoding="utf-8")
    async with environment() as addresses:
        code, out, _ = await cli(addresses, "--env-file", str(env), "consume", "keyed", "--seconds", "1")
        assert code == 0 and json.loads(out)["payload"] == {"key": "used"}
        for argv, message in (
            (["consume", "sse_ok", "--seconds", "0"], "seconds must be positive"),
            (["consume", "sse_ok", "--max-events", "0"], "max_events must be at least 1"),
            (
                ["consume", "sse_ok", "--format", "csv", "--out", "sqlite:never.db"],
                "--format applies to standard output and files, not to sqlite",
            ),
            (["consume", "sse_ok", "--out", "amqp://h:5672/q"], "unknown output scheme 'amqp'"),
            (["consume", "sse_ok", "--out", "zmq+tcp://*"], "zmq+tcp output is zmq+tcp://<interface>:<port>"),
            (["consume", "sse_ok", "--out", "kafka://u:secret@h"], "kafka output takes no user or password: kafka://u:***@h"),
            (["consume", "sse_ok", "--out", "mongodb://u:secret@h/db?bogus=1"], "invalid MongoDB URI mongodb://u:***@h/db?bogus=1"),
            (["consume", "sse_ok", "--out", "cassandra://h/bad-name"], "a Cassandra keyspace is 1 to 48 letters"),
            (["consume", "sse_ok", "--out", "redis://h/zero"], "the path of a redis:// output is a database number"),
            (["consume", "sse_ok", "--out", "redis+cluster://h/1"], "a Redis cluster has no databases to choose"),
            (["consume", "sse_ok", "--out", "opensearch://h?tls=yes"], "option tls is 0 or 1"),
            (["consume", "sse_ok", "--out", "opensearch://h/idx"], "opensearch output takes no path"),
            (["check", "sse_ok", "--concurrency", "0", "--reports", str(tmp_path)], "concurrency"),
            (["sample", "sse_ok", "--concurrency", "0", "--reports", str(tmp_path)], "concurrency"),
            (["sample", "sse_ok", "--rounds", "0", "--reports", str(tmp_path)], "rounds"),
            (["sample", "sse_ok", "--window", "0", "--reports", str(tmp_path)], "positive"),
            (["profile", "sse_ok", "--concurrency", "0", "--reports", str(tmp_path)], "concurrency"),
            (["verdict", str(tmp_path), "--planned", "0"], "planned must be at least 1"),
        ):
            code, _, err = await cli(addresses, *argv)
            assert (code, message in err) == (2, True), (argv, err)
        code, _, err = await cli(addresses, "--catalog", "tests.e2e.duplicate_catalog", "list")
        assert code == 2 and "duplicate source id: ws_ok" in err
        code, out, err = await cli(addresses, "--env-file", str(env), "keys")
        assert code == 1 and "e2e-value-123" not in out and "spare-456" not in out and "plain" not in out
        assert "defines 1 variable(s) neither read by a source nor held" in err
        assert [line.split() for line in out.splitlines()] == [
            ["configured", "E2E_ID", "secret", "optional", "not-set", "https://sign.up/pair"],
            ["configured", "E2E_SECRET", "secret", "optional", "not-set", "https://sign.up/pair"],
            ["configured", "E2E_REGION", "setting", "optional", "default", "default='eu'"],
            ["keyed", "E2E_KEY", "secret", "required", "set", "https://sign.up/e2e"],
            ["settings_only", "E2E_CONTACT", "setting", "optional", "default", "default=''"],
            ["--out", "STREAM_CONSUMERS_OUTPUT_PASSWORD", "secret", "optional", "not-set", "README.md#outputs"],
            ["keyed", "E2E_SPARE_KEY", "held", "-", "set", "https://sign.up/e2e"],
            ["-", "OTHER", "-", "-", "unknown", "not", "read", "by", "any", "source", "and", "not", "held"],
        ]
        env.write_text("E2E_KEY='e2e-value-123'\nE2E_SPARE_KEY=spare-456\n", encoding="utf-8")
        code, _, err = await cli(addresses, "--env-file", str(env), "keys")
        assert (code, err) == (0, "")
        code, out, _ = await cli(addresses, "--env-file", str(env), "keys", "--template")
        assert code == 0 and "e2e-value-123" not in out
        assert "# How: Form; e-mailed.\nE2E_ID=\nE2E_SECRET=\n# Region to read. Default: eu\n# E2E_REGION=eu\n" in out
        assert out.endswith("# --- keyed: Local provider. Second key of the account.\n# Sign-up: https://sign.up/e2e\nE2E_SPARE_KEY=\n")
        assert "spare-456" not in out
        assert "E2E_KEY=\n" in out and "# Contact e-mail. Default: (empty)\n# E2E_CONTACT=\n" in out
        code, out, _ = await cli(addresses, "--catalog", "tests.e2e.no_held_catalog", "keys", "--template")
        assert code == 0 and "Held keys" not in out
        assert out.endswith(
            "E2E_KEY=\n\n# --- --out: credentials of output destinations (README.md#outputs)\n# How: Password of an --out "
            "destination whose URI names a user but no password (keeps it out of the process list).\n"
            "STREAM_CONSUMERS_OUTPUT_PASSWORD=\n"
        )
        code, _, err = await cli(addresses, "--catalog", "tests.e2e.held_clash_catalog", "keys")
        assert code == 2 and "held keys must not be variables a source reads: E2E_KEY" in err
        code, _, err = await cli(addresses, "--catalog", "tests.e2e.output_clash_catalog", "keys")
        assert code == 2 and "output credentials must not be variables a source reads or held keys: STREAM_CONSUMERS_OUTPUT_PASSWORD" in err


async def test_a_reader_that_closes_the_pipe_early_gets_no_traceback() -> None:
    # like `stream-consumers list | head -1`: the reader is gone before the command writes
    read_end, write_end = os.pipe()
    os.close(read_end)
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--rcfile",
        str(ROOT / ".coveragerc.e2e"),
        "-m",
        "stream_consumers",
        "--catalog",
        "tests.e2e.local_catalog",
        "list",
        cwd=ROOT,
        stdout=write_end,
        stderr=asyncio.subprocess.PIPE,
    )
    os.close(write_end)
    _, err = await asyncio.wait_for(process.communicate(), 120)
    assert (process.returncode, err.decode()) == (141, "")


async def test_a_disguised_cancellation_still_ends_the_run_on_time(tmp_path: Path) -> None:
    async with environment() as addresses:
        started = time.monotonic()
        code, out, _ = await cli(addresses, "consume", "disguised_cancel", "--seconds", "1")
        assert code == 0 and [json.loads(line)["payload"] for line in out.splitlines()] == [{"n": 0}]
        assert time.monotonic() - started < 15


# ------------------------------------------------------------------ Ctrl+C and SIGTERM
STOP_WITHIN_S = 2.0
TRANSPORT_SOURCES = ("ws_ok", "sse_ok", "mqtt_tcp", "nats_ok", "zmq_ok", "tcp_lines", "poll_get", "files", "kafka_json")


def command(*argv: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--rcfile",
        str(ROOT / ".coveragerc.e2e"),
        "-m",
        "stream_consumers",
        "--catalog",
        "tests.e2e.local_catalog",
        "--env-file",
        "/nonexistent/.env",
        *argv,
    ]


SIGINT_AS = "import os, signal, sys; signal.signal(signal.SIGINT, getattr(signal, sys.argv[1])); os.execvp(sys.argv[2], sys.argv[2:])"
"""Sets SIGINT's disposition, then becomes the command. The test run may itself have SIGINT ignored (started with
`&` or `nohup`), which a child inherits; a command typed at a terminal has the default (`SIG_DFL`). A wrapper
that execs keeps Python code out of a forked child of this multi-threaded process (no `preexec_fn`)."""


def with_sigint(disposition: str, argv: Sequence[str]) -> list[str]:
    return [sys.executable, "-c", SIGINT_AS, disposition, *argv]


async def spawn(addresses: dict[str, object], *argv: str, sigint: str = "SIG_DFL", **options: object) -> asyncio.subprocess.Process:
    env = dict(os.environ, STREAM_CONSUMERS_E2E=json.dumps(addresses))
    options.setdefault("stdout", asyncio.subprocess.PIPE)
    options.setdefault("stderr", asyncio.subprocess.PIPE)
    return await asyncio.create_subprocess_exec(*with_sigint(sigint, command(*argv)), cwd=ROOT, env=env, **options)  # type: ignore[arg-type]


async def stop_and_finish(process: asyncio.subprocess.Process, sig: signal.Signals) -> tuple[int, str, str, float]:
    """Send `sig`, then collect the exit status, both outputs and the seconds the process took to end."""
    sent = time.monotonic()
    process.send_signal(sig)
    out, err = await asyncio.wait_for(process.communicate(), 60)
    return process.returncode or 0, out.decode(), err.decode(), time.monotonic() - sent


async def until(condition: Callable[[], bool], timeout_s: float = 60) -> None:
    deadline = time.monotonic() + timeout_s
    while not condition():
        assert time.monotonic() < deadline, "condition not met in time"
        await asyncio.sleep(0.05)


@asynccontextmanager
async def watched_silent_server(addresses: dict[str, object]) -> AsyncIterator[asyncio.Event]:
    """Replaces the server of `tcp_silent` by one that also says when the CLI has connected."""
    connected = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        connected.set()
        await hold(reader, writer)

    async with tcp_server(handler) as port:
        addresses["tcp_silent"] = port
        yield connected


async def test_ctrl_c_stops_every_transport_at_once_and_still_writes_the_run_report() -> None:
    async def one(addresses: dict[str, object], source_id: str, sig: signal.Signals) -> None:
        process = await spawn(addresses, "consume", source_id, "--seconds", "120")
        assert process.stdout is not None
        # standard output is handed on per event, so the first one arrives through the pipe while the run goes on
        first = await asyncio.wait_for(process.stdout.readline(), 60)
        code, out, err, took = await stop_and_finish(process, sig)
        expected = -signal.SIGINT if sig is signal.SIGINT else 143
        notice, line = err.splitlines()[-2:]
        assert line.startswith("{"), (source_id, sig.name, err)
        report = json.loads(line)
        assert (code, report["status"]) == (expected, "ok"), (source_id, err)
        assert took < STOP_WITHIN_S, (source_id, took)
        assert notice.startswith(f"stopping ({sig.name}): ending the run") and "Traceback" not in err
        assert report["detail"].startswith(f"stopped by {sig.name} after ") and report["detail"].endswith(" of 120 s")
        assert report["events"] == 1 + len(out.splitlines()) and json.loads(first)["source"] == source_id

    async with environment() as addresses:
        await asyncio.gather(*(one(addresses, s, signal.SIGINT) for s in TRANSPORT_SOURCES))
        # the first runs committed the consumer group's offsets: give the second ones something new to read
        await kafka_produce(str(addresses["kafka"]), "e2e_json", [(None, b'{"n": 3}')])
        await asyncio.gather(*(one(addresses, s, signal.SIGTERM) for s in TRANSPORT_SOURCES))


async def test_a_stopped_run_leaves_every_text_format_and_sqlite_complete(tmp_path: Path) -> None:
    async with environment() as addresses:
        for name in ("json", "csv", "tsv", "jsonl", "pretty"):
            target = tmp_path / f"events.{name}"
            process = await spawn(addresses, "consume", "zmq_fast", "--seconds", "120", "--format", name, "--out", str(target))
            await until(lambda target=target: target.exists() and target.stat().st_size > 10_000)
            code, _, err, _ = await stop_and_finish(process, signal.SIGTERM)
            events = json.loads(err.splitlines()[-1])["events"]
            text = target.read_text(encoding="utf-8")
            assert code == 143 and events > 0, err
            if name == "json":
                assert len(json.loads(text)) == events  # the array was closed
            elif name in ("csv", "tsv"):
                rows = list(csv.reader(io.StringIO(text), delimiter="," if name == "csv" else "\t"))
                assert len(rows) == 1 + events and len({len(row) for row in rows}) == 1  # no row cut short
            elif name == "jsonl":
                assert [json.loads(line)["source"] for line in text.splitlines()] == ["zmq_fast"] * events
            else:
                assert text.count('"source": "zmq_fast"') == events and text.endswith("}\n")
        database = tmp_path / "events.db"

        def stored() -> int:
            if not database.exists():
                return 0
            with contextlib.closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
                try:
                    return int(connection.execute("SELECT count(*) FROM zmq_fast").fetchone()[0])
                except sqlite3.OperationalError:  # the table is not created yet, or the writer holds the lock
                    return 0

        process = await spawn(addresses, "consume", "zmq_fast", "--seconds", "120", "--out", f"sqlite:{database}")
        await until(lambda: stored() > 0)
        code, _, err, _ = await stop_and_finish(process, signal.SIGINT)
        assert code == -signal.SIGINT and stored() == json.loads(err.splitlines()[-1])["events"]  # the last batch was written


async def test_check_and_profile_stopped_report_the_sources_they_started(tmp_path: Path) -> None:
    async with environment() as addresses, watched_silent_server(addresses) as connected:
        argv = ("tcp_silent", "ws_ok", "--seconds", "120", "--concurrency", "1", "--reports", str(tmp_path / "check"))
        process = await spawn(addresses, "check", *argv)
        await asyncio.wait_for(connected.wait(), 60)
        code, out, err, took = await stop_and_finish(process, signal.SIGINT)
        assert code == -signal.SIGINT and took < STOP_WITHIN_S and "stopped by SIGINT: 1 of 2 sources not started" in err
        assert out.startswith("tcp_silent") and out.splitlines()[-1] == "1 sources, 0 delivered or key pending, 1 failed"
        (report,) = (tmp_path / "check").glob("check-*.json")
        (row,) = json.loads(report.read_text())
        assert row["source_id"] == "tcp_silent" and row["detail"].startswith("stopped by SIGINT after")
        connected.clear()
        argv = ("tcp_silent", "ws_ok", "--seconds", "120", "--concurrency", "1", "--out", str(tmp_path / "p"))
        process = await spawn(addresses, "profile", *argv, "--reports", str(tmp_path / "profile"))
        await asyncio.wait_for(connected.wait(), 60)
        code, out, err, _ = await stop_and_finish(process, signal.SIGTERM)
        assert code == 143 and "stopped by SIGTERM: 1 of 2 sources not started" in err
        assert [p.name for p in (tmp_path / "p").iterdir()] == ["tcp_silent.jsonl"]
        assert len(list((tmp_path / "profile").glob("profiles-*.json"))) == 1


async def test_sample_stopped_keeps_its_finished_rounds_and_resumes_from_them(tmp_path: Path) -> None:
    first = tmp_path / "sampling"
    second, elsewhere = first / "segment-2", tmp_path / "elsewhere"  # a continuation inside the first, and one outside
    async with environment() as addresses:
        process = await spawn(addresses, "sample", "ws_ok", "--rounds", "3", "--interval", "120", "--window", "1", "--reports", str(first))
        await until(lambda: any(first.glob("round-01-*.json")))  # round 1 done: now waiting for round 2
        code, out, err, took = await stop_and_finish(process, signal.SIGINT)
        assert code == -signal.SIGINT and took < STOP_WITHIN_S and "rounds=  1/3" in out
        assert f"stopped by SIGINT: 1 of 3 rounds recorded; a round cut short is not recorded; resume with --continue-from {first}" in err
        for reports, advice in (
            (second, f"resume with --continue-from {first}"),
            (elsewhere, f"the rounds are in {first} and {elsewhere}: move them under one directory"),
        ):
            async with watched_silent_server(addresses) as connected:
                argv = ("tcp_silent", "--rounds", "3", "--interval", "120", "--window", "60", "--reports", str(reports))
                process = await spawn(addresses, "sample", *argv, "--continue-from", str(first))
                await asyncio.wait_for(connected.wait(), 60)  # round 2 is reading
                code, _, err, took = await stop_and_finish(process, signal.SIGTERM)
            assert code == 143 and took < STOP_WITHIN_S and f"1 of 3 rounds recorded; a round cut short is not recorded; {advice}" in err
            assert not list(reports.glob("round-*.json"))  # the round cut short was not written
        code, out, _ = await cli(addresses, "verdict", str(first), "--planned", "3")
        assert code == 0 and "rounds=  1/3" in out


async def test_a_second_signal_ends_a_run_stuck_in_writing_at_once(tmp_path: Path) -> None:
    fifo = tmp_path / "stuck"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)  # never read: once the pipe is full, every write blocks
    try:
        async with environment() as addresses:
            process = await spawn(addresses, "consume", "zmq_fast", "--seconds", "120", "--out", str(fifo))
            await asyncio.sleep(3)  # the pipe fills within milliseconds of the first events
            process.send_signal(signal.SIGINT)
            await asyncio.sleep(0.005)
            process.send_signal(signal.SIGINT)  # within the repeat window: the same request again, absorbed
            await asyncio.sleep(1.5)  # later than the repeat window, as a person pressing again
            assert process.returncode is None  # still stuck in the write: the first signal could only ask
            code, _, err, took = await stop_and_finish(process, signal.SIGINT)
        assert code == -signal.SIGINT and took < STOP_WITHIN_S
        assert err.endswith("stopped immediately by a second SIGINT; outputs may be incomplete\n")
    finally:
        os.close(reader)


async def test_one_stop_delivered_twice_at_once_still_ends_the_run_cleanly(tmp_path: Path) -> None:
    # `timeout` signals its child and then its process group; through `uv run` the program gets both
    target = tmp_path / "events.json"
    async with environment() as addresses:
        process = await spawn(addresses, "consume", "zmq_fast", "--seconds", "120", "--format", "json", "--out", str(target))
        await until(lambda: target.exists() and target.stat().st_size > 1_000)
        process.send_signal(signal.SIGTERM)
        await asyncio.sleep(0.005)  # the first one is handled by now (back to back, the kernel merges them)
        code, _, err, took = await stop_and_finish(process, signal.SIGTERM)
    assert code == 143 and took < STOP_WITHIN_S and "stopped immediately" not in err
    assert len(json.loads(target.read_text(encoding="utf-8"))) == json.loads(err.splitlines()[-1])["events"]


async def test_a_job_started_with_sigint_ignored_keeps_ignoring_it_and_stops_on_sigterm() -> None:
    async with environment() as addresses:
        process = await spawn(addresses, "consume", "ws_ok", "--seconds", "120", sigint="SIG_IGN")
        assert process.stdout is not None
        await asyncio.wait_for(process.stdout.readline(), 60)
        process.send_signal(signal.SIGINT)
        await asyncio.sleep(1)
        assert process.returncode is None
        code, _, err, took = await stop_and_finish(process, signal.SIGTERM)
    assert code == 143 and took < STOP_WITHIN_S and "stopped by SIGTERM after" in err


def on_terminal(argv: Sequence[str], press_after: Callable[[str], bool]) -> tuple[int, str]:
    """Run `argv` on a pseudo-terminal and type Ctrl+C (byte 0x03) once `press_after(output so far)` holds.

    The terminal sends SIGINT to its whole foreground process group, as when a person presses Ctrl+C.
    `setsid --ctty` (util-linux) makes the pseudo-terminal the command's controlling terminal."""
    master, slave = os.openpty()
    process = subprocess.Popen(with_sigint("SIG_DFL", ["setsid", "--ctty", *argv]), cwd=ROOT, stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output, pressed, deadline = b"", False, time.monotonic() + 120
    while time.monotonic() < deadline:
        if not pressed and press_after(output.decode(errors="replace")):
            os.write(master, b"\x03")
            pressed = True
        ready, _, _ = select.select([master], [], [], 0.05)
        if ready:
            try:
                chunk = os.read(master, 65536)
            except OSError:  # the terminal closed: the command ended
                break
            if not chunk:
                break
            output += chunk
    status = process.wait(60)
    os.close(master)
    return status, output.decode(errors="replace").replace("\r", "")


async def test_ctrl_c_on_a_terminal_also_stops_the_shell_loop_that_runs_the_command() -> None:
    async with environment() as addresses:
        os.environ["STREAM_CONSUMERS_E2E"] = json.dumps(addresses)
        try:
            run = shlex.join(command("consume", "ws_ok", "--seconds", "120"))
            script = f"for n in 1 2 3; do {run}; echo after-run-$n; done; echo loop-finished"
            status, output = await asyncio.to_thread(on_terminal, ["bash", "-c", script], lambda text: '"source": "ws_ok"' in text)
        finally:
            del os.environ["STREAM_CONSUMERS_E2E"]
    assert "stopping (SIGINT): ending the run" in output and '"detail": "stopped by SIGINT after' in output
    assert "after-run" not in output and "loop-finished" not in output and "Traceback" not in output
    assert status == -signal.SIGINT  # bash saw its command ended by SIGINT and ended too
