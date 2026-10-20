# Plan: Ctrl+C stops every command cleanly, fresh live evidence, and a consistent README

Written 2026-10-20 06:41 UTC from `main` = `origin/main` = `a241b80` (CI run
`39366781615` green). Historical record: once executed, later facts are added
as dated addenda, never by rewriting this text.

Owner's requests (2026-10-20): (1) are all the streams well tested; (2) a README
that is consistent, concise, without redundancy but complete, with several
examples of running the consumers and the configuration (`.env`) instructions;
(3) Ctrl+C must stop the stream consumers; (4) a full detailed plan with no
skipped point.

## 1. Evidence gathered before writing this plan

### 1.1 Test coverage of the sources (read-only inventory)

| Tier | What exists today | Last run |
|---|---|---|
| unit | 73 fixtures in `tests/fixtures/raw` (one per source plus `mbta_v3_stream`; `fink` has none, `lasair` is the provider's documentation example); `tests/unit/test_sources.py` parametrised over every source | CI `39366781615`, 100 % |
| component | every transport against a local server, Kafka against a real broker, broker and database outputs read back with their own clients | same CI run |
| e2e | the CLI as a subprocess against local servers for every transport | same CI run, 100 % |
| live keys | `tests/live/test_keys_live.py`: 35 passed, 2 skipped | 2026-10-20 |
| live sources | `tests/live/test_sources_live.py`: all 73 sources (groups A–E) for `LIVE_SECONDS` (60) each; a source must be `ok` (≥ 1 event) or `key-pending` | **not run since the commits of 2026-10-19 (`6a0514d` changed how sources are read side by side)** |
| all-source `check` | newest `data/reports/check-20261019T144614Z.json`; the newest full-catalog measurement is the sampling runs stopped 2026-10-19 05:38 UTC | not run on the current code |

Gap: no full run against the real providers on the current code.
Known conflict to resolve by measurement: the live source test requires `ok`
from every group E source, but `gfw` measured 0 events in 22 hourly readings
(`data/gfw-growth-20261018/`), so that test cannot pass for `gfw` as written.

### 1.2 Ctrl+C and termination today (measured 2026-10-20 06:38–06:41 UTC)

There is no signal handling in `src/`; `asyncio.run` (Python 3.13.16) turns the
first SIGINT into cancellation of the main task. Probes: a real Ctrl+C typed on
a pseudo-terminal (`/tmp/opencode/sigint/ptyprobe.py`, byte `0x03`), and
`kill -TERM` (`probe_term.sh`).

| Run | Signal | Stopped after | Exit | What was left |
|---|---|---|---|---|
| `consume wikimedia --seconds 30 --out file.jsonl` | Ctrl+C at 5 s | 0.18 s | 130 | ~50-line traceback ending `KeyboardInterrupt`; **no run report**; 117 lines in the file |
| `consume coinbase --format json --out file.json` | Ctrl+C at 4 s | 0.30 s | 130 | traceback; array closed, file parses |
| `consume coinbase --out sqlite:…` | Ctrl+C at 4 s | 0.26 s | 130 | traceback; 18 rows |
| `check wikimedia coinbase bitso --seconds 30` | Ctrl+C at 8 s | 0.33 s | 130 | traceback; **no summary and no `check-*.json`** |
| `profile coinbase --seconds 30` | Ctrl+C at 8 s | 0.25 s | 130 | traceback; sample file kept; **no `profiles-*.json`** |
| `sample … --rounds 3 --interval 20 --window 5` | Ctrl+C at 8 s | 0.22 s | 130 | traceback; `round-01` kept |
| `uv run stream-consumers consume wikimedia` | Ctrl+C at 6 s | 0.13 s | 130 | traceback |
| `consume wikimedia`, 3 presses 1 s apart | Ctrl+C ×3 | 0.18 s | 130 | same as one press |
| `consume coinbase --format json --out file.json` | `kill -TERM` at 4 s | 0.010 s | 143 | **array never closed and the last object cut** (`JSONDecodeError` at char 8653); no report |
| `consume coinbase --out sqlite:…` | `kill -TERM` at 4 s | 0.016 s | 143 | 25 rows; `close()` never ran, so the waiting batch was never written |
| `consume …` started with `&` from a non-interactive shell | `kill -INT` | not stopped; ran the full 30 s | 0 | the shell starts background commands with SIGINT ignored |

Conclusion: Ctrl+C already stops quickly, but it prints a traceback, loses the
reports and summaries, and SIGTERM (`kill`, `docker stop`, systemd) corrupts
text outputs and loses batched events.

## 2. Decisions (recommended default first)

| # | Question | Recommended | Alternative |
|---|---|---|---|
| D1 | Exit code after a clean stop | 130 for Ctrl+C (SIGINT), 143 for SIGTERM, always, so scripts and `set -e` can tell an interrupted run from a complete one | 0 when events were delivered (as `ping` does) |
| D2 | `sample` stopped in the middle of a round | the unfinished round is **not** written (a cut window would enter the median); finished rounds stay; the message says how to resume with `--continue-from` | write it marked as stopped |
| D3 | `check` / `profile` stopped | sources being read end now and are reported with what arrived (`detail` = `stopped by SIGINT after <s> of <window> s`); sources not started yet are not started and are counted in the summary as `not started`; the report file and summary are written | write nothing |
| D4 | Second Ctrl+C | quits at once: one line `stopped immediately; outputs may be incomplete`, exit 130, no traceback | ignore further presses |
| D5 | Which signals | SIGINT and SIGTERM handled the same way; a SIGINT ignored at start (background job) stays ignored, as POSIX shells expect; the README says to use `kill <pid>` there | also SIGHUP |
| D6 | How the stop reaches the application | an inbound port `StopRequestPort` (the operator drives the stop; Cockburn's primary actor), implemented by `adapters/inbound/signals.py` and handed by the CLI to each use case | an outbound port in the system group |
| D7 | Where a stopped run is recorded | in `RunReport.detail` (no change to the report schema, so old `round-*.json` files still load) | a new `RunReport` field |
| D8 | Live source test and group E | group A–D sources must be `ok` or `key-pending`; group E sources must not be `error` (`no-events` is their measured state) | keep the test as is and let `gfw` fail |
| D9 | Group names in the README | one form everywhere: `A · keyless`, `B · project document`, `C · free key`, `D · candidate`, `E · low rate` | letters only |

## 3. Work items

### Stage 0: fresh live evidence on the current code (before any change)

0.1 `uv run stream-consumers check --reports data/reports/baseline-20261020`
(65 sources, defaults); record per-source status and rate.
0.2 `uv run pytest tests/live/test_sources_live.py -m live` (73 sources);
record every failure with its reason.
0.3 `uv run pytest tests/live/test_keys_live.py -m live` and
`uv run stream-consumers keys` (exit 0 expected).
0.4 Every failure is classified by evidence (a second run plus the provider's
own status or a direct request) as a provider outage or a defect here; a defect
is fixed test-first in this work, an outage is recorded in "Known behaviour"
with its date.

### Stage 1: clean stop (commit 1)

Ports and domain
1.1 `ports/inbound.py`: `StopRequestPort(ABC)` with `reason() -> str | None`
(signal name once requested) and `async wait() -> None`.
1.2 The use-case ports `ConsumeStreamUseCase.consume`, `CheckSourcesUseCase.check`,
`SampleSourcesUseCase.sample`, `ProfileSourcesUseCase.profile` take
`stop: StopRequestPort`; a `NeverStop` adapter keeps callers that cannot be
stopped (tests, `profile`'s inner calls) explicit.
1.3 `domain/errors.py`: no new error; a stop is a normal end of the window.

Adapters
1.4 `adapters/inbound/signals.py`: `SignalStopRequest(StopRequestPort)`
installs SIGINT and SIGTERM handlers with `loop.add_signal_handler` (SIGINT only
if not ignored at start, D5); the first signal records the reason, prints
`stopping (<signal>): finishing outputs; press Ctrl+C again to quit at once`
to standard error and removes its handlers so a second signal takes the
default action (D4); `close()` removes them at the end of the run. On a
platform without `add_signal_handler` it falls back to `signal.signal`.
1.5 `cli.py`: creates the stop request inside the running loop, passes it to
the services, writes summaries and reports after a stop, returns 130 / 143
(D1), and catches `KeyboardInterrupt` in `main` for the second press (D4).

Services
1.6 `ConsumeService`: the stop ends the window. The per-event wait stays an
`asyncio.timeout`; one watcher task per run reschedules the current timeout to
now when the stop is requested, so a stop takes the same path as the window
ending (no task created per event). The event being written is finished; the
iterator is closed as today; `detail` records the stop (D7).
1.7 `CheckService` / `ProfileService`: a source waiting for the semaphore does
not start after the stop; the result lists started sources only and the count
of sources not started (D3).
1.8 `SampleService`: the wait between rounds races the stop; a round cut by
the stop is not written and not returned (D2); the CLI prints
`round <n> not recorded; resume with --continue-from <dir>`.
1.9 Outputs need no change: every sink is closed in `finally`; tests prove it
for each kind (1.12).

Tests (each written first and shown failing on `a241b80`)
1.10 unit: `SignalStopRequest` with real `os.kill(os.getpid(), …)`: first
signal sets the reason, second SIGINT raises `KeyboardInterrupt`, second
SIGTERM is restored to default, ignored SIGINT stays ignored, `close()`
restores the handlers.
1.11 unit: `ConsumeService` stopped while waiting, between events and before
the start; `CheckService`, `ProfileService` (not-started sources),
`SampleService` (stop during the wait and during a round); `main` returns 130
without a traceback on `KeyboardInterrupt`; the CLI exit codes 130 / 143.
1.12 e2e (real subprocess, `send_signal`): for each of the nine transports
(WebSocket, SSE, MQTT, NATS, ZeroMQ, TCP, HTTP poll, file drop, Kafka) SIGINT
stops within 2 s with a run report; SIGTERM the same with 143; `--format json`
parses after a stop, CSV/TSV end with a complete row, `sqlite:` rows equal the
report's `events`; `check` writes `check-*.json` and the summary; `profile`
writes `profiles-*.json`; `sample` keeps only finished rounds and
`--continue-from` resumes from them; a second SIGINT exits 130 at once; one
test types `0x03` on a pseudo-terminal (the real Ctrl+C path, process group).
1.13 component (`-m databases` and the broker module): SIGTERM during
`consume` into Kafka, MQTT, NATS, MongoDB, Cassandra, Redis, Neo4j and
OpenSearch; the events read back equal the run report's `events`.
1.14 `test_architecture.py`: the inbound port set includes `StopRequestPort`;
`adapters/inbound/` may hold `signals.py`, which implements an inbound port.
1.15 Performance guard: the e2e fairness/starvation tests (commit `6a0514d`)
pass unchanged.

Live verification
1.16 Repeat the measurements of 1.2 against the real providers (Ctrl+C on a
pseudo-terminal and SIGTERM, every row of the table) and record the new table
in the addendum: no traceback, report present, outputs complete, exit codes.

### Stage 2: README (commit 2)

Structure (each fact once; tables generated where the code holds the data):

| # | Section | Content |
|---|---|---|
| 1 | Title | one paragraph: what, private, where the decision records are |
| 2 | Requirements | uv (installs Python 3.13); Internet for the sources; Docker only for the tests; Linux/macOS signals |
| 3 | Quick start | `uv sync`, `cp .env.example .env`, `keys`, `consume wikimedia --max-events 5` |
| 4 | Configuration | where values come from (process environment wins over `.env`; `--env-file`; `.env.example` generated by `keys --template` and kept identical by a test); the 17 secrets table (variable, source, required/optional, sign-up page, where it is sent, documented limit); a new 11-settings table (variable, source, default, meaning), checked against the descriptors; `STREAM_CONSUMERS_OUTPUT_PASSWORD`; the 28 held keys (what they are, why kept); `keys` output and exit codes; the variables read only by tests (`KEYS_ENV_FILE`, `LIVE_SECONDS`, `STREAM_CONSUMERS_E2E`); terms worth reading |
| 5 | Running the consumers | commands table, options-and-defaults table, **Stopping a run** (Ctrl+C, second Ctrl+C, `kill <pid>` / `docker stop`, exit codes, what is kept per command), **recipes by task** (about 15, each executed and its output captured: explore `list` with `jq`; one source to the terminal; capture 10 min to a file; CSV for a spreadsheet; pipe into `jq`/`head`; a group E source; a source with a key; another `.env`; one source into SQLite, Kafka and MongoDB; health check of all sources; 24-hour sampling in the background, resume, verdict; profile), exit-code and troubleshooting table (`key-pending`, `no-events`, `error`, 1, 2, 130, 141, 143, `unknown` in `keys`) |
| 6 | Outputs | event document; formats; destinations; one real example per destination (kept, shortened) |
| 7 | Sources | one table of all 73: id, name linked to its documentation, provider, group (D9), transport / delivery, key, terms link; replaces today's source table, low-rate table and reference-links table |
| 8 | Measurements | the inclusion rule in five lines; one table of 73 (run, rounds, median, result; for group E the one-line reason); how rates are measured; why 24 rounds; settled verdicts |
| 9 | Known behaviour | per-source notes only, shortened to the fact and its date |
| 10 | Architecture | as today plus the stop port in the diagram and tree |
| 11 | Tests | as today plus the stop tests and the live-test group E rule |
| 12 | Decision records | the 9 `docs/` pages, one line each |

2.1 Nothing is lost: every sentence removed from the README is mapped to the
`docs/` page and section that already states it, or the fact is added there
(reference pages get a change-log row; plans and research get nothing). The
mapping table goes into this plan's addendum.
2.2 Every command in the README is run on the final code and its shown output
is captured from that run, with date and time; personal values masked.
2.3 Guards in `tests/unit/test_documentation.py` (each shown failing on a
broken copy): existing six kept; new: every setting's default in the README
equals the descriptor's; each of the 73 ids appears exactly once in the
Sources table and once in the Measurements table; each group label is one of
D9; every `#anchor` link resolves to a heading; every command, option, exit
code and signal behaviour of `Stopping a run` is present.
2.4 Live link check of every README link (HTTP 200, or the documented
exception with its archived copy).
2.5 `AGENTS.md`: the stop contract (every long-running use case takes
`StopRequestPort`; outputs closed and reports written after a stop; e2e signal
tests per transport), the single Sources table rule, the settings table rule.
2.6 `docs/README.md` lists this plan; `docs/reference/…sub-threshold-sources.md`
and `…api-key-gated-sources.md` receive any fact moved out of the README, with
change-log rows.

### Stage 3: gates, commits and records

3.1 Before each commit: `ruff check`, `ruff format --check`,
`pytest --cov` (100 %), `pytest -m databases`, e2e three times (100 %),
broker component tests three times on one core (`taskset -c 0`), live keys,
`keys` exit 0, secret scan.
3.2 Final live run: stage 0 repeated on the final code (`check` of 65,
live source test of 73); the README's measured statements come from it.
3.3 Commit 1 (stop + plan + its `docs/README.md` row), push, CI green;
commit 2 (README, guards, reference pages, `AGENTS.md`), push, CI green.
3.4 Records: dated addendum in this plan (results, the stop table after the
change, the README mapping table); project memory for the stop contract;
resume note updated; Hindsight initiative captured before coding.
3.5 Clean-up: `/tmp/opencode/sigint/` removed; no test containers left;
`main` = `origin/main`, nothing uncommitted.

## 4. Out of scope

The CSV/other output work (done), the course repository, the labs-setup
clusters, and the lab tier (dropped 2026-10-20).

## 5. Addendum 2026-10-20: stages 0 and 1 done

### 5.1 Stage 0 results (code `a241b80`, before any change)

| Item | Run (UTC) | Result |
|---|---|---|
| 0.1 `check` of the 65 active sources (30-s windows) | 08:20–08:38 | 64 `ok`, `albion` `no-events`; exit 1 |
| 0.2 live source test, 73 sources (60-s windows) | 08:38–08:54 | 73 passed (`gfw` and the other group E sources delivered this time) |
| 0.3 live key suite; `keys` | 08:54–08:55 | 35 passed, 2 skipped (Lasair, Fink: no credentials); `keys` exit 0 |

0.4 classification of the one failure: `albion` read 0 events again in two 30-s
`consume` runs (about 16:08 UTC). A NATS subscription to `>` with the project's
public credentials, made directly with nats-py (server 2.10.14), counted 101
`marketorders.deduped` messages in the next 45 s; then `consume albion --seconds 45`
and the direct subscription ran side by side (16:10 UTC) and both counted exactly
1009. The consumer is correct; the provider publishes in bursts, as "Known
behaviour" already records. No defect, no code change.

### 5.2 Stage 1 as built (differences from section 3)

- 1.1 `StopRequestPort.wait()` returns the reason (`str`), not `None`.
- 1.2 No `NeverStop` adapter: the architecture rule lets application modules
  import only the domain and ports, and the CLI always has a real stop request.
  `stop` is therefore a required keyword argument of the four use cases; tests
  pass a `ManualStop` (tests/support.py) that they request or never request.
- 1.4 Handlers are installed with `signal.signal`, not `loop.add_signal_handler`:
  a handler run by the event loop cannot act while the loop is blocked (a write
  to a full pipe), and the second signal must still end the process. The first
  signal hands the request to the loop (`call_soon_threadsafe`), which prints
  `stopping (<signal>): ending the run, closing outputs and writing reports; a
  second signal (Ctrl+C) quits at once` before anything else is written.
- D4 / 1.10: the second signal prints `stopped immediately by a second <signal>;
  outputs may be incomplete`, restores the default action and sends the signal
  to the process again, so it ends *by* the signal (a shell shows 130 or 143).
  After a clean Ctrl+C stop the console entry point (`cli:run`, now the
  `stream-consumers` script and `python -m stream_consumers`) also ends by
  SIGINT, without a traceback. Measured reason: an ordinary exit status 130 let
  `bash -c 'for …; do stream-consumers consume …; done'` go on to the next
  command after Ctrl+C (all iterations ran, 25 s); ending by the signal stops the
  loop as for any other program (0.24 s).
- D3: the sources not started are reported on standard error
  (`stopped by SIGINT: <n> of <m> sources not started`); the summary line counts
  the started ones.
- 1.8 message: `stopped by <signal>: <n> of <planned> rounds recorded; a round
  cut short is not recorded; resume with --continue-from <reports dir>`.
- Standard output of `consume` is now handed on after every event
  (`TextStreamEventSink(flush_each=True)`), so `consume … | jq` sees each event
  when it arrives instead of after an 8-KiB buffer (`io.DEFAULT_BUFFER_SIZE` 8192 on Python 3.13.16) filled; found by the e2e test
  that waits for the first event through a pipe.
- 1.13 also covers ZeroMQ. The MQTT check uses Eclipse Mosquitto
  (`eclipse-mosquitto:2.1.2-alpine`): amqtt 0.12.1 acknowledged every QoS 1
  publish but forwarded only 8–29 of 58 to its subscribers, while Mosquitto
  delivered 58 of 58 in 5 of 5 runs.
- Found by the live measurement (1.16) and fixed: 9 of 24 WebSocket sources
  took 10.2 s to stop (`atlas`, `base_logs`, `bluesky`, `ris`, `bsc_logs`,
  `solana`, `aisstream`, `binance`, `polygon_logs`), `gemini` 5.1 s, `bitso`
  2.2 s, on every run end and not only after a signal. Cause (websockets 15.0.1
  documentation, "websockets' buffers"): once 16 frames are queued unread the
  connection stops reading the network, so the server's reply to the close is
  never read and `close()` waits `close_timeout`, 10 s by default; Bitso's server
  takes 2.1 s to answer a close. `WebSocketSource` now sets `close_timeout=1`
  (`CLOSE_TIMEOUT_S`); a component test reproduces the 10.01-s close first.
- 1.12 shown failing first: with the new tests on `a241b80` all 7 e2e stop tests
  fail (traceback instead of a report, no summary, no rounds, a background job
  not stopped by SIGTERM cleanly, the shell loop not stopped); the component
  stop tests cannot import their port there.
- `.coveragerc.e2e` excludes three paths that run where coverage cannot record
  them (the second signal, the quiet exception hook after the interpreter's
  last step, a Ctrl+C outside a run); the unit tier covers them.

### 5.3 1.16 the 1.2 table repeated on the final stage-1 code (finished 16:04 UTC)

| Run | Signal | Stopped after | Exit | What was left |
|---|---|---|---|---|
| `consume wikimedia --seconds 30 --out file.jsonl` | Ctrl+C at 5 s | 0.15 s | 130 | no traceback; run report `stopped by SIGINT after 4.554 of 30 s`, events=118; 118 lines in the file |
| `consume coinbase --format json --out file.json` | Ctrl+C at 4 s | 0.24 s | 130 | no traceback; report events=42; array closed, parses: 42 objects |
| `consume coinbase --out sqlite:…` | Ctrl+C at 4 s | 0.30 s | 130 | no traceback; report events=49; 49 rows |
| `check wikimedia coinbase bitso --seconds 30` | Ctrl+C at 8 s | 1.14 s | 130 | no traceback; summary `3 sources, 3 delivered or key pending, 0 failed`; `check-*.json` with 3 sources |
| `profile coinbase --seconds 30` | Ctrl+C at 8 s | 0.29 s | 130 | no traceback; sample file 93 lines; `profiles-*.json` written (93 events inspected) |
| `sample … --rounds 3 --interval 20 --window 5` | Ctrl+C at 8 s | 0.13 s | 130 | no traceback; ['round-01'] kept; `stopped by SIGINT: 1 of 3 rounds recorded; a round cut short is not recorded; resume with --continue-from <dir>` |
| `uv run stream-consumers consume wikimedia` | Ctrl+C at 6 s | 0.13 s | 130 | no traceback; run report present, events=171 |
| `consume wikimedia`, 3 presses 1 s apart | Ctrl+C ×3 | 0.16 s | 130 | no traceback; ended after the first press (report events=87); the later presses found no process |
| `consume coinbase --format json --out file.json` | `kill -TERM` at 4 s | 0.24 s | 143 | no traceback; array closed, parses: 55 objects = report events 55 |
| `consume coinbase --out sqlite:…` | `kill -TERM` at 4 s | 0.24 s | 143 | no traceback; 24 rows = report events 24; the waiting batch was written |
| `consume coinbase --format csv --out file.csv` | `kill -TERM` at 4 s | 0.35 s | 143 | no traceback; 33 rows = report events 33; every row [20] columns |
| `consume …` started with `&` from a non-interactive shell | `kill -INT`, then `kill -TERM` | 0.17 s after TERM | 143 | SIGINT ignored (still running 2 s later: True); SIGTERM: report `stopped by SIGTERM after 5.578 of 30 s`; no traceback |

All 65 active sources, `consume` stopped with SIGTERM after 8 s, all 65 at once
(finished 16:00 UTC): exit 143 for every one; stop time minimum 0.29 s, median 0.92 s,
maximum 1.38 s.

### 5.4 Found while running the recipes and the gates (2026-10-20 16:13–17:00 UTC), all fixed test-first

- **One stop delivered twice.** `timeout 20 uv run stream-consumers consume
  wikimedia` ended with `stopped immediately by a second SIGTERM`: GNU `timeout`
  (without `--foreground`) signals its command and then its process group, and
  `uv run` passes the first one on. A probe recorded the two SIGTERMs 0.05 ms
  apart in 2 of 3 runs through `uv run`; run directly, the two sends merged into
  one delivery in 3 of 3. Fix: `REPEAT_WINDOW_S = 1.0`; a repeat within it is the
  same stop. Two more cases behind it: a clean stop can be over in 0.7 ms, so
  `close()` keeps the handler after a stop instead of restoring `SIG_DFL`; and
  CPython's signal-module shutdown puts the default action back on every Python
  handler, so `cli.run()` ignores the stop signals once a stopped run returned
  (a traced run showed the repeat arriving after the run ended and killing the
  process with -15 instead of exit status 143). After the fix: 3 of 3 runs with
  two SIGTERMs 5 ms apart exit 143 with the report; `timeout 6 uv run …` 3 of 3
  clean. Tests: two unit tests, one e2e test that fails with the window at 0.
- **`uv run` and shell loops.** Through `uv run`, uv 0.13.0 exits with status
  130 after its child was ended by SIGINT, so bash continues a `for` loop after
  Ctrl+C (measured: all three iterations ran); with `.venv/bin/stream-consumers`
  the loop stopped at once, and with `uv run … || break` or `set -e` too. The
  README says so; no code can change uv's exit status.
- **Tests that inherit an ignored SIGINT.** The first gate run, started with
  `setsid nohup … &`, failed 5 SIGINT tests: such a run has SIGINT ignored
  (`SigIgn: 0x7`), its children inherit it, and the CLI rightly keeps an ignored
  SIGINT ignored. The unit tests now set the terminal's handlers first and the
  e2e children start through a `python -c` wrapper that sets SIGINT's
  disposition and execs the command; the same tests then passed under
  `setsid nohup` (64 unit, 7 e2e).
- **No fork in a threaded test process.** The pseudo-terminal test used
  `pty.fork()`, which Python 3.13 warns may deadlock in a multi-threaded
  process; it now uses `os.openpty()`, `subprocess.Popen` and `setsid --ctty`
  (util-linux), and no test uses `preexec_fn`.
- **Mosquitto readiness.** The MQTT stop test failed 1 of 3 runs: Docker's port
  proxy accepts a TCP connection before the broker listens, so `mosquitto_broker()`
  now waits for a CONNACK; 8 of 8 runs passed after.
- **e2e coverage.** A repeat signal runs either in a process that ends by a
  signal or after coverage's last record, so it sits inside the `if
  self._signalled:` block that `.coveragerc.e2e` leaves to the unit tier.
- **`crossref` read 0 events** in one 30-s window of a full `check` at
  16:34–16:51 UTC, while two full-catalog runs and the gates loaded this host;
  alone it read 1,000 events in 60 s and in each of two 30-s checks
  (17:00 UTC), its 16.4-MB first answer taking 5.2 s. The final live run (3.2)
  decides it.

## 6. Addendum 2026-10-20: stage 2 (README) done

### 6.1 Where every removed README passage went (plan 2.1)

| Removed passage (old section) | Where the fact is now |
|---|---|
| "Private, instructor-only repository … do not share" (title) | README introduction, rewritten: the repository is public (found public on 2026-10-20; the owner decided to keep it public), with the secret check before every push |
| decision-records pointer, uv requirement, contents list (title, Quick start) | README introduction, "Requirements", "Contents" |
| inclusion rule and `round_rate` (Inclusion rule) | README "Measurements", first paragraph |
| GDELT kept at 0.977 (2026-10-13) and 0.772 (24 rounds) | README "Measurements" (0.772, the decision) and its `gdelt` row; `docs/reference/…sub-threshold-sources.md` §3.3 (both values, added); research record `2026-10-13-18-54-…`, decision table and source sheet (0.977) |
| free-key providers with a keyless route (MBTA V3, TfL, FIRMS) | README "Sources" (group C: `mbta_v3` and `tfl` take the key optionally, their Key column says `optional`; `firms` reads keyless public files) and "API keys" ("NASA FIRMS needs no key"); API-key page, Table 1 rows 12 and 14 |
| candidates (group D) and the 7 accepted on 2026-10-19 | README "Sources" (definition of D); API-key page, Table 1 ("Accepted 2026-10-19" in each row) |
| ENTSO-E token and 0.010 events/s | README "Measurements" `entsoe` row; sub-threshold page §2.3 |
| streams excluded below 1 event/s (Nostr … zKillboard) | sub-threshold page §3.1 |
| Lasair, Fink, Bitstamp, npm, Digitraffic trains, GFW, ndbc evidence (removals list and "Sources Below 1 Event/s" table) | README "Measurements" rows (measurement and one-line reason); sub-threshold page §2.1–§2.8 |
| Bytewax additions and AirNow, Yahoo Finance, GitHub REST not added | README "Sources" (the six sources are in it); sub-threshold page §3.2 (AirNow); research record `2026-10-19-02-46-…` (Yahoo Finance, GitHub REST events) |
| Vélib' re-added on 2026-10-17 (0.983 → 4.4) | sub-threshold page §3.3 (added); research record `2026-10-13-18-54-…`, table at line 976 and the finding after it |
| group E paragraph (kept, tested, run only when named) | README "Sources" (definition of E) and the group E recipe; AGENTS.md |
| "Sources (65)" table and "Reference links" table | README "Sources": one 73-row table with the same documentation, terms and sign-up links, checked against the catalog |
| "Sampling results" text and table | README "Measurements" (text kept; table extended to 73 rows) |
| examples block (Running the consumers) | README "Recipes" (run on 2026-10-20) and "Options and defaults" |
| configuration prose, settings name list, held-keys prose | README "Configuration": where values come from, API keys, Settings table (defaults), Held keys table; the Binance probe's trade/withdraw check is in the API-key page §13 |
| "Branch protection is not available …" (Known behaviour) | research record `2026-10-13-18-54-…`, line 1941 (same statement) |
| link check of 2026-10-19 23:18 UTC and the earlier ones | README "Decision records", link check paragraph (new check, earlier results summarised) |

Inconsistency found in a historical record (not rewritten): the research
record `2026-10-13-18-54-…` gives Vélib's 15-round median as 4.396 events/s in
its table (line 976) and as "3.3" in a later summary line (1733); the README
and the sub-threshold page use the table's value.

### 6.2 Repository found public, and the audit

The link check found `github.com/mavasbel-itam/stream-consumers` answering
HTTP 200 without signing in; the API answered `private: false`,
`visibility: public` (2026-10-20 ~17:06 UTC). The README's link check of
2026-10-19 23:18 UTC had recorded 404. The organisation audit log is not
available (HTTP 404) and the events API lists one `PublicEvent`, at
2026-10-13 06:34:58 UTC, so when the visibility changed is not established.
The owner decided to keep the repository public. Audit of everything published
and everything local (`/tmp/opencode/audit/audit.py`, then made permanent as
`tests/live/test_secrets_live.py`):

- every object git holds: 671 blobs, 315 trees, 36 commits, 34 unreachable
  objects, all refs and reflogs, plus the pull request ref `refs/pull/1/head`
  fetched from GitHub; GitHub's activity log shows only fast-forward pushes, and
  every commit it lists is in local `main`;
- GitHub: 1 branch, 0 tags, 0 releases, 1 pull request (body, comments,
  reviews, commits), 0 Actions secrets or variables, 0 deployments, no wiki or
  Pages, 20 Actions runs (all logs downloaded) and 2 artifacts (downloaded);
- result: none of the 41 secret values of `.env` (every credential, held key
  and the output password that has a value), nor any 12-character piece of one,
  in any of them; no private key, AWS, GitHub, Slack, Google or Stripe token,
  or JSON Web Token; the credential-like assignments are code, empty template
  entries and the fixed password of the disposable test containers on
  127.0.0.1;
- personal data: the owner's institutional e-mail address in two lines of
  `docs/research/2026-10-12-22-41-…` (masked as `<masked>` with an addendum;
  the earlier commits still hold it), and the owner's personal e-mail address
  as the author and committer of every commit. Removing them from published history
  would need a history rewrite and a forced push, which only the owner can
  decide.

### 6.3 Found by the sampling recipe and fixed test-first (commit 2)

The recipe's second segment (`--reports data/reports/sampling-20261020/segment-2
--continue-from data/reports/sampling-20261020`), stopped with `kill`, advised
`resume with --continue-from data/reports/sampling-20261020/segment-2`: that
directory holds only the second segment's rounds, so resuming from it would
have dropped round 1 (`--continue-from` reads `round-*.json` recursively). The
message now names the directory that holds every round: the reports directory
of a first segment, the `--continue-from` directory when the new reports are
inside it, and otherwise it says the rounds are in two places and must be put
under one directory. Tests: a unit test for both cases, and the e2e sampling
test now continues once inside and once outside the first segment.

### 6.4 Final live run and measurements on the final code (3.2, 1.16)

| Run (2026-10-20, UTC) | Code | Result |
|---|---|---|
| `check` of the 65 active sources, 17:53:53–18:11:54 | `8dd4e60` (the final code differs only in `sample`'s resume message) | 64 delivered or key pending; `eth_logs` no events in its 30-s window, then 3,534 events in a 60-s `consume` at 18:14 (provider behaviour already in "Known behaviour") |
| live source test, 73 sources, 18:48–19:04 | final | 73 passed |
| live key suite and `keys`, 18:29–18:31 | final | 35 passed, 2 skipped (Fink, Lasair: no credentials); `keys` exit 0 |
| secret check (`test_secrets_live.py`) | final | 3 passed |
| all 65 active sources stopped with SIGTERM at once after 8 s, 19:05 | final | 65 of 65 exit 143 with their report; 0.31–1.46 s, median 1.01 s |

The 1.2 table on the final code (finished 19:06 UTC):

|---|---|---|---|---|
| `consume wikimedia --seconds 30 --out file.jsonl` | Ctrl+C at 5 s | 0.11 s | 130 | no traceback; run report `stopped by SIGINT after 4.563 of 30 s`, events=146; 146 lines in the file |
| `consume coinbase --format json --out file.json` | Ctrl+C at 4 s | 0.23 s | 130 | no traceback; report events=34; array closed, parses: 34 objects |
| `consume coinbase --out sqlite:…` | Ctrl+C at 4 s | 0.27 s | 130 | no traceback; report events=31; 31 rows |
| `check wikimedia coinbase bitso --seconds 30` | Ctrl+C at 8 s | 1.14 s | 130 | no traceback; summary `3 sources, 3 delivered or key pending, 0 failed`; `check-*.json` with 3 sources |
| `profile coinbase --seconds 30` | Ctrl+C at 8 s | 0.33 s | 130 | no traceback; sample file 38 lines; `profiles-*.json` written (38 events inspected) |
| `sample … --rounds 3 --interval 20 --window 5` | Ctrl+C at 8 s | 0.13 s | 130 | no traceback; ['round-01'] kept; `stopped by SIGINT: 1 of 3 rounds recorded; a round cut short is not recorded; resume with --continue-from <dir>` |
| `uv run stream-consumers consume wikimedia` | Ctrl+C at 6 s | 0.16 s | 130 | no traceback; run report present, events=186 |
| `consume wikimedia`, 3 presses 1 s apart | Ctrl+C ×3 | 0.13 s | 130 | no traceback; ended after the first press (report events=122); the later presses found no process |
| `consume coinbase --format json --out file.json` | `kill -TERM` at 4 s | 0.23 s | 143 | no traceback; array closed, parses: 12 objects = report events 12 |
| `consume coinbase --out sqlite:…` | `kill -TERM` at 4 s | 0.23 s | 143 | no traceback; 15 rows = report events 15; the waiting batch was written |
| `consume coinbase --format csv --out file.csv` | `kill -TERM` at 4 s | 0.24 s | 143 | no traceback; 75 rows = report events 75; every row [20] columns |
| `consume …` started with `&` from a non-interactive shell | `kill -INT`, then `kill -TERM` | 0.12 s after TERM | 143 | SIGINT ignored (still running 2 s later: True); SIGTERM: report `stopped by SIGTERM after 5.615 of 30 s`; no traceback |


The README recipes were run between 17:21 and 18:46 UTC from the main
checkout's root with `UV_PROJECT` pointing at this work's checkout, so each
command ran exactly as written, with the main checkout's `.env`, on the code of
this work; the sampling recipe was run again from 18:14 on the final code after
the resume-message fix (6.3). The output examples of "Outputs" are kept from
their runs of 2026-10-20 00:53–02:05 UTC: the output adapters did not change
since, except that standard output is now handed on per event.

### 6.5 Guards (2.3) shown failing on broken copies

`tests/unit/test_documentation.py` has 18 tests. Each of 15 broken copies of the
README was caught by the guard written for it: a setting's default changed; a
setting row, a held-key row, a test variable or a measurement row removed; a
source listed twice, with the wrong group, or with a changed terms link; an old
group name; a broken `#anchor`; a `docs/` page not linked; the stop
announcement reworded in the prose; the `uv run … || break` advice removed;
exit code 141 removed; the `unknown` key state removed.
