"""Events in a SQLite database file (Python's own `sqlite3`), one table per source."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from stream_consumers.adapters.outbound.outputs.batching import BatchingEventSink
from stream_consumers.domain.models import Event
from stream_consumers.ports.outbound.system import ClockPort


def _table(source_id: str) -> str:
    return '"' + source_id.replace('"', '""') + '"'


class SqliteEventSink(BatchingEventSink):
    """Table `<source>` with `seq` (row number), `received_at` (Unix seconds) and `payload` (JSON text).

    Query with SQLite's JSON functions, e.g.
    `SELECT datetime(received_at, 'unixepoch'), payload ->> '$.price' FROM binance`.
    """

    def __init__(self, path: Path, clock: ClockPort, batch_size: int = 500, max_delay_s: float = 1.0) -> None:
        super().__init__(clock, f"sqlite:{path}", batch_size, max_delay_s)
        self._path = path
        self._db: sqlite3.Connection | None = None
        self._tables: set[str] = set()

    async def _connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # writes run in a worker thread (one at a time, under the batch lock), never on the event loop
        self._db = sqlite3.connect(self._path, check_same_thread=False)

    def _insert(self, db: sqlite3.Connection, events: Sequence[Event]) -> None:
        for source_id in {e.source_id for e in events} - self._tables:
            db.execute(
                f"CREATE TABLE IF NOT EXISTS {_table(source_id)} "
                "(seq INTEGER PRIMARY KEY, received_at REAL NOT NULL, payload TEXT NOT NULL)"
            )
            self._tables.add(source_id)
        for source_id in {e.source_id for e in events}:
            db.executemany(
                f"INSERT INTO {_table(source_id)} (received_at, payload) VALUES (?, ?)",
                [(e.received_at, json.dumps(e.payload, ensure_ascii=False, default=str)) for e in events if e.source_id == source_id],
            )
        db.commit()

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._db is not None, "open() first"
        await asyncio.to_thread(self._insert, self._db, events)

    async def _disconnect(self) -> None:
        if self._db is not None:
            self._db.close()
