# Stream consumers, key-gated sources and measurements — research record

Written 2026-10-13 18:56 CST (2026-10-14 00:56 UTC) by the streams session (`ses_ecd14c7d…`, titled "Non relational DBs Streams"). This is a historical record of the state at that time; it will not be edited. The 24-hour averages will go into a new dated record.

| Item | Value |
|---|---|
| Repository | `non-relational-dbs/stream-consumers` (GitHub, **private**, instructor-only) |
| Local clone | `/home/mavasbel/Dev/repos/ITAM/stream-consumers` |
| Branch | `main` of `stream-consumers` (its only branch). Correction 2026-10-14 01:16 UTC: the commits below were first made on a work branch of `stream-consumers` named `claude-course-recommendations` (same name as, but unrelated to, the course repository's branch); `main` was fast-forwarded to `f4af707`, so every commit hash in this record is unchanged, and the work branch was deleted |
| Commits | `8448b64` initial README · `9c37757` consumers for 54 streams · `e719191` CI pin · `f4af707` key-ready candidates and cancellation fix |
| HEAD at writing | `f4af707`, working tree clean |
| Pull request | https://github.com/non-relational-dbs/stream-consumers/pull/1 (merged into `main` at `f4af707` on 2026-10-14 01:16 UTC), comment with the `f4af707` summary: https://github.com/non-relational-dbs/stream-consumers/pull/1#issuecomment-6154053047 |
| CI | GitHub Actions `test` workflow: run 38368548940 on `e719191` success; run 38458568897 on `f4af707` success |
| This record | course repository `non-relational-dbs` (a different repository), worktree `worktrees/claude-course-streams`, branch `claude-course-streams` |
| Earlier records (unchanged) | `docs/research/2026-10-12-21-37-public-data-streams-survey.md` (`1dba0b7`), `docs/research/2026-10-12-22-41-public-data-streams-full-report.md` (`5a34175`) |

## 1. Summary

- **65 sources** in the catalog: 45 keyless (A), 6 from the project document (B), 3 with an optional free key (C) and 11 candidates (D) that need a free key nobody has configured yet.
- Every source is a module of a hexagonal Python package (split inbound/outbound ports, abstract base classes, the CLI as the only composition root).
- Credentials and settings are declared per source and read from the environment or a git-ignored `.env`; `stream-consumers keys` shows what is set without printing values and `keys --template` generates `.env.example`.
- Tests at `f4af707` (this record's runs): unit + component `871 passed in 17.71s`, coverage line `TOTAL                                                               3145      0    506      0   100%`; e2e three runs, each `6 passed in 49.20s` with 100 % of its scope; live `65 passed in 71.16s (0:01:11)`.
- A bug in `websockets` 15–17 (an `AssertionError` instead of a cancellation) made the first 54-source profile run hang; it is fixed in `f4af707` and reproduced by a test.
- The 24-hour sampling is in progress: 8 of 24 hourly rounds saved when this record was generated.
- Open: the free keys (requested from Marco), the 24-hour medians, and the student catalog.

## 2. Decisions

| Date (2026) | Decision | Source of the decision |
|---|---|---|
| 10-13 | Inclusion rule: a source is included when its **median measured rate is at least 1 event/s** (`policy.MINIMUM_RATE = 1.0`). | Marco: "Could we proceed as per your recommendations for 1 and 2 and could we keep GDELT?" |
| 10-13 | GDELT is kept although its measured median was 0.977 events/s, because the project document lists it. | same message |
| 10-13 | The 24-hour sampling is done with the repository's own tested `sample` command; the earlier `/tmp` sampler is a cross-check only and not evidence. | same message (recommendation 2) |
| 10-13 | The repository mirrors the hexagonal layout of `quizzes/query_validation` (split inbound/outbound ports). | Marco: "could we follow the same principles we follow for all repos? Hex adapter ports with split inbound outbound ports?" |
| 10-13 | Organization `non-relational-dbs` default member permission changed from `read` to `none` (read back after the change); the repository is private and must not be shared with students. | D12 of the locked plan |
| 10-13 | Two agent sessions share the course repository: this session owns only the streams work (worktree `claude-course-streams`); homeworks, labs, Canvas uploads belong to the other session (`ses_efd787940…`). | Marco approved the ownership split |
| 10-13 | Sources that need a free key are built and tested now as group D (candidate) so that adding the key to `.env` is enough; a candidate is accepted only after its own sampling gives a median of at least 1 event/s, and removed otherwise. This replaces the earlier "pending, not built" rule. | Marco: "Could we leave everything ready for the keys and config to be added to a .env?" |
| 10-13 | This record: course worktree only, streams work only, English. | Marco: "Could we proceed as per your recommendations?" |

## 3. The 65 sources

Generated from the descriptors in `src/stream_consumers/adapters/outbound/sources/` at the commit above.

### 3.1 Overview

| # | id | Source | Provider | Group | Category | Transport | Delivery | Key |
|---|---|---|---|---|---|---|---|---|
| 1 | `base_logs` | Base (L2) contract event logs (PublicNode RPC) | Allnodes (PublicNode RPC) | keyless | Finance & blockchain | websocket | push | — |
| 2 | `bitfinex` | Bitfinex trades + ticker (public v2) | Bitfinex | keyless | Finance & blockchain | websocket | push | — |
| 3 | `bitso` | Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN) | Bitso (Mexico) | keyless | Finance & blockchain | websocket | push | — |
| 4 | `bitstamp` | Bitstamp live trades | Bitstamp | keyless | Finance & blockchain | websocket | push | — |
| 5 | `bsc_logs` | BNB Smart Chain contract event logs (PublicNode RPC) | Allnodes (PublicNode RPC) | keyless | Finance & blockchain | websocket | push | — |
| 6 | `bybit` | Bybit spot tickers | Bybit | keyless | Finance & blockchain | websocket | push | — |
| 7 | `coinbase` | Coinbase Exchange ticker | Coinbase | keyless | Finance & blockchain | websocket | push | — |
| 8 | `deribit` | Deribit perpetual futures ticker | Deribit | keyless | Finance & blockchain | websocket | push | — |
| 9 | `eth_logs` | Ethereum mainnet contract event logs (PublicNode RPC) | Allnodes (PublicNode RPC) | keyless | Finance & blockchain | websocket | push | — |
| 10 | `gemini` | Gemini market data v1 (order-book changes + trades) | Gemini Trust Company | keyless | Finance & blockchain | websocket | push | — |
| 11 | `hyperliquid` | Hyperliquid trades | Hyperliquid | keyless | Finance & blockchain | websocket | push | — |
| 12 | `kraken` | Kraken trades + ticker (v2) | Kraken (Payward) | keyless | Finance & blockchain | websocket | push | — |
| 13 | `okx` | OKX public tickers | OKX | keyless | Finance & blockchain | websocket | push | — |
| 14 | `polygon_logs` | Polygon PoS contract event logs (PublicNode RPC) | Allnodes (PublicNode RPC) | keyless | Finance & blockchain | websocket | push | — |
| 15 | `polymarket` | Polymarket CLOB market channel (prediction-market prices) | Polymarket | keyless | Finance & blockchain | websocket | push | — |
| 16 | `solana` | Solana program logs (public mainnet RPC) | Solana Foundation (public mainnet-beta RPC) | keyless | Finance & blockchain | websocket | push | — |
| 17 | `xrpl` | XRP Ledger transactions | XRP Ledger Foundation (public cluster xrplcluster.com) | keyless | Finance & blockchain | websocket | push | — |
| 18 | `albion` | Albion Online Data Project market orders | Albion Online Data Project (community) | keyless | Games, media & social | nats | push | — |
| 19 | `twitch` | Twitch chat (anonymous read-only IRC) | Twitch Interactive | keyless | Games, media & social | websocket | push | — |
| 20 | `atlas` | RIPE Atlas measurement results stream (ping) | RIPE NCC | keyless | Internet & software | websocket | push | — |
| 21 | `ct` | Certificate Transparency logs (RFC 6962), read directly | Certificate Transparency log operators (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt, TrustAsia) | keyless | Internet & software | http | poll | — |
| 22 | `gharchive` | GH Archive — all public GitHub events (hourly files) | GH Archive (Ilya Grigorik) | keyless | Internet & software | http | file-drop | — |
| 23 | `npm` | npm registry replication changes | npm, Inc. (GitHub) | keyless | Internet & software | http | poll | — |
| 24 | `osm` | OpenStreetMap minutely replication diffs | OpenStreetMap Foundation | keyless | Internet & software | http | file-drop | — |
| 25 | `ris` | RIPE NCC RIS Live — global BGP routing updates | RIPE NCC | keyless | Internet & software | websocket | push | — |
| 26 | `crossref` | Crossref scholarly metadata (works indexed per day) | Crossref | keyless | Science & sensors | http | poll | — |
| 27 | `pskreporter` | PSK Reporter amateur-radio reception reports | PSK Reporter (Philip Gladstone) — MQTT feed by M0LTE | keyless | Science & sensors | mqtt | push | — |
| 28 | `rbn` | Reverse Beacon Network (CW/RTTY skimmer spots) | Reverse Beacon Network | keyless | Science & sensors | tcp | push | — |
| 29 | `seedlink` | EarthScope (IRIS) SeedLink real-time seismic waveforms | EarthScope Consortium (IRIS DMC) | keyless | Science & sensors | tcp | push | — |
| 30 | `sensorcomm` | Sensor.Community citizen air-quality sensors | Sensor.Community (OK Lab Stuttgart / Code for Germany) | keyless | Science & sensors | http | poll | — |
| 31 | `usgs_water` | USGS Water Services instantaneous values (river gauges) | U.S. Geological Survey (USGS) | keyless | Science & sensors | http | poll | — |
| 32 | `adsb_fi` | adsb.fi open data aircraft — 250 NM around Mexico City airport | adsb.fi | keyless | Transport | http | poll | — |
| 33 | `adsb_lol` | adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport | adsb.lol | keyless | Transport | http | poll | — |
| 34 | `bicing` | Bicing Barcelona bike-share station status (GBFS) | Barcelona City Council (Bicing) | keyless | Transport | http | poll | — |
| 35 | `dt_marine` | Digitraffic Finland marine AIS vessel locations | Fintraffic (Digitraffic) | keyless | Transport | mqtt | push | — |
| 36 | `dt_rail` | Digitraffic Finland train GPS locations | Fintraffic (Digitraffic) | keyless | Transport | mqtt | push | — |
| 37 | `dt_rail_trains` | Digitraffic Finland train timetables/actuals | Fintraffic (Digitraffic) | keyless | Transport | mqtt | push | — |
| 38 | `dt_road` | Digitraffic Finland road traffic (TMS) and road-weather sensors | Fintraffic (Digitraffic) | keyless | Transport | mqtt | push | — |
| 39 | `ecobici` | EcoBici CDMX bike-share station status (GBFS) | Gobierno de la Ciudad de México (EcoBici, operated by Lyft) | keyless | Transport | http | poll | — |
| 40 | `entur` | Entur Norway real-time vehicle positions | Entur AS (Norway) | keyless | Transport | http | poll | — |
| 41 | `hsl` | HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains) | Helsinki Regional Transport Authority (HSL) | keyless | Transport | mqtt | push | — |
| 42 | `mbta_gtfsrt` | MBTA Boston GTFS-Realtime VehiclePositions | Massachusetts Bay Transportation Authority (MBTA) | keyless | Transport | http | poll | — |
| 43 | `mta_gtfsrt` | MTA New York City Subway GTFS-Realtime (A/C/E feed) | Metropolitan Transportation Authority (MTA) | keyless | Transport | http | poll | — |
| 44 | `ndov` | NDOV Loket Netherlands public transport KV6 (all operators) | NDOV Loket (Netherlands) | keyless | Transport | zeromq | push | — |
| 45 | `metar` | NOAA aviationweather.gov METAR observations (global airports) | NOAA National Weather Service — Aviation Weather Center | keyless | Weather & environment | http | poll | — |
| 46 | `binance` | Binance spot trades + 24 h tickers | Binance | project document | Finance & blockchain | websocket | push | — |
| 47 | `mempool` | mempool.space — Bitcoin transactions entering the mempool | The Mempool Open Source Project (mempool.space) | project document | Finance & blockchain | websocket | push | — |
| 48 | `bluesky` | Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts) | Bluesky Social PBC | project document | Games, media & social | websocket | push | — |
| 49 | `gdelt` | GDELT 2.0 Event Database — 15-minute event exports | The GDELT Project | project document | Games, media & social | http | file-drop | — |
| 50 | `wikimedia` | Wikimedia EventStreams — recent changes on all Wikimedia wikis | Wikimedia Foundation | project document | Internet & software | sse | push | — |
| 51 | `opensky` | OpenSky Network state vectors — aircraft over Mexico | OpenSky Network | project document | Transport | http | poll | optional |
| 52 | `mbta_v3` | MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry) | Massachusetts Bay Transportation Authority (MBTA) | free key (optional) | Transport | http | poll | optional |
| 53 | `tfl` | Transport for London Unified API — Tube arrival predictions | Transport for London (TfL) | free key (optional) | Transport | http | poll | optional |
| 54 | `firms` | NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files | NASA Earth Science Data Systems (LANCE FIRMS) | free key (optional) | Weather & environment | http | poll | — |
| 55 | `mastodon` | Mastodon federated public timeline (statuses, edits, deletions) | Mastodon (default instance mastodon.social, Mastodon gGmbH) | candidate (key required) | Games, media & social | sse | push | required |
| 56 | `fink` | Fink — Rubin Observatory LSST and ZTF alert livestream | Fink broker (CNRS/IN2P3 and partners) | candidate (key required) | Science & sensors | kafka | push | required |
| 57 | `lasair` | Lasair — Rubin Observatory LSST alerts that pass your saved filter | Lasair (Universities of Edinburgh and Belfast) | candidate (key required) | Science & sensors | kafka | push | required |
| 58 | `aisstream` | aisstream.io — global AIS ship positions and static data | aisstream.io | candidate (key required) | Transport | websocket | push | required |
| 59 | `cta_bus` | CTA Bus Tracker vehicles — every Chicago bus | Chicago Transit Authority (CTA) | candidate (key required) | Transport | http | poll | required |
| 60 | `cta_train` | CTA Train Tracker locations — every Chicago 'L' train | Chicago Transit Authority (CTA) | candidate (key required) | Transport | http | poll | required |
| 61 | `gfw` | Global Fishing Watch events API — fishing, encounter, loitering and port-visit events | Global Fishing Watch | candidate (key required) | Transport | http | poll | required |
| 62 | `mta_bustime` | MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus | Metropolitan Transportation Authority (MTA) | candidate (key required) | Transport | http | poll | required |
| 63 | `nta` | NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland | National Transport Authority (NTA), Ireland | candidate (key required) | Transport | http | poll | required |
| 64 | `wmata` | WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail | Washington Metropolitan Area Transit Authority (WMATA) | candidate (key required) | Transport | http | poll | required |
| 65 | `entsoe` | ENTSO-E Transparency Platform — actual electricity generation per production type | European Network of Transmission System Operators for Electricity (ENTSO-E) | candidate (key required) | Weather & environment | http | poll | required |

### 3.2 Detail per source

#### `base_logs` — Base (L2) contract event logs (PublicNode RPC)

| Field | Value |
|---|---|
| Provider | Allnodes (PublicNode RPC) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://base-rpc.publicnode.com` |
| Documentation | https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub |
| Terms | https://www.publicnode.com/ |

#### `bitfinex` — Bitfinex trades + ticker (public v2)

| Field | Value |
|---|---|
| Provider | Bitfinex |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://api-pub.bitfinex.com/ws/2` |
| Documentation | https://docs.bitfinex.com/docs/ws-public |
| Terms | https://docs.bitfinex.com/docs/ws-public |

#### `bitso` — Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)

| Field | Value |
|---|---|
| Provider | Bitso (Mexico) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws.bitso.com` |
| Documentation | https://docs.bitso.com/bitso-api/docs |
| Terms | https://docs.bitso.com/bitso-api/docs |

#### `bitstamp` — Bitstamp live trades

| Field | Value |
|---|---|
| Provider | Bitstamp |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws.bitstamp.net` |
| Documentation | https://www.bitstamp.net/websocket/v2/ |
| Terms | https://www.bitstamp.net/websocket/v2/ |

#### `bsc_logs` — BNB Smart Chain contract event logs (PublicNode RPC)

| Field | Value |
|---|---|
| Provider | Allnodes (PublicNode RPC) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://bsc-rpc.publicnode.com` |
| Documentation | https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub |
| Terms | https://www.publicnode.com/ |

#### `bybit` — Bybit spot tickers

| Field | Value |
|---|---|
| Provider | Bybit |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://stream.bybit.com/v5/public/spot` |
| Documentation | https://bybit-exchange.github.io/docs/v5/websocket/public/ticker |
| Terms | https://bybit-exchange.github.io/docs/v5/websocket/public/ticker |

#### `coinbase` — Coinbase Exchange ticker

| Field | Value |
|---|---|
| Provider | Coinbase |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws-feed.exchange.coinbase.com` |
| Documentation | https://docs.cdp.coinbase.com/exchange/websocket-feed/overview |
| Terms | https://docs.cdp.coinbase.com/exchange/websocket-feed/overview |

#### `deribit` — Deribit perpetual futures ticker

| Field | Value |
|---|---|
| Provider | Deribit |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://www.deribit.com/ws/api/v2` |
| Documentation | https://docs.deribit.com/ |
| Terms | https://docs.deribit.com/ |

#### `eth_logs` — Ethereum mainnet contract event logs (PublicNode RPC)

| Field | Value |
|---|---|
| Provider | Allnodes (PublicNode RPC) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ethereum-rpc.publicnode.com` |
| Documentation | https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub |
| Terms | https://www.publicnode.com/ |

#### `gemini` — Gemini market data v1 (order-book changes + trades)

| Field | Value |
|---|---|
| Provider | Gemini Trust Company |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://api.gemini.com/v1/marketdata/{BTCUSD,ETHUSD,SOLUSD}` |
| Documentation | https://developer.gemini.com/websocket/streams.md |
| Terms | https://developer.gemini.com/websocket/streams.md |
| Notes | One connection per symbol, read concurrently. |

#### `hyperliquid` — Hyperliquid trades

| Field | Value |
|---|---|
| Provider | Hyperliquid |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://api.hyperliquid.xyz/ws` |
| Documentation | https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions |
| Terms | https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions |
| Personal fields (masked) | `users` |

#### `kraken` — Kraken trades + ticker (v2)

| Field | Value |
|---|---|
| Provider | Kraken (Payward) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws.kraken.com/v2` |
| Documentation | https://docs.kraken.com/api/docs/websocket-v2/trade |
| Terms | https://docs.kraken.com/api/docs/websocket-v2/trade |

#### `okx` — OKX public tickers

| Field | Value |
|---|---|
| Provider | OKX |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws.okx.com:8443/ws/v5/public` |
| Documentation | https://www.okx.com/docs-v5/en/ |
| Terms | https://www.okx.com/docs-v5/en/ |

#### `polygon_logs` — Polygon PoS contract event logs (PublicNode RPC)

| Field | Value |
|---|---|
| Provider | Allnodes (PublicNode RPC) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://polygon-bor-rpc.publicnode.com` |
| Documentation | https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub |
| Terms | https://www.publicnode.com/ |

#### `polymarket` — Polymarket CLOB market channel (prediction-market prices)

| Field | Value |
|---|---|
| Provider | Polymarket |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ws-subscriptions-clob.polymarket.com/ws/market` |
| Documentation | https://docs.polymarket.com/developers/CLOB/websocket/market-channel |
| Terms | https://docs.polymarket.com/developers/CLOB/websocket/market-channel |
| Notes | Subscribes to the 25 markets with the highest 24 h volume. |

#### `solana` — Solana program logs (public mainnet RPC)

| Field | Value |
|---|---|
| Provider | Solana Foundation (public mainnet-beta RPC) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://api.mainnet-beta.solana.com` |
| Documentation | https://solana.com/docs/rpc/websocket/logssubscribe |
| Terms | https://solana.com/docs/references/clusters |

#### `xrpl` — XRP Ledger transactions

| Field | Value |
|---|---|
| Provider | XRP Ledger Foundation (public cluster xrplcluster.com) |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://xrplcluster.com/` |
| Documentation | https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe |
| Terms | https://xrpl.org/docs/tutorials/public-servers |

#### `albion` — Albion Online Data Project market orders

| Field | Value |
|---|---|
| Provider | Albion Online Data Project (community) |
| Group | keyless |
| Transport / delivery | nats / push |
| Endpoint | `nats://nats.albion-online-data.com:4222` |
| Documentation | https://www.albion-online-data.com/ |
| Terms | https://github.com/ao-data/albiondata-client |
| Notes | Public credentials published by the project (user public). |

#### `twitch` — Twitch chat (anonymous read-only IRC)

| Field | Value |
|---|---|
| Provider | Twitch Interactive |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://irc-ws.chat.twitch.tv:443` |
| Documentation | https://dev.twitch.tv/docs/chat/irc/ |
| Terms | https://legal.twitch.com/legal/developer-agreement/ |
| Personal fields (masked) | `display-name`, `user-id`, `id`, `client-nonce`, `message`, `reply-*`, `room-id` |
| Notes | Anonymous read-only login (justinfan nick) to 12 large Spanish- and English-language channels. Chat contains personal content. |

#### `atlas` — RIPE Atlas measurement results stream (ping)

| Field | Value |
|---|---|
| Provider | RIPE NCC |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://atlas-stream.ripe.net/stream/?client=itam-com22102-stream-consumers` |
| Documentation | https://atlas.ripe.net/docs/apis/streaming-api |
| Terms | https://atlas.ripe.net/legal/terms-conditions/ |

#### `ct` — Certificate Transparency logs (RFC 6962), read directly

| Field | Value |
|---|---|
| Provider | Certificate Transparency log operators (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt, TrustAsia) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `<log url>/ct/v1/get-sth, /ct/v1/get-entries (log list https://www.gstatic.com/ct/log_list/v3/log_list.json)` |
| Documentation | https://www.rfc-editor.org/rfc/rfc6962 |
| Terms | https://www.rfc-editor.org/rfc/rfc6962 |
| Notes | Rate = growth of all usable RFC 6962 logs (static-CT logs are not read). Events are the parsed certificates; a log growing faster than 1,024 entries per 10 s poll is skipped ahead. |

#### `gharchive` — GH Archive — all public GitHub events (hourly files)

| Field | Value |
|---|---|
| Provider | GH Archive (Ilya Grigorik) |
| Group | keyless |
| Transport / delivery | http / file-drop |
| Endpoint | `https://data.gharchive.org/YYYY-MM-DD-H.json.gz` |
| Documentation | https://www.gharchive.org/ |
| Terms | https://www.gharchive.org/ |
| Personal fields (masked) | `actor.login`, `actor.display_login`, `actor.avatar_url`, `actor.url`, `actor.gravatar_id`, `actor.id`, `payload.*` |
| Notes | One file per UTC hour; rate = events in the newest complete hour / 3,600 s. |

#### `npm` — npm registry replication changes

| Field | Value |
|---|---|
| Provider | npm, Inc. (GitHub) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://replicate.npmjs.com/registry/_changes` |
| Documentation | https://github.com/npm/registry-follower-tutorial |
| Terms | https://docs.npmjs.com/policies/open-source-terms |
| Minimum interval between requests | 5 s |
| Notes | Changes feed followed every 5 s. The feed returns each changed package once per request, so several updates of one package between polls count once. |

#### `osm` — OpenStreetMap minutely replication diffs

| Field | Value |
|---|---|
| Provider | OpenStreetMap Foundation |
| Group | keyless |
| Transport / delivery | http / file-drop |
| Endpoint | `https://planet.openstreetmap.org/replication/minute/` |
| Documentation | https://wiki.openstreetmap.org/wiki/Planet.osm/diffs |
| Terms | https://www.openstreetmap.org/copyright |
| Personal fields (masked) | `user`, `uid` |
| Notes | One osmChange file per minute; rate = elements in the newest file / 60 s. |

#### `ris` — RIPE NCC RIS Live — global BGP routing updates

| Field | Value |
|---|---|
| Provider | RIPE NCC |
| Group | keyless |
| Transport / delivery | websocket / push |
| Endpoint | `wss://ris-live.ripe.net/v1/ws/?client=itam-com22102-stream-consumers` |
| Documentation | https://ris-live.ripe.net/manual/ |
| Terms | https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions |

#### `crossref` — Crossref scholarly metadata (works indexed per day)

| Field | Value |
|---|---|
| Provider | Crossref |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://api.crossref.org/works?filter=from-index-date:<today>&sort=indexed&order=desc` |
| Documentation | https://www.crossref.org/documentation/retrieve-metadata/rest-api/ |
| Terms | https://www.crossref.org/documentation/retrieve-metadata/rest-api/ |
| Minimum interval between requests | 60 s |
| Setting `CROSSREF_MAILTO` | default `` — Contact e-mail sent as mailto= to join Crossref's polite pool (optional). |
| Personal fields (masked) | `author`, `editor` |
| Notes | Rate = works (re)indexed on the previous UTC day / 86,400 s; most are updates of existing records, not new publications. |

#### `pskreporter` — PSK Reporter amateur-radio reception reports

| Field | Value |
|---|---|
| Provider | PSK Reporter (Philip Gladstone) — MQTT feed by M0LTE |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `mqtt://mqtt.pskreporter.info:1883` |
| Documentation | https://www.mqtt.pskreporter.info/ |
| Terms | https://www.mqtt.pskreporter.info/ |
| Personal fields (masked) | `sc`, `rc`, `sl`, `rl` |

#### `rbn` — Reverse Beacon Network (CW/RTTY skimmer spots)

| Field | Value |
|---|---|
| Provider | Reverse Beacon Network |
| Group | keyless |
| Transport / delivery | tcp / push |
| Endpoint | `telnet://telnet.reversebeacon.net:7000` |
| Documentation | https://www.reversebeacon.net/ |
| Terms | https://www.reversebeacon.net/ |
| Personal fields (masked) | `spotter`, `dx` |
| Notes | Telnet login asks for a callsign; N0CALL (the conventional placeholder) is sent. |

#### `seedlink` — EarthScope (IRIS) SeedLink real-time seismic waveforms

| Field | Value |
|---|---|
| Provider | EarthScope Consortium (IRIS DMC) |
| Group | keyless |
| Transport / delivery | tcp / push |
| Endpoint | `seedlink://rtserve.iris.washington.edu:18000` |
| Documentation | https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ |
| Terms | https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ |
| Notes | 12 IU stations, vertical broadband channel BHZ; the rate grows with the stations selected. |

#### `sensorcomm` — Sensor.Community citizen air-quality sensors

| Field | Value |
|---|---|
| Provider | Sensor.Community (OK Lab Stuttgart / Code for Germany) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://data.sensor.community/static/v2/data.json` |
| Documentation | https://github.com/opendata-stuttgart/meta/wiki/EN-APIs |
| Terms | https://sensor.community/en/ |
| Minimum interval between requests | 150 s |
| Notes | All sensors, last 5 minutes, polled every 150 s; an event is a new measurement id. |

#### `usgs_water` — USGS Water Services instantaneous values (river gauges)

| Field | Value |
|---|---|
| Provider | U.S. Geological Survey (USGS) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H&siteStatus=active` |
| Documentation | https://waterservices.usgs.gov/ |
| Terms | https://waterservices.usgs.gov/ |
| Minimum interval between requests | 300 s |
| Notes | Texas only. Values of the last hour, polled every 5 min; an event is a new value. The provider announces this legacy service retires on 2027-02-22. |

#### `adsb_fi` — adsb.fi open data aircraft — 250 NM around Mexico City airport

| Field | Value |
|---|---|
| Provider | adsb.fi |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250` |
| Documentation | https://github.com/adsbfi/opendata |
| Terms | https://raw.githubusercontent.com/adsbfi/opendata/main/README.md |
| Minimum interval between requests | 5 s |
| Notes | Aircraft within 250 NM of Mexico City airport (AICM), polled every 5 s; an event is an aircraft whose position, altitude, speed or track changed. |

#### `adsb_lol` — adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport

| Field | Value |
|---|---|
| Provider | adsb.lol |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://api.adsb.lol/v2/point/19.436/-99.072/250` |
| Documentation | https://www.adsb.lol/docs/open-data/api/ |
| Terms | https://www.adsb.lol/docs/open-data/api/ |
| Minimum interval between requests | 15 s |
| Notes | Aircraft within 250 NM of Mexico City airport (AICM), polled every 15 s; an event is an aircraft whose position, altitude, speed or track changed. |

#### `bicing` — Bicing Barcelona bike-share station status (GBFS)

| Field | Value |
|---|---|
| Provider | Barcelona City Council (Bicing) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status` |
| Documentation | https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing |
| Terms | https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing |
| Minimum interval between requests | 10 s |
| Notes | GBFS station_status polled every 10 s; an event is a station whose report time, bikes or docks changed. |

#### `dt_marine` — Digitraffic Finland marine AIS vessel locations

| Field | Value |
|---|---|
| Provider | Fintraffic (Digitraffic) |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `wss://meri.digitraffic.fi:443/mqtt` |
| Documentation | https://www.digitraffic.fi/en/marine-traffic/ |
| Terms | https://www.digitraffic.fi/en/terms-of-service/ |
| Notes | Topic segments mmsi are copied into each event. |

#### `dt_rail` — Digitraffic Finland train GPS locations

| Field | Value |
|---|---|
| Provider | Fintraffic (Digitraffic) |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `wss://rata.digitraffic.fi:443/mqtt` |
| Documentation | https://www.digitraffic.fi/en/railway-traffic/ |
| Terms | https://www.digitraffic.fi/en/terms-of-service/ |

#### `dt_rail_trains` — Digitraffic Finland train timetables/actuals

| Field | Value |
|---|---|
| Provider | Fintraffic (Digitraffic) |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `wss://rata.digitraffic.fi:443/mqtt` |
| Documentation | https://www.digitraffic.fi/en/railway-traffic/ |
| Terms | https://www.digitraffic.fi/en/terms-of-service/ |

#### `dt_road` — Digitraffic Finland road traffic (TMS) and road-weather sensors

| Field | Value |
|---|---|
| Provider | Fintraffic (Digitraffic) |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `wss://tie.digitraffic.fi:443/mqtt` |
| Documentation | https://www.digitraffic.fi/en/road-traffic/ |
| Terms | https://www.digitraffic.fi/en/terms-of-service/ |
| Notes | Topic segments feed, stationId, sensorId are copied into each event. |

#### `ecobici` — EcoBici CDMX bike-share station status (GBFS)

| Field | Value |
|---|---|
| Provider | Gobierno de la Ciudad de México (EcoBici, operated by Lyft) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json` |
| Documentation | https://ecobici.cdmx.gob.mx/datos-abiertos/ |
| Terms | https://ecobici.cdmx.gob.mx/datos-abiertos/ |
| Minimum interval between requests | 10 s |
| Notes | GBFS station_status polled every 10 s; an event is a station whose report time, bikes or docks changed. |

#### `entur` — Entur Norway real-time vehicle positions

| Field | Value |
|---|---|
| Provider | Entur AS (Norway) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://api.entur.io/realtime/v2/vehicles/graphql` |
| Documentation | https://developer.entur.org/pages-real-time-intro |
| Terms | https://developer.entur.org/pages-intro-setup-and-access/ |
| Minimum interval between requests | 15 s |
| Notes | GraphQL query polled every 15 s with the identifying ET-Client-Name header Entur requires; an event is a vehicle whose lastUpdated changed. |

#### `hsl` — HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)

| Field | Value |
|---|---|
| Provider | Helsinki Regional Transport Authority (HSL) |
| Group | keyless |
| Transport / delivery | mqtt / push |
| Endpoint | `wss://mqtt.hsl.fi:443/` |
| Documentation | https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md |
| Terms | https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md |

#### `mbta_gtfsrt` — MBTA Boston GTFS-Realtime VehiclePositions

| Field | Value |
|---|---|
| Provider | Massachusetts Bay Transportation Authority (MBTA) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://cdn.mbta.com/realtime/VehiclePositions.pb` |
| Documentation | https://www.mbta.com/developers/gtfs-realtime |
| Terms | https://www.mbta.com/developers/gtfs-realtime |
| Minimum interval between requests | 15 s |
| Notes | GTFS-Realtime feed polled every 15 s; an event is a feed entity that is new or changed. |

#### `mta_gtfsrt` — MTA New York City Subway GTFS-Realtime (A/C/E feed)

| Field | Value |
|---|---|
| Provider | Metropolitan Transportation Authority (MTA) |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace` |
| Documentation | https://api.mta.info/ |
| Terms | https://www.mta.info/developers |
| Minimum interval between requests | 15 s |
| Notes | GTFS-Realtime feed polled every 15 s; an event is a feed entity that is new or changed. |

#### `ndov` — NDOV Loket Netherlands public transport KV6 (all operators)

| Field | Value |
|---|---|
| Provider | NDOV Loket (Netherlands) |
| Group | keyless |
| Transport / delivery | zeromq / push |
| Endpoint | `tcp://pubsub.besteffort.ndovloket.nl:7658` |
| Documentation | https://ndovloket.nl/ |
| Terms | https://ndovloket.nl/ |
| Notes | Best-effort relay; all operators and all envelopes. |

#### `metar` — NOAA aviationweather.gov METAR observations (global airports)

| Field | Value |
|---|---|
| Provider | NOAA National Weather Service — Aviation Weather Center |
| Group | keyless |
| Transport / delivery | http / poll |
| Endpoint | `https://aviationweather.gov/data/cache/metars.cache.csv.gz` |
| Documentation | https://aviationweather.gov/data/api/ |
| Terms | https://aviationweather.gov/data/api/ |
| Minimum interval between requests | 60 s |
| Notes | Cache file of the latest METAR per station, polled every 60 s; an event is a new observation; rate = observations stamped within the last hour / 3,600 s. |

#### `binance` — Binance spot trades + 24 h tickers

| Field | Value |
|---|---|
| Provider | Binance |
| Group | project document |
| Transport / delivery | websocket / push |
| Endpoint | `wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade/btcusdt@ticker/ethusdt@ticker` |
| Documentation | https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md |
| Terms | https://www.binance.com/en/terms |
| Notes | The terms page is served behind a JavaScript challenge (HTTP 202 to scripts) and could not be machine-verified. |

#### `mempool` — mempool.space — Bitcoin transactions entering the mempool

| Field | Value |
|---|---|
| Provider | The Mempool Open Source Project (mempool.space) |
| Group | project document |
| Transport / delivery | websocket / push |
| Endpoint | `wss://mempool.space/api/v1/ws` |
| Documentation | https://mempool.space/docs/api/websocket |
| Terms | https://mempool.space/terms-of-service |

#### `bluesky` — Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts)

| Field | Value |
|---|---|
| Provider | Bluesky Social PBC |
| Group | project document |
| Transport / delivery | websocket / push |
| Endpoint | `wss://jetstream2.us-east.bsky.network/subscribe` |
| Documentation | https://github.com/bluesky-social/jetstream |
| Terms | https://bsky.social/about/support/tos |
| Personal fields (masked) | `did`, `commit.record.text`, `commit.record.subject*`, `commit.record.reply.*`, `commit.record.displayName`, `commit.record.description`, `commit.record.embed*`, `commit.record.facets` |

#### `gdelt` — GDELT 2.0 Event Database — 15-minute event exports

| Field | Value |
|---|---|
| Provider | The GDELT Project |
| Group | project document |
| Transport / delivery | http / file-drop |
| Endpoint | `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` |
| Documentation | https://www.gdeltproject.org/data.html |
| Terms | https://www.gdeltproject.org/about.html |
| Notes | One event export every 15 minutes; rate = rows in the newest export / 900 s. Measured median 0.977 events/s, kept because the project document lists it. Column names: https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf |

#### `wikimedia` — Wikimedia EventStreams — recent changes on all Wikimedia wikis

| Field | Value |
|---|---|
| Provider | Wikimedia Foundation |
| Group | project document |
| Transport / delivery | sse / push |
| Endpoint | `https://stream.wikimedia.org/v2/stream/recentchange` |
| Documentation | https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service |
| Terms | https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use |
| Personal fields (masked) | `user`, `performer.*` |

#### `opensky` — OpenSky Network state vectors — aircraft over Mexico

| Field | Value |
|---|---|
| Provider | OpenSky Network |
| Group | project document |
| Transport / delivery | http / poll |
| Endpoint | `https://opensky-network.org/api/states/all?lamin=14&lomin=-118&lamax=33&lomax=-86` |
| Documentation | https://openskynetwork.github.io/opensky-api/rest.html |
| Terms | https://opensky-network.org/about/terms-of-use |
| Minimum interval between requests | 30 s |
| Credential | `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` (optional) |
| Sign-up | https://opensky-network.org/my-opensky/account |
| How to get it | OpenSky account → Account page → create an API client (its id ends in -api-client) and copy client_id and client_secret. |
| Setting `OPENSKY_POLL_SECONDS` | default `30` — Seconds between requests. This box costs 4 credits per request: anonymous 400 credits/day, standard account 4,000/day. |
| Notes | Without credentials: anonymous access, 400 credits per day. With an API client: OAuth 2 client credentials (token valid 30 minutes) and 4,000 credits per day. This bounding box (19° x 32° = 608 sq°) costs 4 credits per request, so polling every 30 s suits short sampling windows only; continuous reading needs OPENSKY_POLL_SECONDS of about 90 (account) or 870 (anonymous). An event is an aircraft whose position time or last contact changed. The terms require a written agreement for 'operational' REST API use, including automated systems, even non-profit ones. |

#### `mbta_v3` — MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)

| Field | Value |
|---|---|
| Provider | Massachusetts Bay Transportation Authority (MBTA) |
| Group | free key (optional) |
| Transport / delivery | http / poll |
| Endpoint | `https://api-v3.mbta.com/vehicles` |
| Documentation | https://www.mbta.com/developers/v3-api |
| Terms | https://www.mbta.com/developers/v3-api |
| Minimum interval between requests | 20 s |
| Credential | `MBTA_API_KEY` (optional) |
| Sign-up | https://api-v3.mbta.com/register |
| How to get it | V3 API portal account; request a key per application ('Getting a key might take a day'). |
| Notes | Without a key: polled every 20 s (20 requests per minute); an event is a vehicle whose updated_at changed. With MBTA_API_KEY: the vehicles stream over server-sent events (streaming requires a key; a stream counts once against the 1,000 requests per minute); events are reset, add, update and remove. |

#### `tfl` — Transport for London Unified API — Tube arrival predictions

| Field | Value |
|---|---|
| Provider | Transport for London (TfL) |
| Group | free key (optional) |
| Transport / delivery | http / poll |
| Endpoint | `https://api.tfl.gov.uk/Mode/tube/Arrivals` |
| Documentation | https://api-portal.tfl.gov.uk/ |
| Terms | https://api-portal.tfl.gov.uk/ |
| Minimum interval between requests | 30 s |
| Credential | `TFL_APP_KEY` (optional) |
| Sign-up | https://api-portal.tfl.gov.uk/signup |
| How to get it | API portal account, then create a subscription for the '500 requests' data plan. |
| Notes | Answers without a key (measured 2026-10-13); TFL_APP_KEY is sent as app_key when set. Polled every 30 s; an event is an arrival prediction that is new or whose expected arrival or current location changed. |

#### `firms` — NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files

| Field | Value |
|---|---|
| Provider | NASA Earth Science Data Systems (LANCE FIRMS) |
| Group | free key (optional) |
| Transport / delivery | http / poll |
| Endpoint | `https://firms.modaps.eosdis.nasa.gov/data/active_fire/<sensor>/csv/<file>_Global_24h.csv` |
| Documentation | https://firms.modaps.eosdis.nasa.gov/active_fire/ |
| Terms | https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance |
| Minimum interval between requests | 900 s |
| Notes | Reads the keyless public 24 h files (VIIRS NOAA-20, NOAA-21, S-NPP and MODIS), polled every 15 min; the MAP_KEY API serves the same products by area and is not needed. An event is a new detection. |

#### `mastodon` — Mastodon federated public timeline (statuses, edits, deletions)

| Field | Value |
|---|---|
| Provider | Mastodon (default instance mastodon.social, Mastodon gGmbH) |
| Group | candidate (key required) |
| Transport / delivery | sse / push |
| Endpoint | `https://streaming.mastodon.social/api/v1/streaming/public` |
| Documentation | https://docs.joinmastodon.org/methods/streaming/ |
| Terms | https://mastodon.social/terms-of-service |
| Credential | `MASTODON_ACCESS_TOKEN` (required) |
| Sign-up | https://mastodon.social/auth/sign_up |
| How to get it | A user account on the instance, then a user access token with scope read:statuses (OAuth flow: https://docs.joinmastodon.org/client/token/; the web interface's Preferences → Development page is not described in the official docs). Since Mastodon 4.2 app-only tokens are refused. |
| Setting `MASTODON_INSTANCE` | default `mastodon.social` — Host name of the Mastodon instance whose federated timeline is read. |
| Personal fields (masked) | `account.*`, `content`, `text`, `spoiler_text`, `uri`, `url`, `mentions.*`, `in_reply_to_account_id`, `media_attachments.*`, `card.*`, `poll.*`, `reblog.*`, `application.*`, `quote.*` |
| Notes | Statuses are written by people: account names, content and links are personal data and are masked in stored samples. mastodon.social's community standards ban 'using automation to disrupt conversations'; this consumer only reads. |

#### `fink` — Fink — Rubin Observatory LSST and ZTF alert livestream

| Field | Value |
|---|---|
| Provider | Fink broker (CNRS/IN2P3 and partners) |
| Group | candidate (key required) |
| Transport / delivery | kafka / push |
| Endpoint | `kafka://<FINK_KAFKA_SERVERS>/<FINK_TOPICS>` |
| Documentation | https://doc.lsst.fink-broker.org/services/livestream/ |
| Terms | https://github.com/astrolabsoftware/fink-client |
| Credential | `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` (required) |
| Sign-up | https://forms.gle/2td4jysT4e9pkf889 |
| How to get it | Fill the Fink subscription form; the Fink team e-mails the Kafka server address and your group.id ('open to any scientists, but it is password protected'). |
| Setting `FINK_TOPICS` | default `fink_extragalactic_lt20mag_candidate_lsst` — Comma-separated topics (one per Fink filter; list at https://lsst.fink-portal.org/schemas). |
| Notes | Messages are schemaless Avro whose writer schema travels as JSON in the message key (fink-client 12.2 reads them the same way); image cutouts become base64 text. Fink 12.x consumers connect without SASL. The rate depends on the topics chosen. |

#### `lasair` — Lasair — Rubin Observatory LSST alerts that pass your saved filter

| Field | Value |
|---|---|
| Provider | Lasair (Universities of Edinburgh and Belfast) |
| Group | candidate (key required) |
| Transport / delivery | kafka / push |
| Endpoint | `kafka://lasair-lsst-kafka.lsst.ac.uk:9092/<LASAIR_KAFKA_TOPIC>` |
| Documentation | https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html |
| Terms | https://lasair.lsst.ac.uk/privacy |
| Credential | `LASAIR_KAFKA_TOPIC` (required) |
| Sign-up | https://lasair.lsst.ac.uk/ |
| How to get it | Create a Lasair account (e-mail), build and save a filter with Kafka streaming enabled; its topic is 'lasair_' + your user ID + the sanitised filter name. The Kafka server itself needs no password. |
| Setting `LASAIR_KAFKA_SERVER` | default `lasair-lsst-kafka.lsst.ac.uk:9092` — Kafka bootstrap server (the official notebook's 'prod' value). |
| Setting `LASAIR_GROUP_ID` | default `stream-consumers` — Kafka consumer group; Lasair remembers per group where delivery stopped, so use your own. |
| Notes | JSON messages: the filter's selected fields plus UTC, optionally an `alert` object with the light curve. Lasair keeps topic messages for 7 days. The rate depends entirely on the filter you save. No terms-of-use or data licence page was found (only the privacy statement); Lasair asks users to cite Williams et al., RAS Techniques and Instruments. |

#### `aisstream` — aisstream.io — global AIS ship positions and static data

| Field | Value |
|---|---|
| Provider | aisstream.io |
| Group | candidate (key required) |
| Transport / delivery | websocket / push |
| Endpoint | `wss://stream.aisstream.io/v0/stream` |
| Documentation | https://aisstream.io/documentation |
| Terms | https://aisstream.io/privacypolicy |
| Credential | `AISSTREAM_API_KEY` (required) |
| Sign-up | https://aisstream.io/account |
| How to get it | Sign in with GitHub on the Account page and create an API key (shown once; server-side use only). |
| Setting `AISSTREAM_BOUNDING_BOXES` | default `[[[-90, -180], [90, 180]]]` — JSON list of boxes, each two [latitude, longitude] corners (default: the whole world). |
| Notes | Listed in the project document. The subscription (key + boxes) is sent right after connecting; the server closes connections without a valid subscription within 3 seconds. Limits: 3 connections per account and per IP, frames dropped for slow readers. No terms of use are published (only a privacy policy). |

#### `cta_bus` — CTA Bus Tracker vehicles — every Chicago bus

| Field | Value |
|---|---|
| Provider | Chicago Transit Authority (CTA) |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://www.ctabustracker.com/bustime/api/v3/getvehicles?key=<CTA_BUS_KEY>&rt=<up to 10 routes>&format=json` |
| Documentation | https://www.transitchicago.com/developers/bustracker/ |
| Terms | https://www.transitchicago.com/developers/terms/ |
| Minimum interval between requests | 30 s |
| Credential | `CTA_BUS_KEY` (required) |
| Sign-up | https://www.ctabustracker.com/bustime/login.jsp |
| How to get it | Create and activate a Bus Tracker account, then My Account → Developer API → apply; the key is e-mailed after approval (one key per account). |
| Notes | Reads the route list once, then polls getvehicles every 30 s with 10 routes per request (about 13 requests per poll, about 37,000 a day, under the documented 100,000). An event is a bus whose timestamp or position changed. |

#### `cta_train` — CTA Train Tracker locations — every Chicago 'L' train

| Field | Value |
|---|---|
| Provider | Chicago Transit Authority (CTA) |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=<CTA_TRAIN_KEY>&rt=<line>&outputType=JSON` |
| Documentation | https://www.transitchicago.com/developers/traintracker/ |
| Terms | https://www.transitchicago.com/developers/terms/ |
| Minimum interval between requests | 30 s |
| Credential | `CTA_TRAIN_KEY` (required) |
| Sign-up | https://www.transitchicago.com/developers/traintrackerapply/ |
| How to get it | Application form (name, address, e-mail, phone, purpose); CTA reviews it and replies. |
| Notes | One request per line (Red, Blue, Brn, G, Org, P, Pink, Y) every 30 s = 23,040 requests a day, under the documented 50,000. An event is a train (route + run number) whose prediction time or position changed. |

#### `gfw` — Global Fishing Watch events API — fishing, encounter, loitering and port-visit events

| Field | Value |
|---|---|
| Provider | Global Fishing Watch |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest&start-date=<YYYY-MM-DD>&end-date=<YYYY-MM-DD>&limit=100&offset=<n>` |
| Documentation | https://globalfishingwatch.org/our-apis/documentation |
| Terms | https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits |
| Minimum interval between requests | 900 s |
| Credential | `GFW_API_TOKEN` (required) |
| Sign-up | https://globalfishingwatch.org/our-apis/ |
| How to get it | Global Fishing Watch account, then request an API token (self-service; up to 5 tokens, they do not expire). Non-commercial use only. |
| Setting `GFW_DATASET` | default `public-global-fishing-events:latest` — Events dataset (fishing, encounters, loitering or port visits). |
| Setting `GFW_LOOKBACK_DAYS` | default `7` — Days back from today whose events are read at every poll. |
| Setting `GFW_PAGES` | default `5` — Pages of 100 events read at every poll. |
| Notes | A query API, not a push stream: events are derived from AIS and published after processing, so new events appear in batches. Polled every 15 min (limits: 50,000 requests a day, 1,500,000 a month per user). Data licence CC BY-NC 4.0; tokens must not be shared. |

#### `mta_bustime` — MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus

| Field | Value |
|---|---|
| Provider | Metropolitan Transportation Authority (MTA) |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://gtfsrt.prod.obanyc.com/vehiclePositions?key=<MTA_BUSTIME_KEY>` |
| Documentation | https://bustime.mta.info/developers/gtfs-realtime/ |
| Terms | https://www.mta.info/developers/terms-and-conditions |
| Minimum interval between requests | 30 s |
| Credential | `MTA_BUSTIME_KEY` (required) |
| Sign-up | https://register.developer.obanyc.com/ |
| How to get it | Web form (name, e-mail, project); the key arrives by e-mail 'within half an hour'. |
| Notes | The key goes in the `key` query parameter. Polled every 30 s: the Bus Time docs warn that repeated requests for all vehicles 'at less than 30 second intervals' may get the key revoked. An event is a feed entity that is new or changed. |

#### `nta` — NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland

| Field | Value |
|---|---|
| Provider | National Transport Authority (NTA), Ireland |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://api.nationaltransport.ie/gtfsr/v2/Vehicles` |
| Documentation | https://developer.nationaltransport.ie/ |
| Terms | https://developer.nationaltransport.ie/usagepolicy |
| Minimum interval between requests | 60 s |
| Credential | `NTA_API_KEY` (required) |
| Sign-up | https://developer.nationaltransport.ie/signup |
| How to get it | Developer-portal account, then subscribe to the 'GTFS Realtime' product; a pair of keys is issued (either works). |
| Notes | The key goes in the `x-api-key` header. The usage policy allows one call every 60 seconds per token, so it is polled every 60 s. The docs do not state the default response format; the decoder reads both GTFS-Realtime protobuf and its JSON mapping. An event is a feed entity that is new or changed. |

#### `wmata` — WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail

| Field | Value |
|---|---|
| Provider | Washington Metropolitan Area Transit Authority (WMATA) |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb ; https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb` |
| Documentation | https://developer.wmata.com/ |
| Terms | https://developer.wmata.com/license |
| Minimum interval between requests | 15 s |
| Credential | `WMATA_API_KEY` (required) |
| Sign-up | https://developer.wmata.com/signup |
| How to get it | Developer account (licence consent and CAPTCHA), then subscribe to a Transit Data service tier; each subscription generates two keys. |
| Notes | The key goes in the `api_key` header. Both feeds are polled every 15 s (no numeric tier limit was found on an official page). An event is a feed entity that is new or changed; `feed` says bus or rail. |

#### `entsoe` — ENTSO-E Transparency Platform — actual electricity generation per production type

| Field | Value |
|---|---|
| Provider | European Network of Transmission System Operators for Electricity (ENTSO-E) |
| Group | candidate (key required) |
| Transport / delivery | http / poll |
| Endpoint | `https://web-api.tp.entsoe.eu/api?securityToken=<ENTSOE_TOKEN>&documentType=A75&processType=A16&in_Domain=<EIC>&periodStart=<yyyyMMddHHmm>&periodEnd=<yyyyMMddHHmm>` |
| Documentation | https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API |
| Terms | https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions |
| Minimum interval between requests | 300 s |
| Credential | `ENTSOE_TOKEN` (required) |
| Sign-up | https://transparency.entsoe.eu/ |
| How to get it | Register on the Transparency Platform, then e-mail transparency@entsoe.eu asking for RESTful API access; the token is granted 'within 3 working days'. |
| Setting `ENTSOE_AREAS` | default `10Y1001A1001A83F,10YFR-RTE------C,10YES-REE------0` — Comma-separated EIC codes of the areas to read (default Germany, France, Spain; list in the platform's Area List with EIC). |
| Notes | Document A75 (actual generation per type), process A16 (realised), last 6 hours, one request per area every 5 minutes (the limit is 400 requests per minute). An event is a data point (area, production type, time) that is new or whose quantity changed. Load (6.1.A), generation (16.1.B/C) and prices (12.1.D) are not in the platform's CC BY 4.0 list: reuse follows its Terms of Use (credit the source). |

### 3.3 Sources evaluated and not included

The inclusion decision of 2026-10-13 used the rounds of the `/tmp` cross-check sampler that existed then. The table recomputes, for each source not in the catalog, the median over **all 15 rounds** of that sampler (`/tmp/opencode/streams/rounds`, 20261013T021017Z to 20261013T152353Z UTC; 60 s windows). That sampler is a cross-check tool, not repository code, so these figures explain the exclusions but are not evidence for the final list.

| id | Rounds | Rounds `ok` | Median rate of `ok` rounds (events/s) | Median attributes | Status counts | Last note |
|---|---|---|---|---|---|---|
| `airplanes_live` | 15 | 0 | — | — | rejected 15 | HTTP 403: b'{"error": "Please contact us at <e-mail masked>. Your email MUST include any links, a description of  |
| `aprs` | 15 | 15 | 0.000 | 0 | ok 15 |  |
| `bitmex` | 15 | 15 | 0.000 | 0 | ok 15 |  |
| `ena` | 15 | 15 | 0.151 | 196 | ok 15 | runs first made public 2026-10-05..2026-10-11 (7 days) |
| `github_api` | 15 | 0 | — | — | limited 15 | HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source |
| `hn` | 15 | 15 | 0.123 | 6 | ok 15 | item ids allocated over the window |
| `kystverket_ais` | 15 | 0 | — | — | error 15 |  TimeoutError('timed out') |
| `mbta_sse` | 15 | 0 | — | — | error 15 |  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\'' |
| `mlb` | 15 | 2 | 0.057 | 44 | ok 2, idle 13 | 1 games scheduled, none live at sampling time |
| `nostr` | 15 | 15 | 0.917 | 7 | ok 15 | kind-1 notes deduplicated by id across relays that accepted the connection: wss://relay.primal.net, wss://nostr.mom, wss |
| `pypi` | 15 | 15 | 0.120 | 34 | ok 15 | RSS shows the latest 100 releases (5 raw fields); attributes counted on the per-release JSON enrichment (info.*) |
| `stellar` | 15 | 15 | 0.167 | 22 | ok 15 |  |
| `velib` | 15 | 15 | 4.396 | 12 | ok 15 | 6 polls every 10s; 1519 records per snapshot; rate = new/changed records per second |
| `zkillboard` | 15 | 0 | — | — | reachable 15 | HTTP 200: b'[{"attackers":[{"alliance_id":99010105,"character_id":2119934167,"corporation_id":98712041,"damage_done":876 |

Round times of that sampler (UTC): 02:10, 02:11, 03:23, 04:23, 05:23, 06:23, 07:23, 08:23, 09:23, 10:23, 14:17, 14:18, 14:19, 14:23, 15:23. They are not evenly spaced: the sampler caught up after the host slept, so several rounds fall within minutes of each other.

**Finding — `velib` meets the threshold over all rounds.** Its median over the 15 `ok` rounds is 4.396 events/s, and 11 of 15 rounds reach 1 event/s. The decision of 2026-10-13 recorded a median of 0.983 events/s from the rounds available that morning; the four earliest rounds (0.86, 0.815, 0.926, 0.983 events/s) all ran before 04:24 UTC (06:24 in Paris, UTC+2) and each stayed below 1 event/s, while every later round reached at least 1.5 events/s. Re-including it as a source to sample over 24 hours is an open decision (section 10).

Catalog sources the `/tmp` sampler never measured (added later or measured by other tools): `aisstream`, `binance`, `bluesky`, `cta_bus`, `cta_train`, `entsoe`, `fink`, `firms`, `gdelt`, `gfw`, `mbta_v3`, `mempool`, `mta_bustime`, `nta`, `opensky`, `tfl`, `wikimedia`, `wmata`.

## 4. API keys: catalog of the 14 key-based sources

### 4.1 Configuration as documented in the repository README

Credentials and settings are read from the process environment, then from a
git-ignored `.env` file (`--env-file` changes the path). Values are never
printed, logged or written to a report.

```bash
cp .env.example .env                          # every variable the sources read, with how to get each key
uv run stream-consumers keys                  # which are set, missing (required) or not set (optional)
uv run stream-consumers check cta_train       # one source for 30 s once its key is in .env
uv run stream-consumers keys --template       # regenerates .env.example (a unit test keeps them identical)
```

A source whose required credentials are missing reports `key-pending` in `check`,
`sample` and `profile`; it never fails a run.

| Variable(s) | Source | Needed | How to get it (sign-up page) | Where it goes | Documented limit |
|---|---|---|---|---|---|
| `AISSTREAM_API_KEY` | `aisstream` | required | Sign in with GitHub on the [Account page](https://aisstream.io/account) and create a key (shown once) | `APIKey` in the first WebSocket message | 3 connections per account and per IP; frames dropped for slow readers |
| `CTA_BUS_KEY` | `cta_bus` | required | [Bus Tracker account](https://www.ctabustracker.com/bustime/login.jsp) → My Account → Developer API; e-mailed after approval | query `key` | 100,000 transactions/day |
| `CTA_TRAIN_KEY` | `cta_train` | required | [Train Tracker application form](https://www.transitchicago.com/developers/traintrackerapply/); CTA reviews it | query `key` | 50,000 requests/day |
| `ENTSOE_TOKEN` | `entsoe` | required | [Register](https://transparency.entsoe.eu/), then e-mail transparency@entsoe.eu for RESTful API access ("within 3 working days") | query `securityToken` | 400 requests/min |
| `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` | `fink` | required | [Fink subscription form](https://forms.gle/2td4jysT4e9pkf889); the team e-mails server and group id | Kafka bootstrap servers and group.id | none documented |
| `GFW_API_TOKEN` | `gfw` | required | [Global Fishing Watch account](https://globalfishingwatch.org/our-apis/), then request a token (non-commercial use) | `Authorization: Bearer` | 50,000 requests/day, 1,500,000/month |
| `LASAIR_KAFKA_TOPIC` | `lasair` | required | [Lasair account](https://lasair.lsst.ac.uk/) (e-mail), save a filter with Kafka streaming; its topic is `lasair_<user id><filter name>` | Kafka topic (the server needs no password) | none documented for Kafka |
| `MASTODON_ACCESS_TOKEN` | `mastodon` | required | [Account on the instance](https://mastodon.social/auth/sign_up), then a user token with scope `read:statuses` | `Authorization: Bearer` | 300 REST calls per 5 min; streaming not stated |
| `MTA_BUSTIME_KEY` | `mta_bustime` | required | [Web form](https://register.developer.obanyc.com/); e-mailed "within half an hour" | query `key` | no number; all-vehicle requests not under 30 s apart |
| `NTA_API_KEY` | `nta` | required | [Developer portal](https://developer.nationaltransport.ie/signup), subscribe to "GTFS Realtime" | header `x-api-key` | one call every 60 s |
| `WMATA_API_KEY` | `wmata` | required | [Developer account](https://developer.wmata.com/signup), subscribe to a Transit Data tier | header `api_key` | not published on an official page |
| `MBTA_API_KEY` | `mbta_v3` | optional | [V3 API portal](https://api-v3.mbta.com/register), one key per application ("might take a day") | header `x-api-key`; enables streaming | 1,000 requests/min (20 without a key) |
| `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` | `opensky` | optional | [OpenSky account](https://opensky-network.org/my-opensky/account) → create an API client | OAuth 2 client credentials → `Authorization: Bearer` | 4,000 credits/day (400 anonymous) |
| `TFL_APP_KEY` | `tfl` | optional | [API portal](https://api-portal.tfl.gov.uk/signup), subscribe to the "500 requests" data plan | query `app_key` | "500 requests" plan (time unit not stated) |

Settings with defaults: `AISSTREAM_BOUNDING_BOXES`, `CROSSREF_MAILTO`,
`ENTSOE_AREAS`, `FINK_TOPICS`, `GFW_DATASET`, `GFW_LOOKBACK_DAYS`, `GFW_PAGES`,
`LASAIR_KAFKA_SERVER`, `LASAIR_GROUP_ID`, `MASTODON_INSTANCE`,
`OPENSKY_POLL_SECONDS` (described in `.env.example`). NASA FIRMS needs no key:
it reads the public 24 h files.

Terms worth reading before use: OpenSky requires a written agreement for
"operational" REST API use, including automated systems, even non-profit ones;
Global Fishing Watch data is CC BY-NC 4.0 and tokens must not be shared;
aisstream.io and Lasair publish no terms of use (only privacy statements);
Mastodon statuses are personal data and are masked in stored samples.

### 4.2 Credential variables, generated from the descriptors

| Source | Group | Variable(s) | Needed | Sign-up | How to get it |
|---|---|---|---|---|---|
| `opensky` | project document | `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` | optional | https://opensky-network.org/my-opensky/account | OpenSky account → Account page → create an API client (its id ends in -api-client) and copy client_id and client_secret. |
| `mbta_v3` | free key (optional) | `MBTA_API_KEY` | optional | https://api-v3.mbta.com/register | V3 API portal account; request a key per application ('Getting a key might take a day'). |
| `tfl` | free key (optional) | `TFL_APP_KEY` | optional | https://api-portal.tfl.gov.uk/signup | API portal account, then create a subscription for the '500 requests' data plan. |
| `mastodon` | candidate (key required) | `MASTODON_ACCESS_TOKEN` | required | https://mastodon.social/auth/sign_up | A user account on the instance, then a user access token with scope read:statuses (OAuth flow: https://docs.joinmastodon.org/client/token/; the web interface's Preferences → Development page is not described in the official docs). Since Mastodon 4.2 app-only tokens are refused. |
| `fink` | candidate (key required) | `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` | required | https://forms.gle/2td4jysT4e9pkf889 | Fill the Fink subscription form; the Fink team e-mails the Kafka server address and your group.id ('open to any scientists, but it is password protected'). |
| `lasair` | candidate (key required) | `LASAIR_KAFKA_TOPIC` | required | https://lasair.lsst.ac.uk/ | Create a Lasair account (e-mail), build and save a filter with Kafka streaming enabled; its topic is 'lasair_' + your user ID + the sanitised filter name. The Kafka server itself needs no password. |
| `aisstream` | candidate (key required) | `AISSTREAM_API_KEY` | required | https://aisstream.io/account | Sign in with GitHub on the Account page and create an API key (shown once; server-side use only). |
| `cta_bus` | candidate (key required) | `CTA_BUS_KEY` | required | https://www.ctabustracker.com/bustime/login.jsp | Create and activate a Bus Tracker account, then My Account → Developer API → apply; the key is e-mailed after approval (one key per account). |
| `cta_train` | candidate (key required) | `CTA_TRAIN_KEY` | required | https://www.transitchicago.com/developers/traintrackerapply/ | Application form (name, address, e-mail, phone, purpose); CTA reviews it and replies. |
| `gfw` | candidate (key required) | `GFW_API_TOKEN` | required | https://globalfishingwatch.org/our-apis/ | Global Fishing Watch account, then request an API token (self-service; up to 5 tokens, they do not expire). Non-commercial use only. |
| `mta_bustime` | candidate (key required) | `MTA_BUSTIME_KEY` | required | https://register.developer.obanyc.com/ | Web form (name, e-mail, project); the key arrives by e-mail 'within half an hour'. |
| `nta` | candidate (key required) | `NTA_API_KEY` | required | https://developer.nationaltransport.ie/signup | Developer-portal account, then subscribe to the 'GTFS Realtime' product; a pair of keys is issued (either works). |
| `wmata` | candidate (key required) | `WMATA_API_KEY` | required | https://developer.wmata.com/signup | Developer account (licence consent and CAPTCHA), then subscribe to a Transit Data service tier; each subscription generates two keys. |
| `entsoe` | candidate (key required) | `ENTSOE_TOKEN` | required | https://transparency.entsoe.eu/ | Register on the Transparency Platform, then e-mail transparency@entsoe.eu asking for RESTful API access; the token is granted 'within 3 working days'. |

### 4.3 Provider research files

Each provider was researched on 2026-10-13 from its official pages; the files quote the pages verbatim and mark every point that could not be confirmed as **NOT VERIFIED**. They are reproduced in full in Appendix E (e-mail addresses masked except the ENTSO-E request address). Raw copies of the fetched pages are in `/tmp/opencode/streams-session/keydocs/raw/` (not committed).

| File | Covers | Bytes | SHA-256 | NOT VERIFIED items |
|---|---|---|---|---|
| `aisstream.md` | aisstream.io — key/credential documentation (fetched 2026-10-13 ~18:00 UTC) | 14312 | `006989c9703643b5…` | 5 |
| `cta.md` | CTA (Chicago) — Bus Tracker API `getvehicles` + Train Tracker Locations API `ttpositions.a | 24110 | `f0ee4168d1969064…` | 3 |
| `entsoe.md` | ENTSO-E Transparency Platform RESTful API — key facts (fetched 2026-10-13) | 20809 | `2c62e4c427185113…` | 2 |
| `fink.md` | Fink broker (LSST + ZTF) — key facts (fetched 2026-10-13) | 12728 | `5951ad48da733e48…` | 7 |
| `gfw.md` | Global Fishing Watch API v3 — key facts (fetched 2026-10-13) | 10727 | `91866ba42b8d0061…` | 2 |
| `lasair.md` | Lasair for Rubin LSST — key facts (fetched 2026-10-13) | 10058 | `8f28fcdc53bcfe81…` | 1 |
| `mastodon.md` | Mastodon streaming API — key/credential documentation (fetched 2026-10-13 ~18:15 UTC) | 22160 | `3ab4452f1153c4c8…` | 3 |
| `mbta_v3.md` | MBTA V3 API — streaming `/vehicles` (Server-Sent Events) | 14604 | `975dddf87f4b4483…` | 1 |
| `mta_bustime.md` | MTA Bus Time — SIRI VehicleMonitoring (New York City buses) | 22642 | `da6c00d732447424…` | 6 |
| `nta.md` | Ireland — National Transport Authority (NTA) GTFS-Realtime v2 `Vehicles` | 8120 | `6fced60087cde043…` | 5 |
| `opensky.md` | OpenSky Network REST API — key/credential documentation (fetched 2026-10-13 ~18:15 UTC) | 14106 | `f426b4dc788a0c86…` | 4 |
| `wmata.md` | WMATA (Washington DC) — Train Positions API + GTFS-RT bus/rail vehicle positions | 14705 | `2143f89843332547…` | 2 |

### 4.4 How each candidate behaves without a key (live check at this record's HEAD)

`stream-consumers check --seconds 30` report `check-20261014T003632Z.json` (all sources, 30 s each):

| Source | Status | Detail |
|---|---|---|
| `opensky` | ok |  |
| `mbta_v3` | ok |  |
| `tfl` | ok |  |
| `mastodon` | key-pending | missing API credentials MASTODON_ACCESS_TOKEN (free sign-up: https://mastodon.social/auth/sign_up) |
| `fink` | key-pending | missing API credentials FINK_KAFKA_SERVERS, FINK_GROUP_ID (free sign-up: https://forms.gle/2td4jysT4e9pkf889) |
| `lasair` | key-pending | missing API credentials LASAIR_KAFKA_TOPIC (free sign-up: https://lasair.lsst.ac.uk/) |
| `aisstream` | key-pending | missing API credentials AISSTREAM_API_KEY (free sign-up: https://aisstream.io/account) |
| `cta_bus` | key-pending | missing API credentials CTA_BUS_KEY (free sign-up: https://www.ctabustracker.com/bustime/login.jsp) |
| `cta_train` | key-pending | missing API credentials CTA_TRAIN_KEY (free sign-up: https://www.transitchicago.com/developers/traintrackerapply/) |
| `gfw` | key-pending | missing API credentials GFW_API_TOKEN (free sign-up: https://globalfishingwatch.org/our-apis/) |
| `mta_bustime` | key-pending | missing API credentials MTA_BUSTIME_KEY (free sign-up: https://register.developer.obanyc.com/) |
| `nta` | key-pending | missing API credentials NTA_API_KEY (free sign-up: https://developer.nationaltransport.ie/signup) |
| `wmata` | key-pending | missing API credentials WMATA_API_KEY (free sign-up: https://developer.wmata.com/signup) |
| `entsoe` | key-pending | missing API credentials ENTSOE_TOKEN (free sign-up: https://transparency.entsoe.eu/) |

Terms to read before signing up (from the research files): OpenSky requires a prior written agreement for any automated ("operational") use of its REST API, including non-profit use; Global Fishing Watch is non-commercial only (CC BY-NC 4.0), its tokens must not be shared and registration must be on behalf of an organisation; aisstream.io and Lasair publish no terms of use, only a privacy statement; ENTSO-E actual load, actual generation and day-ahead prices are not in its CC BY 4.0 free re-use list; Mastodon statuses are personal data and are masked in stored samples.

## 5. Architecture

Hexagonal (ports and adapters) with split inbound and outbound ports:

```text
src/stream_consumers/
  domain/        models, pure rules (rates, change detection, back-off, masking, field profiles), errors
  ports/
    inbound.py   use cases: ListSources, ConsumeStream, CheckSources, SampleSources, ProfileSources,
                 DescribeConfiguration
    outbound.py  Clock, SecretProvider, HttpClient, RequestAuth, Decoder, EventSource, SourceFactory,
                 SourceRegistry, EventSink, EventSinkFactory, ReportSink
  application/   one service per inbound port; depends on ports and domain only
  adapters/
    inbound/cli.py            the composition root: the only module that names concrete classes
    outbound/transports/      EventSourcePort → BaseEventSource → DecodingEventSource → Push / Poll / FileDrop,
                              and MergedEventSource; one module per transport
    outbound/decoders.py      DecoderPort → BaseDecoder → Json / Line / Csv / GtfsRealtime / AvroSchemaInKey
    outbound/auth.py          RequestAuthPort → OAuthClientCredentials
    outbound/sources/         one module per source (descriptor + decoder + factory), families in _families.py
    outbound/{http,sinks,system,registry}.py

Transports: WebSocket, SSE, MQTT, NATS, ZeroMQ, TCP, HTTP polling, file drops and
Kafka (aiokafka). `raise_if_cancelling` in `transports/base.py` stops every retry
loop when its task is being cancelled, even if a client library turns the
CancelledError into another exception (websockets 15–17 raises AssertionError
when `recv()` is cancelled while reassembling a fragmented message and another
frame is already queued; without the check a merged source never stopped).
```

`tests/unit/test_architecture.py` checks these rules on the code: the domain
imports nothing outside itself, ports and application import only the domain and
ports, every adapter and service class extends a port, and only the CLI imports
the services.

### 5.1 Files under `src/` at HEAD

```
src/stream_consumers/__init__.py
src/stream_consumers/__main__.py
src/stream_consumers/adapters/__init__.py
src/stream_consumers/adapters/inbound/__init__.py
src/stream_consumers/adapters/inbound/cli.py
src/stream_consumers/adapters/outbound/__init__.py
src/stream_consumers/adapters/outbound/auth.py
src/stream_consumers/adapters/outbound/decoders.py
src/stream_consumers/adapters/outbound/http.py
src/stream_consumers/adapters/outbound/registry.py
src/stream_consumers/adapters/outbound/sinks.py
src/stream_consumers/adapters/outbound/sources/__init__.py
src/stream_consumers/adapters/outbound/sources/_base.py
src/stream_consumers/adapters/outbound/sources/_families.py
src/stream_consumers/adapters/outbound/sources/adsb_fi.py
src/stream_consumers/adapters/outbound/sources/adsb_lol.py
src/stream_consumers/adapters/outbound/sources/aisstream.py
src/stream_consumers/adapters/outbound/sources/albion.py
src/stream_consumers/adapters/outbound/sources/atlas.py
src/stream_consumers/adapters/outbound/sources/base_logs.py
src/stream_consumers/adapters/outbound/sources/bicing.py
src/stream_consumers/adapters/outbound/sources/binance.py
src/stream_consumers/adapters/outbound/sources/bitfinex.py
src/stream_consumers/adapters/outbound/sources/bitso.py
src/stream_consumers/adapters/outbound/sources/bitstamp.py
src/stream_consumers/adapters/outbound/sources/bluesky.py
src/stream_consumers/adapters/outbound/sources/bsc_logs.py
src/stream_consumers/adapters/outbound/sources/bybit.py
src/stream_consumers/adapters/outbound/sources/coinbase.py
src/stream_consumers/adapters/outbound/sources/crossref.py
src/stream_consumers/adapters/outbound/sources/ct.py
src/stream_consumers/adapters/outbound/sources/cta_bus.py
src/stream_consumers/adapters/outbound/sources/cta_train.py
src/stream_consumers/adapters/outbound/sources/deribit.py
src/stream_consumers/adapters/outbound/sources/dt_marine.py
src/stream_consumers/adapters/outbound/sources/dt_rail.py
src/stream_consumers/adapters/outbound/sources/dt_rail_trains.py
src/stream_consumers/adapters/outbound/sources/dt_road.py
src/stream_consumers/adapters/outbound/sources/ecobici.py
src/stream_consumers/adapters/outbound/sources/entsoe.py
src/stream_consumers/adapters/outbound/sources/entur.py
src/stream_consumers/adapters/outbound/sources/eth_logs.py
src/stream_consumers/adapters/outbound/sources/fink.py
src/stream_consumers/adapters/outbound/sources/firms.py
src/stream_consumers/adapters/outbound/sources/gdelt.py
src/stream_consumers/adapters/outbound/sources/gemini.py
src/stream_consumers/adapters/outbound/sources/gfw.py
src/stream_consumers/adapters/outbound/sources/gharchive.py
src/stream_consumers/adapters/outbound/sources/hsl.py
src/stream_consumers/adapters/outbound/sources/hyperliquid.py
src/stream_consumers/adapters/outbound/sources/kraken.py
src/stream_consumers/adapters/outbound/sources/lasair.py
src/stream_consumers/adapters/outbound/sources/mastodon.py
src/stream_consumers/adapters/outbound/sources/mbta_gtfsrt.py
src/stream_consumers/adapters/outbound/sources/mbta_v3.py
src/stream_consumers/adapters/outbound/sources/mempool.py
src/stream_consumers/adapters/outbound/sources/metar.py
src/stream_consumers/adapters/outbound/sources/mta_bustime.py
src/stream_consumers/adapters/outbound/sources/mta_gtfsrt.py
src/stream_consumers/adapters/outbound/sources/ndov.py
src/stream_consumers/adapters/outbound/sources/npm.py
src/stream_consumers/adapters/outbound/sources/nta.py
src/stream_consumers/adapters/outbound/sources/okx.py
src/stream_consumers/adapters/outbound/sources/opensky.py
src/stream_consumers/adapters/outbound/sources/osm.py
src/stream_consumers/adapters/outbound/sources/polygon_logs.py
src/stream_consumers/adapters/outbound/sources/polymarket.py
src/stream_consumers/adapters/outbound/sources/pskreporter.py
src/stream_consumers/adapters/outbound/sources/rbn.py
src/stream_consumers/adapters/outbound/sources/ris.py
src/stream_consumers/adapters/outbound/sources/seedlink.py
src/stream_consumers/adapters/outbound/sources/sensorcomm.py
src/stream_consumers/adapters/outbound/sources/solana.py
src/stream_consumers/adapters/outbound/sources/tfl.py
src/stream_consumers/adapters/outbound/sources/twitch.py
src/stream_consumers/adapters/outbound/sources/usgs_water.py
src/stream_consumers/adapters/outbound/sources/wikimedia.py
src/stream_consumers/adapters/outbound/sources/wmata.py
src/stream_consumers/adapters/outbound/sources/xrpl.py
src/stream_consumers/adapters/outbound/system.py
src/stream_consumers/adapters/outbound/transports/__init__.py
src/stream_consumers/adapters/outbound/transports/base.py
src/stream_consumers/adapters/outbound/transports/http_poll.py
src/stream_consumers/adapters/outbound/transports/kafka.py
src/stream_consumers/adapters/outbound/transports/mqtt.py
src/stream_consumers/adapters/outbound/transports/nats.py
src/stream_consumers/adapters/outbound/transports/sse.py
src/stream_consumers/adapters/outbound/transports/tcp.py
src/stream_consumers/adapters/outbound/transports/websocket.py
src/stream_consumers/adapters/outbound/transports/zeromq.py
src/stream_consumers/application/__init__.py
src/stream_consumers/application/check_service.py
src/stream_consumers/application/configuration_service.py
src/stream_consumers/application/consume_service.py
src/stream_consumers/application/list_service.py
src/stream_consumers/application/profile_service.py
src/stream_consumers/application/sample_service.py
src/stream_consumers/domain/__init__.py
src/stream_consumers/domain/errors.py
src/stream_consumers/domain/models.py
src/stream_consumers/domain/policy.py
src/stream_consumers/ports/__init__.py
src/stream_consumers/ports/inbound.py
src/stream_consumers/ports/outbound.py
```

### 5.2 Commands

```bash
uv sync                                    # Python 3.13, locked dependencies
uv run stream-consumers list               # descriptors as JSON lines
uv run stream-consumers consume hsl --seconds 60 --out data/hsl.jsonl
uv run stream-consumers check              # every source for 30 s; exit 1 if any fails
uv run stream-consumers sample --rounds 24 --interval 3600 --window 60 --reports data/reports/sampling
uv run stream-consumers profile --max-events 500 --seconds 120 --out data/profile
```

Personal fields declared by each source (`personal_fields`) and any e-mail
address are masked in everything written, unless `consume --raw` is given.
Captured data and reports go to `data/`, which git ignores.

### 5.3 How rates are measured

| Delivery | Rate | Example |
|---|---|---|
| push | events received ÷ seconds consumed | WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP |
| poll | records new or changed between the first and last poll ÷ time between them | GBFS, GTFS-Realtime, ADS-B |
| poll, snapshot with a stated period | records in the snapshot ÷ that period | METAR (last hour), Sensor.Community (5 min), FIRMS (24 h) |
| file drop | records in the newest complete file ÷ the period it covers | GH Archive (1 h), GDELT (15 min), OpenStreetMap (1 min) |

`RunReport.rate_basis` records which one applies (`observed`, `published`, or
`unmeasured` when a run ended before a rate could be computed).

## 6. Test evidence

All runs below were made for this record at `f4af707` with a clean working tree, on 2026-10-14 UTC. Logs: `/tmp/opencode/streams-session/record/`.

| Tier | Command | Result | Coverage |
|---|---|---|---|
| lint | `ruff check src tests` + `ruff format --check src tests` | All checks passed! 127 files already formatted | — |
| unit + component | `uv run pytest --cov` | 871 passed in 17.71s | `TOTAL                                                               3145      0    506      0   100%` (gate 100 %) |
| e2e run 1 | `uv run pytest tests/e2e` + `coverage combine/report --rcfile=.coveragerc.e2e` | 6 passed in 49.20s | `TOTAL                                                             1135      0    218      0   100%` (gate 100 %) |
| e2e run 2 | `uv run pytest tests/e2e` + `coverage combine/report --rcfile=.coveragerc.e2e` | 6 passed in 43.66s | `TOTAL                                                             1135      0    218      0   100%` (gate 100 %) |
| e2e run 3 | `uv run pytest tests/e2e` + `coverage combine/report --rcfile=.coveragerc.e2e` | 6 passed in 43.67s | `TOTAL                                                             1135      0    218      0   100%` (gate 100 %) |
| live | `LIVE_SECONDS=60 coverage run --rcfile=.coveragerc.live -m pytest tests/live -m live` | 65 passed in 71.16s (0:01:11) | `TOTAL                                                               3145    599    506     73    77%` (reported only) |

The component and e2e tiers start a real single-node Kafka broker in Docker (`apache/kafka:3.9.1`, published on 127.0.0.1 only).

### 6.1 Live check per source

Report `check-20261014T003632Z.json` (30 s per source): key-pending 11, no-events 1, ok 53. The earlier report `check-20261013T195138Z.json` (same command, same code, before the commit) had key-pending 11, ok 54.

| Source | Status | Events | Seconds | Rate (events/s) | Basis | Median attributes | First event (s) | Earlier status |
|---|---|---|---|---|---|---|---|---|
| `base_logs` | ok | 10629 | 40.001 | 265.718 | observed | 10.0 | 0.605 | ok |
| `bitfinex` | ok | 48 | 30.182 | 1.59 | observed | 6.0 | 0.849 | ok |
| `bitso` | ok | 1380 | 32.098 | 42.993 | observed | 10.0 | 0.535 | ok |
| `bitstamp` | ok | 19 | 30.161 | 0.63 | observed | 11.0 | 2.856 | ok |
| `bsc_logs` | ok | 11969 | 40.0 | 299.225 | observed | 10.0 | 0.705 | ok |
| `bybit` | ok | 213 | 30.285 | 7.033 | observed | 12.0 | 1.237 | ok |
| `coinbase` | ok | 250 | 30.106 | 8.304 | observed | 17.0 | 0.609 | ok |
| `deribit` | ok | 152 | 30.16 | 5.04 | observed | 24.0 | 0.726 | ok |
| `eth_logs` | ok | 2899 | 31.245 | 92.783 | observed | 10.0 | 10.185 | ok |
| `gemini` | ok | 24780 | 35.001 | 707.98 | observed | 10.0 | 0.887 | ok |
| `hyperliquid` | ok | 251 | 30.211 | 8.308 | observed | 8.0 | 0.829 | ok |
| `kraken` | ok | 84 | 30.176 | 2.784 | observed | 8.0 | 5.727 | ok |
| `okx` | ok | 924 | 30.216 | 30.58 | observed | 16.0 | 0.949 | ok |
| `polygon_logs` | no-events | 0 | 40.002 | 0.0 | observed | 0.0 | — | ok |
| `polymarket` | ok | 11860 | 30.156 | 393.288 | observed | 10.0 | 1.389 | ok |
| `solana` | ok | 53079 | 30.077 | 1764.77 | observed | 4.0 | 0.577 | ok |
| `xrpl` | ok | 635 | 30.189 | 21.034 | observed | 20.0 | 3.609 | ok |
| `albion` | ok | 99 | 30.001 | 3.3 | observed | 10.0 | 1.058 | ok |
| `twitch` | ok | 394 | 30.14 | 13.072 | observed | 19.0 | 0.814 | ok |
| `atlas` | ok | 51147 | 40.001 | 1278.643 | observed | 25.0 | 0.725 | ok |
| `ct` | ok | 1898 | 30.012 | 397.506 | published | 18.0 | 11.515 | ok |
| `gharchive` | ok | 89914 | 30.001 | 24.976 | published | 18.0 | 0.369 | ok |
| `npm` | ok | 22 | 30.0 | 0.733 | observed | 3.0 | 0.809 | ok |
| `osm` | ok | 2505 | 30.0 | 41.75 | published | 10.0 | 1.648 | ok |
| `ris` | ok | 170850 | 40.002 | 4271.036 | observed | 11.0 | 0.785 | ok |
| `crossref` | ok | 1000 | 30.0 | 12.993 | published | 44.0 | 3.79 | ok |
| `pskreporter` | ok | 8405 | 30.006 | 280.111 | observed | 13.0 | 0.525 | ok |
| `rbn` | ok | 47 | 30.001 | 1.567 | observed | 9.0 | 0.96 | ok |
| `seedlink` | ok | 63 | 30.0 | 2.1 | observed | 14.0 | 6.038 | ok |
| `sensorcomm` | ok | 17560 | 30.0 | 58.74 | published | 17.0 | 2.707 | ok |
| `usgs_water` | ok | 6552 | 30.002 | 1.99 | published | 27.0 | 4.027 | ok |
| `adsb_fi` | ok | 135 | 30.001 | 4.408 | published | 40.0 | 0.481 | ok |
| `adsb_lol` | ok | 50 | 30.0 | 1.577 | published | 39.0 | 0.589 | ok |
| `bicing` | ok | 610 | 30.001 | 3.413 | published | 15.0 | 0.541 | ok |
| `dt_marine` | ok | 923 | 30.013 | 30.753 | observed | 11.0 | 0.759 | ok |
| `dt_rail` | ok | 363 | 30.081 | 12.067 | observed | 8.0 | 2.469 | ok |
| `dt_rail_trains` | ok | 5 | 30.037 | 0.166 | observed | 13.0 | 15.67 | ok |
| `dt_road` | ok | 7864 | 30.078 | 261.454 | observed | 7.0 | 6.335 | ok |
| `ecobici` | ok | 779 | 30.001 | 5.126 | published | 12.0 | 0.53 | ok |
| `entur` | ok | 812 | 30.001 | 13.228 | published | 19.0 | 1.009 | ok |
| `hsl` | ok | 950 | 30.072 | 31.591 | observed | 23.0 | 1.363 | ok |
| `mbta_gtfsrt` | ok | 908 | 30.001 | 30.5 | published | 19.0 | 0.321 | ok |
| `mta_gtfsrt` | ok | 492 | 30.0 | 16.655 | published | 7.5 | 0.435 | ok |
| `ndov` | ok | 31 | 30.001 | 1.033 | observed | 16.0 | 0.992 | ok |
| `metar` | ok | 5034 | 30.002 | 1.395 | published | 44.0 | 1.274 | ok |
| `binance` | ok | 2310 | 36.481 | 63.321 | observed | 10.0 | 1.69 | ok |
| `mempool` | ok | 229 | 30.416 | 7.529 | observed | 26.0 | 2.217 | ok |
| `bluesky` | ok | 11757 | 30.104 | 390.546 | observed | 13.0 | 0.473 | ok |
| `gdelt` | ok | 1547 | 30.028 | 1.719 | published | 61.0 | 0.873 | ok |
| `wikimedia` | ok | 699 | 30.001 | 23.299 | observed | 30.0 | 0.613 | ok |
| `opensky` | ok | 660 | 30.0 | — | unmeasured | 18.0 | 1.136 | ok |
| `mbta_v3` | ok | 823 | 30.003 | 18.548 | published | 21.0 | 0.625 | ok |
| `tfl` | ok | 50 | 30.0 | — | unmeasured | 26.0 | 1.014 | ok |
| `firms` | ok | 219907 | 30.001 | 2.545 | published | 13.0 | 5.36 | ok |
| `mastodon` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `fink` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `lasair` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `aisstream` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `cta_bus` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `cta_train` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `gfw` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `mta_bustime` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `nta` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `wmata` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |
| `entsoe` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | key-pending |

Not delivered in this 30 s window: `polygon_logs`. The live tier (60 s windows, run a few minutes earlier) passed for every source, so this is recorded as a short-window miss, not a broken consumer; the 24-hour sampling decides.

### 6.2 Links

Every documentation, terms and sign-up URL of the descriptors, the README and the documentation fixtures, fetched with `check_links.py` (Appendix D):

```
111 URLs checked, 106 answered HTTP 200
  403  https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions  (entsoe:terms)
  403  https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API  (README, entsoe:docs, fixture:entsoe)
  202  https://www.binance.com/en/terms  (binance:terms)
  403  https://www.mta.info/developers  (mta_gtfsrt:terms)
  403  https://www.mta.info/developers/terms-and-conditions  (mta_bustime:terms)
```

Non-200 answers explained: `www.binance.com/en/terms` answers 202 with a JavaScript challenge; the two `www.mta.info` pages answer 403 to scripts (their text was retrieved with a browser-like fetch on 2026-10-13). The two ENTSO-E Zendesk pages answered 200 at 19:43 UTC on 2026-10-13 and 403 at 00:41 UTC on 2026-10-14 with the header `cf-mitigated: challenge` (a Cloudflare bot challenge, also with browser headers); the Zendesk Help Center API confirms both still exist: `api/v2/help_center/en-us/sections/12783116987028.json` → 200, "Restful API integration guide", updated 2026-09-21; `api/v2/help_center/en-us/articles/40921911218961.json` → 200, "Legal Terms and Conditions", updated 2026-09-22.

Every URL in this document (after generation; Appendix E quotes many provider URLs):

```
298 distinct URLs checked: 238 HTTP 200, 60 non-200 explained, 0 unexplained; 18 skipped as placeholders or local/example hosts
      404  http://api.wmata.com/TrainPositions
           API base path quoted from the documentation, not itself a document
      403  http://www.siri.org.uk/siri
           XML namespace identifier quoted inside a SIRI response, not a web page
      404  https://aisstream.io/terms
           recorded in the research file as HTTP 404: aisstream.io publishes no terms page
      405  https://api.entur.io/realtime/v2/vehicles/graphql
           POST-only endpoint (OAuth token / GraphQL); a GET is refused by design
  TimeoutError (also TimeoutError before the retry)  https://api.fink-portal.org/api/v1/latests
           recorded in the research file: api.fink-portal.org timed out; the LSST and ZTF Fink APIs answered
  500 (also 500 before the retry)  https://api.lasair.lsst.ac.uk/api
           API base path quoted from the documentation, not itself a document
      404  https://api.lasair.lsst.ac.uk/api/
           API base path quoted from the documentation, not itself a document
      401  https://api.lasair.lsst.ac.uk/api/cone/
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://api.lasair.lsst.ac.uk/api/cone/?ra=194.494&dec=48.851&radius=240.0&requestType=all&format=json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://api.lasair.lsst.ac.uk/api/query/?selected=objectId%2Cgmag&tables=objects&conditions=gmag%3C12.0&token=xxxxxxxxxxxxxxxxxxxxxxxx&format=json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      404  https://api.nationaltransport.ie/gtfsr
           API base path quoted from the documentation, not itself a document
      401  https://api.nationaltransport.ie/gtfsr/v2/Vehicles
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      404  https://api.wmata.com/TrainPositions
           API base path quoted from the documentation, not itself a document
      401  https://api.wmata.com/TrainPositions/TrainPositions?contentType=json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      404  https://api.wmata.com/gtfs
           API base path quoted from the documentation, not itself a document
      401  https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions-qa.pb
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      405  https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token
           POST-only endpoint (OAuth token / GraphQL); a GET is refused by design
      401  https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json?version=2
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://bustime.mta.info/api/siri/vehicle-monitoring.json
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://bustime.mta.info/api/siri/vehicle-monitoring.json?version=2
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      403  https://doi.org/10.1093/rasti/rzae024
           DOI resolves to Oxford University Press, which answers 403 to scripts
      401  https://gateway.api.globalfishingwatch.org
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://gateway.api.globalfishingwatch.org/v3/events
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest&start-date=2024-01-01&end-date=2024-01-02&limit=1&offset=0
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://gateway.api.globalfishingwatch.org/v3/events?vessels[0]=9b3e9019d-d67f-005a-9593-b66b997559e5&datasets[0]=public-global-fishing-events:latest&start-date=2017-01-01&end-date=2017-01-31&limit=1&offset=0
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      404  https://github.com/lasair-uk/lasair_api
           recorded in the research file: the lasair package's declared homepage returns 404
      404  https://github.com/non-relational-dbs/stream-consumers/pull/1
           private repository: GitHub answers 404 to unauthenticated clients
      404  https://github.com/non-relational-dbs/stream-consumers/pull/1#issuecomment-6154053047
           private repository: GitHub answers 404 to unauthenticated clients
      400  https://mastodon.social/api/v1/streaming
           WebSocket/streaming endpoint that needs a stream parameter and a token
      404  https://opensky-network.org/api
           API base path quoted from the documentation, not itself a document
      401  https://streaming.mastodon.social/api/v1/streaming/public
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/12783148966036-API-Rate-Limit-Part-1
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/12783223209876-API-Rate-Limit-Part-2
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/12783280128404-Request-Parameters-Time-Interval
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15594449302804
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15696677194644-Request-Endpoint
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15696716612372-Request-Parameters
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15727773247124-Query-Response
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15854491895828
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15854521447188-Get-Method
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15854536354964-API-Query-Size-Limit
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15856995130004-PsrType
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15857039772052-ProcessType
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15857043092756-DocumentType
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/32810427201809
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      403  https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API
           Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)
      401  https://web-api.tp-iop.entsoe.eu/api
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://web-api.tp.entsoe.eu/api
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      401  https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&outBiddingZone_Domain=10YCZ-CEPS-----N&periodStart=202303030000&periodEnd=202303040000
           API endpoint that requires a key: HTTP 401 without one is the expected gate
      202  https://www.binance.com/en/terms
           JavaScript challenge (HTTP 202)
      403  https://www.mta.info/developers
           mta.info answers 403 to scripts; text retrieved with a browser-like fetch on 2026-10-13
      403  https://www.mta.info/developers/terms-and-conditions
           mta.info answers 403 to scripts; text retrieved with a browser-like fetch on 2026-10-13
      403  https://www.mta.info/terms-and-conditions
           mta.info answers 403 to scripts; text retrieved with a browser-like fetch on 2026-10-13
```

### 6.3 Quoted phrases checked against the saved provider pages

Each phrase quoted in the descriptors, the README or this record's prose was searched (whitespace normalised) in the research files and raw page copies:

| Phrase | Found in |
|---|---|
| "within half an hour" | `mta_bustime.md` |
| "Getting a key might take a day" | `mbta_v3.md`, `raw/mbta_portal.raw`, `raw/mbta_portal.txt` |
| "within 3 working days" | `entsoe.md`, `raw/entsoe_zendesk.txt` |
| "open to any scientists" | `fink.md`, `raw/fink_form.html` |
| "password protected" | `fink.md`, `raw/fink_form.html` |
| "at less than 30 second intervals" | `mta_bustime.md` |
| "No results were found that matched the given" | `raw/cta_bus_v2.txt`, `raw/cta_bus_v3.txt` |
| "No matching data found" | `entsoe.md`, `raw/entsoe_zendesk.txt` |
| "using automation to disrupt conversations" | `mastodon.md`, `raw/mhelp_12-community-standards.txt` |
| "requires a previous written agreement, even for non-profit" | `opensky.md`, `raw/osky_terms.html`, `raw/osky_terms.txt` |
| "Five tokens per user" | `gfw.md`, `raw/gfw_authentication.html`, `raw/gfw_authentication.txt`, `raw/gfw_md_authentication.md` |
| "Noncommercial Use Only" | `gfw.md`, `raw/gfw_license-rate-limits.html`, `raw/gfw_license-rate-limits.txt`, `raw/gfw_md_license-rate-limits.md` |
| "API keys may only be used by trusted server-side services" | `aisstream.md` |
| "Within 3 seconds" | `aisstream.md`, `raw/ais_doc_chunk.js`, `raw/aisstream_doc.html` |
| "PLEASE NOT SHARE THESE TOKENS" | `lasair.md`, `raw/lasair_client.html`, `raw/lasair_rest.html`, `raw/lasair_rest.md` (+1) |
"No results were found that matched the given parameters" (CTA Bus Tracker v3, error table) is split by the PDF's table layout: `raw/cta_bus_v3.txt` has "No results were found that matched the given" on one line and "parameters." on the next, with the neighbouring column's text in between.

## 7. Defects found and fixed

### 7.1 Cancellation swallowed by `websockets` (fixed in `f4af707`)

- **Symptom:** the first full `profile` run over 54 sources (systemd unit `stream-profile-20261013`) was still running about 1.5 hours after it should have ended. It was stopped at 19:44 UTC on 2026-10-13.
- **Diagnosis:** an in-process watchdog (`hang/watchdog.py`) dumped the remaining tasks: two pump tasks of `MergedEventSource` (source `gemini`) were still alive after cancellation.
- **Root cause:** `websockets` 15.0.1 (pinned) through 17.2 (the latest release, tested in a separate environment) raises `AssertionError("cannot reset() while queue isn't empty")` instead of `CancelledError` when `recv()` is cancelled while reassembling a fragmented message and another frame is already queued. Our retry loops catch `Exception`, took it for a provider failure and reconnected forever.
- **Fix:** `raise_if_cancelling()` in `transports/base.py` re-raises a cancellation when the current task is being cancelled, whatever the library raised; `MergedEventSource` cancels its children again until every one has stopped.
- **Tests:** `tests/component/test_transports.py::test_websocket_cancelled_mid_fragmented_message_stops_instead_of_reconnecting` (real `websockets` server and client; fails without the fix), `test_merged_close_cancels_again_until_every_child_has_stopped`, `test_push_reconnect_loop_stops_when_its_task_is_cancelled`, `test_poll_retry_loop_stops_when_its_task_is_cancelled`, and an e2e source (`disguised_cancel`) that disguises its cancellation and must still let the CLI exit on time.
- **After the fix:** the profile re-run (unit `stream-profile-20261013b`) finished in about 2 minutes: report `profiles-20261013T195939Z.json`.
- Saved as project memory 1421.

### 7.2 Earlier defects (fixed in `9c37757`, reported when PR #1 was opened)

| Defect | Effect | Where it is handled now |
|---|---|---|
| A provider listed the same record twice in one poll | double counting; Entur read ~571 events/s instead of ~89 | `domain/policy.py` change detection; `tests/unit/test_domain.py::test_a_key_repeated_in_one_snapshot_counts_once` |
| METAR repeats column names (four cloud layers) | three of four cloud layers lost | `CsvDecoder.unique` adds `_2`, `_3`…; `tests/unit/test_decoders.py::test_repeated_column_names_get_suffixes` |
| OpenStreetMap XML entities (`&amp;`) left undecoded | wrong tag values | `sources/osm.py` applies `html.unescape` to attributes and tags |
| A source that failed to start crashed the whole `check` run | one bad source stopped all others | per-source error report; e2e source `bad_interval` must report `ValueError…` while the run continues |
| MQTT shutdown blocked the event loop about 1 s | every other stream froze at shutdown | MQTT connection loop rewritten to stop in under a second (no dedicated test identified for this record) |
| A failed SeedLink handshake left the connection open | socket leak | connection closed on handshake failure (no dedicated test identified for this record) |

## 8. Measurements so far

### 8.1 Hourly sampling (in progress)

Command: `stream-consumers sample --interval 3600 --window 60`. Rounds 1–3 ran from code `e719191` (unit `stream-sampling-20261013b`, reports `data/reports/sampling-20261013b`); that unit was stopped at 19:57 UTC because the old code could hang on the bug of 7.1. Rounds 4–24 run from `f4af707` (unit `stream-sampling-20261013c`, 21 rounds from 20:45 UTC, reports `data/reports/sampling-20261013c`, expected end about 2026-10-14 16:46 UTC). Two rounds of an earlier cancelled run (08:46 and 09:46 UTC on 2026-10-13) were deleted by mistake before being listed; they are not cited anywhere.

| Round | File | Scheduled (UTC) | Sources | ok | Other statuses |
|---|---|---|---|---|---|
| 1 | `sampling-20261013b/round-01-20261013T174611Z.json` | 2026-10-13 17:45:01Z | 54 | 54 | — |
| 2 | `sampling-20261013b/round-02-20261013T184611Z.json` | 2026-10-13 18:45:01Z | 54 | 54 | — |
| 3 | `sampling-20261013b/round-03-20261013T194611Z.json` | 2026-10-13 19:45:01Z | 54 | 54 | — |
| 4 | `sampling-20261013c/round-01-20261013T204610Z.json` | 2026-10-13 20:45:00Z | 65 | 54 | key-pending 11 |
| 5 | `sampling-20261013c/round-02-20261013T214610Z.json` | 2026-10-13 21:45:00Z | 65 | 54 | key-pending 11 |
| 6 | `sampling-20261013c/round-03-20261013T224610Z.json` | 2026-10-13 22:45:00Z | 65 | 54 | key-pending 11 |
| 7 | `sampling-20261013c/round-04-20261013T234610Z.json` | 2026-10-13 23:45:00Z | 65 | 53 | key-pending 11, no-events 1 |
| 8 | `sampling-20261013c/round-05-20261014T004610Z.json` | 2026-10-14 00:45:00Z | 65 | 54 | key-pending 11 |

Rates per source and round (events/s; `·` = not `ok`, with the status in the last column). The median uses the repository rule `policy.median_rate` (rounds with status `ok` and a rate). It is **provisional** (8 of 24 rounds). `≥ 1` marks a provisional median at or above the threshold.

| id | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Median | ≥ 1 | Not ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `base_logs` | 355.691 | 356.461 | 336.295 | 285.996 | 283.32 | 243.179 | 246.064 | 336.738 | 311.145 | yes | — |
| `bitfinex` | 1.363 | 1.13 | 1.279 | 1.446 | 1.097 | 1.03 | 0.631 | 1.911 | 1.2045 | yes | — |
| `bitso` | 55.686 | 41.894 | 49.223 | 44.666 | 22.96 | 24.168 | 14.429 | 39.522 | 40.708 | yes | — |
| `bitstamp` | 1.181 | 1.064 | 1.18 | 1.297 | 0.698 | 1.995 | 0.565 | 0.964 | 1.122 | yes | — |
| `bsc_logs` | 322.767 | 355.318 | 334.667 | 327.51 | 312.305 | 351.376 | 452.816 | 359.783 | 343.021 | yes | — |
| `bybit` | 5.859 | 7.006 | 6.873 | 6.474 | 5.407 | 4.728 | 3.964 | 6.385 | 6.122 | yes | — |
| `coinbase` | 10.237 | 9.322 | 9.938 | 12.119 | 6.589 | 5.623 | 5.856 | 11.046 | 9.63 | yes | — |
| `deribit` | 4.506 | 5.003 | 4.837 | 4.471 | 5.003 | 3.524 | 2.31 | 4.87 | 4.6715 | yes | — |
| `eth_logs` | 59.287 | 66.756 | 69.727 | 80.305 | 55.195 | 88.257 | · | 44.068 | 66.756 | yes | no-events 1 |
| `gemini` | 354.428 | 354.765 | 328.656 | 423.824 | 233.058 | 228.951 | 238.077 | 505.543 | 341.542 | yes | — |
| `hyperliquid` | 10.456 | 9.549 | 11.199 | 13.269 | 4.61 | 3.536 | 2.971 | 6.653 | 8.101 | yes | — |
| `kraken` | 3.987 | 4.719 | 7.13 | 7.842 | 5.049 | 3.123 | 2.326 | 4.966 | 4.8425 | yes | — |
| `okx` | 31.225 | 31.042 | 30.818 | 30.955 | 30.666 | 30.829 | 30.439 | 31.079 | 30.892 | yes | — |
| `polygon_logs` | 317.268 | 372.808 | 337.395 | 335.114 | 338.199 | 397.075 | 374.679 | 40.669 | 337.797 | yes | — |
| `polymarket` | 105.262 | 37.115 | 788.612 | 420.332 | 15.043 | 260.912 | 359.234 | 246.243 | 253.577 | yes | — |
| `solana` | 440.271 | 1434.99 | 481.14 | 625.86 | 1714.03 | 1384.9 | 1467.24 | 1688.34 | 1409.94 | yes | — |
| `xrpl` | 24.058 | 16.955 | 17.445 | 56.279 | 108.323 | 25.874 | 15.49 | 20.167 | 22.1125 | yes | — |
| `albion` | 8.167 | 3.482 | 3.867 | 9.05 | 18.95 | 5.05 | 3.733 | 2.05 | 4.4585 | yes | — |
| `twitch` | 16.999 | 27.406 | 28.509 | 20.484 | 13.24 | 12.731 | 8.358 | 8.246 | 15.1195 | yes | — |
| `atlas` | 838.69 | 1291.84 | 1222.76 | 621.068 | 1107.3 | 1144.01 | 1414.87 | 1342.55 | 1183.38 | yes | — |
| `ct` | 215.925 | 162.076 | 157.801 | 124.847 | 95.56 | 153.33 | 170.604 | 323.333 | 159.938 | yes | — |
| `gharchive` | 22.087 | 21.75 | 22.999 | 23.334 | 23.802 | 23.581 | 25.582 | 24.976 | 23.4575 | yes | — |
| `npm` | 1.016 | 0.633 | 1.083 | 1.349 | 1.033 | 1.783 | 1.099 | 0.733 | 1.058 | yes | — |
| `osm` | 32.867 | 33.467 | 43.3 | 24.983 | 40.967 | 27.367 | 3.267 | 88.8 | 33.167 | yes | — |
| `ris` | 5449.35 | 6963.62 | 5900.41 | 6694.5 | 5701.6 | 4954.62 | 4841.23 | 3056.67 | 5575.48 | yes | — |
| `crossref` | 6.081 | 6.056 | 6.037 | 6.003 | 5.977 | 5.96 | 5.944 | 12.989 | 6.02 | yes | — |
| `pskreporter` | 477.326 | 367.056 | 385.135 | 447.443 | 429.689 | 434.185 | 344.735 | 302.394 | 407.412 | yes | — |
| `rbn` | 3.981 | 6.579 | 17.789 | 4.766 | 4.979 | 2.633 | 1.866 | 1.815 | 4.3735 | yes | — |
| `seedlink` | 2.282 | 2.115 | 2.149 | 2.298 | 1.965 | 2.299 | 2.215 | 2.065 | 2.182 | yes | — |
| `sensorcomm` | 59.26 | 59.187 | 59.233 | 59.203 | 59.077 | 58.88 | 58.84 | 58.74 | 59.132 | yes | — |
| `usgs_water` | 1.807 | 1.774 | 1.795 | 1.813 | 1.801 | 1.768 | 1.797 | 1.796 | 1.7965 | yes | — |
| `adsb_fi` | 6.26 | 5.561 | 5.848 | 7.339 | 5.602 | 6.043 | 4.873 | 3.48 | 5.725 | yes | — |
| `adsb_lol` | 2.199 | 1.642 | 1.81 | 2.283 | 1.57 | 2.245 | 1.863 | 1.079 | 1.8365 | yes | — |
| `bicing` | 5.82 | 6.701 | 5.036 | 5.425 | 5.418 | 3.859 | 3.386 | 2.921 | 5.227 | yes | — |
| `dt_marine` | 35.289 | 34.613 | 32.552 | 32.994 | 30.966 | 31.779 | 31.002 | 30.936 | 32.1655 | yes | — |
| `dt_rail` | 66.924 | 58.439 | 52.305 | 22.756 | 20.311 | 16.358 | 11.706 | 8.059 | 21.5335 | yes | — |
| `dt_rail_trains` | 0.965 | 0.882 | 0.816 | 0.549 | 0.333 | 0.316 | 0.266 | 0.183 | 0.441 | no | — |
| `dt_road` | 276.636 | 256.945 | 256.382 | 240.969 | 239.674 | 245.049 | 248.605 | 249.809 | 249.207 | yes | — |
| `ecobici` | 2.268 | 3.021 | 4.306 | 4.39 | 4.102 | 4.432 | 4.386 | 3.769 | 4.204 | yes | — |
| `entur` | 57.56 | 47.657 | 42.155 | 34.829 | 25.583 | 10.201 | 4.585 | 13.674 | 30.206 | yes | — |
| `hsl` | 920.748 | 777.456 | 648.376 | 441.392 | 260.21 | 153.199 | 47.759 | 30.175 | 350.801 | yes | — |
| `mbta_gtfsrt` | 42.283 | 50.954 | 52.098 | 53.861 | 53.796 | 48.599 | 36.597 | 29.633 | 49.7765 | yes | — |
| `mta_gtfsrt` | 16.686 | 16.98 | 19.835 | 20.043 | 19.587 | 18.611 | 17.56 | 16.238 | 18.0855 | yes | — |
| `ndov` | 111.853 | 85.239 | 76.587 | 72.217 | 61.052 | 22.94 | 1.549 | 0.916 | 66.6345 | yes | — |
| `metar` | 1.425 | 1.427 | 1.41 | 1.402 | 1.401 | 1.389 | 1.376 | 1.379 | 1.4015 | yes | — |
| `binance` | 40.828 | 75.122 | 93.969 | 72.924 | 53.48 | 29.9 | 18.688 | 78.121 | 63.202 | yes | — |
| `mempool` | 4.125 | 4.573 | 85.323 | 4.75 | 17.091 | 2.752 | 2.243 | 7.058 | 4.6615 | yes | — |
| `bluesky` | 394.637 | 405.246 | 385.292 | 455.529 | 367.432 | 343.867 | 341.714 | 389.329 | 387.31 | yes | — |
| `gdelt` | 1.688 | 1.238 | 1.718 | 1.561 | 1.084 | 1.349 | 1.003 | 1.719 | 1.455 | yes | — |
| `wikimedia` | 39.821 | 51.936 | 33.891 | 29.501 | 30.637 | 29.987 | 22.998 | 26.561 | 30.312 | yes | — |
| `opensky` | 28.033 | 29.41 | 31.577 | 28.962 | 29.442 | 27.146 | 21.739 | 19.717 | 28.4975 | yes | — |
| `mbta_v3` | 26.629 | 32.475 | 32.1 | 33.121 | 32.613 | 31.719 | 22.454 | 18.024 | 31.9095 | yes | — |
| `tfl` | 0.342 | 2.273 | 4.697 | 0 | 0 | 8.257 | 7.479 | 2.256 | 2.2645 | yes | — |
| `firms` | 1.768 | 1.793 | 1.941 | 2.317 | 2.43 | 2.501 | 2.532 | 2.546 | 2.3735 | yes | — |
| `mastodon` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `fink` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `lasair` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `aisstream` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `cta_bus` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `cta_train` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `gfw` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `mta_bustime` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `nta` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `wmata` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |
| `entsoe` | — | — | — | · | · | · | · | · | — | — | key-pending 5 |

### 8.2 Profile run of 2026-10-13 (fixed code)

Command: `stream-consumers profile --max-events 500 --seconds 120 --concurrency 64`; report `data/reports/profile-20261013/profiles-20261013T195939Z.json`, masked samples in `data/profile-20261013/<id>.jsonl` (git-ignored). Fields counted on up to 500 events per source.

| id | Status | Events | Seconds | Rate | Basis | Median attributes | First event (s) | Fields seen | Fields ≥ 90 % present |
|---|---|---|---|---|---|---|---|---|---|
| `base_logs` | ok | 500 | 13.272 | 37.673 | observed | 10.0 | 2.102 | 10 | 10 |
| `bitfinex` | ok | 135 | 120.199 | 1.123 | observed | 6.0 | 0.908 | 16 | 2 |
| `bitso` | ok | 500 | 10.466 | 47.774 | observed | 10.0 | 0.553 | 14 | 10 |
| `bitstamp` | ok | 97 | 120.152 | 0.807 | observed | 11.0 | 3.362 | 11 | 11 |
| `bsc_logs` | ok | 500 | 11.9 | 42.017 | observed | 10.0 | 0.904 | 10 | 10 |
| `bybit` | ok | 500 | 84.748 | 5.9 | observed | 12.0 | 1.056 | 12 | 12 |
| `coinbase` | ok | 500 | 60.184 | 8.308 | observed | 17.0 | 0.554 | 17 | 17 |
| `deribit` | ok | 500 | 107.524 | 4.65 | observed | 24.0 | 0.834 | 24 | 24 |
| `eth_logs` | ok | 500 | 21.359 | 23.409 | observed | 10.0 | 10.439 | 10 | 10 |
| `gemini` | ok | 500 | 6.175 | 80.972 | observed | 10.0 | 1.166 | 10 | 9 |
| `hyperliquid` | ok | 500 | 92.637 | 5.397 | observed | 8.0 | 0.902 | 8 | 8 |
| `kraken` | ok | 500 | 85.776 | 5.829 | observed | 8.0 | 3.269 | 20 | 3 |
| `okx` | ok | 500 | 16.523 | 30.261 | observed | 16.0 | 0.914 | 16 | 16 |
| `polygon_logs` | ok | 500 | 12.176 | 41.064 | observed | 10.0 | 1.077 | 10 | 10 |
| `polymarket` | ok | 500 | 13.477 | 37.1 | observed | 10.0 | 1.613 | 12 | 10 |
| `solana` | ok | 500 | 12.012 | 41.625 | observed | 4.0 | 1.299 | 5 | 3 |
| `xrpl` | ok | 500 | 40.641 | 12.303 | observed | 20.0 | 3.24 | 65 | 13 |
| `albion` | ok | 500 | 43.102 | 11.6 | observed | 10.0 | 1.403 | 10 | 10 |
| `twitch` | ok | 500 | 36.451 | 13.717 | observed | 19.0 | 1.09 | 32 | 12 |
| `atlas` | ok | 500 | 12.282 | 40.71 | observed | 25.0 | 0.83 | 26 | 23 |
| `ct` | ok | 500 | 12.976 | 94.938 | published | 18.0 | 11.374 | 18 | 17 |
| `gharchive` | ok | 500 | 0.536 | — | unmeasured | 18.0 | 0.33 | 475 | 13 |
| `npm` | ok | 190 | 120.001 | 1.583 | observed | 3.0 | 15.562 | 3 | 3 |
| `osm` | ok | 500 | 2.235 | — | unmeasured | 10.0 | 2.223 | 92 | 10 |
| `ris` | ok | 500 | 11.935 | 41.894 | observed | 11.0 | 1.404 | 13 | 11 |
| `crossref` | ok | 500 | 2.721 | 6.016 | published | 45.0 | 2.334 | 83 | 32 |
| `pskreporter` | ok | 500 | 1.834 | 272.628 | observed | 13.0 | 0.873 | 13 | 13 |
| `rbn` | ok | 500 | 38.977 | 12.828 | observed | 9.0 | 0.783 | 9 | 9 |
| `seedlink` | ok | 268 | 120.001 | 2.233 | observed | 14.0 | 5.796 | 14 | 14 |
| `sensorcomm` | ok | 500 | 25.403 | 59.317 | published | 17.0 | 25.383 | 33 | 14 |
| `usgs_water` | ok | 500 | 3.212 | 2.209 | published | 27.0 | 3.18 | 27 | 27 |
| `adsb_fi` | ok | 500 | 80.645 | 6.035 | published | 40.0 | 0.286 | 58 | 35 |
| `adsb_lol` | ok | 167 | 120.001 | 1.416 | published | 39.0 | 11.397 | 55 | 33 |
| `bicing` | ok | 500 | 0.61 | — | unmeasured | 15.0 | 0.594 | 15 | 14 |
| `dt_marine` | ok | 500 | 15.808 | 31.63 | observed | 11.0 | 0.811 | 11 | 11 |
| `dt_rail` | ok | 500 | 11.404 | 43.844 | observed | 8.0 | 0.909 | 8 | 8 |
| `dt_rail_trains` | ok | 94 | 120.049 | 0.783 | observed | 13.0 | 5.073 | 13 | 12 |
| `dt_road` | ok | 500 | 7.857 | 63.638 | observed | 5.0 | 7.74 | 5 | 5 |
| `ecobici` | ok | 500 | 0.725 | — | unmeasured | 12.0 | 0.715 | 12 | 12 |
| `entur` | ok | 500 | 1.295 | — | unmeasured | 19.0 | 1.275 | 20 | 14 |
| `hsl` | ok | 500 | 2.872 | 174.095 | observed | 23.0 | 1.226 | 24 | 22 |
| `mbta_gtfsrt` | ok | 500 | 0.653 | — | unmeasured | 19.0 | 0.637 | 21 | 16 |
| `mta_gtfsrt` | ok | 500 | 15.137 | 19.785 | published | 7.5 | 0.567 | 15 | 2 |
| `ndov` | ok | 500 | 7.624 | 65.582 | observed | 16.0 | 1.321 | 17 | 15 |
| `metar` | ok | 500 | 0.502 | 1.258 | published | 44.0 | 0.476 | 44 | 15 |
| `binance` | ok | 500 | 35.105 | 14.243 | observed | 10.0 | 0.841 | 28 | 6 |
| `mempool` | ok | 500 | 87.642 | 5.705 | observed | 26.0 | 4.434 | 27 | 26 |
| `bluesky` | ok | 500 | 11.39 | 43.898 | observed | 13.0 | 0.357 | 76 | 11 |
| `gdelt` | ok | 500 | 1.018 | — | unmeasured | 61.0 | 0.975 | 61 | 26 |
| `wikimedia` | ok | 500 | 12.659 | 39.498 | observed | 25.0 | 1.029 | 45 | 25 |
| `opensky` | ok | 500 | 1.577 | — | unmeasured | 18.0 | 1.564 | 18 | 13 |
| `mbta_v3` | ok | 500 | 0.887 | — | unmeasured | 21.0 | 0.866 | 22 | 18 |
| `tfl` | ok | 500 | 90.203 | 3.964 | published | 27.0 | 0.885 | 27 | 26 |
| `firms` | ok | 500 | 10.399 | 2.029 | published | 13.0 | 10.362 | 13 | 13 |
| `mastodon` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `fink` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `lasair` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `aisstream` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `cta_bus` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `cta_train` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `gfw` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `mta_bustime` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `nta` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `wmata` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |
| `entsoe` | key-pending | 0 | 0.0 | — | unmeasured | 0.0 | — | 0 | 0 |

## 9. How to resume

| What | Where |
|---|---|
| Code | `/home/mavasbel/Dev/repos/ITAM/stream-consumers`, branch `main` (PR #1 merged) |
| Running job | systemd user unit `stream-sampling-20261013c` (`systemctl --user status stream-sampling-20261013c`), script `/tmp/opencode/streams-session/run_sampling_c.sh`, log `data/sampling-20261013c.log` |
| Sampling reports | `data/reports/sampling-20261013b/` (rounds 1–3) + `data/reports/sampling-20261013c/` (rounds 4–24); combine both |
| Profile | `data/reports/profile-20261013/profiles-20261013T195939Z.json`, `data/profile-20261013/` |
| Provider research | `/tmp/opencode/streams-session/keydocs/*.md` (+ `raw/`), reproduced in Appendix E |
| Fixture builder | `/tmp/opencode/streams-session/build_doc_fixtures.py` (Appendix D) |
| This record's logs | `/tmp/opencode/streams-session/record/` |
| Resume note | session note #33; project memory 1421 (websockets constraint) |

When keys arrive:

1. Put them in `stream-consumers/.env` (copy of `.env.example`; never committed).
2. `uv run stream-consumers keys` — every variable of that source must read `set`.
3. `uv run stream-consumers check <id>` — must be `ok` with events.
4. Capture real messages and replace that source's documentation-example fixture (`tests/fixtures/raw/<id>.json`), personal values masked; keep the 100 % gates.
5. Sample the source hourly for 24 rounds; promote it to group C (B for aisstream.io) if its median is at least 1 event/s, otherwise remove it.

When the 24-hour sampling ends: compute the median per source over both report folders, remove every source below 1 event/s except GDELT, commit, and write the averages as a new dated record. Then start the student catalog in the `claude-course-streams` worktree.

## 10. Open items and limits

- The medians in 8.1 are provisional (8 of 24 rounds).
- `policy.median_rate` ignores rounds whose status is not `ok` (for example `no-events`). A source that delivers nothing in some rounds is judged only on the rounds where it delivered. Whether such rounds should count as 0 events/s must be decided before the final list.
- Rates come from 60-second windows (sampling) and 30-second windows (check); a short window can see no event from a source that delivered in other windows (`polygon_logs` in 6.1, `eth_logs` in round 7 of 8.1).
- The 11 candidates are tested only against the providers' documentation examples; their real message shape and rate are unknown until a key exists.
- Points marked NOT VERIFIED in the research files (Appendix E) remain unconfirmed: e.g. Fink broker addresses and licence, Lasair terms, aisstream.io bandwidth limit, ENTSO-E current resolutions, WMATA tier limits, GFW data latency.
- OpenSky's terms require a written agreement for automated use; using `opensky` continuously without one may break those terms.
- Five provider pages answer scripts with a challenge or 403 (Binance, two mta.info pages, two ENTSO-E Zendesk pages; 6.2); their existence was confirmed by other means.
- Branch protection is unavailable for private repositories on the GitHub Free plan; `main` is protected only by convention.
- The student catalog (Spanish, Canvas draft) has not been started.
- Vélib' Paris was excluded on its earliest rounds; over all 15 rounds of the cross-check sampler its median is above 1 event/s (3.3). Decision needed: add it back and let the 24-hour sampling decide. The same check should apply to every exclusion that rested on few rounds.

## Appendix A — `.env.example` (generated by `stream-consumers keys --template`)

```bash
# stream-consumers configuration. Copy to .env (git-ignored) and fill in what you have.
# Generated by `stream-consumers keys --template`; tests/unit/test_configuration.py keeps
# .env.example identical to it. Values set in the process environment win over this file.
#
# A source whose REQUIRED credentials are missing reports `key-pending` and is skipped;
# OPTIONAL credentials only raise a provider's limits. Settings show their default.

# --- aisstream: aisstream.io — global AIS ship positions and static data (aisstream.io)
# Credentials REQUIRED. Sign-up: https://aisstream.io/account
# How: Sign in with GitHub on the Account page and create an API key (shown once; server-side use only).
AISSTREAM_API_KEY=
# JSON list of boxes, each two [latitude, longitude] corners (default: the whole world). Default: [[[-90, -180], [90, 180]]]
# AISSTREAM_BOUNDING_BOXES=[[[-90, -180], [90, 180]]]

# --- crossref: Crossref scholarly metadata (works indexed per day) (Crossref)
# Contact e-mail sent as mailto= to join Crossref's polite pool (optional). Default: (empty)
# CROSSREF_MAILTO=

# --- cta_bus: CTA Bus Tracker vehicles — every Chicago bus (Chicago Transit Authority (CTA))
# Credentials REQUIRED. Sign-up: https://www.ctabustracker.com/bustime/login.jsp
# How: Create and activate a Bus Tracker account, then My Account → Developer API → apply; the key is e-mailed after approval (one key per account).
CTA_BUS_KEY=

# --- cta_train: CTA Train Tracker locations — every Chicago 'L' train (Chicago Transit Authority (CTA))
# Credentials REQUIRED. Sign-up: https://www.transitchicago.com/developers/traintrackerapply/
# How: Application form (name, address, e-mail, phone, purpose); CTA reviews it and replies.
CTA_TRAIN_KEY=

# --- entsoe: ENTSO-E Transparency Platform — actual electricity generation per production type (European Network of Transmission System Operators for Electricity (ENTSO-E))
# Credentials REQUIRED. Sign-up: https://transparency.entsoe.eu/
# How: Register on the Transparency Platform, then e-mail transparency@entsoe.eu asking for RESTful API access; the token is granted 'within 3 working days'.
ENTSOE_TOKEN=
# Comma-separated EIC codes of the areas to read (default Germany, France, Spain; list in the platform's Area List with EIC). Default: 10Y1001A1001A83F,10YFR-RTE------C,10YES-REE------0
# ENTSOE_AREAS=10Y1001A1001A83F,10YFR-RTE------C,10YES-REE------0

# --- fink: Fink — Rubin Observatory LSST and ZTF alert livestream (Fink broker (CNRS/IN2P3 and partners))
# Credentials REQUIRED. Sign-up: https://forms.gle/2td4jysT4e9pkf889
# How: Fill the Fink subscription form; the Fink team e-mails the Kafka server address and your group.id ('open to any scientists, but it is password protected').
FINK_KAFKA_SERVERS=
FINK_GROUP_ID=
# Comma-separated topics (one per Fink filter; list at https://lsst.fink-portal.org/schemas). Default: fink_extragalactic_lt20mag_candidate_lsst
# FINK_TOPICS=fink_extragalactic_lt20mag_candidate_lsst

# --- gfw: Global Fishing Watch events API — fishing, encounter, loitering and port-visit events (Global Fishing Watch)
# Credentials REQUIRED. Sign-up: https://globalfishingwatch.org/our-apis/
# How: Global Fishing Watch account, then request an API token (self-service; up to 5 tokens, they do not expire). Non-commercial use only.
GFW_API_TOKEN=
# Events dataset (fishing, encounters, loitering or port visits). Default: public-global-fishing-events:latest
# GFW_DATASET=public-global-fishing-events:latest
# Days back from today whose events are read at every poll. Default: 7
# GFW_LOOKBACK_DAYS=7
# Pages of 100 events read at every poll. Default: 5
# GFW_PAGES=5

# --- lasair: Lasair — Rubin Observatory LSST alerts that pass your saved filter (Lasair (Universities of Edinburgh and Belfast))
# Credentials REQUIRED. Sign-up: https://lasair.lsst.ac.uk/
# How: Create a Lasair account (e-mail), build and save a filter with Kafka streaming enabled; its topic is 'lasair_' + your user ID + the sanitised filter name. The Kafka server itself needs no password.
LASAIR_KAFKA_TOPIC=
# Kafka bootstrap server (the official notebook's 'prod' value). Default: lasair-lsst-kafka.lsst.ac.uk:9092
# LASAIR_KAFKA_SERVER=lasair-lsst-kafka.lsst.ac.uk:9092
# Kafka consumer group; Lasair remembers per group where delivery stopped, so use your own. Default: stream-consumers
# LASAIR_GROUP_ID=stream-consumers

# --- mastodon: Mastodon federated public timeline (statuses, edits, deletions) (Mastodon (default instance mastodon.social, Mastodon gGmbH))
# Credentials REQUIRED. Sign-up: https://mastodon.social/auth/sign_up
# How: A user account on the instance, then a user access token with scope read:statuses (OAuth flow: https://docs.joinmastodon.org/client/token/; the web interface's Preferences → Development page is not described in the official docs). Since Mastodon 4.2 app-only tokens are refused.
MASTODON_ACCESS_TOKEN=
# Host name of the Mastodon instance whose federated timeline is read. Default: mastodon.social
# MASTODON_INSTANCE=mastodon.social

# --- mbta_v3: MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry) (Massachusetts Bay Transportation Authority (MBTA))
# Credentials OPTIONAL (the source also works without it). Sign-up: https://api-v3.mbta.com/register
# How: V3 API portal account; request a key per application ('Getting a key might take a day').
MBTA_API_KEY=

# --- mta_bustime: MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus (Metropolitan Transportation Authority (MTA))
# Credentials REQUIRED. Sign-up: https://register.developer.obanyc.com/
# How: Web form (name, e-mail, project); the key arrives by e-mail 'within half an hour'.
MTA_BUSTIME_KEY=

# --- nta: NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland (National Transport Authority (NTA), Ireland)
# Credentials REQUIRED. Sign-up: https://developer.nationaltransport.ie/signup
# How: Developer-portal account, then subscribe to the 'GTFS Realtime' product; a pair of keys is issued (either works).
NTA_API_KEY=

# --- opensky: OpenSky Network state vectors — aircraft over Mexico (OpenSky Network)
# Credentials OPTIONAL (the source also works without it). Sign-up: https://opensky-network.org/my-opensky/account
# How: OpenSky account → Account page → create an API client (its id ends in -api-client) and copy client_id and client_secret.
OPENSKY_CLIENT_ID=
OPENSKY_CLIENT_SECRET=
# Seconds between requests. This box costs 4 credits per request: anonymous 400 credits/day, standard account 4,000/day. Default: 30
# OPENSKY_POLL_SECONDS=30

# --- tfl: Transport for London Unified API — Tube arrival predictions (Transport for London (TfL))
# Credentials OPTIONAL (the source also works without it). Sign-up: https://api-portal.tfl.gov.uk/signup
# How: API portal account, then create a subscription for the '500 requests' data plan.
TFL_APP_KEY=

# --- wmata: WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail (Washington Metropolitan Area Transit Authority (WMATA))
# Credentials REQUIRED. Sign-up: https://developer.wmata.com/signup
# How: Developer account (licence consent and CAPTCHA), then subscribe to a Transit Data service tier; each subscription generates two keys.
WMATA_API_KEY=
```

## Appendix B — Commit messages

```
commit 8448b641dec277aa2041466424e6f2e1c3bc6933
Date:   2026-10-13 00:37:18 -0600

docs: initial README

commit 9c37757a7fc42782726857fbf64fbfc2c1ec6e73
Date:   2026-10-13 02:19:07 -0600

Consumers for 54 public real-time data streams

Hexagonal package (split inbound/outbound ports, ABC trees, CLI as the only
composition root) with consumers for every source whose median measured rate
is at least 1 event/s, plus GDELT (project document). Commands: list, consume,
check, sample (hourly rounds on wall-clock targets) and profile (masked samples
and field statistics).

Tests: unit + component 661 tests at 100 % coverage; e2e (CLI subprocess against
local servers for every transport) at 100 % of its scope; live 54/54 sources
delivered events on 2026-10-13.

commit e7191911b18fc2914d8f32539c8b4cac945c569c
Date:   2026-10-13 02:20:01 -0600

CI: setup-uv has no major tag; pin v10.3.0

commit f4af707af150427df0619deb6861c87c6ee3ebfa
Date:   2026-10-13 13:54:22 -0600

Key-ready candidates, .env configuration and a cancellation fix

Candidates (Group.CANDIDATE, 11 sources) need a free key nobody has configured
yet, so their rate is unmeasured: aisstream, cta_bus, cta_train, entsoe, fink,
gfw, lasair, mastodon, mta_bustime, nta, wmata. Each is built from the
provider's official documentation (endpoint, key placement, limits) and tested
against its official examples; adding the key to .env is enough to run it. A
candidate is accepted only after its own sampling gives a median of at least
1 event/s, and is removed otherwise. Optional keys: MBTA (switches to the SSE
stream), OpenSky (OAuth 2 client credentials), TfL. FIRMS needs no key.

Configuration: Credential holds one or more variables and how to obtain them;
Setting holds non-secret values with defaults. New `keys` command lists what is
set (never values) and `keys --template` generates .env.example, which a test
keeps identical.

Infrastructure: Kafka transport (aiokafka), Avro decoder with the schema in the
message key (Fink), GTFS-Realtime JSON mapping, HttpClientPort.post_form and a
RequestAuthPort with OAuthClientCredentials (renewed before expiry and after
HTTP 401).

Fix: websockets 15-17 raises AssertionError ("cannot reset() while queue isn't
empty") when recv() is cancelled while reassembling a fragmented message and a
frame is already queued. The retry loops took it for a provider failure and
reconnected, so a merged source (gemini) never stopped and the 54-source
profile run hung. raise_if_cancelling() now turns any error raised while the
task is being cancelled back into a cancellation, and MergedEventSource cancels
again until every child has stopped. A component test reproduces the race with
the real websockets library; it fails without the fix.

Tests: unit + component 871 passed, 100 % (Kafka against a real broker in
Docker); e2e 6 passed, 100 % of its scope, three runs; live 65 passed (54 ok,
11 key-pending); 108 of 111 links HTTP 200 (binance 202, two mta.info 403).
```

## Appendix C — Pull request #1

Title: Consumers for 54 public real-time data streams · created 2026-10-13T08:19:25Z · https://github.com/non-relational-dbs/stream-consumers/pull/1

```markdown
## What

A hexagonal Python package with consumers for every public stream whose **median measured rate is ≥ 1 event/s**, plus GDELT (listed in the project document, 0.977/s). 54 sources: 45 keyless, 6 from the project document, 3 with an optional free key.

Commands: `list`, `consume`, `check`, `sample` (hourly rounds on wall-clock targets, catches up after the host sleeps), `profile` (masked samples + per-field statistics).

## Architecture

- `ports/inbound.py` (5 use cases) and `ports/outbound.py` (10 ports), all ABCs.
- `application/` depends only on ports and domain.
- Transport tree: `EventSourcePort → BaseEventSource → DecodingEventSource → Push / Poll / FileDrop`, plus `MergedEventSource`.
- `adapters/inbound/cli.py` is the only composition root.
- `tests/unit/test_architecture.py` enforces these rules on the code.

## Evidence (2026-10-13)

| Tier | Result |
|---|---|
| ruff check + format | clean |
| unit + component | 661 passed, coverage 100.00 % (2,583 statements, 390 branches) |
| e2e (CLI subprocess vs local servers, 33 local sources over every transport) | 3 passed, coverage 100 % of its scope (991 statements, 178 branches), stable over 3 runs |
| live (real providers, 60 s each) | 54/54 sources delivered events |
| links | 76 docs/terms/sign-up URLs: 74 HTTP 200; Binance terms (JS challenge, 202) and MTA developers (403 to scripts) documented in the README |

Fixtures are real captured messages, trimmed and with personal values masked; a test checks that none leaks a personal value or an e-mail address.

## Notes

- Branch protection and rulesets are not available for private repositories on the GitHub Free plan (HTTP 403), so work reaches `main` through PRs by convention.
- The 24-hour re-measurement with `sample` starts after this PR; sources whose median falls below 1 event/s will be removed in a follow-up.
```

Comment of 2026-10-13T20:00:42Z:

```markdown
Commit f4af707 adds:

- **11 candidate sources (group D)** that need a free key nobody has configured yet: `aisstream`, `cta_bus`, `cta_train`, `entsoe`, `fink`, `gfw`, `lasair`, `mastodon`, `mta_bustime`, `nta`, `wmata`. Each one follows the provider's official documentation and is tested against its official examples. Without a key it reports `key-pending`. With a key it runs, and it is accepted only after its own sampling gives a median of at least 1 event/s.
- **Optional keys:** MBTA switches to its SSE stream; OpenSky uses OAuth 2 client credentials; TfL. FIRMS needs no key.
- **`.env` support:** a `keys` command shows what is set (never the values). `keys --template` generates `.env.example`, and a test keeps the two identical. README has the full table of keys.
- **New infrastructure:** Kafka transport (aiokafka), an Avro decoder that reads the schema from the message key, GTFS-RT in its JSON form, `post_form` on the HTTP client port, and an OAuth client-credentials adapter.
- **Fix:** websockets 15–17 turns a cancelled `recv()` into an `AssertionError` when it was in the middle of a fragmented message. The retry loops took that for a provider failure and reconnected forever, which hung the 54-source profile run. `raise_if_cancelling()` now treats it as the cancellation it is, and `MergedEventSource` cancels again until every child has stopped. A test reproduces the race with the real library and fails without the fix.

Evidence:
- Unit and component: 871 tests, 100 %. Kafka runs against a real broker in Docker.
- e2e: 6 tests, 100 %, three runs.
- Live: 65 passed (54 ok, 11 key-pending).
- Links: 108 of 111 answer HTTP 200. Binance answers 202 and two mta.info pages answer 403 to scripts; all three are documented.
- CI is green.
```

## Appendix D — Helper scripts used for this work (not part of the repository)

### `/tmp/opencode/streams-session/build_doc_fixtures.py` (sha256 `0975c523058531c8…`)

````python
"""Build test fixtures for key-gated sources from the providers' OFFICIAL documentation examples.

Every message comes from a raw copy of the documentation fetched on 2026-10-13
(/tmp/opencode/streams-session/keydocs/raw). Corrections are only the ones listed in each fixture's
`corrections` field (PDF page footers, typographic quotes, trailing commas, elisions); personal
values are replaced by "<masked>" as for captured fixtures.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RAW = Path("/tmp/opencode/streams-session/keydocs/raw")
DOCS = Path("/tmp/opencode/streams-session/keydocs")
OUT = Path("/home/mavasbel/Dev/repos/ITAM/stream-consumers/tests/fixtures/raw")
MASK = "<masked>"


def write(source: str, url: str, corrections: list[str], messages: list[dict[str, object]]) -> None:
    doc = {
        "source": source,
        "origin": "official documentation example (no key yet to capture live messages)",
        "documentation_url": url,
        "fetched_at": "2026-10-13",
        "corrections": corrections,
        "messages": messages,
    }
    (OUT / f"{source}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(source, len(messages), "messages")


def text(body: object, **attributes: str) -> dict[str, object]:
    out: dict[str, object] = {"body_text": body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)}
    if attributes:
        out["attributes"] = attributes
    return out


def sse_blocks(raw: str) -> list[tuple[str, str]]:
    """(event, data) pairs from `event:` / `data:` lines."""
    out, event = [], None
    for line in raw.splitlines():
        if line.startswith("event: "):
            event = line[len("event: ") :].strip()
        elif line.startswith("data: ") and event is not None:
            out.append((event, line[len("data: ") :]))
            event = None
    return out


# ---------------------------------------------------------------- MBTA V3 streaming (keyed path)
mbta = sse_blocks((DOCS / "mbta_v3.md").read_text(encoding="utf-8").split("## 6.", 1)[1].split("## 7.", 1)[0])
assert [e for e, _ in mbta] == ["reset", "add", "update", "remove"], mbta
write(
    "mbta_v3_stream",
    "https://www.mbta.com/developers/v3-api/streaming",
    [],
    [text(d, event=e) for e, d in mbta],
)

# ---------------------------------------------------------------- Mastodon SSE federated timeline
masto = sse_blocks((RAW / "ex_masto_sse_public.txt").read_text(encoding="utf-8"))
assert [e for e, _ in masto] == ["update", "delete"], masto
from stream_consumers.adapters.outbound.sources.mastodon import MastodonFactory  # noqa: E402
from stream_consumers.domain.policy import PersonalDataMasker  # noqa: E402

MASKER = PersonalDataMasker(MastodonFactory.DESCRIPTOR.personal_fields)


def mask_status(status: dict[str, object]) -> dict[str, object]:
    return dict(MASKER.mask(status))


update = mask_status(json.loads(masto[0][1]))
write(
    "mastodon",
    "https://docs.joinmastodon.org/methods/streaming/#public",
    ["personal values masked with the repository's PersonalDataMasker and the source's personal_fields"],
    [text(update, event="update"), text(masto[1][1], event="delete")],
)

# ---------------------------------------------------------------- aisstream.io
ais_md = (DOCS / "aisstream.md").read_text(encoding="utf-8").split("## 6.", 1)[1].split("## 7.", 1)[0]
blocks = re.findall(r"```json\n(.*?)\n```", ais_md, re.S)
position, confirmation = json.loads(blocks[0]), json.loads(blocks[1])
assert position["MessageType"] == "PositionReport" and confirmation["MessageType"] == "SubscriptionConfirmation"
write(
    "aisstream",
    "https://aisstream.io/documentation#messages",
    ["delivered as binary frames in the service; stored here as UTF-8 text"],
    [text(confirmation), text(position)],
)

# ---------------------------------------------------------------- CTA Train Tracker ttpositions (JSON)
tt = (RAW / "cta_tt_pdf.txt").read_text(encoding="utf-8")
start = tt.index("JSON Response:", tt.index("ttpositions.aspx?key=4ba28f6b2b8843bf9cef1c0fcc05f874&rt=red&outputTy"))
chunk = tt[start + len("JSON Response:") :]
chunk = chunk[: chunk.index("Appendices")]
footer = re.compile(r"^\s*transitchicago\.com\s+v1\.46.*$", re.M)
chunk = footer.sub("", chunk).replace("\f", "")
body = json.loads(chunk[chunk.index("{") : chunk.rindex("}") + 1])
assert body["ctatt"]["route"][0]["@name"] == "red"
write(
    "cta_train",
    "https://www.transitchicago.com/assets/1/6/cta_Train_Tracker_API_Developer_Guide_and_Documentation.pdf",
    ["PDF page footer lines and form-feed characters removed from inside the JSON"],
    [text(body)],
)

# ---------------------------------------------------------------- CTA Bus Tracker v3 getroutes + getvehicles (JSON)
bus = (RAW / "cta_bus_v3.txt").read_text(encoding="utf-8")
footer3 = re.compile(r"^\s*transitchicago\.com\s+v3\.0.*$", re.M)


def json_after(marker: str, upto: str) -> str:
    i = bus.index(marker)
    seg = bus[i:]
    seg = seg[seg.index("{") :]
    seg = seg[: seg.index(upto)]
    return footer3.sub("", seg).replace("\f", "")


vehicles_src = json_after("getvehicles?key=89dj2he89d8j3j3ksjhdue93j&vid=6438,1295&tmres=s&format=json", "Routes\n")
vehicles_src = vehicles_src.replace("\u201d", '"')
vehicles = json.loads(vehicles_src[: vehicles_src.rindex("}") + 1])
assert len(vehicles["bustime-response"]["vehicle"]) == 2
routes_src = json_after("getroutes?key=89dj2he89d8j3j3ksjhdue93j&format=json", "\n\n\n")
routes_src = routes_src.replace('"Pontiac \u2013 Dhu Varren\n', '"Pontiac \u2013 Dhu Varren",\n')
routes_src = re.sub(r",\s*\.\.\.\s*\]", "]", routes_src)
routes = json.loads(routes_src[: routes_src.rindex("}") + 1])
assert [r["rt"] for r in routes["bustime-response"]["routes"]] == ["1", "2"]
write(
    "cta_bus",
    "https://www.transitchicago.com/assets/1/6/cta_Bus_Tracker_API_Developer_Guide_and_Documentation_2025-04-21.pdf",
    [
        "PDF page footer lines and form-feed characters removed from inside the JSON",
        "getvehicles: a typographic closing quote (U+201D) after a value replaced by '\"'",
        "getroutes: the missing closing quote and comma after \"Pontiac \u2013 Dhu Varren\" added; the '...' elision removed",
    ],
    [text(routes, url="getroutes"), text(vehicles, url="getvehicles")],
)

# ---------------------------------------------------------------- ENTSO-E A75 (official Postman collection example)
gen = (RAW / "entsoe_example_gen_0.xml").read_text(encoding="utf-8")
write(
    "entsoe",
    "https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API",
    [],
    [{"body_text": gen, "bytes": True}],
)

# ---------------------------------------------------------------- Lasair Kafka plain message
las = (RAW / "lasairlsst_core_functions_alert-streams.md.txt").read_text(encoding="utf-8")
i = las.index('"UTC": "2026-01-29 11:40:14"')
block = las[las.rindex("{", 0, i) : las.index("}", i) + 1]
block = re.sub(r",\s*}$", "\n}", block)
plain = json.loads(block)
assert set(plain) == {"diaObjectId", "decl", "ra", "UTC"}
write(
    "lasair",
    "https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html",
    ["trailing comma after the last field removed (the documented example is not strict JSON)"],
    [{"body_text": json.dumps(plain), "bytes": True, "attributes": {"topic": "lasair_example", "partition": "0", "offset": "0"}}],
)

# ---------------------------------------------------------------- Global Fishing Watch events
gfw = (RAW / "gfw_md_examples_events_get-example1.md").read_text(encoding="utf-8")
gblock = re.findall(r"```json\n(.*?)\n```", gfw, re.S)
doc = next(json.loads(b) for b in gblock if '"entries"' in b)
assert doc["entries"][0]["id"] == "718a4d93c16f78d9a54e9bc56d20c7e0"
write("gfw", "https://globalfishingwatch.org/our-apis/documentation/docs/examples/events/get-example1", [], [text(doc)])
````

### `/tmp/opencode/streams-session/check_links.py` (sha256 `d47d8147451d9515…`)

```python
"""HTTP status of every docs/terms/sign-up URL in the descriptors, the README and the documentation fixtures."""

import asyncio
import json
import re
import sys
from pathlib import Path

import aiohttp

from stream_consumers.adapters.outbound.sources import FACTORIES

ROOT = Path("/home/mavasbel/Dev/repos/ITAM/stream-consumers")
UA = "Mozilla/5.0 (X11; Linux x86_64) stream-consumers link check (course repository)"

urls: dict[str, set[str]] = {}
for f in FACTORIES:
    d = f.descriptor
    for kind, url in (("docs", d.docs_url), ("terms", d.terms_url), ("signup", d.credential.sign_up_url if d.credential else None)):
        if url:
            urls.setdefault(url, set()).add(f"{d.id}:{kind}")
for url in re.findall(r"\]\((https://[^)\s]+)\)", (ROOT / "README.md").read_text()):
    urls.setdefault(url, set()).add("README")
for path in (ROOT / "tests/fixtures/raw").glob("*.json"):
    doc = json.loads(path.read_text())
    if "documentation_url" in doc:
        urls.setdefault(doc["documentation_url"].split("#")[0], set()).add(f"fixture:{path.stem}")
only = set(sys.argv[1:])


async def status(session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
    try:
        async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=40)) as r:
            return url, str(r.status)
    except Exception as exc:  # noqa: BLE001 - report every failure
        return url, f"{type(exc).__name__}: {exc}"[:120]


async def main() -> None:
    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        results = await asyncio.gather(*(status(session, u) for u in sorted(urls) if not only or any(o in u for o in only)))
    bad = [(u, s) for u, s in results if s != "200"]
    print(f"{len(results)} URLs checked, {len(results) - len(bad)} answered HTTP 200")
    for u, s in bad:
        print(f"  {s}  {u}  ({', '.join(sorted(urls[u]))})")


asyncio.run(main())
```

### `/tmp/opencode/streams-session/run_sampling.sh` (sha256 `4da87d664ab8da24…`)

```bash
#!/usr/bin/env bash
# 24 hourly rounds with the repo's own tested `sample` command; first round at 17:45 UTC (off the :23 slot of the old loop).
set -u
cd /home/mavasbel/Dev/repos/ITAM/stream-consumers
LOG=data/sampling-20261013b.log
target=$(date -u -d "17:45:00" +%s); now=$(date -u +%s)
echo "start $(date -u +%FT%TZ); first round in $((target-now)) s" > "$LOG"
[ $((target-now)) -gt 0 ] && sleep $((target-now))
uv run stream-consumers sample --rounds 24 --interval 3600 --window 60 --reports data/reports/sampling-20261013b >> "$LOG" 2>&1
echo "SAMPLING-DONE rc=$? $(date -u +%FT%TZ)" >> "$LOG"
```

### `/tmp/opencode/streams-session/run_sampling_c.sh` (sha256 `a02cd6245dc95e49…`)

```bash
#!/usr/bin/env bash
# Rounds 4-24 of the 24 h sampling, restarted on commit f4af707 (cancellation fix): the process that ran
# rounds 1-3 (code e719191, reports sampling-20261013b) could hang on the websockets cancellation race.
set -u
cd /home/mavasbel/Dev/repos/ITAM/stream-consumers
LOG=data/sampling-20261013c.log
target=$(date -u -d "20:45:00" +%s); now=$(date -u +%s)
echo "start $(date -u +%FT%TZ) commit $(git rev-parse --short HEAD); first round in $((target-now)) s" > "$LOG"
[ $((target-now)) -gt 0 ] && sleep $((target-now))
uv run stream-consumers sample --rounds 21 --interval 3600 --window 60 --reports data/reports/sampling-20261013c >> "$LOG" 2>&1
echo "SAMPLING-DONE rc=$? $(date -u +%FT%TZ)" >> "$LOG"
```

### `/tmp/opencode/streams-session/hang/watchdog.py` (sha256 `6ba96436c9f593fe…`)

```python
"""Run the CLI in-process; after WATCH seconds print every pending asyncio task's stack."""

import asyncio
import os
import sys

from stream_consumers.adapters.inbound import cli

WATCH = float(os.environ.get("WATCH", "90"))
_real_run = asyncio.run


async def _watched(coro):
    async def watchdog():
        await asyncio.sleep(WATCH)
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        print(f"=== WATCHDOG after {WATCH}s: {len(tasks)} pending tasks", file=sys.stderr, flush=True)
        for t in tasks:
            print(f"--- {t.get_name()} {t.get_coro()!r}", file=sys.stderr)
            t.print_stack(limit=30, file=sys.stderr)
            coro = t.get_coro()
            frame = getattr(coro, "cr_frame", None)
            if frame is not None and "source_id" in frame.f_locals:
                print(f"    source_id={frame.f_locals['source_id']}", file=sys.stderr)
            chain = coro
            while chain is not None:
                f = getattr(chain, "cr_frame", None) or getattr(chain, "ag_frame", None) or getattr(chain, "gi_frame", None)
                print(f"    await-chain: {type(chain).__name__} {getattr(chain, '__qualname__', '')} line={f and f.f_lineno}", file=sys.stderr)
                chain = getattr(chain, "cr_await", None) or getattr(chain, "ag_await", None) or getattr(chain, "gi_yieldfrom", None)
        import gc
        for obj in gc.get_objects():
            if type(obj).__name__ == "async_generator" and obj.ag_frame is not None:
                f = obj.ag_frame
                print(f"ASYNCGEN {obj.__qualname__} running={obj.ag_running} line={f.f_lineno} file={f.f_code.co_filename.rsplit('/', 1)[-1]} await={obj.ag_await!r}"[:300], file=sys.stderr)
        sys.stderr.flush()
        os._exit(3)

    dog = asyncio.create_task(watchdog())
    try:
        return await coro
    finally:
        dog.cancel()


def run(coro, **kw):
    return _real_run(_watched(coro), **kw)


asyncio.run = run

from stream_consumers.adapters.outbound.transports import websocket as _ws  # noqa: E402


class _Proxy:
    def __getattr__(self, name):
        return getattr(asyncio, name)

    async def wait_for(self, aw, timeout):
        task = asyncio.current_task()
        before = task.cancelling()
        try:
            return await asyncio.wait_for(aw, timeout)
        except TimeoutError:
            if task.cancelling() > 0 or before > 0:
                print(f"SWALLOW? TimeoutError with cancelling before={before} after={task.cancelling()} task={task.get_name()}", file=sys.stderr, flush=True)
            raise
        except asyncio.CancelledError:
            print(f"CANCEL-PROPAGATED cancelling={task.cancelling()} task={task.get_name()}", file=sys.stderr, flush=True)
            raise


_ws.asyncio = _Proxy()

from stream_consumers.adapters.outbound.transports import base as _base  # noqa: E402


async def _events(self):
    attempt = 0
    while True:
        stream = self._connect()
        error = _base.TransportError(f"{self._descriptor.id}: connection closed by the provider")
        try:
            async for message in stream:
                attempt = 0
                for record in self._decoder.decode(message):
                    yield record
        except Exception as exc:
            task = asyncio.current_task()
            if task.cancelling():
                import traceback

                print(
                    f"SWALLOWED-BY-RETRY {self._descriptor.id} {type(exc).__module__}.{type(exc).__name__}: {exc!r} task={task.get_name()} cancelling={task.cancelling()}",
                    file=sys.stderr,
                    flush=True,
                )
                traceback.print_exception(exc, file=sys.stderr)
            error = exc
        finally:
            await stream.aclose()
        attempt += 1
        await self._pause_before_retry(attempt, error)


# (unfixed copy disabled)
sys.exit(cli.main(sys.argv[1:]))

_orig_raise = _base.raise_if_cancelling


def _logged(error):
    try:
        _orig_raise(error)
    except asyncio.CancelledError:
        print(f"RE-RAISED-AS-CANCEL {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        raise


_base.raise_if_cancelling = _logged
```

### `/tmp/opencode/streams-session/record/gen_record.py` (sha256 `028567fd948b709b…`)

```python
"""Generate the dated research record of the stream-consumers / API-keys work.

Every table is computed from the repository code, the saved reports and the saved logs; the only
hand-written text is prose and the dated decisions. Run from the stream-consumers checkout:
    uv run python /tmp/opencode/streams-session/record/gen_record.py <output.md>
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.domain.models import RunReport, RunStatus
from stream_consumers.domain.policy import MINIMUM_RATE, median_rate

REPO = Path("/home/mavasbel/Dev/repos/ITAM/stream-consumers")
SESSION = Path("/tmp/opencode/streams-session")
REC = SESSION / "record"
KEYDOCS = SESSION / "keydocs"
OLD_ROUNDS = Path("/tmp/opencode/streams/rounds")
OUT = Path(sys.argv[1])

GROUP = {"A": "keyless", "B": "project document", "C": "free key (optional)", "D": "candidate (key required)"}
ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
KEEP_EMAILS = {"transparency@entsoe.eu"}


def sh(*args: str, cwd: Path = REPO) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def esc(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def mask_emails(text: str) -> str:
    return EMAIL.sub(lambda m: m.group(0) if m.group(0) in KEEP_EMAILS else "<e-mail masked>", text)


def fence(text: str, lang: str = "") -> str:
    longest = max([len(m) for m in re.findall(r"`{3,}", text)] + [2])
    ticks = "`" * (longest + 1)
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


def utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def report(row: dict) -> RunReport:
    data = dict(row)
    data["status"] = RunStatus(data["status"])
    try:
        return RunReport(**data)
    except TypeError:
        fields = RunReport.__dataclass_fields__  # type: ignore[attr-defined]
        return RunReport(**{k: v for k, v in data.items() if k in fields})


def readme_section(title: str) -> str:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    start = text.index(f"## {title}\n")
    end = text.find("\n## ", start + 4)
    body = text[start:end if end != -1 else None].split("\n", 1)[1]
    return re.sub(r"^(#{2,4}) ", lambda m: "#" * (len(m.group(1)) + 2) + " ", body.strip(), flags=re.M)


desc = sorted((f.descriptor for f in FACTORIES), key=lambda d: (ORDER[d.group.value], d.category, d.id))
by_id = {d.id: d for d in desc}
counts = Counter(d.group.value for d in desc)
head = sh("git", "rev-parse", "--short", "HEAD").strip()
status_clean = sh("git", "status", "--short").strip() == ""

# ------------------------------------------------------------------ saved measurements
round_files = sorted((REPO / "data/reports/sampling-20261013b").glob("round-*.json")) + sorted(
    (REPO / "data/reports/sampling-20261013c").glob("round-*.json")
)
rounds = []
for path in round_files:
    doc = json.loads(path.read_text())
    rounds.append((path, doc))
per_source: dict[str, list[RunReport | None]] = defaultdict(list)
for _, doc in rounds:
    rows = {r["source_id"]: report(r) for r in doc["reports"]}
    for d in desc:
        per_source[d.id].append(rows.get(d.id))

profile_path = REPO / "data/reports/profile-20261013/profiles-20261013T195939Z.json"
profiles = {p["run"]["source_id"]: p for p in json.loads(profile_path.read_text())}
check_new = sorted((REC / "check").glob("check-*.json"))[-1]
check_old = sorted((SESSION / "check-keys").glob("check-*.json"))[-1]
check_rows = {r["source_id"]: r for r in json.loads(check_new.read_text())}
check_old_rows = {r["source_id"]: r for r in json.loads(check_old.read_text())}


def log_tail(name: str, pattern: str) -> str:
    lines = [l for l in (REC / name).read_text().splitlines() if re.search(pattern, l)]
    return lines[-1].strip() if lines else "(not found)"


unit_line = log_tail("unit-component.log", r"passed|failed")
unit_total = log_tail("unit-component.log", r"^TOTAL")
e2e = [(log_tail(f"e2e-{i}.log", r"passed|failed"), log_tail(f"e2e-coverage-{i}.txt", r"^TOTAL")) for i in (1, 2, 3)]
live_line = log_tail("live.log", r"passed|failed")
live_total = log_tail("live-coverage.txt", r"^TOTAL")
links_out = (REC / "links.txt").read_text().strip() if (REC / "links.txt").exists() else "(link check output missing)"
doclinks_out = (REC / "doclinks.txt").read_text().strip() if (REC / "doclinks.txt").exists() else "(document link check pending)"

old_rounds = sorted(OLD_ROUNDS.glob("round-*.jsonl"))
old: dict[str, list[dict]] = defaultdict(list)
for path in old_rounds:
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            old[row["id"]].append(row)

out: list[str] = []
w = out.append
now_local = datetime.now().astimezone()

# ------------------------------------------------------------------ 0. header
w("# Stream consumers, key-gated sources and measurements — research record\n")
w(
    f"Written {now_local:%Y-%m-%d %H:%M %Z} ({datetime.now(UTC):%Y-%m-%d %H:%M} UTC) by the streams session "
    "(`ses_ecd14c7d…`, titled \"Non relational DBs Streams\"). This is a historical record of the state at that time; "
    "it will not be edited. The 24-hour averages will go into a new dated record.\n"
)
w("| Item | Value |\n|---|---|")
for k, v in [
    ("Repository", "`non-relational-dbs/stream-consumers` (GitHub, **private**, instructor-only)"),
    ("Local clone", f"`{REPO}`"),
    ("Branch", "`main` of `stream-consumers` (its only branch)"),
    ("Commits", "`8448b64` initial README · `9c37757` consumers for 54 streams · `e719191` CI pin · `f4af707` key-ready candidates and cancellation fix"),
    ("HEAD at writing", f"`{head}`, working tree {'clean' if status_clean else 'NOT clean'}"),
    ("Pull request", "https://github.com/non-relational-dbs/stream-consumers/pull/1 (merged into `main` at `f4af707`), comment with the `f4af707` summary: https://github.com/non-relational-dbs/stream-consumers/pull/1#issuecomment-6154053047"),
    ("CI", "GitHub Actions `test` workflow: run 38368548940 on `e719191` success; run 38458568897 on `f4af707` success"),
    ("This record", "course repository, worktree `worktrees/claude-course-streams`, branch `claude-course-streams`"),
    ("Earlier records (unchanged)", "`docs/research/2026-10-12-21-37-public-data-streams-survey.md` (`1dba0b7`), `docs/research/2026-10-12-22-41-public-data-streams-full-report.md` (`5a34175`)"),
]:
    w(f"| {k} | {v} |")
w("")

# ------------------------------------------------------------------ 1. summary
w("## 1. Summary\n")
w(
    f"- **{len(desc)} sources** in the catalog: {counts['A']} keyless (A), {counts['B']} from the project document (B), "
    f"{counts['C']} with an optional free key (C) and {counts['D']} candidates (D) that need a free key nobody has configured yet.\n"
    "- Every source is a module of a hexagonal Python package (split inbound/outbound ports, abstract base classes, the CLI as the only composition root).\n"
    "- Credentials and settings are declared per source and read from the environment or a git-ignored `.env`; `stream-consumers keys` shows what is set without printing values and `keys --template` generates `.env.example`.\n"
    f"- Tests at `{head}` (this record's runs): unit + component `{unit_line}`, coverage line `{unit_total}`; e2e three runs, each `{e2e[0][0]}` with 100 % of its scope; live `{live_line}`.\n"
    "- A bug in `websockets` 15–17 (an `AssertionError` instead of a cancellation) made the first 54-source profile run hang; it is fixed in `f4af707` and reproduced by a test.\n"
    f"- The 24-hour sampling is in progress: {len(rounds)} of 24 hourly rounds saved when this record was generated.\n"
    "- Open: the free keys (requested from Marco), the 24-hour medians, and the student catalog.\n"
)

# ------------------------------------------------------------------ 2. decisions
w("## 2. Decisions\n")
w("| Date (2026) | Decision | Source of the decision |\n|---|---|---|")
for row in [
    ("10-13", "Inclusion rule: a source is included when its **median measured rate is at least 1 event/s** (`policy.MINIMUM_RATE = 1.0`).", "Marco: \"Could we proceed as per your recommendations for 1 and 2 and could we keep GDELT?\""),
    ("10-13", "GDELT is kept although its measured median was 0.977 events/s, because the project document lists it.", "same message"),
    ("10-13", "The 24-hour sampling is done with the repository's own tested `sample` command; the earlier `/tmp` sampler is a cross-check only and not evidence.", "same message (recommendation 2)"),
    ("10-13", "The repository mirrors the hexagonal layout of `quizzes/query_validation` (split inbound/outbound ports).", "Marco: \"could we follow the same principles we follow for all repos? Hex adapter ports with split inbound outbound ports?\""),
    ("10-13", "Organization `non-relational-dbs` default member permission changed from `read` to `none` (read back after the change); the repository is private and must not be shared with students.", "D12 of the locked plan"),
    ("10-13", "Two agent sessions share the course repository: this session owns only the streams work (worktree `claude-course-streams`); homeworks, labs, Canvas uploads belong to the other session (`ses_efd787940…`).", "Marco approved the ownership split"),
    ("10-13", "Sources that need a free key are built and tested now as group D (candidate) so that adding the key to `.env` is enough; a candidate is accepted only after its own sampling gives a median of at least 1 event/s, and removed otherwise. This replaces the earlier \"pending, not built\" rule.", "Marco: \"Could we leave everything ready for the keys and config to be added to a .env?\""),
    ("10-13", "This record: course worktree only, streams work only, English.", "Marco: \"Could we proceed as per your recommendations?\""),
]:
    w("| " + " | ".join(esc(c) for c in row) + " |")
w("")

# ------------------------------------------------------------------ 3. sources
w(f"## 3. The {len(desc)} sources\n")
w("Generated from the descriptors in `src/stream_consumers/adapters/outbound/sources/` at the commit above.\n")
w("### 3.1 Overview\n")
w("| # | id | Source | Provider | Group | Category | Transport | Delivery | Key |\n|---|---|---|---|---|---|---|---|---|")
for i, d in enumerate(desc, 1):
    key = "—" if d.credential is None else ("required" if d.credential.required else "optional")
    w(f"| {i} | `{d.id}` | {esc(d.name)} | {esc(d.provider)} | {GROUP[d.group.value]} | {esc(d.category)} | {d.transport.value} | {d.delivery.value} | {key} |")
w("")
w("### 3.2 Detail per source\n")
for d in desc:
    w(f"#### `{d.id}` — {d.name}\n")
    w("| Field | Value |\n|---|---|")
    w(f"| Provider | {esc(d.provider)} |")
    w(f"| Group | {GROUP[d.group.value]} |")
    w(f"| Transport / delivery | {d.transport.value} / {d.delivery.value} |")
    w(f"| Endpoint | `{esc(d.endpoint)}` |")
    w(f"| Documentation | {d.docs_url} |")
    w(f"| Terms | {d.terms_url} |")
    if d.min_interval_s:
        w(f"| Minimum interval between requests | {d.min_interval_s:g} s |")
    if d.credential:
        c = d.credential
        w(f"| Credential | {', '.join(f'`{v}`' for v in c.env_vars)} ({'required' if c.required else 'optional'}) |")
        w(f"| Sign-up | {c.sign_up_url} |")
        w(f"| How to get it | {esc(c.how_to_get)} |")
    for s in d.settings:
        w(f"| Setting `{s.env_var}` | default `{esc(s.default)}` — {esc(s.description)} |")
    if d.personal_fields:
        w(f"| Personal fields (masked) | {', '.join(f'`{p}`' for p in d.personal_fields)} |")
    if d.notes:
        w(f"| Notes | {esc(d.notes)} |")
    w("")

w("### 3.3 Sources evaluated and not included\n")
w(
    "The inclusion decision of 2026-10-13 used the rounds of the `/tmp` cross-check sampler that existed then. "
    f"The table recomputes, for each source not in the catalog, the median over **all {len(old_rounds)} rounds** of that sampler "
    f"(`{OLD_ROUNDS}`, {old_rounds[0].name[6:22]} to {old_rounds[-1].name[6:22]} UTC; 60 s windows). That sampler is a cross-check "
    "tool, not repository code, so these figures explain the exclusions but are not evidence for the final list.\n"
)
w("| id | Rounds | Rounds `ok` | Median rate of `ok` rounds (events/s) | Median attributes | Status counts | Last note |\n|---|---|---|---|---|---|---|")
import statistics

for sid in sorted(set(old) - set(by_id)):
    rows = old[sid]
    oks = [r for r in rows if r.get("status") == "ok" and r.get("rate") is not None]
    med = f"{statistics.median(r['rate'] for r in oks):.3f}" if oks else "—"
    att = f"{statistics.median(r['attrs_median'] for r in oks if r.get('attrs_median') is not None):g}" if any(r.get("attrs_median") is not None for r in oks) else "—"
    st = ", ".join(f"{k} {v}" for k, v in Counter(r.get("status") for r in rows).items())
    note = next((esc(r.get("note"))[:120] for r in reversed(rows) if r.get("note")), "")
    w(f"| `{sid}` | {len(rows)} | {len(oks)} | {med} | {att} | {st} | {note} |")
w("")
above = []
for sid in sorted(set(old) - set(by_id)):
    oks = [r for r in old[sid] if r.get("status") == "ok" and r.get("rate") is not None]
    if oks and statistics.median(r["rate"] for r in oks) >= MINIMUM_RATE:
        above.append((sid, oks))
stamps = [p.name[6:22] for p in old_rounds]
w(
    "Round times of that sampler (UTC): " + ", ".join(f"{t[9:11]}:{t[11:13]}" for t in stamps) + ". They are not evenly spaced: "
    "the sampler caught up after the host slept, so several rounds fall within minutes of each other.\n"
)
for sid, oks in above:
    first = [r for r in oks][:4]
    w(
        f"**Finding — `{sid}` meets the threshold over all rounds.** Its median over the {len(oks)} `ok` rounds is "
        f"{statistics.median(r['rate'] for r in oks):.3f} events/s, and {sum(1 for r in oks if r['rate'] >= MINIMUM_RATE)} of {len(oks)} rounds "
        f"reach 1 event/s. The decision of 2026-10-13 recorded a median of 0.983 events/s from the rounds available that morning; the four "
        f"earliest rounds ({', '.join(f'{r['rate']:g}' for r in first)} events/s) all ran before 04:24 UTC (06:24 in Paris, UTC+2) and each "
        "stayed below 1 event/s, while every later round reached at least 1.5 events/s. Re-including it as a source to sample over 24 hours "
        "is an open decision (section 10).\n"
    )
missing_old = sorted(set(by_id) - set(old))
w(f"Catalog sources the `/tmp` sampler never measured (added later or measured by other tools): {', '.join(f'`{s}`' for s in missing_old) or 'none'}.\n")

# ------------------------------------------------------------------ 4. keys
keyed = [d for d in desc if d.credential]
w(f"## 4. API keys: catalog of the {len(keyed)} key-based sources\n")
w("### 4.1 Configuration as documented in the repository README\n")
w(readme_section("API keys and configuration") + "\n")
w("### 4.2 Credential variables, generated from the descriptors\n")
w("| Source | Group | Variable(s) | Needed | Sign-up | How to get it |\n|---|---|---|---|---|---|")
for d in keyed:
    c = d.credential
    w(f"| `{d.id}` | {GROUP[d.group.value]} | {', '.join(f'`{v}`' for v in c.env_vars)} | {'required' if c.required else 'optional'} | {c.sign_up_url} | {esc(c.how_to_get)} |")
w("")
w("### 4.3 Provider research files\n")
w(
    "Each provider was researched on 2026-10-13 from its official pages; the files quote the pages verbatim and mark every point that "
    "could not be confirmed as **NOT VERIFIED**. They are reproduced in full in Appendix E (e-mail addresses masked except the "
    "ENTSO-E request address). Raw copies of the fetched pages are in `/tmp/opencode/streams-session/keydocs/raw/` (not committed).\n"
)
w("| File | Covers | Bytes | SHA-256 | NOT VERIFIED items |\n|---|---|---|---|---|")
for path in sorted(KEYDOCS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    w(f"| `{path.name}` | {esc(text.splitlines()[0].lstrip('# '))[:90]} | {path.stat().st_size} | `{sha(path)[:16]}…` | {len(re.findall('NOT VERIFIED', text))} |")
w("")
w("### 4.4 How each candidate behaves without a key (live check at this record's HEAD)\n")
w(f"`stream-consumers check --seconds 30` report `{check_new.name}` (all sources, 30 s each):\n")
w("| Source | Status | Detail |\n|---|---|---|")
for d in keyed:
    r = check_rows.get(d.id, {})
    w(f"| `{d.id}` | {r.get('status')} | {esc(r.get('detail', ''))} |")
w("")
w(
    "Terms to read before signing up (from the research files): OpenSky requires a prior written agreement for any automated "
    "(\"operational\") use of its REST API, including non-profit use; Global Fishing Watch is non-commercial only (CC BY-NC 4.0), its tokens "
    "must not be shared and registration must be on behalf of an organisation; aisstream.io and Lasair publish no terms of use, only a privacy "
    "statement; ENTSO-E actual load, actual generation and day-ahead prices are not in its CC BY 4.0 free re-use list; Mastodon statuses are "
    "personal data and are masked in stored samples.\n"
)

# ------------------------------------------------------------------ 5. architecture
w("## 5. Architecture\n")
w(readme_section("Architecture") + "\n")
w("### 5.1 Files under `src/` at HEAD\n")
w(fence(sh("git", "ls-files", "src")))
w("### 5.2 Commands\n")
w(readme_section("Use") + "\n")
w("### 5.3 How rates are measured\n")
w(readme_section("How rates are measured") + "\n")

# ------------------------------------------------------------------ 6. tests
w("## 6. Test evidence\n")
w(f"All runs below were made for this record at `{head}` with a clean working tree, on {datetime.now(UTC):%Y-%m-%d} UTC. Logs: `{REC}/`.\n")
w("| Tier | Command | Result | Coverage |\n|---|---|---|---|")
w(f"| lint | `ruff check src tests` + `ruff format --check src tests` | {esc((REC / 'ruff.txt').read_text().strip())} | — |")
w(f"| unit + component | `uv run pytest --cov` | {unit_line} | `{unit_total}` (gate 100 %) |")
for i, (res, cov) in enumerate(e2e, 1):
    w(f"| e2e run {i} | `uv run pytest tests/e2e` + `coverage combine/report --rcfile=.coveragerc.e2e` | {res} | `{cov}` (gate 100 %) |")
w(f"| live | `LIVE_SECONDS=60 coverage run --rcfile=.coveragerc.live -m pytest tests/live -m live` | {live_line} | `{live_total}` (reported only) |")
w("")
w("The component and e2e tiers start a real single-node Kafka broker in Docker (`apache/kafka:3.9.1`, published on 127.0.0.1 only).\n")
w("### 6.1 Live check per source\n")
statuses = Counter(r["status"] for r in check_rows.values())
w(
    f"Report `{check_new.name}` (30 s per source): {', '.join(f'{k} {v}' for k, v in sorted(statuses.items()))}. "
    f"The earlier report `{check_old.name}` (same command, same code, before the commit) had "
    f"{', '.join(f'{k} {v}' for k, v in sorted(Counter(r['status'] for r in check_old_rows.values()).items()))}.\n"
)
w("| Source | Status | Events | Seconds | Rate (events/s) | Basis | Median attributes | First event (s) | Earlier status |\n|---|---|---|---|---|---|---|---|---|")
for d in desc:
    r = check_rows[d.id]
    w(f"| `{d.id}` | {r['status']} | {r['events']} | {r['seconds']} | {r['rate'] if r['rate'] is not None else '—'} | {r['rate_basis']} | {r['attributes_median']} | {r['first_event_s'] if r['first_event_s'] is not None else '—'} | {check_old_rows.get(d.id, {}).get('status', '—')} |")
w("")
bad = [d.id for d in desc if check_rows[d.id]["status"] not in ("ok", "key-pending")]
if bad:
    w(
        f"Not delivered in this 30 s window: {', '.join(f'`{b}`' for b in bad)}. The live tier (60 s windows, run a few minutes earlier) "
        "passed for every source, so this is recorded as a short-window miss, not a broken consumer; the 24-hour sampling decides.\n"
    )
w("### 6.2 Links\n")
w("Every documentation, terms and sign-up URL of the descriptors, the README and the documentation fixtures, fetched with `check_links.py` (Appendix D):\n")
w(fence(links_out))
w(
    "Non-200 answers explained: `www.binance.com/en/terms` answers 202 with a JavaScript challenge; the two `www.mta.info` pages answer 403 to "
    "scripts (their text was retrieved with a browser-like fetch on 2026-10-13). The two ENTSO-E Zendesk pages answered 200 at 19:43 UTC on "
    "2026-10-13 and 403 at 00:41 UTC on 2026-10-14 with the header `cf-mitigated: challenge` (a Cloudflare bot challenge, also with browser "
    "headers); the Zendesk Help Center API confirms both still exist: `api/v2/help_center/en-us/sections/12783116987028.json` → 200, \"Restful "
    "API integration guide\", updated 2026-09-21; `api/v2/help_center/en-us/articles/40921911218961.json` → 200, \"Legal Terms and Conditions\", "
    "updated 2026-09-22.\n"
)
w("Every URL in this document (after generation; Appendix E quotes many provider URLs):\n")
w(fence(doclinks_out))

w("### 6.3 Quoted phrases checked against the saved provider pages\n")
w("Each phrase quoted in the descriptors, the README or this record's prose was searched (whitespace normalised) in the research files and raw page copies:\n")
w("| Phrase | Found in |\n|---|---|")
corpus = {}
for path in list(KEYDOCS.glob("*.md")) + list((KEYDOCS / "raw").glob("*")):
    if path.is_file():
        corpus[path.relative_to(KEYDOCS)] = re.sub(r"\s+", " ", path.read_text(encoding="utf-8", errors="replace"))
for phrase in [
    "within half an hour", "Getting a key might take a day", "within 3 working days", "open to any scientists", "password protected",
    "at less than 30 second intervals", "No results were found that matched the given", "No matching data found",
    "using automation to disrupt conversations", "requires a previous written agreement, even for non-profit",
    "Five tokens per user", "Noncommercial Use Only", "API keys may only be used by trusted server-side services",
    "Within 3 seconds", "PLEASE NOT SHARE THESE TOKENS",
]:
    hits = sorted(str(k) for k, v in corpus.items() if phrase.lower() in v.lower())
    w(f"| \"{phrase}\" | {', '.join(f'`{h}`' for h in hits[:4]) + (f' (+{len(hits) - 4})' if len(hits) > 4 else '') if hits else '**NOT FOUND**'} |")
w(
    "\"No results were found that matched the given parameters\" (CTA Bus Tracker v3, error table) is split by the PDF's table layout: "
    "`raw/cta_bus_v3.txt` has \"No results were found that matched the given\" on one line and \"parameters.\" on the next, with the "
    "neighbouring column's text in between.\n"
)

# ------------------------------------------------------------------ 7. bugs
w("## 7. Defects found and fixed\n")
w("### 7.1 Cancellation swallowed by `websockets` (fixed in `f4af707`)\n")
w(
    "- **Symptom:** the first full `profile` run over 54 sources (systemd unit `stream-profile-20261013`) was still running about 1.5 hours after it should have ended. It was stopped at 19:44 UTC on 2026-10-13.\n"
    "- **Diagnosis:** an in-process watchdog (`hang/watchdog.py`) dumped the remaining tasks: two pump tasks of `MergedEventSource` (source `gemini`) were still alive after cancellation.\n"
    "- **Root cause:** `websockets` 15.0.1 (pinned) through 17.2 (the latest release, tested in a separate environment) raises `AssertionError(\"cannot reset() while queue isn't empty\")` instead of `CancelledError` when `recv()` is cancelled while reassembling a fragmented message and another frame is already queued. Our retry loops catch `Exception`, took it for a provider failure and reconnected forever.\n"
    "- **Fix:** `raise_if_cancelling()` in `transports/base.py` re-raises a cancellation when the current task is being cancelled, whatever the library raised; `MergedEventSource` cancels its children again until every one has stopped.\n"
    "- **Tests:** `tests/component/test_transports.py::test_websocket_cancelled_mid_fragmented_message_stops_instead_of_reconnecting` (real `websockets` server and client; fails without the fix), `test_merged_close_cancels_again_until_every_child_has_stopped`, `test_push_reconnect_loop_stops_when_its_task_is_cancelled`, `test_poll_retry_loop_stops_when_its_task_is_cancelled`, and an e2e source (`disguised_cancel`) that disguises its cancellation and must still let the CLI exit on time.\n"
    f"- **After the fix:** the profile re-run (unit `stream-profile-20261013b`) finished in about 2 minutes: report `{profile_path.name}`.\n"
    "- Saved as project memory 1421.\n"
)
w("### 7.2 Earlier defects (fixed in `9c37757`, reported when PR #1 was opened)\n")
w("| Defect | Effect | Where it is handled now |\n|---|---|---|")
for row in [
    ("A provider listed the same record twice in one poll", "double counting; Entur read ~571 events/s instead of ~89", "`domain/policy.py` change detection; `tests/unit/test_domain.py::test_a_key_repeated_in_one_snapshot_counts_once`"),
    ("METAR repeats column names (four cloud layers)", "three of four cloud layers lost", "`CsvDecoder.unique` adds `_2`, `_3`…; `tests/unit/test_decoders.py::test_repeated_column_names_get_suffixes`"),
    ("OpenStreetMap XML entities (`&amp;`) left undecoded", "wrong tag values", "`sources/osm.py` applies `html.unescape` to attributes and tags"),
    ("A source that failed to start crashed the whole `check` run", "one bad source stopped all others", "per-source error report; e2e source `bad_interval` must report `ValueError…` while the run continues"),
    ("MQTT shutdown blocked the event loop about 1 s", "every other stream froze at shutdown", "MQTT connection loop rewritten to stop in under a second (no dedicated test identified for this record)"),
    ("A failed SeedLink handshake left the connection open", "socket leak", "connection closed on handshake failure (no dedicated test identified for this record)"),
]:
    w("| " + " | ".join(row) + " |")
w("")

# ------------------------------------------------------------------ 8. measurements
w("## 8. Measurements so far\n")
w("### 8.1 Hourly sampling (in progress)\n")
w(
    "Command: `stream-consumers sample --interval 3600 --window 60`. Rounds 1–3 ran from code `e719191` "
    "(unit `stream-sampling-20261013b`, reports `data/reports/sampling-20261013b`); that unit was stopped at 19:57 UTC because the old code could "
    "hang on the bug of 7.1. Rounds 4–24 run from `f4af707` (unit `stream-sampling-20261013c`, 21 rounds from 20:45 UTC, reports "
    "`data/reports/sampling-20261013c`, expected end about 2026-10-14 16:46 UTC). Two rounds of an earlier cancelled run (08:46 and 09:46 UTC "
    "on 2026-10-13) were deleted by mistake before being listed; they are not cited anywhere.\n"
)
w("| Round | File | Scheduled (UTC) | Sources | ok | Other statuses |\n|---|---|---|---|---|---|")
for i, (path, doc) in enumerate(rounds, 1):
    st = Counter(r["status"] for r in doc["reports"])
    sched = doc.get("scheduled_at")
    sched_txt = utc(sched) if isinstance(sched, (int, float)) else esc(sched)
    w(f"| {i} | `{path.parent.name}/{path.name}` | {sched_txt} | {len(doc['reports'])} | {st.get('ok', 0)} | {', '.join(f'{k} {v}' for k, v in st.items() if k != 'ok') or '—'} |")
w("")
w(
    f"Rates per source and round (events/s; `·` = not `ok`, with the status in the last column). The median uses the repository rule "
    f"`policy.median_rate` (rounds with status `ok` and a rate). It is **provisional** ({len(rounds)} of 24 rounds). "
    f"`≥ {MINIMUM_RATE:g}` marks a provisional median at or above the threshold.\n"
)
w("| id | " + " | ".join(f"R{i}" for i in range(1, len(rounds) + 1)) + " | Median | ≥ 1 | Not ok |\n|---|" + "---|" * (len(rounds) + 3))
for d in desc:
    cells, notok = [], Counter()
    reps = per_source[d.id]
    for r in reps:
        if r is None:
            cells.append("—")
        elif r.status is RunStatus.OK and r.rate is not None:
            cells.append(f"{r.rate:g}")
        else:
            cells.append("·")
            notok[r.status.value] += 1
    med = median_rate([r for r in reps if r is not None])
    flag = "yes" if med is not None and med >= MINIMUM_RATE else ("no" if med is not None else "—")
    w(f"| `{d.id}` | " + " | ".join(cells) + f" | {f'{med:g}' if med is not None else '—'} | {flag} | {', '.join(f'{k} {v}' for k, v in notok.items()) or '—'} |")
w("")
w("### 8.2 Profile run of 2026-10-13 (fixed code)\n")
w(
    f"Command: `stream-consumers profile --max-events 500 --seconds 120 --concurrency 64`; report `{profile_path.relative_to(REPO)}`, "
    "masked samples in `data/profile-20261013/<id>.jsonl` (git-ignored). Fields counted on up to 500 events per source.\n"
)
w("| id | Status | Events | Seconds | Rate | Basis | Median attributes | First event (s) | Fields seen | Fields ≥ 90 % present |\n|---|---|---|---|---|---|---|---|---|---|")
for d in desc:
    p = profiles.get(d.id)
    if p is None:
        w(f"| `{d.id}` | (absent) | | | | | | | | |")
        continue
    r = p["run"]
    fields = p.get("fields") or []
    w(f"| `{d.id}` | {r['status']} | {r['events']} | {r['seconds']} | {r['rate'] if r['rate'] is not None else '—'} | {r['rate_basis']} | {r['attributes_median']} | {r['first_event_s'] if r['first_event_s'] is not None else '—'} | {len(fields)} | {sum(1 for f in fields if f.get('present_ratio', 0) >= 0.9)} |")
w("")

# ------------------------------------------------------------------ 9. resume
w("## 9. How to resume\n")
w("| What | Where |\n|---|---|")
for k, v in [
    ("Code", f"`{REPO}`, branch `main` (PR #1 merged)"),
    ("Running job", "systemd user unit `stream-sampling-20261013c` (`systemctl --user status stream-sampling-20261013c`), script `/tmp/opencode/streams-session/run_sampling_c.sh`, log `data/sampling-20261013c.log`"),
    ("Sampling reports", "`data/reports/sampling-20261013b/` (rounds 1–3) + `data/reports/sampling-20261013c/` (rounds 4–24); combine both"),
    ("Profile", f"`{profile_path.relative_to(REPO)}`, `data/profile-20261013/`"),
    ("Provider research", "`/tmp/opencode/streams-session/keydocs/*.md` (+ `raw/`), reproduced in Appendix E"),
    ("Fixture builder", "`/tmp/opencode/streams-session/build_doc_fixtures.py` (Appendix D)"),
    ("This record's logs", f"`{REC}/`"),
    ("Resume note", "session note #33; project memory 1421 (websockets constraint)"),
]:
    w(f"| {k} | {v} |")
w("")
w(
    "When keys arrive:\n\n"
    "1. Put them in `stream-consumers/.env` (copy of `.env.example`; never committed).\n"
    "2. `uv run stream-consumers keys` — every variable of that source must read `set`.\n"
    "3. `uv run stream-consumers check <id>` — must be `ok` with events.\n"
    "4. Capture real messages and replace that source's documentation-example fixture (`tests/fixtures/raw/<id>.json`), personal values masked; keep the 100 % gates.\n"
    "5. Sample the source hourly for 24 rounds; promote it to group C (B for aisstream.io) if its median is at least 1 event/s, otherwise remove it.\n\n"
    "When the 24-hour sampling ends: compute the median per source over both report folders, remove every source below 1 event/s except GDELT, "
    "commit, and write the averages as a new dated record. Then start the student catalog in the `claude-course-streams` worktree.\n"
)

# ------------------------------------------------------------------ 10. open items
w("## 10. Open items and limits\n")
for item in [
    f"The medians in 8.1 are provisional ({len(rounds)} of 24 rounds).",
    "`policy.median_rate` ignores rounds whose status is not `ok` (for example `no-events`). A source that delivers nothing in some rounds is judged only on the rounds where it delivered. Whether such rounds should count as 0 events/s must be decided before the final list.",
    "Rates come from 60-second windows (sampling) and 30-second windows (check); a short window can see no event from a source that delivered in other windows (`polygon_logs` in 6.1, `eth_logs` in round 7 of 8.1).",
    "The 11 candidates are tested only against the providers' documentation examples; their real message shape and rate are unknown until a key exists.",
    "Points marked NOT VERIFIED in the research files (Appendix E) remain unconfirmed: e.g. Fink broker addresses and licence, Lasair terms, aisstream.io bandwidth limit, ENTSO-E current resolutions, WMATA tier limits, GFW data latency.",
    "OpenSky's terms require a written agreement for automated use; using `opensky` continuously without one may break those terms.",
    "Five provider pages answer scripts with a challenge or 403 (Binance, two mta.info pages, two ENTSO-E Zendesk pages; 6.2); their existence was confirmed by other means.",
    "Branch protection is unavailable for private repositories on the GitHub Free plan; `main` is protected only by convention.",
    "The student catalog (Spanish, Canvas draft) has not been started.",
    "Vélib' Paris was excluded on its earliest rounds; over all 15 rounds of the cross-check sampler its median is above 1 event/s (3.3). "
    "Decision needed: add it back and let the 24-hour sampling decide. The same check should apply to every exclusion that rested on few rounds.",
]:
    w(f"- {item}")
w("")

# ------------------------------------------------------------------ appendices
w("## Appendix A — `.env.example` (generated by `stream-consumers keys --template`)\n")
w(fence((REPO / ".env.example").read_text(encoding="utf-8"), "bash"))
w("## Appendix B — Commit messages\n")
w(fence(sh("git", "log", "--reverse", "--format=commit %H%nDate:   %ci%n%n%B")))
w("## Appendix C — Pull request #1\n")
pr = json.loads(sh("gh", "pr", "view", "1", "--json", "title,body,createdAt,url,comments"))
w(f"Title: {pr['title']} · created {pr['createdAt']} · {pr['url']}\n")
w(fence(pr["body"], "markdown"))
for c in pr.get("comments", []):
    w(f"Comment of {c.get('createdAt')}:\n")
    w(fence(c.get("body", ""), "markdown"))
w("## Appendix D — Helper scripts used for this work (not part of the repository)\n")
for path in [
    SESSION / "build_doc_fixtures.py",
    SESSION / "check_links.py",
    SESSION / "run_sampling.sh",
    SESSION / "run_sampling_c.sh",
    SESSION / "hang/watchdog.py",
    REC / "gen_record.py",
    REC / "check_doc_links.py",
]:
    if path.exists():
        w(f"### `{path}` (sha256 `{sha(path)[:16]}…`)\n")
        w(fence(path.read_text(encoding="utf-8"), "python" if path.suffix == ".py" else "bash"))
w("## Appendix E — Provider research files (verbatim, e-mail addresses masked)\n")
for path in sorted(KEYDOCS.glob("*.md")):
    text = mask_emails(path.read_text(encoding="utf-8"))
    text = re.sub(r'(center-block"[^>]*>)[0-9a-f]{32}(</p>)', r"\1<WMATA public demo key, shown on the cited page; not reproduced>\2", text)
    if path.stem == "mastodon":
        text = re.sub(
            r'^(data: |  "payload": ")\{.*$',
            lambda m: m.group(1) + "[official example payload omitted here: it is a real user's post (account, content, avatar URLs); "
            "it is in the cited documentation page and in raw/ex_masto_*.txt]",
            text,
            flags=re.M,
        )
    text = re.sub(r"^(#{1,3}) ", lambda m: "#" * (len(m.group(1)) + 3) + " ", text, flags=re.M)
    w(f"### E.{path.stem} — `{path.name}`\n")
    w(text.rstrip() + "\n")
w("## Appendix F — Tool versions\n")
w("| Tool | Version |\n|---|---|")
from importlib.metadata import version as dist_version

versions = {"python": sys.version.split()[0]}
for dist in ("websockets", "aiohttp", "aiokafka", "fastavro", "paho-mqtt", "pyzmq", "nats-py", "pyais", "gtfs-realtime-bindings", "protobuf", "cryptography", "pytest", "pytest-asyncio", "pytest-cov", "coverage", "ruff"):
    try:
        versions[dist] = dist_version(dist)
    except Exception:  # noqa: BLE001 - a missing distribution is reported as such
        versions[dist] = "not installed"
versions["uv"] = sh("uv", "--version").strip()
versions["docker"] = sh("docker", "--version").strip()
versions["Kafka test image"] = "apache/kafka:3.9.1"
for k, v in versions.items():
    w(f"| {k} | {v} |")
w("")

OUT.write_text(mask_emails("\n".join(out)) + "\n", encoding="utf-8")
print(OUT, len(out), "blocks", OUT.stat().st_size, "bytes")
```

### `/tmp/opencode/streams-session/record/check_doc_links.py` (sha256 `fdbd6eb6d3eb9062…`)

```python
"""HTTP status of every distinct http(s) URL in a Markdown file, with each non-200 answer classified.

Placeholders (<...>, {...}, $..., YYYY) and local or example hosts are skipped. A non-200 answer that matches
no rule below is printed as UNEXPLAINED.
"""

import asyncio
import re
import sys
from pathlib import Path

import aiohttp

UA = "Mozilla/5.0 (X11; Linux x86_64) stream-consumers link check (course repository)"
KEY_GATED = (
    "api.wmata.com/", "api.nationaltransport.ie/gtfsr/v2", "bustime-classic.mta.info/api", "bustime.mta.info/api",
    "gateway.api.globalfishingwatch.org", "web-api.tp.entsoe.eu/api", "web-api.tp-iop.entsoe.eu/api", "api.lasair.lsst.ac.uk/api/cone",
    "api.lasair.lsst.ac.uk/api/query", "streaming.mastodon.social/api/v1/streaming",
)
RULES = [
    (lambda u, s: s == "401" and any(k in u for k in KEY_GATED), "API endpoint that requires a key: HTTP 401 without one is the expected gate"),
    (lambda u, s: "transparencyplatform.zendesk.com/hc/" in u and s == "403", "Cloudflare bot challenge (cf-mitigated: challenge); pages confirmed through the Zendesk Help Center API (section 6.2)"),
    (lambda u, s: "github.com/non-relational-dbs/stream-consumers" in u and s == "404", "private repository: GitHub answers 404 to unauthenticated clients"),
    (lambda u, s: s == "405" and ("openid-connect/token" in u or "entur.io/realtime/v2/vehicles/graphql" in u), "POST-only endpoint (OAuth token / GraphQL); a GET is refused by design"),
    (lambda u, s: s == "400" and ("mastodon.social/api/v1/streaming" in u), "WebSocket/streaming endpoint that needs a stream parameter and a token"),
    (lambda u, s: "siri.org.uk/siri" in u, "XML namespace identifier quoted inside a SIRI response, not a web page"),
    (lambda u, s: s in ("404", "500") and re.search(r"(api\.wmata\.com/(TrainPositions|gtfs)$|nationaltransport\.ie/gtfsr$|opensky-network\.org/api$|api\.lasair\.lsst\.ac\.uk/api/?$)", u), "API base path quoted from the documentation, not itself a document"),
    (lambda u, s: u == "https://aisstream.io/terms" and s == "404", "recorded in the research file as HTTP 404: aisstream.io publishes no terms page"),
    (lambda u, s: u == "https://github.com/lasair-uk/lasair_api" and s == "404", "recorded in the research file: the lasair package's declared homepage returns 404"),
    (lambda u, s: "api.fink-portal.org" in u and "Timeout" in s, "recorded in the research file: api.fink-portal.org timed out; the LSST and ZTF Fink APIs answered"),
    (lambda u, s: "www.mta.info/" in u and s == "403", "mta.info answers 403 to scripts; text retrieved with a browser-like fetch on 2026-10-13"),
    (lambda u, s: u == "https://www.binance.com/en/terms" and s == "202", "JavaScript challenge (HTTP 202)"),
    (lambda u, s: u.startswith("https://doi.org/10.1093/") and s == "403", "DOI resolves to Oxford University Press, which answers 403 to scripts"),
]

text = Path(sys.argv[1]).read_text(encoding="utf-8")
_d = re.search(r"^## Appendix D", text, re.M)
_e = re.search(r"^## Appendix E", text, re.M)
if _d and _e:  # helper-script source code: URLs there are code, not references
    text = text[: _d.start()] + text[_e.start() :]
found = set()
for raw in re.findall(r"https?://[^\s)`\"'|]+", text):
    url = raw.split("](")[0].replace("\\", "").rstrip(".,;:*”’").rstrip("]")
    found.add(url)
skip = re.compile(r"[<>{}$]|YYYY|localhost|127\.0\.0\.1|example\.|\.example\b|\[\^")
urls = sorted(u for u in found if not skip.search(u))
skipped = sorted(found - set(urls))


async def once(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=40)) as r:
            return str(r.status)
    except Exception as exc:  # noqa: BLE001 - every failure is reported
        return f"{type(exc).__name__}"


async def status(session: aiohttp.ClientSession, sem: asyncio.Semaphore, url: str) -> tuple[str, str]:
    """One retry after 20 s for a 5xx answer or a connection error (transient server or rate-limit errors)."""
    async with sem:
        first = await once(session, url)
    if first.isdigit() and int(first) < 500:
        return url, first
    await asyncio.sleep(20)
    async with sem:
        second = await once(session, url)
    return url, second if second == "200" else f"{second} (also {first} before the retry)"


async def main() -> None:
    sem = asyncio.Semaphore(16)
    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        results = await asyncio.gather(*(status(session, sem, u) for u in urls))
    bad = [(u, s) for u, s in results if s != "200"]
    unexplained = 0
    lines = []
    for u, s in bad:
        reason = next((r for rule, r in RULES if rule(u, s.split()[0])), None)
        unexplained += reason is None
        lines.append(f"  {s:>7}  {u}\n           {reason or 'UNEXPLAINED'}")
    print(
        f"{len(results)} distinct URLs checked: {len(results) - len(bad)} HTTP 200, {len(bad) - unexplained} non-200 explained, "
        f"{unexplained} unexplained; {len(skipped)} skipped as placeholders or local/example hosts"
    )
    print("\n".join(lines))


asyncio.run(main())
```

## Appendix E — Provider research files (verbatim, e-mail addresses masked)

### E.aisstream — `aisstream.md`

#### aisstream.io — key/credential documentation (fetched 2026-10-13 ~18:00 UTC)

Sources fetched now (raw copies in `raw/`):
- D1 `https://aisstream.io/documentation` (rendered page + embedded `__NEXT_DATA__` schema JSON) → `raw/aisstream_doc.html`
- D2 `https://aisstream.io/` (home) → `raw/aisstream_home.html`
- D3 `https://aisstream.io/account` (redirect target of `/authenticate`) + JS chunk `/_next/static/chunks/pages/account-f0c83b27f25c46e2.js`
- D4 `https://aisstream.io/privacypolicy` → `raw/aisstream_privacy.html`
- G1 `https://github.com/aisstream/ais-message-models` — `README.md`, `type-definition.yaml` (OpenAPI 3.0) → `raw/aisstream_models_readme.md`, `raw/ais_openapi.yaml`
- G2 `https://github.com/aisstream/example` — `README.md`, `python/main.py` → `raw/aisstream_example_readme.md`, `raw/ais_example_main.py`

##### 1. Sign-up / credential process

D2 (home, "Quick start"):
> 1 Create a key — Sign in with GitHub and create an API key in Account.
> 2 Send a subscription — Authenticate and set bounding boxes with optional message-type filters.
> 3 Read continuously — Decode each binary WebSocket frame as JSON and handle events promptly.

D3 (account page, signed-out state, from its JS chunk):
> "Sign in to manage API keys" … "AIS Stream uses GitHub for account authentication. API keys may only be used by trusted server-side services." … [button] "Continue with GitHub" (href `/api/login/github`)
> "API keys" — "Keys remain masked after creation. Disable a key before deleting it." … [button] "Create API key"

D1 §02 Authenticate:
> **Use WSS and server-side secrets.** Create and rotate keys from [Account](/account). Existing keys are masked; a newly generated key is shown once. Disable a key before permanently deleting it. Direct browser connections are not permitted; proxy only the information your clients need from your own server.

G2 README:
> Before you can use these examples, you will need to sign up for an AISStream API key at [aisstream.io](https://aisstream.io/authenticate).

(`https://aisstream.io/authenticate` now redirects to `https://aisstream.io/account` — observed HTTP 200 after redirect.)

##### 2. Endpoint, protocol, subscription message

- Endpoint (D1 header): `wss://stream.aisstream.io/v0/stream`
- Protocol (D1 §01): "Create a WebSocket connection with `permessage-deflate`, then send one complete JSON subscription within three seconds."
- Deadline: D1 limits table — "Initial subscription | Within 3 seconds | The connection closes if no valid subscription arrives."

D1 §03 Subscribe:
> Bounding boxes are required. MMSI and message-type filters are optional. Resending a subscription replaces the active configuration. Each accepted subscription or replacement returns a `SubscriptionConfirmation`; invalid subscriptions do not.

| Field | Required | Meaning (D1 verbatim) |
| --- | --- | --- |
| APIKey | Yes | Account API key |
| BoundingBoxes | Yes | Pairs of latitude/longitude corners |
| FiltersShipMMSI | No | Up to 200 nine-character MMSIs |
| FilterMessageTypes | No | Supported message type names |

Schema explorer (D1 `__NEXT_DATA__`, model `SubscriptionMessage`):
- `APIKey` string, required — "API key used to authenticate the subscription."
- `BoundingBoxes` `number<double>[][][]`, required — "Pairs of latitude/longitude corners."
- `FiltersShipMMSI` `string[]`, optional — "Optional list of nine-character MMSIs."
- `FilterMessageTypes` `AisMessageTypes[]`, optional — "Optional list of AIS message type names."

G1 OpenAPI (`type-definition.yaml`): `BoundingBoxes` = array of array of array of `number/double`, innermost `minItems: 2, maxItems: 2`; `FiltersShipMMSI` items `type: string, minLength: 9, maxLength: 9`.

**Coordinate order:** `[latitude, longitude]` per corner ("Pairs of latitude/longitude corners"); each box = `[[lat1, lon1], [lat2, lon2]]`; `BoundingBoxes` is a list of boxes. Official example: `[[[25.835, -80.208], [25.603, -79.879]]]`.
- NOT VERIFIED: which corners are required (e.g., NW/SE vs any two opposite corners) and whether corner order matters — the docs only say "Pairs of latitude/longitude corners". The official Python example uses `[[[-11, 178], [30, 74]]]` (first corner has the lower latitude), and the docs example uses a first corner with the higher latitude, suggesting either order is accepted, but this is not stated.

Official subscription example (D1 §03, verbatim):
```json
{
  "APIKey": "<YOUR_API_KEY>",
  "BoundingBoxes": [
    [
      [
        25.835,
        -80.208
      ],
      [
        25.603,
        -79.879
      ]
    ]
  ],
  "FiltersShipMMSI": [
    "368207620"
  ],
  "FilterMessageTypes": [
    "PositionReport"
  ]
}
```

Official Python example (G2 `python/main.py`, verbatim excerpt):
```python
    # Enables compression, which aisstream.io requires to serve full message bandwidth.
    async with websockets.connect("wss://stream.aisstream.io/v0/stream",
                                  compression="deflate") as websocket:
        subscribe_message = {"APIKey": "<YOUR API KEY>", "BoundingBoxes": [[[-11, 178], [30, 74]]]}
```

Supported message types (D1 "Supported message types (25)", identical to G1 enum `AisMessageTypes`):
PositionReport, UnknownMessage, AddressedSafetyMessage, AddressedBinaryMessage, AidsToNavigationReport, AssignedModeCommand, BaseStationReport, BinaryAcknowledge, BinaryBroadcastMessage, ChannelManagement, CoordinatedUTCInquiry, DataLinkManagementMessage, DataLinkManagementMessageData, ExtendedClassBPositionReport, GroupAssignmentCommand, GnssBroadcastBinaryMessage, Interrogation, LongRangeAisBroadcastMessage, MultiSlotBinaryMessage, SafetyBroadcastMessage, ShipStaticData, SingleSlotBinaryMessage, StandardClassBPositionReport, StandardSearchAndRescueAircraftReport, StaticDataReport.
Plus the control message type `SubscriptionConfirmation` (D1 envelope model `SubscriptionConfirmationMessage`).

##### 3. How credentials are sent

Inside the first JSON WebSocket message as field `APIKey` (D1 §01 code: `APIKey: process.env.AISSTREAM_API_KEY`). No HTTP header / query-parameter auth is documented. D1 FAQ: "Direct browser connections are not permitted. Connect from your own server and proxy only the information each client needs. This protects the API key and reduces load on the stream service."

##### 4. Rate limits / quotas (D1 §05, verbatim table)

| Constraint | Limit | Consideration |
| --- | --- | --- |
| Connections per account | 3 subscribed connections | A fourth subscription is rejected. |
| Connections per originating IP | 3 open connections | The limit applies before authentication. |
| Initial subscription | Within 3 seconds | The connection closes if no valid subscription arrives. |
| Subscription updates | 1 per second per connection | A faster update closes the connection. Updates replace, rather than merge with, the previous subscription. |
| MMSI filters | 200 per subscription | Each MMSI must be a nine-character string. |
| Connection speed | Read continuously | If you do not consume messages quickly enough and sufficient buffered messages accumulate, the service drops messages. |

> ### Uncompressed connections
> Beginning in September 2026, uncompressed connections will be subject to per-user bandwidth limits, and messages exceeding those limits will be dropped.

FAQ (D1, verbatim):
> Why did my connection close? — Common causes are a late or malformed subscription, an invalid key, a connection-limit breach, subscription updates faster than once per second, fragmented client messages, missed keepalive activity, or a slow connection.
> What uptime or delivery guarantees are provided? — The service currently provides no SLA or uptime guarantee, and events are not durably replayed. Plan for interruptions, reconnect with backoff, and persist messages your application cannot afford to lose.
> How should I handle reconnects? — Treat the stream as a long-lived but fallible connection. Reconnect with exponential backoff and jitter, then send a complete replacement subscription within three seconds.

NOT VERIFIED: numeric value of the per-user bandwidth limit for uncompressed connections (not stated).

##### 5. Message format

D1 §04:
> `MessageType` selects the typed object under `Message`. `MetaData` contains normalized AIS context such as MMSI and last known position. A subscription confirmation has no AIS metadata; its `CompressionEnabled` value reports whether `permessage-deflate` was negotiated for that connection. The server sends binary WebSocket frames containing UTF-8 JSON.
> What WebSocket framing should I expect? — The service sends binary WebSocket frames whose payload is UTF-8 JSON. Decode the frame bytes before parsing JSON. Client subscription frames may be text or binary, but fragmented messages are not supported.

Envelope (`AisStreamMessage`, D1 schema explorer):
- `MetaData` object, required — "Normalized context added by AIS Stream."
- `MessageType` AisMessageTypes, required — "Name of the serialized stream message."
- `Message` object, required — "Typed stream message payload."

Path to a record: `msg["Message"][msg["MessageType"]]` (e.g. `Message.PositionReport`); G2 Python comment: "the message parameter contains a key of the message type which contains the message itself".

`MetaData` fields: officially shown only by example — `MMSI`, `ShipName`, `Latitude`, `Longitude`. NOT VERIFIED: the complete MetaData field list (the OpenAPI schema types it as a bare `object`; no field list is published).

`PositionReport` fields (D1 schema explorer, verbatim descriptions):
MessageID integer "Numeric AIS message identifier."; RepeatIndicator integer "Number of times the AIS message was repeated."; UserID integer "Vessel or station MMSI."; Valid boolean "Whether the decoded value passed validation."; NavigationalStatus integer "Reported navigation status code."; RateOfTurn integer "Reported rate-of-turn value."; Sog double "Speed over ground in knots."; PositionAccuracy boolean "Reported position-accuracy flag."; Longitude double "Longitude in decimal degrees."; Latitude double "Latitude in decimal degrees."; Cog double "Course over ground in degrees."; TrueHeading integer "True heading in degrees."; Timestamp integer "AIS UTC-second timestamp."; SpecialManoeuvreIndicator integer; Spare integer "Reserved protocol bits." (advanced); Raim boolean "Receiver autonomous integrity monitoring flag."; CommunicationState integer "Raw AIS radio communication state." (advanced).

`ShipStaticData` fields (D1 schema explorer + G1 OpenAPI): MessageID, RepeatIndicator, UserID ("Vessel or station MMSI."), Valid, AisVersion integer, ImoNumber integer, CallSign string, Name string, Type integer, Dimension object {A,B,C,D integers}, FixType integer, Eta object {Month, Day, Hour, Minute integers}, MaximumStaticDraught double, Destination string, Dte boolean, Spare boolean. Descriptions in the explorer are only generic ("AIS ImoNumber field.", "AIS Destination field.", …). NOT VERIFIED: units/semantics of Dimension A–D, Type codes, MaximumStaticDraught units (not documented by aisstream).

##### 6. Official example messages (verbatim)

D1 §04 "Position report · JSON" (https://aisstream.io/documentation#messages):
```json
{
  "MessageType": "PositionReport",
  "MetaData": {
    "MMSI": 368207620,
    "ShipName": "EXAMPLE VESSEL",
    "Latitude": 25.7617,
    "Longitude": -80.1918
  },
  "Message": {
    "PositionReport": {
      "MessageID": 1,
      "UserID": 368207620,
      "Sog": 12.4,
      "Cog": 86.7,
      "TrueHeading": 87,
      "Valid": true
    }
  }
}
```

D1 §04 "Subscription confirmation · JSON":
```json
{
  "MessageType": "SubscriptionConfirmation",
  "Message": {
    "CompressionEnabled": true
  }
}
```

D1 §06 "PositionReport · schema-shaped JSON" (placeholder values):
```json
{
  "MessageID": 1,
  "RepeatIndicator": 1,
  "UserID": 1,
  "Valid": true,
  "NavigationalStatus": 1,
  "RateOfTurn": 1,
  "Sog": 12.3,
  "PositionAccuracy": true,
  "Longitude": 12.3,
  "Latitude": 12.3,
  "Cog": 12.3,
  "TrueHeading": 1,
  "Timestamp": 1,
  "SpecialManoeuvreIndicator": 1,
  "Spare": 1,
  "Raim": true,
  "CommunicationState": 1
}
```

ShipStaticData: NO official full example envelope found in D1, D2, G1 or G2 (only the schema field list with placeholder `example` values such as `1`, `"string"`, `{}` in the explorer data).

##### 7. Probe without credentials (2026-10-13T18:17:31Z, Python `websockets` 16.1.1, `compression="deflate"`, 30 s limits)

1. Connect, send nothing: WebSocket handshake succeeded (`connected: true`); server closed the connection after ~4.08 s total (close code 1006, no close frame/reason); no message received. Consistent with the documented 3-second subscription deadline.
2. Connect, send `{"APIKey": "invalid-probe-key", "BoundingBoxes": [[[25.835, -80.208], [25.603, -79.879]]]}`: handshake succeeded; closed after ~1.22 s with code 1006, empty reason, no `SubscriptionConfirmation` and no error message (first 300 bytes: none). Consistent with "invalid subscriptions do not [return a SubscriptionConfirmation]".

##### 8. Terms / licence

- `https://aisstream.io/terms` → HTTP 404. No terms-of-service page is linked from the site footer (footer links: Documentation, Account, Privacy, Support).
- NOT VERIFIED: any data licence / terms of use for the AIS data — none published on aisstream.io as of this fetch.
- Privacy policy `https://aisstream.io/privacypolicy` (verbatim): "We automatically receive limited device and request information, including your IP address, browser type, referring page, and request timestamps. If you create an account, we also receive the GitHub identity required to authenticate you." / "We use request and account information to operate, secure, troubleshoot, and improve the service. We do not use Google Analytics or advertising trackers."
- Home page D2: "Track ship movements, monitor maritime accidents and discover ship's cargo from aisstream.io's websocket api in real-time and for free."
- Code/model repository licence (G1 README, applies to the model definitions, not the data): "This project is licensed under the MIT License - see the LICENSE file for details."
- Usage constraint (D3): "API keys may only be used by trusted server-side services."

### E.cta — `cta.md`

#### CTA (Chicago) — Bus Tracker API `getvehicles` + Train Tracker Locations API `ttpositions.aspx`

Fetched: 2026-10-13 (UTC ~18:17–18:21). Raw copies (PDFs + extracted text) in `/tmp/opencode/streams-session/keydocs/raw/cta_*`.

Official sources:
- Bus Tracker page: https://www.transitchicago.com/developers/bustracker/
- Bus Tracker API **v3** PDF ("v3.0 / rev. 2025-04-21"): https://www.transitchicago.com/assets/1/6/cta_Bus_Tracker_API_Developer_Guide_and_Documentation_2025-04-21.pdf
- Bus Tracker API **v2** PDF ("v2.0 / rev. 2016-09-29"): https://www.transitchicago.com/assets/1/6/cta_Bus_Tracker_API_Developer_Guide_and_Documentation_20160929.pdf
- Train Tracker page: https://www.transitchicago.com/developers/traintracker/
- Train Tracker PDF ("v1.46 / rev. 04-Aug-2024"): https://www.transitchicago.com/assets/1/6/cta_Train_Tracker_API_Developer_Guide_and_Documentation.pdf
- Train Tracker key form: https://www.transitchicago.com/developers/traintrackerapply/
- Terms: https://www.transitchicago.com/developers/terms/

##### 1. Sign-up and key delivery

###### Bus Tracker (https://www.transitchicago.com/developers/bustracker/)

> To use these APIs, you must agree to the [Terms of Service](/developers/terms/) and apply for a key. You'll also need a Bus Tracker account.

> ### How to get an API key
> First, you'll need to get a Bus Tracker account. If you don't have one, sign up and activate your account first. Then:
> 1. **[Sign into Bus Tracker.](http://www.ctabustracker.com/bustime/login.jsp)**
> 2. Choose on **My Account** in the upper right-hand corner of the page.
> 3. Follow the link under "**Developer API**" to apply.

v3 PDF, p.2:

> In order to use the API, you must sign in to their CTA Bus Tracker account and request an API key. Only one key will be available per account. Once your request has been approved, an e-mail will be sent to you, containing the API key. After receiving the key, you will be able to make calls to the API, entering the key as part of the data request.

=> Bus key delivered **by e-mail after approval**, one key per Bus Tracker account.

###### Train Tracker (https://www.transitchicago.com/developers/traintracker/)

> To use these APIs, you must agree to the Terms of Service and apply for an API key.

> You must first get a key to use our API.  Use our API Key Application Form  to request a key and we'll review your application as soon as possible. You should get a reply pretty quickly.

Form at https://www.transitchicago.com/developers/traintrackerapply/ ("Train Tracker API Key Application"): fields First Name, Last Name, Address, Email Address, Phone Number, Purpose of Use, and checkbox "I have read and agree to the Developer License Agreement and Terms of Use (Note: You must select this checkbox to submit your application)."

Delivery channel for the Train Tracker key (e-mail vs. other): **NOT VERIFIED** — the pages say only "we'll review your application ... You should get a reply pretty quickly."; the PDF says the key is "assigned to you after agreeing to DLA and requesting a key be generated for you."

##### 2. Endpoints, method, parameters

###### Bus Tracker `getvehicles`

v3 PDF p.4 (verbatim):

> Parameters are encoded in the HTTP GET request by following the URL with a “?” and “argument=value” pairs separated by “&”.
>
> A response is returned as a well-formed XML document with a Content-Type of “text/xml”, or as a JSON document with a Content-Type of “application/json”.

> The version of the API that is being accessed is built into the URL. In the above example, “v3” represents version 3.0 of the API.
>
> The “key” parameter represents the API key assigned to the developer making the request. All requests to the API must be accompanied by a valid API key.
>
> In Versions 2 and later, an optional “format” parameter can be included to specify the response type. XML is the default response format, and is used as the default if the “format” parameter is not included. JSON can be chosen by including “format=json”.

Common parameters (v3 PDF p.5): `version` (All, required, `/v3/`, "Legal values are v1, v2, and v3."), `locale` (optional, `locale=en`), `format` (v2+, optional, `format=json`, "Legal values are “xml” and “json”. XML is the default if no format is requested.").

**v3**: `Base URL: https://www.ctabustracker.com/bustime/api/v3/getvehicles` (GET). Parameters (v3 PDF p.8, verbatim):

| Name | Value | Description |
|---|---|---|
| key | string (required) | 25-digit Bus Tracker API access key. |
| vid | comma-delimited list of vehicle IDs (not available with rt parameter) | Set of one or more vehicle IDs whose location should be returned. For example: 509,392,201,4367 will return information for four vehicles (if available). A maximum of 10 identifiers can be specified. |
| rt | comma-delimited list of route designators (not available with vid parameter) | Set of one or more route designators for which matching vehicles should be returned. For example: X3,4,20 will return information for all vehicles currently running those three routes (if available). A maximum of 10 identifiers can be specified. |
| tmres | string (optional) | Resolution of time stamps. Set to “s” to get time resolution to the second. Set to “m” to get time resolution to the minute. If omitted, defaults to “m”. |

> Note: The vid and rt parameters cannot be combined in one request. If both parameters are specified on a request to getvehicles, only the first parameter specified on the request will be processed.

Version 3 also adds `rtpidatafeed` ("Most calls now support an rtpidatafeed parameter to query desired feeds of multi-feed systems") — it appears in the getvehicles XML schema (`<xs:element name="rtpidatafeed" ... minOccurs="0"`) but is not listed in the getvehicles parameter table.

**v2**: `Base URL: http://www.ctabustracker.com/bustime/api/v2/getvehicles` (v2 PDF p.7). Same parameters `Key`, `Vid`, `Rt` ("A maximum of 10 identifiers can be specified."), `tmres`. v3 vs v2 per v3 release notes (p.45): "The URL of the request changes.", rtpidatafeed support, detours, disruption management, route-directions standardisation, RTPI changes, misc fixes. "Version 3 of the API is used by including “v3”in the request URL".

=> **Max routes per getvehicles request: 10** (both v2 and v3). Error (v3 Appendix): "Maximum number of <x> identifiers exceeded — getpredictions, getvehicles — The 'stpid' or 'vid' parameter contains too many IDs. <x> shows the maximum allowed in a single request."

###### Train Tracker Locations API `ttpositions.aspx`

Train Tracker PDF p.17 (verbatim):

> Locations API
> Description
> This API produces a list of in-service trains and basic info and their locations for one or more specified ‘L’ routes.
>
> Each separate entry describes a single train and provides coordinate, geospatial heading, certain train attributes and next stop information.
>
> Base URL
> lapi.transitchicago.com/api/1.0/ttpositions.aspx
>
> Parameters:
> Use URL query string method.

| Name | Value | Description |
|---|---|---|
| rt | Train route(s) (required) | Allows you to specify one or more routes for which you’d like train location information. |
| key | Alphanumeric API key (required) | Your unique API key, assigned to you after agreeing to DLA and requesting a key be generated for you. |
| outputType | “JSON” (optional) | If outputType=JSON is added to query string, API response will be formatted as JSON instead of XML |

Documented example requests use `http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=...&rt=red` and `...&rt=red&outputType=JSON` (GET via query string).

Max routes: Train Locations API Error Codes (PDF p.37–38):

> 107  Maximum number of rt’s per request is 8.  No more than 8 routes can be issued per request. Note duplicates are counted but not returned.

The separator for multiple `rt` values (comma vs. repeated parameter) is **NOT VERIFIED** — no multi-route example or separator is given for ttpositions in the PDF.

#### Documented route codes (Appendix A: Route ID Quick Reference, PDF p.22)

> ‘L’ routes (rapid transit train services) are identified as follows:
> - Red = Red Line (Howard-95th/Dan Ryan service)
> - Blue = Blue Line (O’Hare-Forest Park service)
> - Brn = Brown Line (Kimball-Loop service)
> - G = Green Line (Harlem/Lake-Ashland/63rd-Cottage Grove service)
> - Org = Orange Line (Midway-Loop service)
> - P = Purple Line (Linden-Howard shuttle service)
> - Pink = Pink Line (54th/Cermak-Loop service)
> - Y = Yellow Line (Skokie-Howard [Skokie Swift] shuttle service)
>
> Note: In the separate Customer Alerts API, alerts that apply specifically to the Purple Line Express (but not Purple Line Local/Shuttle service north of Howard) will use the additional route designator “Pexp”.

Locations error 106 lists them lower-case: "Valid route identifiers are: red, blue, brn, g, org, p, pink, y".

##### 3. How the key is sent

Query parameter **`key`** for both APIs (Bus: "The “key” parameter represents the API key ... All requests to the API must be accompanied by a valid API key."; Train: "key — Alphanumeric API key (required)"). No header mechanism documented.

##### 4. Rate limits

Bus Tracker web page (https://www.transitchicago.com/developers/bustracker/):

> **Q: Is there a limit to how much data I can transfer?**
> A: By default, the Bus Tracker API has a transaction limit of 100,000\* transactions/day. This helps us manage bandwidth and server resources better—but you can ask us to increase that limit, which we'll evaluate on a case-by-case basis.
>
> *\*Updated default limit from 50,000 to 100,000 in April 2024*

> **Q: How fresh is the data?**
> A: About as fresh as it can get—Bus Tracker data is updated about every 30 seconds, both on our site and in the API.

v3 PDF p.2:

> Yes. By default, one API key can make a maximum of 100,000 requests. If you believe that you will require more than 100,000 daily requests, you must request that the cap on your key be raised to handle the additional traffic.

(The older v2 PDF p.2 says 10,000 — superseded.)

Train Tracker web page (https://www.transitchicago.com/developers/traintracker/):

> The default daily transaction limit for this API is 50,000 transactions. If you need additional transactions, contact [email protected]  with your request. Additionally, there is DoS protection installed on our servers which may trigger a temporary “time-out” if a large number of transactions from a single IP address.

Locations error 102: "Maximum daily Train Tracker API usage exceeded. — Key usage has exceeded daily limits. Limits are reset at midnight."

##### 5. Response format and structure

###### getvehicles

Path: XML `bustime-response/vehicle[]`; JSON `bustime-response.vehicle[]` (errors: `bustime-response.error[]` with `msg`). Fields (v3 PDF p.9–10, verbatim descriptions):

| Field | Description |
|---|---|
| vid | Alphanumeric string representing the vehicle ID (ie. bus number) |
| tmstmp | Date and local time of the last positional update of the vehicle. ... YYYYMMDD HH:MM ... 24-hour clock. |
| lat | Latitude position of the vehicle in decimal degrees (WGS 84). |
| lon | Longitude position of the vehicle in decimal degrees (WGS 84). |
| hdg | Heading of vehicle as a 360º value, where 0º is North, 90º is East, 180º is South and 270º is West. |
| pid | Pattern ID of trip currently being executed. |
| pdist | Linear distance in feet that the vehicle has traveled into the pattern currently being executed. |
| rt | Route that is currently being executed by the vehicle (ex. “20”). |
| des | Destination of the trip being executed by the vehicle (ex. “Austin”). |
| dly | The value is “true” if the vehicle is delayed. The dly element is only present if the vehicle is delayed. |
| tablockid | TA’s version of the scheduled block identifier for the work currently being performed by the vehicle. |
| tatripid | TA’s version of the scheduled trip identifier for the vehicle’s current trip. |
| origtatripno | Trip ID defined by the TA scheduling system. |
| zone | The zone name if the vehicle has entered a defined zone, otherwise blank. |
| mode | Mode of transportation for the vehicle as a byte with range 0-4. 0 is None, 1 is Bus, 2 is Ferry, 3 is Rail, and 4 is People_Mover. |
| psgld | String representing the ratio of the current passenger count to the vehicle’s total capacity. Possible values include “FULL”, "HALF_EMPTY", "EMPTY” and "N/A". ... |
| stst | Contains the scheduled start time (in seconds past midnight) of the trip that the vehicle is running on. |
| stsd | Contains the scheduled start date (in “yyyy-mm-dd” format) of the trip that the vehicle is running on. |

The schema additionally lists `spd` (int), `srvtmstmp`, `blk`, `stopstatus`, `timepointid`, `stopid`, `sequence`, `gtfsseq`, `rtpidatafeed` without descriptions in the field table (`spd` appears in examples; its unit is NOT VERIFIED — not described). Note the schema names the timestamp `tmpstmp` while the table/examples use `tmstmp` (doc inconsistency; examples use `tmstmp`).

###### ttpositions

Path: XML `ctatt/route[@name]/train[]`; JSON `ctatt.route[].train[]` with route name in `"@name"`. Fields (PDF p.17–18, verbatim):

| Name | Description |
|---|---|
| ctatt | Root element |
| ./tmst | Shows time when response was generated in format: yyyyMMdd HH:mm:ss (24-hour format, time local to Chicago) |
| ./errCd | Numeric error code (see appendices) |
| ./errNm | Textual error description/message (see appendices) |
| ./route name= | Container element (one per route in response), name attribute indicates route per GTFS-matching route identifiers (see appendices) |
| ././train | Container element (one per train in response) |
| ./././rn | Run number |
| ./././destSt | GTFS unique stop ID where this train is expected to ultimately end its service run (experimental and supplemental only—see note below) |
| ./././destNm | Friendly destination description (see note below) |
| ./././trDr | Numeric train route direction code (see appendices) |
| ./././nextStaId | Next station ID (parent station ID matching GTFS) |
| ./././nextStpId | Next stop ID (stop ID matching GTFS) |
| ./././nextStaNm | Proper name of next station |
| ./././prdt | Date-time format stamp for when the prediction was generated: yyyyMMdd HH:mm:ss (24-hour format, time local to Chicago) |
| ./././arrT | Date-time format stamp for when a train is expected to arrive/depart: yyyyMMdd HH:mm:ss (24-hour format, time local to Chicago) |
| ./././isApp | Indicates that Train Tracker is now declaring “Approaching” or “Due” on site for this train |
| ./././isDly | Boolean flag to indicate whether a train is considered “delayed” in Train Tracker |
| ./././flags | Train flags (not presently in use) |
| ./././lat | Latitude position of the train in decimal degrees |
| ./././lon | Longitude position of the train in decimal degrees |
| ./././heading | Heading, expressed in standard bearing degrees (0 = North, 90 = East, 180 = South, and 270 = West; range is 0 to 359, progressing clockwise) |

Note: in the official JSON example all values are strings and timestamps are ISO-like (`2015-04-30T20:29:44`), unlike the `yyyyMMdd HH:mm:ss` format in the field table. The live probe also returned ISO form and an extra `TimeStamp` key (observed, undocumented).

##### 6. Official example responses (verbatim)

###### getvehicles v3 — XML (v3 PDF p.10–11)

Request: `https://www.ctabustracker.com/bustime/api/v3/getvehicles?key=89dj2he89d8j3j3ksjhdue93j&vid=509,392`

```xml
<?xml version="1.0"?>
<bustime-response>
      <vehicle>
            <vid>509</vid>
            <tmstmp>20200308 10:28</tmstmp>
            <lat>41.92124938964844</lat>
            <lon>-87.64849853515625</lon>
            <hdg>358</hdg>
            <pid>3630</pid>
            <pdist>5678</pdist>
            <rt>8</rt>
            <des>Waveland/Broadway</des>
            <spd>27</spd>
            <tablockid>2 -701</tablockid>
            <tatripid>108</tatripid>
            <origtatripno>ME_ME403_V1_AA</origtatripno>
            <zone>Bay 1</zone>
            <mode>1</mode>
            <psgld>EMPTY</psgld>
            <stst>37560</stst>
            <stsd>2020-03-08</stsd>
      </vehicle>
      <vehicle>
            <vid>392</vid>
            <tmstmp>20200308 10:28</tmstmp>
            <lat>41.91095733642578</lat>
            <lon-87.64120713719782</lon>
            <hdg>88</hdg>
            <pid>1519</pid>
            <pdist>11203</pdist>
            <rt>72</rt>
            <des>Clark</des>
            <spd>36</spd>
            <tablockid>3 -703</tablockid>
            <tatripid>108156</tatripid>
            <origtatripno>ME_ME403_V1_AA</origtatripno>
            <zone>Bay 1</zone>
            <mode>1</mode>
            <psgld>FULL</psgld>
            <stst>36900</stst>
            <stsd>2020-03-08</stsd>
      </vehicle>
</bustime-response>
```

(The malformed `<lon-87.64120713719782</lon>` is in the original.)

###### getvehicles v3 — JSON (v3 PDF p.11–12)

Request: `https://ctabustracker.com/bustime/api/v3/getvehicles?key=89dj2he89d8j3j3ksjhdue93j&vid=6438,1295&tmres=s&format=json`

```json
{
     "bustime-response": {
          "vehicle": [
                {
                     "vid": "1",
                     "tmstmp": "20200307 13:14",
                     "lat": "37.54381",
                     "lon": "-77.43878166666667",
                     "hdg": "308",
                     "pid": 1689,
                     "rt": "6",
                     "des": "BROAD WILLOW LAWN",
                     "pdist": 3481,
                     "dly": false,
                     "spd": 3,
                     "tatripid": "12",
                     "tablockid": "6-05",
                     "origtatripno": "ME_ME403_V1_AA",
                     "zone": "",
                     "mode": 1,
                     "psgld": "EMPTY",
                     "stst": 47520,
                     "stsd": "2020-03-07”
                },
                {
                     "vid": "2",
                     "tmstmp": "20200307 13:14",
                     "lat": "37.55896532837857",
                     "lon": "-77.48567781754004",
                     "hdg": "294",
                     "pid": 1559,
                     "rt": "16",
                     "des": "GROVE BF",
                     "pdist": 20156,
                     "dly": false,
                     "spd": 5,
                     "tatripid": "12",
                     "tablockid": "16-02",
                     "origtatripno": "ME_ME403_V1_AA",
                     "zone": "",
                     "mode": 1,
                     "psgld": "FULL",
                     "stst": 46140,
                     "stsd": "2020-03-07"
                }
          ]
     }
}
```

(Original contains a typographic quote `”` after the first `stsd` value, making it invalid JSON; it also shows non-Chicago coordinates and minute-resolution `tmstmp` despite `tmres=s`. Copied as-is.)

###### ttpositions — XML (Train Tracker PDF p.19–20)

Request: `http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=4ba28f6b2b8843bf9cef1c0fcc05f874&rt=red`

```xml
<?xml version="1.0" encoding="utf-8" ?>
<ctatt>
  <tmst>20130610 15:00:21</tmst>
  <errCd>0</errCd>
  <errNm />
  <route name="red">
    <train>
      <rn>804</rn>
      <destSt>30173</destSt>
      <destNm>Howard</destNm>
      <trDr>1</trDr>
      <nextStaId>41400</nextStaId>
      <nextStpId>30269</nextStpId>
      <nextStaNm>Roosevelt</nextStaNm>
      <prdt>20130610 14:58:48</prdt>
      <arrT>20130610 14:59:48</arrT>
      <isApp>1</isApp>
      <isDly>0</isDly>
      <flags />
      <lat>41.86579</lat>
      <lon>-87.62736</lon>
      <heading>358</heading>
    </train>
    <train>
      <rn>808</rn>
      <destSt>30173</destSt>
      <destNm>Howard</destNm>
      <trDr>1</trDr>
      <nextStaId>40510</nextStaId>
        <nextStpId>30099</nextStpId>
        <nextStaNm>Garfield</nextStaNm>
        <prdt>20130610 14:58:03</prdt>
        <arrT>20130610 15:00:03</arrT>
        <isApp>0</isApp>
        <isDly>0</isDly>
        <flags />
        <lat>41.78697</lat>
        <lon>-87.6187</lon>
        <heading>81</heading>
      </train>
   </route>
</ctatt>
```

###### ttpositions — JSON (Train Tracker PDF p.20–21)

Request: `http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=4ba28f6b2b8843bf9cef1c0fcc05f874&rt=red&outputType=JSON`

```json
{
    "ctatt":{
       "tmst":"2015-04-30T20:29:44",
       "errCd":"0",
       "errNm":null,
       "route":[
          {
              "@name":"red",
              "train":[
                 {
                    "rn":"827",
                    "destSt":"30173",
                    "destNm":"Howard",
                    "trDr":"1",
                    "nextStaId":"40650",
                    "nextStpId":"30125",
                    "nextStaNm":"North/Clybourn",
                    "prdt":"2015-04-30T20:29:24",
                    "arrT":"2015-04-30T20:31:24",
                    "isApp":"0",
                    "isDly":"0",
                    "flags":null,
                    "lat":"41.90383",
                    "lon":"-87.63685",
                    "heading":"269"
                 }
              ]
          }
       ]
   }
}
```

##### 7. Probe without key (2026-10-13, Python urllib, 30 s timeout)

```
UTC 2026-10-13T18:19:36Z GET https://www.ctabustracker.com/bustime/api/v3/getvehicles?rt=20&format=json
STATUS 200 | Content-Type: application/json;charset=utf-8
BODY[0:300] '\r\n{"bustime-response": {"error": [ {\r\n    "msg": "No API access key supplied"\r\n} ] }}\r\n\r\n\r\n\t'

UTC 2026-10-13T18:19:37Z GET https://www.ctabustracker.com/bustime/api/v2/getvehicles?rt=20&format=json
STATUS 200 | Content-Type: application/json;charset=utf-8
BODY[0:300] '\r\n{"bustime-response": {"error": [ {\r\n    "msg": "No API access key supplied"\r\n} ] }}\r\n\r\n\r\n\t'

UTC 2026-10-13T18:19:37Z GET http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?rt=red&outputType=JSON
STATUS 200 | Content-Type: application/json; charset=utf-8
BODY[0:300] {"ctatt":{"tmst":"2026-10-13T13:19:37","TimeStamp":"2026-10-13T13:19:37","errCd":"100","errNm":"Required parameter 'key' is missing."}}
```

Important: both APIs return **HTTP 200** for auth errors — errors must be detected in the body (`bustime-response.error[]` / `ctatt.errCd != "0"`).

##### 8. Terms / licence

URL: https://www.transitchicago.com/developers/terms/ ("Developer License Agreement and Terms of Use"; same text embedded on the Train Tracker key form). Key clauses (verbatim):

> Subject to your compliance with this Agreement, CTA grants you a limited, non-exclusive, non-assignable, non-transferable and revocable license to use, reproduce, and distribute CTA Data as provided by CTA through the application programming interfaces (“APIs”), data feeds or otherwise for the sole purpose of assisting mass transportation (i.e., bus or rail) riders or in furtherance of promoting public transportation.  Except as expressly provided in this Agreement, CTA Data may not be copied, reproduced, downloaded or distributed in any manner, in whole or in part, without the express permission of CTA.

> You may cache CTA Data you receive from CTA in order to improve your application’s user experience, but you agree to take reasonable efforts to keep the CTA Data up to date.

> When using the CTA Data, you have the option, but not the obligation, to credit CTA. If you elect to include a credit line, it should read as follows: “Data provided by Chicago Transit Authority,” "Data provided by CTA" or “Powered by CTA data” or similar, descriptive language.

Train Tracker PDF p.3:

> By using this API, you agree to our Developer License Agreement and Terms of Use ... It’s important that you, the developer, understand that this service is provided on an as-is basis and without any guarantees as to availability or accuracy.

### E.entsoe — `entsoe.md`

#### ENTSO-E Transparency Platform RESTful API — key facts (fetched 2026-10-13)

Sources fetched now (all official ENTSO-E):
- Help-centre section "Restful API integration guide": https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API (41 articles, pulled via the Zendesk Help Center JSON API; raw text in `raw/entsoe_zendesk.txt`)
- Official Postman documentation linked from the help centre: https://documenter.getpostman.com/view/7009892/2s93JtP3F6 (collection JSON saved in `raw/entsoe_postman.json`)
- Terms of Use PDF (29/03/2023) and "List of data available for free re-use" PDF (18/10/2023), linked from https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions
- XML examples repository linked from the sitemap: https://gitlab.entsoe.eu/transparency/xml-examples (NOT fetched)

##### 1. Sign-up / credential process
URL: https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token (updated 2026-01-28)

> Security token is required to use web API. ...
> ## 1- Register Transparency Platform
> 1.1- Go to: Production environment: https://transparency.entsoe.eu/ or Test environment: https://iop-transparency.entsoe.eu/ (does not contain as much data as the Production environment) and click on the "Sign In" button
> 1.2- Click register link · 1.3- Register · 1.4- Verify account via URL sent to the registered email address
> ## 2- Send an email
> Send an email to transparency@entsoe.eu with “RESTful API access” in the subject line and the registered e-mail address in the body.
> ## 3- Wait for confirmation e-mail
> You will be granted within 3 working days and will receive an email
> ## 4- Login Transparency Platform and create a security token
> 4.1- Click "My Account" · 4.2- Generate a (new) token
> ## 5- You can start using the RESTful API

##### 2. Endpoint, protocol, parameters
URL: https://transparencyplatform.zendesk.com/hc/en-us/articles/15696677194644-Request-Endpoint
> - Production environment endpoint:  https://web-api.tp.entsoe.eu/api
> - IOP environment endpoint: https://web-api.tp-iop.entsoe.eu/api
> - Only **https** protocol is supported.

Time interval — https://transparencyplatform.zendesk.com/hc/en-us/articles/12783280128404-Request-Parameters-Time-Interval
> - For all data items, time is expressed in UTC.
> 1. periodStart (**yyyyMMddHHmm**) and periodEnd (**yyyyMMddHHmm**) : ... These parameters are only available in **GET** method.
> 2. timeInterval (**yyyy-MM-ddTHH:mmZ/yyyy-MM-ddTHH:mmZ**) : This parameter is available in both **GET** and **POST** methods

Request parameters — https://transparencyplatform.zendesk.com/hc/en-us/articles/15696716612372-Request-Parameters
> Parameter names are case sensitive.
> In every request, time interval must be provided as request parameter.

Code lists — DocumentType (https://transparencyplatform.zendesk.com/hc/en-us/articles/15857043092756-DocumentType): `A44 Price Document`, `A65 System total load`, `A74 Wind and solar generation`, `A75 Actual generation per type`. ProcessType (https://transparencyplatform.zendesk.com/hc/en-us/articles/15857039772052-ProcessType): `A01 Day ahead`, `A16 Realised`. PsrType (https://transparencyplatform.zendesk.com/hc/en-us/articles/15856995130004-PsrType): B01 Biomass, B02 Fossil Brown coal/Lignite, B03 Fossil Coal-derived gas, B04 Fossil Gas, B05 Fossil Hard coal, B06 Fossil Oil, B07 Fossil Oil shale, B08 Fossil Peat, B09 Geothermal, B10 Hydro Pumped Storage, B11 Hydro Run-of-river and poundage, B12 Hydro Water Reservoir, B13 Marine, B14 Nuclear, B15 Other renewable, B16 Solar, B17 Waste, B18 Wind Offshore, B19 Wind Onshore, B20 Other, (B21–B25 grid/storage codes).

Per-request parameters, verbatim from the Postman collection (`[M]` mandatory, `[O]` optional):

**6.1.A Actual Total Load** — `{baseUrl}?documentType=A65&processType=A16&outBiddingZone_Domain=10YCZ-CEPS-----N&periodStart=202303030000&periodEnd=202303060000`
- documentType = A65 :: [M] A65 = System total load
- processType = A16 :: [M] A16 = Realised
- outBiddingZone_Domain :: [M] EIC code of a Control Area, Bidding Zone or Country
- periodStart / periodEnd :: [M] Pattern yyyyMMddHHmm e.g. 201601010000
- curveType = A03 :: [O] A01 = Sequential fixed block; A03 = Variable sized blocks (default)
- Description: "Request limit: Each request may cover a period of up to 1 year."

**16.1.B&C Actual Generation per Production Type** — `{baseUrl}?documentType=A75&processType=A16&in_Domain=10Y1001A1001A83F&periodStart=202308152200&periodEnd=202308162200`
- documentType = A75 :: [M] A75 = Actual generation per type (all production types); A74 = Wind and solar generation only
- processType = A16 :: [M] A16 = Realised
- in_Domain :: [M] Control Area, Bidding Zone, Country
- periodStart / periodEnd :: [M] Pattern yyyyMMddHHmm
- psrType :: [O] (codes above)
- curveType :: [O] A01 / A03 (default)
- Description: "Response from API is same irrespective of querying for Document Types A74 - Wind & Solar & A75 - Actual Generation Per Type. Time series with inBiddingZone_Domain attribute reflects Generation values while outBiddingZone_Domain reflects Consumption values."

**12.1.D Energy Prices (day-ahead)** — `{baseUrl}?documentType=A44&periodStart=202407272200&periodEnd=202407282200&out_Domain=10YAT-APG------L&in_Domain=10YAT-APG------L`
- documentType = A44 :: [M] Price Document
- periodStart / periodEnd :: [M] Pattern yyyyMMddHHmm
- out_Domain :: [M] EIC code of a Bidding Zone
- in_Domain :: [M] EIC code of a Bidding Zone (must be same as out_Domain)
- contract_MarketAgreement.type = A01 :: [O] A01 = Day-ahead ; A07 = Intraday
- classificationSequence_AttributeInstanceComponent.position = 1 :: [O] Integer
- offset = 0 :: [O] Zero‑based index of the first TimeSeries to return (batches of 100 TimeSeries)
- curveType :: [O] A01 / A03 (default)
- Note: no processType parameter in the official A44 example.

EIC codes — https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC (updated 2026-09-21):
| Area | EIC | Area types listed |
|---|---|---|
| Germany-Luxembourg | `10Y1001A1001A82H` | BZN\|DE-LU, IPA\|DE-LU, MBA\|DE-LU, SCA\|DE-LU |
| Germany (DE) | `10Y1001A1001A83F` | IPA\|DE, Germany (DE) (used as in_Domain in the official A75 example) |
| France | `10YFR-RTE------C` | LFA, LFB, SCA, BZN, CTA, MBA \|FR; France (FR) |
| Spain | `10YES-REE------0` | LFA, SCA, BZN, CTA, LFB, MBA \|ES; Spain (ES) |

Resolution: in the official example responses, Actual Total Load for CZ (Mar 2023) has `<resolution>PT60M</resolution>`; Actual Generation per type for DE (Aug 2023) and day-ahead prices for AT (Jul 2024) have `<resolution>PT15M</resolution>`. **NOT VERIFIED**: the current resolution for DE-LU / FR / ES per data item — the help page "Data Items Subjected to Changes to Publication Resolution" (https://transparencyplatform.zendesk.com/hc/en-us/articles/15594449302804) says only "This help page is replaced by an automatic report (Download)." and the report was not fetched. Resolution must be read from each `Period/resolution` element. Publication timing: "Data is published based on the platform's internal configuration. In most cases, it is released as soon as it is received and processed." (https://transparencyplatform.zendesk.com/hc/en-us/articles/32810427201809).

##### 3. How credentials are sent
- Query parameter — https://transparencyplatform.zendesk.com/hc/en-us/articles/15854521447188-Get-Method: "Token has to be present among other params. Parameter key is securityToken. `GET /api?securityToken=TOKEN (other parameters omitted)`"
- Header alternative — official Postman request "6.1.A Actual Total Load - SECURITY_TOKEN in header": header `SECURITY_TOKEN: {{apiKey}}`; "Note: This is an example where the security token is included in the request header rather than in the query parameters."
- https://transparencyplatform.zendesk.com/hc/en-us/articles/15854491895828: "If the token is missing or invalid (including suspended account), the system will respond with Http 401 Unauthorized."

##### 4. Rate limits / quotas
https://transparencyplatform.zendesk.com/hc/en-us/articles/12783148966036-API-Rate-Limit-Part-1 (updated 2026-04-20):
> - **Primary Limit:** **400 requests per minute** per user account (API token).
> - **Enforcement Scope:** Limits are applied **per user account (API token)**, **not per IP address**.
> - **Exceeding Rate Limits:** If a user’s token exceeds **400 requests in a minute**, the system may temporarily ban the token.
> - **Automatic Unbanning:** Bans are temporary. The ticket mentions users are **automatically unbanned after approximately 10 minutes**.

(The older "Query Response" article still lists `429 | - | Too many requests - max allowed 400 per minutes from eash unique IP` — contradicts the per-token wording above.)
https://transparencyplatform.zendesk.com/hc/en-us/articles/12783223209876-API-Rate-Limit-Part-2: "Timeout for every https (http protocol is not allowed) request is 5 minutes (300 seconds)."
https://transparencyplatform.zendesk.com/hc/en-us/articles/15854536354964-API-Query-Size-Limit: Actual Total Load 6.1.A "One-year date range"; Day Ahead Prices 12.1.D "One-year date range"; Aggregated Generation per Type 16.1.B & 16.1.C "One-year date range".
Postman (A44): "A maximum of 100 TimeSeries elements is returned per XML response. The offset parameter can be used to retrieve the data in batches of up to 100 TimeSeries".
Error codes (https://transparencyplatform.zendesk.com/hc/en-us/articles/15727773247124-Query-Response): `200/999 No matching data found`, `400/999 Invalid query attributes or parameters`, `401 Unauthorized. Missing or invalid security token`.

##### 5. Response format
- Encoding: XML (IEC 62325-451 documents). Schema/format: "The response format is defined by the download scenarios described in the implementation guides, which are an integral part of the transparency platform’s manual of procedures." Implementation guides zip: https://www.entsoe.eu/fileadmin/user_upload/_library/resources/Transparency/MoP%20Reference%20documents%20for%20V2R0-2015-09-01.zip ; MoP: https://www.entsoe.eu/data/transparency-platform/mop/ (not fetched).
- Root element: load/generation → `GL_MarketDocument` (ns `urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0`); prices → `Publication_MarketDocument` (ns `urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3`); errors/no data → `Acknowledgement_MarketDocument` with `Reason/code`, `Reason/text`.
- Record path: `/*/TimeSeries/Period/Point`; time of a point = `Period/timeInterval/start + (position-1) × Period/resolution` (ISO 8601 duration, e.g. PT15M, PT60M).
- Value field: `Point/quantity` (load, generation; unit in `TimeSeries/quantity_Measure_Unit.name`, `MAW` = MW) or `Point/price.amount` (prices; `currency_Unit.name` EUR, `price_Measure_Unit.name` MWH).
- Per-TimeSeries metadata: `mRID`, `businessType`, `objectAggregation`, `inBiddingZone_Domain.mRID` / `outBiddingZone_Domain.mRID` (load/gen) or `in_Domain.mRID`/`out_Domain.mRID` (prices), `curveType`, `MktPSRType/psrType` (generation), `auction.type`, `contract_MarketAgreement.type`, `classificationSequence_AttributeInstanceComponent.position` (prices).
- curveType: "Curve type in response is A03 for all data items" (Query Response article). With A03 (variable-sized blocks) positions may be omitted when the value does not change — the official A44 example has 95 `<Point>` elements for a 96-position PT15M day (last position 96).
- Time zone: "In response, time is always expressed in UTC." Day-ahead price responses cover the whole market day in the local zone (e.g. 2024-07-27T22:00Z–2024-07-28T22:00Z).

##### 6. Official example responses (verbatim, truncated after the first points; full bodies in `raw/entsoe_example_*_0.xml`)
Source: Postman collection https://documenter.getpostman.com/view/7009892/2s93JtP3F6 — saved response "CZ (03/03/2023-05/03/2023 UTC)" for 6.1.A:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
    <mRID>deca862df0c9487d990a7878242c1361</mRID>
    <revisionNumber>1</revisionNumber>
    <type>A65</type>
    <process.processType>A16</process.processType>
    <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
    <sender_MarketParticipant.marketRole.type>A32</sender_MarketParticipant.marketRole.type>
    <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
    <receiver_MarketParticipant.marketRole.type>A33</receiver_MarketParticipant.marketRole.type>
    <createdDateTime>2023-08-18T12:18:45Z</createdDateTime>
    <time_Period.timeInterval>
        <start>2023-03-03T00:00Z</start>
        <end>2023-03-06T00:00Z</end>
    </time_Period.timeInterval>
    <TimeSeries>
        <mRID>1</mRID>
        <businessType>A04</businessType>
        <objectAggregation>A01</objectAggregation>
        <outBiddingZone_Domain.mRID codingScheme="A01">10YCZ-CEPS-----N</outBiddingZone_Domain.mRID>
        <quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
        <curveType>A01</curveType>
        <Period>
            <timeInterval>
                <start>2023-03-03T00:00Z</start>
                <end>2023-03-06T00:00Z</end>
            </timeInterval>
            <resolution>PT60M</resolution>
            <Point>
                <position>1</position>
                <quantity>7146</quantity>
            </Point>
            <Point>
                <position>2</position>
                <quantity>7037</quantity>
            </Point>
            ...
```
Saved response "AT (28/07/2024)" for 12.1.D Energy Prices:
```xml
<?xml version="1.0" encoding="utf-8"?>
<Publication_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3">
    <mRID>05e8314f237d4998b65a04c538fc8ec9</mRID>
    <revisionNumber>1</revisionNumber>
    <type>A44</type>
    <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
    <sender_MarketParticipant.marketRole.type>A32</sender_MarketParticipant.marketRole.type>
    <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
    <receiver_MarketParticipant.marketRole.type>A33</receiver_MarketParticipant.marketRole.type>
    <createdDateTime>2024-10-01T15:07:18Z</createdDateTime>
    <period.timeInterval>
        <start>2024-07-27T22:00Z</start>
        <end>2024-07-28T22:00Z</end>
    </period.timeInterval>
    <TimeSeries>
        <mRID>1</mRID>
        <auction.type>A01</auction.type>
        <businessType>A62</businessType>
        <in_Domain.mRID codingScheme="A01">10YAT-APG------L</in_Domain.mRID>
        <out_Domain.mRID codingScheme="A01">10YAT-APG------L</out_Domain.mRID>
        <contract_MarketAgreement.type>A01</contract_MarketAgreement.type>
        <currency_Unit.name>EUR</currency_Unit.name>
        <price_Measure_Unit.name>MWH</price_Measure_Unit.name>
        <classificationSequence_AttributeInstanceComponent.position>2</classificationSequence_AttributeInstanceComponent.position>
        <curveType>A03</curveType>
        <Period>
            <timeInterval>
                <start>2024-07-27T22:00Z</start>
                <end>2024-07-28T22:00Z</end>
            </timeInterval>
            <resolution>PT15M</resolution>
            <Point>
                <position>1</position>
                <price.amount>104.98</price.amount>
            </Point>
            <Point>
                <position>2</position>
                <price.amount>94.98</price.amount>
            </Point>
            <Point>
            ...
```
Saved response "DE (16/08/2023)" for 16.1.B&C (19 TimeSeries in full body):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
    <mRID>dcc3c98be3b54e9aa388ed11e3e22b3e</mRID>
    <revisionNumber>1</revisionNumber>
    <type>A75</type>
    <process.processType>A16</process.processType>
    <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
    <sender_MarketParticipant.marketRole.type>A32</sender_MarketParticipant.marketRole.type>
    <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
    <receiver_MarketParticipant.marketRole.type>A33</receiver_MarketParticipant.marketRole.type>
    <createdDateTime>2023-08-20T04:54:56Z</createdDateTime>
    <time_Period.timeInterval>
        <start>2023-08-15T22:00Z</start>
        <end>2023-08-16T22:00Z</end>
    </time_Period.timeInterval>
    <TimeSeries>
        <mRID>1</mRID>
        <businessType>A01</businessType>
        <objectAggregation>A08</objectAggregation>
        <inBiddingZone_Domain.mRID codingScheme="A01">10Y1001A1001A83F</inBiddingZone_Domain.mRID>
        <quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
        <curveType>A01</curveType>
        <MktPSRType>
            <psrType>B01</psrType>
        </MktPSRType>
        <Period>
            <timeInterval>
                <start>2023-08-15T22:00Z</start>
                <end>2023-08-16T22:00Z</end>
            </timeInterval>
            <resolution>PT15M</resolution>
            <Point>
                <position>1</position>
                <quantity>4300</quantity>
            </Point>
            <Point>
                <position>2</position>
                <quantity>4301</quantity>
            </Point>
            <Point>
            ...
```

##### 7. Probe without credentials (2026-10-13T18:15Z, python3 urllib, 30 s timeout)
`GET https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&outBiddingZone_Domain=10YCZ-CEPS-----N&periodStart=202303030000&periodEnd=202303040000` → **HTTP 401**, `Content-Type: text/xml`, body:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Acknowledgement_MarketDocument
	xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0">
	<mRID>d0da69e0-c179-4</mRID>
	<createdDateTime>2026-10-13T18:15:39Z</createdDateTime>
	<sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
	<sender_MarketParticipant.marketRole.type>A32</sender_MarketParticipant.marketRole.type>
	<receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
	<receiver_MarketParticipant.marketRole.type>A39</receiver_MarketParticipant.marketRole.type>
	<received_MarketDocument.createdDateTime>2026-10-13T18:15:39Z</received_MarketDocument.createdDateTime>
	<Reason>
		<code>999</code>
		<text>Authentication failed.</text>
	</Reason>
</Acknowledgement_MarketDocument>
```

##### 8. Terms / licence
- https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions: "Use of the Transparency Platform implies your acceptance of these documents ... The access to and use of the ENTSO-E Transparency Platform is subject to compliance with the Terms of Use."
- Terms of Use (29/03/2023) PDF https://transparencyplatform.zendesk.com/hc/article_attachments/40921869376401, §2.5: "ENTSO-E currently publishes a subset of the Transparency Platform data available under an open source license (CC-BY 4.0) for the free use of Data Users (hereinafter ‘’Open Data’’)." §3.1: the Data User shall "mention the ENTSO-E Transparency Platform as the source of publication of the data" and "not cause prejudice to the copyright or related right on a Transparency Platform Data, which may be owned by the concerned Primary Owner of Data. In case of a risk to cause prejudice to said right, the Data User shall seek the prior agreement of the holder of the copyright or related right." ... "The Data User has responsibility to check this list before each re-use of the Transparency Platform Data."
- List of data available for free re-use (18/10/2023) PDF https://transparencyplatform.zendesk.com/hc/article_attachments/40921869379729: "Data Users may freely copy, redistribute, and adapt the listed data for any purpose, by giving appropriate credit (attribution) to its source and indicating if they have made any changes".
- **Finding (from text extraction of that PDF):** the article references in the list are 6.1.b–e, 10.1.a–b, 11.1.a–b, 12.1.a–c, 12.1.g, 12.3.a/e/f, 13.1.a–c, 17.1.b–j, 17.2.a–i. **6.1.a (Actual Total Load), 16.1.b/c (Actual Generation per Type) and 12.1.d (Day-ahead prices) do not appear** → they are not in the CC-BY 4.0 open-data list; re-use is governed by §3.1 (attribution + Primary Owner rights). Classroom/non-redistributive use: NOT VERIFIED as explicitly permitted beyond §3.1.

### E.fink — `fink.md`

#### Fink broker (LSST + ZTF) — key facts (fetched 2026-10-13)

Sources fetched now:
- fink-client README: https://github.com/astrolabsoftware/fink-client (raw README.md)
- LSST docs: https://doc.lsst.fink-broker.org/services/livestream/ , https://doc.lsst.fink-broker.org/services/fink_client/ (both "Version 03/06/2026", tested with fink-client 12.0), https://doc.lsst.fink-broker.org/services/api/tagsearch/ , https://doc.lsst.fink-broker.org/services/api/tips/ , https://doc.lsst.fink-broker.org/services/api/definitions/
- ZTF docs: https://doc.ztf.fink-broker.org/services/livestream/ , https://doc.ztf.fink-broker.org/services/fink_client/ ("Version 27/08/2026"), https://doc.ztf.fink-broker.org/services/search/getting_started/ , https://doc.ztf.fink-broker.org/services/search/classsearch/
- fink-client source, PyPI sdist 12.2.0 (uploaded 2026-09-16): https://files.pythonhosted.org/packages/d2/68/46f38fea5d1f44e110629b086d85d26553930149851a99c02dc53d06c41c/fink_client-12.2.0.tar.gz (`fink_client/consumer.py`, `scripts/finkctl.py`, `scripts/finkctl_stream.py`, `avro_utils.py`)
- (Note: the task's `fink-broker.readthedocs.io` / `doc.lsst.fink-portal.org` are superseded; the README links `doc.lsst.fink-broker.org` / `doc.ztf.fink-broker.org`.)

##### 1. Sign-up / credential process
README (https://github.com/astrolabsoftware/fink-client#registration):
> In order to connect and poll alerts from Fink, you need to get your credentials:
> 1. Subscribe to one or more Fink streams by filling this [form](https://forms.gle/2td4jysT4e9pkf889).
> 2. After filling the form, we will send your credentials. Register them on your machine following the [ZTF](https://doc.ztf.fink-broker.org/services/fink_client/) or [LSST](https://doc.lsst.fink-broker.org/services/fink_client/) documentation.

Form (https://forms.gle/2td4jysT4e9pkf889 → Google Form "Fink services subscription"), description: "Fill this form if you are interested in subscribing to one or more Fink services that require an account. The Fink services are open to any scientists, but it is password protected for obvious reasons. After filling this form, we will come back to you with more information about the credentials."

LSST fink_client doc: "For some services, such as the Data Transfer and the Livestream, you must register before polling data." / "How to register? Based on the information sent when you asked for credentials, authenticate using the auth command: `finkctl auth register ...`" (v11 → v12 mapping: `fink_client_register --> finkctl auth register`, `fink_consumer --> finkctl stream`, `fink_datatransfer --> finkctl transfer`).

`finkctl auth register` options (fink-client 12.2.0 `scripts/finkctl.py`, all `required=True`): `-servers` "Fink Kafka bootstrap server in the form name:port"; `-groupid` "group.id used for the authentication on the Kafka cluster"; `-username` "username used for the authentication on the Kafka cluster"; `-survey` choice `ztf`|`lsst` "Note that each survey will have its own configuration file." Config file: `~/.finkclient/lsst_credentials.yml` (LSST livestream troubleshooting).

##### 2. Kafka servers, protocol, topics
- **Kafka bootstrap servers for LSST and ZTF: NOT VERIFIED** — not published in any fetched doc or in the client. They are delivered privately with the credentials ("we will send your credentials"). The client's only default is `["localhost:9093", "localhost:9094", "localhost:9095"]` (placeholder in `consumer.py`).
- Topics: LSST examples `fink_extragalactic_lt20mag_candidate_lsst`, `fink_sn_near_galaxy_candidate_lsst`; ZTF examples `fink_early_sn_candidates_ztf`, `fink_sso_ztf_candidates_ztf`, `fink_sso_fink_candidates_ztf`. LSST doc: "For the list of available topics (aka tags), see the schema page https://lsst.fink-portal.org/schemas . From version 12, you can also access this list programmatically: `finkctl topic list -survey lsst`" (the client implements the LSST list via `requests.get("https://api.lsst.fink-portal.org/api/v1/tags")`). Tags returned now: extragalactic_lt20mag_candidate, extragalactic_new_candidate, extragalactic_svom, faint_trails, fast_transient_gvom, hostless_candidate, in_tns, most_likely_sn, remove_unlikely_transients, sn_near_galaxy_candidate, uniform_sample. Pattern observed in the docs: `fink_<tag>_lsst` (pattern inferred from the two documented examples, not stated as a rule).
- Purpose (LSST livestream doc): "These alerts are sent to the Fink Apache Kafka cluster, and substreams are produced (1 filter = 1 substream), identified by their topic name. Each alert pushed is available for 7 days in the queue, and consumers can replay streams indefinitely." — but the same page later says: "Processed alerts are stored 4 days on our servers" (internal inconsistency; same 4-day text on the ZTF page).
- Offsets: `finkctl stream -survey lsst --display -start_at earliest|latest`; default consumer config `{"auto.offset.reset": "earliest"}`.

##### 3. How credentials are sent (SASL / group id)
- `consumer.py::_get_kafka_config` (12.2.0), verbatim:
  ```python
  if "username" in config and "password" in config:
      kafka_config["security.protocol"] = "sasl_plaintext"
      kafka_config["sasl.mechanism"] = "SCRAM-SHA-512"
      kafka_config["sasl.username"] = config["username"]
      kafka_config["sasl.password"] = config["password"]

  kafka_config["group.id"] = config["group.id"]
  ```
- But `finkctl stream` (12.2.0 `finkctl_stream.py`) builds only `{"bootstrap.servers": conf["servers"], "group.id": conf["groupid"]}` and adds `password` only `if conf.get("password", None) is not None` — `username` is never passed, so SASL is **not** activated by the v12 CLI; `finkctl auth register` has no password option.
- LSST livestream troubleshooting, verbatim: "If you try to poll the servers and get: `... sasl_plaintext://xx.xx.xx.xx:yy/bootstrap: SASL SCRAM-SHA-512 mechanism handshake failed: Broker: Request not valid in current SASL state: broker's supported mechanisms:  (after 18ms in state AUTH_HANDSHAKE)` You are likely giving a password when instantiating the consumer. Check your conf: `finkctl auth show -survey lsst` it should not contain any entry called password:."
- Conclusion from these official sources: current Fink Livestream consumers connect PLAINTEXT with the assigned `group.id` (plus the private server address); SASL/SCRAM-SHA-512 is legacy code. **How the broker restricts access (ACL by group id / IP allow-list) is NOT VERIFIED** — not documented.

##### 4. Rate limits / quotas
- Kafka: retention "available for 7 days" vs "stored 4 days" (see §2). Timeout tip: "edit ~/.finkclient/lsst_credentials.yml `maxtimeout: 30`". No numeric consumer quota documented → NOT VERIFIED.
- REST: no numeric rate limit found → NOT VERIFIED. Tips page (https://doc.lsst.fink-broker.org/services/api/tips/): "When you hit a timeout (120 seconds), if you relaunch the query, it will progress faster as it will re-use data already fetched. Do not abuse". ZTF getting started: "Although the Science Portal and the REST API gives you access to hundreds millions of alerts, they are not designed to massively download data. Instead you would use the Data Transfer service."

##### 5. Message format
- Kafka value: **Apache Avro, schemaless binary** (`_decode_msg`: `avro_alert = io.BytesIO(msg.value())` → `fastavro` schemaless reader). Schema source: **the Kafka message key carries the Avro schema as JSON** (`process_message`: `_parsed_schema = fastavro.schema.parse_schema(json.loads(key))`); legacy fallback: key = version string → schema downloaded from `https://raw.github.com/astrolabsoftware/fink-client/master/schemas/distribution_schema_fink_ztf_{key}.avsc`. LSST doc: "The alert schema is automatically downloaded from the alert packet." / "schema is included in the alert payload". Saved alerts are `.avro` files readable with `fink_client.avro_utils.AlertReader(...).to_pandas()`.
- Kafka alert fields: **exact field list NOT VERIFIED** (no Kafka alert example in the docs; schema browser https://lsst.fink-portal.org/schemas is a JS app). The REST definitions page states column families: "r: original data from LSST · f: added values from Fink Science modules · v: added values from Fink generated at the query runtime · b: cutout data".
- REST API (JSON/CSV/parquet/votable via `output-format`). Public, **no API key** in any example and probes below succeeded without credentials.
  - LSST latest alerts by tag: `POST https://api.lsst.fink-portal.org/api/v1/tags` JSON `{"tag": "in_tns", "n": "5", "columns": "r:diaObjectId", "startdate": "...", "stopdate": "..."}` or `GET https://api.lsst.fink-portal.org/api/v1/tags?tag=in_tns&n=5&output-format=json` ("Get latests 5 alerts reported to TNS"). `GET /api/v1/tags` without args lists tags. Full light curves: `POST /api/v1/sources` `{"diaObjectId": ..., "columns": ...}`. Schema: `POST https://api.lsst.fink-portal.org/api/v1/schema` `{"endpoint": "/api/v1/sources"}`.
  - ZTF latest by class: `POST https://api.ztf.fink-portal.org/api/v1/latests` `{"class": "Early SN Ia candidate", "n": "5"}` (also `startdate`, `stopdate`, `columns`, `trend`); objects: `POST https://api.ztf.fink-portal.org/api/v1/objects` `{"objectId": "ZTF21aaxtctv", "output-format": "json"}`. (The task's `api.fink-portal.org` timed out now; docs use `api.ztf.fink-portal.org`.)
  - Response = JSON array; each element = one alert, keys = prefixed column names (e.g. `r:diaObjectId`, `r:midpointMjdTai`, `r:psfFlux`, `r:psfFluxErr`, `r:band`, `r:ra`, `r:dec`, `f:clf_*`, `f:xm_*`; ZTF: `i:objectId`, `i:jd`, `i:magpsf`, `d:mag_rate`).

##### 6. Official example message
- Kafka livestream: **no official example message** in the fetched docs (only CLI output such as offset tables).
- REST: the docs show request examples but **no verbatim JSON response body**. Only a live sample (NOT an official doc example), first 1200 chars of `GET https://api.lsst.fink-portal.org/api/v1/tags?tag=in_tns&n=1&output-format=json` on 2026-10-13:
```json
{"f:clf_cats_class": 22, "f:clf_cats_score": 0.51305544, "f:clf_earlySNIa_score": -1.0, "f:clf_elephant_kstest_science": null, "f:clf_elephant_kstest_template": null, "f:clf_snnSnVsOthers_score": 0.13581431, "f:fink_broker_version": "5.0rc0", "f:fink_science_version": "8.52.0", "f:lsst_schema_version": "lsst.v11_1", "f:xm_gaiadr3_DR3Name": "Fail", "f:xm_gaiadr3_Plx": null, "f:xm_gaiadr3_VarFlag": "0", "f:xm_gaiadr3_e_Plx": null, "f:xm_gcvs_type": null, "f:xm_legacydr8_e_zphot": null, "f:xm_legacydr8_fqual": null, "f:xm_legacydr8_pstar": null, "f:xm_legacydr8_zphot": null, "f:xm_mangrove_2MASS_name": null, "f:xm_mangrove_HyperLEDA_name": null, "f:xm_mangrove_ang_dist": null, "f:xm_mangrove_lum_dist": null, "f:xm_simbad_otype": "Fail", "f:xm_spicy_class": null, "f:xm_tns_fullname": "AT 2026ejp", "f:xm_tns_redshift": null, "f:xm_tns_type": null, "f:xm_vsx_Type": null, "f:xm_x3hsp_type": null, "f:xm_x4lac_type": null, "r:apFlux": 2164.2568, "r:apFluxErr": 629.55585, "r:apFlux_flag": false, "r:apFlux_flag_apertureTruncated": false, "r:band": "i", "r:bboxSize": 21, "r:centroid_flag": false, "r:dec": -48.1266920498, "r:decErr": 3.2597e-05, "r:detector": 162, "r:diaObjectId": 3140073458468 ...
```

##### 7. Probe without credentials (2026-10-13, python3 urllib, 30 s timeout)
- `GET https://api.lsst.fink-portal.org/api/v1/tags?tag=in_tns&n=1&output-format=json` → **200** application/json, 3609 bytes, starts `[{"f:clf_cats_class":22,"f:clf_cats_score":0.51305544,"f:clf_earlySNIa_score":-1.0,...,"f:fink_broker_version":"5.0rc0","f:fink_science_version":"8.52.0","f:lsst_schema_version":"lsst.v11_1"`
- `GET https://api.lsst.fink-portal.org/api/v1/tags` → **200**, 1716 bytes `{"extragalactic_lt20mag_candidate":{"API support":true,"description":"Select alerts that are rising, bright (mag < 20), and extragalactic candidates"},...`
- `POST https://api.ztf.fink-portal.org/api/v1/latests` `{"class":"Early SN Ia candidate","n":"1","columns":"i:objectId,i:jd,i:magpsf"}` → **200** `[{"i:jd":2461322.7193287001,"i:magpsf":18.880388,"i:objectId":"ZTF26abzidlp"}]`
- `POST https://api.fink-portal.org/api/v1/latests` → **timeout** (URLError timed out).
- Kafka brokers: **not probed** — addresses not public (NOT VERIFIED).

##### 8. Terms / licence
- fink-client software: Apache License 2.0 (`LICENSE` in the sdist: "Apache License Version 2.0, January 2004").
- **Data terms/licence for the Fink streams or REST API: NOT VERIFIED** — no terms/licence page found in the fetched LSST/ZTF docs; https://fink-broker.org/ is a JS-rendered page with no static links. Access statement from the subscription form: "The Fink services are open to any scientists, but it is password protected for obvious reasons."

### E.gfw — `gfw.md`

#### Global Fishing Watch API v3 — key facts (fetched 2026-10-13)

Sources fetched now (official GFW docs; every page has a Markdown twin at `<page>.md`, index at https://globalfishingwatch.org/our-apis/documentation/llms.txt):
- https://globalfishingwatch.org/our-apis/documentation/docs/authentication (.md)
- https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits (.md)
- https://globalfishingwatch.org/our-apis/documentation/docs/v3/events (.md), https://globalfishingwatch.org/our-apis/documentation/docs/v3/events/get-all-events (.md)
- https://globalfishingwatch.org/our-apis/documentation/docs/examples/events/get-example1 (.md)
- https://globalfishingwatch.org/our-apis/documentation/docs/v3/general-api-doc/pagination (.md)
- OpenAPI 3.2.0 document "apiv3" embedded in the events page HTML (operation `EventsV3Controller_getAll`, summary "List events", path `/api/v3/events`, server `https://gateway.api.globalfishingwatch.org`, security scheme `ApiKeyAuth: {type: http, scheme: bearer, bearerFormat: JWT}`)

##### 1. Sign-up / credential process
https://globalfishingwatch.org/our-apis/documentation/docs/authentication:
> 1. **Register** for a Global Fishing Watch account (https://globalfishingwatch.org/our-apis/tokens/signup).
> 2. **Create** an API access token from the token management page (https://globalfishingwatch.org/our-apis/tokens).
> 3. **Agree** to the terms of use and attribute Global Fishing Watch in anything you publish.
>
> Tokens are issued instantly and do not expire, so you normally create one once and reuse it.

Terms §2.A/B (license-rate-limits page): "In order to use many of the Services, You must register for an account. GFW reserves the right to reject any account registration request, in its sole discretion." / "By requesting to open an account ... You represent and warrant to us ... that: (1) You are applying on behalf of an organization or entity that supports the sustainable use of ocean resources; (2) You are authorized to act on behalf of such organization or entity; (3) the application is sent from a valid email from the organization or entity; and (4) no other application or registration for this organization or entity exists."

##### 2. Endpoint and parameters
- Events (list): `GET https://gateway.api.globalfishingwatch.org/v3/events` (also POST with a JSON body for polygons/regions — see POST examples). Example (verbatim, get-example1): `curl --location --request GET 'https://gateway.api.globalfishingwatch.org/v3/events?vessels[0]=9b3e9019d-d67f-005a-9593-b66b997559e5&datasets[0]=public-global-fishing-events:latest&start-date=2017-01-01&end-date=2017-01-31&limit=1&offset=0' -H "Authorization: Bearer [TOKEN]"`
- Dataset per event type (events page, "REMINDER!"): fishing `public-global-fishing-events:latest`; encounters `public-global-encounters-events:latest`; loitering `public-global-loitering-events:latest`; port visits `public-global-port-visits-events:latest`; AIS off `public-global-gaps-events:latest`.
- Parameters of GET /v3/events from the OpenAPI spec (required flags verbatim from spec):
  - `datasets` — **required**, array of string — "Specify the datasets that will be used to search the vessel." (sent as `datasets[0]=...`)
  - `limit` — **required**, number, minimum 1 — "Amount of search results to return."
  - `offset` — **required**, number, minimum 0 — "Offset into the search results, used for pagination. It starts at 0. It is used in combination with the param “limit”."
  - `start-date` — optional — "Start date in format YYYY-MM-DD of the start date of the event (inclusive)"
  - `end-date` — optional — "End date in format YYYY-MM-DD of the end date of the event (exclusive)"
  - other optional filters: `vessels` ("List of vessel ids separated by comma"), `vesselGroups`, `vesselTypes`, `flags` ("Flags in format ISO3."), `types` (ENCOUNTER, FISHING, LOITERING, GAP_START, GAP, PORT_VISIT), `confidences` (port visits 2–4), `encounter-types`, `gap-intentional-disabling`, `includes`, `portIds`, `timeFilterMode`, `regionDatasets`, `regionIds`, `buffer-value`/`buffer-unit`/`buffer-operation`, `minDuration`/`maxDuration` (hours), `nextPortIds`, `is-closed`, `ids`, `include-regions` (default True), plus `*Operator` (INCLUDE/EXCLUDE) companions.
- Pagination (pagination page): collections return `total`, `limit`, `offset`, `nextOffset` ("Offset to pass on the next request to paginate correctly"), `metadata`, `entries`.

##### 3. How credentials are sent
"All Global Fishing Watch API requests must be authenticated with a personal **API access token**, sent as a Bearer token in the `Authorization` header." — `-H "Authorization: Bearer [TOKEN]"`.
Errors: "401 | Unauthorized — the request is not authenticated. | Missing, malformed, or invalid token; missing Bearer prefix." / "403 | Forbidden — authenticated, but not allowed to access this resource. | Your token lacks permission for the requested dataset."
"Five tokens per user. Each account can hold a maximum of five active tokens." "Limits are shared across your tokens."

##### 4. Rate limits / quotas
https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits#rate-limits:
> | Daily requests | 50,000 requests per day |
> | Monthly requests | 1,500,000 requests per month |
> Rate limits are defined and enforced at the user level across all tokens created by that user.
> When a user exceeds a rate limit, the API returns a 429 Too Many Requests HTTP status code.
> If the daily limit is reached, further requests from that user are blocked across all of the user's tokens for 24 hours from the time the limit was exceeded.
> If the monthly limit is reached, further requests from that user are blocked across all of the user's tokens for 30 consecutive days from the time the limit was exceeded.

Headers: `x-ratelimit-daily-limit-requests`, `x-ratelimit-monthly-limit-requests`, `x-ratelimit-daily-remaining-requests`, `x-ratelimit-monthly-remaining-requests`, `x-ratelimit-daily-current-usage`, `x-ratelimit-monthly-current-usage`, `x-ratelimit-daily-reset-hours`, `x-ratelimit-monthly-reset-days` ("Usage checks run every 30 minutes."). Terms §1.C repeats: "We ask that users not exceed 50,000 DAILY API requests per day and 1,500,000 per month."
Data freshness/latency of events: NOT VERIFIED (only the attribution template says "updated daily").

##### 5. Response format
JSON. Paginated object → records at `entries[]`. Record fields (from the official example): `start`, `end` (ISO 8601 UTC), `id`, `type` (e.g. `fishing`), `position.lat`/`position.lon`, `regions` {`mpa`, `eez`, `rfmo`, `fao`, `majorFao`, `eez12Nm`, `highSeas`, `mpaNoTakePartial`, `mpaNoTake`}, `boundingBox` [4 numbers], `distances` {`startDistanceFromShoreKm`, `endDistanceFromShoreKm`, `startDistanceFromPortKm`, `endDistanceFromPortKm`}, `vessel` {`id`, `name`, `ssvid` (MMSI)}, and a type-specific object (for fishing: `fishing` {`totalDistanceKm`, `averageSpeedKnots`, `averageDurationHours`, `potentialRisk`}). Top-level `metadata.datasets` shows the resolved dataset version (`public-global-fishing-events:v3.0` in the example; the live probe header showed `x-datasets: public-global-fishing-events:v4.0`).

##### 6. Official example response (verbatim)
Source: https://globalfishingwatch.org/our-apis/documentation/docs/examples/events/get-example1
```json
{
  "metadata": {
    "datasets": ["public-global-fishing-events:v3.0"],
    "vessels": ["9b3e9019d-d67f-005a-9593-b66b997559e5"],
    "dateRange": {
      "from": "2017-01-01",
      "to": "2017-01-31"
    }
  },
  "limit": 1,
  "offset": 0,
  "nextOffset": 1,
  "total": 10,
  "entries": [
    {
      "start": "2017-01-18T23:56:16.000Z",
      "end": "2017-01-19T03:42:27.000Z",
      "id": "718a4d93c16f78d9a54e9bc56d20c7e0",
      "type": "fishing",
      "position": {
        "lat": -46.1538,
        "lon": -63.2245
      },
      "regions": {
        "mpa": [],
        "eez": ["8466"],
        "rfmo": ["ACAP", "CCSBT", "IWC", "ICCAT"],
        "fao": ["41.3", "41.3.1", "41"],
        "majorFao": ["41"],
        "eez12Nm": [],
        "highSeas": [],
        "mpaNoTakePartial": [],
        "mpaNoTake": []
      },
      "boundingBox": [-63.21452500000001, -46.1618533333, -63.23098, -46.1495283333],
      "distances": {
        "startDistanceFromShoreKm": 221,
        "endDistanceFromShoreKm": 220,
        "startDistanceFromPortKm": 242.616953,
        "endDistanceFromPortKm": 240.71707800000001
      },
      "vessel": {
        "id": "9b3e9019d-d67f-005a-9593-b66b997559e5",
        "name": "CLAUDINA",
        "ssvid": "701000948"
      },
      "fishing": {
        "totalDistanceKm": 2.136563188884008,
        "averageSpeedKnots": 0.49600001273999994,
        "averageDurationHours": 0.15707175925925926,
        "potentialRisk": false
      }
    }
  ]
}
```

##### 7. Probe without credentials (2026-10-13, python3 urllib, 30 s timeout)
`GET https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest&start-date=2024-01-01&end-date=2024-01-02&limit=1&offset=0` → **HTTP 401**, `application/json; charset=utf-8`, headers `x-datasets: public-global-fishing-events:v4.0`, body `{"error":"invalid token"}`.

##### 8. Terms / licence
https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits#terms-of-use — §1.C verbatim: "Noncommercial Use Only. The Services are available for noncommercial use only in accordance with the CC BY-NC 4.0 license, including complying with the attribution requirements set forth in Section 3 below. You are welcome to use the Services provided that Your application and its use are not intended (primarily or materially) for or directed towards commercial advantage or monetary compensation."
§2.G: "The GFW API Token is specific to You and is Your responsibility. Your token is not to be shared or published with any additional users. ... You may not permit or authorize any other person or entity to use the API token issued to you."
§3.A attribution: "“Powered by Global Fishing Watch.” and link this text to https://globalfishingwatch.org" OR "“Global Fishing Watch. [2022 or current year ...], updated daily. [API dataset name and version], [DATE RANGE]. Data set accessed YYYY-MM-DD at https://globalfishingwatch.org/our-apis/.”"
§4.B: "each dataset carries its own license and restrictions. You should review the dataset’s metadata to understand these restrictions."
Implication for classroom use: each student needs their own account/token (no shared token, §2.G), and §2.B requires applying on behalf of an organization supporting sustainable ocean use — whether individual students qualify is NOT VERIFIED.

### E.lasair — `lasair.md`

#### Lasair for Rubin LSST — key facts (fetched 2026-10-13)

Sources fetched now:
- Site: https://lasair.lsst.ac.uk/ (links its documentation at https://lasair-lsst.readthedocs.io/en/main — the LSST-specific docs; https://lasair.readthedocs.io/en/main/ is the older ZTF-era docs whose index links https://lasair-ztf.lsst.ac.uk)
- Alert streams: https://lasair-lsst.readthedocs.io/en/main/core_functions/alert-streams.html (source `_sources/core_functions/alert-streams.md.txt`)
- REST API: https://lasair-lsst.readthedocs.io/en/main/core_functions/rest-api.html
- Python client docs: https://lasair-lsst.readthedocs.io/en/main/core_functions/client.html
- Official example notebook: https://github.com/lsst-uk/lasair-examples/blob/main/notebooks/consume_kafka.ipynb
- `lasair` PyPI package 0.1.4 (uploaded 2026-04-14), file `lasair/lasair.py` (sdist https://files.pythonhosted.org/packages/18/72/ff609c98670da045b45789cda381078fbe3e15d9afdd1ee4c4c8363d8459/lasair-0.1.4.tar.gz). Its declared homepage https://github.com/lasair-uk/lasair_api returned 404 via the GitHub API.

##### 1. Sign-up / credential process
https://lasair-lsst.readthedocs.io/en/main/more_info/account.html:
> We encourage users to register for a Lasair account. All you need is a valid email address.
> You will then be able to store queries and convert them to filters, build watchlists and watchmaps, and use the Lasair API and client.
> [Click here to sign up for an account]({%lasairurl%}/register)

FAQ (https://lasair-lsst.readthedocs.io/en/main/more_info/faqs.html): "Registration is easy, and just requires a valid email (register here). You can then build and save queries, watchlists, and watchmaps (sky areas), convert those to real-time slert treams, and use the Lasair API."

Kafka stream creation (alert-streams page): "You will need to be logged in to your Lasair account. Make a filter, then click “Save". You will then be prompted for "Filter Settings" ... If you select "On new alert", then your filter is run in near-real-time against arriving alerts." The *notification* menu selects the stream content (plain / lite lightcurve / full alert / daily email).

REST token (rest-api page): "Once you are logged in on the website, click on your name at the top right, and choose "My Profile". The API key is shown there."

##### 2. Broker / endpoint, protocol, parameters
Kafka (alert-streams page). **The page itself gives inconsistent host names:**
- prose: "You will be connecting to `lasair-lsst-kafka.lsst_pub.ac.uk` on port 9092."
- sample code: `kafka_server = 'lasair-lsst-kafka_pub.lsst.ac.uk:9092'`
- official notebook `consume_kafka.ipynb`: `kafka_server = 'lasair-lsst-kafka.lsst.ac.uk:9092'   # prod`
DNS check now (§7): `lasair-lsst-kafka.lsst.ac.uk` and `lasair-lsst-kafka_pub.lsst.ac.uk` both resolve to 192.41.122.71 with TCP 9092 open; `lasair-lsst-kafka.lsst_pub.ac.uk` does not resolve (typo in docs). Recommended: `lasair-lsst-kafka.lsst.ac.uk:9092` (the notebook's "prod" value; also avoids an underscore in a hostname).

Topic naming (verbatim): "The topic name is a combination of the string "lasair_", the ID number of your user account, and a sanitised version of the name you gave the filter. Therefore if you edit the filter and change its name, the topic name will also change." Example topic: `lasair_2Hasabsmag` (notebook: `lasair_1Lightweight`). "You can find the topic that corresponds to your filter in the detail page".

group_id (verbatim): "The `group_id` tells Kafka where to start delivery to you. It is just a string that you can make up, for example "Susan3456". The Kafka server remembers which `group_id`s it has seen before, and which was the last alert it delivered. ... If you use a new `group_id`, you get the alerts from the start of the Kafka cache, which is about 7 days."

REST API base: `https://api.lasair.lsst.ac.uk/api/` — methods `/api/cone/`, `/api/query/`, `/api/object/`, `/api/sherlock/object/`, `/api/sherlock/position/`. "you can uses either HTTP GET or POST. Arguments can be passed in the query string, as JSON or form encoded. Responses are JSON."
Example (verbatim): `https://api.lasair.lsst.ac.uk/api/query/?selected=objectId%2Cgmag&tables=objects&conditions=gmag%3C12.0&token=xxxxxxxxxxxxxxxxxxxxxxxx&format=json` (`query` args: `selected`, `tables`, `conditions`, `limit` default 1000, `offset` default 0).

##### 3. How credentials are sent
- Kafka: **no authentication.** The official client `lasair_consumer` (lasair 0.1.4, `lasair/lasair.py`) builds only:
  ```python
  settings = {
    'bootstrap.servers': host,
    'group.id': group_id,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
  }
  ```
  Docstring: "Connects to Lasair public kafka to get the chosen topic." No SASL/SSL settings anywhere in the docs or client. (Plaintext; no TLS settings documented.)
- REST: "Request authentication is via the API key. For GET queries, the key can go in the parameter string, and for POST queries, the key goes in the headers." GET → `&token=...`; POST → `curl --header "Authorization: Token xxxxxxxxxxxxxxxxxxxxxxxx" --data "..." https://api.lasair.lsst.ac.uk/api/cone/`. The client uses `headers = { 'Authorization': 'Token %s' % token }` against `https://api.lasair.lsst.ac.uk/api`.

##### 4. Rate limits / quotas
REST (https://lasair-lsst.readthedocs.io/en/main/core_functions/rest-api.html):
> *   User token (see 'Get Your Token') below: 100 API calls per hour, maximum 10,000 rows from query.
> *   Power user token (on request): 10,000 API calls per hour, maximum 1,000,000 rows from query.

Kafka (alert-streams page): "**WARNING The full alert records can be quite large, perhaps a fraction of a megabyte, and if your filter passes a large number of these they will be dropped.** ... Kafka records are deleted after 7 days, so you will need to be running a consumer either frequently or constantly to get everything." Also: "Whenever a kafka filter is changed, the old records are deleted, and Lasair runs the new filter to try and put 10 records in the stream". Empty topic → error `UNKNOWN_TOPIC_OR_PART` "this is not a problem, the error will go away when the fist message is returned by the filter".

##### 5. Message format
- Encoding: JSON (client docstring: "jmsg = json.loads(msg.value())  # msg will be in json format"). No schema registry; fields = the filter's SQL SELECT list + `UTC` (record production timestamp) + optional `alert` object. Schema browser for SELECT-able attributes: https://lasair.lsst.ac.uk/schema (linked from rest-api page; not fetched).
- One Kafka message = one record (one object that passed the filter).
- Plain stream: "offers just the attributes you selected in your filter query ... with a timestamp added for when the record was produced".
- Lite lightcurve: adds `alert.diaSourcesList[]` with `psfFlux`, `psfFluxErr`, `midpointMjdTai`, `band`, `reliability`, and `alert.diaForcedSourcesList[]`.
- Full alert: adds `alert.diaObject` (~82 attributes), `alert.diaSourcesList[]` (~98 attributes each, e.g. `diaSourceId`, `visit`, `detector`, `diaObjectId`), `alert.diaForcedSourcesList[]` — "the full alert data as received from Rubin, except for the cutout images".

##### 6. Official example messages (verbatim, https://lasair-lsst.readthedocs.io/en/main/core_functions/alert-streams.html)
Plain stream (note: the docs' example has a trailing comma, i.e. it is illustrative, not strict JSON):
```
{
  "diaObjectId": 169760235333878021,
  "decl": -38.16173726666955,
  "ra": 221.87087177320953,
  "UTC": "2026-01-29 11:40:14",
}
```
Lite lightcurve:
```
{
  "diaObjectId": 169760235333878021,
  "decl": -38.16173726666955,
  "ra": 221.87087177320953,
  "UTC": "2026-01-29 11:40:14",
  "alert": {
    "diaSourcesList": [
      {
        "psfFlux": 13677.0458984375,
        "psfFluxErr": 1538.7562255859375,
        "midpointMjdTai": 61029.354114730224,
        "band": "z",
        "reliability": 0.4863438308238983
      },
      ....  (perhaps 100 of these with 5 attributes each)
    ],
    "diaForcedSourcesList": [....]
  }
}
```
REST `/api/query/` example return (verbatim): 
```
status= 200
[
  {
    "objectId": "12345678901234",
    "gmag": 11.4319
  },
  {
    "objectId": "12345678901234",
    "gmag": 11.8582
  },
.... ]
```

##### 7. Probe without credentials (2026-10-13, python3 socket/urllib, 30 s timeout)
- `lasair-lsst-kafka.lsst.ac.uk` → 192.41.122.71, **TCP 9092 OPEN** (0.15 s)
- `lasair-lsst-kafka_pub.lsst.ac.uk` → 192.41.122.71, **TCP 9092 OPEN** (0.15 s)
- `lasair-lsst-kafka.lsst_pub.ac.uk` → **DNS FAIL** (Name or service not known)
- `GET https://api.lasair.lsst.ac.uk/api/cone/?ra=194.494&dec=48.851&radius=240.0&requestType=all&format=json` → **HTTP 401**, `application/json`, `{"detail":"Authentication credentials were not provided."}`
- `GET https://lasair.lsst.ac.uk/` → 200 text/html.
- Kafka protocol-level probe (metadata/topic list): NOT DONE — `confluent_kafka` is not installed locally; only TCP reachability verified.

##### 8. Terms / licence
- **NOT VERIFIED**: no terms-of-use or data licence page was found on lasair.lsst.ac.uk (only `/privacy` is linked) or in the LSST docs.
- Privacy statement https://lasair.lsst.ac.uk/privacy: "The Lasair project may record and process your personal details if you supply them. ... We will not sell, rent, trade or otherwise knowingly share or provide your personal information to any third party, except insofar as legally obliged to do so or as specified below."
- Citation request (https://lasair-lsst.readthedocs.io/en/main/more_info/acknowledgements.html and index): "If you make use of Lasair in any of your work, please remember to cite our paper: R.D.Williams et. al., Enabling science from the Rubin alert stream with Lasair, RAS Techniques and Instruments, 3,1, 362 (2024)." https://doi.org/10.1093/rasti/rzae024
- Token clause: "**Note: PLEASE NOT SHARE THESE TOKENS.** If you share code that uses the Lasair API, please put the token in a separate, imported file or environment variable, that you do not share, and is not put in github."

### E.mastodon — `mastodon.md`

#### Mastodon streaming API — key/credential documentation (fetched 2026-10-13 ~18:15 UTC)

Sources fetched now (raw copies in `raw/`). The rendered pages at docs.joinmastodon.org are built from the official repo `github.com/mastodon/documentation` (`content/en/...`); both were downloaded and the Markdown source is quoted below (rendered `methods/streaming/` HTML confirmed to contain the same text, e.g. "changed to require a User token").
- S1 https://docs.joinmastodon.org/methods/streaming/ (`content/en/methods/streaming.md`)
- S2 https://docs.joinmastodon.org/methods/instance/ (`content/en/methods/instance.md`) and https://docs.joinmastodon.org/entities/Instance/ (`content/en/entities/Instance.md`)
- S3 https://docs.joinmastodon.org/client/token/ (`content/en/client/token.md`)
- S4 https://docs.joinmastodon.org/client/authorized/ (`content/en/client/authorized.md`)
- S5 https://docs.joinmastodon.org/api/oauth-scopes/ (`content/en/api/oauth-scopes.md`)
- S6 https://docs.joinmastodon.org/entities/Status/ (`content/en/entities/Status.md`)
- S7 https://docs.joinmastodon.org/api/rate-limits/ (`content/en/api/rate-limits.md`)
- M1 mastodon.social live instance data via official public endpoints: `GET https://mastodon.social/api/v2/instance`, `/api/v1/instance/rules`, `/api/v1/instance/extended_description`, `/api/v1/instance/terms_of_service`, `/api/v1/instance/privacy_policy` (these are the data sources behind https://mastodon.social/about, /terms-of-service, /privacy-policy, which are JS-rendered pages).

##### 1. Sign-up / credential process

###### What the official docs document (API-based)
S3 "Creating our application":
> The first thing we will need to do is to register an application, in order to be able to generate access tokens later. The application can be created like so:
```bash
curl -X POST \
	-F 'client_name=Test Application' \
	-F 'redirect_uris=urn:ietf:wg:oauth:2.0:oob' \
	-F 'scopes=read write push' \
	-F 'website=https://myapp.example' \
	https://mastodon.example/api/v1/apps
```
S3 then shows `grant_type=client_credentials`, and states: "We are requesting a `grant_type` of `client_credentials`, which defaults to giving us the `read` scope." — **this yields an App token, which is NOT sufficient for streaming since 4.2.0** (see §3).

S4 "Example authorization code flow" (user token):
> To authorize a user, request [GET /oauth/authorize] in a browser with the following query parameters:
```bash
https://mastodon.example/oauth/authorize
?client_id=CLIENT_ID
&scope=read+write+push
&redirect_uri=urn:ietf:wg:oauth:2.0:oob
&response_type=code
```
```bash
curl -X POST \
	-F 'grant_type=authorization_code' \
	-F 'client_id=your_client_id_here' \
	-F 'client_secret=your_client_secret_here' \
	-F 'redirect_uri=urn:ietf:wg:oauth:2.0:oob' \
	-F 'code=user_authzcode_here' \
	https://mastodon.example/oauth/token
```
> The response of this method is a [Token] entity. We will need the `access_token` value.

###### Settings UI path ("Preferences > Development > New application")
NOT VERIFIED. A full-text search of all 193 Markdown pages of `mastodon/documentation` (`content/en/**`) found no description of the web-UI "Development" / "New application" / "Your access token" flow or `/settings/applications`. The page requires login on mastodon.social, so it could not be fetched anonymously. The token obtained that way would be a user token tied to the logged-in account (inference, not documented).

##### 2. Endpoints, protocol, parameters

Hostname discovery (S1 verbatim):
> Depending on server configuration details, the streaming API may be served from a different hostname than the other portions of the REST API. All path values documented here are relative to that hostname value. Clients should first obtain the hostname value by either:
> - Extracting the `configuration.urls.streaming` value from the [instance endpoint](../instance).
> - Making a REST API request to the `api/v1/streaming` endpoint on the regular host. This will redirect to the streaming server URL if configured, or return Not Found when the same host should be used.

S2: `GET /api/v2/instance` — "**OAuth:** Public"; `configuration[urls][streaming]` — "**Description:** The Websockets URL for connecting to the streaming API. **Type:** String (URL) … 4.0.0 - added". (Legacy v1: `urls[streaming_api]`.)

Live mastodon.social value (M1, `GET /api/v2/instance`, fetched now): `configuration.urls.streaming = "wss://streaming.mastodon.social"`; `version = "4.8.0-nightly.2026-10-06"`; `api_versions = {"mastodon": 12}`.

###### SSE — federated timeline (S1 "Watch the federated timeline {#public}")
```http
GET /api/v1/streaming/public HTTP/1.1
```
> Returns all public statuses
> **Returns:** `update`, `delete`, `status.update`
> **OAuth:** User token + `read:statuses`
> **Version history:** 1.0.0 - added / 2.4.0 - add `only_media` parameter / 3.5.0 - now returns `status.update` / 4.2.0 - changed to require a User token, removing Public and App token access [#23989]
> Headers — Authorization: Provide this header with `Bearer <user_token>` to gain authorized access to this API method.
> Query parameters — only_media: Boolean. If true, return only statuses with media attachments.

Other public streams (same section style): `/api/v1/streaming/public/local`, `/api/v1/streaming/public/remote`, `/api/v1/streaming/hashtag?tag=`, `/api/v1/streaming/hashtag/local?tag=` — all "4.2.0 - changed to require a User token".

SSE framing (S1 "About HTTP server-sent events"):
> The stream will contain events as well as heartbeat comments. Lines that begin with a colon (`:`) can be ignored by parsers. For example, the connection may be kept alive with a heartbeat comment:
```text
:thump
```
> Generally, events have this structure:
```text
event: <name>
data: <payload>
```

Health check (S1): `GET /api/v1/streaming/health` — "**OAuth:** Public", returns `OK`.

###### WebSocket alternative (S1 "Establishing a WebSocket connection")
```http
wss://mastodon.example/api/v1/streaming
```
> **OAuth:** User token + `read` (or `read:statuses` and/or `read:notifications`) … 3.3.0 - added / 4.2.0 - changed to require a User token, removing Public and App token access
> Open a multiplexed WebSocket connection to receive events. … the streaming server uses text frames only.
> stream — {required} String. When attempting to watch a single stream for events. See [Streams] for possible values. / {optional} String. When initiating a general connection without a specific subscription target.
> list — String. When `stream` is set to `list`, use this parameter to specify the list ID.
> tag — String. When `stream` is set to `hashtag` or `hashtag:local`, use this parameter to specify the tag name.
> type — String. For JSON-encoded payloads sent to the server, specify either `subscribe` or `unsubscribe` in order to manage the events that you wish to receive.
> Query parameters are recommended for single-purpose connections, but parameters may also be provided by sending a JSON-encoded payload over the WebSocket connection with `type` parameter.
```json
{ "type": "subscribe", "stream": "hashtag:local", "tag": "foo" }
```
So federated timeline over WebSocket: `wss://streaming.mastodon.social/api/v1/streaming?stream=public` (or subscribe message `{"type":"subscribe","stream":"public"}`).

Stream names (S1): `public` "All public posts known to the server. Analogous to the federated timeline."; `public:media`; `public:local`; `public:local:media`; `public:remote`; `public:remote:media`; `hashtag`; `hashtag:local`; `user`; `user:notification`; `list`; `direct`.

##### 3. How credentials are sent

S1 "Authorization styles":
> The streaming endpoints documented here that require authorization suggest using the `Authorization` HTTP header with a `Bearer <user_token>` value. This is the preferred and recommended approach to authorization, and matches what is required for many of the REST API endpoints. As alternatives, sending the same user token as a `Sec-Websocket-Protocol` header or sending an `access_token` query param will also work.
> Performing authorization with an `access_token` query param is not recommended for new clients as query params are sometimes collected in access logs. Legacy support only.
> Events are JSON-encoded. If an invalid access token is provided, the connection will be closed immediately.

Required OAuth scope: `read:statuses` for `/api/v1/streaming/public` (SSE); `read` (or `read:statuses` and/or `read:notifications`) for the WebSocket endpoint. S5: "Requesting `read` will also grant [granular scopes] shown in the right column of the table below." (table lists `read:statuses` under `read`). S4: "If an endpoint specifies `read:statuses` and you have `read` access, then you will be able to use that endpoint, since scopes are hierarchical."
Token type: **User token** (App tokens from `client_credentials` are rejected since 4.2.0, per S1 version history).

##### 4. Rate limits / quotas

S7 (https://docs.joinmastodon.org/api/rate-limits/), verbatim:
> Rate limit information is returned in the response headers: `X-RateLimit-Limit` Number of requests permitted per time period; `X-RateLimit-Remaining` Number of requests you can still make; `X-RateLimit-Reset` Timestamp when your rate limit will reset
> By default, the following limits are hardcoded:
> ### Per account — All endpoints and methods can be called 300 times within 5 minutes.
> ### Per IP — All endpoints and methods can be called 300 times within 5 minutes.

NOT VERIFIED: any limit on the number of concurrent streaming connections per account/IP, or event-rate limits on the streaming server — not documented in S1/S7. The documented limits are for REST API calls; whether they apply to the separate streaming server is not stated.

##### 5. Message format

Event types (S1 verbatim):
- `update` — "A new Status has appeared. Payload contains a [Status] cast to a string. Available since v1.0.0"
- `delete` — "A status has been deleted. Payload contains the String ID of the deleted Status. Available since v1.0.0"
- `status.update` — "A Status has been edited. Payload contains a [Status] cast to a string. Available since v3.5.0"
- also `notification`, `filters_changed`, `conversation`, `announcement`, `announcement.reaction`, `announcement.delete`, `notifications_merged` (not emitted by the public stream; `/streaming/public` "Returns: `update`, `delete`, `status.update`").

SSE: `event:` line = event name; `data:` line = payload (JSON-encoded Status for `update`/`status.update`; bare ID string for `delete`).
WebSocket: JSON object `{"stream": [...], "event": "<name>", "payload": "<string>"}`; S1: "Note that while the event is JSON-encoded, the `payload` is string-encoded and escaped, so it must be parsed and loaded as JSON from that string. However, for `delete` and `announcements.delete` events the payload is a string representing an identifier, not a JSON value."
Path to record: SSE → `json.loads(data)`; WS → `json.loads(json.loads(frame)["payload"])`.

Status entity fields (S6, verbatim descriptions; main ones):
- `id` — ID of the status in the database. (String, cast from an integer but not guaranteed to be a number)
- `uri` — URI of the status used for federation.
- `created_at` — The date when this status was created. (Datetime string)
- `account` — The account that authored this status. (Account)
- `content` — HTML-encoded status content.
- `visibility` — Visibility of this status. (Enumerable oneOf)
- `sensitive` — Is this status marked as sensitive content?
- `spoiler_text` — Subject or summary line, below which status content is collapsed until expanded.
- `media_attachments` — Media that is attached to this status.
- `application` — The application used to post this status. (Hash)
- `mentions` — Mentions of users within the status content.
- `tags` — Hashtags used within the status content.
- `emojis` — Custom emoji to be used when rendering status content.
- `reblogs_count` / `favourites_count` / `quotes_count` / `replies_count` — How many boosts / favourites / accepted quotes / replies this status has received.
- `url` — A link to the status's HTML representation. (nullable)
- `in_reply_to_id` — ID of the status being replied to. (nullable)
- `in_reply_to_account_id` — Might be the ID of the account that authored the status being replied to. (nullable)
- `reblog` — The status being reblogged. (nullable Status)
- `poll` — The poll attached to the status. (nullable) ; `card` — Preview card for links included within status content. (nullable)
- `language` — Primary language of this status. (nullable, ISO 639-1)
- `text` — Plain-text source of a status. Returned instead of `content` when status is deleted … (nullable)
- `edited_at` — Timestamp of when the status was last edited. (nullable)
- `quote`, `quote_approval`, `tagged_collections`; user-relative: `favourited`, `reblogged`, `muted`, `bookmarked`, `pinned`, `filtered`.

##### 6. Official examples (verbatim)

S1 "Watch the federated timeline" — SSE (https://docs.joinmastodon.org/methods/streaming/#public):
````text
```text
event: update
data: [official example payload omitted here: it is a real user's post (account, content, avatar URLs); it is in the cited documentation page and in raw/ex_masto_*.txt]
```

An example delete:

```text
event: delete
data: 107214471804101576
```
````

S1 "Establishing a WebSocket connection" — WebSocket (https://docs.joinmastodon.org/methods/streaming/#websocket); note: the payload line in the official source is very long and is copied exactly as published:
````text
An example update to the public timeline:

```json
{
  "stream": [
    "public"
  ],
  "event": "update",
  "payload": "[official example payload omitted here: it is a real user's post (account, content, avatar URLs); it is in the cited documentation page and in raw/ex_masto_*.txt]
}
```
````

S1 WebSocket delete example:
```json
{
  "stream": [
    "public"
  ],
  "event": "delete",
  "payload": "106692867363994015"
}
```

S1 error responses:
```json
{
  "error": "Unknown channel requested"
}
```
```json
{
  "error": "Unknown stream type",
  "status":400
}
```

##### 7. Probe without credentials (2026-10-13T18:17:31Z, Python urllib / `websockets` 16.1.1, 30 s timeouts)

| Request | Result (status, first ≤300 bytes) |
| --- | --- |
| `GET https://mastodon.social/api/v1/streaming/health` | 200 `text/plain` — `OK` |
| `GET https://streaming.mastodon.social/api/v1/streaming/health` | 200 `text/plain` — `OK` |
| `GET https://mastodon.social/api/v1/streaming` (discovery) | 400 `application/json` — `{"error":"Unknown channel requested"}` (no redirect observed; differs from S1's "redirect … or return Not Found") |
| `GET https://streaming.mastodon.social/api/v1/streaming/public` (no token) | 401 `application/json` — `{"error":"Missing access token"}` |
| `WSS wss://streaming.mastodon.social/api/v1/streaming?stream=public` (no token) | Handshake rejected: HTTP 401 Unauthorized, header `x-error-message: Missing access token`, empty body |
| `GET https://mastodon.social/api/v2/instance` | 200 — `configuration.urls.streaming = wss://streaming.mastodon.social` |

##### 8. Terms / server rules (mastodon.social)

- Terms of service URL (from M1 `configuration.urls.terms_of_service`): https://mastodon.social/terms-of-service ; API `GET /api/v1/instance/terms_of_service` → `effective_date: 2026-08-31`. Title: "Terms for registered users of mastodon.social". Key clauses (verbatim):
  > These terms apply to the provision of the Service by us to registered users of the Service.
  > When you upload Content to the Service, you are making it available via the Internet. Anyone, or any computer, might access your Content via RSS aggregators and readers, embed your Content in web pages and other media, or index and store your Content in search engines and databases. Please note that neither we, nor you, have control over these uses of your Content, and these services may not display your Content as you expect it.
  > We may suspend, limit, or cease to operate any or all of the Service, or vary its functionality, if and to the extent reasonably necessary for operational, security, legal, or business reasons.
  > These terms are provided in equally authoritative German and English versions. … in case of any inconsistency, the German version shall prevail.
- Privacy policy: https://mastodon.social/privacy-policy — "This privacy policy describes how mastodon.social (\"mastodon.social\", \"we\", \"us\") collects, protects and uses the personally identifiable information you may provide through the mastodon.social website or its API." Posts: "When you submit a message, the date and time is stored as well as the application you submitted the message from."
- About page https://mastodon.social/about (extended description, updated 2026-08-07): "Signing up for an account on this server means you agree to follow the server rules below, and our extended community standards here."
- Server rules (`/api/v1/instance/rules`, verbatim titles): (1) Sexually explicit or violent media must be marked as sensitive or with a content warning; (2) No racism, sexism, homophobia, transphobia, ableism, xenophobia, or casteism.; (3) No incitement of violence or promotion of violent ideologies; (4) No harassment, block evasion, dogpiling, or doxxing of others; (7) Do not share information widely-known to be false and misleading; (1008) Content created by others must be attributed, and use of generative AI must be disclosed.
- Extended community standards linked from /about: https://help.joinmastodon.org/article/12-community-standards (fetched now), verbatim:
  > Don't spam or manipulate the platform — No repetitive posting, artificial engagement manipulation, commercial spam, or using automation to disrupt conversations.
  > Don't abuse our systems — No creating single-purpose harassment accounts, mass false reporting, selling accounts, evading bans, or attempting to bypass our security measures or age verification (where applicable).
  > Mastodon.social and Mastodon.online are open to anyone who is 16 years or older.
- NOT VERIFIED: any explicit clause permitting or forbidding read-only automated access, scraping, or bulk collection of the public stream. None of the ToS, privacy policy, about/extended description, server rules, or community standards fetched now contain such a clause (searched for automat/scrap/bot/crawl/harvest/API); the only automation clause is the "using automation to disrupt conversations" prohibition above.

### E.mbta_v3 — `mbta_v3.md`

#### MBTA V3 API — streaming `/vehicles` (Server-Sent Events)

Fetched: 2026-10-13 (UTC ~18:21–18:24). Raw copies in `/tmp/opencode/streams-session/keydocs/raw/mbta_*` (incl. `mbta_swagger.raw` = https://api-v3.mbta.com/docs/swagger/swagger.json, Swagger 2.0, `info.version` "3.0").

##### 1. Sign-up URL and key delivery

https://www.mbta.com/developers/v3-api ("Request an API Key"):

> We recommend using a V3 API key early in your development process. A valid key is required to make a default of 1,000 requests per minute, control the version , and stream requests.
> Request a free key

("Request a free key" links to https://api-v3.mbta.com/.)

https://api-v3.mbta.com/ ("MBTA V3 API Portal"):

> Welcome to the MBTA's V3 API developer portal. The V3 API is the MBTA's premier schedule, real-time, and alert information interface for third-party developers.
> Here you can create or access your account and request API keys or key limit increases.
> ...
> 2. Request an API key
> Register for a developer account for yourself and an API key for each app. Getting a key might take a day, but you don't need an API key to experiment!

Registration link (Swagger securityDefinitions): "[Register for a key](/register)" → https://api-v3.mbta.com/register.

=> Key obtained via the V3 API Portal account ("might take a day"). Whether it is e-mailed or only shown in the portal: **NOT VERIFIED** (not stated).

##### 2. Endpoint, method, parameters

Streaming page https://www.mbta.com/developers/v3-api/streaming (verbatim):

> V3 API “index” endpoints support streaming over the server-sent event/event stream protocol. For clients that can maintain an open connection to the server, this is a more efficient and lower-latency way to receive data from the V3 API.
>
> To stream updates:
> 1. Use the `Accept: text/event-stream` header to tell the server you want streaming updates.
> 2. Specify an API key (either with the `X-API-Key` header or the `api_key` query parameter). Anonymous access is not possible for streaming.
> 3. Handle the four possible event types.
>
> Currently, only the initial request counts against your API key rate limit. As long as you keep the connection open, it will be treated as a single request.

=> **GET https://api-v3.mbta.com/vehicles** with header `Accept: text/event-stream` (+ key).

`/vehicles` GET parameters (Swagger `paths./vehicles.get.parameters`, all `in: query`, none required; descriptions verbatim, truncated where marked …):

| Name | Type / enum | Description |
|---|---|---|
| `page[offset]` | integer | Offset (0-based) of first element in the page |
| `page[limit]` | integer | Max number of elements to return |
| `sort` | string; `bearing`, `carriages`, `current_status`, `current_stop_sequence`, `direction_id`, `label`, `latitude`, `longitude`, `occupancy_status`, `revenue_status`, `speed`, `updated_at` (each also with `-` prefix) | Results can be sorted by the id or any `/data/{index}/attributes` key. Assumes ascending; may be prefixed with '-' for descending … |
| `fields[vehicle]` | string | Fields to include with the response. Multiple fields **MUST** be a comma-separated (U+002C COMMA, ",") list. … |
| `include` | string | Relationships to include. * `trip` * `stop` * `route` … |
| `filter[id]` | string | Filter by multiple IDs. Multiple IDs **MUST** be a comma-separated (U+002C COMMA, ",") list. Cannot be combined with any other filter. |
| `filter[trip]` | string | Filter by `/data/{index}/relationships/trip/data/id`. … comma-separated … Cannot be combined with any other filter. |
| `filter[label]` | string | Filter by label. Multiple `label` **MUST** be a comma-separated (U+002C COMMA, ",") list. |
| `filter[route]` | string | Filter by route. If the vehicle is on a multi-route trip, it will be returned for any of the routes. Multiple `route_id` **MUST** be a comma-separated (U+002C COMMA, ",") list. |
| `filter[direction_id]` | `"0"`, `"1"` | Filter by direction of travel along the route. Must be used in conjuction with `filter[route]` to apply. … |
| `filter[route_type]` | `"0"`–`"4"` | Filter by route_type: https://gtfs.org/documentation/schedule/reference/#routestxt. Multiple `route_type` **MUST** be a comma-separated … list. |
| `filter[revenue]` | `NON_REVENUE`, `REVENUE`, `NON_REVENUE,REVENUE` | Filter vehicles by revenue status. … When filter is not included, the default behavior is to filter by `revenue=REVENUE`. … |

Documented responses: `200`, `400`, `403`, `429` ("Too Many Requests").

Streaming notes (verbatim, streaming page):

> If you’re using the `include` parameter to fetch related resources, only the primary resource will be tracked for updates. For this reason, you likely want to use vehicles, predictions, or alerts as the primary resource type. The included resources will be combined with the primary resources as a part of the `reset` event.
>
> If you do want to receive updates for a single item, you can use the `filter[id]` query parameter to limit your search to that single resource.

Official curl example (streaming page; for `/predictions`, not `/vehicles`):

```
curl -sN -H "accept: text/event-stream" -H "x-api-key: API_KEY"
"https://api-v3.mbta.com/predictions/?filter\\[route\\]=CR-Worcester&filter\\[stop\\]=place-sstat&stop_sequence=1"
```

##### 3. How the key is sent

- Streaming page: "either with the `X-API-Key` header or the `api_key` query parameter".
- Swagger `securityDefinitions`: `api_key_in_header` → `{"type": "apiKey", "name": "x-api-key", "in": "header"}`; `api_key_in_query` → `{"type": "apiKey", "name": "api_key", "in": "query"}`.

##### 4. Rate limits

https://www.mbta.com/developers/v3-api/best-practices ("Rate Limiting"), verbatim:

> Use of the V3 API is subject to certain rate limits:
> Requests made without an API key are limited to 20 requests per minute.
> Requests made with a valid API key are limited to 1,000 requests per minute. If needed, you can request a rate limit increase in the V3 API Portal .
> ...
> All V3 API responses include HTTP headers, which show your rate limit status:
> x-ratelimit-limit — The maximum number of requests you’re allowed to make per time window
> x-ratelimit-remaining — The number of requests remaining in the current time window
> x-ratelimit-reset — The time at which the current rate limit time window ends in UTC epoch seconds

Streaming (verbatim, above): "Currently, only the initial request counts against your API key rate limit. As long as you keep the connection open, it will be treated as a single request." Anonymous streaming is not allowed.

##### 5. Event names and data shape

Streaming page, "Event Types" (verbatim):

> The V3 API sends four different types of events to keep clients up to date: Reset, Add, Update, Remove.
> Each resource/identifier has a unique (`id`, `type`) pair that can be used to track changes across multiple events.

| Event | Data shape (verbatim) |
|---|---|
| `reset` | "The `reset` event contains the full current state of the endpoint represented as a list of JSON-API resource objects. It’s always the first event in the stream, but it can also be sent during the connection if the API server determines that it is more efficient than sending individual resource changes." → `data:` is a **JSON array** of resource objects. |
| `add` | "The `add` event is sent when new resources are added, and it contains a single JSON-API resource object." → `data:` is **one object**. |
| `update` | "The `update` event is sent when existing resources are updated, and it contains a single JSON-API resource object." → **one object**. |
| `remove` | "The `remove` event is sent when a resource is removed, and it contains a single JSON-API resource identifier object." → `{"id": ..., "type": "vehicle"}` only. |

Vehicle resource object: `{"id", "type": "vehicle", "attributes": {...}, "relationships": {"route","stop","trip"}, "links": {"self"}}`. (Non-streaming JSON:API path to the list: `data[]`, `Content-Type: application/vnd.api+json` — observed in probe.)

Attributes (Swagger `definitions` Vehicle resource `attributes`, descriptions verbatim, truncated where marked …):

| Attribute | Type | Description |
|---|---|---|
| `updated_at` | string | Time at which vehicle information was last updated. Format is ISO8601. |
| `speed` | number | Speed that the vehicle is traveling in meters per second. See GTFS-realtime Position speed. |
| `revenue_status` | string | `"REVENUE"` Indicates that the associated trip is accepting passengers. / `"NON_REVENUE"` Indicates that the associated trip is not accepting passengers. |
| `occupancy_status` | string | The degree of passenger occupancy for the vehicle. See GTFS-realtime OccupancyStatus. Only the following values are used for vehicle-level occupancy status: MANY_SEATS_AVAILABLE (Not crowded: the vehicle has a large percentage of seats available.), FEW_SEATS_AVAILABLE (Some crowding …) … |
| `longitude` | number | Longitude of the vehicle's current position.  Degrees East, in the WGS-84 coordinate system. |
| `latitude` | number | Latitude of the vehicle's current position. Degrees North, in the WGS-84 coordinate system. |
| `label` | string | User visible label, such as the one of on the signage on the vehicle. |
| `direction_id` | integer | Direction in which trip is traveling: `0` or `1`. The meaning of `direction_id` varies based on the route. … |
| `current_stop_sequence` | integer | Index of current stop along trip. |
| `current_status` | string | Status of vehicle relative to the stops. See GTFS-realtime VehicleStopStatus. INCOMING_AT (The vehicle is just about to arrive at the stop …), STOPPED_AT (The vehicle is standing at the stop.), IN_TRANSIT_TO … |
| `carriages` | array | Carriage-level crowding details. See GTFS-realtime multi_carriage_details. (example `[{"occupancy_status": "MANY_SEATS_AVAILABLE", "occupancy_percentage": 80, "label": "some-carriage"}]`) |
| `bearing` | integer | Bearing, in degrees, clockwise from True North, i.e., 0 is North and 90 is East. This can be the compass bearing, or the direction towards the next stop or intermediate location. |

Relationships: `trip`, `stop`, `route`. (Note: the Swagger `example` values for `latitude`/`longitude` are swapped — `longitude` example 42.33, `latitude` example -71.27 — a doc error.)

##### 6. Official example (verbatim, https://www.mbta.com/developers/v3-api/streaming)

```
event: reset
data: [{"attributes":{"bearing":315.0,"current_status":"IN_TRANSIT_TO","current_stop_sequence":310,"direction_id":0,"label":"3673-3838","latitude":42.33982849121094,"longitude":-71.15853881835938,"speed":null,"updated_at":"2018-06-08T11:22:55-04:00"},"id":"G-10067","links":{"self":"/vehicles/G-10067"},"relationships":{"route":{"data":{"id":"Green-B","type":"route"}},"stop":{"data":{"id":"70107","type":"stop"}},"trip":{"data":{"id":"36418064","type":"trip"}}},"type":"vehicle"},{"attributes":{"bearing":90.0,"current_status":"IN_TRANSIT_TO","current_stop_sequence":null,"direction_id":1,"label":null,"latitude":42.349124908447266,"longitude":-71.09575653076172,"speed":null,"updated_at":"2018-06-08T11:22:30-04:00"},"id":"0446","links":{"self":"/vehicles/0446"},"relationships":{"route":{"data":{"id":"57","type":"route"}},"stop":{"data":null},"trip":{"data":{"id":"36616656","type":"trip"}}},"type":"vehicle"}]
```

```
event: add
data: {"attributes":{"bearing":160.0,"current_status":"INCOMING_AT","current_stop_sequence":30,"direction_id":0,"label":"3633-3868","latitude":42.36283874511719,"longitude":-71.05811309814453,"speed":null,"updated_at":"2018-06-08T11:22:55-04:00"},"id":"G-10300","links":{"self":"/vehicles/G-10300"},"relationships":{"route":{"data":{"id":"Green-E","type":"route"}},"stop":{"data":{"id":"70204","type":"stop"}},"trip":{"data":{"id":"36420357","type":"trip"}}},"type":"vehicle"}
```

```
event: update
data: {"attributes":{"bearing":76.0,"current_status":"IN_TRANSIT_TO","current_stop_sequence":8,"direction_id":0,"label":"1633","latitude":42.56092834472656,"longitude":-70.81510162353516,"speed":19.0,"updated_at":"2018-06-08T11:21:52-04:00"},"id":"1633","links":{"self":"/vehicles/1633"},"relationships":{"route":{"data":{"id":"CR-Newburyport","type":"route"}},"stop":{"data":{"id":"Beverly Farms","type":"stop"}},"trip":{"data":{"id":"CR-Weekday-Spring-18-107","type":"trip"}}},"type":"vehicle"}
```

```
event: remove
data: {"id":"1723","type":"vehicle"}
```

(The 2018 examples predate the `carriages`, `occupancy_status` and `revenue_status` attributes now in the Swagger schema.)

##### 7. Probe without key (2026-10-13, Python urllib, 30 s timeout)

```
UTC 2026-10-13T18:23:10Z GET https://api-v3.mbta.com/vehicles?filter[route]=Red  {'Accept': 'text/event-stream'}
STATUS 406 | Content-Type: application/json; charset=utf-8
BODY[0:300] {"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}

UTC 2026-10-13T18:23:10Z GET https://api-v3.mbta.com/vehicles?filter[route]=Red&page[limit]=1   (no Accept header, non-streaming)
STATUS 200 | Content-Type: application/vnd.api+json; charset=utf-8 | x-ratelimit-limit: 20
BODY[0:300] {"data":[{"attributes":{"bearing":330,"carriages":[{"label":"1730","occupancy_status":"NO_DATA_AVAILABLE","occupancy_percentage":null},{"label":"1731","occupancy_status":"NO_DATA_AVAILABLE","occupancy_percentage":null},{"label":"1522","occupancy_status":"NO_DATA_AVAILABLE","occupancy_percentage":nul
```

Confirms the docs: anonymous SSE is refused (HTTP 406 `not_acceptable`), anonymous plain JSON works with `x-ratelimit-limit: 20`.

##### 8. Terms / licence

Streaming and V3 pages: "Use of MBTA data is governed by the MassDOT Developers License Agreement (PDF, 85.5 KB)" → https://cdn.mbta.com/sites/default/files/2023-08/mbta-massdot-develop-license-agreement.pdf. Key clauses (verbatim):

> 3.1    MassDOT, subject to your acceptance of the Terms of this License Agreement, hereby grants You (Licensee) non-exclusive, limited, and revocable rights to use, reproduce, and redistribute the Data.

> 4.1       You shall:
> • Clearly acknowledge MassDOT as the provider of the Data.
> ...
> • Not reproduce or use MassDOT or any of its agencies or authorities logos or trademarks in connection with the Data.
> • Not misrepresent the Data.
> • Not claim ownership of the Data in any manner, including but not limited to, on Your website, web application, or any other digital product.
>
> 4.2       You may:
> • Combine the Data with other data, provided such combination does not infringe any third party Intellectual Property Rights.

### E.mta_bustime — `mta_bustime.md`

#### MTA Bus Time — SIRI VehicleMonitoring (New York City buses)

Fetched: 2026-10-13 (UTC ~18:10–18:15). All quotes are verbatim from the pages cited.

##### 1. Sign-up URL and key delivery

Source: https://bustime.mta.info/developers

> Go [here](https://register.developer.obanyc.com/) to request an API Key. You will receive one within half an hour. While you're waiting, please check out the documentation for the [SIRI Real-Time API](/developers/siri/) and the [OneBusAway "Discovery" API](/developers/restful-api).

Source: https://register.developer.obanyc.com/ (the request form itself)

> MTA BusTime Developer API Key Request
> Welcome, developer! Please fill out this form to get a key for MTA BusTime's real-time developer API.
> ...
> You will receive your key by email within half an hour.

Form fields: Name\* (min 2 characters), Email Address\*, "What is the name of your app or project?" ("If you're working on this for a class, let us know."), "What is the URL of your app?", "What platforms does your app work on?" (Web / iPhone / Android / Amazon Echo / Other). (\* = required.)

=> Sign-up: https://register.developer.obanyc.com/ ; key delivered **by email**, "within half an hour".

##### 2. Endpoint, method, parameters

Source: https://bustime.mta.info/developers/siri/vehicle-monitoring/

> It is accessible at the following URLs:
> [https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json](https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json)
>
> Please note that the calls made without either a VehicleRef or LineRef produces quite a load on the system, so use them sparingly. Any developers found to be making repeated calls (e.g. at less than  30 second intervals) for all vehicles in the system may find their key revoked.
>
> with the following GET parameters:
> - **key** - your MTA Bus Time developer API key (required). Go [here](https://register.developer.obanyc.com) to get one.
> - **version** - which version of the SIRI API to use (1 or 2). Defaults to 1, but 2 is preferrable.
> - **OperatorRef** - the GTFS agency ID to be monitored (optional). Currently `MTA`.
> - **VehicleRef** - the ID of the vehicle to be monitored (optional). This is the 4-digit number painted on the side of the bus, for example `7560`. Response will include all buses if not included.
> - **LineRef** - a filter by 'fully qualified' route name, GTFS agency ID + route ID (optional).
> - **DirectionRef** - a filter by GTFS direction ID (optional). Either `0` or `1`.
> - **VehicleMonitoringDetailLevel** - Level of detail present in response. In order of verbosity:
>   - `minimum` - only available in version 2. Designed for front-end use.
>   - `basic` - only available in version 2. Designed for system-to-system interchange when GTFS is loaded.
>   - `normal` - default.
>   - `calls` Determines whether or not the response will include the stops ("calls" in SIRI-speak) each vehicle is going to make **after** it serves the selected stop.
> - **MaximumNumberOfCallsOnwards** Limit on the number of `OnwardCall` elements for each vehicle when `VehicleMonitoringDetailLevel=calls`
> - **MaximumStopVisits** - an upper bound on the number of buses to return in the results.
> - **MinimumStopVisitsPerLine** - a lower bound on the number of buses to return in the results per line/route (assuming that many are available)

Method: **HTTP GET**. Source: https://bustime.mta.info/developers/siri/

> as well, while SIRI requests are typically SOAP requests sent via HTTP POST, in this case we implemented a slimmed-down RESTful interface using HTTP GET requests.

> Thus, MTA Bus Time provides both XML and JSON versions of its API.

Notes:
- The documented host is `bustime-classic.mta.info`. A probe (section 7) shows `https://bustime.mta.info/api/siri/vehicle-monitoring.json` also answers with the same SIRI error envelope, but that host path is **not** stated in the docs (observed only).
- LineRef format: the docs example value of the field in responses is `MTA NYCT_B63` (agency ID + `_` + route ID) — see section 5. The exact request syntax (e.g. URL encoding of the space) is not separately documented: NOT VERIFIED beyond "GTFS agency ID + route ID".
- The XML endpoint URL (e.g. `vehicle-monitoring.xml`) is not listed on the page; only the `.json` URL is given. NOT VERIFIED.

###### GTFS-Realtime vehicle positions (same key)

Source: https://bustime.mta.info/developers/gtfs-realtime/

> MTA Bus Time now supports [ GTFS-Realtime](https://github.com/google/transit/tree/master/gtfs-realtime/spec/en).
>
> TripUpdates, VehiclePositions, and Alerts are available at the following URLs:
> - `https://gtfsrt.prod.obanyc.com/tripUpdates?key=<YOUR_KEY>`
> - `https://gtfsrt.prod.obanyc.com/vehiclePositions?key=<YOUR_KEY>`
> - `https://gtfsrt.prod.obanyc.com/alerts?key=<YOUR_KEY>`
>
> Where `<YOUR_KEY>` is your MTA Bus Time developer API key (required).  Go [here](https://register.developer.obanyc.com) to get one.

=> Yes, a GTFS-RT bus VehiclePositions feed exists on `gtfsrt.prod.obanyc.com`, documented as using the same Bus Time key in the `key` query parameter.

##### 3. How the key is sent

Query parameter **`key`** (SIRI: "**key** - your MTA Bus Time developer API key (required)"; GTFS-RT: "`?key=<YOUR_KEY>`" — quotes above). No header mechanism is documented.

##### 4. Rate limits

No numeric rate limit (requests/second or per day) is published on the Bus Time developer pages fetched. The only usage constraint stated (https://bustime.mta.info/developers/siri/vehicle-monitoring/):

> Please note that the calls made without either a VehicleRef or LineRef produces quite a load on the system, so use them sparingly. Any developers found to be making repeated calls (e.g. at less than  30 second intervals) for all vehicles in the system may find their key revoked.

Formal per-key quota: **NOT VERIFIED** (not stated in any official page fetched).

##### 5. Response format and structure

Source: https://bustime.mta.info/developers/siri/vehicle-monitoring/ — documented as XML (JSON is the same SIRI structure; the JSON endpoint is the one listed). Path to the vehicle list:

- XML: `Siri/ServiceDelivery/VehicleMonitoringDelivery/VehicleActivity[]`
- JSON (observed in the probe envelope, section 7): `Siri.ServiceDelivery.VehicleMonitoringDelivery[0].VehicleActivity[]` — `VehicleMonitoringDelivery` is a JSON **array**. The `VehicleActivity` array key in JSON is inferred from the XML element name; the JSON shape with vehicles was NOT VERIFIED without a key.

Documented per-record fields (comments from the official XML):

| Element | Documented meaning |
|---|---|
| `ServiceDelivery/ResponseTimestamp` | "The timestamp on the MTA Bus Time server at the time the request was fulfilled" |
| `VehicleMonitoringDelivery/ValidUntil` | "The time until which the response data is valid until." |
| `VehicleActivity` | "SIRI container for data about a particular vehicle" |
| `VehicleActivity/RecordedAtTime` | "The timestamp of the last real-time update from the particular vehicle" |
| `VehicleActivity/MonitoredVehicleJourney` | documented separately (below) |

MonitoredVehicleJourney (https://bustime.mta.info/developers/siri/monitored-vehicle-journey/):

| Element | Documented meaning (verbatim comment) |
|---|---|
| `LineRef` | "The 'fully qualified' route name (GTFS agency ID + route ID) for the trip the vehicle is serving. Not intended to be customer-facing." |
| `DirectionRef` | "The GTFS direction for the trip the vehicle is serving" |
| `FramedVehicleJourneyRef/DataFrameRef` | "The GTFS service date for the trip the vehicle is serving" |
| `FramedVehicleJourneyRef/DatedVehicleJourneyRef` | "The GTFS trip ID for trip the vehicle is serving, prefixed by the GTFS agency ID" |
| `JourneyPatternRef` | "The GTFS Shape_ID, prefixed by GTFS Agency ID" |
| `PublishedLineName` | "The GTFS route_short_name" |
| `OperatorRef` | "GTFS Agency_ID" |
| `OriginRef` | "The GTFS stop ID for the first stop on the trip the vehicle is serving, prefixed by Agency ID" |
| `DestinationRef` | "The GTFS stop ID for the last stop on the trip the vehicle is serving, prefixed by Agency ID" |
| `DestinationName` | "The GTFS trip_headsign for the trip the vehicle is serving" |
| `OriginAimedDepartureTime` | "If a bus has not yet departed, OriginAimedDepartureTime indicates the scheduled departure time of that bus from that terminal in ISO8601 format" |
| `SituationRef/SituationSimpleRef` | "SituationRef, present only if there is an active service alert covering this call" |
| `Monitored` | "Always true" |
| `VehicleLocation/Longitude`, `/Latitude` | "The most recently recorded or inferred coordinates of this vehicle" |
| `Bearing` | "Vehicle bearing: 0 is East, increments counter-clockwise" |
| `ProgressRate` | "Indicator of whether the bus is making progress (i.e. moving, generally), not moving (with value noProgress), laying over before beginning a trip (value layover), or serving a trip prior to one which will arrive (prevTrip)." |
| `ProgressStatus` | "Optional indicator of vehicle progress status.  Set to "layover" when the bus is in a layover waiting for its next trip to start at a terminal, and/or "prevTrip" when the bus is currently serving the previous trip ..." |
| `Occupancy` | "Optional indicator of whether the bus occupancy is deemed to be "full","seatsAvailable" or "standingAvailable". If bus occupancy information is not available, this indicator is not shown (aka hidden.)" |
| `VehicleRef` | "The vehicle ID, preceded by the GTFS agency ID" |
| `BlockRef` | "Depending on the system's level of confidence, the GTFS block_id the bus is serving." |
| `MonitoredCall` | "Call data about a particular stop ... in VehicleMonitoring it is the next stop the bus will make." Children: `StopPointRef`, `VisitNumber` ("always 1 in this implementation"), `ExpectedArrivalTime`/`ExpectedDepartureTime` ("Predicted arrival/departure times in ISO8601 format"), `Extensions/Distances/{CallDistanceAlongRoute, DistanceFromCall ("in meters"), PresentableDistance, StopsFromCall}` |
| `OnwardCalls/OnwardCall[]` | "A stop that the vehicle is going to make, if the detailLevel is set to calls" (adds `StopPointName`) |

##### 6. Official example response (verbatim)

Source: https://bustime.mta.info/developers/siri/vehicle-monitoring/ (XML; the docs contain no JSON example; the `...` elisions are in the original)

```xml
<!-- SIRI container elements -->
<Siri version="1.3" xmlns="http://www.siri.org.uk/siri">
  <ServiceDelivery>

    <!-- The timestamp on the MTA Bus Time server at the time the request was fulfilled -->
    <ResponseTimestamp>2011-01-28T14:22:48-05:00</ResponseTimestamp>

    <!-- SIRI container for VehicleMonitoring response data -->
    <VehicleMonitoringDelivery version="1.3">

      <!-- Same as above.  Required by the SIRI spec. -->
      <ResponseTimestamp>2011-01-28T14:22:48-05:00</ResponseTimestamp>
      <!-- The time until which the response data is valid until. -->
      <ValidUntil>2011-01-28T14:23:48-05:00</ValidUntil>

      <!-- SIRI container for data about a particular vehicle -->
      <VehicleActivity>

        <!-- The timestamp of the last real-time update from the particular vehicle -->
        <RecordedAtTime>2011-01-28T14:22:30-05:00</RecordedAtTime>

        <!-- A MonitoredVehicleJourney element for a vehicle in revenue service. Please See the MonitoredVehicleJourney page for a thorough description -->
        <MonitoredVehicleJourney>
          ...
        </MonitoredVehicleJourney>
      </VehicleActivity>

      <!-- The next vehicle. -->
      <VehicleActivity>
        <RecordedAtTime>2011-01-28T14:22:43-05:00</RecordedAtTime>

        <!-- A complete MonitoredVehicleJourney element. See the MonitoredVehicleJourney page for more information -->
        <MonitoredVehicleJourney>...</MonitoredVehicleJourney>
      </VehicleActivity>

      ... More VehicleActivity elements

    </VehicleMonitoringDelivery>
  </ServiceDelivery>
</Siri>
```

Source: https://bustime.mta.info/developers/siri/monitored-vehicle-journey/ (verbatim)

```xml
<MonitoredVehicleJourney>

  <!-- The 'fully qualified' route name (GTFS agency ID + route ID) for the trip the vehicle is serving. Not intended to be customer-facing. -->
  <LineRef>MTA NYCT_B63</LineRef>

  <!-- The GTFS direction for the trip the vehicle is serving -->
  <DirectionRef>1</DirectionRef>

  <!-- A compound element uniquely identifying the trip the vehicle is serving -->
  <FramedVehicleJourneyRef>

    <!-- The GTFS service date for the trip the vehicle is serving -->
    <DataFrameRef>2011-01-28</DataFrameRef>

    <!-- The GTFS trip ID for trip the vehicle is serving, prefixed by the GTFS agency ID -->
    <DatedVehicleJourneyRef>MTA NYCT_20110102EA_087800_B63_0002_B63_19</DatedVehicleJourneyRef>
  </FramedVehicleJourneyRef>

  <!-- The GTFS Shape_ID, prefixed by GTFS Agency ID -->
  <JourneyPatternRef>MTA NYCT_B630152</JourneyPatternRef>

  <!-- The GTFS route_short_name -->
  <PublishedLineName>B63</PublishedLineName>

  <!-- GTFS Agency_ID -->
  <OperatorRef>MTA NYCT</OperatorRef>

  <!-- The GTFS stop ID for the first stop on the trip the vehicle is serving, prefixed by Agency ID  -->
  <OriginRef>MTA_801131</OriginRef>

  <!-- The GTFS stop ID for the last stop on the trip the vehicle is serving, prefixed by Agency ID -->
  <DestinationRef>MTA_801042</DestinationRef>

  <!-- The GTFS trip_headsign for the trip the vehicle is serving -->
  <DestinationName>BAY RIDGE SHORE RD via 5 AV</DestinationName>

  <!-- If a bus has not yet departed, OriginAimedDepartureTime indicates the scheduled departure time of that bus from that terminal in ISO8601 format -->
  <OriginAimedDepartureTime>2011-01-28T14:45:00.000-04:00</OriginAimedDepartureTime>

  <!-- SituationRef, present only if there is an active service alert covering this call -->
  <SituationRef>
    <SituationSimpleRef>MTA NYCT_8d065d76-2813-46ee-b024-20f956232831</SituationSimpleRef>
  </SituationRef>

  <!-- Always true -->
  <Monitored>true</Monitored>

  <!-- The most recently recorded or inferred coordinates of this vehicle -->
  <VehicleLocation>
    <Longitude>-73.97857</Longitude>
    <Latitude>40.68448</Latitude>
  </VehicleLocation>

  <!-- Vehicle bearing: 0 is East, increments counter-clockwise -->
  <Bearing>345.7</Bearing>

  <!-- Indicator of whether the bus is making progress (i.e. moving, generally), not moving (with value noProgress), laying over before beginning a trip (value layover), or serving a trip prior to one which will arrive (prevTrip). -->
  <ProgressRate>normalProgress</ProgressRate>

  <!-- Optional indicator of vehicle progress status.  Set to "layover" when the bus is in a layover waiting for its next trip to start at a terminal, and/or "prevTrip" when the bus is currently serving the previous trip and the information presented 'wraps around' to the following scheduled trip. -->
  <ProgressStatus>layover</ProgressStatus>

  <!-- Optional indicator of whether the bus occupancy is deemed to be "full","seatsAvailable" or "standingAvailable". If bus occupancy information is not available, this indicator is not shown (aka hidden.)  -->
  <Occupancy>seatsAvailable</Occupancy>

  <!-- The vehicle ID, preceded by the GTFS agency ID -->
  <VehicleRef>MTA NYCT_7582</VehicleRef>

  <!-- Depending on the system's level of confidence, the GTFS block_id the bus is serving. Please see "Transparency of Block vs. Trip-Level Assignment" section below  -->
  <BlockRef>MTA NYCT_20120902CE_JG_24900_B35-26-JG_1503</BlockRef>

  <!-- Call data about a particular stop -->
  <!-- In StopMonitoring, it is the stop of interest; in VehicleMonitoring it is the next stop the bus will make. -->

  <MonitoredCall>

    <!-- The GTFS stop ID of the stop prefixed by agency_id -->
    <StopPointRef>MTA_308214</StopPointRef>

    <!-- The ordinal value of the visit of this vehicle to this stop, always 1 in this implementation -->
    <VisitNumber>1</VisitNumber>

    <!-- Predicted arrival/departure times in ISO8601 format  -->
    <ExpectedArrivalTime>2015-06-04T10:46:08.361-04:00</ExpectedArrivalTime>
    <ExpectedDepartureTime>2015-06-04T10:46:08.361-04:00</ExpectedDepartureTime>

    <!-- SIRI container for extensions to the standard -->
    <Extensions>

      <!-- The MTA Bus Time extensions to show distance of the vehicle from the stop -->
      <Distances>

        <!-- The distance of the stop from the beginning of the trip/route  -->
        <CallDistanceAlongRoute>3038.9</CallDistanceAlongRoute>

        <!-- The distance from the vehicle to the stop along the route, in meters -->
        <DistanceFromCall>1101.7</DistanceFromCall>

        <!-- The distance displayed in the UI, see below for an additional note -->
        <PresentableDistance>5 stops away</PresentableDistance>

        <!-- The number of stops on the vehicle's current trip until the stop in question, starting from 0 -->
        <StopsFromCall>5</StopsFromCall>
      </Distances>
    </Extensions>

  </MonitoredCall>

  <!-- The collection of calls that a vehicle is going to make.  -->
  <OnwardCalls>

    <!-- A stop that the vehicle is going to make, if the detailLevel is set to calls  -->
    <OnwardCall>

      <!-- The GTFS stop ID of the stop -->
      <StopPointRef>MTA_308215</StopPointRef>

      <!-- The ordinal value of the visit of this vehicle to this stop, always 1 in this implementation -->
      <VisitNumber>1</VisitNumber>

      <!-- The GTFS stop name of the stop -->
      <StopPointName>5 AV - GARFIELD PL</StopPointName>

      <!-- SIRI container for extensions to the standard -->
      <Extensions>

        <!-- The MTA Bus Time extensions to show distance of the vehicle from the stop -->
        <Distances>

          <!-- The distance of the stop from the beginning of the trip/route  -->
          <CallDistanceAlongRoute>3267.1</CallDistanceAlongRoute>

          <!-- The distance from the vehicle to the stop along the route, in meters -->
          <DistanceFromCall>1329.9</DistanceFromCall>

          <!-- The distance displayed in the UI -->
          <PresentableDistance>6 stops away</PresentableDistance>

          <!-- The number of stops on the vehicle's current trip until the stop in question, starting from 0 -->
          <StopsFromCall>6</StopsFromCall>
        </Distances>
      </Extensions>

    </OnwardCall>

    ... more OnwardCalls

  </OnwardCalls>
</MonitoredVehicleJourney>
```

Official JSON example: **none in the docs** (NOT VERIFIED JSON key names beyond the error envelope observed in the probe).

##### 7. Probe without key (2026-10-13, Python urllib, 30 s timeout)

```
UTC 2026-10-13T18:14:33Z GET https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json?version=2
STATUS 401 | Content-Type: application/json;charset=ISO-8859-1
BODY[0:300] {"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-13T14:14:34.203-04:00","VehicleMonitoringDelivery":[{"ResponseTimestamp":"2026-10-13T14:14:34.203-04:00","ErrorCondition":{"OtherError":{"ErrorText":"API key required."},"Description":"API key required."}}]}}}

UTC 2026-10-13T18:14:34Z GET https://bustime.mta.info/api/siri/vehicle-monitoring.json?version=2   (host not in docs)
STATUS 401 | Content-Type: application/json;charset=ISO-8859-1
BODY[0:300] {"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-13T14:14:34.656-04:00","VehicleMonitoringDelivery":[{"ResponseTimestamp":"2026-10-13T14:14:34.656-04:00","ErrorCondition":{"OtherError":{"ErrorText":"API key required."},"Description":"API key required."}}]}}}

UTC 2026-10-13T18:14:34Z GET https://gtfsrt.prod.obanyc.com/vehiclePositions
STATUS 200 | Content-Type: None
BODY[0:300] (binary protobuf, Python repr) b'\n\r\n\x031.0\x10\x00\x18\xf1\xe9\xb9\xd6\x06\x12\x89\x01\n\rMTA NYCT_9771"x\n0\n\x1eMQ_D6-Weekday-SDon-083500_M8_2\x1a\x0820261013*\x02M90\x01\x12\x0f\r\\\xe5"B\x155\xf5\x93\xc2\x1d\x1c\x17jC(\xe2\xe9\xb9\xd6\x06:\x06403305B\x1c\n\rMTA NYCT_9771\xc2>\n\n\x08STROLLERH\x02\xf2>\x04\x08-\x10P\x12\x8c\x01\n\rMTA NYCT_9775"{\n3\n MV_D6-Weekday-SDon-085100_M10_16\x1a\x0820261013*\x03M100\x01\x12\x0f\rVO#B\x15\x85\xe0\x93\xc2\x1d\x12\x07jC(\xd3\xe9\xb9\xd6\x06:\x06401307B\x1c\n\rMTA NYCT_9775\xc2>\n\n\x08STROLLERH\x01\xf2>\x04\x08\x15\x10P\x12\x82'
```

Observation: the GTFS-RT `vehiclePositions` feed answered **200 with real protobuf data without a key**, although the docs say the key is "(required)". This is an observed behaviour, not a documented guarantee; do not rely on it.

##### 8. Terms / licence

Bus Time pages link "Terms & Conditions" to https://www.mta.info/terms-and-conditions and send developers to https://www.mta.info/developers ("For information about licensing and about MTA's other developer feeds, please see the MTA's Developer Resources page"). The data-feed terms are at https://www.mta.info/developers/terms-and-conditions ("Terms and conditions for MTA data feeds", "Updated Mar 13, 2024"). Key clauses (verbatim):

> By accessing our data feeds, you are agreeing to these Terms and Conditions. This agreement authorizes you to download and host the data on a non-MTA server (maintained by you or a third party) and to make the data available to others who will access that non-MTA server.
> MTA prohibits the development of an app that would make the data available to others directly from MTA's server(s).

> You will not state or imply that the data is accurate, complete, or timely. You may however, state that you obtained the data from MTA and, through your own server, are redistributing it.

> You will not modify or delete any of the data. You may, however, create an app that uses some but not all of the data.

> When using MTA Real-Time data feeds, if there is a lag time of more than 1 minute between the real time of the MTA data and the actual time of the MTA data as accessed from your server, you will also indicate the information provided by your app to the end-user may not be real time because of the lag time between the real time of the MTA data and the MTA data as provided by you.

From https://www.mta.info/developers:

> Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to [apply for a license](/doing-business-with-us/licensing-program).

Note: the terms page states it covers "real-time feeds of subway and railroad data ... subject to our terms and conditions"; the developers page lists Bus Time under the same "Realtime data" section. Whether the Bus Time key is bound by exactly this document is implied by the Bus Time page's pointer, not stated explicitly — partly NOT VERIFIED.

### E.nta — `nta.md`

#### Ireland — National Transport Authority (NTA) GTFS-Realtime v2 `Vehicles`

Fetched: 2026-10-13 (UTC ~18:20–18:23). The portal https://developer.nationaltransport.ie/ is an Azure API Management developer portal (JavaScript-rendered); API docs were read from its official backing data API on the same host:

- `https://developer.nationaltransport.ie/developer/apis?api-version=2022-04-01-preview`
- `https://developer.nationaltransport.ie/developer/apis/gtfsr/operations/vehicles?api-version=2022-04-01-preview`
- `https://developer.nationaltransport.ie/developer/apis/gtfsr?export=true&format=openapi%2Bjson&api-version=2022-04-01-preview`
- `https://developer.nationaltransport.ie/developer/products?api-version=2022-04-01-preview`

Raw copies: `/tmp/opencode/streams-session/keydocs/raw/nta_*`.

##### 1. Sign-up URL and key delivery

Home page (https://developer.nationaltransport.ie/), verbatim:

> Welcome to NTA API Developer Portal
> Providing public transport API's for Ireland.
> Discover APIs, learn how to use them, try them out interactively. To view and use the API you need to sign up to acquire keys.
> IMPORTANT NOTICE:
> A New Version (v2) of GTFS-Realtime API has been released

Sign-up page: https://developer.nationaltransport.ie/signup ("Sign up / Already a member? Sign in .").

API description (`/developer/apis/gtfsr`, field `description`, verbatim excerpt):

> 1) This is throttled as per <a href="https://developer.nationaltransport.ie/usagepolicy">fair usage </a>and you need to register to use the live feed.
>
> 2) Once you <a href ="https://developer.nationaltransport.ie/product#product=gtfs-realtime">subscribe </a>to an API it can take <b>15 minutes </b> before it becomes active.

Product (`/developer/products`): `"id":"gtfs-realtime","name":"GTFS Realtime"`, `"subscriptionRequired":true,"approvalRequired":false,"subscriptionsLimit":1`.

Usage policy §6 (https://developer.nationaltransport.ie/usagepolicy):

> The User will be issued a pair of Unique Tokens (the “Token”) that will be required for each access request. These Tokens are non-transferable and all activity will be attributed to the User.

=> Flow: sign up → subscribe to product "GTFS Realtime" (no approval required, max 1 subscription) → a pair of keys is issued; active up to 15 minutes later. Where the keys are displayed (portal profile page vs. e-mail): **NOT VERIFIED** (the profile page is not readable anonymously and no page states it).

##### 2. Endpoint, method, parameters

API "General Transit Feed Specification - GTFS-Realtime" (id `gtfsr`), OpenAPI export `servers`: `[{"url": "https://api.nationaltransport.ie/gtfsr"}]`. Operations:

| id | name | method | urlTemplate |
|---|---|---|---|
| `vehicles` | Vehicles | GET | `/v2/Vehicles` |
| `TripUpdates` | TripUpdates | GET | `/v2/TripUpdates` |
| `gtfsr-v2` | gtfsr (version 2) | GET | `/v2/gtfsr` ("Request TripUpdates (Alternative function name)") |
| `gtfs-alerts` | GTFS Alerts | GET | `/v2/alerts` |

=> **GET https://api.nationaltransport.ie/gtfsr/v2/Vehicles**

Vehicles operation (verbatim):

```json
{
 "id": "vehicles",
 "name": "Vehicles",
 "method": "GET",
 "urlTemplate": "/v2/Vehicles",
 "templateParameters": [],
 "description": "Request Vehicle Information",
 "request": {
  "queryParameters": [
   {
    "name": "format",
    "type": "string",
    "values": [
     "json"
    ]
   }
  ],
  "headers": [],
  "representations": []
 },
 "responses": [
  {
   "statusCode": 200,
   "description": "Successful Operation",
   "representations": [],
   "headers": []
  }
 ]
}
```

- Only parameter: optional `format` with the single documented value `json`.
- That the response is **protobuf when `format` is omitted** is **NOT VERIFIED** from documentation (no page states the default format; it is the GTFS-RT norm but not written here).

Coverage (API description): "The GTFS-R API contains real-time updates for services provided by Dublin Bus, Bus Éireann, and Go-Ahead Ireland."

##### 3. How the key is sent

`subscriptionKeyParameterNames`: `{'header': 'x-api-key', 'query': 'subscription-key', 'bearer': None}`. OpenAPI export security schemes (verbatim):

```json
{"apiKeyHeader": {"type": "apiKey", "name": "x-api-key", "in": "header"}, "apiKeyQuery": {"type": "apiKey", "name": "subscription-key", "in": "query"}}
```

=> HTTP header **`x-api-key: <key>`** (or query parameter `subscription-key=<key>`).

##### 4. Rate limits

Usage policy §6 "Fair Usage Limits" (https://developer.nationaltransport.ie/usagepolicy), verbatim:

> Fair usage limits refer to the total number of GTFS Real Time API requests within the stated time frame. Usage limits are per day, and are not transferable from day to day or month to month
>
> The User will be issued a pair of Unique Tokens (the “Token”) that will be required for each access request. These Tokens are non-transferable and all activity will be attributed to the User.
>
> Each Token will be restricted to calling the GTFS Real Time API once every 60 seconds.
>
> The NTA may at its discretion alter the usage limit of Users.

=> **1 request / 60 s per token.** A numeric per-day cap is not stated (NOT VERIFIED). Whether the 60 s limit applies per endpoint or across all GTFS-RT endpoints is not stated (NOT VERIFIED; text says "calling the GTFS Real Time API").

Prohibited (§5): "Excessive Downloading : Engaging in activities that place excessive demand on the GTFS Data infrastructure, such as automated scripts or scraping, which can degrade the performance or accessibility of the service for others."

##### 5. Response format and structure

The NTA docs do not describe the response schema; they defer to the GTFS-RT reference (API description, verbatim):

> Further details on the GTFS-R API
> - https://developers.google.com/transit/gtfs-realtime
> - https://gtfs.org/reference/realtime/v2/

So the structure is GTFS-Realtime `FeedMessage` → `entity[]` → `vehicle` (VehiclePosition: `trip`, `vehicle`, `position.latitude/longitude`, `timestamp`, ...). The exact JSON key casing of NTA's `format=json` output (e.g. `entity` vs `Entity`, snake_case vs camelCase) is **NOT VERIFIED** — no official example or schema for the JSON rendering exists on the portal, and it could not be observed without a key.

##### 6. Official example response

**None.** The Vehicles operation has `"representations": []` for both request and the 200 response; no example payload is published in the portal.

##### 7. Probe without key (2026-10-13, Python urllib, 30 s timeout)

```
UTC 2026-10-13T18:21:51Z GET https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json
STATUS 401 | Content-Type: application/json
BODY[0:300] { "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }

UTC 2026-10-13T18:21:51Z GET https://api.nationaltransport.ie/gtfsr/v2/Vehicles
STATUS 401 | Content-Type: application/json
BODY[0:300] { "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }
```

##### 8. Terms / licence

URL: https://developer.nationaltransport.ie/usagepolicy ("Fair Usage Policy"). Key clauses (verbatim):

> 3. Licensing
> GTFS Data © 2025 by  the NTA is licensed under Creative Commons Attribution 4.0 International

> 7. Data Attribution
> Users must attribute the GTFS Data to the NTAwhen using it in any public-facing applications, presentations, or publications. Such attributions should include:
> The name of the Data Provider; in this case, the NTA.
> A link to the GTFS Data source or the NTAs website.
> A statement that clarifies the GTFS Data is provided "as is" and that the NTA is not responsible for any errors or inaccuracies.

> Commercial Exploitation : Using the GTFS Data primarily for profit without adding significant value or enhancements that benefit the public or the transit system.  (listed under "5. Prohibited Uses")

> Research and Analysis : Conducting studies or analysis to improve public transportation services.  (listed under "4. Permissible Uses")

### E.opensky — `opensky.md`

#### OpenSky Network REST API — key/credential documentation (fetched 2026-10-13 ~18:15 UTC)

Sources fetched now (raw copies in `raw/`):
- O1 https://openskynetwork.github.io/opensky-api/rest.html → `raw/osky_rest.html`
- O2 https://openskynetwork.github.io/opensky-api/index.html → `raw/osky_index.html`
- O3 https://opensky-network.org/about/faq → `raw/osky_faq.html`, `raw/osky_faq.txt`
- O4 https://opensky-network.org/about/terms-of-use → `raw/osky_terms.html`, `raw/osky_terms.txt`
- O5 https://opensky-network.org/data/api (only links to O1)

##### 1. Sign-up / credential process

O1 "Authentication" (verbatim):
> OpenSky exclusively supports the OAuth2 *client credentials* flow. Basic authentication with username and password is no longer accepted.
> To get started:
> 1. Log in to your OpenSky account and visit the [Account](https://opensky-network.org/my-opensky/account) page.
> 2. Create a new API client and retrieve your `client_id` and `client_secret`.
> 3. Exchange these for an access token, then pass it as a `Bearer` token on every request.

O3 FAQ Q19 "I have an account — what credentials do I use for each interface?" (verbatim):
> REST API | API Client ( client_id + client_secret ) via OAuth2 | Account page → API Client card; see API docs
> Trino (historical database) | Your website username + password (standard login) | Trino page; your username is shown on the Account page
> A common source of confusion: the API client ID ends in -api-client and is only for the REST API. Do not enter it into your feeder software — use your plain username instead. Similarly, the API client has no relation to Trino access; Trino access is granted separately by the administrators.

NOT VERIFIED: the account registration (sign-up) steps themselves (form fields, e-mail verification, approval). The fetched pages only say "Log in to your OpenSky account"; the site's "Sign in" link points to `/login`, whose registration flow was not documented in any fetched page.

##### 2. Endpoint(s), protocol, parameters

Root (O1): `https://opensky-network.org/api` — HTTPS REST, JSON responses, polling (no streaming endpoint).

`GET /states/all` (O1, verbatim parameter tables):
| Property | Type | Description |
| --- | --- | --- |
| *time* | integer | The time in seconds since epoch (Unix time stamp to retrieve states for. Current time will be used if omitted. |
| *icao24* | string | One or more ICAO24 transponder addresses represented by a hex string (e.g. abc9f3). To filter multiple ICAO24 append the property once for each address. If omitted, the state vectors of all aircraft are returned. |

> In addition to that, it is possible to query a certain area defined by a bounding box of WGS84 coordinates. For this purpose, add all of the following parameters:

| *lamin* | float | lower bound for the latitude in decimal degrees |
| *lomin* | float | lower bound for the longitude in decimal degrees |
| *lamax* | float | upper bound for the latitude in decimal degrees |
| *lomax* | float | upper bound for the longitude in decimal degrees |
| *extended* | integer | Set to 1 if required | (request the category of aircraft)

> Example query with bounding box covering Switzerland: `https://opensky-network.org/api/states/all?lamin=45.8389&lomin=5.9962&lamax=47.8229&lomax=10.5226`

No parameter is mandatory for `/states/all`. Other endpoints: `/states/own` (auth required, 403 otherwise), `/flights/all` (begin, end; ≤ 2 h), `/flights/aircraft`, `/flights/arrival`, `/flights/departure`, `/tracks` (experimental).

Token endpoint (O1, verbatim):
```
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret

export TOKEN=$(curl -X POST "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" https://opensky-network.org/api/states/all | jq .
```
- Token URL: `https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token`
- Form fields (`application/x-www-form-urlencoded`): `grant_type=client_credentials`, `client_id`, `client_secret`.
- Lifetime (O1): "Tokens expire after 30 minutes. A `401 Unauthorized` response means the token has expired - request a new one and retry." The official Python `TokenManager` reads `expires_in` (default `1800`) and refreshes `TOKEN_REFRESH_MARGIN = 30` seconds early.

##### 3. How credentials are sent

`Authorization: Bearer <access_token>` header on every API request (O1: "pass it as a `Bearer` token on every request"; example `curl -H "Authorization: Bearer $TOKEN" …`). `client_id`/`client_secret` are sent only to the token URL as form fields.
Basic auth: O1 "Basic authentication with username and password is no longer accepted." (see probe §7 for observed behaviour).

##### 4. Rate limits / quotas (O1 "Limitations" + "API Credits", verbatim)

> **Anonymous users** (unauthenticated, bucketed by IP): Only the most recent state vectors are available - the `time` parameter is ignored. Time resolution is 10 seconds.
> **Authenticated users:** State vectors up to 1 hour in the past. Requests with t < now - 3600 return `400 Bad Request`. Time resolution is 5 seconds.
> All endpoints consume credits except `/states/own`. Credits are tracked in **three independent buckets** - one each for `/states/*`, `/tracks/*`, and `/flights/*`. Spending credits on one endpoint has no effect on the others.

| Tier | Credits | Refill |
| --- | --- | --- |
| Anonymous | 400 | Daily |
| Standard user | 4,000 | Daily |
| Active feeder (≥30% uptime/month) | 8,000 | Daily |
| Licensed user | 14,400 | Hourly |

> Active feeder status is recalculated every 2 hours. Tier upgrades take effect after ~50 requests. To confirm you are receiving the 8,000-credit allowance, check that `X-Rate-Limit-Remaining` exceeds 4,000 at the start of a day.

Credit cost `/states/all` (bounding box area in sq° = latitude range × longitude range):
| Bounding box area | Credits |
| --- | --- |
| ≤ 25 sq° or serial-only query | 1 |
| 25 – 100 sq° | 2 |
| 100 – 400 sq° | 3 |
| > 400 sq° or global | 4 |

`/flights/*` and `/tracks/*`: Live / < 24 h → 4 credits; 1–2 partitions → 30; 3–10 → 60 × N; … > 25 → 960 × N.
> When credits are available, `X-Rate-Limit-Remaining` shows your remaining balance. When exhausted, the API returns `429 Too Many Requests` and `X-Rate-Limit-Retry-After-Seconds` indicates how many seconds to wait.

O3 FAQ Q17: "The OpenSky REST API is provided "as is". We may change access policies or apply rate limits as needed to protect system performance." … "Institutional (typically academic) researchers can request unlimited API access, including historical data. For non-profit causes with significant impact, please create an account and raise a data request."

##### 5. Response format (`/states/all`)

> The response is a JSON object with the following properties: *time* integer — The time which the state vectors in this response are associated with. All vectors represent the state of a vehicle with the interval [time - 1, time]. *states* array — The state vectors.
> The *states* property is a two-dimensional array. Each row represents a state vector and contains the following fields:

Path to records: `response["states"]` (may be `null` when empty — NOT VERIFIED, not stated in docs); each record is a positional array:

| Index | Property | Type | Description (O1 verbatim) |
| --- | --- | --- | --- |
| 0 | icao24 | string | Unique ICAO 24-bit address of the transponder in hex string representation. |
| 1 | callsign | string | Callsign of the vehicle (8 chars). Can be null if no callsign has been received. |
| 2 | origin_country | string | Country name inferred from the ICAO 24-bit address. |
| 3 | time_position | int | Unix timestamp (seconds) for the last position update. Can be null if no position report was received by OpenSky within the past 15s. |
| 4 | last_contact | int | Unix timestamp (seconds) for the last update in general. … |
| 5 | longitude | float | WGS-84 longitude in decimal degrees. Can be null. |
| 6 | latitude | float | WGS-84 latitude in decimal degrees. Can be null. |
| 7 | baro_altitude | float | Barometric altitude in meters. Can be null. |
| 8 | on_ground | boolean | … position was retrieved from a surface position report. |
| 9 | velocity | float | Velocity over ground in m/s. Can be null. |
| 10 | true_track | float | True track in decimal degrees clockwise from north (north=0°). Can be null. |
| 11 | vertical_rate | float | Vertical rate in m/s. … Can be null. |
| 12 | sensors | int[] | IDs of the receivers which contributed to this state vector. Is null if no filtering for sensor was used in the request. |
| 13 | geo_altitude | float | Geometric altitude in meters. Can be null. |
| 14 | squawk | string | The transponder code aka Squawk. Can be null. |
| 15 | spi | boolean | Whether flight status indicates special purpose indicator. |
| 16 | position_source | int | 0 = ADS-B, 1 = ASTERIX, 2 = MLAT, 3 = FLARM |
| 17 | category | int | Aircraft category (0 = No information at all … 20 = Line Obstacle) — only with `extended=1` (O1: "you can request the category of aircraft by adding the following request parameter") |

##### 6. Official example response

NONE found. O1 and O2 give example request URLs and curl commands but no verbatim example JSON response for `/states/all`. (O1 examples: `$ curl -s "https://opensky-network.org/api/states/all" | python -m json.tool`.)
For reference only (NOT official — live probe output, see §7): `{"time":1791915446,"states":[["4aca95","NSZ33DN ","Sweden",1791915446,1791915446,6.7444,47.2804,11887.2,false,240.26,176.19,0,null,12405.36,"0741",false,0], …` — 17 elements per row without `extended=1`.

##### 7. Probe without credentials (2026-10-13T18:17:31Z, Python urllib, 30 s timeout)

| Request | Status | Headers / first 300 bytes |
| --- | --- | --- |
| `GET /api/states/all?lamin=45.8389&lomin=5.9962&lamax=47.8229&lomax=10.5226` (anonymous) | 200 | `Content-Type: application/json`, `X-Rate-Limit-Remaining: 287` — `{"time":1791915446,"states":[["4aca95","NSZ33DN ","Sweden",1791915446,1791915446,6.7444,47.2804,11887.2,false,240.26,176.19,0,null,12405.36,"0741",false,0],["344409","VLG6263 ","Spain",1791915445,1791915445,7.3167,47.5172,2926.08,false,145.37,256.7,15.28,null,3162.3,"1000",false,0],["407b8f","BAW567` |
| `POST` token URL with `client_id=invalid-probe&client_secret=invalid` | 401 | `{"error":"invalid_client","error_description":"Invalid client or Invalid client credentials"}` |
| Same `/states/all` with `Authorization: Basic` (invalid user/pass) | 200 | `X-Rate-Limit-Remaining: 286` — identical anonymous body. Observation: an invalid Basic header is not rejected; the request is served from the anonymous IP bucket (remaining decreased 287→286). This does not show whether valid Basic credentials would grant authenticated tier; O1 says they are "no longer accepted" — valid-credential behaviour NOT VERIFIED (no credentials used). |

Note: anonymous IP bucket showed 287 remaining of 400 (this IP had already consumed credits today).

##### 8. Terms of use (O4 https://opensky-network.org/about/terms-of-use, verbatim)

> Tl;dr: License required in the following cases:
> Commercial or for-profit entities: Any use by a for-profit or commercial entity — including government and military contractors — requires a written license from OpenSky Network, regardless of purpose.
> Operational REST API use: Use of the REST API in any operational capacity — including integration into a live product, service, or automated system (even if only internal) — requires a previous written agreement, even for non-profit or governmental entities.

> 1. LICENSE — OpenSky Network's authorization to access the data grants You a limited, non-exclusive, non-transferable, non-assignable, and terminable license to copy, modify, and use the data in accordance with this AGREEMENT solely for the purpose of non-profit research and non-profit education. Government entities may obtain an exemption at the discretion of the OpenSky Network. No license is granted for any other purpose and there are no implied licenses in this AGREEMENT.

> 3. (iii) You will not distribute, disclose, transfer or otherwise make available the data set(s) to any person other than those employed by your institute who are assisting or collaborating with You using the data set(s). …
> 3. (v) You will not register multiple accounts on the OpenSky Network website. Specifically, You must not use multiple accounts in order to circumvent technical restrictions or blocks (e.g. obtaining additional requests to the REST API).
> 3. (vi) The REST API is provided for non-profit research and educational use only. Use of the REST API in any operational capacity — including but not limited to integration into a live product, service, or automated system — requires a written license from OpenSky Network, regardless of the entity's non-profit status.
> 4. (i) If You create a publication (including web pages, papers published by a third party, and publicly available presentations) using data from this data set, You must provide OpenSky Network with a copy of (or a link to) the publication and You must cite the data as follows: Bringing up OpenSky: A large-scale ADS-B sensor network for research — Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic, Matthias Wilhelm — ACM/IEEE International Conference on Information Processing in Sensor Networks, April 2014

Implication for course use (interpretation, flagged): educational non-profit use is licensed, but a continuously polling "automated system" may fall under "operational capacity", which requires a written licence; whether a classroom ingestion lab counts as "operational" is NOT VERIFIED — would need confirmation from contact[at]opensky-network.org.

### E.wmata — `wmata.md`

#### WMATA (Washington DC) — Train Positions API + GTFS-RT bus/rail vehicle positions

Fetched: 2026-10-13 (UTC ~18:15–18:20). The developer portal (https://developer.wmata.com) is an Azure API Management portal rendered by JavaScript; the API documentation was retrieved from its official backing data API (same host):

- API list: `https://developer.wmata.com/developer/apis?api-version=2022-04-01-preview`
- Operations: `https://developer.wmata.com/developer/apis/{apiId}/operations[/{opId}]?api-version=2022-04-01-preview`
- OpenAPI export: `https://developer.wmata.com/developer/apis/{apiId}?export=true&format=openapi%2Bjson&api-version=2022-04-01-preview`

Raw copies: `/tmp/opencode/streams-session/keydocs/raw/wmata_*.json`.

##### 1. Sign-up URL and key delivery

- Sign-up: https://developer.wmata.com/signup (static page text: "Sign up / Already a member? Sign in . / Developer License Agreement"; form config shows `"isConsentRequired":true,"termsEnabled":true,"requireHipCaptcha":true` — i.e. licence consent and a CAPTCHA are required).
- Key delivery — Developer License Agreement, https://developer.wmata.com/license ("WMATA Transit Data Terms of Use", "Last Revised on November 19, 2019"), section 5:

> For all other uses, You must create a developer account with WMATA and subscribe to one or more Transit Data service tiers. Each subscription will generate two security keys (Keys) that will enable you to access the service tier to which you are subscribed. The Keys enable WMATA to associate your API activity with your Application.

Section 4:

> Users who would like access to the WMATA API for limited testing purposes only may utilize WMATA’s public use key.

The public "Guests" product (from `https://developer.wmata.com/developer/products?api-version=2022-04-01-preview`, field `description`, verbatim HTML):

```html
<p>Looking for a demo API key? Use the key below to <a href="apis">try out</a> the API.</p>

<p class="bg-primary center-block" style="padding: 1em"><WMATA public demo key, shown on the cited page; not reproduced></p>

<p>Remember, don't use this for production applications! This key is rate limited and is subject to change at any time.</p>
```

(Product fields: `"subscriptionRequired": true, "approvalRequired": true, "subscriptionsLimit": 1`.)

Exactly where the generated keys are displayed after subscribing (profile page) could not be read anonymously: NOT VERIFIED (the licence only says each subscription "will generate two security keys").

##### 2. Endpoints, method, parameters

###### Train Positions — "Live Train Positions"

API "Train Positions" (id `5763fa6ff91823096cac1057`), OpenAPI servers: `http://api.wmata.com/TrainPositions`, `https://api.wmata.com/TrainPositions`. Operation `5763fb35f91823096cac1058`:

```
"name": "Live Train Positions",
"method": "GET",
"urlTemplate": "/TrainPositions?contentType={contentType}",
```

=> **GET https://api.wmata.com/TrainPositions/TrainPositions?contentType=json**

Parameter (verbatim from `templateParameters`):

```
"name": "contentType",
"description": "Returns response in the specified format.  Currently supported formats include <b>json</b> and <b>xml</b>.",
"type": "string",
"defaultValue": "json",
"required": true,
"values": ["json", "xml"]
```

No other query parameters (`"queryParameters": []`). Description (verbatim):

> Returns uniquely identifiable trains in service and what track circuits they currently occupy. Will return an empty set of results when no positions are available.
>
> Data is refreshed once every 7-10 seconds.

Companion operations in the same API: `GET /StandardRoutes?contentType={contentType}` ("Standard Routes"), `GET /TrackCircuits?contentType={contentType}` ("Track Circuits"). Positions are track circuits, not lat/lon — FAQ https://developer.wmata.com/trainpositionsfaq:

> What about lat/lon positions for the circuits?
> The idea of the train position API is to locate trains in relations to stations. For rendering trains on a map, one possibility is to determine the distance between stations (based on our existing APIs), and place the circuits between these stations at equidistant points.

###### GTFS-RT vehicle positions

API "GTFS" (id `gtfs`), OpenAPI server `https://api.wmata.com/gtfs`, description "GTFS and GTFS-RT feeds.":

| Operation (id) | Method | urlTemplate | Full URL |
|---|---|---|---|
| Bus RT Vehicle Positions (`5cdc52139e0b4de98fdfd54a`) | GET | `/bus-gtfsrt-vehiclepositions.pb` | **https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb** |
| Rail RT Vehicle Positions (`5d0244a2a94e17d2c638e590`) | GET | `/rail-gtfsrt-vehiclepositions.pb` | **https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb** |
| Bus RT Vehicle Positions QA (`640a24c8f19da0385c91c0b5`) | GET | `/bus-gtfsrt-vehiclepositions-qa.pb` | https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions-qa.pb |

No parameters (`"templateParameters": []`, `"queryParameters": []`). Descriptions (verbatim):

Bus:
> GTFS RT vehicle positions feed for WMATA bus.  Please refer to the GTFS RT vehicle positions reference for details on this operation, keeping in mind that this feed conforms to the GTFS-RT 1.0 specification *only*. ... As this is a binary feed, using the Developer Portal's Try it feature will *not* work as expected.

Rail:
> GTFS RT 2.0 vehicle positions feed for WMATA rail.  Please refer to the GTFS RT vehicle positions reference for details on this operation. ... As this is a binary feed, using the Developer Portal's Try it feature will *not* work as expected.

##### 3. How the key is sent

Every API in the list carries `"subscriptionKeyParameterNames": {"header": "api_key", "query": "api_key", "bearer": null}`. OpenAPI export security schemes (verbatim):

```json
{"apiKeyHeader": {"type": "apiKey", "name": "api_key", "in": "header"}, "apiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}}
```

=> HTTP header **`api_key: <key>`** or query parameter **`?api_key=<key>`**.

##### 4. Rate limits

- Official, verbatim (Guests product, above): "This key is rate limited and is subject to change at any time." — no numbers.
- Licence section 5 mentions "call limits" ("do not require your users to obtain their own keys from WMATA to use your Application (for example, in an attempt to circumvent call limits)") without numbers.
- Numeric tier limits: **NOT VERIFIED.** The public products list (anonymous) returns only the "Guests" product; no tier with numbers is visible. Third-party pages (rdrr.io `metro` R package; m-soro.github.io) quote a WMATA "Default tier" description "Rate limited to 10 calls/second and 50,000 calls per day", but this could not be confirmed on an official WMATA page today.
- Train Positions data refresh: "Data is refreshed once every 7-10 seconds." (official, above).

##### 5. Response format and structure

###### TrainPositions (JSON/XML)

Path to the list: JSON `TrainPositions[]`; XML `TrainPositionResp/TrainPositions/TrainPosition[]`. Fields (verbatim from the operation's "Response Elements" table):

| Element | Description |
|---|---|
| TrainPositions | Array containing train position information (TrainPosition). |
| CarCount | Number of cars.  Can sometimes be 0 when there is no data available. |
| CircuitId | The circuit identifier the train is currently on.  This identifier can be referenced from the Standard Routes method. |
| DestinationStationCode | Destination station code. Can be NULL. Use this value in other rail-related APIs to retrieve data about a station.  Note that this value may *sometimes* differ from the destination station code returned by our Next Trains methods. |
| DirectionNum | The direction of movement regardless of which track the train is on.  Valid values are 1 or 2.  Generally speaking, trains with direction 1 are northbound/eastbound, while trains with direction 2 are southbound/westbound. |
| LineCode | Two-letter abbreviation for the line (e.g.: RD, BL, YL, OR, GR, or SV). May also be NULL in certain cases. |
| SecondsAtLocation | Approximate "dwell time".  This is not an exact value, but can be used to determine how long a train has been reported at the same track circuit. |
| ServiceType | Service Type of a train, can be any of the following Service Types |
| TrainId | Uniquely identifiable internal train identifier. |
| TrainNumber | *Non-unique* train identifier, often used by WMATA's Rail Scheduling and Operations Teams, as well as over open radio communication. |

Service Types: `NoPassengers` ("This is a non-revenue train with no passengers on board. ..."), `Normal` ("This is a normal revenue service train."), `Special` ("This is a special revenue service train with an unspecified line and destination.  This is more prevalent during scheduled track work."), `Unknown` ("This often denotes cases with unknown data or work vehicles.").

###### GTFS-RT feeds (protobuf binary)

Standard GTFS-RT `FeedMessage.entity[].vehicle` (VehiclePosition). WMATA notes (verbatim):

Bus `VehicleDescriptor`:
> occupancy_status — Estimated degree of passenger occupancy for the vehicle. MANY_SEATS_AVAILABLE: Bus less than 25% occupied / FEW_SEATS_AVAILABLE: Bus 25% - 49% occupied / FULL: Bus is occupied 50% or greater

Rail `VehicleDescriptor`:
> id — Uniquely identifiable internal train identifier. WMATA Example: 422
> label — Non-unique train identifier, often used by WMATA's Rail Scheduling and Operations Teams, as well as over open radio communication. WMATA Example: 213
> license_plate — Number of cars. Can sometimes be 0 when there is no data available. WMATA Example: 8
> occupancy_status — ... MANY_SEATS_AVAILABLE: Rail car less than 20% occupied / FEW_SEATS_AVAILABLE: Rail car 20% - 32% occupied / FULL: Rail car is occupied 33% or greater

##### 6. Official example responses (verbatim)

Source: operation `5763fb35f91823096cac1058`, `responses[0].representations[*].examples.default.value` at
https://developer.wmata.com/developer/apis/5763fa6ff91823096cac1057/operations/5763fb35f91823096cac1058?api-version=2022-04-01-preview
(NB: the official JSON example is itself **not valid JSON** — the comma after `"SecondsAtLocation": 25` is missing in the original; copied as-is.)

```json
{
   "TrainPositions":[
      {
         "TrainId": "100",
         "TrainNumber": "301",
         "CarCount": 6,
         "DirectionNum": 1,
         "CircuitId": 1234,
         "DestinationStationCode": "A01",
         "LineCode": "RD",
         "SecondsAtLocation": 0,
         "ServiceType": "Normal"    
      },
      {
         "TrainId": "200",
         "TrainNumber": "XY1",
         "CarCount": 6,
         "DirectionNum": 2,
         "CircuitId": 4321,
         "DestinationStationCode": null,
         "LineCode": null,
         "SecondsAtLocation": 25
         "ServiceType": "Special"
      }
   ]
}
```

```xml
<TrainPositionResp xmlns="http://www.wmata.com" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
<TrainPositions>
    <TrainPosition>
        <CarCount>6</CarCount>
        <CircuitId>1234</CircuitId>
        <DestinationStationCode>A01</DestinationStationCode>
        <DirectionNum>1</DirectionNum>
        <LineCode>RD</LineCode>
        <SecondsAtLocation>0</SecondsAtLocation>
        <ServiceType>Normal</ServiceType>
        <TrainId>100</TrainId>
        <TrainNumber>301</TrainNumber>
    </TrainPosition>
    <TrainPosition>
        <CarCount>6</CarCount>
        <CircuitId>4321</CircuitId>
        <DestinationStationCode i:nil="true"/>
        <DirectionNum>1</DirectionNum>
        <LineCode i:nil="true"/>
        <SecondsAtLocation>25</SecondsAtLocation>
        <ServiceType>Special</ServiceType>
        <TrainId>200</TrainId>
        <TrainNumber>XY1</TrainNumber>
    </TrainPosition>
</TrainPositions>
</TrainPositionResp>
```

GTFS-RT bus/rail vehicle positions: **no official example payload** in the docs (`"representations": []`; binary feed).

##### 7. Probe without key (2026-10-13, Python urllib, 30 s timeout)

```
UTC 2026-10-13T18:17:31Z GET https://api.wmata.com/TrainPositions/TrainPositions?contentType=json
STATUS 401 | Content-Type: application/json
BODY[0:300] { "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }

UTC 2026-10-13T18:17:32Z GET https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb
STATUS 401 | Content-Type: application/json
BODY[0:300] { "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }

UTC 2026-10-13T18:17:32Z GET https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb
STATUS 401 | Content-Type: application/json
BODY[0:300] { "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }
```

(The published demo key was intentionally not used.)

##### 8. Terms / licence

URL: https://developer.wmata.com/license — "WMATA Transit Data Terms of Use", "Last Revised on November 19, 2019" (linked from the portal footer as "Developer License Agreement"; https://www.wmata.com/about/developers/ says "View our Developer License Agreement for transit data terms of use."). Key clauses (verbatim):

> API . The WMATA API allows users and developers to receive Transit Data and use it for testing purposes or in the developer’s own software application, website, product or service (each an Application). For the sake of clarity, an Application explicitly does not include a user’s or developer’s application programming interface. Re-use of the API Transit Data in a user’s or developer’s application programming interface is strictly prohibited subject to the exceptions provided for in Section 8 below.

> Transit Data License Subject to your compliance with these Terms, WMATA grants you a limited, non-exclusive, non-assignable, non-transferrable, non-sublicensable, revocable license to download, use, reproduce, and redistribute WMATA's Transit Data within your Application.

> The Keys, while issued to you as part of your subscription, remain WMATA’s property and may be revoked or otherwise limited at any time and at WMATA’s sole discretion. You cannot sell, transfer, or sublicense them. Do not try to circumvent them and do not require your users to obtain their own keys from WMATA to use your Application (for example, in an attempt to circumvent call limits).

> To state or imply that the data you provide through your Application is accurate, complete, or timely, or that it is more accurate, more complete or more timely with respect to the underlying Transit Data provided through the API or GTFS.  (listed among prohibited uses)

## Appendix F — Tool versions

| Tool | Version |
|---|---|
| python | 3.13.16 |
| websockets | 15.0.1 |
| aiohttp | 3.14.5 |
| aiokafka | 0.14.0 |
| fastavro | 1.13.1 |
| paho-mqtt | 2.1.0 |
| pyzmq | 27.2.0 |
| nats-py | 2.16.0 |
| pyais | 3.3.1 |
| gtfs-realtime-bindings | 3.0.0 |
| protobuf | 7.36.2 |
| cryptography | 50.0.2 |
| pytest | 9.1.1 |
| pytest-asyncio | 1.4.0 |
| pytest-cov | 7.1.0 |
| coverage | 7.16.2 |
| ruff | 0.17.0 |
| uv | uv 0.13.0 (x86_64-unknown-linux-gnu) |
| docker | Docker version 29.9.0, build f415da8 |
| Kafka test image | apache/kafka:3.9.1 |

