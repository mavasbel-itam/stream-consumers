# stream-consumers — provisional release while the samplings finish

| | |
|---|---|
| Date | 2026-10-19 03:07 UTC (2026-10-18 21:07 CDMX) |
| Approved by | Owner, 2026-10-19 ~03:05 UTC: "continue the measurement in the background but assume they will pass so we continue building and finishing" |
| Repository | `/home/mavasbel/Dev/repos/ITAM/stream-consumers` (GitHub `non-relational-dbs/stream-consumers`, branch `main`) |
| Starting point | local `main` and `origin/main` at `bc3a7fb`; dev checkout `stream-consumers-dev` at `75a87fd` (`7d9012a` held keys → `199e43a` early stop → `2dda597` GDELT note → `66c07da` Bitso → `7c93797` seven Bytewax sources → `75a87fd` Binance) |
| Key page | `docs/reference/2026-10-17-15-13-api-key-gated-sources.md` (sections 1–14) |
| Research record | `docs/research/2026-10-19-02-46-bytewax-real-time-list-screening.md` |

## 1. Decision

The samplings keep running untouched in the background. The release is built
now on the assumption that every source still being measured passes (median
≥ 1 event/s). Each result that is not yet certain is published as
**provisional**, with its round count and the UTC hours its rounds cover. When
the samplings end, any source whose certain result is below 1 event/s is
removed in a follow-up commit and the provisional labels become final.

## 2. State at 03:07 UTC

### 2.1 Certain results (24-round rule, early stop)

| Source | Run | Rounds | Median (events/s) | Result |
|---|---|---|---|---|
| `cta_bus` | `sampling-20261017` | 24/24 | 17.379 | passes |
| `cta_train` | `sampling-keyed-20261018` | 22/24 | 1.424 | passes |
| `nta` | `sampling-nta-20261018` | 21/24 | 11.474 | passes |
| `mta_bustime` | `sampling-mta_bustime-20261018` | 20/24 | 50.567 | passes |
| `wmata` | `sampling-wmata-20261018` | 20/24 | 47.679 | passes |
| `mbta_v3` (key) | `sampling-mbta_v3-20261018` | 20/24 | 55.690 | passes |
| `opensky` (key) | `sampling-opensky-20261018` | 12/24 | 30.477 | passes |

### 2.2 Still being measured (assumed to pass)

| Source | Run (checkout) | Rounds | ≥ 1/s | Median | Expected certain (if rounds keep passing) |
|---|---|---|---|---|---|
| `tfl` (key, 150 s) | `sampling-tfl-20261018` (main) | 12 | 11 | 2.474 | ~03:53 UTC |
| `mastodon` (social.vivaldi.net) | `sampling-mastodon-vivaldi-20261018` (main) | 12 | 12 | 2.425 | ~03:37 UTC |
| `aisstream` | `sampling-aisstream-20261018` (main) | 10 | 10 | 74.209 | ~04:20 UTC |
| `mastodon` (mastodon.world, 2nd option) | `sampling-mastodon-world-20261018` (run) | 5 | 5 | 1.833 | ~10:54 UTC |
| `mbta_v3`, `sensorcomm`, `firms`, `tfl` (D2 fixes) | `sampling-d2-20261018` (run) | 5 | 5 / 4 / 3 / 3 | 46.066 / 58.733 / 3.727 / 1.682 | ~09:35–11:35 UTC |
| 7 Bytewax sources | `sampling-bytewax-20261019` (new) | 1 | 6 of 7 | round 1: ogn 82.4, sharpe 40.442, citibike 23.759, coinpaprika 6.66, ukflood 4.9, blockchain 1.795, **ndbc 0.268** | round 13 at the earliest, ~15:00 UTC |

The early-stop watcher (`stream-early-stop.timer`, every 10 min) stops each
run once every source in it is certain.

### 2.3 Finding: false zeros for `firms` and `sensorcomm`

The D2 run's zero rounds (`firms` 01:35 and 02:35 UTC, `sensorcomm` 02:35 UTC,
status `no-events`, 150 s) coincide with a slow link: timed at 02:56 UTC,
`J1_VIIRS_C2_Global_24h.csv` 9.11 MB took 125.5 s, `data.json` 8.49 MB took
112.4 s (0.07–0.09 MB/s). A 150-s window can end before the first complete
file, and so before the first event.

## 3. Constraints

- The runs on the main checkout (`aisstream`, `mastodon-vivaldi`, `opensky`,
  `tfl`) execute that checkout's code: no file in
  `/home/mavasbel/Dev/repos/ITAM/stream-consumers` other than `data/` changes
  until they stop. The `run`, `verdict` and `new` checkouts are not touched
  while their units run.
- Every key stays in `stream-consumers/.env`; no key value appears in any
  commit, document or log written by this work.
- Only `main` in stream-consumers; only this worktree's own files are staged in
  the course repository (the worktree holds other sessions' uncommitted edits).

## 4. Steps

| # | Step | Where | Done when |
|---|---|---|---|
| 1 | Leave every sampling running | all units | units untouched |
| 2 | Move the measured keyed sources from candidate (D) to accepted: `cta_bus`, `cta_train`, `mta_bustime`, `nta`, `wmata`, `mastodon` → group C (free key); `aisstream` → group B (project document); `entsoe` stays candidate (no key) | dev | descriptors and tests updated |
| 3 | Mastodon default instance → `social.vivaldi.net` (decision D1 = A), with provider, endpoint, terms and sign-up links of that instance; mastodon.world documented as the measured second option | dev | `check mastodon` ok with the stored token |
| 4 | Measure the concurrent download time of all FIRMS files and the Sensor.Community file, and set each source's `min_window_s` from it (with margin) | dev | window values backed by a recorded timing |
| 5 | README: inclusion rule, groups and counts (67 sources), results table with every median labelled certain or provisional (rounds, UTC hours covered), Mastodon instance, window list | dev | README consistent with the code |
| 6 | Checks: unit + component 100 % coverage; 3 clean e2e runs; live run of every source (`check --all`); live key suite; `keys` exit 0; search for every `.env` value in the tree and history | dev | all pass |
| 7 | Commit; push the dev commit to `origin/main` (fast-forward from `bc3a7fb`) without touching the local main checkout; GitHub Actions green | GitHub | CI run passes |
| 8 | After the four main-checkout runs stop (~04:20 UTC): fast-forward local `main` | main | `main` = `origin/main` |
| 9 | Key page (results, groups, Mastodon instance, change log) and research record (provisional status of the seven) | course worktree | committed |
| 10 | Refreshed student-catalog plan (from the accepted list) for the owner's approval | course worktree | presented |
| 11 | Reconcile when the samplings end: `verdict` per run; remove every source below 1 event/s in a follow-up commit; re-run step 6; push; CI; labels → final; remove the `run`, `verdict`, `new` checkouts and the early-stop timer; final key page and research record | all | every result certain and published |

A smart note returns step 11 when the last run's reports show it stopped.

## 5. Risks

| Risk | Handling |
|---|---|
| A provisional source fails at the end | Removed in step 11 (most at risk: `ndbc`, round 1 0.268/s; D2 `tfl`, 3 of 5 rounds ≥ 1/s) |
| Link slowness (WireGuard tunnel, owner-approved) causes failed rounds | Failed rounds count 0; step 4 lengthens the windows of the large-file sources |
| A live check fails because of the link, not the source | Re-checked once; a reproducible failure is reported, not skipped |
