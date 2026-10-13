"""The CLI composition root, in-process, over a scripted catalog."""

from __future__ import annotations

import io
import json
import runpy
import sys
from pathlib import Path

import pytest

from stream_consumers.adapters.inbound.cli import DEFAULT_CATALOG, main

CATALOG = ["--catalog", "tests.catalog_scripted"]


def run(*argv: str, env_file: Path | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    extra = ["--env-file", str(env_file)] if env_file else ["--env-file", "/nonexistent/.env"]
    code = main([*CATALOG, *extra, *argv], out, err)
    return code, out.getvalue(), err.getvalue()


def test_list_prints_one_json_line_per_source_sorted() -> None:
    code, out, _ = run("list")
    rows = [json.loads(line) for line in out.splitlines()]
    assert code == 0 and [r["id"] for r in rows] == ["alpha", "broken", "keyed"]
    assert rows[0]["group"] == "A" and rows[0]["personal_fields"] == ["user"]


def test_default_catalog_lists_the_65_sources() -> None:
    out = io.StringIO()
    assert main(["list"], out, io.StringIO()) == 0
    assert len(out.getvalue().splitlines()) == 65 and DEFAULT_CATALOG.endswith(".sources")


class TestConsume:
    def test_to_stdout_masked_with_the_report_on_stderr(self) -> None:
        code, out, err = run("consume", "alpha", "--seconds", "0.2", "--max-events", "2")
        events = [json.loads(line) for line in out.splitlines()]
        report = json.loads(err)
        assert code == 0 and [e["payload"] for e in events] == [{"user": "<masked>", "n": 1}, {"user": "<masked>", "n": 2}]
        assert report["status"] == "ok" and report["events"] == 2 and report["rate_basis"] == "observed"

    def test_raw_to_a_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out" / "a.jsonl"
        code, out, _ = run("consume", "alpha", "--seconds", "0.1", "--raw", "--out", str(target))
        assert code == 0 and out == ""
        assert [json.loads(line)["payload"]["user"] for line in target.read_text().splitlines()] == ["ana", "beto"]

    def test_missing_key_is_reported_with_the_sign_up_link(self) -> None:
        code, _, err = run("consume", "keyed", "--seconds", "0.1")
        report = json.loads(err)
        assert code == 0 and report["status"] == "key-pending" and "https://sign.up/here" in report["detail"]

    def test_key_from_the_env_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("SCRIPTED_KEY=abc\n")
        code, out, _ = run("consume", "keyed", "--seconds", "0.1", env_file=env)
        assert code == 0 and json.loads(out)["payload"] == {"key_used": True}

    def test_a_failing_source_exits_1(self) -> None:
        code, _, err = run("consume", "broken", "--seconds", "0.1")
        assert code == 1 and json.loads(err)["status"] == "error"

    def test_an_unknown_source_exits_2(self) -> None:
        code, _, err = run("consume", "nope", "--seconds", "0.1")
        assert code == 2 and err == "error: unknown source: nope\n"


class TestCheck:
    def test_all_sources_summary_and_report(self, tmp_path: Path) -> None:
        code, out, _ = run("check", "--seconds", "0.1", "--reports", str(tmp_path))
        lines = out.splitlines()
        assert code == 1 and lines[-1] == "3 sources, 2 delivered or key pending, 1 failed"
        assert [line.split()[0] for line in lines[:3]] == ["alpha", "broken", "keyed"]
        (report,) = tmp_path.glob("check-*.json")
        assert {r["source_id"] for r in json.loads(report.read_text())} == {"alpha", "broken", "keyed"}

    def test_selected_sources_pass(self, tmp_path: Path) -> None:
        code, out, _ = run("check", "alpha", "--seconds", "0.1", "--reports", str(tmp_path))
        assert code == 0 and "rate=" in out and out.endswith("1 sources, 1 delivered or key pending, 0 failed\n")

    def test_unknown_ids_are_rejected_before_running(self, tmp_path: Path) -> None:
        code, _, err = run("check", "alpha", "zzz", "--reports", str(tmp_path))
        assert code == 2 and "zzz" in err and not list(tmp_path.iterdir())


def test_sample_writes_one_report_per_round(tmp_path: Path) -> None:
    code, out, _ = run("sample", "alpha", "--rounds", "2", "--interval", "0.15", "--window", "0.1", "--reports", str(tmp_path))
    assert code == 0 and out.startswith("alpha")
    assert sorted(p.name[:8] for p in tmp_path.glob("round-*.json")) == ["round-01", "round-02"]


def test_profile_writes_masked_events_and_field_statistics(tmp_path: Path) -> None:
    code, _, _ = run("profile", "alpha", "--max-events", "5", "--seconds", "0.1", "--out", str(tmp_path / "p"), "--reports", str(tmp_path))
    assert code == 0
    lines = (tmp_path / "p" / "alpha.jsonl").read_text().splitlines()
    assert [json.loads(line)["payload"]["user"] for line in lines] == ["<masked>", "<masked>"]
    (report,) = tmp_path.glob("profiles-*.json")
    fields = {f["name"]: f for f in json.loads(report.read_text())[0]["fields"]}
    assert fields["user"]["distinct"] == 2 and fields["user"]["example"] == "<masked>"


def test_keys_shows_status_and_template_without_values(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("SCRIPTED_KEY=very-secret\n")
    code, out, _ = run("keys", env_file=env)
    assert code == 0 and "very-secret" not in out
    assert out.split() == ["keyed", "SCRIPTED_KEY", "secret", "required", "set", "https://sign.up/here"]
    code, out, _ = run("keys")
    assert code == 0 and out.split()[4] == "MISSING"
    code, out, _ = run("keys", "--template", env_file=env)
    assert code == 0 and "SCRIPTED_KEY=\n" in out and "very-secret" not in out


def test_keys_shows_settings_with_their_default() -> None:
    out = io.StringIO()
    assert main(["keys"], out, io.StringIO()) == 0
    assert any(
        line.split()[:5] == ["crossref", "CROSSREF_MAILTO", "setting", "optional", "default"] for line in out.getvalue().splitlines()
    )


def test_unknown_command_is_an_argparse_error() -> None:
    with pytest.raises(SystemExit) as error:
        main(["frobnicate"], io.StringIO(), io.StringIO())
    assert error.value.code == 2


def test_module_entry_point(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["stream-consumers", *CATALOG, "list"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("stream_consumers", run_name="__main__")
    assert error.value.code == 0 and capsys.readouterr().out.count("\n") == 3
