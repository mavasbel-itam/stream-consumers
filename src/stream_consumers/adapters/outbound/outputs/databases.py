"""Events written into the course databases: MongoDB, Cassandra, Redis, Neo4j and OpenSearch.

Every database keeps the events of a source apart (a collection, table, stream, index or node per
source) under the `stream_consumers` namespace, and receives them in batches (`BatchingEventSink`).
Blocking drivers (Cassandra) run in a worker thread, never on the event loop.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from cassandra.concurrent import execute_concurrent_with_args
from cassandra.connection import DefaultEndPoint, DefaultEndPointFactory, EndPoint
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncManagedTransaction
from opensearchpy import AsyncOpenSearch
from opensearchpy.exceptions import RequestError
from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from redis.asyncio.cluster import ClusterNode, RedisCluster

from stream_consumers.adapters.outbound.outputs.batching import BatchingEventSink
from stream_consumers.domain.errors import OutputRefusedError
from stream_consumers.domain.models import Event
from stream_consumers.domain.outputs import NAMESPACE, storable
from stream_consumers.ports.outbound.system import ClockPort

CONNECT_TIMEOUT_S = 10.0


def payload_json(event: Event) -> str:
    return json.dumps(event.payload, ensure_ascii=False, default=str, separators=(",", ":"))


def received_at(event: Event) -> datetime:
    return datetime.fromtimestamp(event.received_at, UTC)


def by_source(events: Sequence[Event]) -> Mapping[str, list[Event]]:
    groups: defaultdict[str, list[Event]] = defaultdict(list)
    for event in events:
        groups[event.source_id].append(event)
    return groups


class MongoDbEventSink(BatchingEventSink):
    """Collection `<source>` in the database named by the URI path (default `stream_consumers`);
    documents `{received_at: BSON date, payload: <the payload as a document>}`.

    The URI is passed to pymongo as written (replica sets, `directConnection`, `authSource`, ...).
    Integers outside 64 bits, which BSON cannot hold, are stored as strings (`storable`).
    """

    def __init__(
        self, uri: str, clock: ClockPort, label: str, password: str | None = None, batch_size: int = 500, max_delay_s: float = 1.0
    ) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._uri = uri
        self._password = password
        self._client: AsyncMongoClient[dict[str, Any]] | None = None

    async def _connect(self) -> None:
        options: dict[str, Any] = {"serverSelectionTimeoutMS": int(CONNECT_TIMEOUT_S * 1000), "tz_aware": True}
        if self._password is not None:
            options["password"] = self._password
        client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(self._uri, **options)
        try:
            await client.get_default_database(NAMESPACE).command("ping")
        except BaseException:
            await client.close()
            raise
        self._client = client

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._client is not None, "open() first"
        database = self._client.get_default_database(NAMESPACE)
        for source_id, group in by_source(events).items():
            documents = [{"received_at": received_at(e), "payload": storable(e.payload)} for e in group]
            await database[source_id].insert_many(documents, ordered=True)

    async def _disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()


class PortMappedEndPointFactory(DefaultEndPointFactory):  # type: ignore[misc]
    """Reaches a discovered Cassandra node at the host given for its native port, as the labs do:
    each node publishes its own port on the host, while it advertises an address inside Docker."""

    def __init__(self, hosts_by_port: Mapping[int, str]) -> None:
        super().__init__()
        self._hosts_by_port = dict(hosts_by_port)

    def create(self, row: Mapping[str, Any]) -> EndPoint:
        port = row.get("native_port")
        if port in self._hosts_by_port:
            return DefaultEndPoint(self._hosts_by_port[port], port)
        return super().create(row)


class CassandraEventSink(BatchingEventSink):
    """Table `<source>` in `keyspace`: `day date, received_at timestamp, id uuid, payload text`, primary
    key `((day), received_at, id)` (one partition per source and UTC day; `received_at` has millisecond
    precision, the random `id` keeps events of the same millisecond apart).

    A missing keyspace is created with NetworkTopologyStrategy: in every datacenter the cluster
    reports, a replication factor of its node count, at most 3.
    """

    def __init__(
        self,
        hosts: Sequence[tuple[str, int]],
        keyspace: str,
        clock: ClockPort,
        label: str,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._hosts = list(hosts)
        self._keyspace = keyspace
        self._user = user
        self._password = password
        self._cluster: Cluster | None = None
        self._session: Session | None = None
        self._inserts: dict[str, Any] = {}

    def _open_session(self) -> None:
        auth = PlainTextAuthProvider(self._user, self._password or "") if self._user is not None else None
        cluster = Cluster(
            contact_points=[DefaultEndPoint(host, port) for host, port in self._hosts],
            endpoint_factory=PortMappedEndPointFactory({port: host for host, port in self._hosts}),
            auth_provider=auth,
            load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy()),  # the driver's default, named
            connect_timeout=CONNECT_TIMEOUT_S,
            control_connection_timeout=CONNECT_TIMEOUT_S,
        )
        try:
            session = cluster.connect()
            nodes: defaultdict[str, int] = defaultdict(int)
            for host in cluster.metadata.all_hosts():
                nodes[host.datacenter] += 1
            replication = ", ".join(f"'{dc}': {min(3, count)}" for dc, count in sorted(nodes.items()))
            session.execute(
                f'CREATE KEYSPACE IF NOT EXISTS "{self._keyspace}" '
                f"WITH replication = {{'class': 'NetworkTopologyStrategy', {replication}}}"
            )
        except BaseException:
            cluster.shutdown()
            raise
        self._cluster, self._session = cluster, session

    async def _connect(self) -> None:
        await asyncio.to_thread(self._open_session)

    def _insert(self, events: Sequence[Event]) -> None:
        assert self._session is not None, "open() first"
        for source_id, group in by_source(events).items():
            if source_id not in self._inserts:
                table = f'"{self._keyspace}"."{source_id}"'
                self._session.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} "
                    "(day date, received_at timestamp, id uuid, payload text, PRIMARY KEY ((day), received_at, id))"
                )
                self._inserts[source_id] = self._session.prepare(f"INSERT INTO {table} (day, received_at, id, payload) VALUES (?, ?, ?, ?)")
            rows = [(received_at(e).date(), received_at(e), uuid.uuid4(), payload_json(e)) for e in group]
            execute_concurrent_with_args(self._session, self._inserts[source_id], rows, concurrency=50, raise_on_first_error=True)

    async def _flush(self, events: Sequence[Event]) -> None:
        await asyncio.to_thread(self._insert, events)

    async def _disconnect(self) -> None:
        if self._cluster is not None:
            await asyncio.to_thread(self._cluster.shutdown)


class RedisEventSink(BatchingEventSink):
    """Stream `stream_consumers:<source>`: one `XADD` per event with fields `received_at` (Unix
    seconds) and `payload` (JSON text). A single server, or a cluster whose advertised node
    addresses are mapped to the host given for their port (as the labs do)."""

    def __init__(
        self,
        hosts: Sequence[tuple[str, int]],
        clock: ClockPort,
        label: str,
        cluster: bool = False,
        db: int = 0,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._hosts = list(hosts)
        self._hosts_by_port = {port: host for host, port in self._hosts}
        self._cluster = cluster
        self._db = db
        self._user = user
        self._password = password
        self._client: Redis | RedisCluster | None = None

    def _remap(self, address: tuple[str, int]) -> tuple[str, int]:
        port = address[1]
        return (self._hosts_by_port[port], port) if port in self._hosts_by_port else address

    async def _connect(self) -> None:
        client: Redis | RedisCluster
        if self._cluster:
            client = RedisCluster(
                startup_nodes=[ClusterNode(host, port) for host, port in self._hosts],
                username=self._user,
                password=self._password,
                require_full_coverage=True,
                address_remap=self._remap,
                socket_connect_timeout=CONNECT_TIMEOUT_S,
            )
        else:
            ((host, port),) = self._hosts
            client = Redis(
                host=host, port=port, db=self._db, username=self._user, password=self._password, socket_connect_timeout=CONNECT_TIMEOUT_S
            )
        try:
            await client.ping()
        except BaseException:
            await client.aclose()
            raise
        self._client = client

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._client is not None, "open() first"
        pipe = self._client.pipeline(transaction=False) if isinstance(self._client, Redis) else self._client.pipeline()
        for event in events:
            pipe.xadd(f"{NAMESPACE}:{event.source_id}", {"received_at": repr(event.received_at), "payload": payload_json(event)})
        await pipe.execute()

    async def _disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()


SOURCE_LABEL = "StreamSource"
EVENT_LABEL = "StreamEvent"
_NEO4J_WRITE = f"""
UNWIND $rows AS row
MERGE (s:{SOURCE_LABEL} {{id: row.source}})
CREATE (s)-[:EMITTED]->(:{EVENT_LABEL} {{received_at: row.received_at, payload: row.payload}})
"""


class Neo4jEventSink(BatchingEventSink):
    """`(:StreamSource {id})-[:EMITTED]->(:StreamEvent {received_at, payload})`, `received_at` a
    DateTime and `payload` JSON text, in `database` (default: the server's default database).

    The labels carry the project's name so they cannot be mistaken for other data in a shared
    database (Neo4j Community has a single user database); a uniqueness constraint
    `stream_consumers_source_id` keeps one node per source.
    """

    def __init__(
        self,
        uri: str,
        clock: ClockPort,
        label: str,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._uri = uri
        self._database = database
        self._auth = (user, password or "") if user is not None else None
        self._driver: AsyncDriver | None = None

    async def _connect(self) -> None:
        driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth, connection_timeout=CONNECT_TIMEOUT_S)
        try:  # a single attempt first: execute_query retries an unreachable server for up to 30 s per call
            await driver.verify_connectivity()
            await driver.execute_query(
                f"CREATE CONSTRAINT {NAMESPACE}_source_id IF NOT EXISTS FOR (s:{SOURCE_LABEL}) REQUIRE s.id IS UNIQUE",
                database_=self._database,
            )
        except BaseException:
            await driver.close()
            raise
        self._driver = driver

    @staticmethod
    async def _write(tx: AsyncManagedTransaction, rows: list[dict[str, Any]]) -> None:
        await (await tx.run(_NEO4J_WRITE, rows=rows)).consume()

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._driver is not None, "open() first"
        rows = [{"source": e.source_id, "received_at": received_at(e), "payload": payload_json(e)} for e in events]
        async with self._driver.session(database=self._database) as session:
            await session.execute_write(self._write, rows)

    async def _disconnect(self) -> None:
        if self._driver is not None:
            await self._driver.close()


class OpenSearchEventSink(BatchingEventSink):
    """Index `stream_consumers-<source>`: documents `{received_at (date), payload}`, `payload` mapped as
    `flat_object`, so a field whose type changes between events never gets a document refused."""

    def __init__(
        self,
        hosts: Sequence[tuple[str, int]],
        clock: ClockPort,
        label: str,
        tls: bool = False,
        verify: bool = True,
        user: str | None = None,
        password: str | None = None,
        batch_size: int = 500,
        max_delay_s: float = 1.0,
    ) -> None:
        super().__init__(clock, label, batch_size, max_delay_s)
        self._hosts = [{"host": host, "port": port} for host, port in hosts]
        self._tls = tls
        self._verify = verify
        self._auth = (user, password or "") if user is not None else None
        self._client: AsyncOpenSearch | None = None
        self._indices: set[str] = set()

    async def _connect(self) -> None:
        client = AsyncOpenSearch(
            hosts=self._hosts,
            http_auth=self._auth,
            use_ssl=self._tls,
            verify_certs=self._verify,
            ssl_assert_hostname=self._verify,
            ssl_show_warn=False,
            timeout=30,
        )
        try:
            await client.info()
        except BaseException:
            await client.close()
            raise
        self._client = client

    async def _index(self, source_id: str) -> str:
        assert self._client is not None, "open() first"
        index = f"{NAMESPACE}-{source_id}"
        if index not in self._indices:
            mappings = {"properties": {"received_at": {"type": "date"}, "payload": {"type": "flat_object"}}}
            try:
                await self._client.indices.create(index=index, body={"mappings": mappings})
            except RequestError as exc:
                if exc.error != "resource_already_exists_exception":
                    raise
            self._indices.add(index)
        return index

    async def _flush(self, events: Sequence[Event]) -> None:
        assert self._client is not None, "open() first"
        lines: list[dict[str, Any]] = []
        for event in events:
            lines.append({"index": {"_index": await self._index(event.source_id)}})
            lines.append({"received_at": received_at(event).isoformat(), "payload": event.payload})
        answer = await self._client.bulk(body=lines)
        if answer["errors"]:
            refused = [item["index"] for item in answer["items"] if "error" in item["index"]]
            first = refused[0]["error"]
            raise OutputRefusedError(
                f"{len(refused)} of {len(events)} documents refused; first: {first.get('type')}: {first.get('reason')}"
            )

    async def _disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
