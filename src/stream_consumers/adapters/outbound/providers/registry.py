"""Registry of source factories."""

from __future__ import annotations

from collections.abc import Sequence

from stream_consumers.domain.errors import UnknownSourceError
from stream_consumers.domain.models import SourceDescriptor
from stream_consumers.ports.outbound.providers import EventSourcePort, SourceDependencies, SourceFactoryPort, SourceRegistryPort


class FactoryRegistry(SourceRegistryPort):
    def __init__(self, factories: Sequence[SourceFactoryPort], deps: SourceDependencies) -> None:
        self._factories: dict[str, SourceFactoryPort] = {}
        for factory in factories:
            source_id = factory.descriptor.id
            if source_id in self._factories:
                raise ValueError(f"duplicate source id: {source_id}")
            self._factories[source_id] = factory
        self._deps = deps

    def _factory(self, source_id: str) -> SourceFactoryPort:
        try:
            return self._factories[source_id]
        except KeyError:
            raise UnknownSourceError(source_id) from None

    def descriptors(self) -> Sequence[SourceDescriptor]:
        return [f.descriptor for f in self._factories.values()]

    def descriptor(self, source_id: str) -> SourceDescriptor:
        return self._factory(source_id).descriptor

    def create(self, source_id: str) -> EventSourcePort:
        return self._factory(source_id).create(self._deps)
