"""Where events and reports are written: discarded, a text stream, text files; report files."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TextIO

from stream_consumers.domain.models import Event, RunReport, SamplingRound, SourceProfile
from stream_consumers.ports.outbound.outputs import EventFormatPort, EventSinkFactoryPort, EventSinkPort, ReportSinkPort
from stream_consumers.ports.outbound.system import ClockPort


def _plain(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


class BaseEventSink(EventSinkPort):
    """A sink with nothing to create or connect to; subclasses override what they need."""

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        return None


class NullEventSink(BaseEventSink):
    """Discards events; used when only the measurement matters."""

    async def write(self, event: Event) -> None:
        return None


class TextStreamEventSink(BaseEventSink):
    """Events in a text format on an already-open text stream (the caller owns the stream).

    With `flush_each` every event is handed to the operating system as soon as it is written, so a program
    reading standard output through a pipe (`| jq`, `| grep`) sees each event when it arrives instead of
    once a buffer of several kilobytes has filled."""

    _flush_each = False

    def __init__(self, stream: TextIO, event_format: EventFormatPort, flush_each: bool = False) -> None:
        self._stream: TextIO = stream
        self._encoder = event_format.encoder()
        self._flush_each = flush_each

    async def write(self, event: Event) -> None:
        self._stream.write(self._encoder.encode(event))
        if self._flush_each:
            self._stream.flush()

    async def close(self) -> None:
        self._stream.write(self._encoder.finish())
        self._stream.flush()


class TextFileEventSink(TextStreamEventSink):
    """Events in a text format in a file it creates on `open` (with its directories) and closes itself."""

    def __init__(self, path: Path, event_format: EventFormatPort) -> None:  # the stream exists once `open` ran
        self._encoder = event_format.encoder()
        self._path = path

    async def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self._path.open("w", encoding="utf-8", newline="")

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            self._stream.close()


class TextFileSinkFactory(EventSinkFactoryPort):
    """One file per source, `<directory>/<source><extension of the format>`."""

    def __init__(self, directory: Path, event_format: EventFormatPort) -> None:
        self._directory = directory
        self._format = event_format

    def create(self, source_id: str) -> EventSinkPort:
        return TextFileEventSink(self._directory / f"{source_id}{self._format.extension}", self._format)


class JsonReportSink(ReportSinkPort):
    """Reports as JSON files named after the UTC time they were written."""

    def __init__(self, directory: Path, clock: ClockPort) -> None:
        self._directory = directory
        self._clock = clock

    def _stamp(self) -> str:
        return datetime.fromtimestamp(self._clock.now(), UTC).strftime("%Y%m%dT%H%M%SZ")

    def _write(self, name: str, document: object) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / name
        path.write_text(json.dumps(_plain(document), indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        return path

    def write_check(self, reports: Sequence[RunReport]) -> None:
        self._write(f"check-{self._stamp()}.json", [asdict(r) for r in reports])

    def write_round(self, sampling_round: SamplingRound) -> None:
        self._write(f"round-{sampling_round.number:02d}-{self._stamp()}.json", asdict(sampling_round))

    def write_profiles(self, profiles: Sequence[SourceProfile]) -> None:
        self._write(f"profiles-{self._stamp()}.json", [asdict(p) for p in profiles])
