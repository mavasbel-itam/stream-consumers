"""Outbound ports to the operating system: time and environment values."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


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

    @abstractmethod
    def file_names(self) -> Sequence[str]:
        """Every name the configuration file defines (not the process environment), in file order."""
