# Bytewax "Awesome Public Real-Time Datasets" — screening of every free entry

| | |
|---|---|
| Date | 2026-10-19 00:47–02:00 UTC (screening); record written 2026-10-19 02:46 UTC |
| List | https://github.com/bytewax/awesome-public-real-time-datasets, commit `f598d0a7b08c8ec29457d97b15828095372a102b` (2026-07-10), README read 2026-10-19 00:47 UTC |
| Scope | The 69 entries of the list's **Free** section (the Paid section is out of scope) |
| Evidence | `/home/mavasbel/Dev/repos/ITAM/stream-consumers/data/bytewax-screen-2026-10-19/` (git-ignored): `entries.json`, `README.snapshot.md`, `PROMPT.md` (the screening rules), `results-{A,B,C,D}.json` (one verdict per entry with endpoint, access, measurement, documented bound, terms and quoted evidence), `captures/` (raw captured data), `work-*/` (scripts and outputs), `cadence/` (Last-Modified log of NDBC and the EA flood API) |
| Sampling | The seven added sources: stream-consumers commit `75a87fd` (checkout `stream-consumers-new`), user unit `stream-sampling-bytewax-20261019` started 2026-10-19 02:45 UTC, `sample --rounds 24 --interval 3600 --window 60 --stop-when-settled`, reports in `stream-consumers/data/reports/sampling-bytewax-20261019/` |
| Earlier record | `docs/research/2026-10-12-21-37-public-data-streams-survey.md` (unchanged) |

## Rules applied

Each entry was judged against the project's inclusion rules: real data (not generated or simulated); free, with no key or a free key; at least 1 event/s; at least 10 attributes per event (flattened leaves). Entries reachable without a key were measured live (one window each, so a screen only; inclusion is decided by the source's own 24-round sampling). Entries that need a key were judged from the provider's documentation and stated limits, quoted with their URL and HTTP status. Four parallel screening agents covered entries by category (A finance 17, B transport 8, C information/health/IoT 15, D cybersecurity and other 15); the 10 entries already in the catalog and the 4 synthetic generators were classified directly.

## Summary

| Screen verdict | Entries |
|---|---|
| fails | 26: 4 Finnhub, 5 CoinCheck, 7 SEC EDGAR, 8 FilingFirehose, 11 CoinCap, 15 DexPaprika, 19 OpenChainBench, 25 NY 511 live camera data, 33 Seismic Data, 34 Open Weather API, 35 Clima Cell, 37 NOAA Weather Data, 38 Redfin Realestate, 42 US Energy Grid Data, 43 USGS Earthquake Real-time Feed, 44 News API, 45 New York Times Newswire API, 47 Longevity World Cup, 48 ThingSpeak IoT Public Channels, 50 Certstream, 51 URLhaus, 52 CISA Automated Indicator Sharing (AIS), 59 AI Detector Arena, 64 International Space Station Live Data, 65 Live Satellite Positions, 66 Hacker News |
| in catalog | 10: 1 Coinbase Market Data, 9 Binance, 22 Open Sky Flight, 24 MTA GTFS Feed, 26 Transport for London (TfL), 31 Ireland National Transport Authority, 32 Wikimedia SSE, 46 GDELT 2.0 Event Database, 49 Sensor.Community, 67 Bluesky |
| qualifies-keyless | 10: 2 Blockchain transactions, 3 Yahoo Finance, 14 CoinPaprika, 17 Sharpe, 21 GBFS New York, 23 Open Glider Network, 36 NOAA Buoy Data, 39 EPA Airnow data, 40 UK Flood Data, 61 GitHub Events |
| paid-only | 6: 12 Polygon.io, 13 FinancialData.Net, 16 Pyth Network, 54 Shodan Streaming API, 63 Formula 1 Stats & Telemetry, 69 OpenF1 |
| qualifies-with-free-key | 4: 10 OANDA, 28 German Traffic Data, 29 Swiss Traffic & Public Transport Data, 53 Open Threat Exchange (OTX) |
| synthetic | 4: 56 Lenses Datagen, 57 Mockingbird by Tinybird, 58 SSE.dev, 62 EventSim |
| undetermined | 3: 6 Alpaca Markets, 20 Open Rail Data, 30 Transport for NSW API |
| unreachable | 3: 18 Agent Gateway, 27 Norwegian Coastal Administration, 68 SpaceX API |
| not-a-stream | 3: 41 ZipCheckup, 55 GreyNoise Community API, 60 World Cup 2026 Tour |
| **Total** | **69** |

### Decisions

- **Added to stream-consumers** (keyless; screened at ≥ 1 event/s; measured with `sample --stop-when-settled`): 2 Blockchain transactions → `blockchain`, 14 CoinPaprika → `coinpaprika`, 17 Sharpe → `sharpe`, 21 GBFS New York → `citibike`, 23 Open Glider Network → `ogn`, 36 NOAA Buoy Data → `ndbc`, 40 UK Flood Data → `ukflood`.
- **Corrected and not added:** 39 EPA AirNow (0.55 events/s, see its entry). **Excluded on terms:** 3 Yahoo Finance. **Duplicates of catalog sources:** 50 Certstream (`ct`), 61 GitHub Events (`gharchive`).
- **A free key is needed to decide:** 6 Alpaca, 10 OANDA, 20 Open Rail Data, 29 Swiss opentransportdata, 30 Transport for NSW, 53 OTX; 28 German Mobilithek is not recommended (organisation, provider approval and machine certificate).

## Every entry

| n | Category | Entry | Access | Rate (screen) | Attributes | Verdict | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Finance/Crypto | [Coinbase Market Data](https://docs.cloud.coinbase.com/exchange/docs/websocket-overview) | keyless | — | — | in catalog | Already in the catalog as `coinbase`. |
| 2 | Finance/Crypto | [Blockchain transactions](https://www.blockchain.com/api/api_websocket) | keyless | 22.03 measured (1322 in 60.0 s) | 33 (median) | qualifies-keyless | Added as `blockchain` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 3 | Finance/Crypto | [Yahoo Finance](https://finance.yahoo.com/quote/%5EGSPC?p=%5EGSPC) | keyless | 2.3 measured (138 in 60.0 s) | 20 (median) | qualifies-keyless | Not added: Yahoo's Terms of Service forbid collecting data 'using any automated means'; the endpoint is undocumented. |
| 4 | Finance/Crypto | [Finnhub](https://finnhub.io/docs/api/introduction) | free-key | bound: documented, not measured: rate not documented (trade-driven, up to 50 symbols on free plan); attributes per trade = 5 (s, p, t, v, c) plus message 'type' = 6. | — | fails | Fails. |
| 5 | Finance/Crypto | [CoinCheck](https://coincheck.com/documents/exchange/api#websocket) | keyless | 11.93 measured (716 in 60.0 s) | 9 (median) | fails | Fails. |
| 6 | Finance/Crypto | [Alpaca Markets](https://alpaca.markets/docs/market-data/) | free-key | bound: documented, not measured: free Basic plan = IEX feed, 30 symbols; stock quote schema has 11 fields (T,S,ax,ap,as,bx,bp,bs,c,t,z), trade 9, bar 10; crypto trade  | — | undetermined | Free key would settle it; the free crypto stream has 7 fields per message, so only the stock stream could pass. |
| 7 | Finance/Crypto | [SEC EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | keyless | 0.0 measured (0 in 199.0 s) | 13 (median) | fails | Fails. |
| 8 | Finance/Crypto | [FilingFirehose](https://filingfirehose.com) | keyless | 0.0022 measured (None in None s) | 10 (median) | fails | Fails. |
| 9 | Finance/Crypto | [Binance](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) | keyless | — | — | in catalog | Already in the catalog as `binance`. |
| 10 | Finance/Crypto | [OANDA](https://github.com/oanda/py-api-streaming) | free-key | bound: documented, not measured: "at most 4 prices per second (every 250 milliseconds) for each instrument being requested" -> up to 4 x N instruments events/s; the do | — | qualifies-with-free-key | Free key needed (OANDA demo account). FX prices stop at weekends, so weekend rounds read 0 events/s. |
| 11 | Finance/Crypto | [CoinCap](https://docs.coincap.io) | free-key | bound: documented, not measured: 500 credits/month (rolling to ~2,592,000 s) and 5 calls/min; even if every call cost only 1 credit and returned R changed assets, sust | — | fails | Fails. |
| 12 | Finance/Crypto | [Polygon.io](https://polygon.io/docs/stocks/getting-started) | paid-only | bound: documented, not measured: free tier = 5 REST calls/min of end-of-day data, no WebSocket; no real-time stream without payment. | — | paid-only | Paid only. |
| 13 | Finance/Crypto | [FinancialData.Net](https://financialdata.net/documentation) | free-key | bound: documented, not measured: free key = 300 requests/day x <=300 records = <=90,000 records/day (1.04/s) but these are end-of-day historical rows (new data appears | — | paid-only | Paid only. |
| 14 | Finance/Crypto | [CoinPaprika](https://api.coinpaprika.com) | keyless | 11.1 measured (2000 in 180.2 s) | 26 (median) | qualifies-keyless | Added as `coinpaprika` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 15 | Finance/Crypto | [DexPaprika](https://api.dexpaprika.com) | keyless | 6.21 measured (373 in 60.06 s) | 6 (median) | fails | Fails. |
| 16 | Finance/Crypto | [Pyth Network](https://docs.pyth.network/) | paid-only | bound: documented, not measured: Core feeds update every 400 ms ("500+ price feeds with 400ms updates"), but API access only on paid plans (free plan: no API access; t | — | paid-only | Paid only. |
| 17 | Finance/Crypto | [Sharpe](https://www.sharpe.ai/docs/free-api) | keyless | 68.2 measured (13633 in 199.9 s) | 26 (median) | qualifies-keyless | Added as `sharpe` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 18 | Finance/Crypto | [Agent Gateway](https://agent-gateway-kappa.vercel.app/prices) | keyless | bound: documented, not measured: even if reachable, 50 requests/day x 275 markets = 13,750 records/day = 0.16/s maximum. | — | unreachable | Unreachable. |
| 19 | Finance/Crypto | [OpenChainBench](https://openchainbench.com) | keyless | 0.0 measured (0 in 180.2 s) | 25 (median) | fails | Fails. |
| 20 | Transportation | [Open Rail Data](https://wiki.openraildata.com/index.php/Rail_Data_FAQ) | free-key | bound: Documented, not measured. Train Movements (TRUST): 'Up to 600 per minute' (peak <=10 msg/s; daily average NOT documented); each movement message (msg_type 0003) | — | undetermined | Free account would settle it (Network Rail caps accounts at 1,000 users). |
| 21 | Transportation | [GBFS New York](http://gbfs.citibikenyc.com/gbfs/gbfs.json) | keyless | 13.56 measured (2445 in 180.3 s) | 14 (median) | qualifies-keyless | Added as `citibike` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 22 | Transportation | [Open Sky Flight](https://openskynetwork.github.io/opensky-api/rest.html) | keyless | — | — | in catalog | Already in the catalog as `opensky`. |
| 23 | Transportation | [Open Glider Network](http://wiki.glidernet.org/) | keyless | 102.08 measured (12253 in 120.03 s) | 21 (median) | qualifies-keyless | Added as `ogn` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 24 | Transportation | [MTA GTFS Feed](https://new.mta.info/developers) | keyless | — | — | in catalog | Already in the catalog as `mta_gtfsrt`. |
| 25 | Transportation | [NY 511 live camera data](https://511ny.org/cctv) | free-key | bound: Documented, not measured. GetCameras returns the camera list with exactly 10 documented fields (Latitude, Longitude, ID, Name, DirectionOfTravel, RoadwayName, U | — | fails | Fails. |
| 26 | Transportation | [Transport for London (TfL)](https://tfl.gov.uk/info-for/open-data-users/our-open-data) | keyless | — | — | in catalog | Already in the catalog as `tfl`. |
| 27 | Transportation | [Norwegian Coastal Administration](https://www.kystverket.no/en/navigation-and-monitoring/ais/access-to-ais-data/) | keyless | — | — | unreachable | Unreachable. |
| 28 | Transportation | [German Traffic Data](https://mobilithek.info/offers?categories=%5B%22https%3A%2F%2Fw3id.org%2Fmdp%2Fschema%2Fdata_categories%23REALTIME_TRAFFIC_DATA%22%5D) | free-key | bound: Documented, not measured. NRW offer: 'Verkehrsmengen (Q) und Geschwindigkeiten (v) der Pkw, Lkw und Kfz auf Einzelfahrstreifen an rd. 3.500 Messquerschnitten',  | — | qualifies-with-free-key | Not recommended: Mobilithek access needs an organisation, provider approval and an X.509 machine certificate. |
| 29 | Transportation | [Swiss Traffic & Public Transport Data](https://opentransportdata.swiss/en/group/api-group) | free-key | bound: Documented, not measured. Traffic counters: 'The data is updated every minute'; the keyless static MeasurementSiteTable (v30, 2026-10-15) lists 2496 measurement | — | qualifies-with-free-key | Free key needed (opentransportdata.swiss API Manager). |
| 30 | Transportation | [Transport for NSW API](https://api.nsw.gov.au/ProductCatalogue?apiCategoryId=2) | free-key | bound: Documented, not measured. Requests: 5/s throttle, 60,000/day quota (= 0.69 requests/s daily average). Records per response (number of vehicles) and vehicle upda | — | undetermined | Free key would settle it. |
| 31 | Transportation | [Ireland National Transport Authority](https://developer.nationaltransport.ie/api-details#api=gtfsr&operation=gtfsr-v2) | keyless | — | — | in catalog | Already in the catalog as `nta`. |
| 32 | Information | [Wikimedia SSE](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams) | keyless | — | — | in catalog | Already in the catalog as `wikimedia`. |
| 33 | Information | [Seismic Data](https://www.seismicportal.eu/realtime.html) | keyless | 0.0111 measured (2 in 180.2 s) | 20 (median) | fails | Fails. |
| 34 | Information | [Open Weather API](https://openweathermap.org/api) | free-key | bound: documented, not measured: 1,000,000 calls/month / (30 x 86,400 s) = 0.386 calls/s sustained, with one city record per Current Weather call, so at most 0.386 rec | — | fails | Fails. |
| 35 | Information | [Clima Cell](https://docs.tomorrow.io/reference/realtime-weather) | free-key | bound: documented, not measured: 500 requests/day x 1 location record per response = 0.0058 records/s. The documented response schema has data.time, 20 data.values.* f | — | fails | Fails. |
| 36 | Information | [NOAA Buoy Data](https://www.ndbc.noaa.gov/data/realtime2/) | keyless | 3.31 measured (597 in 180.6 s) | 22 (median) | qualifies-keyless | Added as `ndbc` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 37 | Information | [NOAA Weather Data](https://www.weather.gov/documentation/services-web-api) | keyless | 0.0 measured (0 in 150.5 s) | 44 (median) | fails | Fails. |
| 38 | Information | [Redfin Realestate](https://github.com/ryansherby/RedfinScraper) | none | bound: undetermined: there is no documented official API or rate. Not measured because the terms prohibit automated querying. | — | fails | Fails. |
| 39 | Information | [EPA Airnow data](https://docs.airnowapi.org/) | keyless | 1.226 measured (4415 in 3600 s) | 34 (median) | qualifies-keyless | Not added: correction of the screen. Every hourly HourlyAQObs file of 2026-10-17 23:00 to 2026-10-19 00:00 UTC (25 files read 2026-10-19 01:50 UTC) has exactly 4,415 rows: one per site, reported or not. In the file of 2026-10-18 22:00 UTC only 1,980 rows carry a pollutant value (3,748 values), so the observation rate is 1,980 / 3,600 s = 0.55 events/s (1.04 if each pollutant value were an event, but the per-value HourlyData file has 9 fields). |
| 40 | Information | [UK Flood Data](https://environment.data.gov.uk/flood-monitoring/doc/reference) | keyless | 29.28 measured (4404 in 150.4 s) | 14 (median) | qualifies-keyless | Added as `ukflood` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s. |
| 41 | Information | [ZipCheckup](https://zipcheckup.com/api) | keyless | bound: documented, not measured: 100 requests/day x 1 ZIP profile = 0.0012 records/s; the data are ZIP-level aggregates materialized in batches, not events. | — | not-a-stream | Not a stream. |
| 42 | Information | [US Energy Grid Data](https://www.gridstatus.io/datasets) | free-key | bound: documented, not measured: 500,000 rows/month / 2,592,000 s = 0.19 rows/s (or 0.39 rows/s if the 1 million/month pricing-page figure applies). Attributes depend  | — | fails | Fails. |
| 43 | Information | [USGS Earthquake Real-time Feed](https://earthquake.usgs.gov/fdsnws/event/1/) | keyless | 0.0 measured (0 in 180.3 s) | 32 (median) | fails | Fails. |
| 44 | Information | [News API](https://newsapi.org) | free-key | bound: documented, not measured: 100 requests/day x 100 articles = 10,000/day = 0.116 articles/s, delayed 24 h. Article schema: source.id, source.name, author, title,  | — | fails | Fails. |
| 45 | Information | [New York Times Newswire API](https://developer.nytimes.com/docs/timeswire-product/1/overview) | free-key | bound: documented, not measured: 500 requests/day x 20 articles = 10,000/day = 0.116 articles/s upper bound. The Article schema has 23 top-level properties (more when  | — | fails | Fails. |
| 46 | Information | [GDELT 2.0 Event Database](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/) | keyless | — | — | in catalog | Already in the catalog as `gdelt`. |
| 47 | Health | [Longevity World Cup](https://longevityworldcup.com/api/data/athletes) | keyless | 0.0 measured (0 in 180.3 s) | 54 (median) | fails | Fails. |
| 48 | IoT | [ThingSpeak IoT Public Channels](https://thingspeak.com/channels/public) | keyless | 0.106 measured (9 in 84.9 s) | 8 (median) | fails | Fails. |
| 49 | IoT | [Sensor.Community](https://sensor.community/en/) | keyless | — | — | in catalog | Already in the catalog as `sensorcomm`. |
| 50 | Cybersecurity | [Certstream](https://certstream.calidog.io) | keyless | 0.0 measured (0 in 60.1 s) | 39 (median) | fails | Not added as a separate source: the hosted Certstream service sent nothing; the catalog's `ct` reads the same Certificate Transparency logs directly. |
| 51 | Cybersecurity | [URLhaus](https://urlhaus.abuse.ch/api/) | free-key | 0.0129 measured (33330 in 2592000 s) | 9 (median) | fails | Fails. |
| 52 | Cybersecurity | [CISA Automated Indicator Sharing (AIS)](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/automated-indicator-sharing-ais) | none | bound: undetermined (no public volume figure or schema on the AIS page) | — | fails | Fails. |
| 53 | Cybersecurity | [Open Threat Exchange (OTX)](https://otx.alienvault.com/api) | free-key | bound: Community-wide claim "over 20 million threat indicators contributed daily" (otx.alienvault.com; FAQ variant: 19 million) = ~231 indicators/s (documented, not me | — | qualifies-with-free-key | Free key needed (OTX account); the rate figure is a site-wide claim only. |
| 54 | Cybersecurity | [Shodan Streaming API](https://developer.shodan.io/api/stream) | paid-only | bound: Full firehose (Enterprise): "On average, 1,200-1,500 banners per second" (documented, not measured). Not available to free accounts. | — | paid-only | Paid only. |
| 55 | Cybersecurity | [GreyNoise Community API](https://docs.greynoise.io/reference/community-api) | keyless | bound: <=10 lookups/day keyless (0.000116/s); <=50/week with free key. Documented 200 response fields: ip, noise, riot, classification, name, link, last_seen, message  | 4 (median) | not-a-stream | Not a stream. |
| 56 | Development & Testing | [Lenses Datagen](https://github.com/lensesio/datagen) | — | — | — | synthetic | Fails the real-data rule: generates synthetic data ("synthetic streaming data generator"). |
| 57 | Development & Testing | [Mockingbird by Tinybird](https://github.com/tinybirdco/mockingbird) | — | — | — | synthetic | Fails the real-data rule: generates mock data ("mock streaming data generator"). |
| 58 | Development & Testing | [SSE.dev](https://sse.dev/test) | — | — | — | synthetic | Fails the real-data rule: a public SSE test endpoint emitting test messages. |
| 59 | AI/ML | [AI Detector Arena](https://aidetectarena.com) | keyless | 0.0 measured (0 in 108.7 s) | 14 (median) | fails | Fails. |
| 60 | Sports | [World Cup 2026 Tour](https://ay-worldcup2026.zeabur.app/developers) | keyless | 0.0 measured (0 in 126.8 s) | 25 (median) | not-a-stream | Not a stream. |
| 61 | Other | [GitHub Events](https://github.com/fastai/ghapi) | keyless | 2.754 measured (496 in 180.1 s) | 18 (median) | qualifies-keyless | Not added: the same public GitHub events as the catalog's `gharchive` (GH Archive records the events API). |
| 62 | Other | [EventSim](https://github.com/viirya/eventsim) | — | — | — | synthetic | Fails the real-data rule: simulates event data ("Tool to simulate event data"). |
| 63 | Other | [Formula 1 Stats & Telemetry](https://github.com/theOehrly/Fast-F1) | paid-only | bound: Live: undetermined without an F1TV subscription and outside sessions. livetiming.formula1.com/static/StreamingStatus.json = {"Status":"Offline"} at 2026-10-19 ~ | — | paid-only | Paid only. |
| 64 | Other | [International Space Station Live Data](https://iss-mimic.github.io/Mimic/) | keyless | 0.0 measured (0 in 120 s) | 7 (median) | fails | Fails. |
| 65 | Other | [Live Satellite Positions](https://www.n2yo.com/api/) | free-key | bound: positions: 1000 transactions/h x up to 300 one-second positions = 300,000 positions/h = 83.3 positions/s (documented, not measured); continuous coverage of one  | — | fails | Fails. |
| 66 | Other | [Hacker News](https://github.com/HackerNews/API) | keyless | 0.074 measured (13 in 176.7 s) | 6 (median) | fails | Fails. |
| 67 | Other | [Bluesky](https://docs.bsky.app/docs/advanced-guides/firehose) | keyless | — | — | in catalog | Already in the catalog as `bluesky`. |
| 68 | Other | [SpaceX API](https://github.com/r-spacex/SpaceX-API) | keyless | — | — | unreachable | Unreachable. |
| 69 | Other | [OpenF1](https://openf1.org/) | paid-only | 0.0 measured (0 in 60.0 s) | 11 (median) | paid-only | Paid only. |

## Evidence per screened entry

### 2. Blockchain transactions

- Endpoint: wss://ws.blockchain.info/inv (send {"op":"unconfirmed_sub"})
- Delivery: push (WebSocket); access: keyless
- Measured: {"utc_start": "2026-10-19T00:50:39.817969+00:00", "seconds": 60.0, "events": 1322, "events_per_s": 22.03, "attrs_median": 33, "attrs_max": 779}
- Screen verdict: **qualifies-keyless** — Measured 1,322 unconfirmed-BTC-transaction ('utx') messages in 60 s = 22.0 events/s; median 33 flattened leaf fields per event (26 distinct key paths when list indices are collapsed); real Bitcoin mempool data.
- Decision: Added as `blockchain` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: WebSocket needed no key (measured). API Terms: "You shall not circumvent or attempt to circumvent any limitations on API requests we put in place; and You shall not commercialize (i.e., sell, rent, or lease), copy, store or cache the Blockchain Content, other than for the purposes allowed by this Agreement". The REST Explorer API now has paid plans (Free: "3 requests/second 300 requests/day"); the pricing page does not mention the WebSocket.
  - https://www.blockchain.com/api/api_websocket (200): "Our WebSocket API allows developers to receive Real-Time notifications about new transactions and blocks."
  - https://www.blockchain.com/api/api_websocket (200): "Subscribe to notifications for all new bitcoin transactions. (page config lists "CACHE_SERVER":"wss://ws.blockchain.info")"
  - wss://ws.blockchain.info/inv (101): "Connected without credentials; 1,322 {"op":"utx"} messages in 60 s (capture captures/2-blockchain-transactions.jsonl)"
  - https://www.blockchain.com/explorer/pricing (200): "Free $0 /month Free for everyone ... Address and Transaction endpoints 3 requests/second 300 requests/day"
  - https://www.blockchain.com/legal/api-terms (200): "You shall not circumvent or attempt to circumvent any limitations on API requests we put in place"

### 3. Yahoo Finance

- Endpoint: wss://streamer.finance.yahoo.com/?version=2 (send {"subscribe":[symbols]}; payload = base64 protobuf PricingData)
- Delivery: push (WebSocket, undocumented); access: keyless
- Measured: {"utc_start": "2026-10-19T00:55:34.426534+00:00", "seconds": 60.0, "events": 138, "events_per_s": 2.3, "attrs_median": 20, "attrs_max": 20, "note": "Run with 30 crypto symbols. A second run (2026-10-19T00:54:03Z, 60 s, 20 mixed symbols: indices, futures, FX, crypto, NVDA) gave 229 events = 3.82/s but median 9 attrs (FX/index/stock messages carry 9 fields; crypto 20). Decoded with yfinance 1.7.0 pricing.proto (33 defined fields; zero-valued fields omitted on the wire). Captures: captures/3-yahoo-finance-crypto.jsonl, captures/3-yahoo-finance.jsonl. Measured on Sunday evening US time (US cash equities closed)."}
- Screen verdict: **qualifies-keyless** — Technically meets the numbers with a crypto subscription (2.3 events/s, 20 attributes, keyless) but the endpoint is undocumented and Yahoo's ToS forbid automated data collection without express prior permission — criterion 2 (free to use) is legally doubtful; mixed non-crypto symbol lists gave median 9 attributes (<10).
- Decision: Not added: Yahoo's Terms of Service forbid collecting data 'using any automated means'; the endpoint is undocumented.
- Terms: Undocumented endpoint (no official developer docs). Yahoo Terms of Service prohibit: "access or collect data, or attempt to access or collect data, from our Services using any automated means, devices, programs, algorithms or methodologies, including but not limited to robots, spiders, scrapers, data mining tools, or data gathering or extraction tools, for any purpose without our express, prior permission." Rate depends on the chosen symbol list and market hours.
  - https://finance.yahoo.com/quote/%5EGSPC?p=%5EGSPC (200): "(quote page; no developer documentation for the streamer)"
  - wss://streamer.finance.yahoo.com/?version=2 (101): "Connected keyless; messages {"type":"pricing","message":"<base64 protobuf>"}"
  - https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html (200): "access or collect data ... from our Services using any automated means ... for any purpose without our express, prior permission."

### 4. Finnhub

- Endpoint: wss://ws.finnhub.io?token=<token> (trades)
- Delivery: push (WebSocket); access: free-key; sign-up: https://finnhub.io/register
- Documented bound: documented, not measured: rate not documented (trade-driven, up to 50 symbols on free plan); attributes per trade = 5 (s, p, t, v, c) plus message 'type' = 6.
- Screen verdict: **fails** — Attributes: documented trade object has only 5 fields (s symbol, p price, t timestamp, v volume, c conditions) inside {type, data[]} — below 10 per event.
- Decision: Fails.
- Terms: Token required (keyless connection returned HTTP 401 {"error":"Invalid API key."}). Docs: "1 API key can only open 1 connection at a time." "On top of all plan's limit, there is a 30 API calls/ second limit." Free plan per finnhub.io/pricing (search-engine snippet; page is JS-rendered): "60 API calls/minute Market data: Websocket 50 symbols".
  - https://finnhub.io/docs/api/introduction (200): "Stream real-time trades for US stocks, forex and crypto. ... A message can contain multiple trades. 1 API key can only open 1 connection at a time."
  - https://finnhub.io/docs/api/introduction (200): "responseAttributes: type; data[]: s (Symbol), p (Last price), t (UNIX milliseconds timestamp), v (Volume), c (List of trade conditions)"
  - wss://ws.finnhub.io (401): "{"error":"Invalid API key."}"
  - https://finnhub.io/pricing (200): "(JS-rendered; search snippet of this URL: "60 API calls/minute Market data: Websocket 50 symbols")"

### 5. CoinCheck

- Endpoint: wss://ws-api.coincheck.com/ (channels [pair]-trades, [pair]-orderbook)
- Delivery: push (WebSocket); access: keyless
- Measured: {"utc_start": "2026-10-19T00:57:40.188266+00:00", "seconds": 60.0, "events": 716, "events_per_s": 11.93, "attrs_median": 9, "attrs_max": 90, "note": "All 26 pairs x 2 channels. 3 trades in 60 s (0.05/s, 9 fields each); 713 orderbook-diff messages (11.9/s) with median 9 flattened leaves (semantically 4 fields: pair, bids, asks, last_update_at; extra leaves are only price-level array entries). Capture captures/5-coincheck.jsonl."}
- Screen verdict: **fails** — Trades: 0.05 events/s and 9 attributes. Orderbook diffs: 11.9/s but median 9 flattened leaves (4 semantic fields) — fails the >=10 attribute criterion.
- Decision: Fails.
- Terms: Docs: "The Public WebSocket API is available without authentication." "Data is pushed approximately every 0.1 seconds when a trade occurs." Only 26 JPY pairs.
  - https://coincheck.com/documents/exchange/api#websocket (200): "The Public WebSocket API is available without authentication. ... Connect to the following URI: wss://ws-api.coincheck.com"
  - https://coincheck.com/documents/exchange/api#websocket (200): "RESPONSE ITEMS ["transaction timestamp (unix time)", "transaction ID","pair","transaction rate","transaction amount","order side","ID of the Taker","ID of the Maker","ID of the Itayose order"]"

### 6. Alpaca Markets

- Endpoint: wss://stream.data.alpaca.markets/v2/iex (stocks, free Basic plan); wss://stream.data.alpaca.markets/v1beta3/crypto/us
- Delivery: push (WebSocket); access: free-key; sign-up: https://app.alpaca.markets/signup
- Documented bound: documented, not measured: free Basic plan = IEX feed, 30 symbols; stock quote schema has 11 fields (T,S,ax,ap,as,bx,bp,bs,c,t,z), trade 9, bar 10; crypto trade 7 / quote 7. Stream volume is not documented, so no numeric events/s bound can be derived (bars alone: <= 30 symbols x 1/min = 0.5/s).
- Screen verdict: **undetermined** — Free key gives real IEX quotes with 11 attributes (stocks), but the docs state no message volume, so >=1 event/s cannot be shown from documentation; needs a key to measure (and US market hours). Crypto channels fail attributes (7).
- Decision: Free key would settle it; the free crypto stream has 7 fields per message, so only the stock stream could pass.
- Terms: Linked page returns 404; current docs at docs.alpaca.markets. "With the exception of historical crypto data, all market data endpoints require authentication." Basic (free): "Real-time market coverage IEX ... Websocket subscriptions 30 symbols ... Historical API calls 200 / min". Connection limit "in many subscriptions (or without one) this limit is 1". Keyless crypto WS returned {"T":"error","code":401,"msg":"not authenticated"}.
  - https://alpaca.markets/docs/market-data/ (404): "(page not found)"
  - https://docs.alpaca.markets/docs/about-market-data-api (200): "Equities Basic Algo Trader Plus Pricing Free $99 / month ... Real-time market coverage IEX All US Stock Exchanges Websocket subscriptions 30 symbols Unlimited"
  - https://docs.alpaca.markets/docs/about-market-data-api (200): "With the exception of historical crypto data, all market data endpoints require authentication."
  - https://docs.alpaca.markets/docs/real-time-stock-pricing-data (200): "Quotes Schema ... T, S, ax, ap, as, bx, bp, bs, c, t, z"
  - https://docs.alpaca.markets/docs/real-time-crypto-pricing-data (200): "Trades Schema ... T, S, p, s, t, i, tks"
  - wss://stream.data.alpaca.markets/v1beta3/crypto/us (101): "[{"T":"error","code":401,"msg":"not authenticated"}]"

### 7. SEC EDGAR

- Endpoint: https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=100&output=atom (latest filings Atom)
- Delivery: poll (Atom feed); access: keyless
- Measured: {"utc_start": "2026-10-19T01:00:38.415169+00:00", "seconds": 199.0, "events": 0, "events_per_s": 0.0, "attrs_median": 13, "attrs_max": 13, "note": "19 polls, 10 s apart, all HTTP 200, 100 entries each; 0 new filings (Sunday 21:00 US-Eastern, outside filing hours). The 100 newest entries spanned Fri 2026-10-16 19:09:43 to 21:57:56 -04:00. Daily master index (one row per filing per filer): 2026-10-09 3,216; 10-13 4,534; 10-14 3,220; 10-15 3,652; 10-16 3,318 rows = 0.037-0.052 per second averaged over 24 h. Capture captures/7-sec-edgar.jsonl."}
- Screen verdict: **fails** — Rate: 0 new filings in 199 s (weekend); newest complete daily indexes show 3,216-4,534 filing rows per business day = at most 0.052/s (0.079/s even if compressed into 16 h) — far below 1/s.
- Decision: Fails.
- Terms: "These APIs do not require any authentication or API keys to access." Fair access: "Current max request rate: 10 requests/second." Must declare User-Agent (sent "ITAM course research <owner e-mail>"). EDGAR filings are public-domain U.S. government records.
  - https://www.sec.gov/search-filings/edgar-application-programming-interfaces (200): "These APIs do not require any authentication or API keys to access."
  - https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data (200): "Current max request rate: 10 requests/second. ... Please declare your user agent in request headers"
  - https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=100&output=atom (200): "100 <entry> elements; newest updated 2026-10-16T21:57:56-04:00 throughout 2026-10-19 01:00-01:04 UTC"
  - https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/master.20261016.idx (200): "3,318 filing rows"
  - https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/master.20261013.idx (200): "4,534 filing rows"

### 8. FilingFirehose

- Endpoint: https://filingfirehose.com/v1/public/8k | /v1/public/13d | /v1/public/atm (past 72 h, max limit=50)
- Delivery: poll (REST); access: keyless
- Measured: {"utc_start": "2026-10-19T01:04:50.286108+00:00", "seconds": null, "events": null, "events_per_s": 0.0022, "attrs_median": 10, "attrs_max": 16, "note": "Snapshot method (weekend, no new filings to poll): the 50 most recent 8-Ks spanned 2026-10-16 11:09:29 to 17:30:58 -04:00 (22,889 s) = 0.0022/s; 72-h counts: 13D/G 9, ATM 2. 8 top-level keys (10 flattened leaves due to item lists). Capture captures/8-filingfirehose.jsonl."}
- Screen verdict: **fails** — Rate: ~0.002 filings/s (50 8-Ks over 6.4 business hours; 9 Schedule 13D/G and 2 ATM in 72 h); it is a subset of EDGAR, which itself is <0.06/s.
- Decision: Fails.
- Terms: Terms: "free public tier (covering the past 72 hours of filings, no API key required)"; "Free public tier may be rate limited or temporarily unavailable during traffic spikes." "You may use the parsed data internally and in published research that cites the source (\"data: FilingFirehose\"); you may not republish bulk structured datasets". Derived from SEC EDGAR (subset: 8-K, S-3/424B5, 13D/G).
  - https://filingfirehose.com (200): "Free public tier — no API key required for the past 72 hours of data."
  - https://filingfirehose.com/terms (200): "free public tier (covering the past 72 hours of filings, no API key required)"
  - https://filingfirehose.com/openapi.json (200): "GET /v1/public/8k — Recent 8-K filings, past 72 hours. Free + open. (limit maximum 50)"
  - https://filingfirehose.com/v1/public/8k?limit=50 (200): "50 filings, filed_at 2026-10-16T11:09:29-04:00 .. 2026-10-16T17:30:58-04:00"

### 10. OANDA

- Endpoint: https://stream-fxpractice.oanda.com/v3/accounts/{accountID}/pricing/stream?instruments=... (HTTP chunked JSON stream)
- Delivery: push (HTTP streaming); access: free-key; sign-up: https://www.oanda.com/apply/demo/
- Documented bound: documented, not measured: "at most 4 prices per second (every 250 milliseconds) for each instrument being requested" -> up to 4 x N instruments events/s; the docs' example response shows 4 USD_CAD prices within 0.58 s. ClientPrice example = 21 flattened leaves (asks[4]{price,liquidity}, bids[4]{price,liquidity}, closeoutAsk, closeoutBid, instrument, status, time) plus type/tradeable.
- Screen verdict: **qualifies-with-free-key** — Free practice (demo) account gives the real pricing stream; docs allow up to 4 prices/s per instrument (example shows ~4/s on one pair) and each price has >=10 flattened attributes. Caveat: weekends produce no prices, so a Saturday daily median would be 0.
- Decision: Free key needed (OANDA demo account). FX prices stop at weekends, so weekend rounds read 0 events/s.
- Terms: Requires a v20 account + personal access token: "Try a free demo account or open a live account" then "Generate your personal access token immediately after you agree to the API license." Limits: "Streaming API 20 active streams", "no more than 2 new connections per second". FX trades only Sun-Fri (no weekend prices). Linked repo is a sample client (uses the v1 rates stream).
  - https://github.com/oanda/py-api-streaming (200): "A sample Python application that connects to OANDA's HTTP based rates stream."
  - https://developer.oanda.com/rest-live-v20/pricing-ep/ (200): "will provide at most 4 prices per second (every 250 milliseconds) for each instrument being requested."
  - https://developer.oanda.com/rest-live-v20/development-guide/ (200): "fxTrade Practice https://stream-fxpractice.oanda.com Required. ... Streaming API 20 active streams."
  - https://developer.oanda.com/rest-live-v20/introduction/ (200): "Get an OANDA v20 fxTrade account - Try a free demo account or open a live account"

### 11. CoinCap

- Endpoint: https://rest.coincap.io/v3/assets?apiKey=<key> (WebSocket streaming only on paid Growth+)
- Delivery: poll (REST); push only on paid plans; access: free-key; sign-up: https://coincap.io/api-key
- Documented bound: documented, not measured: 500 credits/month (rolling to ~2,592,000 s) and 5 calls/min; even if every call cost only 1 credit and returned R changed assets, sustained rate <= 500 x R / 2,592,000 s -> needs R >= 5,184 changed records per call for 1/s, while CoinCap covers "over 1,000 cryptocurrencies" (<= ~0.19/s). Asset schema: id, rank, symbol, name, supply, maxSupply, marketCapUsd, volumeUsd24Hr, priceUsd, changePercent24Hr, vwap24Hr, explorer, tokens, status, frozenAt (>=13).
- Screen verdict: **fails** — Free key: no WebSocket and only 500 credits/month — a sustained poll cannot reach 1 event/s (bound ~0.19/s); attributes would pass (>=13).
- Decision: Fails.
- Terms: v3 requires a key (keyless GET returned 401 {"error":"Unauthorized"}); legacy api.coincap.io v2 host no longer resolves (DNS failure). Free plan: "$0 /mo 500 credits/mo 5 calls/min WebSocket streaming — not included".
  - https://docs.coincap.io (200): "Supports accountless x402 payment protocol ... (100 free credits, refill with USDC on Base)"
  - https://rest.coincap.io/api-docs.json (200): "API key — sign up at https://coincap.io and pass Authorization: Bearer <key> or ?apiKey=<key>."
  - https://rest.coincap.io/v3/assets?limit=2 (401): "{"error":"Unauthorized"}"
  - https://splash.coincap.io/pricing (200): "Free $0 /mo 500 credits/mo 5 calls/min WebSocket streaming — not included"

### 12. Polygon.io

- Endpoint: wss://socket.polygon.io (paid plans only; site now branded Massive)
- Delivery: push (WebSocket) on paid plans; REST; access: paid-only; sign-up: https://polygon.io/pricing
- Documented bound: documented, not measured: free tier = 5 REST calls/min of end-of-day data, no WebSocket; no real-time stream without payment.
- Screen verdict: **paid-only** — All free Basic plans have websocket 'unavailable' and end-of-day data only; any streaming (delayed or real-time) requires a paid plan.
- Decision: Paid only.
- Terms: Free "Basic" plans (stocks, options, indices, currencies, futures) list "5 API Calls / Minute", "End of Day Data" and "websocket":"unavailable"; WebSockets start at Stocks Starter $29/mo (15-min delayed); real-time at Stocks Advanced $199/mo. Free plans are "Individual use".
  - https://polygon.io/docs/stocks/getting-started (308): "redirect to /docs/rest/stocks/overview"
  - https://polygon.io/docs/rest/stocks/overview (200): "(REST docs)"
  - https://polygon.io/pricing (200): "Stocks Basic Great for trying our APIs $0 /month ... 5 API Calls / Minute ... End of Day Data"
  - https://polygon.io/pricing (200): "stocks_basic / currencies_basic features: "timeframe":"End of Day Data","websocket":"unavailable""

### 13. FinancialData.Net

- Endpoint: https://financialdata.net/api/v1/... ?key=API_KEY (REST only)
- Delivery: poll (REST); access: free-key; sign-up: https://financialdata.net/pricing
- Documented bound: documented, not measured: free key = 300 requests/day x <=300 records = <=90,000 records/day (1.04/s) but these are end-of-day historical rows (new data appears once per trading day per symbol), and the free Stock Prices record has 7 fields (trading_symbol, date, open, high, low, close, volume).
- Screen verdict: **paid-only** — No stream exists; real-time quotes require Premium. The free tier offers only daily EOD rows with 7 attributes (fails attributes) and no new events at >=1/s.
- Decision: Paid only.
- Terms: "Free subscriptions include up to 300 requests per day." Free plan covers "Symbol Lists" and "Market & Miscellaneous Data" (daily/EOD); real-time Stock/Crypto/Forex Quotes and Latest Prices are "Premium subscription" ($69/month); Minute Prices Standard ($29/month). Pricing page separates Personal Use and Commercial Use.
  - https://financialdata.net/documentation (200): "API rate limits vary by subscription. Free subscriptions include up to 300 requests per day."
  - https://financialdata.net/documentation (200): "Stock Quotes Premium subscription Get real-time stock quotes ... Stock Prices Free subscription ... daily historical stock prices"
  - https://financialdata.net/pricing (200): "Free $ 0 /month 300 Requests / Day REST API & Python SDK Symbol Lists Market & Miscellaneous Data"

### 14. CoinPaprika

- Endpoint: https://api.coinpaprika.com/v1/tickers (keyless free REST); wss://streaming.coinpaprika.com/ticks is Enterprise-only
- Delivery: poll (REST); access: keyless
- Measured: {"utc_start": "2026-10-19T01:07:47.382899+00:00", "seconds": 180.2, "events": 2000, "events_per_s": 11.1, "attrs_median": 26, "attrs_max": 26, "note": "4 polls 60 s apart; 2,000 tickers per response; between first and last poll 1,700 tickers changed (1,691 with a new price) + 300 new ids = 2,000. The window contained exactly one backend refresh; steady state ~1,700-2,000 changed tickers per ~299 s refresh = ~5.7-6.7/s. 20,000 calls/month allows one call every ~130 s, enough to catch every refresh. Capture captures/14-coinpaprika.jsonl."}
- Screen verdict: **qualifies-keyless** — Keyless; measured 2,000 changed/new tickers in 180 s (11.1/s by the poll definition; ~5.7-6.7/s steady-state from the ~5-min refresh) with 26 attributes each. Free tier is 'Personal' use only.
- Decision: Added as `coinpaprika` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: Free: "20,000 requests per month", global "10 requests/second per IP", update interval "Up to 10 min", Usage "Personal" (commercial use only on paid plans; redistribution only Enterprise). Response Cache-Control: "public, max-age=5, s-maxage=5, stale-while-revalidate=10"; observed Last-Modified changed 01:04:48 -> 01:09:47 GMT (~5 min refresh). WebSocket: "WebSocket streaming is part of the Enterprise plan."
  - https://api.coinpaprika.com (200): "CoinPaprika crypto API quickstart: 3 steps, free, no credit card required"
  - https://docs.coinpaprika.com/api-reference/rest-api/introduction.md (200): "Most of our API endpoints are available without an API key. ... Free: 20,000 requests per month"
  - https://docs.coinpaprika.com/faq.md (200): "We have a global limit of 10 requests/second per IP."
  - https://docs.coinpaprika.com/api-plans.md (200): "Update Interval: Free Up to 10 min ... Usage: Free Personal"
  - https://docs.coinpaprika.com/api-reference/streaming-api/streaming-introduction.md (200): "WebSocket streaming is part of the Enterprise plan. Keys issued on the Free ... plans do not open a streaming connection."
  - https://api.coinpaprika.com/v1/tickers (200): "2,000 tickers; Last-Modified Mon, 19 Oct 2026 01:04:48 GMT then 01:09:47 GMT"

### 15. DexPaprika

- Endpoint: https://streaming.dexpaprika.com/sse/prices (POST up to 25 assets; keyless only for 35 showcase assets); REST https://api.dexpaprika.com
- Delivery: push (SSE) / poll (REST); access: keyless; sign-up: https://console.dexpaprika.com/
- Measured: {"utc_start": "2026-10-19T01:11:39.268226+00:00", "seconds": 60.06, "events": 373, "events_per_s": 6.21, "attrs_median": 6, "attrs_max": 6, "note": "POST with 25 showcase tokens; 373 token_price + 3 ping events. Capture captures/15-dexpaprika.jsonl."}
- Documented bound: documented, not measured: sustained allowance 10,000 credits/30 days keyless (0.0039/s) or 100,000 with free key (0.039/s); token_reserves event documented with 9 fields.
- Screen verdict: **fails** — Attributes: token_price events have 6 fields (<10). Rate cannot be sustained: 1 credit per delivered event against 10,000 (keyless) / 100,000 (free key) credits per 30 days = 0.004 / 0.039 events/s.
- Decision: Fails.
- Terms: Credits: "1 credit per update delivered ... against 10,000 credits per rolling 30 days keyless, 100,000 with a free key". REST keyless returned HTTP 402 "Monthly limit reached for unauthenticated use. Register for a free API key to get more credits/month." Swap-transaction and candle streams are paid-only. Entry claim "no limits" is contradicted by the docs.
  - https://api.dexpaprika.com (402): "Monthly limit reached for unauthenticated use. Register for a free API key to get more credits/month."
  - https://docs.dexpaprika.com/streaming/introduction.md (200): "Credit cost | 1 credit per update delivered | ... 10,000 credits per rolling 30 days keyless, 100,000 with a free key"
  - https://docs.dexpaprika.com/streaming/introduction.md (200): "token_price ... {address, chain, price, timestamp, timestamp_price}"
  - https://docs.dexpaprika.com/streaming/showcase-streams.md (200): "/sse/prices — The 35 showcase assets below (without a key); /sse/transactions — Needs a paid plan"

### 16. Pyth Network

- Endpoint: https://hermes.pyth.network/v2/updates/price/stream?ids[]=... (SSE; API key required since 2026-08-26)
- Delivery: push (SSE); access: paid-only; sign-up: https://pythdata.app/signup
- Documented bound: documented, not measured: Core feeds update every 400 ms ("500+ price feeds with 400ms updates"), but API access only on paid plans (free plan: no API access; trial only).
- Screen verdict: **paid-only** — Hermes returns 401 without a key; the only free tier has 'No Pyth API access' and API keys come with a trial then paid plans from $500/month.
- Decision: Paid only.
- Terms: "Since August 26, 2026, every hermes.pyth.network request requires a Pyth API Key." "Sign up at Pyth Terminal: a free trial is included, paid plans cover ongoing use." Products page: Free "$0 /month ... No Pyth API access View-only access through Pyth Terminal"; Starter "$500 /month ... Pyth API access with API Key". On-chain Pyth contracts remain permissionless (reading them requires a blockchain RPC, not a Pyth data service).
  - https://docs.pyth.network/ (200): "(docs home)"
  - https://docs.pyth.network/llms-price-feeds-core.txt (200): "Since August 26, 2026, every hermes.pyth.network request requires a Pyth API Key."
  - https://docs.pyth.network/price-feeds/core/upgrade/preparing/index.mdx (200): "Sign up at Pyth Terminal: a free trial is included, paid plans cover ongoing use."
  - https://pythdata.app/products (200): "Free $0 /month ... No Pyth API access View-only access through Pyth Terminal ... Starter $500 /month ... Pyth API access with API Key"
  - https://hermes.pyth.network/v2/updates/price/latest?ids[]=0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43 (401): "unauthorized"

### 17. Sharpe

- Endpoint: https://www.sharpe.ai/api/funding/rates?type=current (keyless free REST)
- Delivery: poll (REST, edge-cached); access: keyless
- Measured: {"utc_start": "2026-10-19T01:15:19.486776+00:00", "seconds": 199.9, "events": 13633, "events_per_s": 68.2, "attrs_median": 26, "attrs_max": 26, "note": "4 polls ~60 s apart; 13,633 exchange-symbol rows (37 exchanges). All rows changed between first and last poll (updated_at); counting only rate or mark_price changes: 11,153 rows (55.8/s). Snapshot cadence: updated_at 01:10:47 -> 01:15:55 (308 s) with 11,629 rows changing rate/mark_price in that refresh => ~37.8/s steady state. Capture captures/17-sharpe.jsonl."}
- Screen verdict: **qualifies-keyless** — Keyless; measured 13,633 changed funding-rate rows in 200 s (68.2/s by definition; ~37.8/s steady-state counting only rate/mark-price changes per ~5-min snapshot), 26 attributes each; data aggregated from 37 real derivatives exchanges.
- Decision: Added as `sharpe` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: "public REST endpoints at https://www.sharpe.ai/api/* that return JSON data with no API key required ... cached at the edge from 1 minute to 1 hour". "Free endpoints are cache-backed ... Do not treat them as SLA-backed quotas." Protective limit "120 requests per minute on each server instance unless listed below". Funding rates s-maxage "up to 100 s". Response ~8.7 MB.
  - https://www.sharpe.ai/docs/free-api (200): "Sharpe Terminal exposes public REST endpoints at https://www.sharpe.ai/api/* that return JSON data with no API key required."
  - https://www.sharpe.ai/docs/free-api (200): "Every endpoint that carries the freshness fields has a protective per-IP limit ... 120 requests per minute on each server instance"
  - https://www.sharpe.ai/api/funding/rates?type=current (200): "13,633 rows; X-Data-Source lists 37 exchanges; X-Freshness-Sla-Seconds: 600"

### 18. Agent Gateway

- Endpoint: https://agent-gateway-kappa.vercel.app/prices
- Delivery: poll (REST); access: keyless
- Measured: {"utc_start": "2026-10-19T01:21:44.308702+00:00", "seconds": null, "events": 0, "events_per_s": null, "attrs_median": null, "attrs_max": null, "note": "/prices, /api/price/BTC and /api/services/health all returned HTTP 502 ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR (also at ~01:20 UTC); the first attempt timed out. Capture captures/18-agent-gateway.jsonl."}
- Documented bound: documented, not measured: even if reachable, 50 requests/day x 275 markets = 13,750 records/day = 0.16/s maximum.
- Screen verdict: **unreachable** — Endpoint down: HTTP 502 ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR on 4 requests; also the documented 50 requests/day keyless cap bounds it at 0.16 records/s.
- Decision: Unreachable.
- Terms: Homepage: "50 free requests/day ... 50 requests/day without any key"; prices are "Live mid-prices for 275+ perpetual futures markets sourced from Hyperliquid DEX" (proxy of Hyperliquid; Hyperliquid itself not screened here).
  - https://agent-gateway-kappa.vercel.app/prices (502): "An error occurred with this application. ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR"
  - https://agent-gateway-kappa.vercel.app/ (200): "Free Tier $0 / forever 50 free requests/day ... 50 requests/day without any key"

### 19. OpenChainBench

- Endpoint: https://openchainbench.com/api/citable (current value of every benchmark); /api/freshness; /feed.json; daily Parquet on Hugging Face
- Delivery: poll (REST, edge-cached) / daily file drop; access: keyless
- Measured: {"utc_start": "2026-10-19T01:24:22.215651+00:00", "seconds": 180.2, "events": 0, "events_per_s": 0.0, "attrs_median": 25, "attrs_max": 28, "note": "4 polls of /api/citable 60 s apart: 246 records, 0 changed (edge cache HIT, Age 5->185 s). /api/freshness (1 attribute per benchmark: timestamp) polled 7x at 30 s: all 246 timestamps changed first->last (1.37/s; 4.1/s summing consecutive polls) — i.e. benchmarks refresh about once a minute, but the 25-attribute records were not re-served within 180 s. Hugging Face timeseries parquet has 8 columns; headlines config 17,392 rows total. Captures: captures/19-openchainbench.jsonl, captures/19-openchainbench-freshness.jsonl."}
- Documented bound: documented, not measured: 246 benchmark records refreshed 'every minute' => <=4.1 records/s if served uncached; observed edge cache >=408 s => <=0.6/s as delivered.
- Screen verdict: **fails** — Rate: the full 25-attribute records showed 0 changes in 180 s (cache); upper bound 246/min (4.1/s) only reachable on a 1-attribute freshness index; time-series parquet has 8 columns. Data are aggregated KPIs, not an event stream.
- Decision: Fails.
- Terms: MIT-licensed site; dataset CC-BY-4.0 (attribution). /feed.json Cache-Control "public, s-maxage=300, stale-while-revalidate=3600"; /api/citable served from edge cache (Age reached 408 s). Records are aggregated benchmark KPIs (e.g. p50 over 24 h), not individual events.
  - https://openchainbench.com (200): "OpenChainBench runs continuous, reproducible benchmarks on crypto infrastructure"
  - https://openchainbench.com/api/openapi.json (200): "GET /api/citable | Flat index of every citable benchmark with current values. GET /api/freshness | last resolved data timestamp (epoch ms) per benchmark slug."
  - https://openchainbench.com/api/citable (200): "246 benchmarks; Age 408, X-Vercel-Cache: STALE"
  - https://datasets-server.huggingface.co/info?dataset=OpenChainBench/benchmarks&config=timeseries (200): "features: snapshot_date, captured_at, bench_slug, provider_slug, point_index, value, window, schema_version"

### 20. Open Rail Data

- Endpoint: STOMP: publicdatafeeds.networkrail.co.uk (Network Rail Data Feeds; topics e.g. TRAIN_MVT_ALL_TOC, TD_ALL_SIG_AREA); account at https://publicdatafeeds.networkrail.co.uk/
- Delivery: push (STOMP / OpenWire / AMQP on TCP 61612 per wiki); access: free-key; sign-up: https://publicdatafeeds.networkrail.co.uk/ntrod/create-account
- Documented bound: Documented, not measured. Train Movements (TRUST): 'Up to 600 per minute' (peak <=10 msg/s; daily average NOT documented); each movement message (msg_type 0003) has 6 header + 29 body = 35 leaf fields. TD (train describer): 'Up to 6000 per minute' and 'approx. 1.5-2 million published by the feed on a typical day' (= 17.4-23.1 msg/s daily average), but C-class TD messages have only 4-6 fields (time, area_id, msg_type, from, to, descr / report_time). RTPPM: 1 per minute.
- Screen verdict: **undetermined** — Free account (capped at 1,000 users). No single feed is documented to meet both criteria: TD meets the rate (17-23 msg/s/day) but fails attributes (4-6 fields); Train Movements meets attributes (35 fields) but only a peak rate ('up to 600/min') is documented, not a daily average. Would need an account to measure Train Movements.
- Decision: Free account would settle it (Network Rail caps accounts at 1,000 users).
- Terms: Network Rail: 'Access to the feeds is provided on a first come, first served basis and is currently restricted to 1,000 users.' Brand/logo use prohibited; apps must not be called 'official'. Wiki (archived) asks for one account per person and exponential reconnect backoff. Linked FAQ page itself is behind a Cloudflare JS challenge (HTTP 403); content read from Wayback Machine captures.
  - https://wiki.openraildata.com/index.php/Rail_Data_FAQ (403): "Just a moment... Enable JavaScript and cookies to continue (Cloudflare challenge)"
  - http://web.archive.org/web/20260224145625/https://wiki.openraildata.com/index.php/About_the_Network_Rail_feeds (200): "Train Movements Real-time Up to 600 per minute ... TD Real-time Up to 6000 per minute ... First, register for an account by visiting https://publicdatafeeds.networkrail.co.uk/"
  - http://web.archive.org/web/20251212065116/https://wiki.openraildata.com/index.php/TD (200): "usually only 3-5 messages out of the approx. 1.5-2 million published by the feed on a typical day"
  - http://web.archive.org/web/20260219233313/https://wiki.openraildata.com/index.php/C_Class_Messages (200): "{"CA_MSG":{"time":"1349696911000", "area_id":"SK", "msg_type":"CA", "from":"3647", "to":"3649", "descr":"1F42"}}"
  - http://web.archive.org/web/20260203201059/https://wiki.openraildata.com/index.php/Train_Movement (200): "A train movement message is sent whenever a train arrives, passes or departs a location monitored by TRUST. (example: header 6 keys, body 29 keys)"
  - http://web.archive.org/web/20260128185730/https://wiki.openraildata.com/index.php/Train_Movements (200): "Zero or more of these messages is sent out in a JSON list, either every five seconds or when there are 32 messages to be sent."
  - https://www.networkrail.co.uk/who-we-are/transparency-and-ethics/transparency/open-data-feeds/ (200): "Access to the feeds is provided on a first come, first served basis and is currently restricted to 1,000 users."
  - https://publicdatafeeds.networkrail.co.uk/ntrod/welcome (200): "Data Feeds : Network Rail (Angular login app)"
  - https://raw.githubusercontent.com/openraildata/stomp-client-python/main/README.md (200): "To use this service, you will need to sign up for a free account and subscribe to the 'Darwin' feed. (National Rail Darwin, separate service)"

### 21. GBFS New York

- Endpoint: https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json (listed in http://gbfs.citibikenyc.com/gbfs/gbfs.json -> redirects to https)
- Delivery: poll (GBFS 1.1 JSON, ttl=60 s); access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:11.679137+00:00", "seconds": 180.3, "events": 2445, "events_per_s": 13.56, "attrs_median": 14, "attrs_max": 14, "notes": "4 polls at 60 s spacing (00:49-00:52 UTC = 20:49 EDT Sunday). 2519 stations. 2445 station records changed first->last poll (13.56/s); excluding records whose only change was last_reported: 409 (2.27/s). free_bike_status was empty (0 vehicles). Attr count min 12 (some stations omit scooter fields). Single short evening reading = screen only."}
- Screen verdict: **qualifies-keyless** — Measured 13.56 changed station records/s (2.27/s even ignoring last_reported-only changes) with median 14 flat fields; keyless under Citi Bike data license (no stand-alone redistribution).
- Decision: Added as `citibike` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: Citi Bike Data Sharing Policy (License Agreement): 'non-exclusive, royalty-free, limited, perpetual license to access, reproduce, analyze, copy, modify, distribute in your product or service and use the Data for any lawful purpose'; prohibited: 'Host, stream, publish, distribute, sublicense, or sell the Data as a stand-alone dataset' and 'Use data mining or other extraction methods in connection with Bikeshare's website'. Polled once per 60 s per feed ttl.
  - http://gbfs.citibikenyc.com/gbfs/gbfs.json (200): ""name": "station_status", "url": "https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json""
  - https://gbfs.lyft.com/gbfs/1.1/bkn/en/station_status.json (200): "ttl 60, version 1.1, 2519 stations"
  - https://gbfs.lyft.com/gbfs/1.1/bkn/en/free_bike_status.json (200): "ttl 60; bikes list empty (80-byte response)"
  - https://raw.githubusercontent.com/MobilityData/gbfs/master/gbfs.md (200): "`ttl` | REQUIRED | Non-negative integer | Number of seconds before the data in the feed will be updated again"
  - https://citibikenyc.com/system-data (200): "Citi Bike publishes real-time system data in General Bikeshare Feed Specification format."
  - https://www.citibikenyc.com/data-sharing-policy (200): "Bikeshare hereby grants to you a non-exclusive, royalty-free, limited, perpetual license to access, reproduce, analyze, copy, modify, distribute in your product or service and use the Data for any lawful purpose"

### 23. Open Glider Network

- Endpoint: aprs.glidernet.org:14580 (APRS-IS, client-defined filter; full feed port 10152 per python-ogn-client settings)
- Delivery: push (TCP APRS-IS text lines); access: keyless
- Measured: {"utc_start": "2026-10-19T00:52:52Z", "seconds": 120.03, "events": 12253, "events_per_s": 102.08, "attrs_median": 21, "attrs_max": 26, "notes": "Filter r/48/10/3000 (3000 km radius around 48N 10E = Europe) at night in Europe (02:52 CEST). Events = non-comment APRS lines; 7 '#' server lines excluded. Parsed with ogn-client 2.0.0 (raw_message and reference_timestamp excluded, null fields excluded): 12205 parsed, 48 parse errors, min 8, 86.9% of packets have >=10 fields. Mix: position 9260, status 2750; many are OGADSB (ADS-B) beacons."}
- Screen verdict: **qualifies-keyless** — Measured 102 packets/s over 120 s (night-time Europe) with median 21 parsed fields; keyless read-only login (passcode -1), ODbL.
- Decision: Added as `ogn` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: OGN data usage rules: 'Data provided by OGN are under the licence ODbL'; 'When you re-distribute OGN data, you must follow DDB tracking privacy choices'; 'You do not re-distribute OGN data older than 24 hours'. Wiki: 'Please avoid pulling excessive amount of data from the server'. Login used: 'user N0CALL pass -1 vers course-screening 0.1 filter r/48/10/3000' (read-only, server replied 'unverified'). Packets contain aircraft registrations/callsigns (values not reported).
  - https://wiki.glidernet.org/ (200): "The live tracking data is freely available. Please have a look at the OGN data usage policy."
  - https://wiki.glidernet.org/aprs-interaction-examples (200): "Ask the DNS for aprs.glidernet.org port 14580."
  - https://raw.githubusercontent.com/glidernet/python-ogn-client/master/ogn/client/settings.py (200): "APRS_SERVER_PORT_FULL_FEED = 10152 / APRS_SERVER_PORT_CLIENT_DEFINED_FILTERS = 14580"
  - https://raw.githubusercontent.com/glidernet/python-ogn-client/master/ogn/client/client.py (200): "login = create_aprs_login(self.aprs_user, -1, self.settings.APRS_APP_NAME, self.settings.APRS_APP_VER, self.aprs_filter)"
  - https://www.glidernet.org/ogn-data-usage/ (200): "Data provided by OGN are under the licence ODbL ... You do not re-distribute OGN data older than 24 hours"
  - tcp://aprs.glidernet.org:14580 (connected (85.188.1.173)): "# logresp N0CALL unverified, server GLIDERN3"

### 25. NY 511 live camera data

- Endpoint: https://511ny.org/cctv (now a single-page app; camera layer backed by https://api-511x-nysdot.carsprogram.org/cameras per site config). Documented legacy API: https://www.511ny.org/api/getcameras?key={key}&format={format}
- Delivery: scrape / poll (JPEG images; site config polls camera layer every 360000 ms); access: free-key; sign-up: https://511ny.org/developers (legacy developer API; current route returns SPA shell)
- Documented bound: Documented, not measured. GetCameras returns the camera list with exactly 10 documented fields (Latitude, Longitude, ID, Name, DirectionOfTravel, RoadwayName, Url, VideoUrl, Disabled, Blocked); these are reference records, not events. The changing data are camera images (binary JPEG, no attribute fields); image refresh rate undetermined. Max 10 calls/60 s.
- Screen verdict: **fails** — Not a structured event stream: what changes over time are JPEG frames with no attributes (criterion 4); the only structured record (camera list, 10 fields) is static reference data, so NEW/CHANGED records per second is ~0 by the poll definition (rate undetermined, not shown >=1/s). The documented scrape URL pattern no longer serves images.
- Decision: Fails.
- Terms: Legacy developer API (Wayback capture 2026-07-22): 'Requires a developer key' and 'Throttling is enabled. 10 calls every 60 seconds.' The scraping URL pattern from the entry (https://511ny.org/map/Cctv/<id>) now returns the same 9364-byte SPA HTML shell as every other route (identical MD5), not an image.
  - https://511ny.org/cctv (200): "SPA shell loading https://demo.511ny.org/configs/main.json?v=1.8.5 (9364 bytes, same MD5 as /map/Cctv/1 and /api/getcameras)"
  - https://511ny.org/map/Cctv/1 (200): "same SPA HTML shell (md5 ca637030c862ecee91d4d2f5eff910ce), not an image"
  - https://demo.511ny.org/configs/main.json?v=1.8.5 (200): "'name': 'cameras', 'api': 'https://api-511x-nysdot.carsprogram.org/cameras', 'collection': 'cameras', 'poll': 360000"
  - https://api-511x-nysdot.carsprogram.org/cameras (200): "{"healthy":true}"
  - http://web.archive.org/web/20260722072642/https://511ny.org/developers/help (200): "Requires a developer key. ... Throttling is enabled. 10 calls every 60 seconds."
  - http://web.archive.org/web/20260515050920/https://www.511ny.org/developers/help/api/get-api-getcameras_key_format (200): "GET api/GetCameras Returns all cameras. ... Url The url to fetch the camera image."

### 27. Norwegian Coastal Administration

- Endpoint: tcp://153.44.253.27:5631 (raw AIS NMEA, IEC 62320-1)
- Delivery: push (raw TCP); access: keyless
- Screen verdict: **unreachable** — TCP connect to 153.44.253.27:5631 timed out on 5 attempts between 2026-10-19T00:48:50Z and 01:09:01Z (timeouts 20, 40, 30, 30, 60 s); ports 80 and 443 on the same IP also timed out (30 s each). UDP traceroute reached hop 25 (195.0.241.22) without reaching the host. The earlier 2026-10-12 test also got no data. Lines/s and decoded field count are therefore undetermined. Caveat: this machine egresses via a WireGuard tunnel, so a source-IP filter cannot be ruled out. Attempt log: captures/27-norwegian-coastal-ais.jsonl.
- Decision: Unreachable.
- Terms: 'The data are free and universally accessible, and are regulated under the Norwegian Licence for Open Government Data (NLOD). Access does not require user registration.' Open component excludes 'fishing vessels under 15 metres and recreational craft under 45 metres'. Alternative: BarentsWatch Live AIS API requires registering a user and an API client (OAuth client credentials); its docs state no volume figure.
  - https://www.kystverket.no/en/navigation-and-monitoring/ais/access-to-ais-data/ (404): "(listed URL is a 404 page)"
  - https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/ (200): "AIS data are also available at the following IP address: 153.44.253.27 port 5631 ... Access does not require user registration."
  - tcp://153.44.253.27:5631 (TimeoutError('timed out')): "connect timed out after 20/40/30/30/60 s"
  - https://developer.barentswatch.no/docs/AIS/live-ais-api/ (200): "Before you start you have to register a user at barentswatch.no, and create an API client on MyPage."

### 28. German Traffic Data

- Endpoint: Mobilithek catalog (metadata: POST https://mobilithek.info/mdp-api/mdp-msa-metadata/v2/offers/search). Example real-time offers: 'Fahrstreifendaten (Q und v) von Messstellen auf BAB in Nordrhein-Westfalen' (publicationId 110000000003476000), 'Fahrstreifendaten (q und v) ... VZD der Autobahn GmbH' (619101149275615232). Data delivered via Mobilithek brokering (DATEX II XML), accessUrl not public.
- Delivery: poll (Client Pull HTTPS/SOAP) or push via Mobilithek, certificate-authenticated M2M; access: free-key; sign-up: https://mobilithek.info/registration-request
- Documented bound: Documented, not measured. NRW offer: 'Verkehrsmengen (Q) und Geschwindigkeiten (v) der Pkw, Lkw und Kfz auf Einzelfahrstreifen an rd. 3.500 Messquerschnitten', accrualPeriodicity EVERY_1_MINUTE -> ~3500/60 = ~58 cross-section records/s. Hessen (VZD) offer: 'rd. 2.500 Messquerschnitten', EVERY_1_MINUTE -> ~42/s. Attributes: per lane 6 measured values (Q and v for Pkw/Lkw/Kfz) plus site reference id/version and measurement time in DATEX II Profile_Measurement_Data; exact flattened count needs a sample (not available without subscription).
- Screen verdict: **qualifies-with-free-key** — Free (Mobilithek use is free) but requires organisation registration, provider approval and a machine certificate; documented ~3,500 NRW cross-sections updated every minute (~58 records/s) with Q and v per vehicle class per lane (>=6 values per lane + id/version/time). Needs a subscription to confirm attribute count.
- Decision: Not recommended: Mobilithek access needs an organisation, provider approval and an X.509 machine certificate.
- Terms: BASt: 'Die Nutzung der Mobilithek ist kostenlos.' Subscribing requires an account with an institutional e-mail, membership of a registered organisation (e.g. 'eine Universitätsabteilung'), provider approval (contractOffer.providerApprovalRequired=true for both example offers) and an X.509 machine certificate: 'Um ein Maschinenzertifikat anfordern zu können, müssen Sie mit Ihrer Organisation bereits auf der Mobilithek registriert sein.' Licences of the two example offers: LICENSE_RESTRICTED_USE_FREE_OF_CHARGE. Catalog search for REALTIME_TRAFFIC_DATA returned 100 offers: 44 restricted-free, 37 open-data, 10 other contractual, 8 no licence, 1 fee (TomTom).
  - https://mobilithek.info/offers?categories=%5B%22https%3A%2F%2Fw3id.org%2Fmdp%2Fschema%2Fdata_categories%23REALTIME_TRAFFIC_DATA%22%5D (200): "Mobilithek.info - Mobilitätsdaten Deutschland (JS single-page app)"
  - https://mobilithek.info/mdp-api/mdp-msa-metadata/v2/offers/search?page=0&size=100 (200): "110000000003476000 ... Fahrstreifendaten (Q und v) von Messstellen auf BAB in Nordrhein-Westfalen :: Verkehrsmengen (Q) und Geschwindigkeiten (v) der Pkw, Lkw und Kfz auf Einzelfahrstreifen an rd. 3.500 Messquerschnitten auf BAB in Nordrhein-Westfalen"
  - https://mobilithek.info/mdp-api/mdp-msa-metadata/v2/offers/110000000003476000 (200): "accrualPeriodicity: https://w3id.org/idsa/code/EVERY_1_MINUTE; rights: LICENSE_RESTRICTED_USE_FREE_OF_CHARGE; providerApprovalRequired: true"
  - https://mobilithek.info/mdp-api/mdp-msa-metadata/v2/offers/619101149275615232 (200): "Verkehrsmengen (q) und Geschwindigkeiten (v) der Einzelfahrstreifen von rd. 2.500 Messquerschnitten auf BAB in Hessen; EVERY_1_MINUTE; schemaProfileName Profile_Measurement_Data"
  - https://www.bast.de/DE/Publikationen/Daten/VerhaltenundSicherheit/MDC/Datenbezug/Datenbezug_node.html (200): "Die Nutzung der Mobilithek ist kostenlos. ... Um Datenangebote abonnieren zu können, ist die Zugehörigkeit zu einer Organisation notwendig."
  - https://mobilithek.info/cms/downloads/mtssb-de (200): "Jedes Datennehmersystem muss sich mittels digitalen Zertifikats an der Mobilithek authentisieren."

### 29. Swiss Traffic & Public Transport Data

- Endpoint: opentransportdata.swiss FEDRO Traffic Data Platform: 'Traffic counters (road traffic) - real time API' (DATEX II v2.3 SOAP pullMeasuredData); also GTFS-RT, SIRI-ET, SIRI-SX
- Delivery: poll (SOAP/HTTPS with bearer API key); access: free-key; sign-up: https://opentransportdata.swiss/en/cookbook/development-miscellaneous-cookbook/howto-access-apis/ (API Manager)
- Documented bound: Documented, not measured. Traffic counters: 'The data is updated every minute'; the keyless static MeasurementSiteTable (v30, 2026-10-15) lists 2496 measurementSiteRecords with 29952 measurementSpecificCharacteristics (12 measured values per MSR: flow and speed per vehicle class). One pull returns all MSRs (filter optional) -> 2496/60 = ~41.6 MSR records/s, within 50 req/min. Per MSR record: 12 measured values + site id/version + measurement time (>=15 leaf fields).
- Screen verdict: **qualifies-with-free-key** — Free API key; documented 1-minute updates for 2496 measurement-site records (~41.6 records/s) each carrying 12 measured values; needs key to confirm.
- Decision: Free key needed (opentransportdata.swiss API Manager).
- Terms: 'In principle, you can obtain file and service related data free of charge.' Limits: 'FEDRO TDP: Traffic counters, Traffic lights, Traffic information 50 requests per minute and API-key'; 'GTFS RT, GTFS RT Service Alerts 5 requests per minute and API-key'; SIRI-ET 2/min, 3000/day. FEDRO terms: 'Access to the data is limited to six months.' Must cite 'opentransportdata.swiss' as source. Listed URL https://opentransportdata.swiss/en/group/api-group returns 404.
  - https://opentransportdata.swiss/en/group/api-group (404): "(listed URL not found)"
  - https://opentransportdata.swiss/en/limits-and-costs/ (200): "FEDRO TDP: Traffic counters, Traffic lights, Traffic information 50 requests per minute and API-key"
  - https://opentransportdata.swiss/en/cookbook/road-traffic-cookbook/rt-road-traffic-counters/ (200): "The data is updated every minute and concerns the traffic movements of the previous full minute."
  - https://data.opentransportdata.swiss/dataset/9f2cd216-a6a0-47ca-b498-6893bd911f4b/resource/40f978e1-a181-4010-91af-f723e1973b68/download/measurementsitetable.current_2026-10-15_14-25-160200_v30.xml (200): "2496 <measurementSiteRecord>, 29952 <measurementSpecificCharacteristics>, <period>60.00</period>"
  - https://opentransportdata.swiss/en/cookbook/development-miscellaneous-cookbook/howto-access-apis/ (200): "Registration with your e-mail address, surname, first name and password is required."
  - https://opentransportdata.swiss/en/tac-fedro/ (200): "Access to the data is limited to six months."
  - https://opentransportdata.swiss/en/cookbook/realtime-prediction-cookbook/gtfs-rt/ (200): "Trip updates are provided via a GET request. They are cached for 30 seconds"

### 30. Transport for NSW API

- Endpoint: TfNSW Open Data Hub GTFS-realtime APIs (e.g. 'Public Transport - Realtime Vehicle Positions API' for buses, ferries, light rail, NSW Trains, metro, regional buses; v2 for Sydney Trains/Metro/IWLR)
- Delivery: poll (GTFS-realtime protobuf over HTTPS, API key header); access: free-key; sign-up: https://opendata.transport.nsw.gov.au/developers/userguide
- Documented bound: Documented, not measured. Requests: 5/s throttle, 60,000/day quota (= 0.69 requests/s daily average). Records per response (number of vehicles) and vehicle update frequency are not stated in TfNSW docs -> events/s upper bound undetermined. Attributes: GTFS-realtime VehiclePosition schema (trip.*, vehicle.*, position.*, timestamp, stop_id, ...) has >=10 leaf fields (from GTFS-RT spec; TfNSW extension proto requires login).
- Screen verdict: **undetermined** — Free key; attribute count >=10 per GTFS-RT VehiclePosition schema, but TfNSW documents only request limits, not fleet size or update frequency, so >=1 event/s cannot be shown from documents; needs a key to measure.
- Decision: Free key would settle it.
- Terms: 'The default account plan is the "Bronze Plan", which has the following limits: Quota: 60,000 per day Rate Limit: 5 per second'. Dataset licence: Creative Commons Attribution. Listed api.nsw.gov.au catalogue page shows no APIs inline ('More available at Open Data Hub').
  - https://api.nsw.gov.au/ProductCatalogue?apiCategoryId=2 (200): "Transport APIs ... More available at Open Data Hub"
  - https://opendata.transport.nsw.gov.au/developers/api-basics (200): "The default account plan is the "Bronze Plan", which has the following limits: Quota: 60,000 per day Rate Limit: 5 per second"
  - https://opendata.transport.nsw.gov.au/developers/userguide (200): "Register for an account and log in to the Open Data Hub ... Select 'API Tokens', enter name in the text box and click 'CREATE API TOKEN'"
  - https://opendata.transport.nsw.gov.au/data/dataset/public-transport-realtime-vehicle-positions (200): "Current vehicle positions in GTFS-realtime format for Buses, Ferries, Light..."
  - https://opendata.transport.nsw.gov.au/data/dataset/public-transport-realtime-vehicle-positions-v2 (200): "Current vehicle positions in GTFS-realtime format for Sydney Trains, Metro and Inner West Light Rail. License Creative Commons Attribution"

### 33. Seismic Data (EMSC Seismic Portal)

- Endpoint: wss://www.seismicportal.eu/standing_order/websocket
- Delivery: push (WebSocket); access: keyless
- Measured: {"utc_start": "2026-10-19T00:48:57.953957+00:00", "seconds": 180.2, "events": 2, "events_per_s": 0.0111, "attrs_median": 20, "attrs_max": 20}
- Screen verdict: **fails** — Criterion 3: 2 messages in 180.2 s = 0.011/s. The FDSN catalog query for the full UTC day 2026-10-18 returned 289 events = 0.0033/s. Attributes pass (20).
- Decision: Fails.
- Terms: No key used or requested by the docs page; no rate-limit text found on realtime.html.
  - https://www.seismicportal.eu/realtime.html (200): "Using the Websocket protocol , users can be notified in (near) realtime of new events. A Json message is sent when an event is inserted or updated."
  - https://www.seismicportal.eu/fdsnws/event/1/query?starttime=2026-10-18T00:00:00&endtime=2026-10-19T00:00:00&format=json&limit=5000 (200): "289 features returned for 2026-10-18 UTC (measured)"

### 34. Open Weather API (OpenWeatherMap)

- Endpoint: https://api.openweathermap.org/data/2.5/weather (Current Weather API, needs appid)
- Delivery: poll (REST); access: free-key; sign-up: https://home.openweathermap.org/users/sign_up (linked as 'Get API Key'; not visited)
- Documented bound: documented, not measured: 1,000,000 calls/month / (30 x 86,400 s) = 0.386 calls/s sustained, with one city record per Current Weather call, so at most 0.386 records/s (and only if every call returns a changed record). The 60 calls/min burst ceiling is 1 call/s. Example response has 31 flattened fields. Bulk files exist ('We provide number of bulk files with current weather and forecasts') but their access and price were not verified.
- Screen verdict: **fails** — Criterion 3 (documented): the free monthly quota allows about 0.39 single-location records/s sustained, which is below 1/s. Attributes pass (31 in the documented example). Multi-location or bulk options are undetermined.
- Decision: Fails.
- Terms: Free plan quote: 'Free for everyone Current weather and forecasts 60 API calls/minute, 1,000,000 calls/month'. One Call: 'First 1,000 API calls per day are FREE Each additional call costs 0.0015 USD'.
  - https://openweathermap.org/price (200): "Free Weather API access Free for everyone Current weather and forecasts 60 API calls/minute, 1,000,000 calls/month"
  - https://openweathermap.org/current (200): "Bulk downloading We provide number of bulk files with current weather and forecasts."
  - https://openweathermap.org/api (200): "API product index (fetched)"

### 35. Clima Cell (Tomorrow.io Realtime Weather)

- Endpoint: https://api.tomorrow.io/v4/weather/realtime (needs apikey)
- Delivery: poll (REST); access: free-key; sign-up: https://app.tomorrow.io/signup (not visited)
- Documented bound: documented, not measured: 500 requests/day x 1 location record per response = 0.0058 records/s. The documented response schema has data.time, 20 data.values.* fields and location fields (more than 20 attributes).
- Screen verdict: **fails** — Criterion 3 (documented): about 0.006 records/s on the free plan. Attributes pass (20+).
- Decision: Fails.
- Terms: Free plan: '500 requests per day, 25 requests per hour, 3 requests per second'.
  - https://www.tomorrow.io/a/faq/weather-api/what-is-rate-limiting-in-the-context-of-a-weather-api/ (200): "Specifically, the free plan includes: 500 requests per day, 25 requests per hour, 3 requests per second."
  - https://docs.tomorrow.io/reference/rate-limiting.md (200): "According to your plan, you are limited to a certain amount of requests per hour and day to any of the API endpoints."
  - https://docs.tomorrow.io/reference/realtime-weather (200): "Schema values: cloudBase, cloudCeiling, cloudCover, dewPoint, ... windGust, windSpeed (20 fields)"

### 36. NOAA Buoy Data (NDBC realtime2 / latest_obs)

- Endpoint: https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt (all-station snapshot); https://www.ndbc.noaa.gov/data/realtime2/<STATION>.txt (per station, last 45 days)
- Delivery: poll (flat text files); access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:49.432623+00:00", "seconds": 180.6, "events": 597, "events_per_s": 3.31, "attrs_median": 22, "attrs_max": 22, "notes": "latest_obs window 1 (00:49:49 to 00:52:50 UTC): 597 station rows new or changed in 180.6 s = 3.31/s. Window 2 (from 01:04:10 UTC): 0 in 150.1 s, so the snapshot updates in bursts. Both windows together: 597/330.7 s = 1.81/s. Daily estimate: the realtime2 index lists 945 station .txt files; a random sample of 58 had mean 114.8 rows (median 143) dated 2026-10-18, giving 945 x 114.8 / 86,400 = 1.26/s (a sample estimate, not a full count). Columns: 22 in latest_obs and 19 in realtime2 files. The median number of non-'MM' (non-missing) values per row is 14 in latest_obs and 10 in realtime2."}
- Screen verdict: **qualifies-keyless** — Measured 3.31/s in one 180 s snapshot window (0/s in a second window). The daily average estimated from a 58-station sample is about 1.26/s, which is borderline. 22 columns per observation (median 14 non-missing).
- Decision: Added as `ndbc` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: NDBC FAQ: flat files 'may be downloaded via HTTP, wget, or Perl/LWP'. No rate limit published on the pages fetched; polling was kept at 1 request per 30 s.
  - https://www.ndbc.noaa.gov/faq/rt_data_access.shtml (200): "The Realtime directory data/realtime2 contains the current (last 45 days) data."
  - https://www.ndbc.noaa.gov/data/realtime2/ (200): "index listing 945 station .txt files (measured)"
  - https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt (200): "842 station rows at first poll (measured)"

### 37. NOAA Weather Data (api.weather.gov)

- Endpoint: https://api.weather.gov/alerts/active ; https://api.weather.gov/stations/{stationId}/observations
- Delivery: poll (REST, GeoJSON); access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:49.471492+00:00", "seconds": 150.5, "events": 0, "events_per_s": 0.0, "attrs_median": 44, "attrs_max": 197, "notes": "/alerts/active: 481 alerts, 0 new or changed in 150.5 s. /alerts for the full UTC day 2026-10-18 returned 1,456 alerts, 1,223 of them sent on 2026-10-18 = 0.0142/s. Observations are per station only (no all-station feed in openapi.json paths). The /stations listing was cut off at 40 pages (19,998 stations, so the total is at least that). In 12 sampled stations, 6 had zero observations on 2026-10-18 and the mean was 75.3 per station; a naive extrapolation gives about 17/s produced overall, but collecting them needs one request per station. Observation features have 58 flattened fields (median 7 non-null .value measurements)."}
- Screen verdict: **fails** — Criterion 3: alerts run at 0.014/s (full-day count) and 0/s in the 150 s poll. Observations exist only per station, and with 20k+ stations at 1 request per 10 s (the rate limit is not public) the collectable rate is far below 1/s, e.g. a 1 h cycle covers 360 stations, about 0.3/s.
- Decision: Fails.
- Terms: User-Agent required (used 'ITAM course research <owner e-mail>'). Docs: 'open data, free to use for any purpose'; 'The rate limit is not public information, but allows a generous amount for typical use.'
  - https://www.weather.gov/documentation/services-web-api (200): "The rate limit is not public information, but allows a generous amount for typical use."
  - https://api.weather.gov/openapi.json (200): "paths include /alerts, /alerts/active, /stations/{stationId}/observations, /stations/{stationId}/observations/latest"
  - https://api.weather.gov/alerts?start=2026-10-18T00:00:00Z&end=2026-10-19T00:00:00Z&limit=500 (200): "1,456 alerts over 4 pages (measured)"

### 38. Redfin Realestate (RedfinScraper)

- Endpoint: Library calling Redfin's unofficial 'Stingray' API (no public endpoint documented)
- Delivery: library/scraper; access: none
- Documented bound: undetermined: there is no documented official API or rate. Not measured because the terms prohibit automated querying.
- Screen verdict: **fails** — Criterion 2: the underlying source (Redfin) prohibits automated querying, so it is not free to use. It is a scraper library, not a data service; the event rate is undetermined.
- Decision: Fails.
- Terms: Redfin Terms 2.3.5: 'No Scrubbing or Scraping . You may not automatedly crawl or query the Services for any purpose or by any means'. README: 'Unethical use of this library can result in Redfin taking disciplinary action against your IP address'.
  - https://raw.githubusercontent.com/ryansherby/RedfinScraper/main/README.md (200): "A scalable Python library that leverages Redfin's unofficial Stringray API to quickly scrape real estate data."
  - https://www.redfin.com/about/terms-of-use (200): "You may not automatedly crawl or query the Services for any purpose or by any means (including, without limitation, screen and database scraping, spiders, robots, crawlers ...)"
  - https://github.com/ryansherby/RedfinScraper (200): "repo page"

### 39. EPA AirNow data

- Endpoint: https://files.airnowtech.org/airnow/YYYY/YYYYMMDD/HourlyAQObs_YYYYMMDDHH.dat (keyless file drop); AirNow web services need a free account
- Delivery: file drop (hourly ASCII); access: keyless; sign-up: https://docs.airnowapi.org/account/request/ (needed only for web services)
- Measured: {"utc_start": "2026-10-18T22:00:00Z (start of the hour covered by HourlyAQObs_2026101822.dat; S3 LastModified 2026-10-19T00:41:37Z)", "seconds": 3600, "events": 4415, "events_per_s": 1.226, "attrs_median": 34, "attrs_max": 34, "notes": "File-drop definition: 4,415 site records (4,416 lines including the header) in the hour 2026-10-18 22Z = 1.23/s. The 12Z file also has 4,415 records. 34 columns; median 18 non-empty values per row. The alternative HourlyData_2026101822.dat has 7,677 rows (2.13/s) but only 9 fields, so it fails criterion 4."}
- Screen verdict: **qualifies-keyless** — HourlyAQObs file: 4,415 records per hour = 1.23/s with 34 columns, keyless over HTTPS. Data are preliminary and attribution is required.
- Decision: Not added: correction of the screen. Every hourly HourlyAQObs file of 2026-10-17 23:00 to 2026-10-19 00:00 UTC (25 files read 2026-10-19 01:50 UTC) has exactly 4,415 rows: one per site, reported or not. In the file of 2026-10-18 22:00 UTC only 1,980 rows carry a pollutant value (3,748 values), so the observation rate is 1,980 / 3,600 s = 0.55 events/s (1.04 if each pollutant value were an event, but the per-value HourlyData file has 9 fields).
- Terms: Data Exchange Guidelines: data 'are not fully verified or validated ... should be considered preliminary'; 'Credit should first be given to the appropriate source'; values 'should not be altered in any way'. HourlyAQObs: 'updated once per hour (at ~:35 minutes past the hour). All Hourly AQ Obs files for the preceding 72 hours will be updated every hour'.
  - https://docs.airnowapi.org/ (200): "Access to the AirNow API is available to the public, and new accounts can be acquired via the Log In page."
  - https://docs.airnowapi.org/docs/HourlyAQObsFactSheet.pdf (200): "The data file is updated once per hour (at ~:35 minutes past the hour)."
  - https://docs.airnowapi.org/docs/HourlyDataFactSheet.pdf (200): "The data file is updated twice per hour (at 25 and 55 minutes past the hour)"
  - https://docs.airnowapi.org/docs/DataUseGuidelines.pdf (200): "Credit should first be given to the appropriate source"
  - https://files.airnowtech.org/airnow/2026/20261018/HourlyAQObs_2026101822.dat (200): "4,416 lines (measured)"

### 40. UK Flood Data (EA flood-monitoring)

- Endpoint: https://environment.data.gov.uk/flood-monitoring/data/readings?latest&_view=full
- Delivery: poll / 15-minute snapshot; access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:49.419288+00:00", "seconds": 150.4, "events": 4404, "events_per_s": 29.28, "attrs_median": 14, "attrs_max": 15, "notes": "Poll window 1 spanned a snapshot refresh (Last-Modified 00:33:11 to 00:48:12 GMT): 4,404 of 5,402 readings changed in 150.4 s. That window rate is inflated; spread over the 15-min refresh period it is 4,404/900 s = 4.9/s. Window 2 (01:01:40, _view=full): 0 changes in 126.4 s, between refreshes. Daily estimate: 16 sampled measures had mean 90.6 readings on 2026-10-18 (median 96); 5,402 x 90.6 / 86,400 = 5.7/s. Without _view=full each reading has only 4 fields."}
- Screen verdict: **qualifies-keyless** — About 4.9/s per 15-min snapshot (5.7/s daily sample estimate). 14 flattened fields per reading with _view=full (only 4 without it).
- Decision: Added as `ukflood` (stream-consumers), kept only if its own sampling gives a median of at least 1 event/s.
- Terms: 'provided as open data under the Open Government Licence with no requirement for registration'; required attribution: 'this uses Environment Agency flood and river level data from the real-time data API (Beta)'. Docs advise a single latest call every 15 min. Responses carry 'Cache-Control: max-age=300'.
  - https://environment.data.gov.uk/flood-monitoring/doc/reference (200): "The efficient way to do this is to issue a single call every 15 mins: https://environment.data.gov.uk/flood-monitoring/data/readings?latest"
  - https://environment.data.gov.uk/flood-monitoring/doc/reference (200): "These APIs are provided as open data under the Open Government Licence with no requirement for registration."

### 41. ZipCheckup

- Endpoint: https://api.zipcheckup.com/v1/zip/{zip} (per search-engine copy of the docs)
- Delivery: poll (REST), static ZIP profiles; access: keyless
- Documented bound: documented, not measured: 100 requests/day x 1 ZIP profile = 0.0012 records/s; the data are ZIP-level aggregates materialized in batches, not events.
- Screen verdict: **not-a-stream** — Static per-ZIP safety profiles (example materialized 2026-07-27) with no live event feed; 100 requests/day. Direct access from here was blocked by Cloudflare (HTTP 403).
- Decision: Not a stream.
- Terms: Per search snippet of the docs page: 'Rate limit: 100 requests/day per IP (free tier)'. Example meta 'materialized_at': '2026-07-27...', 'freshness': {'state': 'unknown'}.
  - https://zipcheckup.com/api (403): "Cloudflare 'Sorry, you have been blocked'"
  - https://api.zipcheckup.com/v1 (403): "HTTP 403 from this host; doc text taken from a web-search snippet: 'Rate limit: 100 requests/day per IP (free tier).'"

### 42. US Energy Grid Data (Grid Status)

- Endpoint: https://api.gridstatus.io/v1 (x-api-key required)
- Delivery: poll (REST); access: free-key; sign-up: https://www.gridstatus.io/settings/api
- Documented bound: documented, not measured: 500,000 rows/month / 2,592,000 s = 0.19 rows/s (or 0.39 rows/s if the 1 million/month pricing-page figure applies). Attributes depend on the dataset (undetermined). The separate open-source 'gridstatus' library pulls directly from ISO sites; those sources were not screened here.
- Screen verdict: **fails** — Criterion 2/3 (documented): the free tier caps sustained retrieval at 0.19 to 0.39 rows/s; more requires a paid plan.
- Decision: Fails.
- Terms: gridstatusio README: 'The free plan allows 500,000 rows per month.' Rate limits (Basic): 1 request/s, 30/min, 600/h. A search snippet of the pricing page says Free: 'Export up to 1 Million rows of data per month'.
  - https://raw.githubusercontent.com/gridstatus/gridstatusio/main/README.md (200): "The free plan allows 500,000 rows per month."
  - https://docs.gridstatus.io/grid-status-api/rate-limits.md (200): "Basic | Per Second | 1 requests | Per Minute | 30 requests | Per Hour | 600 requests"
  - https://www.gridstatus.io/datasets (200): "JavaScript app ('You need to enable JavaScript to run this app.')"
  - https://www.gridstatus.io/pricing (200): "JS app; figure from search snippet: 'Export up to 1 Million rows of data per month'"

### 43. USGS Earthquake Real-time Feed

- Endpoint: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
- Delivery: poll (GeoJSON summary feed); access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:49.485310+00:00", "seconds": 180.3, "events": 0, "events_per_s": 0.0, "attrs_median": 32, "attrs_max": 32, "notes": "7 events in all_hour, none new or updated over 4 polls. all_day.geojson (generated 2026-10-19 00:49 UTC) had 227 events in 24 h = 0.0026/s."}
- Screen verdict: **fails** — Criterion 3: 0/s measured; 227 events/day = 0.0026/s. Attributes pass (32).
- Decision: Fails.
- Terms: Feeds 'Updated every minute'. Polled once per 60 s.
  - https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php (200): "Past Hour Updated every minute."
  - https://earthquake.usgs.gov/fdsnws/event/1/ (200): "FDSN event web service docs (fetched)"

### 44. News API

- Endpoint: https://newsapi.org/v2/everything , /v2/top-headlines (apiKey required)
- Delivery: poll (REST); access: free-key; sign-up: https://newsapi.org/register (linked as 'Get API key'; not visited)
- Documented bound: documented, not measured: 100 requests/day x 100 articles = 10,000/day = 0.116 articles/s, delayed 24 h. Article schema: source.id, source.name, author, title, description, url, urlToImage, publishedAt, content = 9 fields.
- Screen verdict: **fails** — Criteria 3 and 4 (documented): at most 0.12 articles/s with a 24 h delay, and 9 fields per article (fewer than 10). Paid plans start at $449/month.
- Decision: Fails.
- Terms: Developer (free): 'For development and testing of all project types'; 'Articles have a 24 hour delay'; '100 requests per day'. pageSize 'Maximum: 100'.
  - https://newsapi.org/pricing (200): "Developer $ 0 ... Articles have a 24 hour delay ... 100 requests per day"
  - https://newsapi.org/docs/endpoints/everything (200): "pageSize int ... Default: 100 . Maximum: 100"
  - https://newsapi.org (200): "home (fetched)"

### 45. New York Times Newswire API

- Endpoint: https://api.nytimes.com/svc/news/v3/content/{source}/{section}.json (api-key required)
- Delivery: poll (REST); access: free-key; sign-up: https://developer.nytimes.com/get-started (not visited)
- Documented bound: documented, not measured: 500 requests/day x 20 articles = 10,000/day = 0.116 articles/s upper bound. The Article schema has 23 top-level properties (more when flattened).
- Screen verdict: **fails** — Criterion 3 (documented): at most 0.12 articles/s under the free key limits. Attributes pass (23+).
- Decision: Fails.
- Terms: FAQ (via search snippet; the portal is a JS app): 'there are two rate limits per API: 500 requests per day and 5 requests per minute'. Spec: limit 'between 1 and 20'.
  - https://developer.nytimes.com/faq (200): "Yes, there are two rate limits per API: 500 requests per day and 5 requests per minute. (text from search snippet; page is a JS app)"
  - https://raw.githubusercontent.com/nytimes/public_api_specs/master/timeswire/timeswire_v3.json (200): "limit: Limits the number of results, between 1 and 20"
  - https://developer.nytimes.com/docs/timeswire-product/1/overview (200): "JS app shell"

### 47. Longevity World Cup

- Endpoint: https://longevityworldcup.com/api/data/athletes
- Delivery: poll (JSON snapshot); access: keyless
- Measured: {"utc_start": "2026-10-19T00:58:34.652246+00:00", "seconds": 180.3, "events": 0, "events_per_s": 0.0, "attrs_median": 54, "attrs_max": 303, "notes": "244 athlete records, identical across 4 polls 60 s apart."}
- Screen verdict: **fails** — Criterion 3: 0 new or changed records in 180 s; it is a slowly changing roster of 244 athletes. Attributes pass (median 54).
- Decision: Fails.
- Terms: Response header 'Cache-Control: public,max-age=60,must-revalidate'; ETag unchanged across polls. Contains athlete profiles (personal data): only field names are reported.
  - https://longevityworldcup.com/api/data/athletes (200): "JSON array of 244 records (measured)"

### 48. ThingSpeak IoT Public Channels

- Endpoint: https://api.thingspeak.com/channels/public.json?page=N (listing); https://api.thingspeak.com/channels/{id}/feeds.json (per channel)
- Delivery: poll (REST per channel); MQTT per channel (not verified); access: keyless
- Measured: {"utc_start": "2026-10-19T00:58:35.099896+00:00", "seconds": 84.9, "events": 9, "events_per_s": 0.106, "attrs_median": 8, "attrs_max": 10, "notes": "90 channels (8 random listing pages) read twice, 84.9 s apart on average: 9 new entries in 5 channels = 0.106/s. Naive extrapolation to all 2,412 public channels gives 2.84/s, but there is no aggregate endpoint, and covering 2,412 channels at 1 request per 10 s takes about 6.7 h per cycle. Feed entries have at most 8 data fields plus created_at and entry_id (median 8 in 100 sampled entries)."}
- Screen verdict: **fails** — Criteria 3 and 4: no firehose; measured 0.106/s across 90 channels, and per-channel collection cannot reach 1/s at a polite rate. Entries have median 8 fields (max 10 by design: 8 fields plus 2 metadata).
- Decision: Fails.
- Terms: Free service 'for non-commercial small projects (<3 million messages/year...)'. No firehose of all public updates found: the listing is paginated metadata (15 per page, 2,412 channels) with last_entry_id per channel. MathWorks docs returned 403.
  - https://api.thingspeak.com/channels/public.json?page=1 (200): "pagination: per_page 15, total_entries 2412 (measured)"
  - https://thingspeak.com/prices (200): "ThingSpeak is available as a free service for non-commercial small projects (<3 million messages/year"
  - https://thingspeak.mathworks.com/pages/license_faq (200): "Users of the free option will be limited to sending no more than 3 million messages each year"
  - https://www.mathworks.com/help/thingspeak/listpublicchannels.html (403): "HTTP 403 (blocked)"
  - https://thingspeak.com/channels/public (200): "public channel HTML listing"

### 50. Certstream

- Endpoint: wss://certstream.calidog.io/ (also /domains-only; HTTP /latest.json, /example.json)
- Delivery: push (WebSocket); access: keyless
- Measured: {"utc_start": "2026-10-19T00:49:27Z", "seconds": 60.1, "events": 0, "events_per_s": 0.0, "attrs_median": 39, "attrs_max": 40}
- Screen verdict: **fails** — Criterion 3: WebSocket handshake succeeds but 0 certificate_update messages in 60.1 s on / (and 0 in 30.1 s on /domains-only). The server's 25-message ring buffer (/latest.json) is frozen at seen=2025-10-31 13:52:56 UTC, so the public service appears stalled for ~1 year. Attribute counts (median 39) come from those stale buffered messages, not from live events.
- Decision: Not added as a separate source: the hosted Certstream service sent nothing; the catalog's `ct` reads the same Certificate Transparency logs directly.
- Terms: No key or terms page found on certstream.calidog.io (page is a JS app). certstream-python README uses url='wss://certstream.calidog.io/'.
  - https://certstream.calidog.io (200): "<title>Certstream</title> (JS single-page app)"
  - https://raw.githubusercontent.com/CaliDog/certstream-python/master/README.md (200): "certstream.listen_for_events(print_callback, url='wss://certstream.calidog.io/')"
  - https://raw.githubusercontent.com/CaliDog/certstream-server/master/README.md (200): "`/latest.json` - Get the most recent 25 certificates CertStream has seen"
  - https://certstream.calidog.io/latest.json (200): "25 messages, data.seen range 2025-10-31 13:52:56.417 to 13:52:56.523 UTC"
  - https://certstream.calidog.io/example.json (200): ""cert_link": "https://ct.googleapis.com/logs/us1/argon2026h1/..."; seen = 2025-10-31 13:52:56 UTC"
  - wss://certstream.calidog.io/ (101): "connected 60.1 s, 0 messages received (capture file 50-certstream.jsonl is empty)"

### 51. URLhaus

- Endpoint: https://urlhaus-api.abuse.ch/v1/ (API, Auth-Key); dumps https://urlhaus-api.abuse.ch/v2/files/exports/<AUTH-KEY>/recent.csv; legacy keyless URL https://urlhaus.abuse.ch/downloads/csv_recent/ still answered 200
- Delivery: file drop (CSV dump regenerated every 5 min) / poll REST; access: free-key; sign-up: https://auth.abuse.ch/
- Measured: {"utc_start": "2026-10-19T00:52Z (single download of csv_recent, 'Last updated: 2026-10-19 00:44:17 (UTC)')", "seconds": 2592000, "events": 33330, "events_per_s": 0.0129, "attrs_median": 9, "attrs_max": 9}
- Screen verdict: **fails** — Criteria 3 and 4: newest dump holds 33,330 URLs added 2026-09-19 00:03:15 to 2026-10-19 00:44:17 (30 days) = 0.0129 records/s (last complete day 2026-10-18: 520 rows = 0.0060/s); each record has 9 columns (<10). File-drop definition applied to the keyless csv_recent dump; the documented API requires a free Auth-Key.
- Decision: Fails.
- Terms: "This API is available free of charge under the fair use principles. Use of the API by companies, networks, or individuals with commercial or for- profit needs may require a paid subscription"; "The dumps are generated every 5 minutes. Please do not fetch it more often than every 5 minutes."
  - https://urlhaus.abuse.ch/api/ (200): "In order to interact with the URLhaus API, you need to obtain an Auth-Key first. If you don't have one you can get one for free here: abuse.ch Authentication Portal"
  - https://urlhaus-api.abuse.ch/v1/urls/recent/limit/3/ (401): "{"error": "Unauthorized"}"
  - https://urlhaus.abuse.ch/downloads/csv_recent/ (200): "# Last updated: 2026-10-19 00:44:17 (UTC) ... # id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter"
  - https://auth.abuse.ch/ (200): "abuse.ch Login"

### 52. CISA Automated Indicator Sharing (AIS)

- Endpoint: Bidirectional AIS TAXII 2.1 server (URL not public; provided at onboarding)
- Delivery: TAXII 2.1 (client poll); access: none
- Documented bound: undetermined (no public volume figure or schema on the AIS page)
- Screen verdict: **fails** — Criterion 2: not a public free account/key. Although "AIS is a no-cost service", access requires contacting CISA, an Interconnection Agreement, providing your IP, and a Federal Bridge CA PKI certificate that you "may need to purchase". Volume and attribute count undetermined (no public endpoint to measure).
- Decision: Fails.
- Terms: Onboarding by email; Terms of Use / MISA; Federal Bridge PKI certificate ("you may need to purchase"); signed Interconnection Agreement and registered IP address.
  - https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/automated-indicator-sharing-ais (200): "AIS is a no-cost service. To participate, please complete the following steps: Contact cyberservices@cisa.dhs.gov ... Get a PKI certificate from a Federal Bridge Certificate Authority (you may need to purchase if you do not have one already). Sign an Interconnection Agreement and provide your IP address to CISA."

### 53. Open Threat Exchange (OTX)

- Endpoint: https://otx.alienvault.com/api/v1/pulses/subscribed?modified_since=... (DirectConnect API, header X-OTX-API-KEY)
- Delivery: poll REST; access: free-key; sign-up: https://otx.alienvault.com/accounts/signup
- Documented bound: Community-wide claim "over 20 million threat indicators contributed daily" (otx.alienvault.com; FAQ variant: 19 million) = ~231 indicators/s (documented, not measured). Reachable share via /pulses/subscribed depends on subscriptions and undocumented rate limits: undetermined. Attributes per documented schema: pulse has 15 properties (id, name, description, author_name, public, revision, adversary, industries, TLP, tags, created, modified, references, targeted_countries, indicators); each indicator has 14 (indicator, type, title, description, created, is_active, access_type, content, role, expiration, id, observations, access_groups, access_reason).
- Screen verdict: **qualifies-with-free-key** — Keyless calls return 403 'Authentication required'. Documents state ~20M indicators/day (~231/s) community-wide and the schema has 14 fields per indicator / 15 per pulse; whether a single free key can actually pull >=1 new indicator/s via subscriptions is not documented and must be confirmed with a key (marketing figure, rate limits unstated).
- Decision: Free key needed (OTX account); the rate figure is a site-wide claim only.
- Terms: No rate limit is stated in the external API documentation (searched for 'rate limit', 'throttl', 'per minute', 'per hour': no hits). /pulses/subscribed returns only pulses from users/groups you subscribe to.
  - https://otx.alienvault.com/api/v1/pulses/subscribed?limit=5 (403): "{"detail": "Authentication required"}"
  - https://otx.alienvault.com/api/v1/search/pulses?q=&sort=-modified&limit=5 (403): "{"detail": "Authentication required"}"
  - https://otx.alienvault.com/assets/static/external_api.html (200): "/api/v1/pulses/subscribed ... modified_since : (string) (optional, iso format datetime (UTC) string) Only include pulses who's modified time is strictly greater than the supplied parameter."
  - https://otx.alienvault.com/ (200): "(JS app; text via search-engine snippet) "Gain FREE access to over 20 million threat indicators contributed daily""
  - https://otx.alienvault.com/api (200): "LevelBlue - Open Threat Exchange (JS app)"

### 54. Shodan Streaming API

- Endpoint: https://stream.shodan.io/shodan/banners?key=... (also /ports, /asn, /countries, /alert)
- Delivery: push (HTTP chunked JSON lines / SSE); access: paid-only
- Documented bound: Full firehose (Enterprise): "On average, 1,200-1,500 banners per second" (documented, not measured). Not available to free accounts.
- Screen verdict: **paid-only** — Streaming API requires a paid API subscription; the all-banner firehose is Enterprise-only. The 'free tier' in the list entry applies to the REST API, not the stream.
- Decision: Paid only.
- Terms: "Only users with an API subscription are able to access the Streaming API." Full firehose labelled Enterprise. Pricing (account.shodan.io/billing) returned 403 Cloudflare challenge to the script; search snippet lists Membership $49 one-time, Freelancer $69/month, etc. Shodan Book: students with academic email get the Membership upgrade (Membership monitors 16 IPs; private-firehose volume for 16 IPs undetermined). "All API plans are subject to a rate limit of 1 request per second".
  - https://developer.shodan.io/api/stream (200): "Data Streams Enterprise GET /shodan/banners Banners This stream provides ALL of the data that Shodan collects."
  - https://book.shodan.io/developer-apis/shodan-api/ (200): "Only users with an API subscription are able to access the Streaming API."
  - https://book.shodan.io/enterprise/real-time-firehose/ (200): "On average, 1,200-1,500 banners per second flow through the firehose."
  - https://developer.shodan.io/api/requirements (200): "To use the API you need to have an API key, which you can get for free by creating a Shodan account."
  - https://book.shodan.io/getting-started/platform/ (200): "Are you a student? Sign-up with your academic email to automatically receive the Membership upgrade."
  - https://account.shodan.io/billing (403): "Just a moment... (Cloudflare challenge)"

### 55. GreyNoise Community API

- Endpoint: https://api.greynoise.io/v3/community/{ip}
- Delivery: request/response IP lookup (no feed); access: keyless
- Measured: {"utc_start": "2026-10-19T00:53Z (one lookup)", "seconds": 0, "events": 1, "events_per_s": null, "attrs_median": 4, "attrs_max": 4}
- Documented bound: <=10 lookups/day keyless (0.000116/s); <=50/week with free key. Documented 200 response fields: ip, noise, riot, classification, name, link, last_seen, message (8).
- Screen verdict: **not-a-stream** — Point lookup of a single IP, not a feed of events; limits of 10/day (keyless) or 50/week (free) and <=8 response fields also fail criteria 3 and 4. Listed URL docs.greynoise.io/reference/community-api returns 404.
- Decision: Not a stream.
- Terms: Unauthenticated: "10 IP lookups per day"; free accounts: "50 lookups per week" and only with a business email ("Accounts created with free email accounts like Hotmail, Gmail ... do not have API key-level access").
  - https://docs.greynoise.io/reference/community-api (404): "GreyNoise (not found page)"
  - https://docs.greynoise.io/docs/using-the-greynoise-community-api (200): "Available to unauthenticated users with a limited number of lookups per day ... "rate-limit": "10 IP lookups per day" ... community / free-level accounts are able to do 50 searches per week"
  - https://api.greynoise.io/v3/community/8.8.8.8 (404): "{"ip": "8.8.8.8", "noise": false, "riot": false, "message": "IP not observed scanning the internet."}"

### 59. AI Detector Arena

- Endpoint: https://lionfish-app-zwr6q.ondigitalocean.app/api/api/v1/benchmark/detectors (and /benchmark/models), found in aidetectarena.com JS bundle
- Delivery: poll REST; access: keyless
- Measured: {"utc_start": "2026-10-19T00:55:22Z", "seconds": 108.7, "events": 0, "events_per_s": 0.0, "attrs_median": 14, "attrs_max": 14}
- Screen verdict: **fails** — Criterion 3: leaderboard of 11 detector records; 0 new/changed records across 8 polls in 108.7 s (15 s interval). A benchmark leaderboard, not an event stream.
- Decision: Fails.
- Terms: No API docs or terms page found on aidetectarena.com; endpoint discovered in /assets/BenchmarkPage-Et2eULlM.js.
  - https://aidetectarena.com (200): "Best AI Detectors 2026 - Accuracy Benchmark & Rankings | AI Detector Arena"
  - https://aidetectarena.com/assets/BenchmarkPage-Et2eULlM.js (200): "N="https://lionfish-app-zwr6q.ondigitalocean.app/api/api/v1" ... fetch(`${N}/benchmark/detectors`"
  - https://lionfish-app-zwr6q.ondigitalocean.app/api/api/v1/benchmark/detectors (200): "{"detectors":[{"id":...,"slug":"winston","eloRating":1377,...}] (11 records)"
  - https://doi.org/10.5281/zenodo.18620634 (200): "Zenodo record (InvenioRDM)"

### 60. World Cup 2026 Tour

- Endpoint: https://ay-worldcup2026.zeabur.app/api/public/v1/{matches,next,today,metadata}
- Delivery: poll REST (static schedule); access: keyless
- Measured: {"utc_start": "2026-10-19T01:15:18Z", "seconds": 126.8, "events": 0, "events_per_s": 0.0, "attrs_median": 25, "attrs_max": 25}
- Screen verdict: **not-a-stream** — Docs: "This public API exposes static schedule data. Live scores and odds remain separate app features." 104 fixed fixtures (version 2026.06.19.23); the tournament ended 2026-07-19 (/next still returns the final with teams 'TBD'); /today returns 0 matches; 0 changes in 126.8 s.
- Decision: Not a stream.
- Terms: "Responses are cacheable for 1 hour. Avoid polling faster than necessary." "Please include a link to World Cup 2026 Tour" (attribution requested). "No API key is required."
  - https://ay-worldcup2026.zeabur.app/developers (200): "It returns static schedule data with optional local-time conversion. ... This public API exposes static schedule data. Live scores and odds remain separate app features. No API key is required."
  - https://ay-worldcup2026.zeabur.app/api/public/v1/matches?timezone=UTC (200): "{"version":"2026.06.19.23","count":104,...} Cache-Control: public, max-age=3600"
  - https://ay-worldcup2026.zeabur.app/api/public/v1/next?timezone=UTC (200): ""match":{"id":104,"stage":"final",..."utc":"2026-07-19T19:00:00.000Z"..."home":{"code":"TBD""
  - https://ay-worldcup2026.zeabur.app/api/public/v1/today?timezone=UTC (200): ""generatedAt":"2026-10-19T00:57:32.873Z" ... "matches":[]"

### 61. GitHub Events

- Endpoint: https://api.github.com/events?per_page=100&page=1..3 (ghapi is a Python wrapper over this REST API)
- Delivery: poll REST (ETag / X-Poll-Interval); access: keyless; sign-up: https://github.com/settings/tokens (free personal access token, optional)
- Measured: {"utc_start": "2026-10-19T00:58:19Z", "seconds": 180.1, "events": 496, "events_per_s": 2.754, "attrs_median": 18, "attrs_max": 277}
- Documented bound: With a free token: X-Poll-Interval 60 s and a 300-event timeline (3 pages x 100) => at most 300 new events per 60 s = 5 events/s (documented, not measured; 3 requests/min = 180/h, within 5,000/h). Keyless sustained: 60 requests/h x 100 events = 6,000 events/h = 1.67 events/s ceiling.
- Screen verdict: **qualifies-keyless** — Measured 496 new event IDs in 180.1 s = 2.75/s (a lower bound: consecutive polls had zero overlap and 5 of 12 page requests returned 502/500); median 18 flattened attributes. Caveats: the measurement used 12 requests in 3 min (keyless budget is 60/h, so keyless sustained capture is capped near 1.67/s); a free token raises the bound to ~5/s; docs warn latency 30 s-6 h.
- Decision: Not added: the same public GitHub events as the catalog's `gharchive` (GH Archive records the events API).
- Terms: "The primary rate limit for unauthenticated requests is 60 requests per hour"; token: "5,000 requests per hour". "There is also an \"X-Poll-Interval\" header that specifies how often (in seconds) you are allowed to poll ... Please obey the header" (observed 60). "The timeline will include up to 300 events." "This API is not built to serve real-time use cases. Depending on the time of day, event latency can be anywhere from 30s to 6h." Events include user logins (personal data).
  - https://github.com/fastai/ghapi (200): "(redirects to AnswerDotAI/ghapi) ghapi provides 100% always-updated coverage of the entire GitHub API"
  - https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28 (200): "The timeline will include up to 300 events. ... per_page integer The number of results per page (max 100)."
  - https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28 (200): "The primary rate limit for unauthenticated requests is 60 requests per hour. ... your personal rate limit of 5,000 requests per hour."
  - https://api.github.com/events?per_page=100&page=1 (200): "X-Poll-Interval: 60; X-RateLimit-Limit: 60"
  - https://api.github.com/events?per_page=100&page=2 (502): "5 of 12 page requests returned 502/500 during the capture"

### 63. Formula 1 Stats & Telemetry (FastF1)

- Endpoint: Library; live source wss://livetiming.formula1.com/signalrcore (SignalR Core); historical: livetiming.formula1.com/static/... and jolpica-f1 (Ergast-compatible) API
- Delivery: push (SignalR) during sessions only; access: paid-only
- Documented bound: Live: undetermined without an F1TV subscription and outside sessions. livetiming.formula1.com/static/StreamingStatus.json = {"Status":"Offline"} at 2026-10-19 ~01:03 UTC; /static/2025/Index.json and /static/2026/Index.json returned 401 keyless. Next session: Austin Practice 1, 2026-10-23 17:30 UTC (per OpenF1 /v1/sessions).
- Screen verdict: **paid-only** — FastF1 is a Python library, not a data service. Its real-time source (F1 live timing SignalR) needs an F1TV subscription token per FastF1's own code; it only carries data during sessions (none on 2026-10-19), and FastF1 states live data cannot be processed in real time. Historical static files now return 401 keyless.
- Decision: Paid only.
- Terms: FastF1 client: 'It is **not** possible to use this data during a session' (saves to file for post-session processing). Live auth token: "An active F1TV subscription is required." no_auth "may only work for some sessions or may only return empty or partial data." Docs: live timing client 'does only support Python 3.8 or 3.9!'
  - https://github.com/theOehrly/Fast-F1 (200): "FastF1 is a python package for accessing and analyzing Formula 1 results, schedules, timing data and telemetry"
  - https://raw.githubusercontent.com/theOehrly/Fast-F1/master/fastf1/livetiming/client.py (200): "_connection_url = "wss://livetiming.formula1.com/signalrcore" ... It is **not** possible to use this data during a session."
  - https://raw.githubusercontent.com/theOehrly/Fast-F1/master/fastf1/internals/f1account/tokens.py (200): ""Access token contains no subscription token. " "An active F1TV subscription is required.""
  - https://docs.fastf1.dev/livetiming.html (200): "The live timing client does only support Python 3.8 or 3.9! ... It is not possible to do real-time processing of the data."
  - https://livetiming.formula1.com/static/StreamingStatus.json (200): "{"Status":"Offline"}"
  - https://livetiming.formula1.com/static/2026/Index.json (401): "(empty body)"

### 64. International Space Station Live Data (ISS Mimic)

- Endpoint: Lightstreamer https://push.lightstreamer.com, adapter set ISSLIVE (TLCP over wss://push.lightstreamer.com/lightstreamer), MERGE subscription of 337 telemetry items used by Mimic
- Delivery: push (Lightstreamer TLCP WebSocket); access: keyless
- Measured: {"utc_start": "2026-10-19T01:05:17Z", "seconds": 120, "events": 0, "events_per_s": 0.0, "attrs_median": 7, "attrs_max": 7}
- Screen verdict: **fails** — Criterion 4 (structural): each pushed update is one telemetry item with 6 schema fields + item id = 7 attributes (Mimic itself subscribes only Value, TimeStamp). Criterion 3 at capture time: only the 337-item initial snapshot arrived, then 0 updates in 120 s; TIME_000001 reported Status.Class=1, which Mimic's code renders as 'Signal Lost' (statuses[1]='Missing'), i.e. loss of signal. A single reading during LOS cannot establish the daily median rate.
- Decision: Fails.
- Terms: No terms page found in the Mimic site; the Mimic page itself connects keylessly: new LightstreamerClient("https://push.lightstreamer.com","ISSLIVE"). Server CONF reported 'unlimited, filtered'.
  - https://iss-mimic.github.io/Mimic/ (200): "var client = new LightstreamerClient("https://push.lightstreamer.com","ISSLIVE"); ... new Subscription("MERGE",[...337 items...],["Value","TimeStamp"]); ... if (status === '24') ... "Signal Acquired!" ... "Signal Lost ""
  - wss://push.lightstreamer.com/lightstreamer (101): "CONOK ... SUBOK,1,337,6 ... CONF,1,unlimited,filtered; 337 snapshot updates in 0.16 s, then 0 updates in 120 s"
  - wss://push.lightstreamer.com/lightstreamer (TIME_000001) (101): "U,1,1,6983.105254999995|25139178918|1  (TimeStamp|Value|Status.Class=1); then only PROBE heartbeats for 60 s"

### 65. Live Satellite Positions (N2YO)

- Endpoint: https://api.n2yo.com/rest/v1/satellite/positions/{id}/{lat}/{lng}/{alt}/{seconds}/&apiKey=...
- Delivery: poll REST; access: free-key; sign-up: https://www.n2yo.com/login/register/
- Documented bound: positions: 1000 transactions/h x up to 300 one-second positions = 300,000 positions/h = 83.3 positions/s (documented, not measured); continuous coverage of one satellite needs 12 calls/h, so ~83 satellites at 1 position/s each. Attributes per position element: 8 (satlatitude, satlongitude, sataltitude, azimuth, elevation, ra, dec, timestamp); response-level info adds satid, satname, transactionscount (11 if merged).
- Screen verdict: **fails** — Criterion 1: positions are model calculations, not observations — docs: "Retrieve the future positions of any satellite ... Each element in the response array is one second of calculation." Also only 8 native attributes per position record (10+ only by copying response-level info into each record).
- Decision: Fails.
- Terms: "The REST API v1 is free but it is transaction limited by type" (per hour: tle 1000, positions 1000, visualpasses 100, radiopasses 100, above 100). "Users are requested not to abuse the system, and not use multiple license keys to get around the hourly transation limit."
  - https://www.n2yo.com/api/ (200): "The REST API v1 is free but it is transaction limited by type . The current limit is: Verb Limit tle 1000 positions 1000 visualpasses 100 radiopasses 100 above 100"
  - https://www.n2yo.com/api/ (200): "seconds integer Yes Number of future positions to return. Each second is a position. Limit 300 seconds"
  - https://www.n2yo.com/login/register/ (200): "<TITLE>N2YO.com register</TITLE>"

### 66. Hacker News

- Endpoint: https://hacker-news.firebaseio.com/v0/maxitem.json + /v0/item/{id}.json (also /v0/updates.json; Firebase supports change notifications)
- Delivery: poll REST (Firebase; push via Firebase clients); access: keyless
- Measured: {"utc_start": "2026-10-19T01:09:40Z", "seconds": 176.7, "events": 13, "events_per_s": 0.074, "attrs_median": 6, "attrs_max": 8}
- Screen verdict: **fails** — Criteria 3 and 4: maxitem grew by 13 in 176.7 s = 0.074 new items/s (Sunday ~01:10 UTC; single short reading); new items had median 6 / max 8 attributes (11 comments: by,id,parent,text,time,type; 2 stories: +descendants,score,title).
- Decision: Fails.
- Terms: "There is currently no rate limit." Items contain usernames ('by').
  - https://github.com/HackerNews/API (200): "In partnership with Firebase, we're making the public Hacker News data available in near real time. ... There is currently no rate limit."
  - https://hacker-news.firebaseio.com/v0/maxitem.json (200): "maxitem polled 18 times at 10 s intervals; +13 over 176.7 s"

### 68. SpaceX API

- Endpoint: https://api.spacexdata.com/v4|v5/launches/latest
- Delivery: poll REST; access: keyless
- Screen verdict: **unreachable** — API host returns Cloudflare errors: v4/launches/latest -> 525, then 522; v5/launches/latest -> 522 (twice). Repository archived; even when up it was a launch catalogue (a few launches per month), not a >=1/s stream.
- Decision: Unreachable.
- Terms: GitHub repository r-spacex/SpaceX-API is archived (last push 2024-08-17).
  - https://github.com/r-spacex/SpaceX-API (200): "Open Source REST API for SpaceX launch, rocket, core, capsule, starlink, launchpad, and landing pad data."
  - https://api.github.com/repos/r-spacex/SpaceX-API (200): ""archived": true, "pushed_at": "2024-08-17T01:38:13Z""
  - https://api.spacexdata.com/v4/launches/latest (525): "error code: 525"
  - https://api.spacexdata.com/v5/launches/latest (522): "error code: 522"

### 69. OpenF1

- Endpoint: https://api.openf1.org/v1/* (REST; live also MQTT/WebSocket for sponsors)
- Delivery: poll REST (free historical); REST/MQTT/WebSocket live (paid); access: paid-only
- Measured: {"utc_start": "2026-10-19T01:03:15Z", "seconds": 60.0, "events": 0, "events_per_s": 0.0, "attrs_median": 11, "attrs_max": 11}
- Documented bound: Live (paid): car telemetry "at 3.7 Hz sampling rate"; historical replay of Singapore race (session 11388) car_data 13:00-13:01 UTC = 5,082 records from 22 drivers in 60 s = 84.7 records/s, 10 attributes each (date, session_key, meeting_key, driver_number, rpm, speed, n_gear, throttle, brake, drs) — that rate exists only during sessions and only paid in real time.
- Screen verdict: **paid-only** — Real-time data is sponsor-only (€9.90/month); free access is historical (made free only 30 min after a session ends). No session on 2026-10-19: last was Singapore race 2026-10-11, next Austin FP1 2026-10-23 17:30 UTC. Free polling of race_control?session_key=latest gave 0 new records in 60 s.
- Decision: Paid only.
- Terms: Free tier: "Historical data | Personal use Free / forever ... No authentication required Up to 3 requests per second and 30 requests per minute". Sponsor €9.90/month: "Live data during sessions with REST, MQTT, and WebSocket". "Data is considered live from 30 minutes before a session starts until 30 minutes after it ends. Outside of this window, data is classified as historical and is free to access."
  - https://openf1.org/ (200): "Community Historical data | Personal use Free / forever ... No authentication required ... Sponsor Historical + Live data | Personal use €9 .90 / month ... Live data during sessions with REST, MQTT, and WebSocket"
  - https://openf1.org/ (200): "Data is considered live from 30 minutes before a session starts until 30 minutes after it ends. Outside of this window, data is classified as historical and is free to access."
  - https://api.openf1.org/v1/sessions?year=2026 (200): "11388 Race Marina Bay 2026-10-11T12:00Z; 11389 Practice 1 Austin 2026-10-23T17:30:00+00:00"
  - https://api.openf1.org/v1/car_data?session_key=11388&date>=2026-10-11T13:00:00&date<2026-10-11T13:01:00 (200): "5082 records, 22 drivers, 10 fields"
  - https://api.openf1.org/v1/race_control?session_key=latest (200): "6 polls / 60 s, 0 new or changed records"

## Notes on the evidence

- Rates of one window are screens: all live windows ran 2026-10-19 00:48–01:37 UTC (Sunday evening in the Americas, night in Europe), so market and filing rates are weekend lows.
- Three quotes come from search-engine snippets because the pages are JavaScript applications or blocked from this host (NYT FAQ, Grid Status pricing, ZipCheckup docs; marked in `results-C.json`), and Finnhub's free-plan quote likewise (`results-A.json`).
- NDBC: `latest_obs.txt` keeps one row per station, so its rate counts stations whose observation time changed between rewrites. Observed Last-Modified values on 2026-10-19: 00:35:51, 00:50:42 (597 stations changed), 00:55:50, 01:40:26, 01:50:25 UTC (`cadence/watch.jsonl`, `captures/36-*`); its 24-round sampling decides.
- The screening agents for entries 6, 20 and 30 used the verdict `undetermined`, which the rules did not define: the evidence fits none of the defined verdicts.

## Addendum 2026-10-19 04:30 UTC — catalog status of the seven sources

The seven sources were published to stream-consumers `main` in commit
`e0ab8dd` (added in `7c93797`) on the owner's decision of 2026-10-19 to
release while their 24-round sampling runs, assuming they pass. Their sampling
`data/reports/sampling-bytewax-20261019/` (started 02:45 UTC, early stop
enabled) had 2 of 24 rounds at 04:30 UTC, so every result is provisional
(`uv run stream-consumers verdict data/reports/sampling-bytewax-20261019 --planned 24`):

| Source | Rounds | Median (events/s) | Verdict |
|---|---|---|---|
| `blockchain` | 2/24 | 4.122 | open |
| `citibike` | 2/24 | 23.563 | open |
| `coinpaprika` | 2/24 | 6.661 | open |
| `ndbc` | 2/24 | 0.418 | open |
| `ogn` | 2/24 | 99.007 | open |
| `sharpe` | 2/24 | 40.419 | open |
| `ukflood` | 2/24 | 4.883 | open |

A source whose final median is below 1 event/s is removed in a follow-up
commit; `ndbc` is the most at risk (both rounds below 1 event/s).

## Addendum 2026-10-19 15:00 UTC — final status of the seven sources

The owner stopped every sampling run at 05:38 UTC on 2026-10-19, so each source
was decided on the rounds it had (`uv run stream-consumers verdict
data/reports/sampling-bytewax-20261019 --planned 24`, read 15:00 UTC; rounds
from 02:45 to 04:45 UTC):

| Source | Rounds | Median (events/s) | Catalog status (stream-consumers `2d5a9e6`) |
|---|---|---|---|
| `blockchain` | 3/24 | 1.795 | passes on 3 rounds (stopped early) |
| `citibike` | 3/24 | 23.368 | passes on 3 rounds (stopped early) |
| `coinpaprika` | 3/24 | 6.662 | passes on 3 rounds (stopped early) |
| `ndbc` | 3/24 | 0.268 | **removed** (below 1 event/s) |
| `ogn` | 3/24 | 115.615 | passes on 3 rounds (stopped early) |
| `sharpe` | 3/24 | 40.396 | passes on 3 rounds (stopped early) |
| `ukflood` | 3/24 | 4.865 | passes on 3 rounds (stopped early) |

Six of the seven stay in the catalog, which now has 66 sources. With 21 rounds
missing, none of these verdicts is certain under the 24-round rule.

This record moved into the stream-consumers repository (`docs/research/`) on
2026-10-19; paths in the sections above that name the course repository or its
worktree refer to where it was written.
