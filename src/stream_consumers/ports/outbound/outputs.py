"""Outbound ports for what the application writes (events, reports) and reads back (earlier rounds)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from stream_consumers.domain.models import Event, RunReport, SamplingRound, SourceProfile


class EventSinkPort(ABC):
    """Where the events of a run go: the terminal, a file, a database or a message broker."""

    @abstractmethod
    async def open(self) -> None:
        """Create or connect to what the sink writes to; called once, before the first `write`."""

    @abstractmethod
    async def write(self, event: Event) -> None: ...

    @abstractmethod
    async def close(self) -> None:
        """Write whatever is still buffered and release the connection or file."""


class EventSinkFactoryPort(ABC):
    @abstractmethod
    def create(self, source_id: str) -> EventSinkPort:
        """A new, not yet opened sink for one source."""


class EventEncoderPort(ABC):
    """Turns the events of one output into text; holds the state a format needs (a CSV header)."""

    @abstractmethod
    def encode(self, event: Event) -> str:
        """The text for this event, preceded by whatever the format writes before its first event."""

    @abstractmethod
    def finish(self) -> str:
        """The text that ends the document (the closing bracket of a JSON array), possibly empty."""


class EventFormatPort(ABC):
    """A text format for events (JSON lines, CSV, ...)."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def extension(self) -> str:
        """File name extension, with its dot."""

    @abstractmethod
    def encoder(self) -> EventEncoderPort:
        """A fresh encoder for one output."""


class SamplingHistoryPort(ABC):
    @abstractmethod
    def read_rounds(self) -> Sequence[SamplingRound]:
        """Sampling rounds written earlier, oldest first."""


class ReportSinkPort(ABC):
    @abstractmethod
    def write_check(self, reports: Sequence[RunReport]) -> None: ...

    @abstractmethod
    def write_round(self, sampling_round: SamplingRound) -> None: ...

    @abstractmethod
    def write_profiles(self, profiles: Sequence[SourceProfile]) -> None: ...
