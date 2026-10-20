"""The course databases in Docker for the database output tests, with the images labs-setup uses.

labs-setup (`1f23f32`) names `mongo:7.0`, `cassandra:5.0`, `redis:8.4.0-bookworm`, `neo4j:ubi9` and
`opensearchproject/opensearch:3.4.0`. The floating tags are pinned here to the releases they carried
on 2026-10-20 (`mongo:7.0` and `neo4j:ubi9` have the same image ids as the pinned tags; `cassandra:5.0`
reported CASSANDRA_VERSION 5.0.9), so a test run never changes under a moved tag.

Each server is one container with its own name, published on 127.0.0.1 only at a free port, and
removed afterwards. Containers start together (`start`) and are waited for one by one (`wait`).
"""

from __future__ import annotations

import socket
import subprocess
import time
import uuid
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field

MONGO_IMAGE = "mongo:7.0.43"
CASSANDRA_IMAGE = "cassandra:5.0.9"
REDIS_IMAGE = "redis:8.4.0-bookworm"
NEO4J_IMAGE = "neo4j:2026.04.0-community-ubi9"
OPENSEARCH_IMAGE = "opensearchproject/opensearch:3.4.0"

USER = "ana"
PASSWORD = "Str0ng-Passw0rd!"  # OpenSearch 3 refuses weak initial admin passwords


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@dataclass
class Container:
    image: str
    ports: dict[int, int]
    """host port: container port"""
    command: Sequence[str] = ()
    env: dict[str, str] = field(default_factory=dict)
    entrypoint: str | None = None
    name: str = field(default_factory=lambda: f"stream-consumers-test-{uuid.uuid4().hex[:10]}")

    def start(self) -> None:
        args = ["docker", "run", "-d", "--rm", "--name", self.name]
        for host_port, container_port in self.ports.items():
            args += ["-p", f"127.0.0.1:{host_port}:{container_port}"]
        for key, value in self.env.items():
            args += ["-e", f"{key}={value}"]
        if self.entrypoint is not None:
            args += ["--entrypoint", self.entrypoint]
        subprocess.run([*args, self.image, *self.command], check=True, capture_output=True)

    def stop(self) -> None:
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True)

    def logs(self) -> str:
        done = subprocess.run(["docker", "logs", "--tail", "40", self.name], capture_output=True, text=True)
        return done.stdout + done.stderr


def wait(container: Container, ready: Callable[[], object], timeout_s: float) -> None:
    """Calls `ready` until it returns without raising."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            ready()
            return
        except Exception as exc:
            if time.monotonic() > deadline:
                raise RuntimeError(f"{container.image} not ready after {timeout_s} s ({exc!r}):\n{container.logs()}") from exc
            time.sleep(1)


@contextmanager
def running(containers: Sequence[Container]) -> Iterator[None]:
    try:
        for container in containers:
            container.start()
        yield
    finally:
        for container in containers:
            container.stop()


def mongo() -> Container:
    port = free_port()
    return Container(MONGO_IMAGE, {port: 27017}, env={"MONGO_INITDB_ROOT_USERNAME": USER, "MONGO_INITDB_ROOT_PASSWORD": PASSWORD})


def cassandra() -> Container:
    """One node with password authentication (as in the labs); the default superuser is cassandra/cassandra."""
    port = free_port()
    script = (
        "sed -i 's/^authenticator: AllowAllAuthenticator/authenticator: PasswordAuthenticator/' /etc/cassandra/cassandra.yaml"
        " && exec docker-entrypoint.sh cassandra -f"
    )
    env = {"MAX_HEAP_SIZE": "768M", "HEAP_NEWSIZE": "128M"}
    return Container(CASSANDRA_IMAGE, {port: 9042}, ["-c", script], env, entrypoint="sh")


def redis() -> Container:
    port = free_port()
    return Container(REDIS_IMAGE, {port: 6379}, ["redis-server", "--requirepass", PASSWORD])


REDIS_ANNOUNCED_HOST = "redis-cluster.invalid"
"""What the cluster nodes advertise: a name nobody can resolve, so a client reaches the nodes only
through the address mapping by port."""


def redis_cluster() -> Container:
    """Three masters in one container, each on its own port (the same inside and on the host), that
    advertise `REDIS_ANNOUNCED_HOST` to clients."""
    ports = [free_port() for _ in range(3)]
    # the cluster bus port defaults to port + 10000, which is past 65535 for a free port above 55535:
    # it is set explicitly (17000-17002, used only inside the container)
    servers = " ".join(
        f"redis-server --port {p} --cluster-port {17000 + i} --cluster-enabled yes --cluster-config-file nodes-{p}.conf"
        f" --appendonly no --requirepass {PASSWORD} --masterauth {PASSWORD} --cluster-announce-hostname {REDIS_ANNOUNCED_HOST}"
        f" --cluster-preferred-endpoint-type hostname --daemonize yes --logfile /tmp/redis-{p}.log;"
        for i, p in enumerate(ports)
    )
    create = f"redis-cli -a {PASSWORD} --no-auth-warning --cluster create {' '.join(f'127.0.0.1:{p}' for p in ports)} --cluster-yes"
    up = " ".join(f"until redis-cli -p {p} -a {PASSWORD} --no-auth-warning ping; do sleep 0.2; done;" for p in ports)
    script = f"{servers} {up} {create}; sleep infinity"
    return Container(REDIS_IMAGE, {p: p for p in ports}, ["-c", script], entrypoint="sh")


def neo4j() -> Container:
    port = free_port()
    env = {"NEO4J_AUTH": f"neo4j/{PASSWORD}", "NEO4J_server_memory_heap_max__size": "512m"}
    return Container(NEO4J_IMAGE, {port: 7687}, env=env)


def opensearch() -> Container:
    """Security plugin on, as in the labs: HTTPS with the demonstration certificate, user admin."""
    port = free_port()
    env = {
        "discovery.type": "single-node",
        "OPENSEARCH_INITIAL_ADMIN_PASSWORD": PASSWORD,
        "OPENSEARCH_JAVA_OPTS": "-Xms512m -Xmx512m",
        "DISABLE_PERFORMANCE_ANALYZER_AGENT_CLI": "true",
    }
    return Container(OPENSEARCH_IMAGE, {port: 9200}, env=env)


def host_port(container: Container) -> int:
    (port,) = [h for h, c in container.ports.items() if c in (27017, 9042, 6379, 7687, 9200)]
    return port
