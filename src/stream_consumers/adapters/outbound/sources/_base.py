"""Base class of every source factory."""

from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from stream_consumers.domain.errors import MissingCredentialError
from stream_consumers.domain.models import SourceDescriptor
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies, SourceFactoryPort


class BaseSourceFactory(SourceFactoryPort):
    """Holds the descriptor, resolves credentials and settings, then builds the source."""

    DESCRIPTOR: ClassVar[SourceDescriptor]

    @property
    def descriptor(self) -> SourceDescriptor:
        return self.DESCRIPTOR

    def _credentials(self, deps: SourceDependencies) -> Credentials | None:
        """All credential values, or None for an optional credential that is not (fully) set."""
        credential = self.DESCRIPTOR.credential
        if credential is None:
            return None
        values = {name: deps.secrets.get(name) for name in credential.env_vars}
        missing = [name for name, value in values.items() if value is None]
        if not missing:
            return {name: value for name, value in values.items() if value is not None}
        if credential.required:
            raise MissingCredentialError(missing, credential.sign_up_url)
        return None

    def setting(self, deps: SourceDependencies, env_var: str) -> str:
        """A declared setting: its environment value, else its default."""
        for setting in self.DESCRIPTOR.settings:
            if setting.env_var == env_var:
                return deps.secrets.get(env_var) or setting.default
        raise KeyError(f"{self.DESCRIPTOR.id} declares no setting {env_var}")

    def create(self, deps: SourceDependencies) -> EventSourcePort:
        return self._build(deps, self._credentials(deps))

    @abstractmethod
    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort: ...
