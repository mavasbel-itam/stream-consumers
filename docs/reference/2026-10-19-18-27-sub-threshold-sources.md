# Sources below 1 event/s

Status page, updated in place (change log at the end). Created 2026-10-19
18:27 UTC; corrected 2026-10-19 (see the change log).

The inclusion rule is a median measured rate of at least 1 event/s
(`policy.MINIMUM_RATE = 1.0`, README "Measurements"). This page holds:

1. the 8 sources of **group E** (`Group.LOW_RATE`, value `"E"`): built,
   measured below 1 event/s and kept in the code;
2. the evidence behind each of them;
3. every other stream measured or screened below 1 event/s that was never
   built, with the record it comes from, and the two built sources outside
   group E that were measured below 1 event/s at some point.

Every number below is copied from a report under the git-ignored `data/`
directory, from the source's descriptor, or from a research record in
`docs/research/`; the location is given next to it.

## 1. Group E in the code

- **Kept and tested like every other source.** Each has its module in
  `src/stream_consumers/adapters/outbound/providers/sources/`, a row in
  `tests/unit/test_sources.py::EXPECTED` (fink has no captured message: its
  Kafka transport and Avro decoder are tested against a local broker in the
  component tier, its factory in the unit tier), and is inside the 100 %
  coverage gate.
- **Left out of bulk commands.** With no source id, `check`, `sample` and
  `profile` run the sources whose group is active (`Group.active`, false only
  for group E; `ListService.default_sources`). Naming a group E source runs it:
  `uv run stream-consumers check ndbc --seconds 960`. `consume` always names
  its source. `list` prints all 73 sources with `"group": "E"` for these 8.
- **Keys.** Every credential a group E source reads has a live probe in
  `tests/live/test_keys_live.py` (stored value accepted, damaged copy refused,
  missing value refused). `ENTSOE_TOKEN` and `GFW_API_TOKEN` are set;
  `LASAIR_KAFKA_TOPIC`, `FINK_KAFKA_SERVERS` and `FINK_GROUP_ID` are not, so
  their probes are skipped. The Lasair REST API token `LASAIR_API_TOKEN` is a
  held key: the `lasair` source reads only the Kafka topic.

| id | Source (descriptor) | Transport / delivery | Key | Measured | Record |
|---|---|---|---|---|---|
| `bitstamp` | Bitstamp live trades | websocket / push | — | median **0.515** events/s | `data/reports/sampling-20261017/` |
| `dt_rail_trains` | Digitraffic Finland train timetables/actuals | mqtt / push | — | median **0.865** | `data/reports/sampling-20261017/` |
| `entsoe` | ENTSO-E Transparency Platform — actual electricity generation per production type | http / poll | `ENTSOE_TOKEN` (required, set) | **0.010** (default areas, 600 s) | `data/reports/entsoe-20261019/` |
| `fink` | Fink — Rubin Observatory LSST and ZTF alert livestream | kafka / push | `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` (required, not set) | not measured; no alerts to deliver | README, decision of 2026-10-18 |
| `gfw` | Global Fishing Watch events API — fishing, encounter, loitering and port-visit events | http / poll | `GFW_API_TOKEN` (required, set) | **0** growth in 22 hourly readings | `data/gfw-growth-20261018/snapshots.jsonl` |
| `lasair` | Lasair — Rubin Observatory LSST alerts that pass your saved filter | kafka / push | `LASAIR_KAFKA_TOPIC` (required, not set) | not measured; no alerts to deliver | README, decision of 2026-10-18 |
| `ndbc` | NOAA National Data Buoy Center — latest observation of every buoy and coastal station | http / poll | — | median **0.268** (3 rounds) | `data/reports/sampling-bytewax-20261019/` |
| `npm` | npm registry replication changes | http / poll | — | median **0.790** | `data/reports/sampling-20261017/` |

## 2. Evidence per source

Rates of polled sources count records that are new or changed between the
first and the last poll of a window, divided by the time between them
(README "How rates are measured").

### 2.1 `bitstamp`

- Subscribes to `live_trades_btcusd`, `live_trades_ethusd`,
  `live_trades_xrpusd`, `live_trades_btceur`, `live_trades_solusd` on
  `wss://ws.bitstamp.net`; one event per trade.
- All-source sampling of 2026-10-17/18 (24 hourly rounds, 60-s windows):
  24/24 rounds, 3 at ≥ 1 event/s, minimum 0.150, maximum 3.555, median
  **0.515** events/s — `uv run stream-consumers verdict data/reports/sampling-20261017 bitstamp --planned 24` → `fails`.
- Removed from the catalog 2026-10-18 (commit `908953b`), group E since
  2026-10-19.

### 2.2 `dt_rail_trains`

- MQTT topic `trains/#` on `wss://rata.digitraffic.fi:443/mqtt`; one event per
  message.
- Same run: 24/24 rounds, 7 at ≥ 1 event/s, minimum 0.200, maximum 1.246,
  median **0.865** events/s → `fails`.
- Removed 2026-10-18 (`908953b`), group E since 2026-10-19.

### 2.3 `entsoe`

- Document A75 (actual generation per production type), process A16, last
  6 hours, one request per area every 5 minutes (descriptor notes). Default
  areas: Germany `10Y1001A1001A83F`, France `10YFR-RTE------C`, Spain
  `10YES-REE------0` (`ENTSOE_AREAS`).
- Token check 2026-10-19 (key status page, change log): with the token the
  three areas answered HTTP 200 with data; a damaged copy and no token were
  refused with HTTP 401.
- `check` with the default areas, 2026-10-19 15:25:40–15:35:40 UTC, 600 s:
  744 events, rate **0.010** events/s (`check/check-20261019T153540Z.json`).
  The 744 events are the first answer; the rate counts only points that are
  new or changed afterwards.
- `check` with all 59 areas that returned data (`all59.txt`, set only in
  that process's environment), 600 s: 7,372 events, rate `unmeasured`
  (`check59/check-20261019T153554Z.json`): one round of 59 requests took
  about 380 s, so the window held no second complete poll.
- Upper bound (`ceiling.py`, `ceiling.json`, run at 15:21–15:23 UTC): the 100
  area codes listed in entsoe-py's `mappings.py`, asked for the window
  10:00–16:00 UTC, returned 7,226 points, 59 areas with data; resolutions
  PT15M (45 areas), PT30M (5) and PT60M (9). Even if every point were new
  and only the 5 h 21 min up to the query counted, that is 0.38 points/s;
  over the full 6-hour window, 0.33 points/s.

### 2.4 `fink`

- Kafka topics of the Fink broker (`FINK_TOPICS`, default
  `fink_extragalactic_lt20mag_candidate_lsst`); credentials come from the
  Fink subscription form and are not configured.
- Removed 2026-10-18 (`908953b`): Fink's last alert night was 2026-07-14
  (README; key status page, change log 2026-10-18 05:10). Group E since
  2026-10-19.

### 2.5 `gfw`

- Polls the events API every 15 minutes for the last 7 days, 5 pages of 100
  (`GFW_LOOKBACK_DAYS`, `GFW_PAGES`); an event is an event id not seen before.
- Totals of the four datasets (fishing, encounters, loitering, port visits)
  over the fixed range 2026-09-01 – 2026-11-01, read hourly: 22 readings from
  2026-10-18 03:24 to 2026-10-19 00:24 UTC, the same four totals in every one
  (`data/gfw-growth-20261018/snapshots.jsonl`). The removal decision of
  2026-10-18 used the first 18 (03:24–21:24 UTC).
- When read on 2026-10-18 the latest day with events was 2026-10-14 (key
  status page, Table 1). Removed 2026-10-18 (`908953b`), group E since
  2026-10-19.

### 2.6 `lasair`

- Kafka topic of a saved Lasair filter (`LASAIR_KAFKA_TOPIC`) on
  `lasair-lsst-kafka.lsst.ac.uk:9092`; no topic is configured.
- Live check of the probe, 2026-10-19: subscribing to an invented topic is
  refused by the broker with `TopicAuthorizationFailedError` in 1.8 s.
- Removed 2026-10-18 (`908953b`): latest Lasair detection 2026-07-14 10:03 UTC,
  0 objects in the last 30 days (README; key status page, section 4). Group E
  since 2026-10-19.

### 2.7 `ndbc`

- Polls `latest_obs.txt` every 120 s; an event is a station whose observation
  time changed; windows of at least 960 s (descriptor). NDBC rewrote the file
  at 00:35:51, 00:50:42, 00:55:50, 01:40:26 and 01:50:25 UTC on 2026-10-19
  (Last-Modified, descriptor notes).
- Bytewax sampling run, stopped early on 2026-10-19 05:38 UTC: rounds of
  960 s started at 02:45:10, 03:45:10 and 04:45:10 UTC gave 0.268, 0.569 and 0.045 events/s,
  median **0.268** (`verdict … ndbc` → `open` on 3 of 24 rounds; below
  1 event/s on every round).
- Moved to group E 2026-10-19.

### 2.8 `npm`

- Follows `https://replicate.npmjs.com/registry/_changes` every 5 s; the feed
  returns each changed package once per request, so several updates of one
  package between polls count once (descriptor notes).
- All-source sampling of 2026-10-17/18: 24/24 rounds, 9 at ≥ 1 event/s,
  minimum 0.259, maximum 1.616, median **0.790** events/s → `fails`.
- Removed 2026-10-18 (`908953b`), group E since 2026-10-19.

## 3. Streams below 1 event/s that were never built

### 3.1 First survey, 2026-10-12

From `docs/research/2026-10-12-21-37-public-data-streams-survey.md`, summary
table (3 rounds; "Avg ev/s" and "Min – Max" columns):

| Survey # | Stream | Avg events/s | Min – max | Note |
|---|---|---:|---|---|
| 54 | Nostr public notes (kind 1) across 4 relays | 0.80 | 0.63 – 1.00 | 7 attributes |
| 49 | Stellar Horizon operations stream | 0.17 | 0.17 – 0.17 | |
| 48 | ENA (EMBL-EBI) sequencing runs made public | 0.15 | 0.15 – 0.15 | |
| 51 | Hacker News items (Firebase API) | 0.14 | 0.08 – 0.20 | 6 attributes |
| 47 | PyPI newest releases feed | 0.10 | 0.09 – 0.10 | |
| 50 | MLB Stats API live game feed | 0.06 | 0.05 – 0.06 | 2 of 3 rounds |
| 52 | APRS-IS amateur-radio packet network | 0.00 | 0.00 – 0.00 | not measurable as configured |
| 53 | BitMEX realtime trade/quote/instrument | 0.00 | 0.00 – 0.00 | not measurable as configured |
| 56 | Kystverket open AIS feed | — | — | 0 of 3 rounds usable |
| 61 | zKillboard (EVE Online kills) | — | — | WebSocket answered 403 |

### 3.2 Bytewax list screening, 2026-10-19

From `docs/research/2026-10-19-02-46-bytewax-real-time-list-screening.md`
(entry numbers of that record):

| Entry | Stream | Measured / documented | Verdict in the record |
|---|---|---|---|
| 39 | EPA AirNow (`HourlyAQObs` hourly files) | 4,415 rows per hour (one per site, reported or not); in the file of 2026-10-18 22:00 UTC only 1,980 rows carry a pollutant value: 1,980 / 3,600 s = **0.55** observations/s | qualified at first, then not added (correction recorded in the entry) |
| 43 | USGS earthquake real-time feed | 0 new or updated events in 180.3 s; `all_day.geojson` held 227 events in 24 h = **0.0026**/s | fails |
| 5 | CoinCheck | trades: 3 in 60 s = **0.05**/s (9 fields); order-book diffs 11.9/s but 9 flattened fields (4 semantic) | fails (trades on rate, diffs on attributes) |
| 15 | DexPaprika | 6.21 events/s measured over 60.06 s, but each delivered event costs 1 credit against 10,000 (keyless) or 100,000 (free key) credits per 30 days = **0.004 / 0.039** events/s sustained; 6 fields | fails |
| 30 | Transport for NSW | documented, not measured: 5 requests/s throttle and 60,000 requests/day (**0.69** requests/s on average); vehicles per response not documented | undetermined: needs a free key to measure |

### 3.3 Built sources outside group E measured below 1 event/s at some point

| Source | Group | Below 1 event/s | Now | Where |
|---|---|---|---|---|
| `gdelt` | B (project document) | median 0.977 events/s at the decision of 2026-10-13; median 0.772 over the 24 rounds of `sampling-20261017` (2 rounds at ≥ 1/s, 2026-10-17 21:00 – 2026-10-18 19:44 UTC) | kept by the decision of 2026-10-13: the project document lists it | `docs/research/2026-10-13-18-54-stream-consumers-and-api-keys-record.md` (decision table and source sheet); README "Measurements" |
| `velib` | A (keyless) | median 0.983 events/s from the cross-check rounds available on the morning of 2026-10-13, so it was excluded | re-added on 2026-10-17 (`bc3a7fb`): over all 15 cross-check rounds its median was 4.396 events/s (11 of 15 at ≥ 1/s); 24-round median 4.578 in `sampling-20261017`, passes | same record, recomputed table and finding after it (its later summary line says "3.3"; the table gives 4.396) |

## 4. Change log

| Date (UTC) | Change |
|---|---|
| 2026-10-20 | Section 3.3 added (GDELT and Vélib', moved from the README's former "Inclusion rule" section, which the README rewrite replaced by "Measurements"); the README reference in the introduction follows the new section name. |
| 2026-10-19 23:35 | Source modules moved to `src/stream_consumers/adapters/outbound/providers/sources/` (outbound adapters regrouped by purpose); nothing else changed. |
| 2026-10-19 (correction) | Page rewritten from the records. The first version had: invented figures for CoinCheck ("30 trades in 600 s"), DexPaprika ("14 swaps in 360 s"), USGS ("100–300 earthquakes a day") and Transport for NSW ("5 requests per minute, burst 10 per 15 s", and called it rejected); rounds at ≥ 1 event/s of 4 for `bitstamp` (3) and 6 for `npm` (9); Bitstamp as two pairs (five are subscribed); "no Lasair alerts in 90 days" (the record says 0 objects in 30 days); cause statements without evidence for `dt_rail_trains` and `npm`; and `lasair` reading `LASAIR_API_TOKEN` with a default topic `lasair_all` (the source reads `LASAIR_KAFKA_TOPIC` and has no default). Added: the group value `"E"`, the exclusion of group E from bulk commands, the 22 GFW readings, the ENTSO-E evidence now under `data/reports/entsoe-20261019/`, and section 3.1. |
| 2026-10-19 18:27 | Page created with the 8 group E sources (stream-consumers `e32490d`). |
