"""The guards of the public repository are in place: the versioned pre-push hook runs the secret test, the
documents tell every clone to enable it, and CI runs the checks that need no `.env` on the full history."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-push"
ENABLE = "git config core.hooksPath .githooks"
SECRET_TEST = "tests/live/test_secrets_live.py"


def test_the_hook_is_committed_executable() -> None:
    staged = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", ".githooks/pre-push"], capture_output=True, text=True, check=True
    ).stdout
    assert staged.split()[0] == "100755"


def test_the_hook_runs_the_secret_test_and_ends_with_its_status() -> None:
    commands = [line for line in HOOK.read_text().splitlines() if line and not line.startswith("#")]
    assert commands[-1] == f"exec uv run --locked pytest {SECRET_TEST} -m live -q -p no:cacheprovider"


def test_the_documents_tell_every_clone_to_enable_the_hook() -> None:
    for document in ("README.md", "AGENTS.md"):
        assert ENABLE in (ROOT / document).read_text(), document


def test_ci_runs_the_checks_that_need_no_env_file_on_the_full_history() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text()
    job = workflow.split("\n  publishing:\n", 1)[1].split("\n\n", 1)[0]
    assert "fetch-depth: 0" in job
    assert "github.event.pull_request.head.sha" in job
    assert f'uv run pytest {SECRET_TEST} -m live -k "e_mail or no_reply"' in job
