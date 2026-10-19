"""Outbound ports to the data providers: event sources, their factories and registry, and what they use.

A source is driven, not driving: the application opens it, pulls `events()` for as
long as its window lasts and closes it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field

from stream_consumers.domain.models import HeldKey, PublishedVolume, RawMessage, SourceDescriptor
from stream_consumers.ports.outbound.system import ClockPort, SecretProviderPort

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


class HeldKeyCatalogPort(ABC):
    """Credentials kept for re-testing that no source reads."""

    @abstractmethod
    def held_keys(self) -> Sequence[HeldKey]: ...


class SourceRegistryPort(ABC):
    @abstractmethod
    def descriptors(self) -> Sequence[SourceDescriptor]: ...

    @abstractmethod
    def descriptor(self, source_id: str) -> SourceDescriptor:
        """Raises UnknownSourceError."""

    @abstractmethod
    def create(self, source_id: str) -> EventSourcePort:
        """Raises UnknownSourceError or MissingCredentialError."""
