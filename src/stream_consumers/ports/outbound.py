"""Outbound ports: everything the application and the source adapters need from outside.

Every port is an ABC so that each adapter declares the abstraction it implements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field

from stream_consumers.domain.models import (
    Event,
    PublishedVolume,
    RawMessage,
    RunReport,
    SamplingRound,
    SourceDescriptor,
    SourceProfile,
)


class ClockPort(ABC):
    @abstractmethod
    def now(self) -> float:
        """Wall-clock time, seconds since the epoch."""

    @abstractmethod
    def monotonic(self) -> float:
        """Monotonic seconds, for measuring durations."""

    @abstractmethod
    async def sleep(self, seconds: float) -> None: ...


class SecretProviderPort(ABC):
    """Environment values: API credentials and non-secret settings."""

    @abstractmethod
    def get(self, name: str) -> str | None:
        """The value called `name`, or None when it is not configured."""


Credentials = Mapping[str, str]
"""Credential values by environment variable name, handed to a source factory."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)


class HttpClientPort(ABC):
    @abstractmethod
    async def get(self, url: str, headers: Mapping[str, str] | None = None) -> HttpResponse: ...

    @abstractmethod
    async def post_json(self, url: str, body: object, headers: Mapping[str, str] | None = None) -> HttpResponse: ...

    @abstractmethod
    async def post_form(self, url: str, fields: Mapping[str, str], headers: Mapping[str, str] | None = None) -> HttpResponse:
        """POST `fields` as application/x-www-form-urlencoded."""

    @abstractmethod
    def stream(self, url: str, headers: Mapping[str, str] | None = None) -> AsyncIterator[bytes]:
        """Body chunks of a GET; raises TransportError on a non-200 status."""

    @abstractmethod
    async def close(self) -> None: ...


class RequestAuthPort(ABC):
    """Headers that authenticate a request, obtained (and renewed) by the adapter."""

    @abstractmethod
    async def headers(self) -> Mapping[str, str]: ...

    @abstractmethod
    def invalidate(self) -> None:
        """Forget the current credential so the next `headers()` obtains a new one (e.g. after HTTP 401)."""


class DecoderPort(ABC):
    @abstractmethod
    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        """Zero or more events carried by one transport message."""


class EventSourcePort(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> SourceDescriptor: ...

    @abstractmethod
    def events(self) -> AsyncGenerator[Mapping[str, object]]:
        """Decoded events for as long as the caller keeps iterating; `aclose()` releases the connection."""

    @abstractmethod
    def published_volume(self) -> PublishedVolume | None:
        """Volume the provider itself published, for sources whose rate is not the arrival rate.

        None means the rate is the observed arrival rate of `events()`.
        """


@dataclass(frozen=True)
class SourceDependencies:
    """Ports a source adapter may use; injected by the composition root."""

    http: HttpClientPort
    secrets: SecretProviderPort
    clock: ClockPort
    user_agent: str


class SourceFactoryPort(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> SourceDescriptor: ...

    @abstractmethod
    def create(self, deps: SourceDependencies) -> EventSourcePort:
        """Raises MissingCredentialError when a required key is not configured."""


class SourceRegistryPort(ABC):
    @abstractmethod
    def descriptors(self) -> Sequence[SourceDescriptor]: ...

    @abstractmethod
    def descriptor(self, source_id: str) -> SourceDescriptor:
        """Raises UnknownSourceError."""

    @abstractmethod
    def create(self, source_id: str) -> EventSourcePort:
        """Raises UnknownSourceError or MissingCredentialError."""


class EventSinkPort(ABC):
    @abstractmethod
    def write(self, event: Event) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class EventSinkFactoryPort(ABC):
    @abstractmethod
    def open(self, source_id: str) -> EventSinkPort: ...


class ReportSinkPort(ABC):
    @abstractmethod
    def write_check(self, reports: Sequence[RunReport]) -> None: ...

    @abstractmethod
    def write_round(self, sampling_round: SamplingRound) -> None: ...

    @abstractmethod
    def write_profiles(self, profiles: Sequence[SourceProfile]) -> None: ...
