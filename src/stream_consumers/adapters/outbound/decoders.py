"""Decoder class tree: DecoderPort → BaseDecoder → one decoder per wire format.

Source modules subclass these to pick the events out of a provider's envelope.
"""

from __future__ import annotations

import base64
import csv
import gzip
import io
import json
from abc import abstractmethod
from collections.abc import Mapping, Sequence

import fastavro
from google.protobuf.json_format import MessageToDict, Parse, ParseError
from google.transit import gtfs_realtime_pb2

from stream_consumers.domain.errors import DecodeError
from stream_consumers.domain.models import RawMessage
from stream_consumers.ports.outbound import DecoderPort

Record = Mapping[str, object]


class BaseDecoder(DecoderPort):
    @staticmethod
    def text(message: RawMessage) -> str:
        body = message.body
        return body.decode("utf-8", "replace") if isinstance(body, bytes) else body

    @staticmethod
    def raw(message: RawMessage) -> bytes:
        body = message.body
        return body if isinstance(body, bytes) else body.encode("utf-8")

    @staticmethod
    def gunzip(data: bytes) -> bytes:
        try:
            return gzip.decompress(data)
        except (OSError, EOFError) as exc:
            raise DecodeError(f"not gzip data: {exc}") from exc


class JsonDecoder(BaseDecoder):
    """Parses JSON, then `extract` picks the events. By default a mapping is one event
    and a list yields its mapping items."""

    def decode(self, message: RawMessage) -> Sequence[Record]:
        try:
            document = json.loads(self.raw(message))
        except ValueError as exc:
            raise DecodeError(f"invalid JSON: {exc}") from exc
        return self.extract(document, message)

    def extract(self, document: object, message: RawMessage) -> Sequence[Record]:
        if isinstance(document, Mapping):
            return [document]
        if isinstance(document, list):
            return [d for d in document if isinstance(d, Mapping)]
        return []


class LineDecoder(BaseDecoder):
    """Text messages, one candidate event per line; `parse_line` returns None for lines that are not events."""

    def decode(self, message: RawMessage) -> Sequence[Record]:
        out = []
        for line in self.text(message).splitlines():
            line = line.strip()
            if line:
                record = self.parse_line(line, message)
                if record is not None:
                    out.append(record)
        return out

    @abstractmethod
    def parse_line(self, line: str, message: RawMessage) -> Record | None: ...


class CsvDecoder(BaseDecoder):
    """Delimited text with a header row, or with `fieldnames` when the file has none.

    A header that repeats a column name (METAR repeats each cloud-layer column four
    times) gets suffixes ``_2``, ``_3``... so no column overwrites another."""

    def __init__(self, delimiter: str = ",", fieldnames: Sequence[str] | None = None, gzipped: bool = False) -> None:
        self._delimiter = delimiter
        self._fieldnames = list(fieldnames) if fieldnames else None
        self._gzipped = gzipped

    def decode(self, message: RawMessage) -> Sequence[Record]:
        data = self.gunzip(self.raw(message)) if self._gzipped else self.raw(message)
        text = self.prepare(data.decode("utf-8", "replace"))
        rows = csv.reader(io.StringIO(text), delimiter=self._delimiter)
        names = self._fieldnames or self.unique(next(rows, []))
        return [self.transform(dict(zip(names, row, strict=False))) for row in rows if row]

    @staticmethod
    def unique(header: Sequence[str]) -> list[str]:
        seen: dict[str, int] = {}
        out = []
        for name in header:
            seen[name] = seen.get(name, 0) + 1
            out.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
        return out

    def prepare(self, text: str) -> str:
        """Hook to drop preamble lines before the header."""
        return text

    def transform(self, row: dict[str, object]) -> Record:
        return row


class GtfsRealtimeDecoder(BaseDecoder):
    """GTFS-Realtime FeedMessage: one event per entity, header timestamp attached.

    Protobuf is the GTFS-Realtime wire format. A body that starts with ``{`` is read as the
    JSON mapping of the same message (field names in either lowerCamelCase or the .proto's
    snake_case, as protobuf's JSON parser accepts both), for feeds that answer JSON.
    """

    def decode(self, message: RawMessage) -> Sequence[Record]:
        feed = gtfs_realtime_pb2.FeedMessage()
        raw = self.raw(message)
        try:
            if raw.lstrip()[:1] == b"{":
                Parse(raw.decode("utf-8"), feed, ignore_unknown_fields=True)
            else:
                feed.ParseFromString(raw)
        except (ParseError, UnicodeDecodeError) as exc:
            raise DecodeError(f"invalid GTFS-Realtime JSON feed: {exc}") from exc
        except Exception as exc:  # protobuf raises its own DecodeError type
            raise DecodeError(f"invalid GTFS-Realtime feed: {exc}") from exc
        stamp = feed.header.timestamp
        return [dict(MessageToDict(entity), feedTimestamp=stamp) for entity in feed.entity]


class AvroSchemaInKeyDecoder(BaseDecoder):
    """Schemaless Avro values whose writer schema travels as JSON in the Kafka message key
    (the `key` attribute), as the Fink broker publishes them. Parsed schemas are cached by key
    text. Binary fields (image cutouts) become base64 text so every event is JSON-serialisable.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, object] = {}

    def _schema(self, key: str) -> object:
        if key not in self._schemas:
            try:
                self._schemas[key] = fastavro.parse_schema(json.loads(key))
            except (ValueError, TypeError, fastavro.schema.SchemaParseException) as exc:
                raise DecodeError(f"message key is not an Avro schema: {exc}") from exc
        return self._schemas[key]

    @classmethod
    def jsonable(cls, value: object) -> object:
        if isinstance(value, bytes):
            return base64.b64encode(value).decode("ascii")
        if isinstance(value, Mapping):
            return {k: cls.jsonable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls.jsonable(v) for v in value]
        return value

    def decode(self, message: RawMessage) -> Sequence[Record]:
        key = message.attributes.get("key")
        if not key:
            raise DecodeError("Avro message without a schema in its key")
        try:
            record = fastavro.schemaless_reader(io.BytesIO(self.raw(message)), self._schema(key), None)
        except (EOFError, ValueError, TypeError, IndexError) as exc:
            raise DecodeError(f"value does not match its Avro schema: {exc}") from exc
        out = self.jsonable(record)
        return [out] if isinstance(out, Mapping) else []
