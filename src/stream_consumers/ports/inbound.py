"""Inbound ports: the use cases this package offers to its driving adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from stream_consumers.domain.models import ConfigStatus, RateVerdict, RunReport, SamplingRound, SourceDescriptor, SourceProfile
from stream_consumers.ports.outbound.outputs import EventSinkPort


class ListSourcesUseCase(ABC):
    @abstractmethod
    def list_sources(self) -> Sequence[SourceDescriptor]: ...

    @abstractmethod
    def default_sources(self) -> Sequence[SourceDescriptor]:
        """The sources a command runs when no source id is given: those of an active group, in catalog order."""


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
        """Read events from one source into `sink` for at most `seconds` (or `max_events`).

        The caller opens `sink` before and closes it after; the use case only writes to it."""


class CheckSourcesUseCase(ABC):
    @abstractmethod
    async def check(self, source_ids: Sequence[str], seconds: float) -> Sequence[RunReport]:
        """Consume each source briefly and report whether it delivers decodable events."""


class SampleSourcesUseCase(ABC):
    @abstractmethod
    async def sample(
        self,
        source_ids: Sequence[str],
        rounds: int,
        interval_s: float,
        window_s: float,
        prior: Sequence[SamplingRound] = (),
        stop_when_settled: bool = False,
    ) -> Sequence[SamplingRound]:
        """Measure every source once per round, rounds `interval_s` apart on wall-clock targets.

        `rounds` is the whole plan: rounds already in `prior` (an interrupted run) are not repeated
        and numbering continues after them. With `stop_when_settled` a source is no longer read once
        its verdict over `rounds` can no longer change, and sampling ends when every source is settled."""


class JudgeSamplingUseCase(ABC):
    @abstractmethod
    def verdicts(self, rounds: Sequence[SamplingRound], planned: int, source_ids: Sequence[str] = ()) -> Sequence[RateVerdict]:
        """Median rate and verdict of each source (default: every source in `rounds`) over a plan of `planned` rounds."""


class ProfileSourcesUseCase(ABC):
    @abstractmethod
    async def profile(self, source_ids: Sequence[str], max_events: int, seconds: float) -> Sequence[SourceProfile]:
        """Keep up to `max_events` masked events per source and describe their fields."""


class DescribeConfigurationUseCase(ABC):
    @abstractmethod
    def status(self) -> Sequence[ConfigStatus]:
        """Every credential and setting the sources read, every held key, and whether each is set (values are never returned)."""

    @abstractmethod
    def env_template(self) -> str:
        """A `.env` template naming every credential, setting and held key, with how to obtain each credential."""

    @abstractmethod
    def unknown_variables(self) -> Sequence[str]:
        """Names the `.env` file defines that are neither read by a source nor held, so `.env` can be kept to the template."""
