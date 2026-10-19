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
    KAFKA = "kafka"


class Group(Enum):
    """Why a source is in the repository (see README)."""

    KEYLESS = "A"
    PROJECT_DOCUMENT = "B"
    FREE_KEY = "C"
    CANDIDATE = "D"  # needs a free key that is not configured yet; rate not measured, so not yet accepted


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
    """API credentials read from the environment; never stored in the repository.

    `env_vars` are needed together (one key, or for example a username and a
    password). `required` False means the provider also serves a keyless route:
    the credentials only raise its limits and are used only when all are set.
    `how_to_get` says how the provider hands them out (form, e-mail, waiting time).
    """

    env_vars: tuple[str, ...]
    sign_up_url: str
    required: bool = True
    how_to_get: str = ""

    def __post_init__(self) -> None:
        if not self.env_vars:
            raise ValueError("a credential names at least one environment variable")


@dataclass(frozen=True)
class Setting:
    """A non-secret configuration value read from the environment, with a default."""

    env_var: str
    default: str
    description: str


@dataclass(frozen=True)
class HeldKey:
    """A credential the project keeps so that it can be tested again, although no source reads it.

    `owner` is the source it belongs to, or the id of a removed source; `env_vars` are needed together.
    """

    owner: str
    env_vars: tuple[str, ...]
    provider: str
    purpose: str
    sign_up_url: str

    def __post_init__(self) -> None:
        if not self.env_vars:
            raise ValueError("a held key names at least one environment variable")


class ConfigKind(Enum):
    SECRET = "secret"
    SETTING = "setting"
    HELD = "held"


@dataclass(frozen=True)
class ConfigStatus:
    """Whether one environment variable a source reads, or a held key, is set (never its value)."""

    source_id: str
    env_var: str
    kind: ConfigKind
    required: bool
    configured: bool
    sign_up_url: str = ""
    default: str = ""
    description: str = ""


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
    settings: tuple[Setting, ...] = ()
    min_interval_s: float = 0.0
    personal_fields: tuple[str, ...] = ()
    notes: str = ""
    min_window_s: float = 0.0
    """Shortest measuring window that yields a rate; a shorter requested window is extended to it."""

    def __post_init__(self) -> None:
        if self.min_window_s < 0:
            raise ValueError("min_window_s must not be negative")


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


class FieldClass(Enum):
    """What a field's observed values are, decided by fixed rules in this order (`policy.classify_field`)."""

    DATETIME = "datetime"  # ISO 8601 text; epoch s/ms/µs/ns or YYYYMMDD[hhmmss] within 400 days of the observation
    GEOGRAPHIC = "geographic"  # a latitude or longitude with its partner field, both within range
    NUMBER = "number"  # every value a number, or numeric text without a leading zero (flagged)
    IDENTIFIER = "identifier"  # text without spaces, more distinct values than a category may have
    FREE_TEXT = "free-text"  # text averaging 30+ characters, at least half distinct, mostly with spaces
    LABEL = "label"  # other text with more distinct values than a category may have: names, titles
    CATEGORY = "category"  # text or Booleans with at most max(20, 5 % of the events) distinct values
    NESTED = "nested"  # lists, mappings and mixed kinds
    EMPTY = "empty"  # never carried a value


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
    field_class: FieldClass
    numeric_text: bool  # numbers carried as text


@dataclass(frozen=True)
class SourceProfile:
    run: RunReport
    events_inspected: int
    fields: tuple[FieldProfile, ...]
    bytes_mean: float | None  # compact UTF-8 JSON of each decoded event
    bytes_p95: int | None
    duplicate_ratio: float | None  # share of events equal to an earlier event of the sample
    natural_key: tuple[str, ...]  # smallest field set unique across the sample; empty when none


class Verdict(Enum):
    """Where the median of a planned number of rounds stands against the minimum rate."""

    PASSES = "passes"  # at or above the minimum whatever the missing rounds measure
    FAILS = "fails"  # below the minimum whatever the missing rounds measure
    OPEN = "open"  # the missing rounds can still decide it


@dataclass(frozen=True)
class RateVerdict:
    source_id: str
    rounds: int
    planned: int
    median: float | None
    verdict: Verdict


@dataclass(frozen=True)
class SamplingRound:
    number: int
    scheduled_at: float
    reports: tuple[RunReport, ...]
