"""The CLI composition root, in-process, over a scripted catalog."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import runpy
import socket
import sqlite3
import sys
from pathlib import Path

import pytest

from stream_consumers.adapters.inbound.cli import DEFAULT_CATALOG, SIGPIPE_EXIT, _parser, main
from tests.support import FakeSecrets

CATALOG = ["--catalog", "tests.catalog_scripted"]


def run(*argv: str, env_file: Path | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    extra = ["--env-file", str(env_file)] if env_file else ["--env-file", "/nonexistent/.env"]
    code = main([*CATALOG, *extra, *argv], out, err)
    return code, out.getvalue(), err.getvalue()


def test_list_prints_one_json_line_per_source_sorted() -> None:
    code, out, _ = run("list")
    rows = [json.loads(line) for line in out.splitlines()]
    assert code == 0 and [r["id"] for r in rows] == ["alpha", "broken", "keyed", "quiet"]
    assert rows[0]["group"] == "A" and rows[0]["personal_fields"] == ["user"] and rows[3]["group"] == "E"


def test_default_catalog_lists_the_73_sources_8_of_them_low_rate() -> None:
    out = io.StringIO()
    assert main(["list"], out, io.StringIO()) == 0
    groups = [json.loads(line)["group"] for line in out.getvalue().splitlines()]
    assert len(groups) == 73 and groups.count("E") == 8 and DEFAULT_CATALOG.endswith(".sources")


def test_a_reader_that_closed_the_pipe_ends_the_command_without_a_traceback() -> None:
    read_end, write_end = os.pipe()
    os.close(read_end)
    with os.fdopen(write_end, "w") as out:
        assert main([*CATALOG, "list"], out, io.StringIO()) == SIGPIPE_EXIT == 141
        out.write("buffered text now goes to /dev/null\n")


class TestConsume:
    def test_to_stdout_masked_with_the_report_on_stderr(self) -> None:
        code, out, err = run("consume", "alpha", "--seconds", "0.2", "--max-events", "2")
        events = [json.loads(line) for line in out.splitlines()]
        report = json.loads(err)
        assert code == 0 and [e["payload"] for e in events] == [{"user": "<masked>", "n": 1}, {"user": "<masked>", "n": 2}]
        assert report["status"] == "ok" and report["events"] == 2 and report["rate_basis"] == "observed"

    @pytest.mark.parametrize(("name", "delimiter"), [("csv", ","), ("tsv", "\t")])
    def test_delimited_formats_to_standard_output(self, name: str, delimiter: str) -> None:
        code, out, _ = run("consume", "alpha", "--seconds", "0.2", "--max-events", "2", "--format", name)
        rows = [line.split(delimiter) for line in out.splitlines()]
        assert code == 0 and rows[0] == ["source", "received_at", "payload.user", "payload.n", "extra"]
        assert [(r[0], r[2], r[3], r[4]) for r in rows[1:]] == [("alpha", "<masked>", "1", ""), ("alpha", "<masked>", "2", "")]

    def test_a_json_array_file(self, tmp_path: Path) -> None:
        target = tmp_path / "a.json"
        code, _, _ = run("consume", "alpha", "--seconds", "0.2", "--max-events", "2", "--format", "json", "--out", str(target))
        assert code == 0 and [e["payload"]["n"] for e in json.loads(target.read_text(encoding="utf-8"))] == [1, 2]

    def test_into_sqlite(self, tmp_path: Path) -> None:
        target = tmp_path / "db" / "events.db"
        code, out, _ = run("consume", "alpha", "--seconds", "0.2", "--max-events", "2", "--out", f"sqlite:{target}")
        with contextlib.closing(sqlite3.connect(target)) as db:
            stored = [json.loads(p) for (p,) in db.execute("SELECT payload FROM alpha ORDER BY seq")]
        assert code == 0 and out == "" and stored == [{"user": "<masked>", "n": 1}, {"user": "<masked>", "n": 2}]

    @pytest.mark.parametrize(
        ("argv", "message"),
        [
            (["--out", "sqlite:{tmp}/x.db", "--format", "csv"], "error: --format applies to standard output and files, not to sqlite"),
            (
                ["--out", "amqp://h:5672/q"],
                "error: unknown output scheme 'amqp' (known: bolt, cassandra, kafka, mongodb, mqtt, nats, neo4j, opensearch, redis, "
                "redis+cluster, sqlite, zmq+tcp)",
            ),
            (
                ["--out", "mongodb://ana:pw@h/db?bogus=1"],
                "error: invalid MongoDB URI mongodb://ana:***@h/db?bogus=1: Unknown option: bogus. Did you mean one of (timeoutms, "
                "wtimeoutms, journal) or maybe a camelCase version of one? Refer to docstring.",
            ),
            (["--out", "mongodb://ana:pw@h:99999"], "error: invalid port '99999' in mongodb://ana:***@h:99999"),
            (["--out", "cassandra://h/bad-name"], "error: a Cassandra keyspace is 1 to 48 letters, digits or _, got 'bad-name'"),
            (["--out", "cassandra://h?consistency=one"], "error: unknown option(s) consistency for cassandra (known: none)"),
            (["--out", "redis://h/zero"], "error: the path of a redis:// output is a database number, got 'zero'"),
            (["--out", "redis://h1,h2"], "error: redis output takes exactly one host:port: redis://h1,h2"),
            (
                ["--out", "redis+cluster://h:7000/1"],
                "error: a Redis cluster has no databases to choose: remove '1' from redis+cluster://h:7000/1",
            ),
            (["--out", "neo4j://h1,h2"], "error: neo4j output takes exactly one host:port: neo4j://h1,h2"),
            (["--out", "opensearch://h?tls=yes"], "error: option tls is 0 or 1, got 'yes' in opensearch://h?tls=yes"),
            (["--out", "opensearch://h?ssl=1"], "error: unknown option(s) ssl for opensearch (known: tls, verify)"),
            (
                ["--out", "opensearch://h/idx"],
                "error: opensearch output takes no path (indices are stream_consumers-<source>): opensearch://h/idx",
            ),
            (["--out", "sqlite:"], "error: missing location after sqlite:"),
            (["--out", "kafka://ana:pw@h/t"], "error: kafka output takes no user or password: kafka://ana:***@h/t"),
            (["--out", "mqtt://h1,h2/t"], "error: mqtt output takes exactly one host:port: mqtt://h1,h2/t"),
            (["--out", "nats://h/s?tls=1"], "error: unknown option(s) tls for nats (known: none)"),
            (["--out", "kafka:t"], "error: kafka needs kafka://host:port..., got kafka:t"),
            (["--out", "zmq+tcp://*"], "error: zmq+tcp output is zmq+tcp://<interface>:<port> (the address it binds), got zmq+tcp://*"),
            (
                ["--out", "zmq+tcp://*:5555/x"],
                "error: zmq+tcp output is zmq+tcp://<interface>:<port> (the address it binds), got zmq+tcp://*:5555/x",
            ),
        ],
    )
    def test_rejected_destinations_create_nothing(self, argv: list[str], message: str, tmp_path: Path) -> None:
        code, _, err = run("consume", "alpha", "--seconds", "0.1", *(a.format(tmp=tmp_path) for a in argv))
        assert code == 2 and err == message + "\n" and list(tmp_path.iterdir()) == []

    def test_an_output_that_cannot_be_opened_exits_1(self) -> None:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        code, out, err = run("consume", "alpha", "--seconds", "0.1", "--out", f"nats://127.0.0.1:{port}")
        assert (
            code == 1
            and out == ""
            and err == f"error: output nats://127.0.0.1:{port} failed: NoServersError: nats: no servers available for connection\n"
        )

    def test_raw_to_a_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out" / "a.jsonl"
        code, out, _ = run("consume", "alpha", "--seconds", "0.1", "--raw", "--out", str(target))
        assert code == 0 and out == ""
        assert [json.loads(line)["payload"]["user"] for line in target.read_text().splitlines()] == ["ana", "beto"]

    def test_missing_key_is_reported_with_the_sign_up_link(self) -> None:
        code, _, err = run("consume", "keyed", "--seconds", "0.1")
        report = json.loads(err)
        assert code == 0 and report["status"] == "key-pending" and "https://sign.up/here" in report["detail"]

    def test_key_from_the_env_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("SCRIPTED_KEY=abc\n")
        code, out, _ = run("consume", "keyed", "--seconds", "0.1", env_file=env)
        assert code == 0 and json.loads(out)["payload"] == {"key_used": True}

    def test_a_failing_source_exits_1(self) -> None:
        code, _, err = run("consume", "broken", "--seconds", "0.1")
        assert code == 1 and json.loads(err)["status"] == "error"

    def test_an_unknown_source_exits_2(self) -> None:
        code, _, err = run("consume", "nope", "--seconds", "0.1")
        assert code == 2 and err == "error: unknown source: nope\n"


class TestCheck:
    def test_without_ids_every_active_source_and_no_low_rate_one(self, tmp_path: Path) -> None:
        code, out, _ = run("check", "--seconds", "0.1", "--reports", str(tmp_path))
        lines = out.splitlines()
        assert code == 1 and lines[-1] == "3 sources, 2 delivered or key pending, 1 failed"
        assert [line.split()[0] for line in lines[:3]] == ["alpha", "broken", "keyed"]
        (report,) = tmp_path.glob("check-*.json")
        assert {r["source_id"] for r in json.loads(report.read_text())} == {"alpha", "broken", "keyed"}

    def test_a_low_rate_source_runs_when_named(self, tmp_path: Path) -> None:
        code, out, _ = run("check", "quiet", "--seconds", "0.1", "--reports", str(tmp_path))
        assert code == 0 and out.startswith("quiet") and out.endswith("1 sources, 1 delivered or key pending, 0 failed\n")

    def test_selected_sources_pass(self, tmp_path: Path) -> None:
        code, out, _ = run("check", "alpha", "--seconds", "0.1", "--reports", str(tmp_path))
        assert code == 0 and "rate=" in out and out.endswith("1 sources, 1 delivered or key pending, 0 failed\n")

    def test_unknown_ids_are_rejected_before_running(self, tmp_path: Path) -> None:
        code, _, err = run("check", "alpha", "zzz", "--reports", str(tmp_path))
        assert code == 2 and "zzz" in err and not list(tmp_path.iterdir())


def test_sample_writes_one_report_per_round(tmp_path: Path) -> None:
    code, out, _ = run("sample", "alpha", "--rounds", "2", "--interval", "0.15", "--window", "0.1", "--reports", str(tmp_path))
    assert code == 0 and out.startswith("alpha")
    assert sorted(p.name[:8] for p in tmp_path.glob("round-*.json")) == ["round-01", "round-02"]


def test_sample_stops_settled_sources_and_prints_their_verdicts(tmp_path: Path) -> None:
    argv = ["alpha", "broken", "--rounds", "5", "--interval", "0.05", "--window", "0.05", "--reports", str(tmp_path)]
    code, out, _ = run("sample", *argv, "--stop-when-settled")
    assert code == 1  # broken's last round failed
    assert sorted(p.name[:8] for p in tmp_path.glob("round-*.json")) == ["round-01", "round-02", "round-03"]
    lines = out.splitlines()
    assert any(line.startswith("alpha") and "rounds=  3/5" in line and line.endswith("passes") for line in lines)
    assert any(line.startswith("broken") and "median=0.000/s" in line and line.endswith("fails") for line in lines)
    assert lines[-1] == "1 passes, 1 fails, 0 open"


def test_sample_continues_an_interrupted_run_and_verdict_reads_every_segment(tmp_path: Path) -> None:
    first, second = tmp_path / "segment-1", tmp_path / "segment-2"
    assert run("sample", "alpha", "--rounds", "2", "--interval", "0.05", "--window", "0.05", "--reports", str(first))[0] == 0
    code, out, _ = run(
        "sample",
        "alpha",
        "--rounds",
        "3",
        "--interval",
        "0.05",
        "--window",
        "0.05",
        "--reports",
        str(second),
        "--continue-from",
        str(tmp_path),
    )
    assert code == 0 and [p.name[:8] for p in second.glob("round-*.json")] == ["round-03"]
    assert "rounds=  3/3" in out
    code, out, _ = run("verdict", str(tmp_path), "--planned", "24")
    assert (
        code == 0
        and out.splitlines()[0].startswith("alpha")
        and "rounds=  3/24" in out
        and out.splitlines()[-1] == "0 passes, 0 fails, 1 open"
    )
    code, _, err = run("verdict", str(tmp_path / "missing"))
    assert code == 2 and "no such reports directory" in err


def test_profile_writes_its_samples_in_the_chosen_format(tmp_path: Path) -> None:
    code, _, _ = run(
        "profile",
        "alpha",
        "--max-events",
        "5",
        "--seconds",
        "0.1",
        "--out",
        str(tmp_path / "p"),
        "--reports",
        str(tmp_path),
        "--format",
        "csv",
    )
    assert code == 0 and (tmp_path / "p" / "alpha.csv").read_text(encoding="utf-8").splitlines()[1].startswith("alpha,")


def test_profile_writes_masked_events_and_field_statistics(tmp_path: Path) -> None:
    code, _, _ = run("profile", "alpha", "--max-events", "5", "--seconds", "0.1", "--out", str(tmp_path / "p"), "--reports", str(tmp_path))
    assert code == 0
    lines = (tmp_path / "p" / "alpha.jsonl").read_text().splitlines()
    assert [json.loads(line)["payload"]["user"] for line in lines] == ["<masked>", "<masked>"]
    (report,) = tmp_path.glob("profiles-*.json")
    fields = {f["name"]: f for f in json.loads(report.read_text())[0]["fields"]}
    assert fields["user"]["distinct"] == 2 and fields["user"]["example"] == "<masked>"


def test_keys_shows_status_and_template_without_values(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("SCRIPTED_KEY=very-secret\nSCRIPTED_SPARE_KEY=spare-secret\nSTREAM_CONSUMERS_OUTPUT_PASSWORD=db-secret\n")
    code, out, _ = run("keys", env_file=env)
    assert code == 0 and "very-secret" not in out and "spare-secret" not in out and "db-secret" not in out
    assert [line.split() for line in out.splitlines()] == [
        ["keyed", "SCRIPTED_KEY", "secret", "required", "set", "https://sign.up/here"],
        ["--out", "STREAM_CONSUMERS_OUTPUT_PASSWORD", "secret", "optional", "set", "README.md#outputs"],
        ["keyed", "SCRIPTED_SPARE_KEY", "held", "-", "set", "https://sign.up/here"],
    ]
    code, out, _ = run("keys")
    assert code == 0 and [line.split()[4] for line in out.splitlines()] == ["MISSING", "not-set", "not-set"]
    code, out, _ = run("keys", "--template", env_file=env)
    assert code == 0 and "SCRIPTED_KEY=\n" in out and "SCRIPTED_SPARE_KEY=\n" in out and "-secret" not in out


def test_keys_fails_on_a_variable_no_source_reads(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("SCRIPTED_KEY=very-secret\nLEFTOVER_SECRET=also-secret\n")
    code, out, err = run("keys", env_file=env)
    assert code == 1 and "also-secret" not in out + err and "very-secret" not in out + err
    assert out.splitlines()[-1].split() == [
        "-",
        "LEFTOVER_SECRET",
        "-",
        "-",
        "unknown",
        *["not", "read", "by", "any", "source", "and", "not", "held"],
    ]
    assert "defines 1 variable(s) neither read by a source nor held" in err
    code, out, _ = run("keys", "--template", env_file=env)
    assert code == 0 and "LEFTOVER_SECRET" not in out


def test_keys_shows_settings_with_their_default() -> None:
    out = io.StringIO()
    assert main(["keys"], out, io.StringIO()) == 0
    assert any(
        line.split()[:5] == ["crossref", "CROSSREF_MAILTO", "setting", "optional", "default"] for line in out.getvalue().splitlines()
    )


def test_unknown_command_is_an_argparse_error() -> None:
    with pytest.raises(SystemExit) as error:
        main(["frobnicate"], io.StringIO(), io.StringIO())
    assert error.value.code == 2


def test_module_entry_point(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["stream-consumers", *CATALOG, "list"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("stream_consumers", run_name="__main__")
    assert error.value.code == 0 and capsys.readouterr().out.count("\n") == 4


def test_every_option_with_a_default_states_it_in_its_help() -> None:
    parser = _parser()
    (commands,) = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    actions = [a for p in (parser, *commands.choices.values()) for a in p._actions]
    stated = [a for a in actions if a.default not in (None, False, argparse.SUPPRESS) and a.nargs != "*"]
    assert stated and all("(default: " in str(a.help) for a in stated)
    numeric = [a for a in stated if isinstance(a.default, int | float)]
    assert all(f"(default: {a.default:g})" in str(a.help) for a in numeric)
    paths = [a for a in stated if isinstance(a.default, Path)]
    assert all(f"(default: {a.default})" in str(a.help) for a in paths)
    assert "(default: -)" in str(next(a for a in actions if a.dest == "out" and a.default == "-").help)


def test_broker_destinations_are_built_from_the_target() -> None:
    from stream_consumers.adapters.inbound.cli import _event_sink
    from stream_consumers.adapters.outbound.outputs.brokers import KafkaEventSink, MqttEventSink, NatsEventSink, ZeroMqEventSink
    from stream_consumers.adapters.outbound.system.clock import SystemClock

    clock, out = SystemClock(), io.StringIO()
    kafka = _event_sink("kafka://k1,[::1]:9093", None, out, clock, FakeSecrets())
    assert (
        isinstance(kafka, KafkaEventSink)
        and kafka._bootstrap == ["k1:9092", "[::1]:9093"]
        and kafka._template == "stream_consumers.{source}"
    )
    mqtt = _event_sink("mqtt://ana:pw@m/lab/{source}/events", None, out, clock, FakeSecrets())
    assert isinstance(mqtt, MqttEventSink) and (mqtt._host, mqtt._port, mqtt._template, mqtt._user, mqtt._password) == (
        "m",
        1883,
        "lab/{source}/events",
        "ana",
        "pw",
    )
    assert _event_sink("mqtt://m:8883", None, out, clock, FakeSecrets())._template == "stream_consumers/{source}"  # type: ignore[attr-defined]
    nats = _event_sink("nats://n1,n2:4333/all", None, out, clock, FakeSecrets())
    assert isinstance(nats, NatsEventSink) and nats._servers == ["nats://n1:4222", "nats://n2:4333"] and nats._template == "all"
    zeromq = _event_sink("zmq+tcp://*:5556", None, out, clock, FakeSecrets())
    assert isinstance(zeromq, ZeroMqEventSink) and zeromq._endpoint == "tcp://*:5556"
    assert mqtt._label == "mqtt://ana:***@m/lab/{source}/events"


def test_database_destinations_are_built_from_the_target() -> None:
    from stream_consumers.adapters.inbound.cli import _event_sink
    from stream_consumers.adapters.outbound.outputs.databases import (
        CassandraEventSink,
        MongoDbEventSink,
        Neo4jEventSink,
        OpenSearchEventSink,
        RedisEventSink,
    )
    from stream_consumers.adapters.outbound.system.clock import SystemClock

    clock, out, none = SystemClock(), io.StringIO(), FakeSecrets()
    mongo = _event_sink("mongodb://ana:pw@m1:27011,m2:27012/lab?replicaSet=rs0&authSource=admin", None, out, clock, none)
    assert isinstance(mongo, MongoDbEventSink) and mongo._uri == "mongodb://ana:pw@m1:27011,m2:27012/lab?replicaSet=rs0&authSource=admin"
    assert mongo._password is None and mongo._label == "mongodb://ana:***@m1:27011,m2:27012/lab?replicaSet=rs0&authSource=admin"
    cassandra = _event_sink("cassandra://cassandra:pw@c1:9041,c2:9042,c3", None, out, clock, none)
    assert isinstance(cassandra, CassandraEventSink)
    assert (cassandra._hosts, cassandra._keyspace, cassandra._user, cassandra._password) == (
        [("c1", 9041), ("c2", 9042), ("c3", 9042)],
        "stream_consumers",
        "cassandra",
        "pw",
    )
    assert _event_sink("cassandra://c/lab_ks", None, out, clock, none)._keyspace == "lab_ks"  # type: ignore[attr-defined]
    redis = _event_sink("redis://:pw@r:6380/2", None, out, clock, none)
    assert isinstance(redis, RedisEventSink) and (redis._hosts, redis._db, redis._user, redis._password, redis._cluster) == (
        [("r", 6380)],
        2,
        None,
        "pw",
        False,
    )
    cluster = _event_sink("redis+cluster://default:pw@127.0.0.1:6381,127.0.0.1:6382", None, out, clock, none)
    assert isinstance(cluster, RedisEventSink) and cluster._cluster and cluster._hosts == [("127.0.0.1", 6381), ("127.0.0.1", 6382)]
    assert cluster._remap(("172.20.0.5", 6382)) == ("127.0.0.1", 6382) and cluster._remap(("10.0.0.9", 7000)) == ("10.0.0.9", 7000)
    assert _event_sink("redis://r", None, out, clock, none)._db == 0  # type: ignore[attr-defined]
    neo4j = _event_sink("bolt://neo4j:pw@n/lab", None, out, clock, none)
    assert isinstance(neo4j, Neo4jEventSink) and (neo4j._uri, neo4j._database, neo4j._auth) == ("bolt://n:7687", "lab", ("neo4j", "pw"))
    routed = _event_sink("neo4j://[::1]:7688", None, out, clock, none)
    assert (routed._uri, routed._database, routed._auth) == ("neo4j://[::1]:7688", None, None)  # type: ignore[attr-defined]
    search = _event_sink("opensearch://admin:pw@o1:9201,o2:9202?tls=1&verify=0", None, out, clock, none)
    assert isinstance(search, OpenSearchEventSink)
    assert (search._hosts, search._tls, search._verify, search._auth) == (
        [{"host": "o1", "port": 9201}, {"host": "o2", "port": 9202}],
        True,
        False,
        ("admin", "pw"),
    )
    plain = _event_sink("opensearch://o", None, out, clock, none)
    assert (plain._hosts, plain._tls, plain._verify, plain._auth) == ([{"host": "o", "port": 9200}], False, True, None)  # type: ignore[attr-defined]


def test_a_password_from_the_environment_when_the_uri_names_a_user_without_one() -> None:
    from stream_consumers.adapters.inbound.cli import _event_sink
    from stream_consumers.adapters.outbound.system.clock import SystemClock

    clock, out = SystemClock(), io.StringIO()
    secrets = FakeSecrets({"STREAM_CONSUMERS_OUTPUT_PASSWORD": "from-env"})
    mongo = _event_sink("mongodb://ana@m/?authSource=admin", None, out, clock, secrets)
    assert (mongo._uri, mongo._password, mongo._label) == (
        "mongodb://ana@m/?authSource=admin",
        "from-env",
        "mongodb://ana@m/?authSource=admin",
    )  # type: ignore[attr-defined]
    assert _event_sink("cassandra://cassandra@c", None, out, clock, secrets)._password == "from-env"  # type: ignore[attr-defined]
    assert _event_sink("mqtt://ana@m", None, out, clock, secrets)._password == "from-env"  # type: ignore[attr-defined]
    # a password in the URI wins; no user, or no variable, leaves the password unset
    assert _event_sink("mongodb://ana:in-uri@m", None, out, clock, secrets)._password is None  # type: ignore[attr-defined]
    assert _event_sink("cassandra://ana:in-uri@c", None, out, clock, secrets)._password == "in-uri"  # type: ignore[attr-defined]
    assert _event_sink("cassandra://c", None, out, clock, secrets)._password is None  # type: ignore[attr-defined]
    assert _event_sink("cassandra://ana@c", None, out, clock, FakeSecrets())._password is None  # type: ignore[attr-defined]
