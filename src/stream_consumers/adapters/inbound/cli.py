"""Command-line interface and composition root: the only place concrete classes are named."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

from stream_consumers.adapters.outbound.http import AiohttpClient
from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sinks import (
    JsonlFileEventSink,
    JsonlFileSinkFactory,
    JsonReportSink,
    NullEventSink,
    TextStreamEventSink,
)
from stream_consumers.adapters.outbound.system import EnvSecretProvider, SystemClock
from stream_consumers.application.check_service import CheckService
from stream_consumers.application.configuration_service import ConfigurationService
from stream_consumers.application.consume_service import ConsumeService
from stream_consumers.application.list_service import ListService
from stream_consumers.application.profile_service import ProfileService
from stream_consumers.application.sample_service import SampleService
from stream_consumers.domain.errors import StreamConsumersError
from stream_consumers.domain.models import ConfigKind, RunReport, RunStatus
from stream_consumers.ports.outbound import (
    ClockPort,
    EventSinkPort,
    HttpClientPort,
    SourceDependencies,
    SourceFactoryPort,
    SourceRegistryPort,
)

USER_AGENT = "stream-consumers/0.1 (ITAM COM-22102 course research; non-commercial)"
DEFAULT_CATALOG = "stream_consumers.adapters.outbound.sources"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stream-consumers", description="Consume public real-time data streams.")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG, help="module exposing FACTORIES (default: the built-in sources)")
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="git-ignored file with API keys (default: .env)")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="list the sources as JSON lines")

    keys = commands.add_parser("keys", help="show which API credentials and settings are set (never their values)")
    keys.add_argument("--template", action="store_true", help="print a .env template instead")

    consume = commands.add_parser("consume", help="write the events of one source as JSON lines")
    consume.add_argument("source")
    consume.add_argument("--seconds", type=float, default=60.0)
    consume.add_argument("--max-events", type=int)
    consume.add_argument("--out", default="-", help="output file, or - for standard output")
    consume.add_argument("--raw", action="store_true", help="do not mask personal fields")

    check = commands.add_parser("check", help="consume each source briefly and report whether events arrive")
    check.add_argument("sources", nargs="*", help="source ids (default: all)")
    check.add_argument("--seconds", type=float, default=30.0)
    check.add_argument("--reports", type=Path, default=Path("data/reports"))
    check.add_argument("--concurrency", type=int, default=16, help="sources consumed at the same time")

    sample = commands.add_parser("sample", help="measure every source once per round, rounds on wall-clock targets")
    sample.add_argument("sources", nargs="*", help="source ids (default: all)")
    sample.add_argument("--rounds", type=int, default=24)
    sample.add_argument("--interval", type=float, default=3600.0, help="seconds between round starts")
    sample.add_argument("--window", type=float, default=60.0, help="seconds each source is consumed per round")
    sample.add_argument("--reports", type=Path, default=Path("data/reports"))
    sample.add_argument("--concurrency", type=int, default=64, help="sources consumed at the same time")

    profile = commands.add_parser("profile", help="keep a masked sample of events per source and describe their fields")
    profile.add_argument("sources", nargs="*", help="source ids (default: all)")
    profile.add_argument("--max-events", type=int, default=500)
    profile.add_argument("--seconds", type=float, default=120.0)
    profile.add_argument("--out", type=Path, default=Path("data/profile"))
    profile.add_argument("--reports", type=Path, default=Path("data/reports"))
    profile.add_argument("--concurrency", type=int, default=64, help="sources consumed at the same time")
    return parser


def _factories(module_name: str) -> Sequence[SourceFactoryPort]:
    return tuple(importlib.import_module(module_name).FACTORIES)


def _line(report: RunReport) -> str:
    rate = "-" if report.rate is None else f"{report.rate:.3f}/s"
    return f"{report.source_id:16} {report.status.value:11} events={report.events:<7} rate={rate:<12} {report.rate_basis.value:10} {report.detail[:120]}"


def _summary(reports: Sequence[RunReport], stream: TextIO) -> int:
    for report in sorted(reports, key=lambda r: r.source_id):
        stream.write(_line(report) + "\n")
    failed = [r for r in reports if r.status in (RunStatus.ERROR, RunStatus.NO_EVENTS)]
    stream.write(f"{len(reports)} sources, {len(reports) - len(failed)} delivered or key pending, {len(failed)} failed\n")
    return 1 if failed else 0


async def _run(args: argparse.Namespace, registry: SourceRegistryPort, clock: ClockPort, out: TextIO, err: TextIO) -> int:
    consume = ConsumeService(registry, clock)
    ids = list(getattr(args, "sources", None) or [d.id for d in registry.descriptors()])
    for source_id in ids:
        registry.descriptor(source_id)
    if args.command == "consume":
        sink: EventSinkPort = TextStreamEventSink(out) if args.out == "-" else JsonlFileEventSink(Path(args.out))
        try:
            report = await consume.consume(args.source, args.seconds, sink, args.max_events, mask=not args.raw)
        finally:
            sink.close()
        err.write(json.dumps(asdict(report), default=lambda v: getattr(v, "value", str(v))) + "\n")
        return 0 if report.status in (RunStatus.OK, RunStatus.KEY_PENDING) else 1
    reports_sink = JsonReportSink(args.reports, clock)
    if args.command == "profile":
        service = ProfileService(consume, JsonlFileSinkFactory(args.out), reports_sink, registry, args.concurrency)
        return _summary([p.run for p in await service.profile(ids, args.max_events, args.seconds)], out)
    discard = NullEventSink()
    try:
        if args.command == "check":
            return _summary(await CheckService(consume, discard, reports_sink, args.concurrency).check(ids, args.seconds), out)
        sampler = SampleService(consume, discard, reports_sink, clock, args.concurrency)
        return _summary((await sampler.sample(ids, args.rounds, args.interval, args.window))[-1].reports, out)
    finally:
        discard.close()


def main(argv: Sequence[str] | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int:
    out, err = out or sys.stdout, err or sys.stderr
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
        if args.command == "keys":
            configuration = ConfigurationService(registry, deps.secrets)
            if args.template:
                out.write(configuration.env_template())
                return 0
            for row in configuration.status():
                need = "required" if row.required else "optional"
                if row.configured:
                    state = "set"
                elif row.kind is ConfigKind.SETTING:
                    state = "default"
                else:
                    state = "MISSING" if row.required else "not-set"
                where = row.sign_up_url or f"default={row.default!r}"
                out.write(f"{row.source_id:14} {row.env_var:28} {row.kind.value:8} {need:9} {state:8} {where}\n")
            return 0

        async def run_and_close() -> int:
            try:
                return await _run(args, registry, clock, out, err)
            finally:
                await http.close()

        return asyncio.run(run_and_close())
    except (StreamConsumersError, ValueError) as exc:
        err.write(f"error: {exc}\n")
        return 2
