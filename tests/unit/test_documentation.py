"""The README documents every credential, setting, source link, docs page, command and option the code has."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from stream_consumers.adapters.inbound.cli import _parser
from stream_consumers.adapters.outbound.sources import FACTORIES

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def section(title: str) -> str:
    start = README.index(f"\n## {title}\n")
    end = README.find("\n## ", start + 1)
    return README[start:] if end == -1 else README[start:end]


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


def test_every_source_link_is_listed_in_reference_links() -> None:
    text = section("Reference links")
    for factory in FACTORIES:
        d = factory.descriptor
        row = next(line for line in text.splitlines() if line.startswith(f"| `{d.id}` |"))
        links = [d.docs_url, d.terms_url, *([d.credential.sign_up_url] if d.credential and d.credential.sign_up_url else [])]
        assert all(f"<{url}>" in row for url in links), d.id
        assert row.count("<https://") == len(links), d.id


def test_every_docs_page_is_linked_in_reference_links() -> None:
    text = section("Reference links")
    pages = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs").rglob("*.md"))
    assert pages and all(f"]({page})" in text for page in pages)


def test_every_command_and_option_is_documented_in_running_the_consumers() -> None:
    text = section("Running the consumers")
    parser = _parser()
    global_options = [a for a in parser._actions if a.option_strings and a.dest != "help"]
    assert all(f"| every command | `{a.option_strings[0]}" in text for a in global_options)
    commands = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    for name, command in commands.choices.items():
        assert f"| `{name}" in text, name
        for action in command._actions:
            if action.option_strings and action.dest != "help":
                assert f"| `{name}` | `{action.option_strings[0]}" in text, (name, action.option_strings[0])
