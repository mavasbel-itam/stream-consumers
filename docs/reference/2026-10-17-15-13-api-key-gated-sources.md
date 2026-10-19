# API-key-gated stream sources — status and sign-up reference

| | |
|---|---|
| Last updated | 2026-10-19 (group E correction; see the change log) |
| Repository | `/home/mavasbel/Dev/repos/ITAM/stream-consumers` (private, GitHub `mavasbel-itam/stream-consumers`, named `non-relational-dbs/stream-consumers` until 2026-10-19; branch `main`) |
| This page | `docs/reference/2026-10-17-15-13-api-key-gated-sources.md` in this repository since 2026-10-19 15:00 UTC (before: the course repository, where it was created) |
| Key file | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/.env` (git-ignored, permissions `600`) |
| Sources of this page | `uv run stream-consumers keys` (key state), the source descriptors in `src/stream_consumers/adapters/outbound/sources/` (endpoints, poll intervals, links), the repository `README.md` (sign-up steps, limits, terms), the sampling reports under `data/reports/` (rates) |

This page holds no key values. It is a status page: the status columns are
updated in place whenever a key is added or a measurement finishes.

## 1. How to add a key

1. Create the account on the sign-up page (Table 2) and get the key.
2. Put it in `/home/mavasbel/Dev/repos/ITAM/stream-consumers/.env` on the line
   with the variable name from Table 1 (the file was created from
   `.env.example`, so every line already exists).
3. Check it: `uv run stream-consumers keys` must show the variable as `set`,
   then `uv run stream-consumers check <source id> --seconds 60` must show `ok`.
4. Every key the project has stays in `.env`, including keys no source reads
   ("held keys", section 11). Re-test all of them at any time with
   `uv run pytest tests/live/test_keys_live.py -m live`.

A source that requires a key reports `key-pending` until its key is set; it
never fails a run. A required-key source joins the catalog only when its own
24 hourly rounds, measured with the key, give a median of at least 1 event/s
(a round that delivers nothing or fails counts as 0 events/s).

## 2. Summary

| Group | Sources | Key set | Key missing / not set |
|---|---|---|---|
| Key required | 11: 7 accepted 2026-10-19; 4 in group E, below 1 event/s (`entsoe`, `fink`, `gfw`, `lasair`) | 9 read by their source (`aisstream`, `cta_bus`, `cta_train`, `entsoe`, `gfw`, `mastodon`, `mta_bustime`, `nta`, `wmata`) | 2 (`fink`, `lasair`; both group E) |
| Key optional (work without one; a key raises limits) | 3 | 3 (`mbta_v3`, `opensky`, `tfl`) | 0 |
| **Total** | **14** | **12** | **2** |

Four more keys are stored and verified but are **not read by any stream**: the
Coinbase CDP key (section 3), the Lasair REST API token (section 4), the Bitso
private API key (section 12) and the Binance API key (section 13).

All 14 sign-ups are free. NASA FIRMS is not in this list: the repository reads
its public 24-hour files, which need no key.

## Table 1 — Status

Rates are events per second. "Round 1" is the first round of the 24-hour
sampling started 2026-10-17 21:00:36 UTC on commit `bc3a7fb`
(`data/reports/sampling-20261017/`). "Earlier median" is the median over the 23
earlier hourly rounds of 2026-10-13/14 (`data/reports/sampling-20261013b`, `-c`),
which are a cross-check only.

| # | Source id | Service | Provider | Key | Variable(s) | Key state | Measured with the key | Round 1 | Earlier median | Catalog status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `cta_bus` | CTA Bus Tracker — every Chicago bus | Chicago Transit Authority | required | `CTA_BUS_KEY` | **set** (2026-10-17; key replaced 2026-10-18 02:41 UTC) | `check` 60 s: 2.92/s at 06:45 UTC (01:45 in Chicago, night service); 28.30/s at 20:52 UTC (15:52 in Chicago); 16.44/s at 02:42 UTC with the replacement key | 28.258 | — (no key then) | **Accepted 2026-10-19** (group C, free key; stream-consumers `e0ab8dd`): all-source run `sampling-20261017`, 24/24 rounds, 23 at ≥ 1/s, median 17.379/s — certain |
| 2 | `aisstream` | aisstream.io — global AIS ship positions | aisstream.io | required | `AISSTREAM_API_KEY` | **set** (2026-10-18 17:15 UTC) | `check` 60 s: 4,047 events, 57.81/s at 17:17 UTC (section 9, Table 13) | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group B, project document; `e0ab8dd`): `sampling-aisstream-20261018` stopped by early stop 04:25 UTC, 12/24 rounds, all ≥ 1/s, median 74.209/s — certain |
| 3 | `cta_train` | CTA Train Tracker — train positions | Chicago Transit Authority | required | `CTA_TRAIN_KEY` | **set** (2026-10-18 03:20 UTC) | `check` 60 s: 1.54/s at 03:22 UTC (22:22 in Chicago, evening service), 17 fields per train; 51 trains on 8 lines | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group C; `e0ab8dd`): `sampling-keyed-20261018`, 22/24 rounds, 17 at ≥ 1/s, median 1.424/s — certain |
| 4 | `entsoe` | ENTSO-E Transparency Platform — European electricity | ENTSO-E | required | `ENTSOE_TOKEN` | **set** (2026-10-19 15:18 UTC, `.env` modification time) | `check` 600 s, 15:25:40–15:35:40 UTC, default areas (Germany, France, Spain): 744 events, rate 0.010/s; all 59 areas with data: 7,372 events, rate unmeasured (one round of requests takes about 380 s) | — | — | **Group E since 2026-10-19** (below 1 event/s: at most 0.38 points/s over every area; `docs/reference/2026-10-19-18-27-sub-threshold-sources.md` §2.3) |
| 5 | `fink` | Fink alert broker (LSST) — Kafka stream | Fink | required | `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` | missing | — | key-pending | — | Removed 2026-10-18 (no LSST alerts since 2026-07-14); **group E since 2026-10-19** |
| 6 | `gfw` | Global Fishing Watch — fishing events | Global Fishing Watch | required | `GFW_API_TOKEN` | **set** (2026-10-18 03:20 UTC) | `check` 60 s: ok, 500 events from the first read but rate unmeasured (one read per 15 min, so a 60-s round has no second read); 0 events for 2026-10-15/16/17 in every dataset (published about 3 days late) | key-pending (key added after the run started) | — (no key then) | **Removed 2026-10-18** (stream-consumers commit `908953b`): the totals of all four datasets did not grow in 18 hourly readings (2026-10-18 03:24–21:24 UTC), so the median growth of the 24 readings is 0 whatever the last 6 show (section 10). The token stays valid in `.env`. **Group E since 2026-10-19**: the source reads the token again, so it is no longer a held key; all 22 readings up to 2026-10-19 00:24 UTC were unchanged |
| 7 | `lasair` | Lasair alert broker (LSST) — Kafka stream | Lasair | required | `LASAIR_KAFKA_TOPIC` | missing (the account and its REST API token exist, section 4; the topic needs a saved filter) | 0 new alerts: the latest detection in Lasair is 2026-07-14 10:03 UTC (section 4) | key-pending | — | Removed 2026-10-18 (no LSST alerts since 2026-07-14); **group E since 2026-10-19**, still needing a saved filter's topic |
| 8 | `mastodon` | Mastodon public timeline (streaming) | social.vivaldi.net (since 2026-10-18 15:34 UTC; before: mastodon.social) | required | `MASTODON_ACCESS_TOKEN`, `MASTODON_INSTANCE` | **set** (2026-10-18 15:34 UTC; account on social.vivaldi.net; `MASTODON_INSTANCE=social.vivaldi.net`) | `check` 60 s: 234 events, 3.90/s at 15:35 UTC (section 7, Table 11) | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group C; default instance now social.vivaldi.net; `e0ab8dd`): `sampling-mastodon-vivaldi-20261018` stopped by early stop, 13/24 rounds, all ≥ 1/s, median 2.383/s — certain. mastodon.world (second option, held token): `sampling-mastodon-world-20261018` stopped 2026-10-19 05:38 UTC by the owner's decision, 7/24 rounds, median 1.633/s, not decided (open); social.vivaldi.net stays the default. The mastodon.social round 1 (0.85/s, deletions only) stays as evidence only |
| 9 | `mta_bustime` | MTA Bus Time — New York buses (GTFS-RT) | MTA | required | `MTA_BUSTIME_KEY` | **set** (2026-10-18 04:53 UTC) | `check` 60 s: 1,217 events, 20.18/s at 04:54 UTC (00:54 in New York); 585 buses in the feed | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group C; `e0ab8dd`): `sampling-mta_bustime-20261018`, 20/24 rounds, all ≥ 1/s, median 50.567/s — certain |
| 10 | `nta` | NTA Ireland — national vehicle positions (GTFS-RT) | National Transport Authority | required | `NTA_API_KEY` | **set** (2026-10-18 04:22 UTC, primary key) | `check` 150 s: 169 events, 0.94/s at 04:25 UTC (05:25 in Dublin); 62 vehicles in the feed at 04:30 UTC | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group C; `e0ab8dd`): `sampling-nta-20261018` (150-s window), 21/24 rounds, all ≥ 1/s, median 11.474/s — certain |
| 11 | `wmata` | WMATA — Washington bus and rail positions (GTFS-RT) | WMATA | required | `WMATA_API_KEY` | **set** (2026-10-18 04:53 UTC; key of the "GTFS" product, primary) | `check` 60 s: 1,690 events, 28.37/s at 04:54 UTC (00:54 in Washington); 328 buses and 89 trains in the feeds | key-pending (key added after the run started) | — (no key then) | **Accepted 2026-10-19** (group C; `e0ab8dd`): `sampling-wmata-20261018`, 20/24 rounds, all ≥ 1/s, median 47.679/s — certain |
| 12 | `mbta_v3` | MBTA V3 API — Boston vehicles | MBTA | optional | `MBTA_API_KEY` | **set** (2026-10-18 04:53 UTC) | `check` 60 s with the key (streaming): 2,238 events, 37.30/s at 04:54 UTC; the first `reset` message carries all 245 vehicles, live events only 32.32/s | 17.297 (keyless) | 21.481 (keyless) | In the catalog (group C, key optional). Keyed streaming mode: `sampling-mbta_v3-20261018` 20/24 rounds, median 55.690/s — certain. The README table uses run `d2` (opening-snapshot fix): stopped 2026-10-19 05:38 UTC by the owner's decision, 7/24 rounds, median 45.787/s — passes on 7 rounds (stopped early) |
| 13 | `opensky` | OpenSky Network — aircraft over Mexico | OpenSky Network | optional | `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` | **set** (2026-10-18 15:47 UTC; API client) | `check` 60 s with the key: 2,016 events, 32.57/s at 15:48 UTC (section 8, Table 12) | 26.253 (keyless) | 27.146 (keyless) | In the catalog (project document). Keyed mode: `sampling-opensky-20261018` stopped by early stop 02:55 UTC, 12/24 rounds, all ≥ 1/s, median 30.477/s — certain |
| 14 | `tfl` | TfL — London Underground arrivals | Transport for London | optional | `TFL_APP_KEY` | **set** (2026-10-18 15:47 UTC; primary key of the "AirQuality" subscription, product "500 Requests per min") | `check` 60 s with the key: 110 events, rate 0.000/s — a cached answer, see section 8 | 0.000 (keyless, 22:01 London time) | 0.342 (keyless); current run, rounds 1–20: median 4.977/s, 5 rounds at 0.000 | In the catalog (group C, key optional). Keyed mode: `sampling-tfl-20261018` stopped by early stop 03:55 UTC, 13/24 rounds, median 2.515/s — certain. The README table uses run `d2` (150-s window): stopped 2026-10-19 05:38 UTC by the owner's decision, 7/24 rounds, median 1.750/s — passes on 7 rounds (stopped early). The 0.000 rounds come from TfL's shared cache (section 8) |

## Table 2 — How to get each key

The sign-up links were fetched on 2026-10-17 at 21:14 UTC; every one returned HTTP 200.

| # | Source id | Sign-up page | Steps | Waiting time stated by the provider |
|---|---|---|---|---|
| 1 | `cta_bus` | https://www.ctabustracker.com/bustime/login.jsp | Bus Tracker account → My Account → Developer API → apply | e-mailed after approval (**done**) |
| 2 | `aisstream` | https://aisstream.io/account | Sign in with GitHub, create a key (shown once) | not stated |
| 3 | `cta_train` | https://www.transitchicago.com/developers/traintrackerapply/ | Application form; CTA reviews it | not stated (review) |
| 4 | `entsoe` | https://transparency.entsoe.eu/ | Register, then e-mail transparency@entsoe.eu asking for RESTful API access | "within 3 working days" |
| 5 | `fink` | https://forms.gle/2td4jysT4e9pkf889 | Fink subscription form; the team e-mails the server address and group id | not stated |
| 6 | `gfw` | https://globalfishingwatch.org/our-apis/ | Account, then request a token (non-commercial use) | not stated |
| 7 | `lasair` | https://lasair.lsst.ac.uk/ | Account (e-mail), save a filter with Kafka streaming; its topic is `lasair_<user id><filter name>` | not stated |
| 8 | `mastodon` | https://social.vivaldi.net/auth/sign_up (used); any instance with open live feeds | Account on the instance, then Preferences → Development → New application, scope `read:statuses` only, copy "Your access token" | not stated |
| 9 | `mta_bustime` | https://register.developer.obanyc.com/ | Web form | "within half an hour" |
| 10 | `nta` | https://developer.nationaltransport.ie/signup | Developer portal account, subscribe to "GTFS Realtime" | not stated |
| 11 | `wmata` | https://developer.wmata.com/signup | Developer account, subscribe to a Transit Data tier | not stated |
| 12 | `mbta_v3` | https://api-v3.mbta.com/register | One key per application | "might take a day" |
| 13 | `opensky` | https://opensky-network.org/my-opensky/account | Account → create an API client (client id + secret); the client id ends in `-api-client` | not stated |
| 14 | `tfl` | https://api-portal.tfl.gov.uk/signup | API portal, subscribe to the product "500 Requests per min" | not stated |

## Table 3 — Technical details

"Poll every" is the interval this repository uses; push sources stay connected.

| # | Source id | Endpoint | Where the key goes | Documented limit | Poll every |
|---|---|---|---|---|---|
| 1 | `cta_bus` | `https://www.ctabustracker.com/bustime/api/v3/getvehicles?key=<CTA_BUS_KEY>&rt=<up to 10 routes>&format=json` | query `key` | 100,000 transactions/day | 30 s (≈13 requests per poll, ≈37,000/day) |
| 2 | `aisstream` | `wss://stream.aisstream.io/v0/stream` | `APIKey` in the first WebSocket message | 3 connections per account and per IP; frames dropped for slow readers | push |
| 3 | `cta_train` | `https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=<CTA_TRAIN_KEY>&rt=<line>&outputType=JSON` | query `key` | 50,000 requests/day | 30 s (8 lines) |
| 4 | `entsoe` | `https://web-api.tp.entsoe.eu/api?securityToken=<ENTSOE_TOKEN>&documentType=A75&processType=A16&in_Domain=<EIC>…` | query `securityToken` | 400 requests/min | 300 s |
| 5 | `fink` | `kafka://<FINK_KAFKA_SERVERS>/<FINK_TOPICS>` | Kafka bootstrap servers and `group.id` | none documented | push |
| 6 | `gfw` | `https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest…` | header `Authorization: Bearer` | 50,000 requests/day, 1,500,000/month | 900 s |
| 7 | `lasair` | `kafka://lasair-lsst-kafka.lsst.ac.uk:9092/<LASAIR_KAFKA_TOPIC>` | Kafka topic (the server needs no password) | none documented for Kafka | push |
| 8 | `mastodon` | `https://social.vivaldi.net/api/v1/streaming/public` (host from `configuration.urls.streaming` = `wss://social.vivaldi.net`) | header `Authorization: Bearer` | 300 REST calls per 5 min; streaming not stated | push |
| 9 | `mta_bustime` | `https://gtfsrt.prod.obanyc.com/vehiclePositions?key=<MTA_BUSTIME_KEY>` | query `key` | no number; all-vehicle requests not under 30 s apart | 30 s |
| 10 | `nta` | `https://api.nationaltransport.ie/gtfsr/v2/Vehicles` | header `x-api-key` | one call every 60 s | 60 s |
| 11 | `wmata` | `https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb` and `…/rail-gtfsrt-vehiclepositions.pb` | header `api_key` | not published on an official page | 15 s |
| 12 | `mbta_v3` | `https://api-v3.mbta.com/vehicles` | header `x-api-key`; enables streaming | 1,000 requests/min (20 without a key) | 20 s keyless; push with a key |
| 13 | `opensky` | `https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86` | OAuth 2 client credentials → header `Authorization: Bearer` | 4,000 credits/day (400 anonymous) | 30 s (`OPENSKY_POLL_SECONDS`) |
| 14 | `tfl` | `https://api.tfl.gov.uk/Mode/tube/Arrivals` | query `app_key` | 500 requests per minute (product "500 Requests per min", as shown on the subscription page) | 30 s |

Optional settings that already have defaults (described in `.env.example`):
`AISSTREAM_BOUNDING_BOXES`, `ENTSOE_AREAS`, `FINK_TOPICS`, `GFW_DATASET`,
`GFW_LOOKBACK_DAYS`, `GFW_PAGES`, `LASAIR_KAFKA_SERVER`, `LASAIR_GROUP_ID`,
`MASTODON_INSTANCE`, `OPENSKY_POLL_SECONDS`, and `CROSSREF_MAILTO` (keyless Crossref).

## Table 4 — Documentation, terms and conditions to know

Links fetched on 2026-10-17 at 21:14 UTC. Three terms pages answer HTTP 403 to
scripted requests (marked "403"); their text was read earlier by other means and
is summarised in the 2026-10-13 stream-consumers record.

| # | Source id | Documentation | Terms | Condition to know before using it |
|---|---|---|---|---|
| 1 | `cta_bus` | https://www.transitchicago.com/developers/bustracker/ | https://www.transitchicago.com/developers/terms/ | One key per account |
| 2 | `aisstream` | https://aisstream.io/documentation | https://aisstream.io/privacypolicy | Publishes no terms of use, only a privacy policy |
| 3 | `cta_train` | https://www.transitchicago.com/developers/traintracker/ | https://www.transitchicago.com/developers/terms/ | Application reviewed by CTA |
| 4 | `entsoe` | https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API (403) | https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions (403) | Actual load, actual generation and day-ahead prices are not in the CC BY 4.0 free re-use list; they fall under §3.1 of the Terms of Use |
| 5 | `fink` | https://doc.lsst.fink-broker.org/services/livestream/ | https://github.com/astrolabsoftware/fink-client | The form says access is open "to any scientists" |
| 6 | `gfw` | https://globalfishingwatch.org/our-apis/documentation | https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits | Non-commercial only (CC BY-NC 4.0); the token must not be shared; register on behalf of the course/ITAM |
| 7 | `lasair` | https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html | https://lasair.lsst.ac.uk/privacy | Publishes no terms of use, only a privacy statement |
| 8 | `mastodon` | https://docs.joinmastodon.org/methods/streaming/ | https://social.vivaldi.net/terms-of-service (HTTP 200; `/api/v2/instance` gives no terms URL) and the server rules (`/api/v1/instance/rules`: last rule "Follow the Terms of Use and Code of Conduct of Vivaldi.net") | Posts are personal data; they are masked in every stored sample |
| 9 | `mta_bustime` | https://bustime.mta.info/developers/gtfs-realtime/ | https://www.mta.info/developers/terms-and-conditions (403) | No numeric quota; requesting all vehicles less than 30 s apart may get the key revoked |
| 10 | `nta` | https://developer.nationaltransport.ie/ | https://developer.nationaltransport.ie/usagepolicy | One call every 60 s |
| 11 | `wmata` | https://developer.wmata.com/ | https://developer.wmata.com/license | Free today, but WMATA reserves the right to charge in the future |
| 12 | `mbta_v3` | https://www.mbta.com/developers/v3-api | https://www.mbta.com/developers/v3-api | One key per application |
| 13 | `opensky` | https://openskynetwork.github.io/opensky-api/rest.html | https://opensky-network.org/about/terms-of-use | A written agreement is required for "operational" REST API use, including automated systems, even non-profit ones |
| 14 | `tfl` | https://api-portal.tfl.gov.uk/ | https://api-portal.tfl.gov.uk/ | Product "500 Requests per min"; answers are cached for up to 60 s by a shared cache (section 8) |

## 3. Coinbase CDP Secret API Key — tested, not needed by the stream

| | |
|---|---|
| Received | 2026-10-17, file `~/Downloads/cdp_api_key.json` (fields `id`, `privateKey`) |
| Stored in | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/credentials/coinbase_cdp_api_key.json`` until 2026-10-18 23:15 UTC; since then in `.env` as the held key `COINBASE_CDP_KEY_ID` + `COINBASE_CDP_KEY_SECRET` (owner's decision: every key stays in `.env`; section 11). |
| Key type | CDP Secret API Key, Ed25519 (64-byte secret: 32-byte seed + 32-byte public key) |
| Sign-up page | https://portal.cdp.coinbase.com/ |
| How it is used | A JWT signed with EdDSA, sent as `Authorization: Bearer`, valid 2 minutes ("Your JWT expires after 2 minutes, after which all requests are unauthenticated.") — https://docs.cdp.coinbase.com/get-started/authentication/jwt-authentication |
| Terms | https://www.coinbase.com/legal/developer-platform/terms-of-service |
| Test script | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/coinbase-key-test/test_key.py` (git-ignored; read-only calls only; prints statuses and field names, never the key, the JWT, account identifiers or balances) |
| Result file | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/coinbase-key-test/result-2026-10-18T020422Z.json` |

### Table 5 — Test results (run 2026-10-18 02:04:22 UTC)

| # | Check | With the key | Without a key | With a different (random) key |
|---|---|---|---|---|
| 1 | Secret decodes to 64 bytes and its public half matches the seed | yes | — | — |
| 2 | `GET https://api.coinbase.com/api/v3/brokerage/key_permissions` | HTTP 200 | HTTP 401 | HTTP 401 |
| 3 | Permissions reported by Coinbase for this key | `can_view: true`, `can_trade: false`, `can_transfer: false`, portfolio type `DEFAULT` | — | — |
| 4 | `GET https://api.coinbase.com/api/v3/brokerage/products?limit=1` (private product list) | HTTP 200, 1 product | HTTP 401 | HTTP 401 |
| 5 | `GET https://api.cdp.coinbase.com/platform/v2/evm/accounts?pageSize=1` (CDP platform API) | HTTP 200, 0 accounts | HTTP 401 | HTTP 401 |
| 6 | `GET https://api.coinbase.com/api/v3/brokerage/market/products?limit=1` (public product list) | — | HTTP 200, 1 product | — |

The key is valid and **view-only**: it cannot place orders or move funds.

### Table 6 — Key or no key, the same 60 s window (BTC, ETH, SOL, XRP, DOGE against USD; run 2026-10-18 02:04:22 UTC)

| Connection | JWT in the subscription | Messages | Events | Events/s | First event |
|---|---|---|---|---|---|
| Advanced Trade `wss://advanced-trade-ws.coinbase.com`, channel `market_trades` | yes | 282 | 962 trades (500 of them the initial snapshot) | — | 0.53 s |
| Advanced Trade `wss://advanced-trade-ws.coinbase.com`, channel `market_trades` | no | 279 | 962 trades (500 of them the initial snapshot) | — | 0.52 s |

The two rows are identical, which is what this table shows. Their counts are
**not rates**: on subscribing, `market_trades` first sends a snapshot of past
trades (100 per product here), so 962/60 overstates the live flow. The live rates
are in Table 7.

What this shows:

1. **The key adds nothing to the public stream.** The same 962 trades arrived
   with and without the JWT (the same snapshot plus the same live trades). Coinbase's documentation says so for every public
   channel ("A JWT is not required.") —
   https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-endpoints
2. **The key does not apply to the stream the repository uses today.** The
   `coinbase` source reads the Exchange feed, and Coinbase lists the Exchange API
   as a "Separate key system with passphrase" —
   https://docs.cdp.coinbase.com/get-started/authentication/overview
3. **The key's only streaming use is private account data** (channels `user`
   and `futures_balance_summary` on `wss://advanced-trade-ws-user.coinbase.com`,
   "A CDP JWT is required."). It was deliberately not tested: those channels carry
   the account's own orders and positions, which are not stream data for the course.
4. **Correction (2026-10-18 02:40 UTC).** Version `de3338a` of this page said
   `market_trades` delivered 16.0 trades/s against 7.7/s for the current source.
   That was wrong: the 16.0 included the 500 snapshot trades. Measured live-only
   in one shared window (Table 7), `market_trades` delivers about the same as the
   current source, with 6 fields per trade instead of 17.
5. Documented limits: "Advanced Trade API WebSocket connections are rate-limited at
   **750 per second per IP address**" and "unauthenticated messages are rate-limited
   at **8 per second per IP address**" (these are messages the client sends, such as
   subscriptions) —
   https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/websocket/websocket-rate-limits

### Table 7 — Live events only (snapshots excluded), the same 60 s window for all three (run 2026-10-18 02:26:22 UTC)

| Connection | Live events | Snapshot events excluded | Live events/s | Fields per event |
|---|---|---|---|---|
| Exchange `wss://ws-feed.exchange.coinbase.com`, channel `ticker` (the current `coinbase` source) | 350 | 0 | 5.833 | 17 |
| Advanced Trade `wss://advanced-trade-ws.coinbase.com`, channel `ticker` | 676 | 5 | 11.267 | 13 |
| Advanced Trade `wss://advanced-trade-ws.coinbase.com`, channel `market_trades` | 345 | 500 | 5.750 | 6 |

Script and result: `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/coinbase-key-test/same.py` and
`same-window-2026-10-18T022622Z.json` (git-ignored). One 60-second window only; not a daily rate.

The original file `~/Downloads/cdp_api_key.json` still holds the key with
permissions `664` (readable by the user's group).

## 4. Lasair REST API token — tested; the stream needs a topic, and no alerts arrive

| | |
|---|---|
| Received | 2026-10-18 (Lasair account of the course owner) |
| Stored in | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/credentials/lasair_api_token`` until 2026-10-18 23:15 UTC; since then in `.env` as the held key `LASAIR_API_TOKEN` (section 11). |
| What it is for | Lasair's REST API (`https://api.lasair.lsst.ac.uk/api/`: `query`, `cone`, `object`, `sherlock`). The `lasair` source reads Lasair's Kafka stream, which needs no password, only the topic of a filter saved with Kafka streaming. The REST API and the official client `lasair` 0.1.4 have no method to create a filter or a topic (client methods: `annotate`, `annotate_list`, `cone`, `fetch`, `fetch_from_server`, `hash_it`, `object`, `query`, `sherlock_object`, `sherlock_position`). |
| Documented limit | 100 calls per hour; 10,000 for power users (Lasair REST API documentation) |

### Table 8 — Test results (run 2026-10-18 03:40–03:52 UTC)

| Check | Result |
|---|---|
| `query` (3 objects) with the token as `token=` parameter | HTTP 200, 3 objects |
| Same with the header `Authorization: Token …` | HTTP 200, the same 3 objects |
| No token | HTTP 401 `{"detail":"Authentication credentials were not provided."}` |
| A damaged token (control) | HTTP 401 `{"detail":"Invalid token."}` |
| `cone` and `object` with the token | HTTP 200 |
| Latest detection in Lasair (`objects` ordered by `lastDiaSourceMjdTai`) | 2026-07-14 10:03 UTC; 0 objects with a detection in the last 1 h, 24 h, 3, 7, 14 or 30 days. Lasair's home page lists its latest alerts as 95.7 days old. |
| Fink (a second, independent LSST broker; `api.lsst.fink-portal.org/api/v1/statistics`, no key) | 95 nights with alerts in 2026; the last is 2026-07-14 (473,344 alerts); peak night 2026-07-13, 744,559 alerts. No night after 2026-07-14. |
| Lasair Kafka server `lasair-lsst-kafka.lsst.ac.uk:9092` without any credential | 248 topics of saved filters can be listed and read; their end offsets add up to 16,768,847 messages ever written, but only 189 are kept now (Lasair keeps 7 days), the 1–10 records Lasair writes when a filter is saved |

Conclusion: the token works. Both LSST brokers report no alerts after the
night of 2026-07-14, so the `lasair` stream (and `fink`) would deliver 0
events/s today; under the 1 event/s rule it would be removed. Creating the
filter (sign in → Filters → new filter → Save → Filter Settings "On new alert"
with Kafka streaming; its topic appears on the filter's detail page) is useful
only once alerts resume. The cause of the pause is not stated on the pages read.

## 5. Mastodon and NTA — tests of 2026-10-18

### Table 9 — Test results (run 2026-10-18 04:22–04:45 UTC)

| Check | Result |
|---|---|
| NTA primary key | HTTP 200, `application/protobuf`, 4,554 bytes |
| NTA secondary key | HTTP 200, `application/protobuf`, 4,808 bytes (not stored; it stays on the NTA portal as a spare) |
| NTA without a key | HTTP 401 "Access denied due to missing subscription key." |
| NTA damaged key (control) | HTTP 401 "Access denied due to invalid subscription key." |
| Mastodon token, `GET /api/v1/accounts/verify_credentials` | HTTP 200; the account is on mastodon.social |
| Mastodon without a token, and with a damaged token | HTTP 401 `{"error":"The access token is invalid"}` |
| Scopes of the application `epistelabs` (`GET /api/v1/apps/verify_credentials`) | every scope, including `write`, `write:*`, `follow`, `push` and `admin:*`; the stream needs only `read:statuses` |
| mastodon.social `GET /api/v2/instance` → `configuration.timelines_access` | `live_feeds`: local `disabled`, remote `disabled` (hashtag and trending-link feeds `public`); version 4.8.0-alpha.3 |
| mastodon.social `GET /api/v1/timelines/public` (all, `local=true`, `remote=true`), with the token | HTTP 200, empty list each time |
| mastodon.social streaming `public`, `public/local`, `public/remote` (≈17 s each, the server then closes the connection) | 13 `delete`, 0 events, 18 `delete`; no `update` (no posts) |
| Same check on mastodon.online (also run by Mastodon gGmbH) | `live_feeds` local and remote `disabled` |
| Federated timeline on other large instances, no account (new posts counted over 40 s, `GET /api/v1/timelines/public?limit=40` every 10 s, 04:41 UTC) | social.vivaldi.net 1.14/s, mas.to 0.97/s, mastodon.world 0.91/s, mstdn.jp 0.79/s, fosstodon.org 0.56/s, pawoo.net 0.50/s, hachyderm.io and mastodon.uno 0.42/s, troet.cafe 0.34/s; these instances report `live_feeds` `public` (pawoo.net runs 4.1.18 and does not report it) |

Conclusion for `mastodon`: the token works, but mastodon.social publishes no
posts on its public timelines, so the source as configured receives only
deletions (2 fields). Its sampling was stopped after round 1 (kept as
evidence). To keep the source, the token must come from an account on an
instance whose live feeds are open; `MASTODON_INSTANCE` then names that
instance. The token's application has every scope; a new one should have only
`read:statuses`.

Conclusion for `nta`: the key works. Test data replaced by a real capture (3 of
62 vehicles, 2026-10-18 04:30:23 UTC). That capture was taken while the
sampling round was polling with the same key, so it was one call within 60 s
of another; no error was returned.

## 6. MTA Bus Time, WMATA and MBTA — tests of 2026-10-18

### Table 10 — Test results (run 2026-10-18 04:53–04:57 UTC)

| Check | Result |
|---|---|
| MTA, SIRI vehicle monitoring (`bustime-classic.mta.info/api/siri/vehicle-monitoring.json`, line M15) | key: HTTP 200 with vehicles; no key: HTTP 401; damaged key: HTTP 403 |
| MTA, GTFS-Realtime `vehiclePositions` (the endpoint `mta_bustime` reads) | key, no key and damaged key: HTTP 200, the same 82,106 bytes — this feed does not check the key today; the source still sends it, as the documentation requires |
| WMATA bus and rail GTFS-Realtime feeds, each of the 3 products' primary keys ("Bus Route and Stop Methods", "GTFS", "GTFS Metro Alert") and the "GTFS" secondary key | HTTP 200 `application/octet-stream` for all four keys on both feeds |
| WMATA without a key, and with a damaged key | HTTP 401 on both feeds |
| WMATA key stored | the "GTFS" product's primary key (the product that names these feeds); the other five keys stay on the WMATA portal, not stored |
| MBTA `GET /vehicles` | key: HTTP 200; no key: HTTP 200 (keyless allowance, 20 requests/min); damaged key: HTTP 403 |
| MBTA streaming (`Accept: text/event-stream`) | key: HTTP 200 `text/event-stream`, first event `reset`; no key: HTTP 406 `not_acceptable` |
| MBTA streaming, 60.2 s counted by event type | `reset` 1 message with 245 vehicles, `update` 1,945, `remove` 2 → live events only 32.32/s; our 60-s `check` (37.30/s) counts the `reset` vehicles too |
| `check` 60 s, 04:54 UTC | `mta_bustime` ok 1,217 events 20.18/s; `wmata` ok 1,690 events 28.37/s; `mbta_v3` ok 2,238 events 37.30/s |

Test data replaced by real captures (2026-10-18 04:57:22 UTC): `mta_bustime` 3
of 585 buses; `wmata` 3 of 328 buses and 3 of 89 trains; the MBTA stream's
first `reset` (2 of 240 vehicles) and its first `add`, `update` and `remove`.
No key is stored in them.

Decisions of 2026-10-18 recorded here: `lasair` and `fink` are removed (no
LSST alerts since 2026-07-14), so no Lasair filter has to be created;
`mastodon` is kept and waits for a token from an instance with open live feeds.

## 7. Mastodon on social.vivaldi.net — tests of 2026-10-18

### Table 11 — Test results (run 2026-10-18 15:34–15:39 UTC)

| Check | Result |
|---|---|
| `GET /api/v1/accounts/verify_credentials` | token: HTTP 200 (the account); no token: HTTP 401; damaged token: HTTP 401 "The access token is invalid" |
| `GET /api/v2/instance` | version `4.7.3+vivaldimod`; `configuration.timelines_access.live_feeds` local `public`, remote `public` (on mastodon.social both were `disabled`) |
| `GET /api/v1/apps/verify_credentials` | application `epistelabs` with **every** scope, including `write`, `write:statuses`, `follow`, `push`, `admin:read` and `admin:write`; the stream needs only `read:statuses` |
| `check mastodon` 60 s | ok: 234 events, 3.90/s |
| Sampling round 1 (15:37 UTC) | ok: 272 events, 4.53/s, median 63 fields per status |

Test data replaced by a real capture (2026-10-18 15:36:51 UTC): one public
`update` and one `delete` from this stream, the status flattened and masked
with the source's own personal fields; no token is stored.

While masking it I found and fixed a defect in the masking rule: a pattern
such as `mentions.*` did not cover `mentions` itself when its value is a list,
so a status's mentions (user names and profile links) and media attachments
(file links and image descriptions) were not masked in stored samples. Lists under such a pattern are now masked; a unit
test pins it (the earlier code left `username` unmasked in the same case).

## 8. OpenSky and TfL — tests of 2026-10-18

### Table 12 — Test results (run 2026-10-18 15:46–15:53 UTC)

| Check | Result |
|---|---|
| OpenSky token request (`auth.opensky-network.org`, client credentials) | HTTP 200, `Bearer`, `expires_in` 1800 (30 min); with a damaged secret: HTTP 401 `unauthorized_client` |
| OpenSky `/states/all` (our Mexico box) | token: HTTP 200, 1,066 aircraft, `X-Rate-Limit-Remaining: 3996`; no token: HTTP 200, 1,067 aircraft, `X-Rate-Limit-Remaining: 236`; damaged token: HTTP 401 |
| OpenSky credits | one request of this box cost 4 credits (4,000 → 3,996); the anonymous allowance is shared with the all-source run, which had left 236 of 400 that day |
| TfL `/Mode/tube/Arrivals`, each subscription's primary key and one secondary key (5 keys) | HTTP 200 for all; no key: HTTP 200; damaged key: HTTP **429** "Invalid app_key is provided." |
| TfL key stored | primary key of the "AirQuality" subscription (product "500 Requests per min"); "Occupancy" and "Crowding" are the same product; "Trackernet" is a separate product (TrackernetFeedPublic) that this source does not use; the other keys stay on the portal |
| TfL response headers | no rate-limit headers; `Cache-Control: public, must-revalidate, max-age=30, s-maxage=60` |
| TfL, 5 polls 30 s apart (15:50–15:52 UTC, with the key) | changed predictions 214, 193, **0**, 214; the poll with 0 had `X-Cache: HIT`, `Age: 31` and the same body as the previous poll |
| `check` 60 s, with the keys | `opensky` ok 2,016 events 32.57/s; `tfl` ok 110 events, rate 0.000/s |

Why TfL sometimes measures 0.000/s: a shared cache in front of the API keeps an
answer for up to 60 s (`s-maxage=60`), with or without a key. A 60-s round
polls at 0 s and 30 s; when the 30-s poll gets the cached copy, no prediction
has changed and the round's rate is 0. In the all-source run this happened in
5 of 20 rounds; its median over those 20 rounds is still 4.977/s. TfL's keyed
sampling therefore uses a 150-s window (like NTA), so every round spans
several fresh answers. A fix for the source itself (for example polling every
60 s) is proposed after the samplings end; no code changes during them.

The OpenSky terms still apply with an account: a written agreement is required
for "operational" REST API use, including automated systems.

## 9. aisstream.io — tests of 2026-10-18

### Table 13 — Test results (run 2026-10-18 17:15–17:20 UTC)

| Check | Result |
|---|---|
| Subscription with the key (whole world) | `SubscriptionConfirmation` first, then messages; 4,070 messages in the test window, first after 3.0 s |
| Subscription without a key / with a damaged key | the server closes the connection without a close frame and without an error message; 0 messages |
| Message types in the test window | `PositionReport` 2,527, `StandardClassBPositionReport` 717, `ShipStaticData` 455, `StaticDataReport` 358, `ExtendedClassBPositionReport` 12 |
| `check aisstream` 60 s | ok: 4,047 events, 57.81/s |
| Sampling round 1 (17:20 UTC) | ok: 5,434 events, 77.62/s, median 24 fields |

Test data replaced by a real capture (2026-10-18 17:18:44 UTC): the
subscription confirmation and the first message of each of the four most
frequent types; the key is not stored. The real `MetaData` differs from the
documentation example: it writes `latitude`/`longitude` in lower case and adds
`MMSI_String` and `time_utc`. Our decoder copies `MetaData` as it arrives, so
nothing breaks. The sampling holds one of the 3 connections the account
allows.

## 10. mastodon.world and Global Fishing Watch — 2026-10-18

### Table 14 — Can the existing Mastodon token read mastodon.world? (2026-10-18 22:20 UTC)

| Request | Result |
|---|---|
| social.vivaldi.net token on social.vivaldi.net, `GET /api/v1/accounts/verify_credentials` | HTTP 200 |
| Same token on mastodon.world, `GET /api/v1/accounts/verify_credentials` | HTTP 401 `{"error":"The access token is invalid"}` |
| mastodon.world streaming `public` with that token | HTTP 401 `{"error":"Invalid access token"}` |
| mastodon.world streaming `public` with no token | HTTP 401 `{"error":"Missing access token"}` |
| mastodon.world `GET /api/v1/timelines/public?limit=1`, no token | HTTP 200 (the REST timeline is open; the stream is not) |
| mastodon.world `GET /api/v2/instance` | version 4.7.3; `live_feeds` local and remote `public`; no terms-of-service URL |

A Mastodon token is issued by one server and is valid only there, and
mastodon.world's stream refuses requests without a token, so measuring
mastodon.world needs a token created on mastodon.world. The social.vivaldi.net
token keeps all its scopes (checked 22:05 UTC); kept as it is by decision of
2026-10-18.

### Global Fishing Watch result

`data/gfw-growth-20261018/snapshots.jsonl`: 19 snapshots (03:24–21:24 UTC) of
the totals over 2026-09-01..2026-11-01. Unchanged in every snapshot: fishing
1,735,359; encounters 138,214; loitering 2,346,131; port visits 3,504,964. 18
of the 24 hourly differences are 0, so the median is 0 and `gfw` is removed
under the agreed rule (a median growth of at least 3,600 per hour was needed).

### mastodon.world token (received 2026-10-18 22:45 UTC)

| Check (22:50 UTC) | Result |
|---|---|
| `GET /api/v1/accounts/verify_credentials` with the token | HTTP 200 (account created 2026-10-18) |
| Same without a token, and with a damaged token | HTTP 401 `{"error":"The access token is invalid"}` |
| `GET /api/v1/apps/verify_credentials` | application `epistelabs`; every scope, including `write:*`, `follow`, `push` and `admin:*` (the stream needs only `read:statuses`) |
| Streaming `public`, 20 s, with the token | HTTP 200: 30 `update` (posts), 7 `delete` |
| Streaming `public` with a damaged token | HTTP 401 `{"error":"Invalid access token"}` |

Own 24-hour sampling: unit `stream-sampling-mastodon-world-20261018`, from the
separate checkout `stream-consumers-run` at commit `908953b`, with
`MASTODON_INSTANCE=mastodon.world` and the token as `MASTODON_ACCESS_TOKEN` in
the process environment (it wins over `.env`, which keeps social.vivaldi.net).
Started 22:54 UTC, ends ~2026-10-19 21:56 UTC, reports in
`data/reports/sampling-mastodon-world-20261018/`. Round 1: ok, 139 events,
2.317 events/s, median 63 fields. The social.vivaldi.net sampling continues
unchanged; the two are compared when both end.

Result: the run was stopped 2026-10-19 05:38 UTC by the owner's decision after 7
rounds, median 1.633 events/s (`verdict`: open). social.vivaldi.net's own run
is certain at 2.383 events/s, so social.vivaldi.net stays the default instance;
the mastodon.world token stays a held key.

## 11. Every key in `.env` — held keys (2026-10-18)

Owner's decision (2026-10-18 22:45 UTC): every key of every application stays
in `stream-consumers/.env`, so that each can be tested again. Keys that no
source reads are declared as **held keys** in stream-consumers (commit
`7d9012a`, `HELD_KEYS`); `keys` lists them as `held`, `.env.example` names
them, and `keys` still exits 1 for any other variable. `data/credentials/` was
removed after checking that its two files equalled the new `.env` values.
`.env` now follows the generated template exactly, with 37 values set
(`ENTSOE_TOKEN` is the only empty key; the empty `FINK_*` and
`LASAIR_KAFKA_TOPIC` lines of the removed sources were dropped).

### Table 15 — Held keys

| Owner | Variable(s) | What it is |
|---|---|---|
| `mastodon` | `MASTODON_CLIENT_ID`, `MASTODON_CLIENT_SECRET` | Application that issued `MASTODON_ACCESS_TOKEN` (social.vivaldi.net) |
| `mastodon` | `MASTODON_WORLD_ACCESS_TOKEN`; `MASTODON_WORLD_CLIENT_ID`, `MASTODON_WORLD_CLIENT_SECRET` | mastodon.world token and its application |
| `mastodon` | `MASTODON_SOCIAL_ACCESS_TOKEN`; `MASTODON_SOCIAL_CLIENT_ID`, `MASTODON_SOCIAL_CLIENT_SECRET` | mastodon.social token (live feeds disabled) and its application |
| `nta` | `NTA_API_KEY_SECONDARY` | Secondary key of the subscription |
| `wmata` | `WMATA_API_KEY_SECONDARY` | Secondary key of the "GTFS" product |
| `wmata` | `WMATA_BUS_ROUTES_KEY`, `WMATA_BUS_ROUTES_KEY_SECONDARY` | "Bus Route and Stop Methods" product |
| `wmata` | `WMATA_METRO_ALERTS_KEY`, `WMATA_METRO_ALERTS_KEY_SECONDARY` | "GTFS Metro Alert" product |
| `tfl` | `TFL_APP_KEY_SECONDARY` | Secondary key of the "AirQuality" subscription |
| `tfl` | `TFL_OCCUPANCY_KEY`, `TFL_CROWDING_KEY`, `TFL_TRACKERNET_KEY` and each `_SECONDARY` | The other three subscriptions |
| `coinbase` | `COINBASE_CDP_KEY_ID`, `COINBASE_CDP_KEY_SECRET` | CDP Secret API Key (section 3) |
| `bitso` | `BITSO_API_KEY`, `BITSO_API_SECRET` | Private API key and secret (section 12) |
| `binance` | `BINANCE_API_KEY`, `BINANCE_API_SECRET` | API key and secret key, reading only (section 13) |
| `lasair` | `LASAIR_API_TOKEN` | REST API token (section 4); the `lasair` source (group E since 2026-10-19) reads only `LASAIR_KAFKA_TOPIC` |
| `gfw` | `GFW_API_TOKEN` | API token (section 10); held until 2026-10-19, read again by the `gfw` source (group E) since then |

### Table 16 — Re-test of every key (`tests/live/test_keys_live.py`, 2026-10-18 23:03 UTC)

For each credential: the stored value must be accepted, a copy with its last
four characters changed must be refused, and a request without it must be
refused where the provider requires a key (accepted where it is optional).

| Result | Credentials |
|---|---|
| passed (32 of 32 set) | `AISSTREAM_API_KEY`, `CTA_BUS_KEY`, `CTA_TRAIN_KEY`, `MASTODON_ACCESS_TOKEN`, the three Mastodon applications, `MASTODON_WORLD_ACCESS_TOKEN`, `MASTODON_SOCIAL_ACCESS_TOKEN`, `MBTA_API_KEY`, `MTA_BUSTIME_KEY`, both NTA keys, the OpenSky client, all 8 TfL keys, all 6 WMATA keys, the Coinbase CDP key, `LASAIR_API_TOKEN`, `GFW_API_TOKEN` |
| skipped | `ENTSOE_TOKEN` (not set) |
| control | with a made-up `CTA_TRAIN_KEY` in the environment the test fails (`errCd` 101), as it must |

Every Mastodon application (vivaldi, world, social) carries every scope,
including posting and admin; the stream needs only `read:statuses`.

## 12. Bitso private API key — 2026-10-19

Received 2026-10-19 01:15 UTC (key; secret 01:22 UTC). Bitso private API keys
are a pair, the API Key and the API Secret, and every private request must be
signed with both: "use your generated Bitso API Secret as the cryptographic key
on the concatenation of: nonce + HTTP method + request path + JSON payload",
sent as `Authorization: Bitso <key>:<nonce>:<signature>` —
https://docs.bitso.com/bitso-api/docs/create-signed-requests

The `bitso` source does **not** need it: it reads the public WebSocket
`wss://ws.bitso.com` (trades and order-book changes), which takes no key. The
pair is therefore a held key (owner `bitso`, stream-consumers commit `66c07da`):
`BITSO_API_KEY` and `BITSO_API_SECRET` in `.env`, named in `.env.example`, and
probed by `tests/live/test_keys_live.py` with a signed `GET /api/v3/balance/`.

### Table 17 — Test results (2026-10-19 01:24–01:33 UTC; read-only requests only)

| # | Test | Result |
|---|---|---|
| 1 | Signed `GET https://api.bitso.com/api/v3/balance/` with the stored key and secret | HTTP 200, `success: true`, 289 currency balances |
| 2 | The same request without the `Authorization` header | HTTP 401, code `0201`, "Invalid Nonce or Invalid Credentials" |
| 3 | Last character of the secret changed | HTTP 401, code `0215`, same message |
| 4 | Last character of the key changed | HTTP 401, code `0201`, same message |
| 5 | Signed `GET /api/v3/account_status/` | HTTP 200; only the field names were read |
| 6 | `uv run stream-consumers --env-file ../stream-consumers/.env keys` | exit 0; both variables listed as `held`, `set` |
| 7 | `uv run pytest tests/live/test_keys_live.py -m live` (all keys) | 33 passed, 1 skipped (`ENTSOE_TOKEN`, not set) |
| 8 | Control: the same Bitso probe with a wrong secret in the env file | fails ("stored value refused: HTTP 401 … 0215"), as it must |
| 9 | `uv run stream-consumers check bitso` (public WebSocket, no key) | `ok`, 1,141 events, 35.527 events/s |
| 10 | Search for both values in the stream-consumers checkouts, their git histories and the course worktree | found only in `stream-consumers/.env` |

**Scope of this key.** `account_status` returns the account's personal profile
(name, e-mail, phone, date of birth, identification). Bitso's API has no
endpoint that reports a key's permissions, so whether trading or withdrawals
are enabled cannot be read from the API; it is shown on the Bitso website under
the API key's settings. Recommendation: confirm that only the read/view
permission is enabled (the key and secret were sent through chat).

## 13. Binance API key — 2026-10-19

Two keys were received. The first, 2026-10-19 ~02:20 UTC, came without its
secret key. Binance signs every keyed Spot request ("All endpoints with a
security type other than `NONE` are `SIGNED` requests") with HMAC-SHA256 of
the query string under the secret key, so without the secret it could only be
checked for recognition: at 02:22:29 UTC an account request with a dummy
signature gave `-1022` "Signature for this request is not valid." (key
recognised; a damaged copy gave `-2015`, no key `-2014`). Binance then
answered it inconsistently (one `-2015` refusal in a full test run ending
~02:27 UTC; 3 refusals in 20 calls at ~02:34 UTC) and refused it on every call
from ~02:35 UTC with `-2015` "Invalid API-key, IP, or permissions for action."
(5 of 5 at 02:40 UTC), so it is not stored. The second, received
02:38 UTC as a pair (API key and secret key; Binance reports the key created
2026-10-19 02:38:05 UTC), is stored.

The `binance` source does **not** need it: it reads the public streams
(`check binance` 2026-10-19 02:27 UTC: `ok`, 4,718 events, 68.571 events/s).
The pair is a held key (owner `binance`, stream-consumers commit `75a87fd`):
`BINANCE_API_KEY` and `BINANCE_API_SECRET` in `.env`, named in `.env.example`,
probed by `tests/live/test_keys_live.py` with a signed
`GET /sapi/v1/account/apiRestrictions` (the endpoint as written in Binance's
connector,
https://github.com/binance/binance-connector-python/blob/master/clients/wallet/src/binance_sdk_wallet/rest_api/api/account_api.py).
The probe accepts the key only while it can read and can neither trade,
withdraw, transfer, nor use futures or margin, so the test fails if the key's
permissions are ever widened.

### Table 18 — Test results (2026-10-19 02:39–02:44 UTC; read-only requests only)

| # | Test | Result |
|---|---|---|
| 1 | Signed `GET https://api.binance.com/sapi/v1/account/apiRestrictions` | HTTP 200: `enableReading` true; `enableSpotAndMarginTrading`, `enableWithdrawals`, `enableInternalTransfer`, `permitsUniversalTransfer`, `enableFutures`, `enableMargin`, `enableVanillaOptions`, `enablePortfolioMarginTrading`, `enableFixApiTrade`, `enableFixReadOnly` all false; `ipRestrict` false |
| 2 | Signed `GET /api/v3/account` | HTTP 200, `accountType` SPOT, 7 non-zero balances (only field names and counts read). `canTrade`/`canWithdraw` there are account-level flags; the key's own permissions are those of test 1 |
| 3 | The account request without a signature | HTTP 400, `-1102` "Mandatory parameter 'signature' was not sent…" |
| 4 | Last character of the secret changed | HTTP 400, `-1022` "Signature for this request is not valid." |
| 5 | Last character of the key changed | HTTP 401, `-2015` "Invalid API-key, IP, or permissions for action." |
| 6 | No key | HTTP 401, `-2014` "API-key format invalid." |
| 7 | `uv run stream-consumers --env-file ../stream-consumers/.env keys` | exit 0; both variables listed as `held`, `set` |
| 8 | `uv run pytest tests/live/test_keys_live.py -m live` (all keys) | 34 passed, 1 skipped (`ENTSOE_TOKEN`, not set) |
| 9 | Controls: the Binance probe with a damaged secret, then with a damaged key, in a copy of the env file | both fail ("stored value refused": `-1022`; `-2008` "Invalid Api-Key ID."), as they must |
| 10 | Search for the three values (both keys and the secret) under `~/Dev/repos/ITAM` | found only in `stream-consumers/.env` |

**Network note.** At 02:35 UTC this computer was reaching the Internet through
a full WireGuard tunnel (`wg0`, all traffic, public address 149.56.13.232);
when the tunnel came up was not recorded. The stored key has no IP restriction
(`ipRestrict` false), so the address does not affect it.

## 14. Change log

| Date (UTC) | Change |
|---|---|
| 2026-10-19 20:36 | Test fixtures of `entsoe` and `gfw` replaced by answers captured with the keys (2026-10-19 20:35:45 and 20:35:58 UTC, HTTP 200): ENTSO-E actual generation for Germany, 15:00–21:00 UTC, trimmed to 3 of 16 TimeSeries; GFW fishing events 2026-10-12 to 2026-10-20, first page trimmed to 3 of 100 entries (total 175,697; dataset `public-global-fishing-events:v4.0`, the documentation example was v3.0). Both decoders read the captures without change; neither key is stored in the fixtures. `lasair` keeps its documentation example until a filter topic exists. |
| 2026-10-19 (correction) | Corrections to the 18:27 change: `LASAIR_KAFKA_TOPIC` is again the `lasair` source's required key (the 18:27 change had made the source require `LASAIR_API_TOKEN`, which it never reads, with an unverified default topic); `LASAIR_API_TOKEN` is again a held key; `GFW_API_TOKEN` is read by the `gfw` source and no longer held (Tables 1, 2 and 15 updated); the ENTSO-E all-area bound is 0.38 points/s (0.33 over the full 6-hour window). New live probe for the Kafka keys: joins the consumer group on the topic and is accepted only when partitions are assigned; an invented Lasair topic is refused with `TopicAuthorizationFailedError`. Re-test of all keys: 35 passed, 2 skipped (`LASAIR_KAFKA_TOPIC`; `FINK_KAFKA_SERVERS` + `FINK_GROUP_ID`, not set). Repository on GitHub: `mavasbel-itam/stream-consumers`. |
| 2026-10-19 18:27 | `ENTSOE_TOKEN` set (2026-10-19 15:18 UTC) and tested against the live API: HTTP 200 with data for Germany, France and Spain; a damaged copy and no token refused with HTTP 401. `check` 600 s: 0.010 events/s with the default areas; all 59 areas with data: rate unmeasured (one round takes about 380 s). `entsoe`, `fink`, `gfw`, `lasair` (with `bitstamp`, `dt_rail_trains`, `ndbc`, `npm`) restored as group E (stream-consumers `e32490d`; `docs/reference/2026-10-19-18-27-sub-threshold-sources.md`). Re-test of all keys: 35 passed, 1 skipped. |
| 2026-10-19 15:00 | Page moved into the stream-consumers repository (`docs/reference/`), with the research records it cites. The sampling runs still open were stopped 05:38 UTC by the owner's decision and decided on the rounds they had (stream-consumers `2d5a9e6`): `mbta_v3` 7/24 rounds, median 45.787/s, and `tfl` 7/24, 1.750/s — both pass on 7 rounds (stopped early); mastodon.world 7/24, 1.633/s, not used (section 10). No key changed. |
| 2026-10-19 04:30 | Keyed sources accepted (Table 1; stream-consumers `e0ab8dd`, pushed to `main`, local `main` fast-forwarded): `cta_bus`, `cta_train`, `mastodon`, `mta_bustime`, `nta`, `wmata` → group C; `aisstream` → group B; `entsoe` stays a candidate. Every accepted result is certain under the 24-round rule (early stop). Mastodon default instance → social.vivaldi.net. HTTP client fix: the 120-s limit cut slow whole-file downloads (Sensor.Community 8.5 MB took 175 s), which made `firms`/`sensorcomm` rounds read 0; their windows are now 600 s. Re-test of all keys: 34 passed, 1 skipped (ENTSO-E). |
| 2026-10-19 02:50 | Binance API key and secret key set as held keys `BINANCE_API_KEY` + `BINANCE_API_SECRET` (section 13, Table 18; stream-consumers `75a87fd`): reading permission only (the live probe fails if trading or withdrawals are enabled); refused when damaged or missing. A first key sent without a secret was recognised at 02:22 UTC, then refused on every call from ~02:35 UTC, and is not stored. Re-test of all keys: 34 passed, 1 skipped. |
| 2026-10-19 01:40 | Bitso private API key and secret set as held keys `BITSO_API_KEY` + `BITSO_API_SECRET` (section 12, Table 17; stream-consumers `66c07da`): valid, refused without or damaged; not needed by the `bitso` stream (public WebSocket, 35.5 events/s). Re-test of all keys: 33 passed, 1 skipped. |
| 2026-10-18 23:20 | Every key now in `.env` (section 11, Tables 15–16): 24 held keys added, `data/credentials/` removed, re-test of all keys passed. mastodon.world token set as a held key (`MASTODON_WORLD_ACCESS_TOKEN`), tested, own 24-hour sampling started 22:54 UTC (section 10). |
| 2026-10-18 22:45 | `gfw` removed (section 10; stream-consumers `908953b`). The social.vivaldi.net Mastodon token does not work on mastodon.world and mastodon.world's stream needs a token (Table 14); a mastodon.world token is needed to measure it. |
| 2026-10-18 17:30 | `AISSTREAM_API_KEY` set (section 9, Table 13); own 24-hour sampling started 17:20 UTC; test data replaced by a real capture. Only `entsoe` is still missing a key. |
| 2026-10-18 16:05 | `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` and `TFL_APP_KEY` set (section 8, Table 12); own 24-hour samplings started for both (TfL with a 150-s window). TfL's 0.000/s rounds explained by its 60-s shared cache; TfL no longer at risk (median 4.977/s over 20 rounds of the current run). All three optional keys are now set. |
| 2026-10-18 15:45 | `mastodon` moved to social.vivaldi.net: new `MASTODON_ACCESS_TOKEN` and `MASTODON_INSTANCE=social.vivaldi.net` (section 7, Table 11); own 24-hour sampling started 15:37 UTC; test data replaced by a masked real capture; masking of lists under a wildcard fixed. The token again has every scope (recommendation: regenerate with `read:statuses` only). |
| 2026-10-18 05:10 | `MTA_BUSTIME_KEY`, `WMATA_API_KEY` ("GTFS" product) and `MBTA_API_KEY` set (section 6, Table 10); own 24-hour samplings started for all three. `lasair` and `fink` removed (no LSST alerts since 2026-07-14). `mastodon` kept, waiting for a token from an instance with open live feeds. |
| 2026-10-18 04:50 | `NTA_API_KEY` and `MASTODON_ACCESS_TOKEN` set (section 5, Table 9). NTA: own 24-hour sampling with a 150-s window started 04:28:45 UTC; test data replaced by a real capture. Mastodon: mastodon.social has its live feeds disabled, so only deletions arrive; its sampling stopped after round 1; needs a token from another instance or removal. |
| 2026-10-18 03:55 | Lasair REST API token received and tested (section 4, Table 8); stored outside `.env`. Found: no LSST alerts in Lasair or Fink after 2026-07-14. Coinbase: no Advanced Trade source will be added (owner accepted the recommendation; Table 7). |
| 2026-10-18 03:35 | `CTA_TRAIN_KEY` and `GFW_API_TOKEN` set. CTA Train: all 8 lines → HTTP 200, `errCd` 0, 51 trains; a made-up key → HTTP 200 with `errCd` 101 "Invalid API key."; `check cta_train` 60 s ok, 100 events, 1.54/s; own 24-round sampling started 03:23:41 UTC (unit `stream-sampling-keyed-20261018`). GFW: token → HTTP 200 (172,997 fishing events overlapping the last 7 days); no token and a damaged token → HTTP 401 `{"error":"invalid token"}`; per-day totals 2026-10-04…14: fishing 39,138–53,396, encounters 2,722–4,512, loitering 66,521–107,852, port visits 202,273–372,438, and 0 for 10-15/16/17 in all four (overlap counts, upper bounds); the date filter selects events overlapping the range (one returned for 10-10…18 started 2026-05-27). Hourly total growth of the 4 datasets for 2026-09-01…11-01 started 03:24 UTC (unit `gfw-growth-20261018`, 25 snapshots). Test data for both replaced by messages captured with the keys (key values not stored; checked: each value is found only in `.env`). |
| 2026-10-18 02:50 | `CTA_BUS_KEY` replaced by a new key from the owner. Before replacing: new key `getroutes` → 125 routes; old key and a made-up key → "Invalid API access key supplied". `check cta_bus` 60 s with the new key: ok, 1,008 events, 16.44/s. The 24-hour sampling had loaded the old key at start (rounds 1–6 ok, last at 02:01 UTC), so it was restarted at 02:44 UTC between rounds to load the new key; it resumed with the 18 missing rounds (new segment, ends ~2026-10-18 19:45 UTC); its first round gave `cta_bus` ok, 16.69/s. |
| 2026-10-18 02:40 | Coinbase key moved out of `.env` to `stream-consumers/data/credentials/` (`.env` now equals the template plus values). Correction: the 16.0 trades/s side finding included a 500-trade snapshot; live-only rates added as Table 7. |
| 2026-10-18 02:10 | Coinbase CDP key received, stored in `.env`, tested (section 3): valid, view-only, not needed by any stream. |
| 2026-10-17 21:14 | Page created. `CTA_BUS_KEY` set and verified; `cta_bus` test data replaced by messages captured with the key; `cta_bus` in the 24-hour sampling from round 1. |
