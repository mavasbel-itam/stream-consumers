"""Inbound ports: the use cases this package offers to its driving adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from stream_consumers.domain.models import ConfigStatus, RunReport, SamplingRound, SourceDescriptor, SourceProfile
from stream_consumers.ports.outbound import EventSinkPort


class ListSourcesUseCase(ABC):
    @abstractmethod
    def list_sources(self) -> Sequence[SourceDescriptor]: ...


class ConsumeStreamUseCase(ABC):
    @abstractmethod
    async def consume(
        self,
        source_id: str,
        seconds: float,
        sink: EventSinkPort,
        max_events: int | None = None,
        mask: bool = True,
    ) -> RunReport:
        """Read events from one source into `sink` for at most `seconds` (or `max_events`)."""


class CheckSourcesUseCase(ABC):
    @abstractmethod
    async def check(self, source_ids: Sequence[str], seconds: float) -> Sequence[RunReport]:
        """Consume each source briefly and report whether it delivers decodable events."""


class SampleSourcesUseCase(ABC):
    @abstractmethod
    async def sample(self, source_ids: Sequence[str], rounds: int, interval_s: float, window_s: float) -> Sequence[SamplingRound]:
        """Measure every source once per round, rounds `interval_s` apart on wall-clock targets."""


class ProfileSourcesUseCase(ABC):
    @abstractmethod
    async def profile(self, source_ids: Sequence[str], max_events: int, seconds: float) -> Sequence[SourceProfile]:
        """Keep up to `max_events` masked events per source and describe their fields."""


class DescribeConfigurationUseCase(ABC):
    @abstractmethod
    def status(self) -> Sequence[ConfigStatus]:
        """Every credential and setting the sources read, and whether it is set (values are never returned)."""

    @abstractmethod
    def env_template(self) -> str:
        """A `.env` template naming every credential and setting, with how to obtain each credential."""

    @abstractmethod
    def unknown_variables(self) -> Sequence[str]:
        """Names the `.env` file defines that no source reads, so `.env` can be kept to the template."""
