# stream-consumers

Consumers and subscribers for the public real-time data streams evaluated for the
final project of COM-22102 *Bases de Datos No Relacionales* (ITAM, Otoño 2026).

**Private, instructor-only repository.** Students build their own ingestion
consumer as part of the project; do not share this repository with them.

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
- **Candidates** (group D, 8 sources) need a free key; until their own sampling
  with the key finishes, their rate is not measured. They are built and tested against the
  providers' official documentation examples so that adding the key to `.env` is
  enough to run them. A candidate is accepted (group C, or B for aisstream.io)
  only after its own sampling gives a median of at least 1 event/s with the key,
  and is removed otherwise. Until then it reports `key-pending` and counts for
  nothing.
- Measured below 1 event/s and therefore excluded: Nostr, Stellar,
  ENA, PyPI, Hacker News, MLB; not measurable as configured: BitMEX, APRS-IS,
  Kystverket AIS, zKillboard.

The rate list will be re-checked with this repository's own `sample` command
(24 hourly rounds); a source whose median falls below the threshold is removed.

- **Lasair and Fink were removed on 2026-10-18**: both relay alerts of the
  Rubin Observatory LSST, and neither had published a single alert since
  2026-07-14 (Lasair's latest detection 2026-07-14 10:03 UTC, 0 objects in the
  last 30 days; Fink's last alert night 2026-07-14), so both would measure
  0 events/s. The Kafka transport and the Avro decoder stay, tested against a
  local broker, so either can be re-added if alerts resume.
- **Removed on 2026-10-18 after the 24-hour sampling of 2026-10-17/18**
  (24 hourly rounds, 60-s windows): Bitstamp (`bitstamp`, median 0.515
  events/s), npm (`npm`, 0.790) and Digitraffic train timetables
  (`dt_rail_trains`, 0.865), all below 1 event/s. GDELT (0.772) stays, as
  decided above.
- **Global Fishing Watch (`gfw`) was removed on 2026-10-18**: its events API
  publishes events days after they happen (the latest day with events was
  2026-10-14 when read on 2026-10-18), so a poll sees no new events within a
  round. The totals of all four event datasets over a fixed date range did not
  grow at all in 18 hourly readings (2026-10-18 03:24–21:24 UTC), so the median
  arrival rate is 0 events/s.
- **Added on 2026-10-19 from the Bytewax "Awesome Public Real-Time Datasets"
  list** (all 69 free entries screened): `blockchain`, `citibike`, `coinpaprika`,
  `ndbc`, `ogn`, `sharpe` and `ukflood`, each keyless and measured at ≥ 1
  event/s in one screening window. They stay only if their own sampling
  (`sample --stop-when-settled`) gives a median of at least 1 event/s. Not
  added from that list: EPA AirNow (its hourly file lists 4,415 sites but only
  1,980 reported in the hour 2026-10-18 22:00 UTC, 0.55 events/s), Yahoo
  Finance (its terms forbid automated collection) and GitHub's REST events
  (the same events as `gharchive`).
- **Vélib' Paris was re-added on 2026-10-17**: it had been excluded at 0.983
  events/s on its earliest (night-time) rounds, but its median over 15 earlier
  cross-check rounds was 4.4 events/s; the 24-hour sampling decides.

## Sources (67)

Groups: **keyless** (50), **project document** (6, the sources the project
document lists), **free key** (3, key optional), **candidate** (8, key
required, rate not yet measured).

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
| `ndbc` | [NOAA National Data Buoy Center — latest observation of every buoy and coastal station](https://www.ndbc.noaa.gov/faq/rt_data_access.shtml) | NOAA National Data Buoy Center (NDBC) | keyless | http | poll |
| `ukflood` | [Environment Agency (England) — real-time flood-monitoring readings: river level, flow, rainfall, tide](https://environment.data.gov.uk/flood-monitoring/doc/reference) | Environment Agency (England) | keyless | http | poll |
| `binance` | [Binance spot trades + 24 h tickers](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md) | Binance | project document | websocket | push |
| `mempool` | [mempool.space — Bitcoin transactions entering the mempool](https://mempool.space/docs/api/websocket) | The Mempool Open Source Project (mempool.space) | project document | websocket | push |
| `bluesky` | [Bluesky Jetstream — firehose of AT Protocol commits (posts, likes, follows, reposts)](https://github.com/bluesky-social/jetstream) | Bluesky Social PBC | project document | websocket | push |
| `gdelt` | [GDELT 2.0 Event Database — 15-minute event exports](https://www.gdeltproject.org/data.html) | The GDELT Project | project document | http | file-drop |
| `wikimedia` | [Wikimedia EventStreams — recent changes on all Wikimedia wikis](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service) | Wikimedia Foundation | project document | sse | push |
| `opensky` | [OpenSky Network state vectors — aircraft over Mexico](https://openskynetwork.github.io/opensky-api/rest.html) | OpenSky Network | project document | http | poll |
| `mbta_v3` | [MBTA V3 API vehicles (Boston subway, bus, commuter rail, ferry)](https://www.mbta.com/developers/v3-api) | Massachusetts Bay Transportation Authority (MBTA) | free key (optional) | http | poll |
| `tfl` | [Transport for London Unified API — Tube arrival predictions](https://api-portal.tfl.gov.uk/) | Transport for London (TfL) | free key (optional) | http | poll |
| `firms` | [NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS), global 24 h files](https://firms.modaps.eosdis.nasa.gov/active_fire/) | NASA Earth Science Data Systems (LANCE FIRMS) | free key (optional) | http | poll |
| `mastodon` | [Mastodon federated public timeline (statuses, edits, deletions)](https://docs.joinmastodon.org/methods/streaming/) | Mastodon (default instance mastodon.social, Mastodon gGmbH) | candidate (key required) | sse | push |
| `aisstream` | [aisstream.io — global AIS ship positions and static data](https://aisstream.io/documentation) | aisstream.io | candidate (key required) | websocket | push |
| `cta_bus` | [CTA Bus Tracker vehicles — every Chicago bus](https://www.transitchicago.com/developers/bustracker/) | Chicago Transit Authority (CTA) | candidate (key required) | http | poll |
| `cta_train` | [CTA Train Tracker locations — every Chicago 'L' train](https://www.transitchicago.com/developers/traintracker/) | Chicago Transit Authority (CTA) | candidate (key required) | http | poll |
| `mta_bustime` | [MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus](https://bustime.mta.info/developers/gtfs-realtime/) | Metropolitan Transportation Authority (MTA) | candidate (key required) | http | poll |
| `nta` | [NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland](https://developer.nationaltransport.ie/) | National Transport Authority (NTA), Ireland | candidate (key required) | http | poll |
| `wmata` | [WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail](https://developer.wmata.com/) | Washington Metropolitan Area Transit Authority (WMATA) | candidate (key required) | http | poll |
| `entsoe` | [ENTSO-E Transparency Platform — actual electricity generation per production type](https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API) | European Network of Transmission System Operators for Electricity (ENTSO-E) | candidate (key required) | http | poll |

Three links cannot be checked by a script: `www.binance.com/en/terms` answers
HTTP 202 with a JavaScript challenge, and `www.mta.info/developers` and
`www.mta.info/developers/terms-and-conditions` answer HTTP 403 to scripts (their
text was retrieved with a browser-like fetch on 2026-10-13). Every other
documentation, terms and sign-up link in the descriptors, this README and the
documentation fixtures (108 of 111) answered HTTP 200 on 2026-10-13; the 13
links of the sources added on 2026-10-19 answered HTTP 200 that day.

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
uv run stream-consumers check              # every source for 30 s; exit 1 if any fails
uv run stream-consumers sample --rounds 24 --interval 3600 --window 60 --reports data/reports/sampling
uv run stream-consumers sample --stop-when-settled --reports data/reports/sampling/segment-2 \
    --continue-from data/reports/sampling   # resume an interrupted run; stop each source once settled
uv run stream-consumers verdict data/reports/sampling --planned 24   # passes / fails / open per source
uv run stream-consumers profile --max-events 500 --seconds 120 --out data/profile
```

Personal fields declared by each source (`personal_fields`) and any e-mail
address are masked in everything written, unless `consume --raw` is given.
Captured data and reports go to `data/`, which git ignores.

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
can trade or withdraw), and the tokens of the removed `lasair` and `gfw`. A new key is added to `HELD_KEYS` (or to a source's
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
| `MASTODON_ACCESS_TOKEN` | `mastodon` | required | [Account on the instance](https://mastodon.social/auth/sign_up), then a user token with scope `read:statuses` | `Authorization: Bearer` | 300 REST calls per 5 min; streaming not stated |
| `MTA_BUSTIME_KEY` | `mta_bustime` | required | [Web form](https://register.developer.obanyc.com/); e-mailed "within half an hour" | query `key` | no number; all-vehicle requests not under 30 s apart |
| `NTA_API_KEY` | `nta` | required | [Developer portal](https://developer.nationaltransport.ie/signup), subscribe to "GTFS Realtime" | header `x-api-key` | one call every 60 s |
| `WMATA_API_KEY` | `wmata` | required | [Developer account](https://developer.wmata.com/signup), subscribe to a Transit Data tier | header `api_key` | not published on an official page |
| `MBTA_API_KEY` | `mbta_v3` | optional | [V3 API portal](https://api-v3.mbta.com/register), one key per application ("might take a day") | header `x-api-key`; enables streaming | 1,000 requests/min (20 without a key) |
| `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET` | `opensky` | optional | [OpenSky account](https://opensky-network.org/my-opensky/account) → create an API client | OAuth 2 client credentials → `Authorization: Bearer` | 4,000 credits/day (400 anonymous) |
| `TFL_APP_KEY` | `tfl` | optional | [API portal](https://api-portal.tfl.gov.uk/signup), subscribe to the product "500 Requests per min" | query `app_key` | 500 requests per minute (subscription page, 2026-10-18) |

Settings with defaults: `AISSTREAM_BOUNDING_BOXES`, `CROSSREF_MAILTO`,
`ENTSOE_AREAS`, `MASTODON_INSTANCE`,
`OPENSKY_POLL_SECONDS` (described in `.env.example`). NASA FIRMS needs no key:
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
and the MBTA stream on 2026-10-18), trimmed, with personal values replaced by `<masked>`; a test checks
that no fixture leaks a personal value or an e-mail address. Candidates without a
key yet have the providers' official documentation examples as fixtures, marked
with `origin`, `documentation_url` and the `corrections` applied (PDF page footers,
a typographic quote, a trailing comma); each is replaced by captured messages once
its key works (done for `cta_bus`, `cta_train`, `nta`, `mta_bustime`, `wmata`,
`mastodon`, `aisstream` and `mbta_v3_stream`, captured with a key and
stored without it; a test checks that these say when they were captured and that
the key is not stored).

## Known behaviour

- Digitraffic road sensors (`dt_road`) publish in bursts; a short window can see
  none.
- With `MBTA_API_KEY`, `mbta_v3` streams: the first `reset` message lists
  every vehicle (245 on 2026-10-18 04:54 UTC). It is the starting state, not a
  change, so it yields no events, like the first poll of a polled feed (until
  2026-10-18 it was counted: 37.3 vs 32.3 events/s live-only that minute).
- `mta_bustime`'s GTFS-Realtime feed answered the same with no key or a wrong
  key on 2026-10-18 (its SIRI API refuses them: 401 / 403); the source still
  sends the key, as the provider's documentation requires.
- mastodon.social (the default `MASTODON_INSTANCE`) reports
  `configuration.timelines_access.live_feeds` local and remote `disabled`
  (`GET /api/v2/instance`, 2026-10-18), so its public stream carries only
  `delete` events. Use a token from an instance whose live feeds are `public`
  (social.vivaldi.net, used since 2026-10-18) and set `MASTODON_INSTANCE` to it.
- TfL answers carry `Cache-Control: ... s-maxage=60` and a shared cache serves
  them with or without a key, so a poll 30 s after a fresh answer can return
  the same copy (`X-Cache: HIT`); a 60-s round then measures 0 events/s
  (5 of 24 rounds on 2026-10-17/18).
- Sources declare a minimum measuring window (`SourceDescriptor.min_window_s`);
  `check`, `sample` and `profile` extend a shorter `--seconds`/`--window` to it.
  150 s for `tfl` (the 60-s cache), `nta` (one call per 60 s, so two polls need
  more than 60 s), `firms` and `sensorcomm` (whole files must arrive before
  the first event: up to 73 s and 50 s in the rounds of 2026-10-17/18; both
  delivered nothing in 6 consecutive rounds, 2026-10-18 00:01–04:45 UTC, while
  other sources were unaffected). `citibike` is regenerated every 60 s (`ttl`
  60) behind a CloudFront cache: a 60-s check on 2026-10-19 02:13 UTC polled
  only copies of one version and measured 0 events/s, so its window is 150 s.
  `coinpaprika` and `sharpe` refresh their whole
  snapshot together about every 5 min (CoinPaprika: "up to 10 min"; Sharpe's
  freshness SLA is 600 s), so their windows are 630 s; `ndbc` rewrites its
  file at irregular times (consecutive rewrites seen 14 min 51 s and 9 min 59 s
  apart on 2026-10-19) and `ukflood` is polled every 15 min, so theirs are 960 s.
- The USGS legacy Water Services announce their retirement on 2027-02-22.
- Branch protection is not available for private repositories on the GitHub Free
  plan; work reaches `main` through pull requests by convention.
