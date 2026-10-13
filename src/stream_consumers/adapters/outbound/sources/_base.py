"""Base class of every source factory."""

from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from stream_consumers.domain.errors import MissingCredentialError
from stream_consumers.domain.models import SourceDescriptor
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies, SourceFactoryPort


class BaseSourceFactory(SourceFactoryPort):
    """Holds the descriptor and resolves the API key before building the source."""

    DESCRIPTOR: ClassVar[SourceDescriptor]

    @property
    def descriptor(self) -> SourceDescriptor:
        return self.DESCRIPTOR

    def _key(self, deps: SourceDependencies) -> str | None:
        credential = self.DESCRIPTOR.credential
        if credential is None:
            return None
        value = deps.secrets.get(credential.env_var)
        if value is None and credential.required:
            raise MissingCredentialError(credential.env_var, credential.sign_up_url)
        return value

    def create(self, deps: SourceDependencies) -> EventSourcePort:
        return self._build(deps, self._key(deps))

    @abstractmethod
    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort: ...
