"""The installed CLI, run as a subprocess under coverage, against local servers for every transport."""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import time
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

import fastavro
import pytest
import websockets
from aiohttp import web

from stream_consumers.application.consume_service import ATTRIBUTE_SAMPLE
from tests.servers import MqttBroker, NatsServer, http_server, kafka_broker, kafka_produce, tcp_server, ws_server, zmq_publisher

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
        assert code == 0 and out.endswith("E2E_KEY=\n") and "Held keys" not in out
        code, _, err = await cli(addresses, "--catalog", "tests.e2e.held_clash_catalog", "keys")
        assert code == 2 and "held keys must not be variables a source reads: E2E_KEY" in err


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
