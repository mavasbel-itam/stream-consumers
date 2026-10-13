# stream-consumers

Consumers and subscribers for the public real-time data streams evaluated for the
final project of COM-22102 *Bases de Datos No Relacionales* (ITAM, Otoño 2026).

**Private, instructor-only repository.** Students build their own ingestion
consumer as part of the project; do not share this repository with them.

## Inclusion rule

A source is included when its **median measured rate is at least 1 event per
second** over the sampling rounds (`stream_consumers.domain.policy.MINIMUM_RATE`,
`meets_minimum_rate`). The exceptions and pending cases:

- **GDELT is kept** although its measured median was 0.977 events/s, because the
  project document lists it (decision of 2026-10-13).
- Free-key providers whose keyless route was measured at ≥ 1 event/s are included
  (MBTA V3, TfL, NASA FIRMS); the key is optional for MBTA V3 and TfL, and FIRMS
  uses its keyless public files.
- **Candidates** (group D, 11 sources) need a free key that is not configured yet,
  so their rate has never been measured. They are built and tested against the
  providers' official documentation examples so that adding the key to `.env` is
  enough to run them. A candidate is accepted (group C, or B for aisstream.io)
  only after its own sampling gives a median of at least 1 event/s with the key,
  and is removed otherwise. Until then it reports `key-pending` and counts for
  nothing.
- Measured below 1 event/s and therefore excluded: Vélib' Paris, Nostr, Stellar,
  ENA, PyPI, Hacker News, MLB; not measurable as configured: BitMEX, APRS-IS,
  Kystverket AIS, zKillboard.

The rate list will be re-checked with this repository's own `sample` command
(24 hourly rounds); a source whose median falls below the threshold is removed.

## Sources (65)

Groups: **keyless** (45), **project document** (6, the sources the project
document lists), **free key** (3, key optional), **candidate** (11, key
required, rate not yet measured).

| id | Source | Provider | Group | Transport | Delivery |
|---|---|---|---|---|---|
| `base_logs` | [Base (L2) contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `bitfinex` | [Bitfinex trades + ticker (public v2)](https://docs.bitfinex.com/docs/ws-public) | Bitfinex | keyless | websocket | push |
| `bitso` | [Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)](https://docs.bitso.com/bitso-api/docs) | Bitso (Mexico) | keyless | websocket | push |
| `bitstamp` | [Bitstamp live trades](https://www.bitstamp.net/websocket/v2/) | Bitstamp | keyless | websocket | push |
| `bsc_logs` | [BNB Smart Chain contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `bybit` | [Bybit spot tickers](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) | Bybit | keyless | websocket | push |
| `coinbase` | [Coinbase Exchange ticker](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) | Coinbase | keyless | websocket | push |
| `deribit` | [Deribit perpetual futures ticker](https://docs.deribit.com/) | Deribit | keyless | websocket | push |
| `eth_logs` | [Ethereum mainnet contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `gemini` | [Gemini market data v1 (order-book changes + trades)](https://developer.gemini.com/websocket/streams.md) | Gemini Trust Company | keyless | websocket | push |
| `hyperliquid` | [Hyperliquid trades](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) | Hyperliquid | keyless | websocket | push |
| `kraken` | [Kraken trades + ticker (v2)](https://docs.kraken.com/api/docs/websocket-v2/trade) | Kraken (Payward) | keyless | websocket | push |
| `okx` | [OKX public tickers](https://www.okx.com/docs-v5/en/) | OKX | keyless | websocket | push |
| `polygon_logs` | [Polygon PoS contract event logs (PublicNode RPC)](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) | Allnodes (PublicNode RPC) | keyless | websocket | push |
| `polymarket` | [Polymarket CLOB market channel (prediction-market prices)](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) | Polymarket | keyless | websocket | push |
| `solana` | [Solana program logs (public mainnet RPC)](https://solana.com/docs/rpc/websocket/logssubscribe) | Solana Foundation (public mainnet-beta RPC) | keyless | websocket | push |
| `xrpl` | [XRP Ledger transactions](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe) | XRP Ledger Foundation (public cluster xrplcluster.com) | keyless | websocket | push |
| `albion` | [Albion Online Data Project market orders](https://www.albion-online-data.com/) | Albion Online Data Project (community) | keyless | nats | push |
| `twitch` | [Twitch chat (anonymous read-only IRC)](https://dev.twitch.tv/docs/chat/irc/) | Twitch Interactive | keyless | websocket | push |
| `atlas` | [RIPE Atlas measurement results stream (ping)](https://atlas.ripe.net/docs/apis/streaming-api) | RIPE NCC | keyless | websocket | push |
| `ct` | [Certificate Transparency logs (RFC 6962), read directly](https://www.rfc-editor.org/rfc/rfc6962) | Certificate Transparency log operators (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt, TrustAsia) | keyless | http | poll |
| `gharchive` | [GH Archive — all public GitHub events (hourly files)](https://www.gharchive.org/) | GH Archive (Ilya Grigorik) | keyless | http | file-drop |
| `npm` | [npm registry replication changes](https://github.com/npm/registry-follower-tutorial) | npm, Inc. (GitHub) | keyless | http | poll |
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
| `dt_marine` | [Digitraffic Finland marine AIS vessel locations](https://www.digitraffic.fi/en/marine-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `dt_rail` | [Digitraffic Finland train GPS locations](https://www.digitraffic.fi/en/railway-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `dt_rail_trains` | [Digitraffic Finland train timetables/actuals](https://www.digitraffic.fi/en/railway-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `dt_road` | [Digitraffic Finland road traffic (TMS) and road-weather sensors](https://www.digitraffic.fi/en/road-traffic/) | Fintraffic (Digitraffic) | keyless | mqtt | push |
| `ecobici` | [EcoBici CDMX bike-share station status (GBFS)](https://ecobici.cdmx.gob.mx/datos-abiertos/) | Gobierno de la Ciudad de México (EcoBici, operated by Lyft) | keyless | http | poll |
| `entur` | [Entur Norway real-time vehicle positions](https://developer.entur.org/pages-real-time-intro) | Entur AS (Norway) | keyless | http | poll |
| `hsl` | [HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md) | Helsinki Regional Transport Authority (HSL) | keyless | mqtt | push |
| `mbta_gtfsrt` | [MBTA Boston GTFS-Realtime VehiclePositions](https://www.mbta.com/developers/gtfs-realtime) | Massachusetts Bay Transportation Authority (MBTA) | keyless | http | poll |
| `mta_gtfsrt` | [MTA New York City Subway GTFS-Realtime (A/C/E feed)](https://api.mta.info/) | Metropolitan Transportation Authority (MTA) | keyless | http | poll |
| `ndov` | [NDOV Loket Netherlands public transport KV6 (all operators)](https://ndovloket.nl/) | NDOV Loket (Netherlands) | keyless | zeromq | push |
| `metar` | [NOAA aviationweather.gov METAR observations (global airports)](https://aviationweather.gov/data/api/) | NOAA National Weather Service — Aviation Weather Center | keyless | http | poll |
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
| `fink` | [Fink — Rubin Observatory LSST and ZTF alert livestream](https://doc.lsst.fink-broker.org/services/livestream/) | Fink broker (CNRS/IN2P3 and partners) | candidate (key required) | kafka | push |
| `lasair` | [Lasair — Rubin Observatory LSST alerts that pass your saved filter](https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html) | Lasair (Universities of Edinburgh and Belfast) | candidate (key required) | kafka | push |
| `aisstream` | [aisstream.io — global AIS ship positions and static data](https://aisstream.io/documentation) | aisstream.io | candidate (key required) | websocket | push |
| `cta_bus` | [CTA Bus Tracker vehicles — every Chicago bus](https://www.transitchicago.com/developers/bustracker/) | Chicago Transit Authority (CTA) | candidate (key required) | http | poll |
| `cta_train` | [CTA Train Tracker locations — every Chicago 'L' train](https://www.transitchicago.com/developers/traintracker/) | Chicago Transit Authority (CTA) | candidate (key required) | http | poll |
| `gfw` | [Global Fishing Watch events API — fishing, encounter, loitering and port-visit events](https://globalfishingwatch.org/our-apis/documentation) | Global Fishing Watch | candidate (key required) | http | poll |
| `mta_bustime` | [MTA Bus Time GTFS-Realtime vehicle positions — every New York City bus](https://bustime.mta.info/developers/gtfs-realtime/) | Metropolitan Transportation Authority (MTA) | candidate (key required) | http | poll |
| `nta` | [NTA Ireland GTFS-Realtime vehicle positions — Dublin Bus, Bus Éireann, Go-Ahead Ireland](https://developer.nationaltransport.ie/) | National Transport Authority (NTA), Ireland | candidate (key required) | http | poll |
| `wmata` | [WMATA GTFS-Realtime vehicle positions — Washington DC Metrobus and Metrorail](https://developer.wmata.com/) | Washington Metropolitan Area Transit Authority (WMATA) | candidate (key required) | http | poll |
| `entsoe` | [ENTSO-E Transparency Platform — actual electricity generation per production type](https://transparencyplatform.zendesk.com/hc/en-us/sections/12783116987028-Restful-API) | European Network of Transmission System Operators for Electricity (ENTSO-E) | candidate (key required) | http | poll |

Three links cannot be checked by a script: `www.binance.com/en/terms` answers
HTTP 202 with a JavaScript challenge, and `www.mta.info/developers` and
`www.mta.info/developers/terms-and-conditions` answer HTTP 403 to scripts (their
text was retrieved with a browser-like fetch on 2026-10-13). Every other
documentation, terms and sign-up link in the descriptors, this README and the
documentation fixtures (108 of 111) answered HTTP 200 on 2026-10-13.

## How rates are measured

| Delivery | Rate | Example |
|---|---|---|
| push | events received ÷ seconds consumed | WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP |
| poll | records new or changed between the first and last poll ÷ time between them | GBFS, GTFS-Realtime, ADS-B |
| poll, snapshot with a stated period | records in the snapshot ÷ that period | METAR (last hour), Sensor.Community (5 min), FIRMS (24 h) |
| file drop | records in the newest complete file ÷ the period it covers | GH Archive (1 h), GDELT (15 min), OpenStreetMap (1 min) |

`RunReport.rate_basis` records which one applies (`observed`, `published`, or
`unmeasured` when a run ended before a rate could be computed).

## Use

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

## API keys and configuration

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
| live | every source against its real provider, 60 s | see below | reported only (`.coveragerc.live`) |

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

Fixtures are real messages captured on 2026-10-13, trimmed, with personal values
replaced by `<masked>`; a test checks that no fixture leaks a personal value or an
e-mail address. Candidates have no key yet, so their fixtures are the providers'
official documentation examples, marked with `origin`, `documentation_url` and the
`corrections` applied (PDF page footers, a typographic quote, a trailing comma);
they are replaced by captured messages once the key works.

## Known behaviour

- Digitraffic road sensors (`dt_road`) publish in bursts; a short window can see
  none.
- `npm` counts changed packages per request: several updates of one package
  between two polls count once.
- The USGS legacy Water Services announce their retirement on 2027-02-22.
- Branch protection is not available for private repositories on the GitHub Free
  plan; work reaches `main` through pull requests by convention.
