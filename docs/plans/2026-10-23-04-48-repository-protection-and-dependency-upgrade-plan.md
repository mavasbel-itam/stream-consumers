# Repository protection, pre-push secret hook and dependency upgrade

| Field | Value |
|---|---|
| Written | 2026-10-23 04:48 UTC |
| Base | `main` = `origin/main` = `f401c0c` (CI run 39552466637 passed) |
| Approved | by the owner on 2026-10-23 ("proceed up to 3" of the follow-up list) |
| Branch | `hardening`, worktree `/tmp/opencode/sc-hardening` |

## 0. State read before writing (2026-10-23 04:40–04:48 UTC)

| Item | Reading | Source |
|---|---|---|
| Secret scanning, push protection, non-provider patterns, validity checks, Dependabot security updates | all `disabled` | `GET /repos/mavasbel-itam/stream-consumers` → `security_and_analysis` |
| Dependabot alerts | enabled | `GET …/vulnerability-alerts` → HTTP 204 |
| Branch protection of `main` | none | `GET …/branches/main` → `"protected": false` |
| Organization plan | `free` | `GET /orgs/mavasbel-itam` → `plan.name` |
| Pre-push hook | none; `.githooks/` does not exist, `core.hooksPath` unset | local clone |
| Outdated direct dependencies (`uv tree --outdated --depth 1`) | `websockets` 15.0.1 → 17.3, `neo4j` 6.2.0 → 6.4.1, `pymongo` 4.17.0 → 4.19.0, `opensearch-py` 3.0.0 → 3.2.0, `coverage` 7.16.2 → 7.17.0, `ruff` 0.17.0 → 0.17.2 | uv 0.13.0 |
| Outdated indirect dependencies (`uv lock --upgrade --dry-run`) | `certifi` 2026.10.18 → 2026.10.19, `pluggy` 1.6.0 → 1.7.0, `pycparser` 3.11 → 3.12, `python-dateutil` 2.9.0.post0 → 3.0.0 (needed by `opensearch-py`), `tzdata` 2026.5 added | uv 0.13.0 |
| CI actions (latest release) | `actions/checkout` v7.0.1 (used: `@v7`), `astral-sh/setup-uv` v10.3.2 (used: `v10.3.0`), `actions/upload-artifact` v7.0.2 (`@v7`), `actions/download-artifact` v8.0.2 (`@v8`) | `GET /repos/<action>/releases/latest` |
| uv | local 0.13.0; latest release 0.13.5; CI installs the latest (setup-uv has no `version`) | `uv --version`, `GET /repos/astral-sh/uv/releases/latest` |

## 1. GitHub protection (settings, no file change)

1. Enable through the API: secret scanning, push protection, Dependabot
   security updates. Also try non-provider patterns and validity checks and
   record GitHub's answer (they may need a paid Secret Protection licence on a
   `free` organization).
2. Protect `main`: no force push, no deletion, applied to administrators too
   (`enforce_admins`). No required status checks and no required reviews,
   because every change reaches `main` by a direct fast-forward push of the
   owner, and GitHub only accepts a push to a branch with required checks once
   the commit has already passed them. A future history rewrite needs the
   protection lifted for its force push and restored after it.
3. Verify by reading every setting back; read the secret-scanning alert list
   (GitHub scans the whole history once enabled); try one real force push of
   `main`'s parent (`b850c96`) over `main`, which must be refused; if it were
   accepted, `main` is restored at once by pushing `f401c0c` (a fast-forward).
   Push protection itself is checked by reading the setting only: proving it
   would mean pushing a real-format credential to the public repository.
4. Dependabot opens pull requests authored by `dependabot[bot]`; they cannot be
   merged as they are (every commit must carry the no-reply identity), so a
   proposed bump is redone in an own commit.

## 2. Pre-push hook and CI check

1. `.githooks/pre-push` (executable, POSIX `sh`): from the clone's top level,
   `exec uv run --locked pytest tests/live/test_secrets_live.py -m live -q -p
   no:cacheprovider`. Any failure, a missing `.env` (the fixture fails when it
   finds no secret) or a missing `uv` refuses the push. Enabled per clone with
   `git config core.hooksPath .githooks`; enabled in the owner's clone.
2. Tests, written first and seen failing:
   - e2e `tests/e2e/test_pre_push_hook.py`: a new repository built from the
     files to publish, one commit with the no-reply identity, a bare remote,
     a `.env` holding a random fake value of a known secret variable. A clean
     push is accepted; a commit holding the fake value is refused and the
     output names the variable, never the value; a commit holding a personal
     e-mail address is refused. The fake value and the address are built at
     run time so this file never holds them.
   - unit `tests/unit/test_publishing.py`: the hook is committed executable
     (mode 100755) and runs exactly the secret test; README and AGENTS.md give
     the `core.hooksPath` command; the CI workflow runs the secret test's
     checks that need no `.env`.
3. CI: a `publishing` job with the full history (`fetch-depth: 0`; a pull
   request is checked at its own head commit, not GitHub's merge commit) runs
   the three checks that need no `.env` (`-k "e_mail or no_reply"`).
4. Documents: README "Publishing safely" and "Tests", AGENTS.md.

## 3. Dependency upgrade

1. Raise to the newest release: `websockets` 17.3, `coverage` 7.17.0, `ruff`
   0.17.2, every indirect dependency (`uv lock --upgrade`), `setup-uv` v10.3.2.
2. Kept: `pymongo` 4.17.0, `neo4j` 6.2.0, `opensearch-py` 3.0.0 (and
   `cassandra-driver` 3.30.1, `redis` 8.1.0). AGENTS.md requires the database
   outputs to use the client versions labs-setup locks, recorded in
   `docs/plans/2026-10-20-00-11-event-outputs-plan.md` §1 (labs-setup
   `1f23f32`). The follow-up list of 2026-10-22 proposed raising three of them;
   that contradicted this rule. This session may not read labs-setup (owner's
   rule), so those versions move only when the owner reports new labs-setup
   versions.
3. websockets 16.0–17.3 changes read on the official changelog
   (https://websockets.readthedocs.io/en/stable/project/changelog.html,
   2026-10-23): Python ≥ 3.11 (project: 3.13); some boolean arguments
   keyword-only (`send(text=…)`, `ping(ack_on_close=…)`,
   `broadcast(raise_exceptions=…)`; the code passes none of them positionally);
   non-ASCII handshake headers in ISO-8859-1; `connect()` closes with 1011 when
   its context ends by an exception (17.2); a race between a fragmented message
   and cancelling `recv()` fixed (17.3; the transport cancels `recv()` through
   `asyncio.wait_for`).
4. Gates on the final code: lint and format; unit + component 100 %; database
   tests; e2e three times at 100 % (it stops every transport, WebSocket
   included, with SIGINT and SIGTERM); the live test of all 73 sources; the key
   tests; `keys` exit 0; the secret test; then CI.
5. Not changed, reported: local uv 0.13.0 vs 0.13.5 (a tool of the machine);
   the Docker test images (pinned on purpose; the database ones follow
   labs-setup).

## 4. Commits

1. Hook, CI job, tests, documents and this plan.
2. Upgrade.

Each passes the gates above before it is pushed; the hook guards both pushes.

## 5. Results of §1 and §2 (2026-10-23)

| Check | Result |
|---|---|
| Secret scanning, push protection | `enabled` (04:49 UTC, read back from `security_and_analysis`) |
| Non-provider patterns, validity checks | the PATCH was answered, the status stays `disabled`: not available to this `free` organization's public repository |
| Dependabot security updates | `PUT …/automated-security-fixes` → HTTP 204; read back `{"enabled":true,"paused":false}` |
| Secret-scanning alerts after the history scan | 0 (`GET …/secret-scanning/alerts`, 60 s after enabling) |
| Protection of `main` | `enforce_admins` true, force pushes false, deletions false, no required checks or reviews; `"protected": true` |
| Real force push of `b850c96` over `main` (04:51:05 UTC) | refused: `GH006: Protected branch update failed … Cannot force-push to this branch`; `main` stayed `f401c0c` |
| `tests/e2e/test_pre_push_hook.py` before the hook existed | 3 failed (every push accepted) |
| The same after adding `.githooks/pre-push` | 3 passed in 16.8 s: clean push accepted with `5 passed`; fake `.env` value refused naming `AISSTREAM_API_KEY in blob …` and `… in leak.txt`, the value absent from the output; personal address refused by both e-mail tests; the remote's `main` unchanged after each refusal |
| CI checks without `.env` (`KEYS_ENV_FILE=/nonexistent … -k "e_mail or no_reply"`) | 3 passed, 2 deselected |
| Lint and format | pass |
| Unit + component + database tests | 1,382 passed, coverage 100 % |
| e2e three times (04:59–05:14 UTC) | 23 passed each, coverage 100 % each |
| Secret test with the real `.env` | 5 passed |
