"""Domain errors."""


class StreamConsumersError(Exception):
    """Base class of every error raised on purpose by this package."""


class UnknownSourceError(StreamConsumersError):
    def __init__(self, source_id: str) -> None:
        super().__init__(f"unknown source: {source_id}")
        self.source_id = source_id


class MissingCredentialError(StreamConsumersError):
    def __init__(self, env_var: str, sign_up_url: str) -> None:
        super().__init__(f"missing API key {env_var} (free sign-up: {sign_up_url})")
        self.env_var = env_var
        self.sign_up_url = sign_up_url


class DecodeError(StreamConsumersError):
    """A message could not be decoded into events."""


class TransportError(StreamConsumersError):
    """The provider refused or broke the connection."""
