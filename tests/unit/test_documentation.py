"""The README documents every credential, setting, held key, source, docs page, command, option, output and
stop behaviour the code has, each in one place, and its internal links resolve."""

from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import pytest

from stream_consumers.adapters.inbound.cli import FORMATS, SINKS, _not_started, _parser
from stream_consumers.adapters.inbound.signals import SignalStopRequest
from stream_consumers.adapters.outbound.providers.sources import FACTORIES, HELD_KEYS
from stream_consumers.domain.models import Group
from tests.support import ManualStop

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text(encoding="utf-8")
GROUP_LABELS = {
    Group.KEYLESS: "A · keyless",
    Group.PROJECT_DOCUMENT: "B · project document",
    Group.FREE_KEY: "C · free key",
    Group.CANDIDATE: "D · candidate",
    Group.LOW_RATE: "E · low rate",
}
DESCRIPTORS = [f.descriptor for f in FACTORIES]


def section(title: str, level: int = 2) -> str:
    marks = "#" * level
    start = README.index(f"\n{marks} {title}\n")
    ends = [i for i in (README.find(f"\n{'#' * n} ", start + 1) for n in range(1, level + 1)) if i != -1]
    return README[start : min(ends)] if ends else README[start:]


def table_rows(text: str, first_column: str = "`") -> list[list[str]]:
    """The cells of the table rows of `text` whose first cell starts with `first_column`."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        if cells and cells[0].startswith(first_column):
            rows.append(cells)
    return rows


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation removed, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def test_every_credential_has_a_row_in_the_key_table() -> None:
    rows = table_rows(section("API keys", 3))
    for d in DESCRIPTORS:
        if d.credential is not None:
            matching = [r for r in rows if all(f"`{v}`" in r[0] for v in d.credential.env_vars)]
            assert matching and f"`{d.id}`" in matching[0][1], d.id


def test_every_setting_has_one_row_with_its_source_and_default() -> None:
    rows = table_rows(section("Settings", 3))
    expected = {(s.env_var, d.id, s.default) for d in DESCRIPTORS for s in d.settings}
    documented = {(r[0].strip("`"), r[1].strip("`"), "" if r[2] == "(empty)" else r[2].strip("`")) for r in rows}
    assert len(rows) == len(expected) == 11 and documented == expected


def test_every_held_key_has_a_row() -> None:
    rows = table_rows(section("Held keys", 3))
    assert [tuple(re.findall(r"`([A-Z0-9_]+)`", r[0])) for r in rows] == [h.env_vars for h in HELD_KEYS]
    assert [r[1] for r in rows] == [f"`{h.owner}`" for h in HELD_KEYS]


def test_the_variables_read_only_by_the_tests_are_listed() -> None:
    rows = table_rows(section("Variables read only by the tests", 3))
    assert [r[0] for r in rows] == ["`KEYS_ENV_FILE`", "`LIVE_SECONDS`", "`STREAM_CONSUMERS_E2E`"]


def test_the_sources_table_has_each_source_once_with_its_group_and_every_link() -> None:
    rows = table_rows(section("Sources"))
    assert sorted(r[0] for r in rows) == sorted(f"`{d.id}`" for d in DESCRIPTORS) and len(rows) == 73
    by_id = {r[0].strip("`"): r for r in rows}
    for d in DESCRIPTORS:
        row = by_id[d.id]
        assert row[3] == GROUP_LABELS[d.group], d.id
        links = [d.docs_url, *([d.credential.sign_up_url] if d.credential else []), d.terms_url]  # column order
        assert re.findall(r"\]\((https?://[^)]+)\)", " | ".join(row)) == links, d.id
        assert row[4] == f"{d.transport.value} / {d.delivery.value}", d.id


def test_the_measurements_table_has_each_source_once_with_its_group() -> None:
    rows = table_rows(section("Measurements"))
    assert sorted(r[0] for r in rows) == sorted(f"`{d.id}`" for d in DESCRIPTORS) and len(rows) == 73
    groups = {d.id: GROUP_LABELS[d.group] for d in DESCRIPTORS}
    assert all(r[1] == groups[r[0].strip("`")] for r in rows)


def test_groups_are_named_one_way_everywhere() -> None:
    for old in ("| keyless |", "| project document |", "| free key |", "| free key (", "low-rate (E)", "(group B)", "(group E)"):
        assert old not in README, old
    assert all(label in section("Sources") for label in GROUP_LABELS.values())


def test_every_anchor_link_resolves_to_a_heading() -> None:
    anchors = {slug(h) for h in re.findall(r"^#{1,6} (.+)$", README, flags=re.MULTILINE)}
    links = re.findall(r"\]\(#([^)]+)\)", README)
    assert links and sorted(set(links) - anchors) == []


def test_every_docs_page_is_linked_in_decision_records() -> None:
    text = section("Decision records")
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


def test_every_format_and_destination_scheme_is_documented_in_outputs() -> None:
    text = section("Outputs")
    formats = text[text.index("### Text formats") : text.index("### Destinations")]
    assert all(f"| `{name}`" in formats for name in FORMATS)
    destinations = text[text.index("### Destinations") :]
    assert all(f"| `{scheme}:" in destinations for scheme in SINKS)
    assert all(f"`{scheme}:" in section("Running the consumers") for scheme in SINKS)


async def test_stopping_a_run_quotes_what_the_program_prints() -> None:
    prose = re.sub(r"```.*?```", "", section("Stopping a run", 3), flags=re.DOTALL)  # not the captured runs
    text = " ".join(prose.split())
    err = io.StringIO()
    stop = SignalStopRequest(err, signals=())
    stop._request("SIGINT")
    assert err.getvalue().strip() in text
    stopped = ManualStop()
    stopped.request("SIGINT")
    err = io.StringIO()
    _not_started(stopped, 1, 3, err)
    assert err.getvalue().strip().replace("2 of 3", "<n> of <m>") in text
    for fact in (
        "stopped immediately by a second SIGINT; outputs may be incomplete",
        "stopped by SIGINT after <seconds> of <window> s",
        "a round cut short is not recorded",
        "--continue-from",
        "**130**",
        "**143**",
        "kill <pid>",
        "SIGINT ignored",
        "`uv run`",
        "|| break",
        "set -e",
    ):
        assert fact in text, fact


@pytest.mark.parametrize("code", ["0", "1", "2", "130 / 143", "141"])
def test_every_exit_code_is_in_the_troubleshooting_table(code: str) -> None:
    rows = table_rows(section("Exit codes and troubleshooting", 3), "exit")
    assert any(r[0] == f"exit {code}" for r in rows)


def test_every_run_status_and_key_state_is_in_the_troubleshooting_table() -> None:
    text = section("Exit codes and troubleshooting", 3)
    assert all(f"status `{s}`" in text for s in ("key-pending", "no-events", "error"))
    assert "`MISSING` in `keys`" in text and "`unknown` in `keys`" in text
