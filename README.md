# stream-consumers

Consumers and subscribers for the public real-time data streams evaluated for the
final project of COM-22102 *Bases de Datos No Relacionales* (ITAM, Otoño 2026).

**Private, instructor-only repository**
([`mavasbel-itam/stream-consumers`](https://github.com/mavasbel-itam/stream-consumers)
on GitHub; it was `non-relational-dbs/stream-consumers` until 2026-10-19, and
older records still use that name). Students build their own ingestion
consumer as part of the project; do not share this repository with them.

The decision records are in [`docs/`](docs/README.md): the stream surveys,
how this repository was built, the screening of the Bytewax list and the status
of every API key
([`docs/reference/2026-10-17-15-13-api-key-gated-sources.md`](docs/reference/2026-10-17-15-13-api-key-gated-sources.md)).

## Inclusion rule

A source is included when its **median measured rate is at least 1 event per
second** over the sampling rounds (`stream_consumers.domain.policy.MINIMUM_RATE`,
`meets_minimum_rate`). A round in which the source delivered nothing (`no-events`)
or failed (`error`) counts as 0 events/s; a `key-pending` round measures nothing
and is left out (`round_rate`). The exceptions and pending cases:

- **GDELT is kept** although its measured medians were 0.977 events/s (2026-10-13)
  and 0.772 events/s (24 rounds, 2026-10-17/18), because the project document
  lists it (decision of 2026-10-13).
- Free-key providers whose keyless route was measured at ≥ 1 event/s are included
  (MBTA V3, TfL, NASA FIRMS); the key is optional for MBTA V3 and TfL, and FIRMS
  uses its keyless public files.
- **Candidates** (group D) needed a free key; until their own sampling with the
  key finished, their rate was unmeasured. They were built and tested against the
  providers' official documentation examples so that adding the key to `.env` was
  enough to run them. A candidate is accepted (group C, or B for aisstream.io)
  when its own sampling gives a median of at least 1 event/s with the key, and is
  transferred to the low-rate catalog otherwise.
  Seven of the eight were measured with their keys on 2026-10-17/19 and accepted
  on 2026-10-19: `cta_bus`, `cta_train`, `mastodon`, `mta_bustime`, `nta` and
  `wmata` (group C) and `aisstream` (group B), each with a certain median of at
  least 1 event/s (see [Sampling results](#sampling-results)). The ENTSO-E
  (`entsoe`) token arrived and was tested on 2026-10-19; the source measured
  0.010 events/s and cannot reach 1 event/s even reading every European area
  (under 0.4 points/s), so it went to group E
  ([Sources Below 1 Event/s](#sources-below-1-events-measured--low-rate-catalog)).
- Measured below 1 event/s and therefore excluded: Nostr, Stellar,
  ENA, PyPI, Hacker News, MLB; not measurable as configured: BitMEX, APRS-IS,
  Kystverket AIS, zKillboard.

Every rate in the source list was then re-checked with this repository's own
`sample` command; the results are in [Sampling results](#sampling-results).

- **Low-rate group (E) since 2026-10-19**: every source measured below
  1 event/s was first removed from the catalog and, on 2026-10-19, restored
  unchanged into group E: kept, tested and documented, but left out of
  `check`, `sample` and `profile` unless named (see
  [Sources Below 1 Event/s](#sources-below-1-events-measured--low-rate-catalog)).
  The removals, with the evidence of the day:
- **Lasair and Fink, removed 2026-10-18 (group E since 2026-10-19)**: both relay
  alerts of the Rubin Observatory LSST, and neither had published a single
  alert since 2026-07-14 (Lasair's latest detection 2026-07-14 10:03 UTC, 0
  objects in the last 30 days; Fink's last alert night 2026-07-14), so both
  would measure 0 events/s. The Kafka transport and the Avro decoder are
  tested against a local broker.
- **Removed 2026-10-18 after the 24-hour sampling of 2026-10-17/18, group E
  since 2026-10-19** (24 hourly rounds, 60-s windows): Bitstamp (`bitstamp`,
  median 0.515 events/s), npm (`npm`, 0.790) and Digitraffic train timetables
  (`dt_rail_trains`, 0.865), all below 1 event/s. GDELT (0.772) stays in the
  active catalog, as decided above.
- **Global Fishing Watch (`gfw`), removed 2026-10-18 (group E since
  2026-10-19)**: its events API publishes events days after they happen (the
  latest day with events was 2026-10-14 when read on 2026-10-18), so a poll
  sees no new events within a round. The totals of all four event datasets
  over a fixed date range did not grow at all in 18 hourly readings
  (2026-10-18 03:24–21:24 UTC), so the median arrival rate is 0 events/s; the
  readings continued to 2026-10-19 00:24 UTC (22 in all) and never changed.
- **ENTSO-E (`entsoe`), group E since 2026-10-19**: see the candidates above.
- **Added on 2026-10-19 from the Bytewax "Awesome Public Real-Time Datasets"
  list** (all 69 free entries screened): `blockchain`, `citibike`, `coinpaprika`,
  `ogn`, `sharpe` and `ukflood`, each keyless with a median of at least 1
  event/s in their own sampling. NOAA's National Data Buoy Center latest
  observations (`ndbc`) were added too and moved to group E on 2026-10-19:
  median 0.268 events/s over 3 rounds. Not added from that list: EPA AirNow (its hourly file lists 4,415 sites but only
  1,980 reported in the hour 2026-10-18 22:00 UTC, 0.55 events/s), Yahoo
  Finance (its terms forbid automated collection) and GitHub's REST events
  (the same events as `gharchive`).
- **Vélib' Paris was re-added on 2026-10-17**: it had been excluded at 0.983
  events/s on its earliest (night-time) rounds, but its median over 15 earlier
  cross-check rounds was 4.4 events/s; the 24-hour sampling decides.

## Sources (65)

Groups: **keyless** (49), **project document** (7, the sources the project
document lists), **free key** (9: key optional for 3, required for 6, rate
measured with the key), and **candidate** (group D, empty since 2026-10-19).
The 8 sources measured below 1 event/s are group E, listed in
[Sources Below 1 Event/s](#sources-below-1-events-measured--low-rate-catalog);
the code holds 73 sources in all.

| id | Source | Provider | Group | Transport | Delivery |
|---|---|---|---|---|---|
| `base_logs` | [Base (L2) contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `bitfinex` | [Bitfinex trades + ticker (public v2)](https://docs.bitfinex.com/docs/ws-public) | Bitfinex | keyless | websocket | push |
| `bitso` | [Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)](https://docs.bitso.com/bitso-api/docs) | Bitso (Mexico) | keyless | websocket | push |
| `blockchain` | [Blockchain.com — unconfirmed Bitcoin transactions](https://www.blockchain.com/api/api_websocket) | Blockchain.com | keyless | websocket | push |
| `bsc_logs` | [BNB Smart Chain contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `bybit` | [Bybit spot tickers](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) | Bybit | keyless | websocket | push |
| `coinbase` | [Coinbase Exchange ticker](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) | Coinbase | keyless | websocket | push |
| `coinpaprika` | [CoinPaprika — prices and market data of the 2,000 top-ranked crypto assets](https://docs.coinpaprika.com/api-reference/rest-api/introduction) | CoinPaprika | keyless | http | poll |
| `deribit` | [Deribit perpetual futures ticker](https://docs.deribit.com/) | Deribit | keyless | websocket | push |
| `eth_logs` | [Ethereum mainnet contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `gemini` | [Gemini market data v1 (order-book changes + trades)](https://developer.gemini.com/websocket/streams.md) | Gemini Trust Company | keyless | websocket | push |
| `hyperliquid` | [Hyperliquid trades](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) | Hyperliquid | keyless | websocket | push |
| `kraken` | [Kraken trades + ticker (v2)](https://docs.kraken.com/api/docs/websocket-v2/trade) | Kraken (Payward) | keyless | websocket | push |
| `okx` | [OKX public tickers](https://www.okx.com/docs-v5/en/) | OKX | keyless | websocket | push |
| `polygon_logs` | [Polygon PoS contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `polymarket` | [Polymarket CLOB market channel (prediction-market prices)](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) | Polymarket | keyless | websocket | push |
| `sharpe` | [Sharpe — perpetual-futures funding rates of 37 derivatives exchanges](https://www.sharpe.ai/docs/free-api) | Sharpe AI (Sharpe Terminal) | keyless | http | poll |
| `solana` | [Solana program logs (public mainnet RPC)](https://solana.com/docs/rpc/websocket/logssubscribe) | Solana Foundation (public mainnet-beta RPC) | keyless | websocket | push |
| `xrpl` | [XRP Ledger transactions](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe) | XRP Ledger Foundation (public cluster xrplcluster.com) | keyless | websocket | push |
| `albion` | [Albion Online Data Project market orders](https://www.albion-online-data.com/) | Albion Online Data Project (community) | keyless | nats | push |
| `twitch` | [Twitch chat (anonymous read-only IRC)](https://dev.twitch.tv/docs/chat/irc/) | Twitch Interactive | keyless | websocket | push |
| `atlas` | [RIPE Atlas measurement results stream (ping)](https://atlas.ripe.net/docs/apis/streaming-api) | RIPE NCC | keyless | websocket | push |
| `ct` | [Certificate Transparency logs (RFC 6962), read directly](https://www.rfc-editor.org/rfc/rfc6962) | Certificate Transparency log operators (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt, TrustAsia) | keyless | http | poll |
| `gharchive` | [GH Archive — all public GitHub events (hourly files)](https://www.gharchive.org/) | GH Archive (Ilya Grigorik) | keyless | http | file-drop |
| `osm` | [OpenStreetMap minutely replication diffs](https://wiki.openstreetmap.org/wiki/Planet.osm/diffs) | OpenStreetMap Foundation | keyless | http | file-drop |
| `ris` | [RIPE NCC RIS Live — global BGP routing updates](https://ris-live.ripe.net/manual/) | RIPE NCC | keyless | websocket | push |
| `crossref` | [Crossref scholarly metadata (works indexed per day)](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | Crossref | keyless | http | poll |
| `pskreporter` | [PSK Reporter amateur-radio reception reports](https://www.mqtt.pskreporter.info/) | PSK Reporter (Philip Gladstone) — MQTT feed by M0LTE | keyless | mqtt | push |
| `rbn` | [Reverse Beacon Network (CW/RTTY skimmer spots)](https://www.reversebeacon.net/) | Reverse Beacon Network | keyless | tcp | push |
| `seedlink` | [EarthScope (IRIS) SeedLink real-time seismic waveforms](https://ds.iris.edu/ds/nodes/dmc/services/seedlink/) | EarthScope Consortium (IRIS DMC) | keyless | tcp | push |
| `sensorcomm` | [Sensor.Community citizen air-quality sensors](https://github.com/opendata-stuttgart/meta/wiki/EN-APIs) | Sensor.Community (OK Lab Stuttgart / Code for Germany) | keyless | http | poll |
| `usgs_water` | [USGS Water Services instantaneous values (river gauges)](https://waterservices.usgs.gov/) | U.S. Geological Survey (USGS) | keyless | http | poll |
| `adsb_fi` | [adsb.fi open data aircraft — 250 NM around Mexico City airport](https://github.com/adsbfi/opendata) | adsb.fi | keyless | http | poll |
| `adsb_lol` | [adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport](https://www.adsb.lol/docs/open-data/api/) | adsb.lol | keyless | http | poll |
| `bicing` | [Bicing Barcelona bike-share station status (GBFS)](https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing) | Barcelona City Council (Bicing) | keyless | http | poll |
| `citibike` | [Citi Bike New York bike-share station status (GBFS)](https://citibikenyc.com/system-data) | Citi Bike (Lyft, Inc.) | keyless | http | poll |
| `dt_marine` | [Digitraffic Finland marine AIS vessel locations](https://www.digitraffic.fi/en/marine-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `dt_rail` | [Digitraffic Finland train GPS locations](https://www.digitraffic.fi/en/railway-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `dt_road` | [Digitraffic Finland road traffic (TMS) and road-weather sensors](https://www.digitraffic.fi/en/road-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `ecobici` | [EcoBici CDMX bike-share station status (GBFS)](https://ecobici.cdmx.gob.mx/datos-abiertos/) | Gobierno de la Ciudad de México (EcoBici, operated by Lyft) | keyless | http | poll |
| `entur` | [Entur Norway real-time vehicle positions](https://developer.entur.org/pages-real-time-intro) | Entur AS (Norway) | keyless | http | poll |
| `hsl` | [HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md) | Helsinki Regional Transport Authority (HSL) | keyless | mqtt | push |
| `mbta_gtfsrt` | [MBTA Boston GTFS-Realtime VehiclePositions](https://www.mbta.com/developers/gtfs-realtime) | Massachusetts Bay Transportation Authority (MBTA) | keyless | http | poll |
| `mta_gtfsrt` | [MTA New York City Subway GTFS-Realtime (A/C/E feed)](https://api.mta.info/) | Metropolitan Transportation Authority (MTA) | keyless | http | poll |
| `ndov` | [NDOV Loket Netherlands public transport KV6 (all operators)](https://ndovloket.nl/) | NDOV Loket (Netherlands) | keyless | zeromq | push |
| `ogn` | [Open Glider Network — live positions of gliders, light aircraft and ADS-B traffic](https://wiki.glidernet.org/wiki:subscribe-to-ogn-data) | Open Glider Network | keyless | tcp | push |
| `velib` | [Vélib' Métropole Paris bike-share station status (GBFS)](https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel) | Vélib' Métropole (Smovengo) | keyless | http | poll |
| `metar` | [NOAA aviationweather.gov METAR observations (global airports)](https://aviationweather.gov/data/api/) | NOAA National Weather Service — Aviation Weather Center | keyless | http | poll |
| `ukflood` | [Environment Agency (England) — real-time flood-monitoring readings: river level, flow, rainfall, tide](https://environment.data.gov.uk/flood-monitoring/doc/reference) | Environment Agency (England) | keyless | http | poll |
| `binance` | [Binance spot trades + 24 h tickers](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md) | Binance | project document | websocket | push |
| `mempool` | [mempool.space — Bitcoin transactions entering the mempool](https://mempool.space/docs/api/websocket) | The Mempool Open Source Project (mempool.space) | project document | websocket | push |
| `bluesky` | [Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts)](https://github.com/bluesky-social/jetstream) | Bluesky Social PBC | project document | websocket | push |
| `gdelt` | [GDELT 2.0 Event Database — 15-minute event exports](https://www.gdeltproject.org/data.html) | The GDELT Project | project document | http | file-drop |
| `wikimedia` | [Wikimedia EventStreams — recent changes on all Wikimedia wikis](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service) | Wikimedia Foundation | project document | sse | push |
| `opensky` | [OpenSky Network state vectors — aircraft over Mexico](https://openskynetwork.github.io/opensky-api/rest.html) | OpenSky Network | project document | http | poll |
| `aisstream` | [aisstream.io — global AIS ship positions and static data](https://aisstream.io/documentation) | aisstream.io | project document | websocket | push |
| `mbta_v3` | [MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)](https://www.mbta.com/developers/v3-api) | Massachusetts Bay Transportation Authority (MBTA) | free key (optional) | http | poll |
| `tfl` | [Transport for London Unified API — Tube arrival predictions](https://api-portal.tfl.gov.uk/) | Transport for London (TfL) | free key (optional) | http | poll |
| `firms` | [NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files](https://firms.modaps.eosdis.nasa.gov/active_fire/) | NASA Earth Science Data Systems (LANCE FIRMS) | free key (optional) | http | poll |
| `cta_bus` | [CTA Bus Tracker vehicles — every Chicago bus](https://www.transitchicago.com/developers/bustracker/) | Chicago Transit Authority (CTA) | free key (required) | http | poll |
| `cta_train` | [CTA Train Tracker locations — every Chicago 'L' train](https://www.transitchicago.com/developers/traintracker/) | Chicago Transit Authority (CTA) | free key (required) | http | poll |
| `mastodon` | [Mastodon federated public timeline (statuses, edits, deletions)](https://docs.joinmastodon.org/methods/streaming/) | Mastodon (default instance social.vivaldi.net, funded by Vivaldi Technologies) | free key (required) | sse | push |
| `mta_bustime` | [MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus](https://bustime.mta.info/developers/gtfs-realtime/) | Metropolitan Transportation Authority (MTA) | free key (required) | http | poll |
| `nta` | [NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland](https://developer.nationaltransport.ie/) | National Transport Authority (NTA), Ireland | free key (required) | http | poll |
| `wmata` | [WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail](https://developer.wmata.com/) | Washington Metropolitan Area Transit Authority (WMATA) | free key (required) | http | poll |

## Sources Below 1 Event/s (Measured & Low-Rate Catalog)

Group E (`Group.LOW_RATE`) holds the 8 sources measured below 1 event/s. Their
consumers, decoders and test data are kept and tested like every other source
(the 100 % coverage gate includes them), and every key they read has a live
probe. `check`, `sample` and `profile` leave them out when no source id is
given (`Group.active`); name one to run it, for example
`uv run stream-consumers check ndbc --seconds 960`. `list` shows all 73 sources
with their group. The measurements and the evidence behind each row are in
[`docs/reference/2026-10-19-18-27-sub-threshold-sources.md`](docs/reference/2026-10-19-18-27-sub-threshold-sources.md).

| id | Source | Transport / delivery | Key | Measured | Why it stays below 1 event/s (evidence) |
|---|---|---|---|---|---|
| `bitstamp` | [Bitstamp live trades](https://www.bitstamp.net/websocket/v2/) | websocket / push | — | median **0.515** events/s; 24/24 rounds, 3 at ≥ 1/s, min 0.150, max 3.555 (`sampling-20261017`) | Trades of the five subscribed pairs (BTC/USD, ETH/USD, XRP/USD, BTC/EUR, SOL/USD) arrive at under 1/s in most hours |
| `dt_rail_trains` | [Digitraffic Finland train timetables/actuals](https://www.digitraffic.fi/en/railway-traffic/) | mqtt / push | — | median **0.865**; 24/24 rounds, 7 at ≥ 1/s, min 0.200, max 1.246 (`sampling-20261017`) | Every message on `trains/#` is counted; fewer than 1 per second in most hours |
| `entsoe` | [ENTSO-E actual generation per production type](https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API) | http / poll | `ENTSOE_TOKEN` (required, set) | **0.010** with the default areas (Germany, France, Spain), 600 s on 2026-10-19; all 59 reporting areas: one request round takes about 380 s, so no rate in 600 s (`data/reports/entsoe-20261019/`) | The platform publishes one value per period (15 to 60 min) per area and production type: asked at 15:21–15:23 UTC for the window 10:00–16:00 UTC, the 100 areas listed by entsoe-py returned 7,226 points (59 areas with data), 0.38 points/s even over only the 5 h 21 min up to the query and if every point were new |
| `fink` | [Fink — Rubin Observatory LSST and ZTF alerts](https://doc.lsst.fink-broker.org/services/livestream/) | kafka / push | `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` (required, not set) | 0 (no measurement possible without credentials) | No LSST alert night after 2026-07-14 (checked 2026-10-18) |
| `gfw` | [Global Fishing Watch events API](https://globalfishingwatch.org/our-apis/documentation) | http / poll | `GFW_API_TOKEN` (required, set) | **0**: dataset totals unchanged in all 22 hourly readings, 2026-10-18 03:24 – 2026-10-19 00:24 UTC (`data/gfw-growth-20261018/`) | Events are derived from AIS after processing and published days later (latest day with events 2026-10-14 when read on 2026-10-18) |
| `lasair` | [Lasair — LSST alerts passing a saved filter](https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html) | kafka / push | `LASAIR_KAFKA_TOPIC` (required, not set) | 0 (no filter topic yet) | Latest detection 2026-07-14 10:03 UTC, 0 objects in the last 30 days (checked 2026-10-18) |
| `ndbc` | [NOAA National Data Buoy Center latest observations](https://www.ndbc.noaa.gov/faq/rt_data_access.shtml) | http / poll | — | median **0.268**; 3 rounds of 960 s: 0.268, 0.569, 0.045 (`sampling-bytewax-20261019`, stopped early) | About 840 stations, one observation each per file rewrite; rewrites seen 9 min 59 s and 14 min 51 s apart |
| `npm` | [npm registry replication changes](https://github.com/npm/registry-follower-tutorial) | http / poll | — | median **0.790**; 24/24 rounds, 9 at ≥ 1/s, min 0.259, max 1.616 (`sampling-20261017`) | Polled every 5 s; the feed returns each changed package once per request, so several updates of one package between polls count once |

Three links cannot be checked by a script: `www.binance.com/en/terms` answers
HTTP 202 with a JavaScript challenge, and `www.mta.info/developers` and
`www.mta.info/developers/terms-and-conditions` answer HTTP 403 to scripts (their
text was retrieved with a browser-like fetch on 2026-10-13). Every other
documentation, terms and sign-up link in the descriptors, this README and the
documentation fixtures (108 of 111) answered HTTP 200 on 2026-10-13; the 13
links of the sources added on 2026-10-19 answered HTTP 200 that day.

## Sampling results

One sampling run decides each source: the all-source run of 2026-10-17/18
(24 hourly rounds, 60-s windows) unless a later run measured the source with
its key or with a changed consumer (`mbta_v3`, `firms`, `sensorcomm`, `tfl`:
run `d2`, after the minimum windows and the `mbta_v3` opening-snapshot fix).
Values come from `uv run stream-consumers verdict data/reports/<run> --planned 24`.
**passes (certain)** means the median of 24 rounds is at least 1 event/s
whatever the missing rounds show. The runs `d2`, `mastodon-world` and
`bytewax` were stopped on 2026-10-19 05:38 UTC before 24 rounds; their
sources are decided on the median of the rounds they completed
(**passes on N rounds (stopped early)**), and `ndbc`, the only one below
1 event/s, went to group E. Read at
<!-- results-read-at -->2026-10-19 05:39 UTC; the table lists every source of groups A–C (65); the
group E measurements are in [Sources Below 1 Event/s](#sources-below-1-events-measured--low-rate-catalog).

<!-- results-table -->
| id | Group | Run (`data/reports/sampling-…`) | Rounds | Rounds ≥ 1/s | Median (events/s) | Rounds span (UTC) | Result |
|---|---|---|---|---|---|---|---|
| `adsb_fi` | keyless | 20261017 | 24/24 | 21 | 3.350 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `adsb_lol` | keyless | 20261017 | 24/24 | 12 | 1.727 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `aisstream` | project document | aisstream-20261018 | 12/24 | 12 | 74.209 | 10-18 17:20–10-19 04:20 | passes (certain) |
| `albion` | keyless | 20261017 | 24/24 | 20 | 6.225 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `atlas` | keyless | 20261017 | 24/24 | 24 | 870.392 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `base_logs` | keyless | 20261017 | 24/24 | 24 | 298.250 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `bicing` | keyless | 20261017 | 24/24 | 24 | 3.681 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `binance` | project document | 20261017 | 24/24 | 24 | 42.585 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `bitfinex` | keyless | 20261017 | 24/24 | 16 | 1.338 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `bitso` | keyless | 20261017 | 24/24 | 24 | 26.812 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `blockchain` | keyless | bytewax-20261019 | 3/24 | 2 | 1.795 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `bluesky` | project document | 20261017 | 24/24 | 24 | 275.843 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `bsc_logs` | keyless | 20261017 | 24/24 | 24 | 372.913 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `bybit` | keyless | 20261017 | 24/24 | 24 | 5.499 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `citibike` | keyless | bytewax-20261019 | 3/24 | 2 | 23.368 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `coinbase` | keyless | 20261017 | 24/24 | 24 | 5.696 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `coinpaprika` | keyless | bytewax-20261019 | 3/24 | 3 | 6.662 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `crossref` | keyless | 20261017 | 24/24 | 23 | 7.983 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `ct` | keyless | 20261017 | 24/24 | 24 | 263.575 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `cta_bus` | free key | 20261017 | 24/24 | 23 | 17.379 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `cta_train` | free key | keyed-20261018 | 22/24 | 17 | 1.424 | 10-18 03:23–10-19 00:23 | passes (certain) |
| `deribit` | keyless | 20261017 | 24/24 | 24 | 3.935 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `dt_marine` | keyless | 20261017 | 24/24 | 24 | 31.041 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `dt_rail` | keyless | 20261017 | 24/24 | 24 | 48.622 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `dt_road` | keyless | 20261017 | 24/24 | 24 | 274.221 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `ecobici` | keyless | 20261017 | 24/24 | 15 | 1.465 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `entur` | keyless | 20261017 | 24/24 | 24 | 28.648 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `eth_logs` | keyless | 20261017 | 24/24 | 21 | 43.822 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `firms` | free key | d2-20261018 | 7/24 | 4 | 3.727 | 10-18 22:35–10-19 04:35 | passes on 7 rounds (stopped early) |
| `gdelt` | project document | 20261017 | 24/24 | 2 | 0.772 | 10-17 21:00–10-18 19:44 | kept below 1/s: the project document lists it |
| `gemini` | keyless | 20261017 | 24/24 | 24 | 286.996 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `gharchive` | keyless | 20261017 | 24/24 | 24 | 2.939 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `hsl` | keyless | 20261017 | 24/24 | 24 | 648.168 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `hyperliquid` | keyless | 20261017 | 24/24 | 24 | 4.390 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `kraken` | keyless | 20261017 | 24/24 | 23 | 2.968 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `mastodon` | free key | mastodon-vivaldi-20261018 | 13/24 | 13 | 2.383 | 10-18 15:37–10-19 03:37 | passes (certain) |
| `mbta_gtfsrt` | keyless | 20261017 | 24/24 | 24 | 24.620 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `mbta_v3` | free key | d2-20261018 | 7/24 | 7 | 45.787 | 10-18 22:35–10-19 04:35 | passes on 7 rounds (stopped early) |
| `mempool` | project document | 20261017 | 24/24 | 24 | 3.554 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `metar` | keyless | 20261017 | 24/24 | 23 | 1.386 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `mta_bustime` | free key | mta_bustime-20261018 | 20/24 | 20 | 50.567 | 10-18 04:56–10-18 23:56 | passes (certain) |
| `mta_gtfsrt` | keyless | 20261017 | 24/24 | 24 | 10.106 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `ndov` | keyless | 20261017 | 24/24 | 24 | 67.944 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `nta` | free key | nta-20261018 | 21/24 | 21 | 11.474 | 10-18 04:28–10-19 00:28 | passes (certain) |
| `ogn` | keyless | bytewax-20261019 | 3/24 | 3 | 115.615 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `okx` | keyless | 20261017 | 24/24 | 24 | 30.451 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `opensky` | project document | opensky-20261018 | 12/24 | 12 | 30.477 | 10-18 15:53–10-19 02:53 | passes (certain) |
| `osm` | keyless | 20261017 | 24/24 | 24 | 30.275 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `polygon_logs` | keyless | 20261017 | 24/24 | 24 | 353.452 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `polymarket` | keyless | 20261017 | 24/24 | 24 | 328.189 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `pskreporter` | keyless | 20261017 | 24/24 | 24 | 414.680 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `rbn` | keyless | 20261017 | 24/24 | 24 | 23.200 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `ris` | keyless | 20261017 | 24/24 | 24 | 2921.520 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `seedlink` | keyless | 20261017 | 24/24 | 23 | 1.873 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `sensorcomm` | keyless | d2-20261018 | 7/24 | 5 | 58.733 | 10-18 22:35–10-19 04:35 | passes on 7 rounds (stopped early) |
| `sharpe` | keyless | bytewax-20261019 | 3/24 | 3 | 40.396 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `solana` | keyless | 20261017 | 24/24 | 24 | 1391.347 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `tfl` | free key | d2-20261018 | 7/24 | 5 | 1.750 | 10-18 22:35–10-19 04:35 | passes on 7 rounds (stopped early) |
| `twitch` | keyless | 20261017 | 24/24 | 24 | 5.275 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `ukflood` | keyless | bytewax-20261019 | 3/24 | 3 | 4.865 | 10-19 02:45–10-19 04:45 | passes on 3 rounds (stopped early) |
| `usgs_water` | keyless | 20261017 | 24/24 | 24 | 2.402 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `velib` | keyless | 20261017 | 24/24 | 24 | 4.578 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `wikimedia` | project document | 20261017 | 24/24 | 24 | 29.034 | 10-17 21:00–10-18 19:44 | passes (certain) |
| `wmata` | free key | wmata-20261018 | 20/24 | 20 | 47.679 | 10-18 04:56–10-18 23:56 | passes (certain) |
| `xrpl` | keyless | 20261017 | 24/24 | 24 | 23.440 | 10-17 21:00–10-18 19:44 | passes (certain) |

## How rates are measured

| Delivery | Rate | Example |
|---|---|---|
| push | events received ÷ seconds consumed | WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP |
| poll | records new or changed between the first and last poll ÷ time between them | GBFS, GTFS-Realtime, ADS-B |
| poll, snapshot with a stated period | records in the snapshot ÷ that period | METAR (last hour), Sensor.Community (5 min), FIRMS (24 h) |
| file drop | records in the newest complete file ÷ the period it covers | GH Archive (1 h), GDELT (15 min), OpenStreetMap (1 min) |

`RunReport.rate_basis` records which one applies (`observed`, `published`, or
`unmeasured` when a run ended before a rate could be computed).

Rounds are spread over a day (24 rounds, one per hour) because many streams
follow the daily cycle of where they are: in the 2026-10-17/18 rounds `ecobici`
ranged from 3.63 events/s in the evening to 0.14 at night, and in 18 of the 56
measured sources at least one single round was on the other side of 1 event/s
from the source's 24-round median. A short test at one time of day therefore
cannot decide inclusion.

A source's verdict is fixed before the 24th round once the missing rounds can no
longer move its median across 1 event/s (`policy.verdict`): each missing round
could add 0 events/s, any higher rate or nothing, so the lowest possible median
fills them with 0 and the highest with an unbounded rate. With 24 rounds planned,
13 rounds at or above 1 event/s always pass and 13 below always fail; it can be
earlier (12 rounds of at least 2 events/s already give a lowest median of 1).
`sample --stop-when-settled` stops reading each source at that point, and the run
ends when every source is settled; `verdict` gives the median and verdict of each
source from recorded rounds.

## Use

```bash
uv sync                                    # Python 3.13, locked dependencies
uv run stream-consumers list               # descriptors as JSON lines
uv run stream-consumers consume hsl --seconds 60 --out data/hsl.jsonl
uv run stream-consumers check              # the 65 sources of groups A–C (D is empty) for 30 s; exit 1 if any fails
uv run stream-consumers check ndbc --seconds 960   # a group E source runs only when named
uv run stream-consumers sample --rounds 24 --interval 3600 --window 60 --reports data/reports/sampling
uv run stream-consumers sample --stop-when-settled --reports data/reports/sampling/segment-2 \
    --continue-from data/reports/sampling   # resume an interrupted run; stop each source once settled
uv run stream-consumers verdict data/reports/sampling --planned 24   # passes / fails / open per source
uv run stream-consumers profile --max-events 500 --seconds 120 --out data/profile
```

Personal fields declared by each source (`personal_fields`) and any e-mail
address are masked in everything written, unless `consume --raw` is given.
Captured data and reports go to `data/`, which git ignores.

`profile` writes `profiles-<time>.json` to `--reports`: per source the event
size in compact UTF-8 JSON (mean and 95th percentile), the share of events equal
to an earlier one, the natural key (smallest set of at most three fields unique
across the sample, preferring identifiers and times) and, per flattened field,
presence, distinct values, kinds, numeric range, a masked example and a class.
Classes are decided in this order (`FieldClass`, `policy.classify_field`):
`datetime` (ISO 8601 text, or epoch s/ms/µs/ns or `YYYYMMDD[hhmmss]` within
400 days of the run), `geographic` (a latitude or longitude whose partner field
is present, within range), `number` (numbers, or numeric text without a leading
zero, flagged `numeric_text`), `identifier` (text without spaces with more
distinct values than a category may have), `free-text` (30+ characters on
average, mostly with spaces, at least half distinct), `label` (other text with
that many distinct values), `category` (text or Booleans with at most
max(20, 5 % of the events) distinct values), `nested` and `empty`.

## API keys and configuration

Credentials and settings are read from the process environment, then from a
git-ignored `.env` file (`--env-file` changes the path). Values are never
printed, logged or written to a report.

```bash
cp .env.example .env                          # every variable the sources read and every held key, with how to get each
uv run stream-consumers keys                  # which are set, missing (required) or not set (optional);
                                              # exits 1 and lists as `unknown` any .env variable neither read nor held
uv run stream-consumers check cta_train       # one source for 30 s once its key is in .env
uv run stream-consumers keys --template       # regenerates .env.example (a unit test keeps them identical)
```

A source whose required credentials are missing reports `key-pending` in `check`,
`sample` and `profile`; it never fails a run.

`.env` holds only the variables of `.env.example`, and every key the project
has is kept in it. Keys that no source reads are **held keys**, declared in
`stream_consumers/adapters/outbound/held_keys.py` (`HELD_KEYS`, exported by the
catalog next to `FACTORIES`) and listed by `keys` as `held`: secondary keys
(NTA, WMATA, TfL), WMATA and TfL products the sources do not read, the
Mastodon applications' client id and secret and the tokens of other instances
(mastodon.world, mastodon.social), the Coinbase CDP key, the Bitso and Binance
key pairs (reading permission only; the Binance probe also fails if the key
can trade or withdraw), and the Lasair REST API token (the `lasair` source reads only the Kafka topic of a saved filter). A new key is added to `HELD_KEYS` (or to a source's
`Credential`) and to `tests/live/test_keys_live.py`, which fails if a key has
no probe. That test sends, for each key, one read-only request with the stored
value (must be accepted), one with its last four characters changed (must be
refused) and one without it (refused where the provider requires a key,
accepted where the key is optional):

```bash
uv run pytest tests/live/test_keys_live.py -m live    # KEYS_ENV_FILE=path/.env to test another file
```

| Variable(s) | Source | Needed | How to get it (sign-up page) | Where it goes | Documented limit |
|---|---|---|---|---|---|
| `AISSTREAM_API_KEY` | `aisstream` | required | Sign in with GitHub on the [Account page](https://aisstream.io/account) and create a key (shown once) | `APIKey` in the first WebSocket message | 3 connections per account and per IP; frames dropped for slow readers |
| `CTA_BUS_KEY` | `cta_bus` | required | [Bus Tracker account](https://www.ctabustracker.com/bustime/login.jsp) → My Account → Developer API; e-mailed after approval | query `key` | 100,000 transactions/day |
| `CTA_TRAIN_KEY` | `cta_train` | required | [Train Tracker application form](https://www.transitchicago.com/developers/traintrackerapply/); CTA reviews it | query `key` | 50,000 requests/day |
| `ENTSOE_TOKEN` | `entsoe` | required | [Register](https://transparency.entsoe.eu/), then e-mail transparency@entsoe.eu for RESTful API access ("within 3 working days") | query `securityToken` | 400 requests/min |
| `FINK_KAFKA_SERVERS`, `FINK_GROUP_ID` | `fink` (group E) | required | [Fink subscription form](https://forms.gle/2td4jysT4e9pkf889); the Fink team e-mails the Kafka server address and your `group.id` | Kafka bootstrap servers and `group.id` | none documented |
| `GFW_API_TOKEN` | `gfw` (group E) | required | [Global Fishing Watch account](https://globalfishingwatch.org/our-apis/), then request an API token (self-service; up to 5 tokens, they do not expire); non-commercial use only | `Authorization: Bearer` | 50,000 requests/day, 1,500,000/month |
| `LASAIR_KAFKA_TOPIC` | `lasair` (group E) | required | [Lasair account](https://lasair.lsst.ac.uk/), then build and save a filter with Kafka streaming enabled; its topic is `lasair_` + your user ID + the sanitised filter name | Kafka topic (the server needs no password) | none documented for Kafka |
| `MASTODON_ACCESS_TOKEN` | `mastodon` | required | [Account on the instance](https://social.vivaldi.net/auth/sign_up) (the default `MASTODON_INSTANCE`; a token works only on the instance that issued it), then a user token with scope `read:statuses` | `Authorization: Bearer` | 300 REST calls per 5 min; streaming not stated |
| `MTA_BUSTIME_KEY` | `mta_bustime` | required | [Web form](https://register.developer.obanyc.com/); e-mailed "within half an hour" | query `key` | no number; all-vehicle requests not under 30 s apart |
| `NTA_API_KEY` | `nta` | required | [Developer portal](https://developer.nationaltransport.ie/signup), subscribe to "GTFS Realtime" | header `x-api-key` | one call every 60 s |
| `WMATA_API_KEY` | `wmata` | required | [Developer account](https://developer.wmata.com/signup), subscribe to a Transit Data tier | header `api_key` | not published on an official page |
| `MBTA_API_KEY` | `mbta_v3` | optional | [V3 API portal](https://api-v3.mbta.com/register), one key per application ("might take a day") | header `x-api-key`; enables streaming | 1,000 requests/min (20 without a key) |
| `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` | `opensky` | optional | [OpenSky account](https://opensky-network.org/my-opensky/account) → create an API client | OAuth 2 client credentials → `Authorization: Bearer` | 4,000 credits/day (400 anonymous) |
| `TFL_APP_KEY` | `tfl` | optional | [API portal](https://api-portal.tfl.gov.uk/signup), subscribe to the product "500 Requests per min" | query `app_key` | 500 requests per minute (subscription page, 2026-10-18) |

Settings with defaults: `AISSTREAM_BOUNDING_BOXES`, `CROSSREF_MAILTO`,
`ENTSOE_AREAS`, `FINK_TOPICS`, `GFW_DATASET`, `GFW_LOOKBACK_DAYS`, `GFW_PAGES`,
`LASAIR_GROUP_ID`, `LASAIR_KAFKA_SERVER`, `MASTODON_INSTANCE`,
`OPENSKY_POLL_SECONDS` (each described, with its default, in `.env.example`). NASA FIRMS needs no key:
it reads the public 24 h files.

Terms worth reading before use: OpenSky requires a written agreement for
"operational" REST API use, including automated systems, even non-profit ones;
Global Fishing Watch data is CC BY-NC 4.0 and tokens must not be shared;
aisstream.io publishes no terms of use (only a privacy statement);
Mastodon statuses are personal data and are masked in stored samples.

## Architecture

Hexagonal (ports and adapters) with split inbound and outbound ports:

```text
src/stream_consumers/
  domain/        models, pure rules (rates, change detection, back-off, masking, field profiles), errors
  ports/
    inbound.py   use cases: ListSources, ConsumeStream, CheckSources, SampleSources, JudgeSampling,
                 ProfileSources, DescribeConfiguration
    outbound.py  Clock, SecretProvider, HttpClient, RequestAuth, Decoder, EventSource, SourceFactory,
                 HeldKeyCatalog, SourceRegistry, EventSink, EventSinkFactory, SamplingHistory, ReportSink
  application/   one service per inbound port; depends on ports and domain only
  adapters/
    inbound/cli.py            the composition root: the only module that names concrete classes
    outbound/transports/      EventSourcePort → BaseEventSource → DecodingEventSource → Push / Poll / FileDrop,
                              and MergedEventSource; one module per transport
    outbound/decoders.py      DecoderPort → BaseDecoder → Json / Line / Csv / GtfsRealtime / AvroSchemaInKey
    outbound/auth.py          RequestAuthPort → OAuthClientCredentials
    outbound/sources/         one module per source (descriptor + decoder + factory), families in _families.py
    outbound/held_keys.py     HeldKeyCatalogPort → StaticHeldKeyCatalog (keys kept in .env that no source reads)
    outbound/history.py       SamplingHistoryPort → JsonSamplingHistory (reads round-*.json for `verdict`)
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

## Tests

| Tier | What | Command | Coverage |
|---|---|---|---|
| unit | domain, decoders against real captured messages (`tests/fixtures/raw`), factories, sinks, CLI in-process, architecture rules | `uv run pytest --cov` (with component) | 100 % gated |
| component | services with scripted sources; every transport against a local server, Kafka against a real broker; sources with their own fetching logic against captured answers | (same run) | (same gate) |
| e2e | the CLI as a subprocess against local servers for every transport (Kafka included), working and failing | see below | 100 % gated on the CLI, services, ports and infrastructure adapters (`.coveragerc.e2e`) |
| live | every source against its real provider, 60 s; every key in `.env` accepted, a damaged copy refused (`test_keys_live.py`) | see below | reported only (`.coveragerc.live`) |

```bash
uv run pytest --cov                                   # unit + component, fails under 100 %
uv run coverage erase --rcfile=.coveragerc.e2e
uv run pytest tests/e2e
uv run coverage combine --rcfile=.coveragerc.e2e && uv run coverage report --rcfile=.coveragerc.e2e
uv run coverage run --rcfile=.coveragerc.live -m pytest tests/live -m live   # needs Internet; never in CI
uv run ruff check src tests && uv run ruff format --check src tests
```

The component and e2e tiers start a single-node Kafka broker with Docker
(`apache/kafka:3.9.1`, published on 127.0.0.1 only); Docker is required.

Fixtures are real messages captured on 2026-10-13 (`velib` and `cta_bus` on
2026-10-17; `cta_train`, `nta`, `mta_bustime`, `wmata`, `mastodon`, `aisstream`
and the MBTA stream on 2026-10-18; `blockchain`, `citibike`, `coinpaprika`,
`ogn`, `sharpe`, `ukflood`, `ndbc`, `entsoe` and `gfw` on 2026-10-19), trimmed,
with personal values replaced by `<masked>`; a test checks that no fixture leaks
a personal value or an e-mail address. Fixtures of keyed sources (`aisstream`,
`cta_bus`, `cta_train`, `entsoe`, `gfw`, `mastodon`, `mbta_v3_stream`,
`mta_bustime`, `nta`, `wmata`) were captured with the key and stored without it;
a test checks that they say when they were captured and that the key is not
stored. `lasair`, whose filter topic is not set, still uses the provider's
official documentation example, marked with `origin`, `documentation_url` and the
`corrections` applied (a trailing comma removed), until a topic exists. `fink`
has no fixture: its Avro decoder is tested with messages written to the local
Kafka broker.

## Known behaviour

- Digitraffic road sensors (`dt_road`) publish in bursts; a short window can see
  none.
- Albion Online market orders (`albion`) arrive in bursts: on 2026-10-19 the
  subject `marketorders.deduped` was silent for 50 s and then carried 350
  orders in 30 s, so 60-s windows at 03:53 and 04:10 UTC read 0 events and
  one at 04:24 UTC read 4.1 events/s (1 of the 24 rounds of 2026-10-17/18 read
  0).
- PublicNode's Ethereum endpoint (`eth_logs`) can acknowledge the unfiltered
  `eth_subscribe("logs")` and then send no logs: on 2026-10-19 it sent none
  in 60-s windows at 03:53, 04:10, 04:24 and 05:45 UTC nor in a 180-s window at
  06:01 UTC, while `eth_getLogs` returned
  666 logs for the latest block, a subscription filtered by one contract
  address received 252 logs in 40 s, and
  the BSC, Base and Polygon endpoints delivered (3 of the 24 rounds of
  2026-10-17/18 read 0; median 43.8 events/s). It recovered without any change
  here: on 2026-10-19 14:44 UTC the unfiltered subscription delivered 58.5 logs/s
  over 40 s and `check eth_logs` read 96.3 events/s.
- With `MBTA_API_KEY`, `mbta_v3` streams: the first `reset` message lists
  every vehicle (245 on 2026-10-18 04:54 UTC). It is the starting state, not a
  change, so it yields no events, like the first poll of a polled feed (until
  2026-10-18 it was counted: 37.3 vs 32.3 events/s live-only that minute).
- `mta_bustime`'s GTFS-Realtime feed answered the same with no key or a wrong
  key on 2026-10-18 (its SIRI API refuses them: 401 / 403); the source still
  sends the key, as the provider's documentation requires.
- The default `MASTODON_INSTANCE` is social.vivaldi.net (since 2026-10-19;
  measured with its token since 2026-10-18). mastodon.social reports
  `configuration.timelines_access.live_feeds` local and remote `disabled`
  (`GET /api/v2/instance`, 2026-10-18), so its public stream carries only
  `delete` events; social.vivaldi.net and mastodon.world report both `public`.
  A token works only on the instance that issued it (the social.vivaldi.net
  token got HTTP 401 on mastodon.world), so changing `MASTODON_INSTANCE` needs a
  token from that instance. mastodon.world was measured as a second option
  (median 1.833 events/s over its first 5 rounds, 2026-10-18/19).
- TfL answers carry `Cache-Control: ... s-maxage=60` and a shared cache serves
  them with or without a key, so a poll 30 s after a fresh answer can return
  the same copy (`X-Cache: HIT`); a 60-s round then measures 0 events/s
  (5 of 24 rounds on 2026-10-17/18).
- Sources declare a minimum measuring window (`SourceDescriptor.min_window_s`);
  `check`, `sample` and `profile` extend a shorter `--seconds`/`--window` to it.
  150 s for `tfl` (the 60-s cache) and `nta` (one call per 60 s, so two polls
  need more than 60 s). 600 s for `firms` and `sensorcomm`: their whole files
  must arrive before the first event, and on 2026-10-19 the servers sent them
  at 0.05–0.09 MB/s (first event after 462 s and 297 s for `firms`, 155 s for
  `sensorcomm`, in 600-s checks), while the 2026-10-17/18 rounds needed at most
  73 s and 50 s. Until 2026-10-19 the HTTP client also cut every request at
  120 s in total, so a slow but steady download (Sensor.Community's 8.5 MB in
  175 s) failed and the round counted 0 events/s (both sources: 6 consecutive
  rounds on 2026-10-18 00:01–04:45 UTC, and 3 rounds of the `d2` run on
  2026-10-19 01:35–02:35 UTC). The 120 s now bound connecting and each wait for
  bytes; a whole request is capped at 900 s. `citibike` is regenerated every 60 s (`ttl`
  60) behind a CloudFront cache: a 60-s check on 2026-10-19 02:13 UTC polled
  only copies of one version and measured 0 events/s, so its window is 150 s.
  `coinpaprika` and `sharpe` refresh their whole
  snapshot together about every 5 min (CoinPaprika: "up to 10 min"; Sharpe's
  freshness SLA is 600 s), so their windows are 630 s; `ukflood` is polled every
  15 min, so its window is 960 s.
- The USGS legacy Water Services announce their retirement on 2027-02-22.
- Branch protection is not available for private repositories on the GitHub Free
  plan; work reaches `main` through pull requests by convention.
