"""Environment values from the process environment and a `.env` file."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from stream_consumers.ports.outbound.system import SecretProviderPort


class EnvSecretProvider(SecretProviderPort):
    """Secrets from the process environment, then from a git-ignored `.env` file.

    The `.env` format is one `NAME=value` per line; blank lines and `#` comments
    are ignored and one pair of surrounding quotes is removed.
    """

    def __init__(self, environ: Mapping[str, str], dotenv: Path | None = None) -> None:
        self._environ = environ
        self._file: dict[str, str] = {}
        if dotenv is not None and dotenv.is_file():
            for line in dotenv.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                    value = value[1:-1]
                self._file[name.strip()] = value

    def get(self, name: str) -> str | None:
        value = self._environ.get(name) or self._file.get(name)
        return value or None

    def file_names(self) -> Sequence[str]:
        return list(self._file)
