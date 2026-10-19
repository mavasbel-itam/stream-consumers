"""A catalog of scripted sources (no network) for exercising the CLI in-process: `--catalog tests.catalog_scripted`."""

from __future__ import annotations

from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Credential, Group, HeldKey
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies, SourceFactoryPort
from tests.support import ScriptedSource, descriptor


class Alpha(BaseSourceFactory):
    DESCRIPTOR = descriptor("alpha", personal=("user",))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"user": "ana", "n": 1}, {"user": "beto", "n": 2}], deps.clock, hang=True)  # type: ignore[arg-type]


class Keyed(BaseSourceFactory):
    DESCRIPTOR = descriptor("keyed", credential=Credential(("SCRIPTED_KEY",), "https://sign.up/here"))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"key_used": credentials is not None}], deps.clock, hang=True)  # type: ignore[arg-type]


class Broken(BaseSourceFactory):
    DESCRIPTOR = descriptor("broken")

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [TransportError("refused")], deps.clock)  # type: ignore[arg-type]


class Quiet(BaseSourceFactory):
    """A low-rate source: run only when named."""

    DESCRIPTOR = descriptor("quiet", group=Group.LOW_RATE)

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"n": 1}], deps.clock, hang=True)  # type: ignore[arg-type]


FACTORIES: tuple[SourceFactoryPort, ...] = (Alpha(), Keyed(), Broken(), Quiet())
HELD_KEYS = (HeldKey("keyed", ("SCRIPTED_SPARE_KEY",), "Scripted provider", "Second key of the same account.", "https://sign.up/here"),)
