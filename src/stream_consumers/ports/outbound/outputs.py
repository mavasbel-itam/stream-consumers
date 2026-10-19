"""Outbound ports for what the application writes (events, reports) and reads back (earlier rounds)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from stream_consumers.domain.models import Event, RunReport, SamplingRound, SourceProfile


class EventSinkPort(ABC):
    @abstractmethod
    def write(self, event: Event) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class EventSinkFactoryPort(ABC):
    @abstractmethod
    def open(self, source_id: str) -> EventSinkPort: ...


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
