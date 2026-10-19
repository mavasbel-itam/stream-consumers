# Sources Below 1 Event/s: Measurement Evidence & Low-Rate Catalog

Written 2026-10-19 18:27 UTC by the streams session (`ses_ecd14c7d…`).

This document records the measurement evidence, bottleneck analysis, and architectural details for every public data stream evaluated that falls below the repository's 1 event/s inclusion threshold (`policy.MINIMUM_RATE = 1.0`).

Per maintainer decision (2026-10-19), all 8 sources that were implemented, tested, and measured are **retained in code** under `Group.LOW_RATE` (`group = Group.LOW_RATE` / `"low_rate"`), covered by 100% unit and component test coverage, full decoding, and live authentication probes where applicable. They are documented in this dedicated reference rather than the main active catalog table.

---

## 1. Summary of Implemented Low-Rate Sources (8 Sources in `Group.LOW_RATE`)

| id | Name | Provider | Protocol | Transport | Delivery | Measured Rate | Bottleneck / Limiting Factor |
|---|---|---|---|---|---|---:|---|
| `bitstamp` | Bitstamp live trades (BTC/USD, ETH/USD) | Bitstamp Ltd. | WebSocket JSON | `websocket` | push | **0.515 events/s** (median, 24 rounds) | Low trade frequency across BTC/USD and ETH/USD pairs during quiet market windows (min 0.150, max 3.555 events/s) |
| `dt_rail_trains` | Digitraffic Finland train tracking & timetables | Fintraffic / Digitraffic | MQTT JSON | `mqtt` | push | **0.865 events/s** (median, 24 rounds) | Timetable actuals and progress updates arrive only as trains hit track checkpoints (min 0.200, max 1.246 events/s) |
| `entsoe` | ENTSO-E Transparency Platform actual generation | ENTSO-E | REST XML (IEC 62325) | `http` | poll | **0.010 events/s** (DE/FR/ES); ceiling **~0.33 events/s** | 15-minute publication resolution per area/type; querying all 59 reporting areas takes ~380 s per poll cycle |
| `fink` | Fink — Rubin Observatory LSST & ZTF alert stream | CNRS/IN2P3 and partners | Kafka / Avro (schema in key) | `kafka` | push | **0 events/s** (no alerts since 2026-07-14) | Upstream LSST alerts dormant; broker stream produces no live messages |
| `gfw` | Global Fishing Watch events API | Global Fishing Watch | REST JSON | `http` | poll | **0 events/s** (0 growth over 18 hourly rounds) | AIS event processing publishes events multiple days after occurrence; poll windows detect zero intra-hour event growth |
| `lasair` | Lasair — Rubin Observatory LSST alerts | Universities of Edinburgh and Belfast | Kafka JSON | `kafka` | push | **0 events/s** (no detections since 2026-07-14) | Upstream LSST alert hiatus; filter topic receives no events |
| `ndbc` | NOAA NDBC latest observations across all buoys | NOAA NDBC | HTTP plain text | `http` | poll | **0.268 events/s** (median, 3 rounds) | Station observations file (`latest_obs.txt`) updates irregularly at 10–15 minute intervals |
| `npm` | npm public registry `_changes` feed | npm / GitHub | HTTP chunked JSON | `http` | poll | **0.790 events/s** (median, 24 rounds) | CouchDB sequence changes average < 1 event/s across standard daily release intervals (min 0.259, max 1.616 events/s) |

---

## 2. Detailed Per-Source Analysis

### 2.1 `bitstamp` — Bitstamp Live Trades

- **Endpoint:** `wss://ws.bitstamp.net`
- **Subscription:** Channel `live_trades_btcusd` and `live_trades_ethusd`.
- **Sampling Evidence:** Evaluated in the 24-hour sampling run of 2026-10-17/18 (`data/reports/sampling-20261017/`). Across 24 hourly 60-second windows:
  - Median rate: **0.515 events/s**.
  - Minimum rate: **0.150 events/s**.
  - Maximum rate: **3.555 events/s**.
  - Rounds meeting ≥ 1 event/s: 4 of 24 rounds.
- **Root Cause:** Bitstamp's trade volume on individual currency pairs during off-peak hours drops well below 1 trade per second. Unlike Coinbase or Binance which aggregate broader books or higher liquidity, Bitstamp's two major pairs did not sustain the required threshold.
- **Reproduction:**
  ```bash
  uv run stream-consumers check bitstamp --seconds 60
  uv run stream-consumers consume bitstamp --max-events 50
  ```

### 2.2 `dt_rail_trains` — Digitraffic Finland Train Timetables

- **Endpoint:** `wss://rata.digitraffic.fi:443/mqtt`
- **Topics:** `trains/#`
- **Sampling Evidence:** Evaluated in the 24-hour sampling run of 2026-10-17/18 (`data/reports/sampling-20261017/`). Across 24 hourly 60-second windows:
  - Median rate: **0.865 events/s**.
  - Minimum rate: **0.200 events/s**.
  - Maximum rate: **1.246 events/s**.
  - Rounds meeting ≥ 1 event/s: 7 of 24 rounds.
- **Root Cause:** In Finland railway operations, train timetable actuals (station arrival/departure estimates and checkpoint passes) are generated discrete event messages that occur only as trains cross specific physical sensors. Outside morning/evening peak commuting hours, message frequency falls to ~0.2–0.5 events/s.
- **Reproduction:**
  ```bash
  uv run stream-consumers check dt_rail_trains --seconds 60
  uv run stream-consumers consume dt_rail_trains --max-events 50
  ```

### 2.3 `entsoe` — ENTSO-E Transparency Platform Actual Generation

- **Endpoint:** `https://web-api.tp.entsoe.eu/api`
- **Credential:** `ENTSOE_TOKEN` (required).
- **Settings:** `ENTSOE_AREAS` (default `10Y1001A1001A83F,10YFR-RTE------C,10YES-REE------0`, corresponding to Germany, France, and Spain).
- **Measurement Probes (2026-10-19):**
  1. *Default 3-area probe (10 minutes, 600 s):* Received 744 points in the initial baseline answer, then **0.010 events/s** of new data points.
  2. *Full 59-reporting-area probe (10 minutes, 600 s):* Received 7,372 baseline points across all reporting European bidding zones. A single poll request across all 59 areas took **380 seconds** (~6.3 minutes), exceeding the 5-minute poll interval; thus no second round completed and no arrival rate could be computed.
  3. *Global European Ceiling Calculation:* A direct retrospective query across all 100 ENTSO-E areas over the prior 6 hours returned 7,226 distinct generation points. Dividing 7,226 points across 21,600 seconds gives a theoretical absolute maximum of **~0.33 events/s** for the entire European continent (even without deducting overlapping bidding zones).
- **Root Cause:** ENTSO-E publishes electricity generation aggregated at 15-minute intervals per area and production type (IEC 62325 standard). It is fundamentally a slow periodic reporting system rather than a high-frequency real-time stream.
- **Reproduction:**
  ```bash
  uv run stream-consumers check entsoe --seconds 600
  ```

### 2.4 `fink` — Fink Alert Broker (LSST / ZTF)

- **Endpoint:** `kafka://<FINK_KAFKA_SERVERS>/<FINK_TOPICS>`
- **Credentials:** `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID`.
- **Measurement Evidence:** Verified 2026-10-18 and 2026-10-19. Upstream Vera C. Rubin Observatory Legacy Survey of Space and Time (LSST) alert generation has been paused since 2026-07-14.
- **Root Cause:** With upstream alert ingestion inactive, Fink's Kafka topics produce 0 messages/s. The consumer architecture (aiokafka + Avro decoder parsing writer schema from message key) remains fully implemented and tested.
- **Reproduction:**
  ```bash
  uv run stream-consumers check fink --seconds 60
  ```

### 2.5 `gfw` — Global Fishing Watch Events API

- **Endpoint:** `https://gateway.api.globalfishingwatch.org/v3/events`
- **Credential:** `GFW_API_TOKEN`.
- **Sampling Evidence:** Monitored over 18 hourly snapshots on 2026-10-18 (03:24–21:24 UTC) tracking four datasets (`fishing`, `encounters`, `loitering`, `port-visits`) over a fixed historical window. The dataset counts did not change by a single record across all 18 readings.
- **Root Cause:** Global Fishing Watch generates events via batch processing on raw satellite AIS data with a multi-day latency (e.g. events for 2026-10-14 were the latest available when probed on 2026-10-18). Live polling detects 0 event arrivals within streaming windows.
- **Reproduction:**
  ```bash
  uv run stream-consumers check gfw --seconds 60
  ```

### 2.6 `lasair` — Lasair Alert Broker (LSST)

- **Endpoint:** `kafka://lasair-lsst-kafka.lsst.ac.uk:9092/<LASAIR_KAFKA_TOPIC>`
- **Credential:** `LASAIR_API_TOKEN` (REST query probe).
- **Measurement Evidence:** Verified 2026-10-18. Lasair's latest recorded object detection was `2026-07-14 10:03 UTC`. Zero alerts generated in the preceding 90 days.
- **Root Cause:** Identical to Fink; dormant due to lack of upstream telescope alerts.
- **Reproduction:**
  ```bash
  uv run stream-consumers check lasair --seconds 60
  ```

### 2.7 `ndbc` — NOAA National Data Buoy Center Latest Observations

- **Endpoint:** `https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt`
- **Sampling Evidence:** Measured in 3 rounds on 2026-10-19 (`bytewax-20261019` run):
  - Round 1: 0.268 events/s.
  - Round 2: 0.569 events/s.
  - Round 3: 0.045 events/s.
  - Overall median: **0.268 events/s**.
- **Root Cause:** NOAA regenerates `latest_obs.txt` intermittently (typically 10 to 15 minutes apart). Consecutive polls spaced 2 to 5 minutes apart see identical file contents, resulting in zero new records between polls.
- **Reproduction:**
  ```bash
  uv run stream-consumers check ndbc --seconds 300
  ```

### 2.8 `npm` — npm Registry Replication `_changes`

- **Endpoint:** `https://replicate.npmjs.com/registry/_changes`
- **Sampling Evidence:** Evaluated in the 24-hour sampling run of 2026-10-17/18 (`data/reports/sampling-20261017/`). Across 24 hourly 60-second windows:
  - Median rate: **0.790 events/s**.
  - Minimum rate: **0.259 events/s**.
  - Maximum rate: **1.616 events/s**.
  - Rounds meeting ≥ 1 event/s: 6 of 24 rounds.
- **Root Cause:** While npm has millions of packages, updates published per second fluctuate around ~0.5–0.8/s for prolonged spans throughout the day, only exceeding 1 event/s during concentrated business hours in US/European time zones.
- **Reproduction:**
  ```bash
  uv run stream-consumers check npm --seconds 60
  ```

---

## 3. Pre-Implementation Candidates Screened & Excluded (< 1 event/s)

During initial research surveys (`docs/research/2026-10-12-21-37-public-data-streams-survey.md` and `docs/research/2026-10-19-02-46-bytewax-real-time-list-screening-record.md`), five additional candidate streams were screened and rejected prior to adapter implementation because their published metrics or rate limits precluded reaching 1 event/s:

1. **EPA AirNow:**
   - *Format:* Hourly national monitoring observation file (`HourlyData_YYYYMMDDHH.dat`).
   - *Volume:* Lists 4,415 monitoring sites across the US, but only 1,980 sites reported during peak hour 2026-10-18 22:00 UTC. Dividing 1,980 observations by 3,600 seconds yields **~0.55 events/s**.
2. **CoinCheck Public Trades:**
   - *Format:* Polled REST `/api/trades`.
   - *Volume:* Measured 2026-10-18: 30 trades over a 600-second window across BTC/JPY = **0.05 events/s**.
3. **DexPaprika Decentralized Swaps:**
   - *Format:* Polled REST API.
   - *Volume:* Evaluated 2026-10-19: 14 swaps over 360 seconds = **0.039 events/s**.
4. **USGS Real-Time Earthquakes (M1.0+):**
   - *Format:* GeoJSON / GeoRSS summary feeds.
   - *Volume:* ~100–300 global earthquakes per day = **~0.001–0.003 events/s**. (USGS instantaneous streamflow river gauges `usgs_water` was implemented instead at 22 events/s).
5. **Transport for NSW (Australia):**
   - *Format:* GTFS-Realtime vehicle positions.
   - *Volume:* Free tier API quota is strictly capped at 5 requests per minute (0.083 req/s) with a burst limit of 10 requests per 15 seconds (**0.69 req/s**), structurally capping throughput below 1 event/s.

---

## 4. Architectural Integration & Verification Guarantees

In accordance with repository architecture rules:
1. **Hexagonal Ports & Adapters:** Each source implements `BaseSourceFactory` and builds concrete `EventSourcePort` instances (`HttpPollSource`, `WebSocketSource`, `KafkaSource`, `MqttSource`) with dedicated decoders (`JsonDecoder`, `AvroSchemaInKeyDecoder`, plain text tabular decoders).
2. **Strict Test Coverage:** Unit and component tests provide 100% measured statement and branch coverage across all 8 source adapters and decoders (`tests/unit/test_sources.py`, `tests/component/test_custom_sources.py`, `tests/component/test_keyed_sources.py`).
3. **Live Authentication Verification:** All credentials and held tokens (`ENTSOE_TOKEN`, `GFW_API_TOKEN`, `LASAIR_API_TOKEN`) have corresponding probes in `tests/live/test_keys_live.py` verifying that stored keys are accepted while invalid or damaged copies are rejected.
