"""List the registered sources."""

from __future__ import annotations

from collections.abc import Sequence

from stream_consumers.domain.models import SourceDescriptor
from stream_consumers.ports.inbound import ListSourcesUseCase
from stream_consumers.ports.outbound.providers import SourceRegistryPort


class ListService(ListSourcesUseCase):
    def __init__(self, registry: SourceRegistryPort) -> None:
        self._registry = registry

    def list_sources(self) -> Sequence[SourceDescriptor]:
        return sorted(self._registry.descriptors(), key=lambda d: d.id)

    def default_sources(self) -> Sequence[SourceDescriptor]:
        return [d for d in self._registry.descriptors() if d.group.active]
