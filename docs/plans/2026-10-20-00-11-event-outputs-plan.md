# Event outputs: formats, SQLite, message brokers, course databases

| | |
|---|---|
| Created | 2026-10-20 00:11 UTC (2026-10-19 18:11 in Mexico City) |
| Base | `main` = `fc14ce7` |
| Scope approved | 2026-10-19: text formats + SQLite, message brokers, course databases; CSV "extra column" rule |
| Status | approved on 2026-10-20 (UTC), shortly after it was written, with both section 7 decisions taken as recommended |

## 1. Current state (measured at `fc14ce7`)

- One format, JSON lines. `consume --out -` writes to the terminal, `--out <path>` to a file;
  `profile --out <dir>` writes `<dir>/<source>.jsonl`. `check` and `sample` discard events
  (`NullEventSink`).
- `ports/outbound/outputs.py`: `EventSinkPort.write(event)` and `close()` are **synchronous**;
  `ConsumeService` calls `sink.write(...)` once per event.
- Adapters: `adapters/outbound/outputs/sinks.py` (`NullEventSink`, `TextStreamEventSink` →
  `JsonlFileEventSink`, `JsonlFileSinkFactory`, `JsonReportSink`).
- `domain/policy.py::flatten` already flattens nested mappings into dotted keys (lists and
  scalars are leaves); CSV reuses it.
- Client libraries already installed for the sources: `aiokafka` 0.14.0, `paho-mqtt` 2.1.0,
  `nats-py` 2.16.0, `pyzmq` 27.2.0. `amqtt` 0.12.1 (a real MQTT broker) is a dev dependency.
- Course databases (labs-setup `1f23f32`): MongoDB `mongo:7.0` (3-node replica set,
  27011–27013), Cassandra `cassandra:5.0` (3 nodes, 9041–9043, endpoint mapping by native
  port), Redis `redis:8.4.0-bookworm` (6-node cluster, 6381–6386, address remap), Neo4j
  `neo4j:ubi9` (= Neo4j 2026.04.0 community, bolt 7687), OpenSearch
  `opensearchproject/opensearch:3.4.0` (3 nodes, 9201–9203, TLS with the demo certificate).
  Client versions locked by labs-setup: `pymongo` 4.17.0, `cassandra-driver` 3.30.1,
  `redis` 8.1.0, `neo4j` 6.2.0, `opensearch-py` 3.0.0. All five import on Python 3.13.16
  (checked 2026-10-19; `AsyncOpenSearch` needs the `async` extra, i.e. aiohttp, already a
  dependency; the Cassandra wheel defaults to `LibevConnection`, so no `asyncore` is needed).

## 2. Port changes (`ports/outbound/outputs.py`)

- `EventSinkPort`: `async open()`, `async write(event)`, `async close()`. Kafka and NATS clients
  are async only, so the port becomes async; `ConsumeService` awaits `write`, the CLI and
  `ProfileService` await `open`/`close`. The per-event `await asyncio.sleep(0)` stays.
- New `EventFormatPort` (`extension`, `encoder()`) and `EventEncoderPort` (`encode(event) -> str`
  including any header the format needs first, `finish() -> str` closing the document).
- The destination string is parsed by a pure domain rule (`domain/outputs.py::parse_target`)
  into an `OutputTarget` value (scheme, hosts, path, user, password, options); the CLI
  composition root maps the scheme to the adapter. No new port is needed for parsing.

## 3. Formats (stage 1)

| `--format` | Output | Notes |
|---|---|---|
| `jsonl` (default) | one JSON object per line (unchanged bytes) | `{"source", "received_at", "payload"}` |
| `csv` / `tsv` | `source`, `received_at`, then each payload field as a column (`flatten`, dotted names); lists and empty mappings as JSON text | header from the first event; fields first seen later go into a final `extra` column as one JSON object; Python `csv` quoting |
| `json` | one JSON array document | `[]` for an empty run; valid JSON after `close` |
| `pretty` | indented JSON per event, one document after the other | for reading on screen |

`--format` applies to `consume` (terminal or file) and `profile` (file extension follows the
format). Personal-field masking happens before any format, as today.

## 4. Destinations (`--out`)

| `--out` | Adapter | Where an event goes |
|---|---|---|
| `-` (default) | terminal | in the chosen format |
| `<path>` | file | in the chosen format |
| `sqlite:<path>` | SQLite (stdlib `sqlite3`) | table `<source>` (`seq`, `received_at`, `payload` JSON text) |
| `kafka://host:port[,host:port]/<topic>` | aiokafka producer | key = source id, value = the JSON-lines document |
| `mqtt://host:port/<topic>` | paho-mqtt, QoS 1 | the JSON-lines document |
| `nats://host:port/<subject>` | nats-py | the JSON-lines document |
| `zmq+tcp://host:port` | pyzmq PUB socket (binds) | two frames: source id, document |
| `mongodb://…` (any MongoDB URI) | pymongo `AsyncMongoClient` | database from the URI path (default `stream_consumers`), collection `<source>`, payload as a native document (`received_at` as a BSON date) |
| `cassandra://host:port[,…]/<keyspace>` | cassandra-driver | keyspace (default `stream_consumers`, created if missing), table `<source>` partitioned by day |
| `redis://…` / `redis+cluster://host:port[,…]` | redis-py asyncio | stream `stream_consumers:<source>` (`XADD`, fields `received_at`, `payload`) |
| `neo4j://…` / `bolt://…` | neo4j async driver | `(:Source {id})-[:EMITTED]->(:Event {received_at, payload})`, payload as JSON text |
| `opensearch://host:port[,…]` (`?tls=1&verify=0` for the lab's demo certificate) | opensearch-py async | index `stream_consumers-<source>`, `payload` mapped as `flat_object` so changing field types never reject a document |

- Topics, subjects and keyspaces default to `stream_consumers.<source>` (Kafka, NATS),
  `stream_consumers/<source>` (MQTT) when the path is omitted; a `{source}` placeholder in the
  path is replaced by the source id.
- Credentials: user and password from the URI (the form the labs print), or, when the URI has a
  user and no password, from `STREAM_CONSUMERS_OUTPUT_PASSWORD` in the environment or `.env`
  (declared as a setting, listed by `keys`, documented in the README). Passwords are never
  printed: run reports show the destination with the password replaced by `***`.
- Cluster address mapping (the labs publish container ports on the host): Cassandra maps every
  discovered node to the host given for its native port; Redis cluster maps every advertised
  node address to the host given for its port — the same rules the labs' own notebooks use.
- Database and broker adapters write in batches: a `BatchingEventSink` base flushes every
  500 events or 1 s after the oldest buffered event (measured with `ClockPort`), and on close.
- Values MongoDB cannot store (integers outside 64 bits, found in blockchain payloads) are
  written as strings; the rule is a pure domain function with unit tests.

## 5. Architecture

```text
ports/outbound/outputs.py      EventSinkPort, EventSinkFactoryPort, EventFormatPort, EventEncoderPort, ReportSinkPort, SamplingHistoryPort
adapters/outbound/outputs/
  formats.py                   EventFormatPort → JsonLines / Delimited (Csv, Tsv) / JsonArray / Pretty, with their encoders
  sinks.py                     EventSinkPort → BaseEventSink → Null / TextStream → TextFile; factories; JsonReportSink
  sqlite.py                    BatchingEventSink → SqliteEventSink
  brokers.py                   BaseEventSink → Kafka / Mqtt / Nats / ZeroMq sinks
  databases.py                 BatchingEventSink → MongoDb / Cassandra / Redis / Neo4j / OpenSearch sinks
domain/outputs.py              OutputTarget, parse_target, flatten_row (CSV), storable (64-bit rule), mask_password
```

Every class extends a port of the outputs group; the architecture tests already enforce the
group rules. Only `adapters/inbound/cli.py` maps a scheme to a concrete class.

## 6. Tests and verification

- Unit (100 % gated): every encoder against real captured fixtures (`tests/fixtures/raw`),
  the CSV `extra` rule, `parse_target` for every scheme and malformed input, password masking,
  the 64-bit rule, batching by size and by time with a fake clock, CLI wiring and `--help`
  defaults.
- Component (100 % gated, real servers, each adapter writes and the test reads back with the
  server's own client): SQLite file; Kafka in `apache/kafka:3.9.1` (existing helper); MQTT in
  `amqtt`; NATS in the official `nats` image (version pinned after checking the registry);
  ZeroMQ with a real SUB socket; MongoDB, Cassandra, Redis (single node and a 3-master
  cluster), Neo4j and OpenSearch in Docker with **the labs-setup images and tags**, each
  container started with its own name and a free port and removed afterwards, exactly like
  the Kafka helper.
- e2e: `consume` of a local source into a file in every format and into SQLite, run as a
  subprocess; three runs at 100 %.
- Lab tier (`-m lab`, not in CI): the same adapters against the running labs-setup clusters
  (multi-node Cassandra, Redis cluster, MongoDB replica set, OpenSearch with TLS) — see 7.
- README: a "Outputs" section with every format and destination, an example and the schema per
  database; `AGENTS.md` rule; `tests/unit/test_documentation.py` extended so every format and
  scheme must be documented.
- Full gate set per commit: ruff, unit+component 100 %, e2e ×3, live key suite, `keys`,
  secret scan, push, CI green.

## 7. Delivery and open decisions

Three commits, each with the full gate set and green CI: (1) async port, formats, SQLite;
(2) brokers; (3) databases.

Decisions (2026-10-19, both as recommended):
1. Lab tier — **approved, after the three commits**: the labs-setup cluster containers on this machine (`mongodb-node-1..3`,
   `cassandra-node-1..3`, `neo4j-instance`) belong to the course checkout and were stopped at
   about 18:00. Running the lab tier means starting them (Redis and OpenSearch clusters are
   not present and would be created by their infrastructure notebooks), writing into
   `stream_consumers` namespaces only, and stopping them again with `docker stop`.
2. CI layout — **separate parallel job for the database tests**: the database containers lengthen every CI run (by an amount measured once they
   exist; the current run takes 1 min 36 s, CI `39343946894`). Either they run in the existing
   job, or in a separate parallel job for the database tests so the main job keeps its time.
