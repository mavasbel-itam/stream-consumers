"""Command-line interface and composition root: the only place concrete classes are named."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

from stream_consumers.adapters.outbound.outputs.brokers import KafkaEventSink, MqttEventSink, NatsEventSink, ZeroMqEventSink
from stream_consumers.adapters.outbound.outputs.formats import (
    CsvFormat,
    JsonArrayFormat,
    JsonLinesFormat,
    PrettyJsonFormat,
    TsvFormat,
)
from stream_consumers.adapters.outbound.outputs.history import JsonSamplingHistory
from stream_consumers.adapters.outbound.outputs.sinks import (
    JsonReportSink,
    NullEventSink,
    TextFileEventSink,
    TextFileSinkFactory,
    TextStreamEventSink,
)
from stream_consumers.adapters.outbound.outputs.sqlite import SqliteEventSink
from stream_consumers.adapters.outbound.providers.held_keys import StaticHeldKeyCatalog
from stream_consumers.adapters.outbound.providers.http import AiohttpClient
from stream_consumers.adapters.outbound.providers.registry import FactoryRegistry
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.adapters.outbound.system.environment import EnvSecretProvider
from stream_consumers.application.check_service import CheckService
from stream_consumers.application.configuration_service import ConfigurationService
from stream_consumers.application.consume_service import ConsumeService
from stream_consumers.application.list_service import ListService
from stream_consumers.application.profile_service import ProfileService
from stream_consumers.application.sample_service import SampleService
from stream_consumers.application.verdict_service import VerdictService
from stream_consumers.domain.errors import OutputError, OutputTargetError, StreamConsumersError
from stream_consumers.domain.models import ConfigKind, RateVerdict, RunReport, RunStatus, Verdict
from stream_consumers.domain.outputs import TERMINAL, OutputTarget, check_target, endpoints, parse_target
from stream_consumers.ports.outbound.outputs import EventFormatPort, EventSinkPort
from stream_consumers.ports.outbound.providers import (
    HeldKeyCatalogPort,
    HttpClientPort,
    SourceDependencies,
    SourceFactoryPort,
    SourceRegistryPort,
)
from stream_consumers.ports.outbound.system import ClockPort

USER_AGENT = "stream-consumers/0.1 (ITAM COM-22102 course research; non-commercial)"
DEFAULT_CATALOG = "stream_consumers.adapters.outbound.providers.sources"
SIGPIPE_EXIT = 141  # 128 + SIGPIPE: what a shell reports for a writer whose reader closed the pipe
FORMATS: Mapping[str, EventFormatPort] = {
    f.name: f for f in (JsonLinesFormat(), CsvFormat(), TsvFormat(), JsonArrayFormat(), PrettyJsonFormat())
}
DEFAULT_FORMAT = "jsonl"
DEFAULT_TOPIC = "stream_consumers.{source}"
"""Kafka topic and NATS subject when `--out` names none; MQTT uses `stream_consumers/{source}`."""


def _host_port(host: str, port: int) -> str:
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def _kafka(target: OutputTarget, clock: ClockPort) -> EventSinkPort:
    check_target(target)
    bootstrap = [_host_port(h, p) for h, p in endpoints(target, 9092)]
    return KafkaEventSink(bootstrap, target.path or DEFAULT_TOPIC, clock, target.display)


def _mqtt(target: OutputTarget, clock: ClockPort) -> EventSinkPort:
    check_target(target, credentials=True, one_host=True)
    ((host, port),) = endpoints(target, 1883)
    topic = target.path or "stream_consumers/{source}"
    return MqttEventSink(host, port, topic, clock, target.display, target.user, target.password)


def _nats(target: OutputTarget, clock: ClockPort) -> EventSinkPort:
    check_target(target, credentials=True)
    servers = [f"nats://{_host_port(h, p)}" for h, p in endpoints(target, 4222)]
    return NatsEventSink(servers, target.path or DEFAULT_TOPIC, clock, target.display, target.user, target.password)


def _zeromq(target: OutputTarget, clock: ClockPort) -> EventSinkPort:
    check_target(target, one_host=True)
    ((host, port),) = target.hosts
    if port is None or target.path:
        raise OutputTargetError(f"zmq+tcp output is zmq+tcp://<interface>:<port> (the address it binds), got {target.display}")
    return ZeroMqEventSink(f"tcp://{_host_port(host, port)}", target.display)


SINKS: Mapping[str, Callable[[OutputTarget, ClockPort], EventSinkPort]] = {
    "sqlite": lambda target, clock: SqliteEventSink(Path(target.location), clock),
    "kafka": _kafka,
    "mqtt": _mqtt,
    "nats": _nats,
    "zmq+tcp": _zeromq,
}
"""Destinations of `consume --out` other than the terminal and files, by URI scheme."""
DEFAULT_SOURCES_HELP = "source ids (default: every source outside the low-rate group E; name a low-rate source to run it)"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stream-consumers", description="Consume public real-time data streams.")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG, help="module exposing FACTORIES (default: the built-in sources)")
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="git-ignored file with API keys (default: .env)")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="list the sources as JSON lines")

    keys = commands.add_parser("keys", help="show which API credentials and settings are set (never their values)")
    keys.add_argument("--template", action="store_true", help="print a .env template instead")

    consume = commands.add_parser("consume", help="write the events of one source to the terminal, a file or a database")
    consume.add_argument("source", help="source id (see `list`)")
    consume.add_argument(
        "--seconds", type=float, default=60.0, help="seconds to consume, at least the source's minimum window (default: 60)"
    )
    consume.add_argument("--max-events", type=int, help="stop after this many events (default: no limit)")
    consume.add_argument(
        "--out",
        default="-",
        help="where events go: - for standard output, a file path, or a destination (sqlite:, kafka://, mqtt://, nats://, zmq+tcp://; README 'Outputs') (default: -)",
    )
    consume.add_argument(
        "--format",
        choices=list(FORMATS),
        help=f"text format for standard output and files: {', '.join(FORMATS)} (default: {DEFAULT_FORMAT})",
    )
    consume.add_argument("--raw", action="store_true", help="do not mask personal fields")

    check = commands.add_parser("check", help="consume each source briefly and report whether events arrive")
    check.add_argument("sources", nargs="*", help=DEFAULT_SOURCES_HELP)
    check.add_argument("--seconds", type=float, default=30.0, help="seconds per source, at least its minimum window (default: 30)")
    check.add_argument("--reports", type=Path, default=Path("data/reports"), help="directory for check-<time>.json (default: data/reports)")
    check.add_argument("--concurrency", type=int, default=16, help="sources consumed at the same time (default: 16)")

    sample = commands.add_parser("sample", help="measure every source once per round, rounds on wall-clock targets")
    sample.add_argument("sources", nargs="*", help=DEFAULT_SOURCES_HELP)
    sample.add_argument("--rounds", type=int, default=24, help="number of rounds (default: 24)")
    sample.add_argument("--interval", type=float, default=3600.0, help="seconds between round starts (default: 3600)")
    sample.add_argument(
        "--window", type=float, default=60.0, help="seconds each source is consumed per round, at least its minimum window (default: 60)"
    )
    sample.add_argument(
        "--reports", type=Path, default=Path("data/reports"), help="directory for round-NN-<time>.json (default: data/reports)"
    )
    sample.add_argument("--concurrency", type=int, default=64, help="sources consumed at the same time (default: 64)")
    sample.add_argument(
        "--continue-from",
        type=Path,
        default=None,
        help="reports directory of an interrupted run: its rounds count toward --rounds and are not repeated",
    )
    sample.add_argument(
        "--stop-when-settled",
        action="store_true",
        help="stop reading a source once its median over --rounds is fixed on one side of 1 event/s",
    )

    verdict = commands.add_parser("verdict", help="median rate and verdict per source from recorded sampling rounds")
    verdict.add_argument("reports_dir", type=Path, help="directory holding round-*.json files (searched recursively)")
    verdict.add_argument("sources", nargs="*", help="source ids (default: every source in the rounds)")
    verdict.add_argument("--planned", type=int, default=24, help="rounds in the plan the verdict is about (default: 24)")

    profile = commands.add_parser("profile", help="keep a masked sample of events per source and describe their fields")
    profile.add_argument("sources", nargs="*", help=DEFAULT_SOURCES_HELP)
    profile.add_argument("--max-events", type=int, default=500, help="events kept per source (default: 500)")
    profile.add_argument(
        "--seconds", type=float, default=120.0, help="at most this long per source, at least its minimum window (default: 120)"
    )
    profile.add_argument(
        "--out",
        type=Path,
        default=Path("data/profile"),
        help="directory for the masked samples, <source> plus the extension of --format (default: data/profile)",
    )
    profile.add_argument(
        "--format",
        choices=list(FORMATS),
        default=DEFAULT_FORMAT,
        help=f"format of the samples: {', '.join(FORMATS)} (default: {DEFAULT_FORMAT})",
    )
    profile.add_argument(
        "--reports", type=Path, default=Path("data/reports"), help="directory for profiles-<time>.json (default: data/reports)"
    )
    profile.add_argument("--concurrency", type=int, default=64, help="sources consumed at the same time (default: 64)")
    return parser


def _factories(module_name: str) -> Sequence[SourceFactoryPort]:
    return tuple(importlib.import_module(module_name).FACTORIES)


def _held_keys(module_name: str) -> HeldKeyCatalogPort:
    """A catalog module may also name the keys it holds for re-testing (HELD_KEYS)."""
    return StaticHeldKeyCatalog(tuple(getattr(importlib.import_module(module_name), "HELD_KEYS", ())))


def _line(report: RunReport) -> str:
    rate = "-" if report.rate is None else f"{report.rate:.3f}/s"
    return f"{report.source_id:16} {report.status.value:11} events={report.events:<7} rate={rate:<12} {report.rate_basis.value:10} {report.detail[:120]}"


def _summary(reports: Sequence[RunReport], stream: TextIO) -> int:
    for report in sorted(reports, key=lambda r: r.source_id):
        stream.write(_line(report) + "\n")
    failed = [r for r in reports if r.status in (RunStatus.ERROR, RunStatus.NO_EVENTS)]
    stream.write(f"{len(reports)} sources, {len(reports) - len(failed)} delivered or key pending, {len(failed)} failed\n")
    return 1 if failed else 0


def _verdicts(verdicts: Sequence[RateVerdict], stream: TextIO) -> None:
    for v in verdicts:
        median = "-" if v.median is None else f"{v.median:.3f}/s"
        stream.write(f"{v.source_id:16} rounds={v.rounds:>3}/{v.planned:<3} median={median:<12} {v.verdict.value}\n")
    counts = {kind: sum(v.verdict is kind for v in verdicts) for kind in Verdict}
    stream.write(", ".join(f"{n} {kind.value}" for kind, n in counts.items()) + "\n")


def _event_sink(destination: str, format_name: str | None, out: TextIO, clock: ClockPort) -> EventSinkPort:
    target = parse_target(destination, SINKS)
    if target.scheme in SINKS:
        if format_name is not None:
            raise OutputTargetError(f"--format applies to standard output and files, not to {target.scheme}")
        return SINKS[target.scheme](target, clock)
    event_format = FORMATS[format_name or DEFAULT_FORMAT]
    return TextStreamEventSink(out, event_format) if target.scheme == TERMINAL else TextFileEventSink(Path(target.location), event_format)


async def _run(args: argparse.Namespace, registry: SourceRegistryPort, clock: ClockPort, out: TextIO, err: TextIO) -> int:
    consume = ConsumeService(registry, clock)
    ids = list(getattr(args, "sources", None) or [d.id for d in ListService(registry).default_sources()])
    for source_id in ids:
        registry.descriptor(source_id)
    if args.command == "consume":
        sink = _event_sink(args.out, args.format, out, clock)
        await sink.open()
        try:
            report = await consume.consume(args.source, args.seconds, sink, args.max_events, mask=not args.raw)
        finally:
            await sink.close()
        err.write(json.dumps(asdict(report), default=lambda v: getattr(v, "value", str(v))) + "\n")
        return 0 if report.status in (RunStatus.OK, RunStatus.KEY_PENDING) else 1
    reports_sink = JsonReportSink(args.reports, clock)
    if args.command == "profile":
        service = ProfileService(consume, TextFileSinkFactory(args.out, FORMATS[args.format]), reports_sink, registry, args.concurrency)
        return _summary([p.run for p in await service.profile(ids, args.max_events, args.seconds)], out)
    discard = NullEventSink()
    try:
        if args.command == "check":
            return _summary(await CheckService(consume, discard, reports_sink, args.concurrency).check(ids, args.seconds), out)
        sampler = SampleService(consume, discard, reports_sink, clock, args.concurrency)
        prior = JsonSamplingHistory(args.continue_from).read_rounds() if args.continue_from else ()
        rounds = [*prior, *await sampler.sample(ids, args.rounds, args.interval, args.window, prior, args.stop_when_settled)]
        latest = {r.source_id: r for sampling_round in rounds for r in sampling_round.reports}
        code = _summary([latest[s] for s in ids if s in latest], out)
        _verdicts(VerdictService().verdicts(rounds, args.rounds, ids), out)
        return code
    finally:
        await discard.close()


def main(argv: Sequence[str] | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int:
    out, err = out or sys.stdout, err or sys.stderr
    try:
        code = _main(argv, out, err)
        out.flush()
    except BrokenPipeError:
        # the reader closed the pipe early (e.g. `list | head`): stop without a traceback and point the
        # descriptor at /dev/null so the interpreter's final flush cannot fail again
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, out.fileno())
        os.close(devnull)
        return SIGPIPE_EXIT
    return code


def _main(argv: Sequence[str] | None, out: TextIO, err: TextIO) -> int:
    args = _parser().parse_args(argv)
    clock = SystemClock()
    http: HttpClientPort = AiohttpClient(USER_AGENT)
    deps = SourceDependencies(http, EnvSecretProvider(os.environ, args.env_file), clock, USER_AGENT)
    try:
        registry = FactoryRegistry(_factories(args.catalog), deps)
        if args.command == "list":
            for descriptor in ListService(registry).list_sources():
                out.write(json.dumps(asdict(descriptor), default=lambda v: getattr(v, "value", str(v)), ensure_ascii=False) + "\n")
            return 0
        if args.command == "verdict":
            _verdicts(VerdictService().verdicts(JsonSamplingHistory(args.reports_dir).read_rounds(), args.planned, args.sources), out)
            return 0
        if args.command == "keys":
            configuration = ConfigurationService(registry, deps.secrets, _held_keys(args.catalog))
            if args.template:
                out.write(configuration.env_template())
                return 0
            for row in configuration.status():
                need = "-" if row.kind is ConfigKind.HELD else "required" if row.required else "optional"
                if row.configured:
                    state = "set"
                elif row.kind is ConfigKind.SETTING:
                    state = "default"
                else:
                    state = "MISSING" if row.required else "not-set"
                where = row.sign_up_url or f"default={row.default!r}"
                out.write(f"{row.source_id:14} {row.env_var:32} {row.kind.value:8} {need:9} {state:8} {where}\n")
            unknown = configuration.unknown_variables()
            for name in unknown:
                out.write(f"{'-':14} {name:32} {'-':8} {'-':9} {'unknown':8} not read by any source and not held\n")
            if unknown:
                err.write(
                    f"error: {args.env_file} defines {len(unknown)} variable(s) neither read by a source nor held; keep it to the template\n"
                )
                return 1
            return 0

        async def run_and_close() -> int:
            try:
                return await _run(args, registry, clock, out, err)
            finally:
                await http.close()

        return asyncio.run(run_and_close())
    except OutputError as exc:  # the destination refused or went away: the run did not complete
        err.write(f"error: {exc}\n")
        return 1
    except (StreamConsumersError, ValueError) as exc:
        err.write(f"error: {exc}\n")
        return 2
