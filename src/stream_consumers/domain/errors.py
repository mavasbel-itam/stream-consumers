"""Domain errors."""

from collections.abc import Sequence


class StreamConsumersError(Exception):
    """Base class of every error raised on purpose by this package."""


class UnknownSourceError(StreamConsumersError):
    def __init__(self, source_id: str) -> None:
        super().__init__(f"unknown source: {source_id}")
        self.source_id = source_id


class MissingCredentialError(StreamConsumersError):
    def __init__(self, env_vars: Sequence[str], sign_up_url: str) -> None:
        super().__init__(f"missing API credentials {', '.join(env_vars)} (free sign-up: {sign_up_url})")
        self.env_vars = tuple(env_vars)
        self.sign_up_url = sign_up_url


class DecodeError(StreamConsumersError):
    """A message could not be decoded into events."""


class TransportError(StreamConsumersError):
    """The provider refused or broke the connection."""


class OutputTargetError(StreamConsumersError):
    """An output destination (`--out`) that cannot be used as written."""


class OutputError(StreamConsumersError):
    """An output could not be opened or written (a database or broker that refused or went away)."""

    def __init__(self, output: str, cause: BaseException) -> None:
        name, detail = type(cause).__name__, str(cause)
        super().__init__(f"output {output} failed: {detail if detail.startswith(name) else f'{name}: {detail}'}")
        self.output = output
