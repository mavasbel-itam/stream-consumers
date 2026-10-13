"""Where events and reports are written."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TextIO

from stream_consumers.domain.models import Event, RunReport, SamplingRound, SourceProfile
from stream_consumers.ports.outbound import ClockPort, EventSinkFactoryPort, EventSinkPort, ReportSinkPort


def _plain(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


def _event_line(event: Event) -> str:
    return json.dumps(
        {"source": event.source_id, "received_at": event.received_at, "payload": event.payload},
        ensure_ascii=False,
        default=str,
    )


class NullEventSink(EventSinkPort):
    """Discards events; used when only the measurement matters."""

    def write(self, event: Event) -> None:
        return None

    def close(self) -> None:
        return None


class TextStreamEventSink(EventSinkPort):
    """One JSON line per event on an already-open text stream (the caller owns the stream)."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def write(self, event: Event) -> None:
        self._stream.write(_event_line(event) + "\n")

    def close(self) -> None:
        self._stream.flush()


class JsonlFileEventSink(TextStreamEventSink):
    """One JSON line per event in a file it opens and closes itself."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("w", encoding="utf-8")
        super().__init__(self._file)

    def close(self) -> None:
        self._file.close()


class JsonlFileSinkFactory(EventSinkFactoryPort):
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def open(self, source_id: str) -> EventSinkPort:
        return JsonlFileEventSink(self._directory / f"{source_id}.jsonl")


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
