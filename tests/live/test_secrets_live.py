"""No secret in anything git holds, and no personal e-mail address in the files: run before every push (the
repository is public). Reads the real `.env` like the key probes (`KEYS_ENV_FILE`, default `.env`); a finding
names the variable and the place, never the value.

Run: uv run pytest tests/live/test_secrets_live.py -m live
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from stream_consumers.adapters.outbound.providers.sources import FACTORIES, HELD_KEYS
from stream_consumers.adapters.outbound.system.environment import EnvSecretProvider

pytestmark = pytest.mark.live
ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path(os.environ.get("KEYS_ENV_FILE", ".env"))
SECRET_VARIABLES = (
    {v for f in FACTORIES if f.descriptor.credential for v in f.descriptor.credential.env_vars}
    | {v for h in HELD_KEYS for v in h.env_vars}
    | {"STREAM_CONSUMERS_OUTPUT_PASSWORD"}
)
FRAGMENT = 12
"""Characters of a secret that, found anywhere, count as a leak of it (a value cut or wrapped in a record)."""
TOKEN_FORMATS = {
    "private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "AWS access key id": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}"),
    "Slack token": re.compile(rb"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Google API key": re.compile(rb"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "Stripe live key": re.compile(rb"\b[sr]k_live_[0-9A-Za-z]{16,}"),
    "JSON Web Token": re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
}
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PUBLIC_ADDRESSES = {
    "transparency@entsoe.eu",  # ENTSO-E's published address for API access requests
    "contact@airplanes.live",  # airplanes.live's published contact, quoted from its HTTP 403 answer
    "cyberservices@cisa.dhs.gov",  # quoted from a provider's published page in a research record
    "git@github.com",  # the SSH user of every GitHub remote
}
PLACEHOLDER_DOMAINS = {"example.org", "example.social", "b.org", "d.io", "f.mx", "x.org", "y.org"}
"""Made-up domains of the tests' own payloads."""
MASKED_IRC = ".tmi.twitch.tv"
"""Twitch's IRC prefixes `<nick>!<nick>@<nick>.tmi.twitch.tv`, with the nick masked or a test's one-letter nick."""


def personal(address: str) -> bool:
    domain = address.split("@", 1)[1]
    return address not in PUBLIC_ADDRESSES and domain not in PLACEHOLDER_DOMAINS and not domain.endswith(MASKED_IRC)


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def secrets() -> Mapping[str, str]:
    env = EnvSecretProvider({}, ENV_FILE)
    values = {name: env.get(name) for name in SECRET_VARIABLES}
    return {name: value for name, value in values.items() if value}


def every_object() -> Iterator[tuple[str, bytes]]:
    """Every blob, commit and tag of every ref, the reflogs and the unreachable objects."""
    listed = git("rev-list", "--all", "--reflog", "--objects").decode().split()
    fsck = git("fsck", "--unreachable", "--no-reflogs", "--full").decode().splitlines()
    oids = {o for o in listed if re.fullmatch(r"[0-9a-f]{40}", o)} | {line.split()[-1] for line in fsck if line.startswith("unreachable")}
    for oid in sorted(oids):
        kind = git("cat-file", "-t", oid).decode().strip()
        if kind in ("blob", "commit", "tag"):
            yield f"{kind} {oid[:10]}", git("cat-file", "-p", oid)


def files_to_publish() -> Iterator[tuple[str, bytes]]:
    """The tracked files as they are now, and the untracked ones `git add -A` would take."""
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    for name in sorted(n for n in names if n and (ROOT / n).is_file()):
        yield name, (ROOT / name).read_bytes()


def leaks(found: Mapping[str, str], place: str, data: bytes) -> Iterator[str]:
    text = data.decode("utf-8", "replace")
    for name, value in found.items():
        pieces = [value] if len(value) < FRAGMENT else [value[i : i + FRAGMENT] for i in range(len(value) - FRAGMENT + 1)]
        if any(piece in text for piece in pieces):
            yield f"{name} in {place}"
    for kind, pattern in TOKEN_FORMATS.items():
        if pattern.search(data):
            yield f"a {kind} in {place}"


@pytest.fixture(scope="module")
def found() -> Mapping[str, str]:
    values = secrets()
    assert values, f"no secret value in {ENV_FILE}: nothing would be checked"
    return values


def test_no_secret_in_anything_git_holds(found: Mapping[str, str]) -> None:
    problems = [p for place, data in every_object() for p in leaks(found, place, data)]
    assert problems == []


def test_no_secret_in_the_files_to_publish(found: Mapping[str, str]) -> None:
    problems = [p for place, data in files_to_publish() for p in leaks(found, place, data)]
    assert problems == []


def test_no_personal_e_mail_address_in_the_files_to_publish() -> None:
    addresses = {
        (name, a.lower())
        for name, data in files_to_publish()
        for a in EMAIL.findall(data.decode("utf-8", "replace"))
        if personal(a.lower())
    }
    assert sorted(addresses) == []
