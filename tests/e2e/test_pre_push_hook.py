"""The pre-push hook (`.githooks/pre-push`) run by a real `git push`: a clean push is accepted; a push that would
publish a secret of `.env` or a personal e-mail address is refused, and the refusal names the variable, never
the value. The repository pushed is a new one built from the files to publish, with a `.env` of its own, so the
check reads only what this test puts there; the fake value and the address are built at run time, so this file
never holds them."""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ("-c", "user.name=mavasbel", "-c", "user.email=28605223+mavasbel@users.noreply.github.com")
SECRET_VARIABLE = "AISSTREAM_API_KEY"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *IDENTITY, *args], capture_output=True, text=True, check=True).stdout.strip()


@dataclass(frozen=True)
class Clone:
    repo: Path
    remote: Path
    secret: str
    base: str

    def commit(self, name: str, text: str) -> None:
        (self.repo / name).write_text(text)
        git(self.repo, "add", name)
        git(self.repo, "commit", "-q", "-m", f"add {name}")

    def push(self) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "KEYS_ENV_FILE")}
        return subprocess.run(
            ["git", "-C", str(self.repo), "push", "origin", "HEAD:main"], capture_output=True, text=True, env=env, timeout=600
        )

    def remote_main(self) -> str:
        return git(self.remote, "rev-parse", "main")


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory) -> Clone:
    work = tmp_path_factory.mktemp("pre-push")
    repo, remote = work / "repo", work / "remote.git"
    names = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"], capture_output=True, text=True, check=True
    ).stdout.split("\0")
    for name in (n for n in names if n and (ROOT / n).is_file()):
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, repo / name)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "files to publish")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "config", "core.hooksPath", ".githooks")
    secret = "e2e" + secrets.token_hex(16)
    (repo / ".env").write_text(f"{SECRET_VARIABLE}={secret}\n")
    return Clone(repo, remote, secret, git(repo, "rev-parse", "HEAD"))


@pytest.fixture
def clone(base: Clone) -> Iterator[Clone]:
    yield base
    git(base.repo, "reset", "-q", "--hard", git(base.remote, "rev-parse", "main") if _has_main(base.remote) else base.base)
    git(base.repo, "reflog", "expire", "--expire=now", "--all")
    git(base.repo, "gc", "-q", "--prune=now")


def _has_main(remote: Path) -> bool:
    return subprocess.run(["git", "-C", str(remote), "rev-parse", "-q", "--verify", "main"], capture_output=True).returncode == 0


def test_a_clean_push_is_accepted(clone: Clone) -> None:
    clone.commit("notes.txt", "nothing secret here\n")
    pushed = clone.push()
    assert pushed.returncode == 0, pushed.stdout + pushed.stderr
    assert "5 passed" in pushed.stdout + pushed.stderr
    assert clone.remote_main() == git(clone.repo, "rev-parse", "HEAD")


def test_a_push_publishing_a_secret_of_dot_env_is_refused_naming_only_the_variable(clone: Clone) -> None:
    before = clone.remote_main() if _has_main(clone.remote) else None
    clone.commit("leak.txt", f"token: {clone.secret}\n")
    refused = clone.push()
    output = refused.stdout + refused.stderr
    assert refused.returncode != 0
    assert f"{SECRET_VARIABLE} in blob" in output
    assert f"{SECRET_VARIABLE} in leak.txt" in output
    assert clone.secret not in output
    assert "failed to push" in output
    assert (clone.remote_main() if _has_main(clone.remote) else None) == before


def test_a_push_publishing_a_personal_e_mail_address_is_refused(clone: Clone) -> None:
    before = clone.remote_main() if _has_main(clone.remote) else None
    address = "someone" + "@" + "personal-mail.net"
    clone.commit("contact.txt", f"write to {address}\n")
    refused = clone.push()
    output = refused.stdout + refused.stderr
    assert refused.returncode != 0
    assert "test_no_personal_e_mail_address_in_the_files_to_publish" in output
    assert "test_no_personal_e_mail_address_in_anything_git_holds" in output
    assert (clone.remote_main() if _has_main(clone.remote) else None) == before
