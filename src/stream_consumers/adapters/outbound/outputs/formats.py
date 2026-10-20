"""Text formats for events: JSON lines, CSV, TSV, one JSON array, indented JSON."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping

from stream_consumers.domain.models import Event
from stream_consumers.domain.policy import flatten
from stream_consumers.ports.outbound.outputs import EventEncoderPort, EventFormatPort

EXTRA = "extra"
"""CSV/TSV column holding, as one JSON object, the fields an event has beyond the header."""


def event_document(event: Event) -> dict[str, object]:
    """The document every output writes for an event."""
    return {"source": event.source_id, "received_at": event.received_at, "payload": event.payload}


def _json(value: object, indent: int | None = None) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, indent=indent)


class BaseEventEncoder(EventEncoderPort):
    def finish(self) -> str:
        return ""


class JsonLinesEncoder(BaseEventEncoder):
    def encode(self, event: Event) -> str:
        return _json(event_document(event)) + "\n"


class PrettyJsonEncoder(BaseEventEncoder):
    """Each event as indented JSON; the output is a stream of JSON documents (`jq` reads it as is)."""

    def encode(self, event: Event) -> str:
        return _json(event_document(event), indent=2) + "\n"


class JsonArrayEncoder(BaseEventEncoder):
    """All events as one JSON array; the document is complete once `finish` has been written."""

    def __init__(self) -> None:
        self._started = False

    def encode(self, event: Event) -> str:
        opening = ",\n" if self._started else "[\n"
        self._started = True
        return opening + _json(event_document(event))

    def finish(self) -> str:
        return "\n]\n" if self._started else "[]\n"


class DelimitedEncoder(BaseEventEncoder):
    """One row per event: `source`, `received_at` and every payload field as `payload.<dotted path>`.

    The header comes from the first event, so rows can be written while events arrive (also to
    the terminal). Fields first seen later go into the last column, `extra`, as one JSON object.
    Lists and empty objects are written as JSON text, `null` as an empty cell, booleans as
    `true`/`false`.
    """

    def __init__(self, delimiter: str) -> None:
        self._buffer = io.StringIO()
        self._writer = csv.writer(self._buffer, delimiter=delimiter, lineterminator="\n")
        self._columns: list[str] | None = None

    @staticmethod
    def _cell(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return value
        if isinstance(value, int | float):
            return str(value)
        return _json(value)

    def _row(self, values: list[str]) -> str:
        self._buffer.seek(0)
        self._buffer.truncate()
        self._writer.writerow(values)
        return self._buffer.getvalue()

    def encode(self, event: Event) -> str:
        fields: Mapping[str, object] = flatten(event_document(event))
        text = ""
        if self._columns is None:
            self._columns = list(fields)
            text = self._row([*self._columns, EXTRA])
        extra = {k: v for k, v in fields.items() if k not in self._columns}
        row = [self._cell(fields.get(c)) for c in self._columns]
        return text + self._row([*row, _json(extra) if extra else ""])


class BaseEventFormat(EventFormatPort):
    def __init__(self, name: str, extension: str) -> None:
        self._name = name
        self._extension = extension

    @property
    def name(self) -> str:
        return self._name

    @property
    def extension(self) -> str:
        return self._extension


class JsonLinesFormat(BaseEventFormat):
    def __init__(self) -> None:
        super().__init__("jsonl", ".jsonl")

    def encoder(self) -> EventEncoderPort:
        return JsonLinesEncoder()


class PrettyJsonFormat(BaseEventFormat):
    def __init__(self) -> None:
        super().__init__("pretty", ".txt")  # a stream of JSON documents, not one JSON document

    def encoder(self) -> EventEncoderPort:
        return PrettyJsonEncoder()


class JsonArrayFormat(BaseEventFormat):
    def __init__(self) -> None:
        super().__init__("json", ".json")

    def encoder(self) -> EventEncoderPort:
        return JsonArrayEncoder()


class CsvFormat(BaseEventFormat):
    def __init__(self) -> None:
        super().__init__("csv", ".csv")

    def encoder(self) -> EventEncoderPort:
        return DelimitedEncoder(",")


class TsvFormat(BaseEventFormat):
    def __init__(self) -> None:
        super().__init__("tsv", ".tsv")

    def encoder(self) -> EventEncoderPort:
        return DelimitedEncoder("\t")
