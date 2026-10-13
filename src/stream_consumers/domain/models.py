"""Domain model: what a source is, what an event is, what a run produced."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class Delivery(Enum):
    PUSH = "push"
    POLL = "poll"
    FILE_DROP = "file-drop"


class Transport(Enum):
    WEBSOCKET = "websocket"
    SSE = "sse"
    MQTT = "mqtt"
    NATS = "nats"
    ZMQ = "zeromq"
    TCP = "tcp"
    HTTP = "http"


class Group(Enum):
    """Why a source is in the repository (see README)."""

    KEYLESS = "A"
    PROJECT_DOCUMENT = "B"
    FREE_KEY = "C"


class RunStatus(Enum):
    OK = "ok"
    NO_EVENTS = "no-events"
    KEY_PENDING = "key-pending"
    ERROR = "error"


class RateBasis(Enum):
    """How a run's events-per-second figure was obtained."""

    OBSERVED = "observed"  # events received / seconds consumed
    PUBLISHED = "published"  # volume the provider published over a stated period
    UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class Credential:
    """An API key read from the environment; never stored in the repository.

    `required` False means the provider also serves a keyless route and the key
    only raises its limits.
    """

    env_var: str
    sign_up_url: str
    required: bool = True


@dataclass(frozen=True)
class SourceDescriptor:
    id: str
    name: str
    category: str
    provider: str
    group: Group
    delivery: Delivery
    transport: Transport
    endpoint: str
    docs_url: str
    terms_url: str
    credential: Credential | None = None
    min_interval_s: float = 0.0
    personal_fields: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class RawMessage:
    """One unit received from a transport, before decoding."""

    body: bytes | str
    attributes: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishedVolume:
    """`events` published by the provider over `period_s` seconds."""

    events: int
    period_s: float


@dataclass(frozen=True)
class Event:
    source_id: str
    received_at: float
    payload: Mapping[str, object]


@dataclass(frozen=True)
class RunReport:
    source_id: str
    status: RunStatus
    events: int
    seconds: float
    rate: float | None
    rate_basis: RateBasis
    attributes_median: float
    first_event_s: float | None
    started_at: float
    detail: str = ""


@dataclass(frozen=True)
class FieldProfile:
    name: str
    present_ratio: float
    distinct: int
    kinds: tuple[str, ...]
    minimum: float | None
    maximum: float | None
    mean: float | None
    example: str


@dataclass(frozen=True)
class SourceProfile:
    run: RunReport
    events_inspected: int
    fields: tuple[FieldProfile, ...]


@dataclass(frozen=True)
class SamplingRound:
    number: int
    scheduled_at: float
    reports: tuple[RunReport, ...]
