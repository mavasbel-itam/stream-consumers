"""The README's key table and settings list name every credential and setting of the catalog."""

from __future__ import annotations

import re
from pathlib import Path

from stream_consumers.adapters.outbound.sources import FACTORIES

README = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")


def section(title: str) -> str:
    start = README.index(f"\n## {title}\n")
    return README[start : README.index("\n## ", start + 1)]


def test_every_credential_has_a_row_in_the_key_table() -> None:
    lines = [line for line in section("API keys and configuration").splitlines() if line.startswith("| `")]
    variables_and_source = [(line.split("|")[1], line.split("|")[2]) for line in lines]
    for factory in FACTORIES:
        credential = factory.descriptor.credential
        if credential is not None:
            rows = [r for r in variables_and_source if all(f"`{v}`" in r[0] for v in credential.env_vars)]
            assert rows and f"`{factory.descriptor.id}`" in rows[0][1], factory.descriptor.id


def test_every_setting_is_named_in_the_settings_list() -> None:
    text = section("API keys and configuration")
    listed = set(re.findall(r"`([A-Z0-9_]+)`", text[text.index("Settings with defaults:") :].split("\n\n")[0]))
    assert listed == {s.env_var for f in FACTORIES for s in f.descriptor.settings}
