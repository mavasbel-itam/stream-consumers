"""Database outputs against the real databases (labs-setup images, tests/databases.py): every sink
writes the real captured payloads of every source and the test reads them back with the database's
own client. Marked `databases` (CI runs them in their own job)."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from typing import Any

import pytest
import redis as redis_sync
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.connection import DefaultEndPoint
from neo4j import GraphDatabase
from opensearchpy import OpenSearch
from pymongo import MongoClient
from redis.cluster import ClusterNode
from redis.cluster import RedisCluster as SyncRedisCluster

from stream_consumers.adapters.outbound.outputs import databases
from stream_consumers.adapters.outbound.outputs.databases import (
    CassandraEventSink,
    MongoDbEventSink,
    Neo4jEventSink,
    OpenSearchEventSink,
    RedisEventSink,
    by_source,
)
from stream_consumers.adapters.outbound.system.clock import SystemClock
from stream_consumers.domain.errors import OutputError
from stream_consumers.domain.models import Event
from stream_consumers.ports.outbound.outputs import EventSinkPort
from tests import databases as db
from tests.unit.test_outputs import WITH_FIXTURES, plain, real_events

pytestmark = pytest.mark.databases

EVENTS = [e for source_id in WITH_FIXTURES for e in real_events(source_id)]
"""The payloads every source decodes from its captured real messages (713 events, 67 sources)."""
GROUPS = by_source(EVENTS)


def test_the_fixture_covers_every_source_with_captures() -> None:
    assert len(GROUPS) == len(WITH_FIXTURES) >= 60 and len(EVENTS) >= 700


def ms(event: Event) -> datetime:
    """`received_at` at the millisecond precision of BSON, CQL and Neo4j-independent comparisons."""
    stamp = datetime.fromtimestamp(event.received_at, UTC)
    return stamp.replace(microsecond=stamp.microsecond // 1000 * 1000)


async def publish(sink: EventSinkPort, events: Sequence[Event]) -> None:
    await sink.open()
    try:
        for event in events:
            await sink.write(event)
    finally:
        await sink.close()


async def refused(sink: EventSinkPort, match: str) -> OutputError:
    with pytest.raises(OutputError, match=match) as error:
        await sink.open()
    await sink.close()  # nothing was opened: nothing to close
    return error.value


@pytest.fixture(scope="module")
def servers() -> Iterator[dict[str, db.Container]]:
    containers = {
        "mongo": db.mongo(),
        "cassandra": db.cassandra(),
        "redis": db.redis(),
        "redis_cluster": db.redis_cluster(),
        "neo4j": db.neo4j(),
        "opensearch": db.opensearch(),
    }
    with db.running(list(containers.values())):
        yield containers


def mongo_client(port: int) -> MongoClient[dict[str, Any]]:
    return MongoClient(
        f"mongodb://{db.USER}:{db.PASSWORD}@127.0.0.1:{port}/?authSource=admin", serverSelectionTimeoutMS=2000, tz_aware=True
    )


class TestMongoDb:
    @pytest.fixture(scope="class")
    @classmethod
    def port(cls, servers: dict[str, db.Container]) -> int:
        container = servers["mongo"]
        port = db.host_port(container)
        db.wait(container, lambda: mongo_client(port).admin.command("ping"), 120)
        return port

    async def test_every_source_as_native_documents(self, port: int) -> None:
        uri = f"mongodb://{db.USER}:{db.PASSWORD}@127.0.0.1:{port}/?authSource=admin"
        await publish(MongoDbEventSink(uri, SystemClock(), "mongodb", batch_size=100), EVENTS)
        with mongo_client(port) as client:
            database = client["stream_consumers"]
            assert sorted(database.list_collection_names()) == sorted(GROUPS)
            for source_id, group in GROUPS.items():
                documents = list(database[source_id].find({}, {"_id": 0}).sort("_id", 1))
                assert [d["payload"] for d in documents] == [e.payload for e in group], source_id
                assert [d["received_at"] for d in documents] == [ms(e) for e in group], source_id

    async def test_database_from_the_path_password_from_the_environment_and_64_bit_integers(self, port: int) -> None:
        big = Event("chain", 1_760_000_000.0, {"wei": 2**70, "values": [2**63, 2**63 - 1, -(2**63)], "ok": True})
        uri = f"mongodb://{db.USER}@127.0.0.1:{port}/lab_outputs?authSource=admin"
        await publish(MongoDbEventSink(uri, SystemClock(), "mongodb", password=db.PASSWORD), [big])
        with mongo_client(port) as client:
            (stored,) = client["lab_outputs"]["chain"].find({}, {"_id": 0})
            assert stored["payload"] == {"wei": str(2**70), "values": [str(2**63), 2**63 - 1, -(2**63)], "ok": True}
            with pytest.raises(OverflowError, match="8-byte ints"):  # why the rule exists
                client["lab_outputs"]["raw"].insert_one({"wei": 2**70})

    async def test_a_wrong_password_and_no_server(self, port: int, monkeypatch: pytest.MonkeyPatch) -> None:
        wrong = f"mongodb://{db.USER}:wrong@127.0.0.1:{port}/?authSource=admin"
        await refused(MongoDbEventSink(wrong, SystemClock(), "mongodb://here"), "^output mongodb://here failed: OperationFailure")
        monkeypatch.setattr(databases, "CONNECT_TIMEOUT_S", 0.5)
        nobody = MongoDbEventSink(f"mongodb://127.0.0.1:{db.free_port()}/", SystemClock(), "m")
        await refused(nobody, "ServerSelectionTimeoutError")


def cassandra_session(port: int) -> Any:
    cluster = Cluster([DefaultEndPoint("127.0.0.1", port)], auth_provider=PlainTextAuthProvider("cassandra", "cassandra"))
    return cluster, cluster.connect()


class TestCassandra:
    @pytest.fixture(scope="class")
    @classmethod
    def port(cls, servers: dict[str, db.Container]) -> int:
        container = servers["cassandra"]
        port = db.host_port(container)

        def ready() -> None:
            cluster, session = cassandra_session(port)
            try:
                session.execute("SELECT release_version FROM system.local")
            finally:
                cluster.shutdown()

        db.wait(container, ready, 240)
        return port

    async def test_every_source_in_a_table_per_source(self, port: int) -> None:
        sink = CassandraEventSink(
            [("127.0.0.1", port)], "stream_consumers", SystemClock(), "cassandra", "cassandra", "cassandra", batch_size=100
        )
        await publish(sink, EVENTS)
        cluster, session = cassandra_session(port)
        try:
            keyspace = session.execute("SELECT replication FROM system_schema.keyspaces WHERE keyspace_name = 'stream_consumers'").one()
            datacenter = session.execute("SELECT data_center FROM system.local").one().data_center  # the node's own report
            assert dict(keyspace.replication) == {"class": "org.apache.cassandra.locator.NetworkTopologyStrategy", datacenter: "1"}
            for source_id, group in GROUPS.items():
                rows = list(session.execute(f'SELECT day, received_at, payload FROM stream_consumers."{source_id}"'))
                rows.sort(key=lambda r: r.received_at)
                assert [json.loads(r.payload) for r in rows] == [plain(e.payload) for e in group], source_id
                assert [r.received_at.replace(tzinfo=UTC) for r in rows] == [ms(e) for e in group], source_id
                assert {str(r.day) for r in rows} == {ms(e).date().isoformat() for e in group}
        finally:
            cluster.shutdown()

    async def test_a_wrong_password(self, port: int) -> None:
        sink = CassandraEventSink([("127.0.0.1", port)], "ks", SystemClock(), "cassandra://here", "cassandra", "wrong")
        await refused(sink, "^output cassandra://here failed: NoHostAvailable")


class TestRedis:
    @pytest.fixture(scope="class")
    @classmethod
    def ports(cls, servers: dict[str, db.Container]) -> tuple[int, list[int]]:
        single, cluster = servers["redis"], servers["redis_cluster"]
        port = db.host_port(single)
        db.wait(single, lambda: redis_sync.Redis(port=port, password=db.PASSWORD).ping(), 60)
        cluster_ports = list(cluster.ports)

        def cluster_ready() -> None:
            text = redis_sync.Redis(port=cluster_ports[0], password=db.PASSWORD).execute_command("CLUSTER", "INFO")
            info = dict(line.split(":", 1) for line in text.decode().split() if ":" in line)
            assert info["cluster_state"] == "ok" and info["cluster_known_nodes"] == "3"

        db.wait(cluster, cluster_ready, 60)
        return port, cluster_ports

    @staticmethod
    def streams(client: Any) -> dict[str, list[tuple[float, object]]]:
        out = {}
        for source_id in GROUPS:
            entries = client.xrange(f"stream_consumers:{source_id}")
            out[source_id] = [(float(fields[b"received_at"]), json.loads(fields[b"payload"])) for _, fields in entries]
        return out

    async def test_a_single_server_with_a_database_number(self, ports: tuple[int, list[int]]) -> None:
        port, _ = ports
        sink = RedisEventSink([("127.0.0.1", port)], SystemClock(), "redis", db=3, password=db.PASSWORD, batch_size=100)
        await publish(sink, EVENTS)
        read = self.streams(redis_sync.Redis(port=port, db=3, password=db.PASSWORD))
        assert read == {s: [(e.received_at, plain(e.payload)) for e in group] for s, group in GROUPS.items()}

    async def test_a_cluster_reached_through_the_address_mapping(self, ports: tuple[int, list[int]]) -> None:
        _, cluster_ports = ports
        hosts = [("127.0.0.1", p) for p in cluster_ports]
        await publish(RedisEventSink(hosts, SystemClock(), "redis+cluster", cluster=True, password=db.PASSWORD, batch_size=100), EVENTS)
        nodes = [ClusterNode("127.0.0.1", p) for p in cluster_ports]
        client = SyncRedisCluster(startup_nodes=nodes, password=db.PASSWORD, address_remap=lambda a: ("127.0.0.1", a[1]))
        try:
            assert {n.host for n in client.get_nodes()} == {"127.0.0.1"} and len(client.get_primaries()) == 3
            assert self.streams(client) == {s: [(e.received_at, plain(e.payload)) for e in group] for s, group in GROUPS.items()}
            # the streams are spread over all three masters
            assert all(redis_sync.Redis(port=p, password=db.PASSWORD).dbsize() > 0 for p in cluster_ports)
        finally:
            client.close()
        # the nodes advertise a name nobody resolves: without the mapping nothing is reachable
        with pytest.raises(redis_sync.exceptions.RedisClusterException):
            SyncRedisCluster(startup_nodes=nodes, password=db.PASSWORD).get_nodes()

    async def test_a_wrong_password(self, ports: tuple[int, list[int]]) -> None:
        port, cluster_ports = ports
        await refused(RedisEventSink([("127.0.0.1", port)], SystemClock(), "redis://here", password="wrong"), "AuthenticationError")
        cluster = RedisEventSink([("127.0.0.1", cluster_ports[0])], SystemClock(), "c", cluster=True, password="wrong")
        await refused(cluster, "^output c failed")


class TestNeo4j:
    @pytest.fixture(scope="class")
    @classmethod
    def uri(cls, servers: dict[str, db.Container]) -> str:
        container = servers["neo4j"]
        uri = f"bolt://127.0.0.1:{db.host_port(container)}"

        def ready() -> None:
            with GraphDatabase.driver(uri, auth=("neo4j", db.PASSWORD)) as driver:
                driver.verify_connectivity()

        db.wait(container, ready, 120)
        return uri

    async def test_every_source_as_a_graph(self, uri: str) -> None:
        await publish(Neo4jEventSink(uri, SystemClock(), "neo4j", None, "neo4j", db.PASSWORD, batch_size=100), EVENTS)
        with GraphDatabase.driver(uri, auth=("neo4j", db.PASSWORD)) as driver:
            records, _, _ = driver.execute_query(
                "MATCH (s:StreamSource)-[:EMITTED]->(e:StreamEvent) RETURN s.id AS source, e.received_at AS at, e.payload AS payload "
                "ORDER BY at"
            )
            read: dict[str, list[tuple[datetime, object]]] = {}
            for r in records:
                read.setdefault(r["source"], []).append((r["at"].to_native(), json.loads(r["payload"])))
            assert read == {s: [(datetime.fromtimestamp(e.received_at, UTC), plain(e.payload)) for e in g] for s, g in GROUPS.items()}
            (sources,), _, _ = driver.execute_query("MATCH (s:StreamSource) RETURN count(s)")
            constraints, _, _ = driver.execute_query("SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties")
        assert sources[0] == len(GROUPS)
        assert {"name": "stream_consumers_source_id", "labelsOrTypes": ["StreamSource"], "properties": ["id"]} in [
            c.data() for c in constraints
        ]

    async def test_an_unknown_database_and_a_wrong_password(self, uri: str) -> None:
        await refused(Neo4jEventSink(uri, SystemClock(), "neo4j://here", "nope", "neo4j", db.PASSWORD), "^output neo4j://here failed")
        await refused(Neo4jEventSink(uri, SystemClock(), "n", None, "neo4j", "wrong-password"), "AuthError")


def opensearch_client(port: int) -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "127.0.0.1", "port": port}],
        http_auth=("admin", db.PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )


class TestOpenSearch:
    @pytest.fixture(scope="class")
    @classmethod
    def port(cls, servers: dict[str, db.Container]) -> int:
        container = servers["opensearch"]
        port = db.host_port(container)
        db.wait(container, lambda: opensearch_client(port).cluster.health(wait_for_status="yellow"), 240)
        return port

    async def test_every_source_in_an_index_per_source_over_tls(self, port: int) -> None:
        sink = OpenSearchEventSink([("127.0.0.1", port)], SystemClock(), "opensearch", True, False, "admin", db.PASSWORD, batch_size=100)
        await publish(sink, EVENTS)
        client = opensearch_client(port)
        client.indices.refresh(index="stream_consumers-*")
        for source_id, group in GROUPS.items():
            index = f"stream_consumers-{source_id}"
            mapping = client.indices.get_mapping(index=index)[index]["mappings"]["properties"]
            assert mapping == {"received_at": {"type": "date"}, "payload": {"type": "flat_object"}}
            hits = client.search(index=index, body={"size": 1000, "sort": [{"received_at": "asc"}]})["hits"]["hits"]
            assert [h["_source"]["payload"] for h in hits] == [plain(e.payload) for e in group], source_id
            assert [h["_source"]["received_at"] for h in hits] == [datetime.fromtimestamp(e.received_at, UTC).isoformat() for e in group]

    async def test_refused_documents_an_invalid_index_and_a_wrong_password(self, port: int) -> None:
        client = opensearch_client(port)
        client.indices.create(index="stream_consumers-clash", body={"mappings": {"properties": {"received_at": {"type": "integer"}}}})
        sink = OpenSearchEventSink([("127.0.0.1", port)], SystemClock(), "os", True, False, "admin", db.PASSWORD)
        await sink.open()
        await sink.write(Event("clash", 1.0, {"a": 1}))
        with pytest.raises(
            OutputError, match=r"OutputRefusedError: 1 of 1 documents refused; first: (mapper_parsing_exception|document_parsing_exception)"
        ):
            await sink.close()
        sink = OpenSearchEventSink([("127.0.0.1", port)], SystemClock(), "os", True, False, "admin", db.PASSWORD)
        await sink.open()
        await sink.write(Event("Upper", 1.0, {"a": 1}))
        with pytest.raises(OutputError, match="invalid_index_name_exception"):
            await sink.close()
        wrong = OpenSearchEventSink([("127.0.0.1", port)], SystemClock(), "opensearch://here", True, False, "admin", "wrong")
        await refused(wrong, "^output opensearch://here failed: AuthenticationException")
