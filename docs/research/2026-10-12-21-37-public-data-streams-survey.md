# Public real-time data streams for the COM-22102 final project — measured survey

- **Generated:** 2026-10-13 03:37 UTC
- **Sampling rounds:** 3 (first 2026-10-13T02:10Z, last 2026-10-13T03:23Z); one round samples every source concurrently.
- **Sources probed:** 61 across 6 categories.
- **Rounds (UTC start):** 20261013T0210, 20261013T0211, 20261013T0323
- **Result:** 32 meet both project requirements on the measured average; 12 meet the rate only; 6 meet the attributes only; 4 meet neither; 7 were not usable as tested.
- **Key-based sources:** see Section 7 (free key with no paid plan, excluded paid/limited plans, and free keys below 1 event/s).

## 1. Requirements and scope

The requirements are quoted from `course-setup/course-documents/03-proyecto-final/proyecto-final-com-22102-otono-2026.pdf` (text extracted with `pdftotext`):

> Los datos del stream deben ser reales. … Cada evento del stream debe contar con al menos 10 atributos distintos. El stream debe producir al menos 1 evento por segundo en promedio. Esta permitido utilizar más de un stream a la vez para conseguir el número de eventos mínimo en promedio.

Excluded because the same document already suggests them: Bluesky Jetstream; Wikimedia EventStreams (recentchange); GDELT; Binance; mempool.space (Bitcoin); aisstream.io; OpenSky Network; Bytewax awesome-public-real-time-datasets list (linked). Overlap with the Bytewax list (linked from the same document) was checked automatically: a source is flagged “yes” when the registered domain of its endpoint, documentation or terms URL appears among the links of the list's README (HTTP 200, 80 distinct domains). Flagged sources are reported, not excluded, because the document links the list without naming them.

## 2. Method

- **Live streams** (WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP, SeedLink): connect, subscribe, count every event for a 60 s window.
- **Polled snapshots** (aircraft, GBFS bike stations, GTFS-Realtime, Entur): poll at the stated interval for 60 s and count records that are new or changed between successive polls — the events a consumer would actually receive.
- **Batch files** (METAR, OSM minutely, GH Archive hourly, Sensor.Community 5-min, Crossref daily, ENA weekly, USGS hourly): events in the file ÷ the period the file covers.
- **Counters** (Certificate Transparency tree size over all 9 usable RFC 6962 logs, npm update sequence, Hacker News max item): growth over a 60 s window.
- **Attributes per event** = number of distinct fields after flattening nested objects (lists count as one field); the table reports the **median per event** over up to 1,000 events per round, plus the maximum and the union across events.
- **Average rate** = mean of the per-round rates; min/median/max show the spread across the day.
- **Links**: every docs and terms URL was fetched live with a browser User-Agent at report time; the HTTP status is shown. Licence/terms evidence is a verbatim excerpt found in that page; “not found” means no matching text was found, not that the data is unlicensed.
- **Personal data**: sample values that identify people (chat users, callsigns, GitHub actors, OSM editors, Nostr keys) are masked as ‹redacted›.

## 3. Master table

| # | Source | Category | Delivery | Access | Avg ev/s | Min – Max ev/s | Attrs/event (median) | Max attrs | Rounds OK | ≥1 ev/s | ≥10 attrs | Verdict | Mexico | In Bytewax list |
|---|---|---|---|---|---:|---|---:|---:|---|:-:|:-:|---|:-:|---|
| 1 | [HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)](#s-hsl) | Transport | live · MQTT over WSS | None | 630.96 | 389.87 – 1,067.97 | 22.0 | 22 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 2 | [Digitraffic Finland marine AIS vessel locations](#s-dt_marine) | Transport | live · MQTT over WSS | None | 31.87 | 31.50 – 32.47 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 3 | [Entur Norway real-time vehicle positions](#s-entur) | Transport | poll · GraphQL over HTTPS (POST), polled every 15 s | None (identifying ET-Client-Name header required) | 16.18 | 3.76 – 31.98 | 19.0 | 19 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 4 | [MBTA Boston GTFS-Realtime VehiclePositions](#s-mbta_gtfsrt) | Transport | poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s | None | 14.10 | 13.08 – 14.88 | 18.0 | 18 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 5 | [NDOV Loket Netherlands public transport KV6 (all operators)](#s-ndov) | Transport | live · ZeroMQ PUB/SUB (gzip XML) | None (best-effort relay) | 4.90 | 1.27 – 12.13 | 15.0 | 16 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 6 | [adsb.fi open data aircraft — 250 NM around Mexico City airport](#s-adsb_fi) | Transport | poll · REST JSON, polled every 5 s | None | 4.62 | 4.00 – 5.24 | 39.0 | 54 | 3/3 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 7 | [Bicing Barcelona bike-share station status (GBFS)](#s-bicing) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 3.48 | 3.17 – 3.73 | 14.0 | 14 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 8 | [EcoBici CDMX bike-share station status (GBFS)](#s-ecobici) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 3.48 | 1.90 – 5.78 | 11.0 | 11 | 3/3 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 9 | [adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport](#s-adsb_lol) | Transport | poll · REST JSON, polled every 15 s | None | 1.82 | 1.48 – 2.12 | 38.0 | 51 | 3/3 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 10 | [NOAA aviationweather.gov METAR observations (global airports)](#s-metar) | Weather & environment | batch · gzip CSV cache file, refreshed every minute | None | 1.35 | 1.33 – 1.37 | 38.0 | 38 | 3/3 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 11 | [RIPE NCC RIS Live — global BGP routing updates](#s-ris) | Internet & software | live · WebSocket (JSON) | None | 861.05 | 98.62 – 2,077.12 | 11.0 | 13 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 12 | [RIPE Atlas measurement results stream (ping)](#s-atlas) | Internet & software | live · WebSocket (JSON) | None | 350.05 | 56.65 – 785.35 | 25.0 | 26 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 13 | [Certificate Transparency logs (RFC 6962), read directly](#s-ct) | Internet & software | counter · REST JSON (get-sth / get-entries) | None | 131.60 | 103.24 – 161.96 | 17.0 | 17 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 14 | [GH Archive — all public GitHub events (hourly files)](#s-gharchive) | Internet & software | batch · Hourly gzip NDJSON over HTTPS | None | 22.34 | 22.07 – 22.88 | 18.0 | 203 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 15 | [PSK Reporter amateur-radio reception reports](#s-pskreporter) | Science & sensors | live · MQTT (TCP 1883) | None | 258.89 | 211.97 – 299.52 | 13.0 | 13 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 16 | [Sensor.Community citizen air-quality sensors](#s-sensorcomm) | Science & sensors | batch · JSON file over HTTPS (last 5 minutes) | None | 58.74 | 58.66 – 58.87 | 17.0 | 25 | 3/3 | ✅ | ✅ | Meets both |  | yes (sensor.community) |
| 17 | [Crossref scholarly metadata (works indexed per day)](#s-crossref) | Science & sensors | batch · REST JSON (cursor paging by index date) | None | 6.49 | 6.47 – 6.50 | 43.0 | 48 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 18 | [EarthScope (IRIS) SeedLink real-time seismic waveforms](#s-seedlink) | Science & sensors | live · SeedLink 3/4 over TCP (miniSEED records) | None | 2.42 | 2.32 – 2.48 | 12.0 | 12 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 19 | [USGS Water Services instantaneous values (river gauges)](#s-usgs_water) | Science & sensors | batch · REST JSON (WaterML-JSON) | None | 1.82 | 1.79 – 1.85 | 26.0 | 26 | 3/3 | ✅ | ✅ | Meets both |  | yes (usgs.gov) |
| 20 | [Polymarket CLOB market channel (prediction-market prices)](#s-polymarket) | Finance & blockchain | live · WebSocket (JSON) | None | 681.75 | 293.63 – 1,343.25 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 21 | [Base (L2) contract event logs (PublicNode RPC)](#s-base_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 298.66 | 123.93 – 391.12 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 22 | [Polygon PoS contract event logs (PublicNode RPC)](#s-polygon_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 285.96 | 151.87 – 417.88 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 23 | [BNB Smart Chain contract event logs (PublicNode RPC)](#s-bsc_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 189.63 | 0.00 – 371.75 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 24 | [Ethereum mainnet contract event logs (PublicNode RPC)](#s-eth_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 83.13 | 71.33 – 93.43 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 25 | [Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)](#s-bitso) | Finance & blockchain | live · WebSocket (JSON) | None | 40.74 | 32.93 – 47.38 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 26 | [OKX public tickers](#s-okx) | Finance & blockchain | live · WebSocket (JSON) | None | 30.81 | 30.27 – 31.42 | 16.0 | 16 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 27 | [XRP Ledger transactions](#s-xrpl) | Finance & blockchain | live · WebSocket (JSON) | None | 22.54 | 17.68 – 26.58 | 20.0 | 27 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 28 | [Coinbase Exchange ticker](#s-coinbase) | Finance & blockchain | live · WebSocket (JSON) | None | 11.36 | 8.17 – 16.42 | 17.0 | 17 | 3/3 | ✅ | ✅ | Meets both |  | yes (coinbase.com) |
| 29 | [Deribit perpetual futures ticker](#s-deribit) | Finance & blockchain | live · JSON-RPC over WebSocket | None | 5.20 | 4.83 – 5.80 | 24.0 | 24 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 30 | [Bitstamp live trades](#s-bitstamp) | Finance & blockchain | live · WebSocket (JSON) | None | 1.66 | 1.43 – 2.05 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 31 | [Twitch chat (anonymous read-only IRC)](#s-twitch) | Games, media & social | live · IRC over WebSocket | Anonymous (justinfan) read-only login | 21.44 | 18.22 – 24.07 | 19.0 | 28 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 32 | [Albion Online Data Project market orders](#s-albion) | Games, media & social | live · NATS (TCP 4222) | Published public credentials | 21.06 | 1.02 – 47.73 | 10.0 | 10 | 3/3 | ✅ | ✅ | Meets both |  | no |
| 33 | [Digitraffic Finland road traffic (TMS) and road-weather sensors](#s-dt_road) | Transport | live · MQTT over WSS | None | 338.37 | 327.33 – 356.93 | 2.0 | 4 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 34 | [Digitraffic Finland train GPS locations](#s-dt_rail) | Transport | live · MQTT over WSS | None | 37.23 | 30.50 – 48.55 | 8.0 | 8 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 35 | [MTA New York City Subway GTFS-Realtime (A/C/E feed)](#s-mta_gtfsrt) | Transport | poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s | None | 4.96 | 4.68 – 5.41 | 6.5 | 9 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | yes (mta.info) |
| 36 | [OpenStreetMap minutely replication diffs](#s-osm) | Internet & software | batch · gzip osmChange XML, one file per minute | None | 28.74 | 6.37 – 52.80 | 9.0 | 294 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 37 | [npm registry replication changes](#s-npm) | Internet & software | counter · CouchDB-style _changes over HTTPS | None | 1.99 | 1.89 – 2.18 | 3.0 | 3 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 38 | [Reverse Beacon Network (CW/RTTY skimmer spots)](#s-rbn) | Science & sensors | live · Telnet text lines | None | 1.42 | 1.23 – 1.65 | 9.0 | 9 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 39 | [Gemini market data v1 (order-book changes + trades)](#s-gemini) | Finance & blockchain | live · WebSocket (JSON) | None | 680.44 | 422.62 – 832.17 | 9.0 | 9 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 40 | [Solana program logs (public mainnet RPC)](#s-solana) | Finance & blockchain | live · JSON-RPC over WebSocket (logsSubscribe) | None (public RPC is rate-limited) | 589.19 | 46.10 – 1,216.87 | 4.0 | 4 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 41 | [Hyperliquid trades](#s-hyperliquid) | Finance & blockchain | live · WebSocket (JSON) | None | 8.89 | 4.87 – 12.12 | 8.0 | 8 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 42 | [Bybit spot tickers](#s-bybit) | Finance & blockchain | live · WebSocket (JSON) | None | 7.61 | 7.08 – 8.40 | 9.0 | 9 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 43 | [Kraken trades + ticker (v2)](#s-kraken) | Finance & blockchain | live · WebSocket (JSON) | None | 7.07 | 4.38 – 9.47 | 7.0 | 14 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 44 | [Bitfinex trades + ticker (public v2)](#s-bitfinex) | Finance & blockchain | live · WebSocket (JSON arrays) | None | 1.80 | 1.33 – 2.47 | 5.0 | 11 | 3/3 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 45 | [Digitraffic Finland train timetables/actuals](#s-dt_rail_trains) | Transport | live · MQTT over WSS | None | 0.98 | 0.82 – 1.23 | 13.0 | 13 | 3/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 46 | [Vélib' Métropole Paris bike-share station status (GBFS)](#s-velib) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 0.87 | 0.81 – 0.93 | 12.0 | 12 | 3/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 47 | [PyPI newest releases feed](#s-pypi) | Internet & software | batch · RSS over HTTPS (+ JSON API per release) | None | 0.10 | 0.09 – 0.10 | 33.0 | 34 | 3/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 48 | [ENA (EMBL-EBI) sequencing runs made public — DNA/genomics](#s-ena) | Science & sensors | batch · REST (ENA Portal API) | None | 0.15 | 0.15 – 0.15 | 196.0 | 196 | 3/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 49 | [Stellar Horizon operations stream](#s-stellar) | Finance & blockchain | live · Server-Sent Events | None | 0.17 | 0.17 – 0.17 | 22.0 | 24 | 3/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 50 | [MLB Stats API live game feed](#s-mlb) | Games, media & social | poll · REST JSON (GUMBO), polled every 10 s | None | 0.06 | 0.05 – 0.06 | 44.0 | 48 | 2/3 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 51 | [Hacker News items (Firebase API)](#s-hn) | Internet & software | counter · REST JSON (also Firebase SSE) | None | 0.14 | 0.08 – 0.20 | 6.0 | 6 | 3/3 | ❌ | ❌ | Neither |  | no |
| 52 | [APRS-IS amateur-radio packet network (full feed)](#s-aprs) | Science & sensors | live · Raw TCP text lines | Read-only login with pass -1 | 0.00 | 0.00 – 0.00 | — | 0 | 3/3 | ❌ | ❌ | Neither |  | no |
| 53 | [BitMEX realtime trade/quote/instrument](#s-bitmex) | Finance & blockchain | live · WebSocket (JSON) | None | 0.00 | 0.00 – 0.00 | — | 0 | 3/3 | ❌ | ❌ | Neither |  | no |
| 54 | [Nostr public notes (kind 1) across 4 relays](#s-nostr) | Games, media & social | live · WebSocket (NIP-01) | None | 0.80 | 0.63 – 1.00 | 7.0 | 7 | 3/3 | ❌ | ❌ | Neither |  | no |
| 55 | [MBTA V3 API vehicle streaming (Server-Sent Events)](#s-mbta_sse) | Transport | live · Server-Sent Events | Returned 406 without a key | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | no |
| 56 | [Kystverket (Norwegian Coastal Administration) open AIS feed](#s-kystverket_ais) | Transport | live · Raw TCP NMEA 0183 (AIVDM) | None | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | yes (kystverket.no) |
| 57 | [airplanes.live aircraft API](#s-airplanes_live) | Transport | poll · REST JSON | Rejected (403): operator asks for an e-mail request | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested | 🇲🇽 | no |
| 58 | [GitHub REST public events (unauthenticated)](#s-github_api) | Internet & software | poll · REST JSON | None, but 60 requests/hour without a token | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | no |
| 59 | [Rubin Observatory LSST alerts via Lasair broker (Kafka)](#s-lasair) | Science & sensors | live · Kafka (kafka.lsst.ac.uk:9092) | Lasair account + saved filter required | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | no |
| 60 | [Mastodon public streaming (mastodon.social)](#s-mastodon) | Games, media & social | live · WebSocket / SSE | Access token required (401) | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | no |
| 61 | [zKillboard (EVE Online kills)](#s-zkillboard) | Games, media & social | live · WebSocket / RedisQ | WebSocket returned 403 to this client | — | — – — | — | — | 0/3 | ❌ | ❌ | Not usable as tested |  | no |

## 4. Endpoints and APIs

| # | Source | Endpoint | Request / subscription | Documentation (HTTP) |
|---|---|---|---|---|
| 1 | HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains) | `wss://mqtt.hsl.fi:443/` | `SUBSCRIBE /hfp/v2/journey/ongoing/vp/#` | [https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/s…](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md) (200) |
| 2 | Digitraffic Finland marine AIS vessel locations | `wss://meri.digitraffic.fi:443/mqtt` | `SUBSCRIBE vessels-v2/+/location (also vessels-v2/+/metadata)` | [https://www.digitraffic.fi/en/marine-traffic/](https://www.digitraffic.fi/en/marine-traffic/) (200) |
| 3 | Entur Norway real-time vehicle positions | `https://api.entur.io/realtime/v2/vehicles/graphql` | `POST {query: vehicles{vehicleId lastUpdated line location speed delay ...}} with header ET-Client-Name` | [https://developer.entur.org/pages-real-time-intro](https://developer.entur.org/pages-real-time-intro) (200) |
| 4 | MBTA Boston GTFS-Realtime VehiclePositions | `https://cdn.mbta.com/realtime/VehiclePositions.pb` | `GET (also TripUpdates.pb, Alerts.pb)` | [https://www.mbta.com/developers/gtfs-realtime](https://www.mbta.com/developers/gtfs-realtime) (200) |
| 5 | NDOV Loket Netherlands public transport KV6 (all operators) | `tcp://pubsub.besteffort.ndovloket.nl:7658` | `SUB '' (all envelopes)` | [https://ndovloket.nl/](https://ndovloket.nl/) (200) |
| 6 | adsb.fi open data aircraft — 250 NM around Mexico City airport | `https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250` | `GET` | [https://github.com/adsbfi/opendata](https://github.com/adsbfi/opendata) (200) |
| 7 | Bicing Barcelona bike-share station status (GBFS) | `https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status` | `GET` | [https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estac…](https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing) (200) |
| 8 | EcoBici CDMX bike-share station status (GBFS) | `https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json` | `GET (station_information.json for names/coordinates)` | [https://ecobici.cdmx.gob.mx/datos-abiertos/](https://ecobici.cdmx.gob.mx/datos-abiertos/) (200) |
| 9 | adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport | `https://api.adsb.lol/v2/point/19.436/-99.072/250` | `GET` | [https://www.adsb.lol/docs/open-data/api/](https://www.adsb.lol/docs/open-data/api/) (200) |
| 10 | NOAA aviationweather.gov METAR observations (global airports) | `https://aviationweather.gov/data/cache/metars.cache.csv.gz` | `GET` | [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/) (200) |
| 11 | RIPE NCC RIS Live — global BGP routing updates | `wss://ris-live.ripe.net/v1/ws/?client=<identifier>` | `{"type":"ris_subscribe","data":{"type":"UPDATE"}}` | [https://ris-live.ripe.net/manual/](https://ris-live.ripe.net/manual/) (200) |
| 12 | RIPE Atlas measurement results stream (ping) | `wss://atlas-stream.ripe.net/stream/?client=<identifier>` | `["atlas_subscribe",{"streamType":"result","type":"ping"}]` | [https://atlas.ripe.net/docs/apis/streaming-api](https://atlas.ripe.net/docs/apis/streaming-api) (200) |
| 13 | Certificate Transparency logs (RFC 6962), read directly | `<log url>/ct/v1/get-sth and /ct/v1/get-entries; log list https://www.gstatic.com/ct/log_list/v3/log_list.json` | `GET` | [https://www.rfc-editor.org/rfc/rfc6962](https://www.rfc-editor.org/rfc/rfc6962) (200) |
| 14 | GH Archive — all public GitHub events (hourly files) | `https://data.gharchive.org/YYYY-MM-DD-H.json.gz` | `GET` | [https://www.gharchive.org/](https://www.gharchive.org/) (200) |
| 15 | PSK Reporter amateur-radio reception reports | `mqtt://mqtt.pskreporter.info:1883` | `SUBSCRIBE pskr/filter/v2/#` | [https://www.mqtt.pskreporter.info/](https://www.mqtt.pskreporter.info/) (200) |
| 16 | Sensor.Community citizen air-quality sensors | `https://data.sensor.community/static/v2/data.json` | `GET` | [https://github.com/opendata-stuttgart/meta/wiki/EN-APIs](https://github.com/opendata-stuttgart/meta/wiki/EN-APIs) (200) |
| 17 | Crossref scholarly metadata (works indexed per day) | `https://api.crossref.org/works?filter=from-index-date:<d>,until-index-date:<d>` | `GET with mailto=` | [https://www.crossref.org/documentation/retrieve-metadata/rest-api/](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) (200) |
| 18 | EarthScope (IRIS) SeedLink real-time seismic waveforms | `tcp://rtserve.iris.washington.edu:18000` | `STATION <sta> <net> / SELECT BHZ / DATA ... END` | [https://ds.iris.edu/ds/nodes/dmc/services/seedlink/](https://ds.iris.edu/ds/nodes/dmc/services/seedlink/) (200) |
| 19 | USGS Water Services instantaneous values (river gauges) | `https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H` | `GET per state` | [https://waterservices.usgs.gov/](https://waterservices.usgs.gov/) (200) |
| 20 | Polymarket CLOB market channel (prediction-market prices) | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | `{"assets_ids":[...],"type":"market"} (ids from https://gamma-api.polymarket.com/markets)` | [https://docs.polymarket.com/developers/CLOB/websocket/market-channel](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) (200) |
| 21 | Base (L2) contract event logs (PublicNode RPC) | `wss://base-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 22 | Polygon PoS contract event logs (PublicNode RPC) | `wss://polygon-bor-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 23 | BNB Smart Chain contract event logs (PublicNode RPC) | `wss://bsc-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 24 | Ethereum mainnet contract event logs (PublicNode RPC) | `wss://ethereum-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 25 | Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN) | `wss://ws.bitso.com` | `{"action":"subscribe","book":"btc_mxn","type":"trades"\|"diff-orders"}` | [https://docs.bitso.com/bitso-api/docs](https://docs.bitso.com/bitso-api/docs) (200) |
| 26 | OKX public tickers | `wss://ws.okx.com:8443/ws/v5/public` | `{"op":"subscribe","args":[{"channel":"tickers","instId":"BTC-USDT"},...]}` | [https://www.okx.com/docs-v5/en/](https://www.okx.com/docs-v5/en/) (200) |
| 27 | XRP Ledger transactions | `wss://xrplcluster.com/` | `{"command":"subscribe","streams":["transactions"]}` | [https://xrpl.org/docs/references/http-websocket-apis/public-api-metho…](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe) (200) |
| 28 | Coinbase Exchange ticker | `wss://ws-feed.exchange.coinbase.com` | `{"type":"subscribe","product_ids":[...],"channels":["ticker"]}` | [https://docs.cdp.coinbase.com/exchange/websocket-feed/overview](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) (200) |
| 29 | Deribit perpetual futures ticker | `wss://www.deribit.com/ws/api/v2` | `public/subscribe ["ticker.BTC-PERPETUAL.100ms", ...]` | [https://docs.deribit.com/](https://docs.deribit.com/) (200) |
| 30 | Bitstamp live trades | `wss://ws.bitstamp.net` | `{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}` | [https://www.bitstamp.net/websocket/v2/](https://www.bitstamp.net/websocket/v2/) (200) |
| 31 | Twitch chat (anonymous read-only IRC) | `wss://irc-ws.chat.twitch.tv:443` | `CAP REQ :twitch.tv/tags; PASS SCHMOOPIIE; NICK justinfanNNNN; JOIN #<channels>` | [https://dev.twitch.tv/docs/chat/irc/](https://dev.twitch.tv/docs/chat/irc/) (200) |
| 32 | Albion Online Data Project market orders | `nats://nats.albion-online-data.com:4222` | `CONNECT user=public pass=thenewalbiondata; SUB marketorders.deduped` | [https://www.albion-online-data.com/](https://www.albion-online-data.com/) (200) |
| 33 | Digitraffic Finland road traffic (TMS) and road-weather sensors | `wss://tie.digitraffic.fi:443/mqtt` | `SUBSCRIBE tms-v2/# and weather-v2/#` | [https://www.digitraffic.fi/en/road-traffic/](https://www.digitraffic.fi/en/road-traffic/) (200) |
| 34 | Digitraffic Finland train GPS locations | `wss://rata.digitraffic.fi:443/mqtt` | `SUBSCRIBE train-locations/#` | [https://www.digitraffic.fi/en/railway-traffic/](https://www.digitraffic.fi/en/railway-traffic/) (200) |
| 35 | MTA New York City Subway GTFS-Realtime (A/C/E feed) | `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace` | `GET (7 more subway feeds: gtfs, -bdfm, -g, -jz, -nqrw, -l, -si)` | [https://api.mta.info/](https://api.mta.info/) (200) |
| 36 | OpenStreetMap minutely replication diffs | `https://planet.openstreetmap.org/replication/minute/NNN/NNN/NNN.osc.gz (state.txt gives the sequence)` | `GET` | [https://wiki.openstreetmap.org/wiki/Planet.osm/diffs](https://wiki.openstreetmap.org/wiki/Planet.osm/diffs) (200) |
| 37 | npm registry replication changes | `https://replicate.npmjs.com/registry/_changes` | `GET ?since=<seq>` | [https://github.com/npm/registry-follower-tutorial](https://github.com/npm/registry-follower-tutorial) (200) |
| 38 | Reverse Beacon Network (CW/RTTY skimmer spots) | `telnet://telnet.reversebeacon.net:7000` | `send any callsign at login` | [https://www.reversebeacon.net/](https://www.reversebeacon.net/) (200) |
| 39 | Gemini market data v1 (order-book changes + trades) | `wss://api.gemini.com/v1/marketdata/<SYMBOL>` | `connect per symbol (no message)` | [https://developer.gemini.com/websocket/streams.md](https://developer.gemini.com/websocket/streams.md) (200) |
| 40 | Solana program logs (public mainnet RPC) | `wss://api.mainnet-beta.solana.com` | `{"method":"logsSubscribe","params":["all",{"commitment":"confirmed"}]}` | [https://solana.com/docs/rpc/websocket/logssubscribe](https://solana.com/docs/rpc/websocket/logssubscribe) (200) |
| 41 | Hyperliquid trades | `wss://api.hyperliquid.xyz/ws` | `{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}}` | [https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/we…](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) (200) |
| 42 | Bybit spot tickers | `wss://stream.bybit.com/v5/public/spot` | `{"op":"subscribe","args":["tickers.BTCUSDT",...]}` | [https://bybit-exchange.github.io/docs/v5/websocket/public/ticker](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) (200) |
| 43 | Kraken trades + ticker (v2) | `wss://ws.kraken.com/v2` | `{"method":"subscribe","params":{"channel":"trade"\|"ticker","symbol":[...]}}` | [https://docs.kraken.com/api/docs/websocket-v2/trade](https://docs.kraken.com/api/docs/websocket-v2/trade) (200) |
| 44 | Bitfinex trades + ticker (public v2) | `wss://api-pub.bitfinex.com/ws/2` | `{"event":"subscribe","channel":"trades"\|"ticker","symbol":"tBTCUSD"}` | [https://docs.bitfinex.com/docs/ws-public](https://docs.bitfinex.com/docs/ws-public) (200) |
| 45 | Digitraffic Finland train timetables/actuals | `wss://rata.digitraffic.fi:443/mqtt` | `SUBSCRIBE trains/#` | [https://www.digitraffic.fi/en/railway-traffic/](https://www.digitraffic.fi/en/railway-traffic/) (200) |
| 46 | Vélib' Métropole Paris bike-share station status (GBFS) | `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json` | `GET` | [https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite…](https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel) (200) |
| 47 | PyPI newest releases feed | `https://pypi.org/rss/updates.xml ; https://pypi.org/pypi/<name>/<version>/json` | `GET` | [https://docs.pypi.org/api/feeds/](https://docs.pypi.org/api/feeds/) (200) |
| 48 | ENA (EMBL-EBI) sequencing runs made public — DNA/genomics | `https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=first_public>=<date>` | `GET` | [https://www.ebi.ac.uk/ena/portal/api/](https://www.ebi.ac.uk/ena/portal/api/) (200) |
| 49 | Stellar Horizon operations stream | `https://horizon.stellar.org/operations?cursor=now` | `GET with Accept: text/event-stream` | [https://developers.stellar.org/docs/data/apis/horizon/api-reference/s…](https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming) (200) |
| 50 | MLB Stats API live game feed | `https://statsapi.mlb.com/api/v1.1/game/<gamePk>/feed/live` | `GET (schedule: /api/v1/schedule?sportId=1&date=...)` | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) (200) |
| 51 | Hacker News items (Firebase API) | `https://hacker-news.firebaseio.com/v0/maxitem.json ; /v0/item/<id>.json` | `GET` | [https://github.com/HackerNews/API](https://github.com/HackerNews/API) (200) |
| 52 | APRS-IS amateur-radio packet network (full feed) | `tcp://rotate.aprs2.net:10152` | `user N0CALL pass -1 vers <app> <ver>` | [https://www.aprs-is.net/Connecting.aspx](https://www.aprs-is.net/Connecting.aspx) (200) |
| 53 | BitMEX realtime trade/quote/instrument | `wss://ws.bitmex.com/realtime` | `{"op":"subscribe","args":["trade:XBTUSD","quote:XBTUSD",...]}` | [https://www.bitmex.com/app/wsAPI](https://www.bitmex.com/app/wsAPI) (200) |
| 54 | Nostr public notes (kind 1) across 4 relays | `wss://nos.lol, wss://relay.primal.net, wss://relay.damus.io, wss://nostr.mom` | `["REQ","sub",{"kinds":[1],"since":<now>}]` | [https://github.com/nostr-protocol/nips/blob/master/01.md](https://github.com/nostr-protocol/nips/blob/master/01.md) (200) |
| 55 | MBTA V3 API vehicle streaming (Server-Sent Events) | `https://api-v3.mbta.com/vehicles?filter[route_type]=0,1,2,3` | `GET with Accept: text/event-stream` | [https://www.mbta.com/developers/v3-api/streaming](https://www.mbta.com/developers/v3-api/streaming) (200) |
| 56 | Kystverket (Norwegian Coastal Administration) open AIS feed | `tcp://153.44.253.27:5631` | `connect and read lines` | [https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ai…](https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/) (200) |
| 57 | airplanes.live aircraft API | `https://api.airplanes.live/v2/point/19.436/-99.072/250` | `GET` | [https://airplanes.live/api-docs/](https://airplanes.live/api-docs/) (200) |
| 58 | GitHub REST public events (unauthenticated) | `https://api.github.com/events` | `GET ?per_page=100` | [https://docs.github.com/en/rest/activity/events](https://docs.github.com/en/rest/activity/events) (200) |
| 59 | Rubin Observatory LSST alerts via Lasair broker (Kafka) | `kafka.lsst.ac.uk:9092 (topic per saved filter)` | `Kafka consumer` | [https://lasair.readthedocs.io/en/main/core_functions/alert-streams.ht…](https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html) (200) |
| 60 | Mastodon public streaming (mastodon.social) | `https://mastodon.social/api/v1/streaming/public` | `GET` | [https://docs.joinmastodon.org/methods/streaming/](https://docs.joinmastodon.org/methods/streaming/) (200) |
| 61 | zKillboard (EVE Online kills) | `wss://zkillboard.com/websocket/` | `{"action":"sub","channel":"killstream"}` | [https://github.com/zKillboard/zKillboard/wiki](https://github.com/zKillboard/zKillboard/wiki) (200) |

## 5. Access, cost and licence evidence

| # | Source | Access | Terms / licence page (HTTP) | Verbatim excerpt |
|---|---|---|---|---|
| 1 | HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains) | None | [https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/s…](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md) (200) | “Digitransit makes the data available based on JHS-189 [permission to use the open data] and [Creative Commons name 4.0 (CC BY)](https://creativecommons.org/licenses/by/4.0/) licensing. CC BY is global, gratuitous, non-exclusive, and non” |
| 2 | Digitraffic Finland marine AIS vessel locations | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 3 | Entur Norway real-time vehicle positions | None (identifying ET-Client-Name header required) | [https://developer.entur.org/pages-intro-setup-and-access/](https://developer.entur.org/pages-intro-setup-and-access/) (200) | “Norwegian Licence for Open Government Data (NLOD)” |
| 4 | MBTA Boston GTFS-Realtime VehiclePositions | None | [https://www.mbta.com/developers/gtfs-realtime](https://www.mbta.com/developers/gtfs-realtime) (200) | “Use of MBTA data is governed by the MassDOT Developers License Agreement” |
| 5 | NDOV Loket Netherlands public transport KV6 (all operators) | None (best-effort relay) | [https://ndovloket.nl/](https://ndovloket.nl/) (200) | “Open Data Bestanden Datasets Realtime Home Projecten FAQ Documentatie Data Incidenten Aanmelden Grenzeloze Openbaar Vervoer Informatie voor Nederland en daar net buiten” |
| 6 | adsb.fi open data aircraft — 250 NM around Mexico City airport | None | [https://raw.githubusercontent.com/adsbfi/opendata/main/README.md](https://raw.githubusercontent.com/adsbfi/opendata/main/README.md) (200) | “Please contact us if you have commercial or higher request rate requirements” |
| 7 | Bicing Barcelona bike-share station status (GBFS) | None | [https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estac…](https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing) (200) | “token")” |
| 8 | EcoBici CDMX bike-share station status (GBFS) | None | [https://ecobici.cdmx.gob.mx/datos-abiertos/](https://ecobici.cdmx.gob.mx/datos-abiertos/) (200) | “GBFS (General Bikeshare Feed Specification)” |
| 9 | adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport | None | [https://www.adsb.lol/docs/open-data/api/](https://www.adsb.lol/docs/open-data/api/) (200) | “ODbL 1” |
| 10 | NOAA aviationweather.gov METAR observations (global airports) | None | [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/) (200) | “Cache This service facilitates machine-to-machine access to aviation weather information” |
| 11 | RIPE NCC RIS Live — global BGP routing updates | None | [https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-co…](https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions) (200) | “Access to and use of the RIPE Data Repository and the Data for any commercial purposes, for example selling the Data or services based on the Data, is not allowed. [these are the RIPE Data Repository terms; the RIS Live manual itself was not found to state separate terms]” |
| 12 | RIPE Atlas measurement results stream (ping) | None | [https://atlas.ripe.net/legal/terms-conditions/](https://atlas.ripe.net/legal/terms-conditions/) (200) | not found |
| 13 | Certificate Transparency logs (RFC 6962), read directly | None | [https://www.rfc-editor.org/rfc/rfc6962](https://www.rfc-editor.org/rfc/rfc6962) (200) | “publicly auditable, append-only, untrusted logs of all issued certificates” |
| 14 | GH Archive — all public GitHub events (hourly files) | None | [https://www.gharchive.org/](https://www.gharchive.org/) (200) | “public GitHub timeline, archive it , and make it easily accessible for further analysis” |
| 15 | PSK Reporter amateur-radio reception reports | None | [https://www.mqtt.pskreporter.info/](https://www.mqtt.pskreporter.info/) (200) | “A real-time MQTT distribution of every spot reported to pskreporter” |
| 16 | Sensor.Community citizen air-quality sensors | None | [https://sensor.community/en/](https://sensor.community/en/) (200) | “DB Contents License [the site footer link 'DB Contents License' points to https://opendatacommons.org/licenses/dbcl/1-0/ (Open Data Commons DbCL v1.0)]” |
| 17 | Crossref scholarly metadata (works indexed per day) | None | [https://www.crossref.org/documentation/retrieve-metadata/rest-api/](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) (200) | “No sign-up is required to use the REST API, and almost none of the metadata is subject to copyright, and you may use it for any purpose” |
| 18 | EarthScope (IRIS) SeedLink real-time seismic waveforms | None | [https://ds.iris.edu/ds/nodes/dmc/services/seedlink/](https://ds.iris.edu/ds/nodes/dmc/services/seedlink/) (200) | “a publicly accessible SeedLink server on the following host and port: host port rtserve” |
| 19 | USGS Water Services instantaneous values (river gauges) | None | [https://waterservices.usgs.gov/](https://waterservices.usgs.gov/) (200) | “decommissioned February 22nd, 2027 WaterServices will be permanently shut down on February 22nd, 2027” |
| 20 | Polymarket CLOB market channel (prediction-market prices) | None | [https://docs.polymarket.com/developers/CLOB/websocket/market-channel](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) (200) | “public market data your application depends on current without repeated polling” |
| 21 | Base (L2) contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 22 | Polygon PoS contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 23 | BNB Smart Chain contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 24 | Ethereum mainnet contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 25 | Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN) | None | [https://docs.bitso.com/bitso-api/docs](https://docs.bitso.com/bitso-api/docs) (200) | “s Look Up Orders Cancel an Order List Fees WEBSOCKET API General Trades Channel Diff-Orders Channel Orders Channel Processed-Orders Channel CONVERSIONS Understanding Conversions Request a Conversion Quote Execut” |
| 26 | OKX public tickers | None | [https://www.okx.com/docs-v5/en/](https://www.okx.com/docs-v5/en/) (200) | “Public Channel Public structure block trades channel Public block trades channel Block tickers” |
| 27 | XRP Ledger transactions | None | [https://xrpl.org/docs/tutorials/public-servers](https://xrpl.org/docs/tutorials/public-servers) (200) | “io/ Full history server cluster with Clio InFTF Mainnet https://xrplcluster” |
| 28 | Coinbase Exchange ticker | None | [https://docs.cdp.coinbase.com/exchange/websocket-feed/overview](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) (200) | “ebSocket Overview Copy page Copy page Copy page Copy page The WebSocket feed is publicly available and provides real-time market data updates for orders and trades” |
| 29 | Deribit perpetual futures ticker | None | [https://docs.deribit.com/](https://docs.deribit.com/) (200) | “agement/private-unsubscribe_all\",\"autogeneratedByOpenApi\":true},{\"title\":\"public/subscribe\",\"description\":\"Subscribe to one or more channels” |
| 30 | Bitstamp live trades | None | [https://www.bitstamp.net/websocket/v2/](https://www.bitstamp.net/websocket/v2/) (200) | not found |
| 31 | Twitch chat (anonymous read-only IRC) | Anonymous (justinfan) read-only login | [https://legal.twitch.com/legal/developer-agreement/](https://legal.twitch.com/legal/developer-agreement/) (200) | “Chat We consider chat to be an essential component of the broadcast experience on Twitch” |
| 32 | Albion Online Data Project market orders | Published public credentials | [https://github.com/ao-data/albiondata-client](https://github.com/ao-data/albiondata-client) (200) | “ternate_user_config_repo","async_conversion_coverage_enabled","billing_billable_licenses_cost_center_bucket_fix","billing_budget_expiration","billing_cost_center_list_assigned_resources","billing_discount_th” |
| 33 | Digitraffic Finland road traffic (TMS) and road-weather sensors | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 34 | Digitraffic Finland train GPS locations | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 35 | MTA New York City Subway GTFS-Realtime (A/C/E feed) | None | [https://www.mta.info/developers](https://www.mta.info/developers) (403) | “Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to apply for a license. [page refuses scripted requests (HTTP 403); text retrieved with the webfetch tool on 2026-10-13]” |
| 36 | OpenStreetMap minutely replication diffs | None | [https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) (200) | “Open Data Commons Open Database License (ODbL) by the OpenStreetMap Foundation (OSMF)” |
| 37 | npm registry replication changes | None | [https://docs.npmjs.com/policies/open-source-terms](https://docs.npmjs.com/policies/open-source-terms) (200) | “rted Setting up your npm user account Creating a new user account on the public registry Creating a strong password Receiving a one-time password over email About two-factor authentication Configuring two-factor authentication Accessing npm using t” |
| 38 | Reverse Beacon Network (CW/RTTY skimmer spots) | None | [https://www.reversebeacon.net/](https://www.reversebeacon.net/) (200) | “lst about A Short History Telnet servers Get Smart About the RBN Who We Are RBN Value Multipliers ARCluster V6 Filtering Red Pitaya, preparing Guide to the new site (beta) How to get spotted b” |
| 39 | Gemini market data v1 (order-book changes + trades) | None | [https://developer.gemini.com/websocket/streams.md](https://developer.gemini.com/websocket/streams.md) (200) | “er ID â an obfuscated alias for the numeric order ID ('i'), safe for external/public display \| \| 'c' \| string \| Client order ID” |
| 40 | Solana program logs (public mainnet RPC) | None (public RPC is rate-limited) | [https://solana.com/docs/references/clusters](https://solana.com/docs/references/clusters) (200) | “Each of these public endpoints are subject to rate limits, but are available for users and developers to interact with the Solana blockchain” |
| 41 | Hyperliquid trades | None | [https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/we…](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) (200) | “: int , fast: boolean (5 levels if fast, 20 levels if slow) Data format: WsBook trades : Subscription message: { &quot;type&quot;: &quot;trades&quot;, &quot;coin&quot;: &quot;&lt;coin_symbol&gt;&quot; } Dat” |
| 42 | Bybit spot tickers | None | [https://bybit-exchange.github.io/docs/v5/websocket/public/ticker](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) (200) | “Spot &amp; Option tickers message are snapshot only Push frequency: Derivatives &amp; Options - 100ms , Spot - 50ms Topic: tickers” |
| 43 | Kraken trades + ticker (v2) | None | [https://docs.kraken.com/api/docs/websocket-v2/trade](https://docs.kraken.com/api/docs/websocket-v2/trade) (200) | “base-ui-disable-scrollbar::-webkit-scrollbar{display:none} Trades - Kraken Developers !function(){var b=""; function a(p){if(p==null)return"/";p=""+p;if(""===p)return"/";return"/"===p” |
| 44 | Bitfinex trades + ticker (public v2) | None | [https://docs.bitfinex.com/docs/ws-public](https://docs.bitfinex.com/docs/ws-public) (200) | “Public Channels {"@context":"https://schema” |
| 45 | Digitraffic Finland train timetables/actuals | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 46 | Vélib' Métropole Paris bike-share station status (GBFS) | None | [https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite…](https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel) (200) | “Licence Open Data Commons Open Database License (ODbL)” |
| 47 | PyPI newest releases feed | None | [https://docs.pypi.org/api/](https://docs.pypi.org/api/) (200) | “s and Datasets Introduction Introduction Table of contents API policies Caching Rate limiting API Preference Integration guide Querying PyPI for Package URLs Official guidance Predictable URLs Index API JSON API Upload API Integrity API Stats API Big” |
| 48 | ENA (EMBL-EBI) sequencing runs made public — DNA/genomics | None | [https://www.ebi.ac.uk/about/terms-of-use/](https://www.ebi.ac.uk/about/terms-of-use/) (200) | “atics Institute (EMBL-EBI) promotes open science through its mission to provide freely available Data Resources and Tools (which includes online services, databases and software) to the largest possible community” |
| 49 | Stellar Horizon operations stream | None | [https://developers.stellar.org/docs/data/apis/horizon/api-reference/s…](https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming) (200) | “Streaming \| Stellar Docs {"@context":"https://schema” |
| 50 | MLB Stats API live game feed | None | [https://gdx.mlb.com/components/copyright.txt](https://gdx.mlb.com/components/copyright.txt) (200) | “Only individual, non-commercial, non-bulk use of the Materials is permitted and any other use of the Materials is prohibited without prior written authorization from MLBAM” |
| 51 | Hacker News items (Firebase API) | None | [https://github.com/HackerNews/API](https://github.com/HackerNews/API) (200) | “There is currently no rate limit” |
| 52 | APRS-IS amateur-radio packet network (full feed) | Read-only login with pass -1 | [https://www.aprs-is.net/Connecting.aspx](https://www.aprs-is.net/Connecting.aspx) (200) | “-1 is used for receive-only” |
| 53 | BitMEX realtime trade/quote/instrument | None | [https://www.bitmex.com/app/wsAPI](https://www.bitmex.com/app/wsAPI) (200) | “You may subscribe to real-time changes on any available table” |
| 54 | Nostr public notes (kind 1) across 4 relays | None | [https://github.com/nostr-protocol/nips/blob/master/01.md](https://github.com/nostr-protocol/nips/blob/master/01.md) (200) | “inds"},{"level":2,"text":"Communication between clients and relays","anchor":"communication-between-clients-and-relays","htmlText":"Communication between clients and relays"},{"level":3” |
| 55 | MBTA V3 API vehicle streaming (Server-Sent Events) | Returned 406 without a key | [https://www.mbta.com/developers/v3-api/streaming](https://www.mbta.com/developers/v3-api/streaming) (200) | “Specify an API key (either with the X-API-Key header or the api_key query parameter)” |
| 56 | Kystverket (Norwegian Coastal Administration) open AIS feed | None | [https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ai…](https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/) (200) | “The data are free and universally accessible, and are regulated under the Norwegian Licence for Open Government Data (NLOD)” |
| 57 | airplanes.live aircraft API | Rejected (403): operator asks for an e-mail request | [https://airplanes.live/terms-of-use/](https://airplanes.live/terms-of-use/) (200) | not found |
| 58 | GitHub REST public events (unauthenticated) | None, but 60 requests/hour without a token | [https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-th…](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) (200) | “60 requests per hour” |
| 59 | Rubin Observatory LSST alerts via Lasair broker (Kafka) | Lasair account + saved filter required | [https://rubinobservatory.org/for-scientists/data-products/alerts-and-…](https://rubinobservatory.org/for-scientists/data-products/alerts-and-brokers) (200) | “world public and have no proprietary period” |
| 60 | Mastodon public streaming (mastodon.social) | Access token required (401) | [https://docs.joinmastodon.org/methods/streaming/](https://docs.joinmastodon.org/methods/streaming/) (200) | “ontend guide Components State management CSS and styling Creating themes Design tokens reference Spec compliance ActivityPub WebFinger Security Microformats OAuth Bearcaps REST API Datetime formats Guideli” |
| 61 | zKillboard (EVE Online kills) | WebSocket returned 403 to this client | [https://github.com/zKillboard/zKillboard/wiki](https://github.com/zKillboard/zKillboard/wiki) (200) | “ref":"/","aria-label":"Homepage "},"notifications":{"indicatorMode":"disabled","websocketChannel":null,"fetchIndicatorSrc":"/notifications/indicator","fetchIndicatorEnabled":false},"issues":{"href":"/issues"},” |

## 6. Per-source detail

<a id="s-hsl"></a>
### 1. HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)

- **Verdict:** Meets both — average 630.96 events/s, median 22.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://mqtt.hsl.fi:443/`
- **Request:** `SUBSCRIBE /hfp/v2/journey/ongoing/vp/#`
- **Access:** None
- **Documentation:** https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md (HTTP 200)
- **Terms / licence:** https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md (HTTP 200) — “Digitransit makes the data available based on JHS-189 [permission to use the open data] and [Creative Commons name 4.0 (CC BY)](https://creativecommons.org/licenses/by/4.0/) licensing. CC BY is global, gratuitous, non-exclusive, and non”
- **Measurement note (latest representative round):** example topic: /hfp/v2/journey/ongoing/vp/tram/0040/00458/100HC3/1/Kuusitie/05:49/1140436/5/60;24/19/82/42

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 389.87 | 23,392 | 60 | 22.0 | 22 | 23 |
| 2026-10-13T02:11 | ok | 435.05 | 26,103 | 60 | 22.0 | 22 | 23 |
| 2026-10-13T03:23 | ok | 1,067.97 | 64,078 | 60 | 22.0 | 22 | 23 |

<details><summary>Sample event — 22 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `desi` | H |
| `dir` | 1 |
| `oper` | 40 |
| `veh` | 458 |
| `tst` | 2026-10-13T02:10:18.256Z |
| `tsi` | 1791857418 |
| `spd` | 0.0 |
| `hdg` | null |
| `lat` | 60.184476 |
| `long` | 24.922378 |
| `acc` | 0.0 |
| `dl` | null |
| `odo` | 0 |
| `drst` | 0 |
| `oday` | 2026-10-13 |
| `jrn` | 33 |
| `line` | 1177 |
| `start` | 05:49 |
| `loc` | GPS |
| `stop` | null |
| `route` | 100HC3 |
| `occu` | 0 |

</details>

<a id="s-dt_marine"></a>
### 2. Digitraffic Finland marine AIS vessel locations

- **Verdict:** Meets both — average 31.87 events/s, median 10.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://meri.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE vessels-v2/+/location (also vessels-v2/+/metadata)`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/marine-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: vessels-v2/636025787/location

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 31.50 | 1,890 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 31.65 | 1,899 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 32.47 | 1,948 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `cog` | 74.9 |
| `heading` | 77 |
| `lat` | 59.721775 |
| `lon` | 24.353438 |
| `navStat` | 0 |
| `posAcc` | true |
| `raim` | false |
| `rot` | 0 |
| `sog` | 11.2 |
| `time` | 1791857417 |

</details>

<a id="s-entur"></a>
### 3. Entur Norway real-time vehicle positions

- **Verdict:** Meets both — average 16.18 events/s, median 19.0 attributes per event.
- **Delivery:** poll · GraphQL over HTTPS (POST), polled every 15 s
- **Endpoint:** `https://api.entur.io/realtime/v2/vehicles/graphql`
- **Request:** `POST {query: vehicles{vehicleId lastUpdated line location speed delay ...}} with header ET-Client-Name`
- **Access:** None (identifying ET-Client-Name header required)
- **Documentation:** https://developer.entur.org/pages-real-time-intro (HTTP 200)
- **Terms / licence:** https://developer.entur.org/pages-intro-setup-and-access/ (HTTP 200) — “Norwegian Licence for Open Government Data (NLOD)”
- **Measurement note (latest representative round):** 2 polls every 15s; 1026 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 3.76 | 290 | 77 | 19.0 | 19 | 20 |
| 2026-10-13T02:11 | ok | 12.79 | 780 | 61 | 19.0 | 19 | 20 |
| 2026-10-13T03:23 | ok | 31.98 | 1,556 | 49 | 19.0 | 19 | 20 |

<details><summary>Sample event — 19 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `vehicleId` | 3620703295 |
| `lastUpdated` | 2026-10-13T02:09:44Z |
| `codespace.codespaceId` | BRA |
| `line.lineRef` | BRA:Line:4_6119 |
| `line.publicCode` | 119 |
| `line.lineName` | Hokksund - Voldstad - Sundet |
| `location.latitude` | 59.7671945951879 |
| `location.longitude` | 9.90892969071865 |
| `bearing` | null |
| `speed` | null |
| `delay` | -11416.0 |
| `occupancyStatus` | noData |
| `vehicleStatus` | ASSIGNED |
| `inCongestion` | false |
| `originName` | Sundet |
| `destinationName` | Vestfossen stasjon |
| `serviceJourney.id` | BRA:ServiceJourney:6119_260630061448489_1014 |
| `operator.operatorRef` | BRA:Operator:61 |
| `mode` | BUS |

</details>

<a id="s-mbta_gtfsrt"></a>
### 4. MBTA Boston GTFS-Realtime VehiclePositions

- **Verdict:** Meets both — average 14.10 events/s, median 18.0 attributes per event.
- **Delivery:** poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s
- **Endpoint:** `https://cdn.mbta.com/realtime/VehiclePositions.pb`
- **Request:** `GET (also TripUpdates.pb, Alerts.pb)`
- **Access:** None
- **Documentation:** https://www.mbta.com/developers/gtfs-realtime (HTTP 200)
- **Terms / licence:** https://www.mbta.com/developers/gtfs-realtime (HTTP 200) — “Use of MBTA data is governed by the MassDOT Developers License Agreement”
- **Measurement note (latest representative round):** 4 polls every 15s; 342 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 13.08 | 848 | 65 | 18.0 | 18 | 20 |
| 2026-10-13T02:11 | ok | 14.33 | 801 | 56 | 18.0 | 18 | 20 |
| 2026-10-13T03:23 | ok | 14.88 | 686 | 46 | 18.0 | 18 | 20 |

<details><summary>Sample event — 18 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | y2078 |
| `vehicle.trip.tripId` | 78273645 |
| `vehicle.trip.startTime` | 21:58:00 |
| `vehicle.trip.startDate` | 20261012 |
| `vehicle.trip.scheduleRelationship` | SCHEDULED |
| `vehicle.trip.routeId` | 111 |
| `vehicle.trip.directionId` | 0 |
| `vehicle.position.latitude` | 42.38946 |
| `vehicle.position.longitude` | -71.03907 |
| `vehicle.position.bearing` | 90.0 |
| `vehicle.currentStopSequence` | 5 |
| `vehicle.currentStatus` | IN_TRANSIT_TO |
| `vehicle.timestamp` | 1791857410 |
| `vehicle.stopId` | 5613 |
| `vehicle.vehicle.id` | y2078 |
| `vehicle.vehicle.label` | 2078 |
| `vehicle.occupancyStatus` | FEW_SEATS_AVAILABLE |
| `vehicle.occupancyPercentage` | 60 |

</details>

<a id="s-ndov"></a>
### 5. NDOV Loket Netherlands public transport KV6 (all operators)

- **Verdict:** Meets both — average 4.90 events/s, median 15.0 attributes per event.
- **Delivery:** live · ZeroMQ PUB/SUB (gzip XML)
- **Endpoint:** `tcp://pubsub.besteffort.ndovloket.nl:7658`
- **Request:** `SUB '' (all envelopes)`
- **Access:** None (best-effort relay)
- **Documentation:** https://ndovloket.nl/ (HTTP 200)
- **Terms / licence:** https://ndovloket.nl/ (HTTP 200) — “Open Data Bestanden Datasets Realtime Home Projecten FAQ Documentatie Data Incidenten Aanmelden Grenzeloze Openbaar Vervoer Informatie voor Nederland en daar net buiten”
- **Measurement note (latest representative round):** KV6 vehicle-journey messages (all operators) on the best-effort ZeroMQ relay

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.30 | 78 | 60 | 15.0 | 16 | 16 |
| 2026-10-13T02:11 | ok | 1.27 | 76 | 60 | 15.0 | 16 | 16 |
| 2026-10-13T03:23 | ok | 12.13 | 728 | 60 | 15.0 | 16 | 19 |

<details><summary>Sample event — 16 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `dataownercode` | CXX |
| `lineplanningnumber` | M097 |
| `operatingday` | 2026-10-12 |
| `journeynumber` | 4007 |
| `reinforcementnumber` | 0 |
| `omloopnumber` | 630103 |
| `userstopcode` | 56330680 |
| `passagesequencenumber` | 0 |
| `timestamp` | 2026-10-13T04:10:18+02:00 |
| `source` | VEHICLE |
| `vehiclenumber` | 9774 |
| `punctuality` | -36 |
| `distancesincelastuserstop` | 1244 |
| `rd-x` | 107981 |
| `rd-y` | 478436 |
| `messagetype` | ONROUTE |

</details>

<a id="s-adsb_fi"></a>
### 6. adsb.fi open data aircraft — 250 NM around Mexico City airport

- **Verdict:** Meets both — average 4.62 events/s, median 39.0 attributes per event.
- **Delivery:** poll · REST JSON, polled every 5 s
- **Endpoint:** `https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/adsbfi/opendata (HTTP 200)
- **Terms / licence:** https://raw.githubusercontent.com/adsbfi/opendata/main/README.md (HTTP 200) — “Please contact us if you have commercial or higher request rate requirements”
- **Measurement note (latest representative round):** 9 polls every 5s; 35 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.61 | 263 | 57 | 39.0 | 54 | 56 |
| 2026-10-13T02:11 | ok | 5.24 | 293 | 56 | 39.0 | 54 | 56 |
| 2026-10-13T03:23 | ok | 4.00 | 230 | 58 | 39.0 | 52 | 57 |

<details><summary>Sample event — 54 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `hex` | ad6b0e |
| `type` | adsb_icao |
| `flight` | AMX014   |
| `r` | N964AM |
| `t` | B788 |
| `desc` | BOEING 787-8 Dreamliner |
| `ownOp` | WILMINGTON TRUST CO TRUSTEE |
| `year` | 2013 |
| `alt_baro` | 39000 |
| `alt_geom` | 41525 |
| `gs` | 472.7 |
| `ias` | 258 |
| `tas` | 482 |
| `mach` | 0.828 |
| `wd` | 66 |
| `ws` | 13 |
| `oat` | -50 |
| `tat` | -19 |
| `track` | 103.33 |
| `track_rate` | 0.0 |
| `roll` | -0.18 |
| `mag_heading` | 100.2 |
| `true_heading` | 102.25 |
| `baro_rate` | 0 |
| `geom_rate` | 0 |
| `squawk` | 3262 |
| `emergency` | none |
| `category` | A5 |
| `nav_qnh` | 1012.8 |
| `nav_altitude_mcp` | 39008 |
| `nav_heading` | 99.84 |
| `nav_modes` | ['autopilot', 'vnav', 'lnav', 'tcas'] |
| `lat` | 18.811981 |
| `lon` | -95.079264 |
| `nic` | 8 |
| `rc` | 186 |
| `seen_pos` | 0.056 |
| `version` | 2 |
| `nic_baro` | 1 |
| `nac_p` | 9 |
| `nac_v` | 1 |
| `sil` | 3 |
| `sil_type` | perhour |
| `gva` | 2 |
| `sda` | 2 |
| `alert` | 0 |
| `spi` | 0 |
| `mlat` | [] |
| `tisb` | [] |
| `messages` | 11920 |
| `seen` | 0.1 |
| `rssi` | -15.8 |
| `dst` | 229.567 |
| `dir` | 98.7 |

</details>

<a id="s-bicing"></a>
### 7. Bicing Barcelona bike-share station status (GBFS)

- **Verdict:** Meets both — average 3.48 events/s, median 14.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing (HTTP 200)
- **Terms / licence:** https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing (HTTP 200) — “token")”
- **Measurement note (latest representative round):** 6 polls every 10s; 543 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 3.73 | 228 | 61 | 14.0 | 14 | 14 |
| 2026-10-13T02:11 | ok | 3.17 | 173 | 54 | 14.0 | 14 | 14 |
| 2026-10-13T03:23 | ok | 3.54 | 182 | 51 | 14.0 | 14 | 14 |

<details><summary>Sample event — 14 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `station_id` | 1 |
| `num_bikes_available` | 14 |
| `num_bikes_disabled` | 5 |
| `is_charging_station` | true |
| `status` | IN_SERVICE |
| `traffic` | null |
| `num_docks_available` | 26 |
| `num_docks_disabled` | 0 |
| `last_reported` | 1791857315 |
| `is_installed` | true |
| `is_renting` | true |
| `is_returning` | true |
| `vehicle_docks_available` | [{'vehicle_type_ids': ['ICONIC', 'BOOST', 'FIT', 'EFIT'], 'count': 26}] |
| `vehicle_types_available` | [{'vehicle_type_id': 'FIT', 'count': 0}, {'vehicle_type_id': 'BOOST', 'count': 4}, {'vehi… |

</details>

<a id="s-ecobici"></a>
### 8. EcoBici CDMX bike-share station status (GBFS)

- **Verdict:** Meets both — average 3.48 events/s, median 11.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json`
- **Request:** `GET (station_information.json for names/coordinates)`
- **Access:** None
- **Documentation:** https://ecobici.cdmx.gob.mx/datos-abiertos/ (HTTP 200)
- **Terms / licence:** https://ecobici.cdmx.gob.mx/datos-abiertos/ (HTTP 200) — “GBFS (General Bikeshare Feed Specification)”
- **Measurement note (latest representative round):** 5 polls every 10s; 677 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.75 | 144 | 52 | 11.0 | 11 | 11 |
| 2026-10-13T02:11 | ok | 5.78 | 322 | 56 | 11.0 | 11 | 11 |
| 2026-10-13T03:23 | ok | 1.90 | 100 | 53 | 11.0 | 11 | 11 |

<details><summary>Sample event — 11 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `station_id` | 1 |
| `num_bikes_available` | 11 |
| `num_bikes_disabled` | 2 |
| `num_docks_available` | 26 |
| `num_docks_disabled` | 0 |
| `is_installed` | 1 |
| `is_renting` | 1 |
| `is_returning` | 1 |
| `last_reported` | 1791857391 |
| `eightd_has_available_keys` | false |
| `is_charging` | false |

</details>

<a id="s-adsb_lol"></a>
### 9. adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport

- **Verdict:** Meets both — average 1.82 events/s, median 38.0 attributes per event.
- **Delivery:** poll · REST JSON, polled every 15 s
- **Endpoint:** `https://api.adsb.lol/v2/point/19.436/-99.072/250`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.adsb.lol/docs/open-data/api/ (HTTP 200)
- **Terms / licence:** https://www.adsb.lol/docs/open-data/api/ (HTTP 200) — “ODbL 1”
- **Measurement note (latest representative round):** 3 polls every 15s; 44 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.86 | 84 | 45 | 38.0 | 51 | 53 |
| 2026-10-13T02:11 | ok | 2.12 | 119 | 56 | 38.0 | 51 | 53 |
| 2026-10-13T03:23 | ok | 1.48 | 70 | 47 | 37.0 | 51 | 54 |

<details><summary>Sample event — 51 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `hex` | ab761e |
| `type` | adsb_icao |
| `flight` | AMX555   |
| `r` | N838AM |
| `t` | B39M |
| `alt_baro` | 36000 |
| `alt_geom` | 38425 |
| `gs` | 470.9 |
| `ias` | 263 |
| `tas` | 466 |
| `mach` | 0.792 |
| `wd` | 142 |
| `ws` | 10 |
| `oat` | -45 |
| `tat` | -17 |
| `track` | 260.96 |
| `track_rate` | 0.0 |
| `roll` | 0.18 |
| `mag_heading` | 257.52 |
| `true_heading` | 259.84 |
| `baro_rate` | 64 |
| `geom_rate` | 32 |
| `squawk` | 0610 |
| `emergency` | none |
| `category` | A3 |
| `nav_qnh` | 1013.6 |
| `nav_altitude_mcp` | 36000 |
| `nav_altitude_fms` | 36000 |
| `nav_heading` | 258.75 |
| `lat` | 19.124451 |
| `lon` | -95.726823 |
| `nic` | 8 |
| `rc` | 186 |
| `seen_pos` | 0.215 |
| `version` | 2 |
| `nic_baro` | 1 |
| `nac_p` | 10 |
| `nac_v` | 2 |
| `sil` | 3 |
| `sil_type` | perhour |
| `gva` | 2 |
| `sda` | 2 |
| `alert` | 0 |
| `spi` | 0 |
| `mlat` | [] |
| `tisb` | [] |
| `messages` | 10146 |
| `seen` | 0.1 |
| `rssi` | -6.7 |
| `dst` | 190.499 |
| `dir` | 95.1 |

</details>

<a id="s-metar"></a>
### 10. NOAA aviationweather.gov METAR observations (global airports)

- **Verdict:** Meets both — average 1.35 events/s, median 38.0 attributes per event.
- **Delivery:** batch · gzip CSV cache file, refreshed every minute
- **Endpoint:** `https://aviationweather.gov/data/cache/metars.cache.csv.gz`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://aviationweather.gov/data/api/ (HTTP 200)
- **Terms / licence:** https://aviationweather.gov/data/api/ (HTTP 200) — “Cache This service facilitates machine-to-machine access to aviation weather information”
- **Measurement note (latest representative round):** cache file lists 5001 stations; rate = observations stamped within the last hour / 3600

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.33 | 4,796 | 3,600 | 38.0 | 38 | 38 |
| 2026-10-13T02:11 | ok | 1.35 | 4,850 | 3,600 | 38.0 | 38 | 38 |
| 2026-10-13T03:23 | ok | 1.37 | 4,920 | 3,600 | 38.0 | 38 | 38 |

<details><summary>Sample event — 38 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `raw_text` | SPECI CYQV 130208Z AUTO 02004KT 1 3/4SM -RA BKN006 OVC012 04/ A2999 RMK DP MISG SLP181 |
| `station_id` | CYQV |
| `observation_time` | 2026-10-13T02:08:00.000Z |
| `latitude` | 51.2600 |
| `longitude` | -102.4610 |
| `temp_c` | 4 |
| `dewpoint_c` |  |
| `wind_dir_degrees` | 20 |
| `wind_speed_kt` | 4 |
| `wind_gust_kt` |  |
| `visibility_statute_mi` | 1.75 |
| `altim_in_hg` | 29.99 |
| `sea_level_pressure_mb` | 1018.1 |
| `corrected` |  |
| `auto` | TRUE |
| `auto_station` |  |
| `maintenance_indicator_on` |  |
| `no_signal` |  |
| `lightning_sensor_off` |  |
| `freezing_rain_sensor_off` |  |
| `present_weather_sensor_off` |  |
| `wx_string` | -RA |
| `sky_cover` |  |
| `cloud_base_ft_agl` |  |
| `flight_category` | IFR |
| `three_hr_pressure_tendency_mb` |  |
| `maxT_c` |  |
| `minT_c` |  |
| `maxT24hr_c` |  |
| `minT24hr_c` |  |
| `precip_in` |  |
| `pcp3hr_in` |  |
| `pcp6hr_in` |  |
| `pcp24hr_in` |  |
| `snow_in` |  |
| `vert_vis_ft` |  |
| `metar_type` | SPECI |
| `elevation_m` | 493 |

</details>

<a id="s-ris"></a>
### 11. RIPE NCC RIS Live — global BGP routing updates

- **Verdict:** Meets both — average 861.05 events/s, median 11.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ris-live.ripe.net/v1/ws/?client=<identifier>`
- **Request:** `{"type":"ris_subscribe","data":{"type":"UPDATE"}}`
- **Access:** None
- **Documentation:** https://ris-live.ripe.net/manual/ (HTTP 200)
- **Terms / licence:** https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions (HTTP 200) — “Access to and use of the RIPE Data Repository and the Data for any commercial purposes, for example selling the Data or services based on the Data, is not allowed. [these are the RIPE Data Repository terms; the RIS Live manual itself was not found to state separate terms]”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 98.62 | 5,917 | 60 | 11.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 407.42 | 24,445 | 60 | 11.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 2,077.12 | 124,627 | 60 | 11.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `timestamp` | 1791857414.62 |
| `peer` | 2001:7f8:30:0:2:1:1:3030 |
| `peer_asn` | 13030 |
| `id` | 2001:7f8:30:0:2:1:1:3030-01a1330651dc0000 |
| `host` | rrc05.ripe.net |
| `type` | UPDATE |
| `path` | [13030, 6939, 4637, 1221, 132847, 154927] |
| `community` | [[6939, 1000], [6939, 7548], [6939, 8826], [6939, 9002], [13030, 51702]] |
| `origin` | IGP |
| `med` | 1 |
| `aggregator` | 154927:163.52.204.1 |
| `announcements` | [{'next_hop': '2001:7f8:30:0:2:1:1:3030,fe80::fe0a:81ff:fefe:2415', 'prefixes': ['2402:76… |
| `withdrawals` | [] |

</details>

<a id="s-atlas"></a>
### 12. RIPE Atlas measurement results stream (ping)

- **Verdict:** Meets both — average 350.05 events/s, median 25.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://atlas-stream.ripe.net/stream/?client=<identifier>`
- **Request:** `["atlas_subscribe",{"streamType":"result","type":"ping"}]`
- **Access:** None
- **Documentation:** https://atlas.ripe.net/docs/apis/streaming-api (HTTP 200)
- **Terms / licence:** https://atlas.ripe.net/legal/terms-conditions/ (HTTP 200) — no matching text found

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 56.65 | 3,399 | 60 | 25.0 | 26 | 26 |
| 2026-10-13T02:11 | ok | 208.15 | 12,489 | 60 | 25.0 | 26 | 26 |
| 2026-10-13T03:23 | ok | 785.35 | 47,121 | 60 | 25.0 | 26 | 26 |

<details><summary>Sample event — 26 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `fw` | 5120 |
| `mver` | 2.6.4 |
| `lts` | 40 |
| `dst_name` | d1.awsstatic.com |
| `ttr` | 66.673208 |
| `af` | 4 |
| `dst_addr` | 13.226.115.78 |
| `src_addr` | 192.168.12.11 |
| `proto` | ICMP |
| `ttl` | 249 |
| `size` | 64 |
| `result` | [{'rtt': 4.857986}, {'rtt': 4.957526}, {'rtt': 4.931453}] |
| `dup` | 0 |
| `rcvd` | 3 |
| `sent` | 3 |
| `min` | 4.857986 |
| `max` | 4.957526 |
| `avg` | 4.915655 |
| `msm_id` | 177401165 |
| `prb_id` | 1015336 |
| `timestamp` | 1791857388 |
| `msm_name` | Ping |
| `from` | 182.52.241.150 |
| `type` | ping |
| `group_id` | 177401165 |
| `step` | 240 |

</details>

<a id="s-ct"></a>
### 13. Certificate Transparency logs (RFC 6962), read directly

- **Verdict:** Meets both — average 131.60 events/s, median 17.0 attributes per event.
- **Delivery:** counter · REST JSON (get-sth / get-entries)
- **Endpoint:** `<log url>/ct/v1/get-sth and /ct/v1/get-entries; log list https://www.gstatic.com/ct/log_list/v3/log_list.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.rfc-editor.org/rfc/rfc6962 (HTTP 200)
- **Terms / licence:** https://www.rfc-editor.org/rfc/rfc6962 (HTTP 200) — “publicly auditable, append-only, untrusted logs of all issued certificates”
- **Measurement note (latest representative round):** 9 RFC 6962 logs (static-CT logs not counted); growth over the window: Google 'Argon2026h2' log: 1381; Google 'Xenon2026h2' log: 1551; Cloudflare 'Nimbus2026': 0; DigiCert 'Wyvern2026h2': 1597; DigiCert 'Sphinx2026h2': 1546; Sectigo 'Elephant2026h2': 0; Sectigo 'Tiger2026h2': 0; TrustAsia 'log2026a': 1254; TrustAsia 'log2026b': 978. Raw entry = leaf_input + extra_data (base64); attributes counted after X.509 decoding of 30 entries.

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 129.59 | 8,307 | 64 | 17.0 | 17 | 17 |
| 2026-10-13T02:11 | ok | 103.24 | 6,595 | 64 | 17.0 | 17 | 17 |
| 2026-10-13T03:23 | ok | 161.96 | 9,894 | 61 | 17.0 | 17 | 17 |

<details><summary>Sample event — 17 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `timestamp_ms` | 1791857354079 |
| `entry_type` | x509 |
| `serial` | 5f4cbfe81911a6c2d03f9e3652096539eda |
| `subject_cn` | null |
| `subject_o` | null |
| `issuer_cn` | YE1 |
| `issuer_o` | Let's Encrypt |
| `issuer_c` | US |
| `not_before` | 2026-10-13T01:10:43+00:00 |
| `not_after` | 2026-10-19T17:10:42+00:00 |
| `san_count` | 0 |
| `san_first` | null |
| `key_type` | ECPublicKey |
| `key_size` | 256 |
| `signature_algorithm` | ecdsa-with-SHA384 |
| `extensions` | 9 |
| `log` | Google 'Argon2026h2' log |

</details>

<a id="s-gharchive"></a>
### 14. GH Archive — all public GitHub events (hourly files)

- **Verdict:** Meets both — average 22.34 events/s, median 18.0 attributes per event.
- **Delivery:** batch · Hourly gzip NDJSON over HTTPS
- **Endpoint:** `https://data.gharchive.org/YYYY-MM-DD-H.json.gz`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.gharchive.org/ (HTTP 200)
- **Terms / licence:** https://www.gharchive.org/ (HTTP 200) — “public GitHub timeline, archive it , and make it easily accessible for further analysis”
- **Measurement note (latest representative round):** hour file 2026-10-12-23 UTC; payload fields vary by event type (union across 1,000 events reported)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 22.07 | 79,440 | 3,600 | 18.0 | 203 | 362 |
| 2026-10-13T02:11 | ok | 22.07 | 79,440 | 3,600 | 18.0 | 203 | 362 |
| 2026-10-13T03:23 | ok | 22.88 | 82,370 | 3,600 | 18.0 | 168 | 378 |

<details><summary>Sample event — 203 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 17051373760 |
| `type` | IssueCommentEvent |
| `actor.id` | ‹redacted› |
| `actor.login` | ‹redacted› |
| `actor.display_login` | ‹redacted› |
| `actor.gravatar_id` | ‹redacted› |
| `actor.url` | ‹redacted› |
| `actor.avatar_url` | ‹redacted› |
| `repo.id` | 1262518964 |
| `repo.name` | Jonathan-Harris1975/HIVE |
| `repo.url` | https://api.github.com/repos/Jonathan-Harris1975/HIVE |
| `payload.action` | ‹redacted› |
| `payload.issue.url` | ‹redacted› |
| `payload.issue.repository_url` | ‹redacted› |
| `payload.issue.labels_url` | ‹redacted› |
| `payload.issue.comments_url` | ‹redacted› |
| `payload.issue.events_url` | ‹redacted› |
| `payload.issue.html_url` | ‹redacted› |
| `payload.issue.id` | ‹redacted› |
| `payload.issue.node_id` | ‹redacted› |
| `payload.issue.number` | ‹redacted› |
| `payload.issue.title` | ‹redacted› |
| `payload.issue.user.login` | ‹redacted› |
| `payload.issue.user.id` | ‹redacted› |
| `payload.issue.user.node_id` | ‹redacted› |
| `payload.issue.user.avatar_url` | ‹redacted› |
| `payload.issue.user.gravatar_id` | ‹redacted› |
| `payload.issue.user.url` | ‹redacted› |
| `payload.issue.user.html_url` | ‹redacted› |
| `payload.issue.user.followers_url` | ‹redacted› |
| `payload.issue.user.following_url` | ‹redacted› |
| `payload.issue.user.gists_url` | ‹redacted› |
| `payload.issue.user.starred_url` | ‹redacted› |
| `payload.issue.user.subscriptions_url` | ‹redacted› |
| `payload.issue.user.organizations_url` | ‹redacted› |
| `payload.issue.user.repos_url` | ‹redacted› |
| `payload.issue.user.events_url` | ‹redacted› |
| `payload.issue.user.received_events_url` | ‹redacted› |
| `payload.issue.user.type` | ‹redacted› |
| `payload.issue.user.user_view_type` | ‹redacted› |
| `payload.issue.user.site_admin` | ‹redacted› |
| `payload.issue.labels` | ‹redacted› |
| `payload.issue.state` | ‹redacted› |
| `payload.issue.locked` | ‹redacted› |
| `payload.issue.assignees` | ‹redacted› |
| `payload.issue.milestone` | ‹redacted› |
| `payload.issue.comments` | ‹redacted› |
| `payload.issue.created_at` | ‹redacted› |
| `payload.issue.updated_at` | ‹redacted› |
| `payload.issue.closed_at` | ‹redacted› |
| `payload.issue.assignee` | ‹redacted› |
| `payload.issue.active_lock_reason` | ‹redacted› |
| `payload.issue.draft` | ‹redacted› |
| `payload.issue.pull_request.url` | ‹redacted› |
| `payload.issue.pull_request.html_url` | ‹redacted› |
| `payload.issue.pull_request.diff_url` | ‹redacted› |
| `payload.issue.pull_request.patch_url` | ‹redacted› |
| `payload.issue.pull_request.merged_at` | ‹redacted› |
| `payload.issue.body` | ‹redacted› |
| `payload.issue.reactions.url` | ‹redacted› |
| `payload.issue.reactions.total_count` | ‹redacted› |
| `payload.issue.reactions.+1` | ‹redacted› |
| `payload.issue.reactions.-1` | ‹redacted› |
| `payload.issue.reactions.laugh` | ‹redacted› |
| `payload.issue.reactions.hooray` | ‹redacted› |
| `payload.issue.reactions.confused` | ‹redacted› |
| `payload.issue.reactions.heart` | ‹redacted› |
| `payload.issue.reactions.rocket` | ‹redacted› |
| `payload.issue.reactions.eyes` | ‹redacted› |
| `payload.issue.timeline_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.id` | ‹redacted› |
| `payload.issue.performed_via_github_app.client_id` | ‹redacted› |
| `payload.issue.performed_via_github_app.slug` | ‹redacted› |
| `payload.issue.performed_via_github_app.node_id` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.login` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.id` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.node_id` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.avatar_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.gravatar_id` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.html_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.followers_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.following_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.gists_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.starred_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.subscriptions_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.organizations_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.repos_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.events_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.received_events_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.type` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.user_view_type` | ‹redacted› |
| `payload.issue.performed_via_github_app.owner.site_admin` | ‹redacted› |
| `payload.issue.performed_via_github_app.name` | ‹redacted› |
| `payload.issue.performed_via_github_app.description` | ‹redacted› |
| `payload.issue.performed_via_github_app.external_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.html_url` | ‹redacted› |
| `payload.issue.performed_via_github_app.created_at` | ‹redacted› |
| `payload.issue.performed_via_github_app.updated_at` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.actions` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.checks` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.contents` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.emails` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.issues` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.metadata` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.pull_requests` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.statuses` | ‹redacted› |
| `payload.issue.performed_via_github_app.permissions.workflows` | ‹redacted› |
| `payload.issue.performed_via_github_app.events` | ‹redacted› |
| `payload.issue.state_reason` | ‹redacted› |
| `payload.comment.url` | ‹redacted› |
| `payload.comment.html_url` | ‹redacted› |
| `payload.comment.issue_url` | ‹redacted› |
| `payload.comment.id` | ‹redacted› |
| `payload.comment.node_id` | ‹redacted› |
| `payload.comment.user.login` | ‹redacted› |
| `payload.comment.user.id` | ‹redacted› |
| `payload.comment.user.node_id` | ‹redacted› |
| `payload.comment.user.avatar_url` | ‹redacted› |
| `payload.comment.user.gravatar_id` | ‹redacted› |
| `payload.comment.user.url` | ‹redacted› |
| `payload.comment.user.html_url` | ‹redacted› |
| `payload.comment.user.followers_url` | ‹redacted› |
| `payload.comment.user.following_url` | ‹redacted› |
| `payload.comment.user.gists_url` | ‹redacted› |
| `payload.comment.user.starred_url` | ‹redacted› |
| `payload.comment.user.subscriptions_url` | ‹redacted› |
| `payload.comment.user.organizations_url` | ‹redacted› |
| `payload.comment.user.repos_url` | ‹redacted› |
| `payload.comment.user.events_url` | ‹redacted› |
| `payload.comment.user.received_events_url` | ‹redacted› |
| `payload.comment.user.type` | ‹redacted› |
| `payload.comment.user.user_view_type` | ‹redacted› |
| `payload.comment.user.site_admin` | ‹redacted› |
| `payload.comment.created_at` | ‹redacted› |
| `payload.comment.updated_at` | ‹redacted› |
| `payload.comment.body` | ‹redacted› |
| `payload.comment.reactions.url` | ‹redacted› |
| `payload.comment.reactions.total_count` | ‹redacted› |
| `payload.comment.reactions.+1` | ‹redacted› |
| `payload.comment.reactions.-1` | ‹redacted› |
| `payload.comment.reactions.laugh` | ‹redacted› |
| `payload.comment.reactions.hooray` | ‹redacted› |
| `payload.comment.reactions.confused` | ‹redacted› |
| `payload.comment.reactions.heart` | ‹redacted› |
| `payload.comment.reactions.rocket` | ‹redacted› |
| `payload.comment.reactions.eyes` | ‹redacted› |
| `payload.comment.performed_via_github_app.id` | ‹redacted› |
| `payload.comment.performed_via_github_app.client_id` | ‹redacted› |
| `payload.comment.performed_via_github_app.slug` | ‹redacted› |
| `payload.comment.performed_via_github_app.node_id` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.login` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.id` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.node_id` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.avatar_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.gravatar_id` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.html_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.followers_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.following_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.gists_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.starred_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.subscriptions_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.organizations_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.repos_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.events_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.received_events_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.type` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.user_view_type` | ‹redacted› |
| `payload.comment.performed_via_github_app.owner.site_admin` | ‹redacted› |
| `payload.comment.performed_via_github_app.name` | ‹redacted› |
| `payload.comment.performed_via_github_app.description` | ‹redacted› |
| `payload.comment.performed_via_github_app.external_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.html_url` | ‹redacted› |
| `payload.comment.performed_via_github_app.created_at` | ‹redacted› |
| `payload.comment.performed_via_github_app.updated_at` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.actions` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.administration` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.artifact_metadata` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.attestations` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.checks` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.code_quality` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.contents` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.copilot_requests` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.deployments` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.discussions` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.drives` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.issues` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.merge_queues` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.metadata` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.models` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.packages` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.pages` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.pull_requests` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.repository_hooks` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.repository_projects` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.security_events` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.statuses` | ‹redacted› |
| `payload.comment.performed_via_github_app.permissions.vulnerability_alerts` | ‹redacted› |
| `payload.comment.performed_via_github_app.events` | ‹redacted› |
| `payload.comment.minimized` | ‹redacted› |
| `public` | true |
| `created_at` | 2026-10-12T23:00:06Z |

</details>

<a id="s-pskreporter"></a>
### 15. PSK Reporter amateur-radio reception reports

- **Verdict:** Meets both — average 258.89 events/s, median 13.0 attributes per event.
- **Delivery:** live · MQTT (TCP 1883)
- **Endpoint:** `mqtt://mqtt.pskreporter.info:1883`
- **Request:** `SUBSCRIBE pskr/filter/v2/#`
- **Access:** None
- **Documentation:** https://www.mqtt.pskreporter.info/ (HTTP 200)
- **Terms / licence:** https://www.mqtt.pskreporter.info/ (HTTP 200) — “A real-time MQTT distribution of every spot reported to pskreporter”
- **Measurement note (latest representative round):** example topic: pskr/filter/v2/160m/FT8/AI4UC/K3LR.D/FM19/EN91/291/291

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 265.20 | 15,912 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 299.52 | 17,971 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 211.97 | 12,718 | 60 | 13.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `sq` | 73663134648 |
| `f` | 1840200 |
| `md` | FT8 |
| `rp` | 34 |
| `t` | 1791857355 |
| `t_tx` | 1791857340 |
| `sc` | ‹redacted› |
| `sl` | ‹redacted› |
| `rc` | ‹redacted› |
| `rl` | ‹redacted› |
| `sa` | 291 |
| `ra` | 291 |
| `b` | 160m |

</details>

<a id="s-sensorcomm"></a>
### 16. Sensor.Community citizen air-quality sensors

- **Verdict:** Meets both — average 58.74 events/s, median 17.0 attributes per event.
- **Delivery:** batch · JSON file over HTTPS (last 5 minutes)
- **Endpoint:** `https://data.sensor.community/static/v2/data.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/opendata-stuttgart/meta/wiki/EN-APIs (HTTP 200)
- **Terms / licence:** https://sensor.community/en/ (HTTP 200) — “DB Contents License [the site footer link 'DB Contents License' points to https://opendatacommons.org/licenses/dbcl/1-0/ (Open Data Commons DbCL v1.0)]”
- **Measurement note (latest representative round):** file = last 5 minutes of all sensors; sensordatavalues expanded per value_type

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 58.66 | 17,599 | 300 | 17.0 | 25 | 33 |
| 2026-10-13T02:11 | ok | 58.68 | 17,603 | 300 | 17.0 | 25 | 33 |
| 2026-10-13T03:23 | ok | 58.87 | 17,661 | 300 | 17.0 | 25 | 33 |

<details><summary>Sample event — 25 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 31016224013 |
| `sampling_rate` | null |
| `timestamp` | 2026-10-13 02:08:11 |
| `location.id` | 980 |
| `location.latitude` | 43.794 |
| `location.longitude` | 11.212 |
| `location.altitude` | 38.1 |
| `location.country` | IT |
| `location.exact_location` | 0 |
| `location.indoor` | 0 |
| `sensor.id` | 1959 |
| `sensor.pin` | 1 |
| `sensor.sensor_type.id` | 14 |
| `sensor.sensor_type.name` | SDS011 |
| `sensor.sensor_type.manufacturer` | Nova Fitness |
| `value.N05` | 15.17 |
| `value.N1` | 17.24 |
| `value.N10` | 17.28 |
| `value.N25` | 17.27 |
| `value.N4` | 17.28 |
| `value.P0` | 2.16 |
| `value.P1` | 2.29 |
| `value.P2` | 2.29 |
| `value.P4` | 2.29 |
| `value.TS` | 0.46 |

</details>

<a id="s-crossref"></a>
### 17. Crossref scholarly metadata (works indexed per day)

- **Verdict:** Meets both — average 6.49 events/s, median 43.0 attributes per event.
- **Delivery:** batch · REST JSON (cursor paging by index date)
- **Endpoint:** `https://api.crossref.org/works?filter=from-index-date:<d>,until-index-date:<d>`
- **Request:** `GET with mailto=`
- **Access:** None
- **Documentation:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/ (HTTP 200)
- **Terms / licence:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/ (HTTP 200) — “No sign-up is required to use the REST API, and almost none of the metadata is subject to copyright, and you may use it for any purpose”
- **Measurement note (latest representative round):** 2026-10-12: 561170 records (re)indexed, of which 39951 newly created (0.462/s)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 6.50 | 561,204 | 86,400 | 43.0 | 45 | 60 |
| 2026-10-13T02:11 | ok | 6.50 | 561,170 | 86,400 | 45.0 | 48 | 59 |
| 2026-10-13T03:23 | ok | 6.47 | 558,644 | 86,400 | 41.5 | 47 | 59 |

<details><summary>Sample event — 48 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `indexed.date-parts` | [[2026, 10, 12]] |
| `indexed.date-time` | 2026-10-12T00:11:22Z |
| `indexed.timestamp` | 1791763882784 |
| `indexed.version` | 4.3.4 |
| `reference-count` | 55 |
| `publisher` | The Royal Society |
| `issue` | 1955 |
| `license` | [{'start': {'date-parts': [[2021, 7, 21]], 'date-time': '2021-07-21T00:00:00Z', 'timestam… |
| `funder` | [{'name': 'Newkirk Center for Science and Society'}, {'name': 'UCI OCEANS Graduate Resear… |
| `content-domain.domain` | ['royalsocietypublishing.org'] |
| `content-domain.crossmark-restriction` | true |
| `short-container-title` | ['Proc. R. Soc. B.'] |
| `published-print.date-parts` | [[2021, 7, 28]] |
| `abstract` | <jats:p>Looking to nature for inspiration has led to many diverse technological advances.… |
| `DOI` | 10.1098/rspb.2021.1359 |
| `type` | journal-article |
| `created.date-parts` | [[2021, 7, 21]] |
| `created.date-time` | 2021-07-21T07:06:19Z |
| `created.timestamp` | 1626851179000 |
| `page` | 20211359 |
| `update-policy` | https://doi.org/10.1098/crossmark-policy |
| `source` | Crossref |
| `is-referenced-by-count` | 28 |
| `title` | ['Shark spiral intestines may operate as Tesla valves'] |
| `prefix` | 10.1098 |
| `volume` | 288 |
| `author` | ‹redacted› |
| `member` | 175 |
| `published-online.date-parts` | [[2021, 7, 21]] |
| `reference` | [{'key': 'e_1_3_6_2_2', 'doi-asserted-by': 'publisher', 'DOI': '10.1126/sciadv.aat9533'},… |
| `container-title` | ['Proceedings of the Royal Society B: Biological Sciences'] |
| `language` | en |
| `link` | [{'URL': 'https://royalsocietypublishing.org/doi/pdf/10.1098/rspb.2021.1359', 'content-ty… |
| `deposited.date-parts` | [[2021, 7, 21]] |
| `deposited.date-time` | 2021-07-21T07:08:45Z |
| `deposited.timestamp` | 1626851325000 |
| `score` | 0.0 |
| `resource.primary.URL` | https://royalsocietypublishing.org/doi/10.1098/rspb.2021.1359 |
| `issued.date-parts` | [[2021, 7, 21]] |
| `references-count` | 55 |
| `journal-issue.issue` | 1955 |
| `journal-issue.published-print.date-parts` | [[2021, 7, 28]] |
| `alternative-id` | ['10.1098/rspb.2021.1359'] |
| `URL` | https://doi.org/10.1098/rspb.2021.1359 |
| `ISSN` | ['0962-8452', '1471-2954'] |
| `issn-type` | [{'value': '0962-8452', 'type': 'print'}, {'value': '1471-2954', 'type': 'electronic'}] |
| `published.date-parts` | [[2021, 7, 21]] |
| `assertion` | [{'value': '2021-06-14', 'order': 0, 'name': 'received', 'label': 'Received', 'group': {'… |

</details>

<a id="s-seedlink"></a>
### 18. EarthScope (IRIS) SeedLink real-time seismic waveforms

- **Verdict:** Meets both — average 2.42 events/s, median 12.0 attributes per event.
- **Delivery:** live · SeedLink 3/4 over TCP (miniSEED records)
- **Endpoint:** `tcp://rtserve.iris.washington.edu:18000`
- **Request:** `STATION <sta> <net> / SELECT BHZ / DATA ... END`
- **Access:** None
- **Documentation:** https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ (HTTP 200)
- **Terms / licence:** https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ (HTTP 200) — “a publicly accessible SeedLink server on the following host and port: host port rtserve”
- **Measurement note (latest representative round):** 12 IU stations, channel BHZ; rate scales with stations selected (each 512-byte miniSEED record carries ~400 samples)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.45 | 147 | 60 | 12.0 | 12 | 12 |
| 2026-10-13T02:11 | ok | 2.32 | 139 | 60 | 12.0 | 12 | 12 |
| 2026-10-13T03:23 | ok | 2.48 | 149 | 60 | 12.0 | 12 | 12 |

<details><summary>Sample event — 12 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `seq` | 51E631 |
| `station` | MAJO |
| `location` | 00 |
| `channel` | BHZ |
| `network` | IU |
| `year` | 2026 |
| `doy` | 286 |
| `hour` | 2 |
| `minute` | 10 |
| `second` | 8 |
| `nsamples` | 412 |
| `rate_factor` | 40 |

</details>

<a id="s-usgs_water"></a>
### 19. USGS Water Services instantaneous values (river gauges)

- **Verdict:** Meets both — average 1.82 events/s, median 26.0 attributes per event.
- **Delivery:** batch · REST JSON (WaterML-JSON)
- **Endpoint:** `https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H`
- **Request:** `GET per state`
- **Access:** None
- **Documentation:** https://waterservices.usgs.gov/ (HTTP 200)
- **Terms / licence:** https://waterservices.usgs.gov/ (HTTP 200) — “decommissioned February 22nd, 2027 WaterServices will be permanently shut down on February 22nd, 2027”
- **Measurement note (latest representative round):** Texas only: 2677 active series; nationwide is ~50x larger. Legacy service retires 2027-02-22

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.79 | 6,433 | 3,600 | 26.0 | 26 | 26 |
| 2026-10-13T02:11 | ok | 1.85 | 6,648 | 3,600 | 26.0 | 26 | 26 |
| 2026-10-13T03:23 | ok | 1.83 | 6,592 | 3,600 | 26.0 | 26 | 26 |

<details><summary>Sample event — 26 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `siteName` | Canadian Rv nr Amarillo, TX |
| `siteCode` | [{'value': '07227500', 'network': 'NWIS', 'agencyCode': 'USGS'}] |
| `timeZoneInfo.defaultTimeZone.zoneOffset` | -06:00 |
| `timeZoneInfo.defaultTimeZone.zoneAbbreviation` | CST |
| `timeZoneInfo.daylightSavingsTimeZone.zoneOffset` | -05:00 |
| `timeZoneInfo.daylightSavingsTimeZone.zoneAbbreviation` | CDT |
| `timeZoneInfo.siteUsesDaylightSavingsTime` | true |
| `geoLocation.geogLocation.srs` | EPSG:4326 |
| `geoLocation.geogLocation.latitude` | 35.4703261 |
| `geoLocation.geogLocation.longitude` | -101.879628 |
| `geoLocation.localSiteXY` | [] |
| `note` | [] |
| `siteType` | [] |
| `siteProperty` | [{'value': 'ST', 'name': 'siteTypeCd'}, {'value': '11090105', 'name': 'hucCd'}, {'value':… |
| `variableCode` | [{'value': '00010', 'network': 'NWIS', 'vocabulary': 'NWIS:UnitValues', 'variableID': 458… |
| `variableName` | Temperature, water, &#176;C |
| `variableDescription` | Temperature, water, degrees Celsius |
| `valueType` | Derived Value |
| `unit.unitCode` | deg C |
| `options.option` | [{'name': 'Statistic', 'optionCode': '00000'}] |
| `noDataValue` | -999999.0 |
| `variableProperty` | [] |
| `oid` | 45807042 |
| `value` | -999999 |
| `qualifiers` | ['P', '***'] |
| `dateTime` | 2026-10-12T20:30:00.000-05:00 |

</details>

<a id="s-polymarket"></a>
### 20. Polymarket CLOB market channel (prediction-market prices)

- **Verdict:** Meets both — average 681.75 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws-subscriptions-clob.polymarket.com/ws/market`
- **Request:** `{"assets_ids":[...],"type":"market"} (ids from https://gamma-api.polymarket.com/markets)`
- **Access:** None
- **Documentation:** https://docs.polymarket.com/developers/CLOB/websocket/market-channel (HTTP 200)
- **Terms / licence:** https://docs.polymarket.com/developers/CLOB/websocket/market-channel (HTTP 200) — “public market data your application depends on current without repeated polling”
- **Measurement note (latest representative round):** top 25 markets by 24h volume (50 outcome tokens)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 408.37 | 24,502 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 293.63 | 17,618 | 60 | 10.0 | 10 | 12 |
| 2026-10-13T03:23 | ok | 1,343.25 | 80,595 | 60 | 10.0 | 10 | 12 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `market` | 0xdce84960dce38aa4a5800a5eba7c9ac34d2ce49ba9d44c42572c472d468af264 |
| `timestamp` | 1791857418277 |
| `event_type` | price_change |
| `asset_id` | 88403451835230950222119400360490338078378790763472355557584611572247419676051 |
| `price` | 0.983 |
| `size` | 236.4 |
| `side` | BUY |
| `hash` | d6ba9956e422280b97a98e5e7eb4dea8e70eadfd |
| `best_bid` | 0.983 |
| `best_ask` | 0.984 |

</details>

<a id="s-base_logs"></a>
### 21. Base (L2) contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 298.66 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://base-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 123.93 | 7,436 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 380.93 | 22,856 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 391.12 | 23,467 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `address` | 0x4200000000000000000000000000000000000010 |
| `blockHash` | 0x47598f2ac8347851c0764d7bb31c55043f9077bf078dc701a53c9f9098d0660b |
| `blockNumber` | 0x3219b14 |
| `blockTimestamp` | 0x6acd930b |
| `data` | 0x000000000000000000000000de80257eeb34cb3695386f13bdd76e2502d9d0c600000000000000000000000… |
| `logIndex` | 0x0 |
| `removed` | false |
| `topics` | ['0xb0444523268717a02698be47d0803aa7468c00acbed2f8bd93a0459cde61dd89', '0x000000000000000… |
| `transactionHash` | 0x676aae0559f3a52d4103fcbc09de32ea24145386300aa7e3be8aa18c451907b8 |
| `transactionIndex` | 0x1 |

</details>

<a id="s-polygon_logs"></a>
### 22. Polygon PoS contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 285.96 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://polygon-bor-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 151.87 | 9,112 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 288.13 | 17,288 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 417.88 | 25,073 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `address` | 0x0000000000000000000000000000000000001010 |
| `blockHash` | 0xd35b34e15c0ccbe6489f74bdde1dcffe4b61fc73ceeca63dcbd5f9e3df075c5f |
| `blockNumber` | 0x5b03800 |
| `blockTimestamp` | 0x6acd930a |
| `data` | 0x000000000000000000000000000000000000000000000001e12adbee837008ce00000000000000000000000… |
| `logIndex` | 0x0 |
| `removed` | false |
| `topics` | ['0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4', '0x000000000000000… |
| `transactionHash` | 0x518c0ed5373ad72b8f3340a4aa65b687b92250fb27db78b3b458a9d08935a404 |
| `transactionIndex` | 0x0 |

</details>

<a id="s-bsc_logs"></a>
### 23. BNB Smart Chain contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 189.63 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://bsc-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 197.15 | 11,829 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 371.75 | 22,305 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `address` | 0x55d398326f99059ff775485246999027b3197955 |
| `blockHash` | 0xd059242f460d65d95e97de0cc6a55964fe6d90e934d8f0c2e3ecce0da78b4284 |
| `blockNumber` | 0x796c14d |
| `blockTimestamp` | 0x6acd9309 |
| `data` | 0x00000000000000000000000000000000000000000000000051e102bd8ece0000 |
| `logIndex` | 0x0 |
| `removed` | false |
| `topics` | ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', '0x000000000000000… |
| `transactionHash` | 0xd9840c0eb24a78fae52754f9584d6ff4c1f2ed4310eb27081494e9662803d222 |
| `transactionIndex` | 0x1 |

</details>

<a id="s-eth_logs"></a>
### 24. Ethereum mainnet contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 83.13 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://ethereum-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 71.33 | 4,280 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 93.43 | 5,606 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 84.62 | 5,077 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `address` | 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 |
| `blockHash` | 0xcb0c119dd30a67825166b8e6d442c455f75bbb5ed5beb99d7a868411e4b51c0a |
| `blockNumber` | 0x18f7b8d |
| `blockTimestamp` | 0x6acd930f |
| `data` | 0x0000000000000000000000000000000000000000000000000000000000006d76 |
| `logIndex` | 0x0 |
| `removed` | false |
| `topics` | ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', '0x000000000000000… |
| `transactionHash` | 0x4e40b68e6b783d608ec29d2332cdb2f2a18316266e887968f0323ee770c77c1c |
| `transactionIndex` | 0x0 |

</details>

<a id="s-bitso"></a>
### 25. Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)

- **Verdict:** Meets both — average 40.74 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.bitso.com`
- **Request:** `{"action":"subscribe","book":"btc_mxn","type":"trades"|"diff-orders"}`
- **Access:** None
- **Documentation:** https://docs.bitso.com/bitso-api/docs (HTTP 200)
- **Terms / licence:** https://docs.bitso.com/bitso-api/docs (HTTP 200) — “s Look Up Orders Cancel an Order List Fees WEBSOCKET API General Trades Channel Diff-Orders Channel Orders Channel Processed-Orders Channel CONVERSIONS Understanding Conversions Request a Conversion Quote Execut”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 32.93 | 1,976 | 60 | 10.0 | 10 | 14 |
| 2026-10-13T02:11 | ok | 41.92 | 2,515 | 60 | 10.0 | 10 | 14 |
| 2026-10-13T03:23 | ok | 47.38 | 2,843 | 60 | 10.0 | 10 | 14 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `a` | 0.10111700 |
| `d` | 1791857417681 |
| `o` | F67a2CIb7lAnkPkU |
| `r` | 1474330 |
| `s` | open |
| `t` | 0 |
| `v` | 149079.82661000 |
| `z` | 0 |
| `book` | btc_mxn |
| `type` | diff-orders |

</details>

<a id="s-okx"></a>
### 26. OKX public tickers

- **Verdict:** Meets both — average 30.81 events/s, median 16.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.okx.com:8443/ws/v5/public`
- **Request:** `{"op":"subscribe","args":[{"channel":"tickers","instId":"BTC-USDT"},...]}`
- **Access:** None
- **Documentation:** https://www.okx.com/docs-v5/en/ (HTTP 200)
- **Terms / licence:** https://www.okx.com/docs-v5/en/ (HTTP 200) — “Public Channel Public structure block trades channel Public block trades channel Block tickers”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 30.27 | 1,816 | 60 | 16.0 | 16 | 16 |
| 2026-10-13T02:11 | ok | 30.75 | 1,845 | 60 | 16.0 | 16 | 16 |
| 2026-10-13T03:23 | ok | 31.42 | 1,885 | 60 | 16.0 | 16 | 16 |

<details><summary>Sample event — 16 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `instType` | SPOT |
| `instId` | BTC-USDT |
| `last` | 82497.9 |
| `lastSz` | 0.00199 |
| `askPx` | 82498 |
| `askSz` | 0.10114532 |
| `bidPx` | 82497.9 |
| `bidSz` | 2.4469972 |
| `open24h` | 83683.8 |
| `high24h` | 84361.6 |
| `low24h` | 81032.8 |
| `sodUtc0` | 81853.2 |
| `sodUtc8` | 82721.2 |
| `volCcy24h` | 543406387.883584829 |
| `vol24h` | 6548.61768163 |
| `ts` | 1791857417963 |

</details>

<a id="s-xrpl"></a>
### 27. XRP Ledger transactions

- **Verdict:** Meets both — average 22.54 events/s, median 20.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://xrplcluster.com/`
- **Request:** `{"command":"subscribe","streams":["transactions"]}`
- **Access:** None
- **Documentation:** https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe (HTTP 200)
- **Terms / licence:** https://xrpl.org/docs/tutorials/public-servers (HTTP 200) — “io/ Full history server cluster with Clio InFTF Mainnet https://xrplcluster”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 23.35 | 1,401 | 60 | 20.0 | 26 | 63 |
| 2026-10-13T02:11 | ok | 17.68 | 1,061 | 60 | 21.0 | 27 | 63 |
| 2026-10-13T03:23 | ok | 26.58 | 1,595 | 60 | 19.0 | 27 | 64 |

<details><summary>Sample event — 27 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `Account` | raRBY29mxKf8oADemdUg5618xL6m5RhMLP |
| `Amount.currency` | BRB |
| `Amount.issuer` | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| `Amount.value` | 9999999999999990e79 |
| `DeliverMax.currency` | BRB |
| `DeliverMax.issuer` | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| `DeliverMax.value` | 9999999999999990e79 |
| `DeliverMin.currency` | BRB |
| `DeliverMin.issuer` | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| `DeliverMin.value` | 955.649949521643 |
| `Destination` | raRBY29mxKf8oADemdUg5618xL6m5RhMLP |
| `Fee` | 12 |
| `Flags` | 196608 |
| `LastLedgerSequence` | 107618699 |
| `Paths` | [[{'currency': '4249547800000000000000000000000000000000', 'issuer': 'rBitcoiNXev8VoVxV7p… |
| `SendMax` | 164181 |
| `Sequence` | 103803480 |
| `SigningPubKey` | 03616FF3FCA0EDDD6CD99CDB3E9E34644F56A2DEB27111FEB790939246784FBEA0 |
| `SourceTag` | 3978681839 |
| `TransactionType` | Payment |
| `TxnSignature` | 3045022100FE72A4E5B01ECF48ED8240CB6865E058C3338986D229238F60284402EE10A9A4022043017462B92… |
| `date` | 845172721 |
| `hash` | 59014F4144026142DFF4CD2DFD573B007094411748EF334EF34C7F383D5C9E0C |
| `ledger_index` | 107618680 |
| `validated` | true |
| `close_time_iso` | 2026-10-13T02:12:01Z |
| `TransactionResult` | tesSUCCESS |

</details>

<a id="s-coinbase"></a>
### 28. Coinbase Exchange ticker

- **Verdict:** Meets both — average 11.36 events/s, median 17.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws-feed.exchange.coinbase.com`
- **Request:** `{"type":"subscribe","product_ids":[...],"channels":["ticker"]}`
- **Access:** None
- **Documentation:** https://docs.cdp.coinbase.com/exchange/websocket-feed/overview (HTTP 200)
- **Terms / licence:** https://docs.cdp.coinbase.com/exchange/websocket-feed/overview (HTTP 200) — “ebSocket Overview Copy page Copy page Copy page Copy page The WebSocket feed is publicly available and provides real-time market data updates for orders and trades”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.48 | 569 | 60 | 17.0 | 17 | 17 |
| 2026-10-13T02:11 | ok | 16.42 | 985 | 60 | 17.0 | 17 | 17 |
| 2026-10-13T03:23 | ok | 8.17 | 490 | 60 | 17.0 | 17 | 17 |

<details><summary>Sample event — 17 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `type` | ticker |
| `sequence` | 33062849932 |
| `product_id` | SOL-USD |
| `price` | 105.42 |
| `open_24h` | 111.9 |
| `volume_24h` | 1032296.29463029 |
| `low_24h` | 101.55 |
| `high_24h` | 113.26 |
| `volume_30d` | 26310333.07328899 |
| `best_bid` | 105.410 |
| `best_bid_size` | 30.25986614 |
| `best_ask` | 105.420 |
| `best_ask_size` | 8.26913607 |
| `side` | buy |
| `time` | 2026-10-13T02:10:15.482827Z |
| `trade_id` | 357552848 |
| `last_size` | 0.0368486 |

</details>

<a id="s-deribit"></a>
### 29. Deribit perpetual futures ticker

- **Verdict:** Meets both — average 5.20 events/s, median 24.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket
- **Endpoint:** `wss://www.deribit.com/ws/api/v2`
- **Request:** `public/subscribe ["ticker.BTC-PERPETUAL.100ms", ...]`
- **Access:** None
- **Documentation:** https://docs.deribit.com/ (HTTP 200)
- **Terms / licence:** https://docs.deribit.com/ (HTTP 200) — “agement/private-unsubscribe_all\",\"autogeneratedByOpenApi\":true},{\"title\":\"public/subscribe\",\"description\":\"Subscribe to one or more channels”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.83 | 290 | 60 | 24.0 | 24 | 24 |
| 2026-10-13T02:11 | ok | 5.80 | 348 | 60 | 24.0 | 24 | 24 |
| 2026-10-13T03:23 | ok | 4.97 | 298 | 60 | 24.0 | 24 | 24 |

<details><summary>Sample event — 24 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `timestamp` | 1791857417771 |
| `state` | open |
| `stats.high` | 2577.15 |
| `stats.low` | 2406.15 |
| `stats.price_change` | -3.0589 |
| `stats.volume` | 71527.956029 |
| `stats.volume_usd` | 179353118.0 |
| `stats.volume_notional` | 179353118.0 |
| `index_price` | 2463.35 |
| `instrument_name` | ETH-PERPETUAL |
| `last_price` | 2464.05 |
| `settlement_price` | 2561.16 |
| `min_price` | 2427.2 |
| `max_price` | 2501.15 |
| `open_interest` | 243663246 |
| `mark_price` | 2464.18 |
| `interest_value` | 0.7948244270987193 |
| `current_funding` | 8.7e-05 |
| `estimated_delivery_price` | 2463.35 |
| `funding_8h` | 1.9e-05 |
| `best_ask_price` | 2464.2 |
| `best_bid_price` | 2464.15 |
| `best_ask_amount` | 3.0 |
| `best_bid_amount` | 37713.0 |

</details>

<a id="s-bitstamp"></a>
### 30. Bitstamp live trades

- **Verdict:** Meets both — average 1.66 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.bitstamp.net`
- **Request:** `{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}`
- **Access:** None
- **Documentation:** https://www.bitstamp.net/websocket/v2/ (HTTP 200)
- **Terms / licence:** https://www.bitstamp.net/websocket/v2/ (HTTP 200) — no matching text found

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.48 | 89 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 2.05 | 123 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 1.43 | 86 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 653888310 |
| `timestamp` | 1791857420 |
| `amount` | 21.47412281 |
| `amount_str` | 21.47412281 |
| `price` | 1.35372 |
| `price_str` | 1.35372 |
| `type` | 0 |
| `microtimestamp` | 1791857420968000 |
| `buy_order_id` | 2060379940085762 |
| `sell_order_id` | 2060379938447361 |

</details>

<a id="s-twitch"></a>
### 31. Twitch chat (anonymous read-only IRC)

- **Verdict:** Meets both — average 21.44 events/s, median 19.0 attributes per event.
- **Delivery:** live · IRC over WebSocket
- **Endpoint:** `wss://irc-ws.chat.twitch.tv:443`
- **Request:** `CAP REQ :twitch.tv/tags; PASS SCHMOOPIIE; NICK justinfanNNNN; JOIN #<channels>`
- **Access:** Anonymous (justinfan) read-only login
- **Documentation:** https://dev.twitch.tv/docs/chat/irc/ (HTTP 200)
- **Terms / licence:** https://legal.twitch.com/legal/developer-agreement/ (HTTP 200) — “Chat We consider chat to be an essential component of the broadcast experience on Twitch”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 24.07 | 1,444 | 60 | 19.0 | 28 | 33 |
| 2026-10-13T02:11 | ok | 22.03 | 1,322 | 60 | 19.0 | 28 | 33 |
| 2026-10-13T03:23 | ok | 18.22 | 1,093 | 60 | 19.0 | 28 | 32 |

<details><summary>Sample event — 28 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `badge-info` |  |
| `badges` | pichu/1 |
| `client-nonce` | ‹redacted› |
| `color` | #00FF7F |
| `display-name` | ‹redacted› |
| `emotes` |  |
| `first-msg` | 0 |
| `flags` |  |
| `id` | ‹redacted› |
| `mod` | 0 |
| `reply-parent-display-name` | ‹redacted› |
| `reply-parent-msg-body` | ‹redacted› |
| `reply-parent-msg-id` | ‹redacted› |
| `reply-parent-user-id` | ‹redacted› |
| `reply-parent-user-login` | ‹redacted› |
| `reply-thread-parent-display-name` | ‹redacted› |
| `reply-thread-parent-msg-id` | ‹redacted› |
| `reply-thread-parent-user-id` | ‹redacted› |
| `reply-thread-parent-user-login` | ‹redacted› |
| `returning-chatter` | 0 |
| `room-id` | ‹redacted› |
| `subscriber` | 0 |
| `tmi-sent-ts` | 1791857421948 |
| `turbo` | 0 |
| `user-id` | ‹redacted› |
| `user-type` |  |
| `channel` | #xqc |
| `message` | ‹redacted› |

</details>

<a id="s-albion"></a>
### 32. Albion Online Data Project market orders

- **Verdict:** Meets both — average 21.06 events/s, median 10.0 attributes per event.
- **Delivery:** live · NATS (TCP 4222)
- **Endpoint:** `nats://nats.albion-online-data.com:4222`
- **Request:** `CONNECT user=public pass=thenewalbiondata; SUB marketorders.deduped`
- **Access:** Published public credentials
- **Documentation:** https://www.albion-online-data.com/ (HTTP 200)
- **Terms / licence:** https://github.com/ao-data/albiondata-client (HTTP 200) — “ternate_user_config_repo","async_conversion_coverage_enabled","billing_billable_licenses_cost_center_bucket_fix","billing_budget_expiration","billing_cost_center_list_assigned_resources","billing_discount_th”
- **Measurement note (latest representative round):** NATS subject marketorders.deduped (Americas server)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 14.43 | 866 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 1.02 | 61 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 47.73 | 2,864 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `Id` | 15454378873 |
| `ItemTypeId` | T4_CAPEITEM_FW_LYMHURST |
| `ItemGroupTypeId` | T4_CAPEITEM_FW_LYMHURST |
| `LocationId` | 5003 |
| `QualityLevel` | 3 |
| `EnchantmentLevel` | 0 |
| `UnitPriceSilver` | 64996 |
| `Amount` | 1 |
| `AuctionType` | offer |
| `Expires` | 2026-11-11T22:53:42.354584 |

</details>

<a id="s-dt_road"></a>
### 33. Digitraffic Finland road traffic (TMS) and road-weather sensors

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 338.37 events/s, median 2.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://tie.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE tms-v2/# and weather-v2/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/road-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Enrichment:** Station and sensor metadata: https://tie.digitraffic.fi/api/tms/v1/stations and /api/weather/v1/stations
- **Measurement note (latest representative round):** example topic: tms-v2/23572/5055

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 327.33 | 19,640 | 60 | 2.0 | 4 | 4 |
| 2026-10-13T02:11 | ok | 356.93 | 21,416 | 60 | 2.0 | 4 | 4 |
| 2026-10-13T03:23 | ok | 330.83 | 19,850 | 60 | 2.0 | 2 | 2 |

<details><summary>Sample event — 4 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `end` | 1791856800 |
| `start` | 1791853200 |
| `time` | 1791857431 |
| `value` | 54.0 |

</details>

<a id="s-dt_rail"></a>
### 34. Digitraffic Finland train GPS locations

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 37.23 events/s, median 8.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://rata.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE train-locations/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/railway-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: train-locations/2026-10-13/2003

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 30.50 | 1,830 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T02:11 | ok | 32.63 | 1,958 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T03:23 | ok | 48.55 | 2,913 | 60 | 8.0 | 8 | 8 |

<details><summary>Sample event — 8 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `accuracy` | 0 |
| `isGpsLocation` | true |
| `location.type` | Point |
| `location.coordinates` | [28.495049, 61.122156] |
| `speed` | 0 |
| `trainNumber` | 2003 |
| `departureDate` | 2026-10-13 |
| `timestamp` | 2026-10-13T01:23:24Z |

</details>

<a id="s-mta_gtfsrt"></a>
### 35. MTA New York City Subway GTFS-Realtime (A/C/E feed)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 4.96 events/s, median 6.5 attributes per event.
- **Delivery:** poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s
- **Endpoint:** `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace`
- **Request:** `GET (7 more subway feeds: gtfs, -bdfm, -g, -jz, -nqrw, -l, -si)`
- **Access:** None
- **Documentation:** https://api.mta.info/ (HTTP 200)
- **Terms / licence:** https://www.mta.info/developers (HTTP 403) — “Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to apply for a license. [page refuses scripted requests (HTTP 403); text retrieved with the webfetch tool on 2026-10-13]”
- **Measurement note (latest representative round):** 4 polls every 15s; 180 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.68 | 304 | 65 | 6.5 | 9 | 14 |
| 2026-10-13T02:11 | ok | 5.41 | 303 | 56 | 6.5 | 9 | 14 |
| 2026-10-13T03:23 | ok | 4.78 | 221 | 46 | 6.5 | 9 | 14 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 000002A |
| `vehicle.trip.tripId` | 124150_A..N55R |
| `vehicle.trip.startTime` | 20:41:30 |
| `vehicle.trip.startDate` | 20261012 |
| `vehicle.trip.routeId` | A |
| `vehicle.currentStopSequence` | 31 |
| `vehicle.currentStatus` | STOPPED_AT |
| `vehicle.timestamp` | 1791857397 |
| `vehicle.stopId` | A09N |

</details>

<a id="s-osm"></a>
### 36. OpenStreetMap minutely replication diffs

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 28.74 events/s, median 9.0 attributes per event.
- **Delivery:** batch · gzip osmChange XML, one file per minute
- **Endpoint:** `https://planet.openstreetmap.org/replication/minute/NNN/NNN/NNN.osc.gz (state.txt gives the sequence)`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://wiki.openstreetmap.org/wiki/Planet.osm/diffs (HTTP 200)
- **Terms / licence:** https://www.openstreetmap.org/copyright (HTTP 200) — “Open Data Commons Open Database License (ODbL) by the OpenStreetMap Foundation (OSMF)”
- **Measurement note (latest representative round):** minute diff #7326630; 9 fixed attributes per element + its OSM tags (tag:*), counted per event

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 52.80 | 3,168 | 60 | 9.0 | 18 | 36 |
| 2026-10-13T02:11 | ok | 27.07 | 1,624 | 60 | 9.0 | 15 | 27 |
| 2026-10-13T03:23 | ok | 6.37 | 382 | 60 | 9.0 | 294 | 360 |

<details><summary>Sample event — 294 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 424313451 |
| `version` | 93 |
| `timestamp` | 2026-10-13T03:20:51Z |
| `uid` | ‹redacted› |
| `user` | ‹redacted› |
| `changeset` | 190430503 |
| `lat` | 36.5748441 |
| `lon` | 139.2394179 |
| `element` | node |
| `tag:alt_name:eo` | Japanujo;Nipono |
| `tag:alt_name:ja` | 日本 |
| `tag:alt_name:ja-Hira` | にっぽん |
| `tag:alt_name:ja-Latn` | Nippon |
| `tag:alt_name:lfn` | Japan |
| `tag:alt_name:vi` | Nhật |
| `tag:capital_city` | Tokyo |
| `tag:country_code_fips` | JA |
| `tag:country_code_iso3166_1_alpha_2` | JP |
| `tag:int_name` | Japan |
| `tag:name` | 日本 |
| `tag:name:aa` | Japan |
| `tag:name:ab` | Иапониа |
| `tag:name:ace` | Jeupun |
| `tag:name:af` | Japan |
| `tag:name:ak` | Gyapan |
| `tag:name:als` | Japan |
| `tag:name:am` | ጃፓን |
| `tag:name:an` | Chapón |
| `tag:name:ang` | Iapan |
| `tag:name:ar` | اليابان |
| `tag:name:arc` | ܝܦܢ |
| `tag:name:arz` | اليابان |
| `tag:name:as` | জাপান |
| `tag:name:ast` | Xapón |
| `tag:name:ay` | Nihun |
| `tag:name:az` | Yaponiya |
| `tag:name:azb` | ژاپون |
| `tag:name:ba` | Япония |
| `tag:name:bar` | Japan |
| `tag:name:bat-smg` | Japuonėjė |
| `tag:name:bcl` | Hapon |
| `tag:name:be` | Японія |
| `tag:name:be-tarask` | Японія |
| `tag:name:bg` | Япония |
| `tag:name:bjn` | Japang |
| `tag:name:bm` | Zapɔn |
| `tag:name:bn` | জাপান |
| `tag:name:bo` | རི་པིན། |
| `tag:name:bpy` | জাপান |
| `tag:name:br` | Japan |
| `tag:name:bs` | Japan |
| `tag:name:bug` | ᨍᨛᨄ |
| `tag:name:bxr` | Жибэн |
| `tag:name:ca` | Japó |
| `tag:name:cbk-zam` | Japón |
| `tag:name:cdo` | Nĭk-buōng |
| `tag:name:ce` | Япони |
| `tag:name:ceb` | Hapon |
| `tag:name:ch` | Chapan |
| `tag:name:chr` | ᏣᏆᏂ |
| `tag:name:ckb` | ژاپۆن |
| `tag:name:cnr` | Japan |
| `tag:name:crh` | Yaponiya |
| `tag:name:cs` | Japonsko |
| `tag:name:csb` | Japòńskô |
| `tag:name:cu` | Ꙗпѡні́ꙗ |
| `tag:name:cv` | Япони |
| `tag:name:cy` | Japan |
| `tag:name:da` | Japan |
| `tag:name:dak` | Kisuƞna Maḳoc̣e |
| `tag:name:de` | Japan |
| `tag:name:diq` | Japonya |
| `tag:name:dsb` | Japańska |
| `tag:name:dv` | ޖަޕާނު |
| `tag:name:dz` | ཇ་པཱན |
| `tag:name:ee` | Japan |
| `tag:name:el` | Ιαπωνία |
| `tag:name:en` | Japan |
| `tag:name:eo` | Japanio |
| `tag:name:es` | Japón |
| `tag:name:et` | Jaapan |
| `tag:name:eu` | Japonia |
| `tag:name:ext` | Japón |
| `tag:name:fa` | ژاپن |
| `tag:name:ff` | Sapoo |
| `tag:name:fi` | Japani |
| `tag:name:fo` | Japan |
| `tag:name:fr` | Japon |
| `tag:name:frp` | J·apon |
| `tag:name:frr` | Japan |
| `tag:name:fur` | Gjapon |
| `tag:name:fy` | Japan |
| `tag:name:ga` | An tSeapáin |
| `tag:name:gag` | Yaponiya |
| `tag:name:gan` | 日本 |
| `tag:name:gd` | Iapan |
| `tag:name:gl` | Xapón - 日本 |
| `tag:name:glk` | ژاپؤن |
| `tag:name:gn` | Hapõ |
| `tag:name:gu` | જાપાન |
| `tag:name:gv` | Yn Çhapaan |
| `tag:name:ha` | Japan |
| `tag:name:hak` | Ngi̍t-pún |
| `tag:name:haw` | Iāpana |
| `tag:name:he` | יפן |
| `tag:name:hi` | जापान |
| `tag:name:hif` | Japan |
| `tag:name:hr` | Japan |
| `tag:name:hsb` | Japanska |
| `tag:name:ht` | Japon |
| `tag:name:hu` | Japán |
| `tag:name:hy` | Ճապոնիա |
| `tag:name:ia` | Japon |
| `tag:name:id` | Jepang |
| `tag:name:ie` | Japan |
| `tag:name:ii` | ꏝꀪ |
| `tag:name:ilo` | Japon |
| `tag:name:io` | Japonia |
| `tag:name:is` | Japan |
| `tag:name:it` | Giappone |
| `tag:name:iu` | ᓃᑉᐊᓐ |
| `tag:name:iu-Latn` | niipan |
| `tag:name:ja` | 日本 |
| `tag:name:ja-Hira` | にほん |
| `tag:name:ja-Latn` | Nihon |
| `tag:name:jbo` | pongu&apos;e |
| `tag:name:jv` | Jepang |
| `tag:name:ka` | იაპონია |
| `tag:name:kab` | Jappu |
| `tag:name:kbd` | Япон |
| `tag:name:ki` | Njabani |
| `tag:name:kk` | Жапония |
| `tag:name:kl` | Japani |
| `tag:name:km` | ជប៉ុន |
| `tag:name:kmr` | ژاپۆن |
| `tag:name:kn` | ಜಪಾನ್ |
| `tag:name:ko` | 일본 |
| `tag:name:koi` | Ниппон |
| `tag:name:krc` | Япония |
| `tag:name:ks` | جاپون |
| `tag:name:ksh` | Japan |
| `tag:name:ku` | Japon |
| `tag:name:kv` | Япония |
| `tag:name:kw` | Nihon |
| `tag:name:ky` | Жапония |
| `tag:name:la` | Iaponia |
| `tag:name:lb` | Japan |
| `tag:name:lez` | Япония |
| `tag:name:lfn` | Nion |
| `tag:name:lg` | Japani |
| `tag:name:li` | Japan |
| `tag:name:lij` | Giappon |
| `tag:name:lkt` | Kisúŋla-Makȟóčhe |
| `tag:name:lmo` | Giapun |
| `tag:name:ln` | Zapɔ́ |
| `tag:name:lo` | ປະເທດຍີ່ປຸ່ນ |
| `tag:name:lrc` | جاپوݩ |
| `tag:name:lt` | Japonija |
| `tag:name:ltg` | Japoneja |
| `tag:name:lv` | Japāna |
| `tag:name:lzh` | 日本 |
| `tag:name:mdf` | Япунмастор |
| `tag:name:mg` | Japana |
| `tag:name:mhr` | Японий |
| `tag:name:mi` | Nipono |
| `tag:name:min` | Japang |
| `tag:name:mk` | Јапонија |
| `tag:name:ml` | ജപ്പാന്‍ |
| `tag:name:mn` | Япон |
| `tag:name:mo` | Жапония |
| `tag:name:mr` | जपान |
| `tag:name:mrj` | Япони |
| `tag:name:ms` | Jepun |
| `tag:name:mt` | Ġappun |
| `tag:name:mwl` | Japon |
| `tag:name:my` | ဂျပန်နိုင်ငံ |
| `tag:name:mzn` | جاپون |
| `tag:name:na` | Djapan |
| `tag:name:nah` | Xapon |
| `tag:name:nan` | Ji̍t-pún |
| `tag:name:nap` | Giappone |
| `tag:name:nds` | Japan |
| `tag:name:nds-nl` | Japan |
| `tag:name:ne` | जापान |
| `tag:name:new` | जापान |
| `tag:name:nl` | Japan |
| `tag:name:nn` | Japan |
| `tag:name:no` | Japan |
| `tag:name:nov` | Japan |
| `tag:name:nrm` | Japon |
| `tag:name:nso` | Japane |
| `tag:name:nv` | Bina&apos;adaałtzózí |
| `tag:name:oc` | Japon |
| `tag:name:om` | Japan |
| `tag:name:or` | ଜାପାନ |
| `tag:name:os` | Япон |
| `tag:name:pa` | ਜਪਾਨ |
| `tag:name:pam` | Hapon |
| `tag:name:pap` | Hapon |
| `tag:name:pcd` | Japon |
| `tag:name:pdc` | Japan |
| `tag:name:pih` | Japan |
| `tag:name:pl` | Japonia |
| `tag:name:pms` | Giapon |
| `tag:name:pnb` | جاپان |
| `tag:name:ps` | جاپان |
| `tag:name:pt` | Japão |
| `tag:name:qu` | Nihun |
| `tag:name:rm` | Giapun |
| `tag:name:rn` | Ubuyapani |
| `tag:name:ro` | Japonia |
| `tag:name:roa-rup` | Japonia |
| `tag:name:roa-tara` | Giappone |
| `tag:name:ru` | Япония |
| `tag:name:rue` | Японія |
| `tag:name:rw` | Ubuyapani |
| `tag:name:sa` | जापान |
| `tag:name:sah` | Дьоппуон |
| `tag:name:sc` | Giapone |
| `tag:name:scn` | Giappuni |
| `tag:name:sco` | Japan |
| `tag:name:sd` | جاپان |
| `tag:name:se` | Japána |
| `tag:name:sg` | Zapöon |
| `tag:name:sh` | Japan |
| `tag:name:si` | ජපානය |
| `tag:name:sk` | Japonsko |
| `tag:name:sl` | Japonska |
| `tag:name:sm` | Iapani |
| `tag:name:smn` | Jaapaan |
| `tag:name:sms` | Japaan |
| `tag:name:sn` | Japan |
| `tag:name:so` | Jabaan |
| `tag:name:sq` | Japonia |
| `tag:name:sr` | Јапан |
| `tag:name:srn` | Japan |
| `tag:name:ss` | IJaphani |
| `tag:name:stq` | Japan |
| `tag:name:su` | Jepang |
| `tag:name:sv` | Japan |
| `tag:name:sw` | Japani |
| `tag:name:szl` | Japōnijŏ |
| `tag:name:ta` | ஜப்பான் |
| `tag:name:te` | జపాన్ |
| `tag:name:tg` | Ҷопон |
| `tag:name:th` | ประเทศญี่ปุ่น |
| `tag:name:ti` | ጃፓን |
| `tag:name:tk` | Ýaponiýa |
| `tag:name:tl` | Hapon |
| `tag:name:to` | Siapani |
| `tag:name:tok` | ma Nijon |
| `tag:name:tpi` | Siapan |
| `tag:name:tr` | Japonya |
| `tag:name:tt` | Япония |
| `tag:name:tw` | Yapan |
| `tag:name:ty` | Tāpōnē |
| `tag:name:tzl` | Cipangu |
| `tag:name:udm` | Япония |
| `tag:name:ug` | ياپونىيە |
| `tag:name:uk` | Японія |
| `tag:name:ur` | جاپان |
| `tag:name:uz` | Yaponiya |
| `tag:name:vec` | Giapòn |
| `tag:name:vi` | Nhật Bản |
| `tag:name:vo` | Yapän |
| `tag:name:vro` | Jaapan |
| `tag:name:wal` | Jaappaane |
| `tag:name:war` | Hapon |
| `tag:name:wo` | Sapoŋ |
| `tag:name:wuu` | 日本 |
| `tag:name:xal` | Японь |
| `tag:name:xmf` | იაპონია |
| `tag:name:xnb` | Ripun |
| `tag:name:yi` | יאפאן |
| `tag:name:yo` | Japan |
| `tag:name:yue` | 日本 |
| `tag:name:za` | Nditbonj |
| `tag:name:zea` | Japan |
| `tag:name:zh` | 日本 |
| `tag:name:zh-Hans` | 日本 |
| `tag:name:zh-Hant` | 日本 |
| `tag:name:zh-Latn-pinyin` | Rìběn |
| `tag:name:zu` | iJapani |
| `tag:official_name:ar` | دولة اليابان |
| `tag:official_name:ca` | Estat del Japó |
| `tag:official_name:pt` | Império do Japão |
| `tag:old_name:vi` | Nhật Bổn |
| `tag:place` | country |
| `tag:population` | 127360000 |
| `tag:source:population` | http://www.stat.go.jp/english/data/jinsui/tsuki/index.htm 2010 |
| `tag:source:sqkm` | CIA World Factbook |
| `tag:sqkm` | 377915 |
| `tag:wikidata` | Q17 |
| `tag:wikipedia` | en:Japan |

</details>

<a id="s-npm"></a>
### 37. npm registry replication changes

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 1.99 events/s, median 3.0 attributes per event.
- **Delivery:** counter · CouchDB-style _changes over HTTPS
- **Endpoint:** `https://replicate.npmjs.com/registry/_changes`
- **Request:** `GET ?since=<seq>`
- **Access:** None
- **Documentation:** https://github.com/npm/registry-follower-tutorial (HTTP 200)
- **Terms / licence:** https://docs.npmjs.com/policies/open-source-terms (HTTP 200) — “rted Setting up your npm user account Creating a new user account on the public registry Creating a strong password Receiving a one-time password over email About two-factor authentication Configuring two-factor authentication Accessing npm using t”
- **Measurement note (latest representative round):** raw change record; full package metadata needs one extra GET per change

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.18 | 140 | 64 | 3.0 | 3 | 3 |
| 2026-10-13T02:11 | ok | 1.89 | 124 | 65 | 3.0 | 3 | 3 |
| 2026-10-13T03:23 | ok | 1.90 | 115 | 61 | 3.0 | 3 | 3 |

<details><summary>Sample event — 3 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `seq` | 136460198 |
| `id` | @typescript-eslint/rule-schema-to-typescript-types |
| `changes` | [{'rev': '538-e54131f803d620041b0d9f1fe0d25994'}] |

</details>

<a id="s-rbn"></a>
### 38. Reverse Beacon Network (CW/RTTY skimmer spots)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 1.42 events/s, median 9.0 attributes per event.
- **Delivery:** live · Telnet text lines
- **Endpoint:** `telnet://telnet.reversebeacon.net:7000`
- **Request:** `send any callsign at login`
- **Access:** None
- **Documentation:** https://www.reversebeacon.net/ (HTTP 200)
- **Terms / licence:** https://www.reversebeacon.net/ (HTTP 200) — “lst about A Short History Telnet servers Get Smart About the RBN Who We Are RBN Value Multipliers ARCluster V6 Filtering Red Pitaya, preparing Guide to the new site (beta) How to get spotted b”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.65 | 99 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 1.38 | 83 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 1.23 | 74 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `spotter` | ‹redacted› |
| `freq` | 1836.00 |
| `dx` | ‹redacted› |
| `mode` | CW |
| `snr` | 4 |
| `speed` | 21 |
| `unit` | WPM |
| `type` | CQ |
| `time` | 0210 |

</details>

<a id="s-gemini"></a>
### 39. Gemini market data v1 (order-book changes + trades)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 680.44 events/s, median 9.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://api.gemini.com/v1/marketdata/<SYMBOL>`
- **Request:** `connect per symbol (no message)`
- **Access:** None
- **Documentation:** https://developer.gemini.com/websocket/streams.md (HTTP 200)
- **Terms / licence:** https://developer.gemini.com/websocket/streams.md (HTTP 200) — “er ID â an obfuscated alias for the numeric order ID ('i'), safe for external/public display \| \| 'c' \| string \| Client order ID”
- **Measurement note (latest representative round):** 3 symbols (BTCUSD, ETHUSD, SOLUSD), v1 market data: order-book changes + trades

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 832.17 | 49,930 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 786.53 | 47,192 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 422.62 | 25,357 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `delta` | 0.0843954 |
| `price` | 82249.0 |
| `reason` | initial |
| `remaining` | 0.0843954 |
| `side` | bid |
| `type` | change |
| `eventId` | 1764561291336754 |
| `timestampms` | null |
| `socket_sequence` | 0 |

</details>

<a id="s-solana"></a>
### 40. Solana program logs (public mainnet RPC)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 589.19 events/s, median 4.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (logsSubscribe)
- **Endpoint:** `wss://api.mainnet-beta.solana.com`
- **Request:** `{"method":"logsSubscribe","params":["all",{"commitment":"confirmed"}]}`
- **Access:** None (public RPC is rate-limited)
- **Documentation:** https://solana.com/docs/rpc/websocket/logssubscribe (HTTP 200)
- **Terms / licence:** https://solana.com/docs/references/clusters (HTTP 200) — “Each of these public endpoints are subject to rate limits, but are available for users and developers to interact with the Solana blockchain”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 46.10 | 2,766 | 60 | 4.0 | 4 | 5 |
| 2026-10-13T02:11 | ok | 504.60 | 30,276 | 60 | 4.0 | 4 | 5 |
| 2026-10-13T03:23 | ok | 1,216.87 | 73,012 | 60 | 4.0 | 4 | 5 |

<details><summary>Sample event — 4 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `context.slot` | 456271998 |
| `value.signature` | 4Pn8gD7sYLj7fVHJ4bT9JpXrdERmiGkz9QfhuKPpEUFB3EcStpvGPCuun1AcpaptM9pvxtNo8bMYKFLyYN6aDkYc |
| `value.err` | null |
| `value.logs` | ['Program ComputeBudget111111111111111111111111111111 invoke [1]', 'Program ComputeBudget… |

</details>

<a id="s-hyperliquid"></a>
### 41. Hyperliquid trades

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 8.89 events/s, median 8.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://api.hyperliquid.xyz/ws`
- **Request:** `{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}}`
- **Access:** None
- **Documentation:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions (HTTP 200)
- **Terms / licence:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions (HTTP 200) — “: int , fast: boolean (5 levels if fast, 20 levels if slow) Data format: WsBook trades : Subscription message: { &quot;type&quot;: &quot;trades&quot;, &quot;coin&quot;: &quot;&lt;coin_symbol&gt;&quot; } Dat”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.68 | 581 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T02:11 | ok | 12.12 | 727 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T03:23 | ok | 4.87 | 292 | 60 | 8.0 | 8 | 8 |

<details><summary>Sample event — 8 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `coin` | BTC |
| `side` | B |
| `px` | 82440.0 |
| `sz` | 0.00115 |
| `time` | 1791857404350 |
| `hash` | 0x182acbd523bc9e6219a40446706558020c1300babebfbd34bbf37727e2b0784c |
| `tid` | 640851645839836 |
| `users` | ‹redacted› |

</details>

<a id="s-bybit"></a>
### 42. Bybit spot tickers

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 7.61 events/s, median 9.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://stream.bybit.com/v5/public/spot`
- **Request:** `{"op":"subscribe","args":["tickers.BTCUSDT",...]}`
- **Access:** None
- **Documentation:** https://bybit-exchange.github.io/docs/v5/websocket/public/ticker (HTTP 200)
- **Terms / licence:** https://bybit-exchange.github.io/docs/v5/websocket/public/ticker (HTTP 200) — “Spot &amp; Option tickers message are snapshot only Push frequency: Derivatives &amp; Options - 100ms , Spot - 50ms Topic: tickers”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 7.35 | 441 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 8.40 | 504 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 7.08 | 425 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `symbol` | BTCUSDT |
| `lastPrice` | 82505.9 |
| `highPrice24h` | 84355.8 |
| `lowPrice24h` | 81031.2 |
| `prevPrice24h` | 83695.2 |
| `volume24h` | 9674.971793 |
| `turnover24h` | 801562254.50840967 |
| `price24hPcnt` | -0.0142 |
| `usdIndexPrice` | 82396.431504 |

</details>

<a id="s-kraken"></a>
### 43. Kraken trades + ticker (v2)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 7.07 events/s, median 7.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.kraken.com/v2`
- **Request:** `{"method":"subscribe","params":{"channel":"trade"|"ticker","symbol":[...]}}`
- **Access:** None
- **Documentation:** https://docs.kraken.com/api/docs/websocket-v2/trade (HTTP 200)
- **Terms / licence:** https://docs.kraken.com/api/docs/websocket-v2/trade (HTTP 200) — “base-ui-disable-scrollbar::-webkit-scrollbar{display:none} Trades - Kraken Developers !function(){var b=""; function a(p){if(p==null)return"/";p=""+p;if(""===p)return"/";return"/"===p”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.47 | 568 | 60 | 7.0 | 14 | 19 |
| 2026-10-13T02:11 | ok | 7.35 | 441 | 60 | 7.0 | 14 | 19 |
| 2026-10-13T03:23 | ok | 4.38 | 263 | 60 | 7.0 | 14 | 19 |

<details><summary>Sample event — 14 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `symbol` | BTC/USD |
| `bid` | 82399.1 |
| `bid_qty` | 0.40154298 |
| `ask` | 82399.2 |
| `ask_qty` | 0.40687101 |
| `last` | 82399.1 |
| `volume` | 2569.66148165 |
| `vwap` | 82800.7 |
| `low` | 80951.2 |
| `high` | 84250.0 |
| `change` | -1191.7 |
| `change_pct` | -1.43 |
| `trades` | 162558 |
| `timestamp` | 2026-10-13T02:10:19.909591Z |

</details>

<a id="s-bitfinex"></a>
### 44. Bitfinex trades + ticker (public v2)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 1.80 events/s, median 5.0 attributes per event.
- **Delivery:** live · WebSocket (JSON arrays)
- **Endpoint:** `wss://api-pub.bitfinex.com/ws/2`
- **Request:** `{"event":"subscribe","channel":"trades"|"ticker","symbol":"tBTCUSD"}`
- **Access:** None
- **Documentation:** https://docs.bitfinex.com/docs/ws-public (HTTP 200)
- **Terms / licence:** https://docs.bitfinex.com/docs/ws-public (HTTP 200) — “Public Channels {"@context":"https://schema”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.60 | 96 | 60 | 5.0 | 11 | 15 |
| 2026-10-13T02:11 | ok | 2.47 | 148 | 60 | 5.0 | 11 | 15 |
| 2026-10-13T03:23 | ok | 1.33 | 80 | 60 | 5.0 | 11 | 15 |

<details><summary>Sample event — 11 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `BID` | 82491 |
| `BID_SIZE` | 0.72583456 |
| `ASK` | 82501 |
| `ASK_SIZE` | 0.95128019 |
| `DAILY_CHANGE` | -1554 |
| `DAILY_CHANGE_RELATIVE` | -0.01848877 |
| `LAST_PRICE` | 82497 |
| `VOLUME` | 378.42662028 |
| `HIGH` | 84378 |
| `LOW` | 81054 |
| `symbol` | tBTCUSD |

</details>

<a id="s-dt_rail_trains"></a>
### 45. Digitraffic Finland train timetables/actuals

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.98 events/s, median 13.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://rata.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE trains/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/railway-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: trains/2026-10-12/3061/Cargo/T/vr//true/REGULAR

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.82 | 49 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 0.88 | 53 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 1.23 | 74 | 60 | 13.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `commuterLineID` |  |
| `runningCurrently` | true |
| `cancelled` | false |
| `version` | 293816082956 |
| `timetableType` | REGULAR |
| `timetableAcceptanceDate` | 2025-10-30T06:30:01Z |
| `departureDate` | 2026-10-12 |
| `trainNumber` | 3061 |
| `operatorUICCode` | 10 |
| `operatorShortCode` | vr |
| `timeTableRows` | [{'type': 'DEPARTURE', 'commercialTrack': '218', 'cancelled': False, 'scheduledTime': '20… |
| `trainCategory` | Cargo |
| `trainType` | T |

</details>

<a id="s-velib"></a>
### 46. Vélib' Métropole Paris bike-share station status (GBFS)

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.87 events/s, median 12.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel (HTTP 200)
- **Terms / licence:** https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel (HTTP 200) — “Licence Open Data Commons Open Database License (ODbL)”
- **Measurement note (latest representative round):** 5 polls every 10s; 1519 records per snapshot; rate = new/changed records per second

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.86 | 48 | 56 | 12.0 | 12 | 12 |
| 2026-10-13T02:11 | ok | 0.81 | 41 | 50 | 12.0 | 12 | 12 |
| 2026-10-13T03:23 | ok | 0.93 | 51 | 55 | 12.0 | 12 | 12 |

<details><summary>Sample event — 12 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `station_id` | 213688169 |
| `num_bikes_available` | 5 |
| `numBikesAvailable` | 5 |
| `num_bikes_available_types` | [{'mechanical': 4}, {'ebike': 1}] |
| `num_docks_available` | 29 |
| `numDocksAvailable` | 29 |
| `is_installed` | 1 |
| `is_returning` | 1 |
| `is_renting` | 1 |
| `last_reported` | 1791855310 |
| `stationCode` | 16107 |
| `station_opening_hours` | null |

</details>

<a id="s-pypi"></a>
### 47. PyPI newest releases feed

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.10 events/s, median 33.0 attributes per event.
- **Delivery:** batch · RSS over HTTPS (+ JSON API per release)
- **Endpoint:** `https://pypi.org/rss/updates.xml ; https://pypi.org/pypi/<name>/<version>/json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://docs.pypi.org/api/feeds/ (HTTP 200)
- **Terms / licence:** https://docs.pypi.org/api/ (HTTP 200) — “s and Datasets Introduction Introduction Table of contents API policies Caching Rate limiting API Preference Integration guide Querying PyPI for Package URLs Official guidance Predictable URLs Index API JSON API Upload API Integrity API Stats API Big”
- **Measurement note (latest representative round):** RSS shows the latest 100 releases (5 raw fields); attributes counted on the per-release JSON enrichment (info.*)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.10 | 100 | 1,001 | 33.0 | 33 | 33 |
| 2026-10-13T02:11 | ok | 0.09 | 100 | 1,055 | 32.0 | 32 | 32 |
| 2026-10-13T03:23 | ok | 0.10 | 100 | 1,005 | 34.0 | 34 | 34 |

<details><summary>Sample event — 34 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `author` | bissli |
| `author_email` | null |
| `bugtrack_url` | null |
| `classifiers` | ['Development Status :: 5 - Production/Stable', 'Environment :: Console', 'Intended Audie… |
| `description` | # memman  **Persistent memory for Claude Code and Codex.**  memman saves decisions, prefe… |
| `description_content_type` | text/markdown |
| `docs_url` | null |
| `download_url` | null |
| `downloads.last_day` | -1 |
| `downloads.last_month` | -1 |
| `downloads.last_week` | -1 |
| `dynamic` | null |
| `home_page` | null |
| `keywords` | ai, ai-agents, agent-memory, agents, llm, memory, long-term-memory, rag, embeddings, vect… |
| `license` | MIT |
| `license_expression` | null |
| `license_files` | ['LICENSE'] |
| `maintainer` | null |
| `maintainer_email` | null |
| `name` | memman |
| `package_url` | https://pypi.org/project/memman/ |
| `platform` | null |
| `project_url` | https://pypi.org/project/memman/ |
| `project_urls.Documentation` | https://github.com/bissli/memman/blob/master/docs/DESIGN.md |
| `project_urls.Homepage` | https://github.com/bissli/memman |
| `project_urls.Repository` | https://github.com/bissli/memman |
| `provides_extra` | ['postgres'] |
| `release_url` | https://pypi.org/project/memman/0.50.0/ |
| `requires_dist` | ['click<9.0,>=8.1', 'httpx<0.28,>=0.27', 'numpy<3,>=1.26', 'pgvector<0.6,>=0.3; extra == … |
| `requires_python` | <4.0,>=3.11 |
| `summary` | LLM-supervised persistent memory for Claude Code and Codex - fused keyword, vector and re… |
| `version` | 0.50.0 |
| `yanked` | false |
| `yanked_reason` | null |

</details>

<a id="s-ena"></a>
### 48. ENA (EMBL-EBI) sequencing runs made public — DNA/genomics

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.15 events/s, median 196.0 attributes per event.
- **Delivery:** batch · REST (ENA Portal API)
- **Endpoint:** `https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=first_public>=<date>`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.ebi.ac.uk/ena/portal/api/ (HTTP 200)
- **Terms / licence:** https://www.ebi.ac.uk/about/terms-of-use/ (HTTP 200) — “atics Institute (EMBL-EBI) promotes open science through its mission to provide freely available Data Resources and Tools (which includes online services, databases and software) to the largest possible community”
- **Measurement note (latest representative round):** runs first made public 2026-10-05..2026-10-11 (7 days)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |
| 2026-10-13T02:11 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |
| 2026-10-13T03:23 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |

<details><summary>Sample event — 196 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `run_accession` | ERR18022750 |
| `experiment_title` | Revio sequencing |
| `sample_accession` | SAMEA123079245 |
| `project_name` |  |
| `submission_accession` | ERA37358500 |
| `library_min_fragment_size` |  |
| `bam_md5` |  |
| `assembly_software` |  |
| `library_prep_longitude` |  |
| `library_selection` | RANDOM |
| `pcr_isolation_protocol` |  |
| `chip_protocol` |  |
| `sequencing_primer_provider` |  |
| `serotype` |  |
| `environment_feature` | ENVO:01000407 |
| `last_updated` | 2026-10-11 |
| `submitted_galaxy` | ftp.sra.ebi.ac.uk/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| `extraction_protocol` |  |
| `germline` |  |
| `secondary_project` |  |
| `culture_collection` |  |
| `submission_tool` |  |
| `sra_bytes` |  |
| `read_strand` |  |
| `rna_purity_280_ratio` |  |
| `hi_c_protocol` |  |
| `collected_by` |  |
| `submitted_ftp` | ftp.sra.ebi.ac.uk/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| `restriction_enzyme_target_sequence` |  |
| `isolate` |  |
| `fastq_bytes` |  |
| `instrument_platform` | PACBIO_SMRT |
| `variety` |  |
| `sra_file_role` |  |
| `sequencing_date_format` |  |
| `temperature` |  |
| `sra_aspera` |  |
| `ecotype` |  |
| `submitted_aspera` | fasp.sra.ebi.ac.uk:/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| `sampling_campaign` |  |
| `bam_ftp` |  |
| `tissue_lib` |  |
| `environmental_sample` |  |
| `control_experiment` |  |
| `sex` |  |
| `submitted_md5` | b81ad61ab20a36538b9396e8331a0ae8 |
| `checklist` | ERC000024 |
| `fastq_galaxy` |  |
| `library_gen_protocol` |  |
| `specimen_voucher` |  |
| `library_prep_latitude` |  |
| `submitted_bytes` | 3508305175 |
| `taxonomic_identity_marker` |  |
| `run_date` |  |
| `country` | USA |
| `ncbi_reporting_standard` |  |
| `sample_description` |  |
| `sra_galaxy` |  |
| `sample_prep_interval` |  |
| `fastq_md5` |  |
| `secondary_study_accession` | ERP201065 |
| `experimental_protocol` |  |
| `read_count` | 0 |
| `study_title` | EDNAID metagenomic study |
| `bio_material` |  |
| `fastq_file_role` |  |
| `rna_prep_5_protocol` |  |
| `host_body_site` |  |
| `local_environmental_context` | ENVO:01000407 |
| `assembly_quality` |  |
| `collection_date_end` | 2026-04-16 |
| `sample_capture_status` |  |
| `sample_title` |  |
| `host_genotype` |  |
| `host_phenotype` |  |
| `environmental_medium` | ENVO:00002149 |
| `cultivar` |  |
| `instrument_model` | Revio |
| `faang_library_selection` |  |
| `target_gene` |  |
| `bam_bytes` |  |
| `library_max_fragment_size` |  |
| `experiment_target` |  |
| `sequencing_date` |  |
| `description` | Revio sequencing |
| `bam_file_role` |  |
| `nominal_sdev` |  |
| `chip_ab_provider` |  |
| `environment_material` | ENVO:00002149 |
| `host_tax_id` |  |
| `sample_material` |  |
| `sample_storage_processing` |  |
| `sra_md5` |  |
| `cell_type` |  |
| `fastq_ftp` |  |
| `disease` |  |
| `sample_prep_interval_units` |  |
| `broker_name` |  |
| `sub_strain` |  |
| `base_count` | 0 |
| `library_strategy` | WGS |
| `restriction_site` |  |
| `serovar` |  |
| `investigation_type` |  |
| `location` | 32.8634 N 117.2546 W |
| `library_source` | METAGENOMIC |
| `sra_ftp` |  |
| `age` |  |
| `library_layout` | PAIRED |
| `experimental_factor` |  |
| `sequencing_primer_catalog` |  |
| `environment_biome` | ENVO:00000447 |
| `rna_purity_230_ratio` |  |
| `dnase_protocol` |  |
| `dev_stage` |  |
| `library_prep_date_format` |  |
| `bam_aspera` |  |
| `binning_software` |  |
| `datahub` | dcc_metagenome |
| `rna_integrity_num` |  |
| `library_prep_date` |  |
| `location_start` | 32.8634 N 117.2546 W |
| `marine_region` |  |
| `aligned` |  |
| `file_location` |  |
| `sample_collection` |  |
| `chip_target` |  |
| `nominal_length` |  |
| `broad_scale_environmental_context` | ENVO:00000447 |
| `sequencing_location` |  |
| `status` | public |
| `completeness_score` |  |
| `lon` | -117.2546 |
| `fastq_aspera` |  |
| `tax_lineage` | 1;2787823;12908;408169;410657;1561972 |
| `host_sex` |  |
| `library_pcr_isolation_protocol` |  |
| `sample_alias` | 3281 |
| `mating_type` |  |
| `collection_date_start` | 2026-04-15 |
| `sub_species` |  |
| `contamination_score` |  |
| `run_alias` | run-5482 |
| `restriction_enzyme` |  |
| `depth` | 0.5 |
| `submitted_file_role` | SUBMISSION_FILE |
| `submitted_read_type` | PAIRED |
| `library_construction_protocol` |  |
| `host_growth_conditions` |  |
| `collection_date` | 2026-04-16 |
| `experiment_alias` | 30481 |
| `host_gravidity` |  |
| `center_name` | University of California San Diego Microbiome Initiative;UCSDMI |
| `identified_by` |  |
| `cell_line` |  |
| `sampling_site` |  |
| `host` |  |
| `library_name` |  |
| `tag` | env_tax:marine;env_geo;env_geo:coastal;env_geo:terrestrial;env_tax |
| `first_created` | 2026-10-06 |
| `lat` | 32.8634 |
| `strain` |  |
| `experiment_accession` | ERX17413712 |
| `scientific_name` | seawater metagenome |
| `host_status` |  |
| `tax_id` | 1561972 |
| `study_accession` | PRJEB120985 |
| `submitted_format` | FASTQ |
| `submitted_host_sex` |  |
| `surveillance_target` |  |
| `bisulfite_protocol` |  |
| `altitude` |  |
| `rt_prep_protocol` |  |
| `host_scientific_name` |  |
| `bam_galaxy` |  |
| `accession` | ERR18022750 |
| `secondary_sample_accession` | ERS30780806 |
| `sample_storage` |  |
| `cage_protocol` |  |
| `sampling_platform` |  |
| `taxonomic_classification` |  |
| `location_end` | 32.8634 N 117.2546 W |
| `protocol_label` |  |
| `elevation` |  |
| `salinity` |  |
| `sequencing_method` |  |
| `sequencing_primer_lot` |  |
| `first_public` | 2026-10-11 |
| `transposase_protocol` |  |
| `study_alias` | 25006 |
| `library_prep_location` |  |
| `rna_prep_3_protocol` |  |
| `ph` |  |
| `sequencing_longitude` |  |
| `tissue_type` |  |
| `isolation_source` |  |

</details>

<a id="s-stellar"></a>
### 49. Stellar Horizon operations stream

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.17 events/s, median 22.0 attributes per event.
- **Delivery:** live · Server-Sent Events
- **Endpoint:** `https://horizon.stellar.org/operations?cursor=now`
- **Request:** `GET with Accept: text/event-stream`
- **Access:** None
- **Documentation:** https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming (HTTP 200)
- **Terms / licence:** https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming (HTTP 200) — “Streaming \| Stellar Docs {"@context":"https://schema”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.17 | 10 | 60 | 22.0 | 22 | 24 |
| 2026-10-13T02:11 | ok | 0.17 | 10 | 60 | 22.0 | 24 | 24 |
| 2026-10-13T03:23 | ok | 0.17 | 10 | 60 | 17.0 | 22 | 25 |

<details><summary>Sample event — 24 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `_links.self.href` | https://horizon.stellar.org/operations/278804997406212097 |
| `_links.transaction.href` | https://horizon.stellar.org/transactions/7e0e234cb85de906bcab19b1dcb0e2485c86de85ec8054fc… |
| `_links.effects.href` | https://horizon.stellar.org/operations/278804997406212097/effects |
| `_links.succeeds.href` | https://horizon.stellar.org/effects?order=desc&cursor=278804997406212097 |
| `_links.precedes.href` | https://horizon.stellar.org/effects?order=asc&cursor=278804997406212097 |
| `id` | 278804997406212097 |
| `paging_token` | 278804997406212097 |
| `transaction_successful` | true |
| `source_account` | GAPLYDVLMPHXGWPXHTSWUKG7R5FVVXNRXHDPMDVADJTPNSGOR7HRVYJD |
| `type` | manage_sell_offer |
| `type_i` | 3 |
| `created_at` | 2026-10-13T02:11:57Z |
| `transaction_hash` | 7e0e234cb85de906bcab19b1dcb0e2485c86de85ec8054fc19a9beacd545f1bf |
| `amount` | 0.1911935 |
| `price` | 1.0000944 |
| `price_r.n` | 125011800 |
| `price_r.d` | 125000000 |
| `buying_asset_type` | credit_alphanum12 |
| `buying_asset_code` | PYUSD |
| `buying_asset_issuer` | GDQE7IXJ4HUHV6RQHIUPRJSEZE4DRS5WY577O2FY6YQ5LVWZ7JZTU2V5 |
| `selling_asset_type` | credit_alphanum4 |
| `selling_asset_code` | USDC |
| `selling_asset_issuer` | GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN |
| `offer_id` | 1861295388 |

</details>

<a id="s-mlb"></a>
### 50. MLB Stats API live game feed

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.06 events/s, median 44.0 attributes per event.
- **Delivery:** poll · REST JSON (GUMBO), polled every 10 s
- **Endpoint:** `https://statsapi.mlb.com/api/v1.1/game/<gamePk>/feed/live`
- **Request:** `GET (schedule: /api/v1/schedule?sportId=1&date=...)`
- **Access:** None
- **Documentation:** https://statsapi.mlb.com/ (HTTP 200)
- **Terms / licence:** https://gdx.mlb.com/components/copyright.txt (HTTP 200) — “Only individual, non-commercial, non-bulk use of the Materials is permitted and any other use of the Materials is prohibited without prior written authorization from MLBAM”
- **Measurement note (latest representative round):** 5 polls every 10s; 5 records per snapshot; rate = new/changed records per second; game 849820 (1 live)

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.05 | 3 | 56 | 44.0 | 48 | 48 |
| 2026-10-13T02:11 | ok | 0.06 | 3 | 50 | 44.0 | 47 | 48 |
| 2026-10-13T03:23 | idle | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T03:23 idle: 2 games scheduled, none live at sampling time

<details><summary>Sample event — 48 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `result.type` | atBat |
| `result.event` | Flyout |
| `result.eventType` | field_out |
| `result.description` | Jonathan Aranda flies out sharply to center fielder Steven Kwan. |
| `result.rbi` | 0 |
| `result.awayScore` | 2 |
| `result.homeScore` | 2 |
| `result.isOut` | true |
| `about.atBatIndex` | 56 |
| `about.halfInning` | bottom |
| `about.isTopInning` | false |
| `about.inning` | 7 |
| `about.startTime` | 2026-10-13T02:09:31.364Z |
| `about.endTime` | 2026-10-13T02:10:46.864Z |
| `about.isComplete` | true |
| `about.isScoringPlay` | false |
| `about.hasReview` | false |
| `about.hasOut` | true |
| `about.captivatingIndex` | 0 |
| `count.balls` | 1 |
| `count.strikes` | 1 |
| `count.outs` | 2 |
| `matchup.batter.id` | 666018 |
| `matchup.batter.fullName` | Jonathan Aranda |
| `matchup.batter.link` | /api/v1/people/666018 |
| `matchup.batSide.code` | L |
| `matchup.batSide.description` | Left |
| `matchup.pitcher.id` | 683769 |
| `matchup.pitcher.fullName` | Hunter Gaddis |
| `matchup.pitcher.link` | /api/v1/people/683769 |
| `matchup.pitchHand.code` | R |
| `matchup.pitchHand.description` | Right |
| `matchup.postOnFirst.id` | 650490 |
| `matchup.postOnFirst.fullName` | Yandy Díaz |
| `matchup.postOnFirst.link` | /api/v1/people/650490 |
| `matchup.batterHotColdZoneStats.stats` | [{'type': {'displayName': 'hotColdZones'}, 'group': {'displayName': 'hitting'}, 'exemptio… |
| `matchup.batterHotColdZones` | [{'zone': '01', 'color': 'rgba(255, 255, 255, 0.55)', 'temp': 'lukewarm', 'value': '-'}, … |
| `matchup.pitcherHotColdZones` | [] |
| `matchup.splits.batter` | vs_RHP |
| `matchup.splits.pitcher` | vs_LHB |
| `matchup.splits.menOnBase` | Men_On |
| `pitchIndex` | [0, 1, 2] |
| `actionIndex` | [] |
| `runnerIndex` | [0] |
| `runners` | [{'movement': {'originBase': None, 'start': None, 'end': None, 'outBase': '1B', 'isOut': … |
| `playEvents` | [{'details': {'call': {'code': 'S', 'description': 'Swinging Strike'}, 'description': 'Sw… |
| `playEndTime` | 2026-10-13T02:10:46.864Z |
| `atBatIndex` | 56 |

</details>

<a id="s-hn"></a>
### 51. Hacker News items (Firebase API)

- **Verdict:** Neither — average 0.14 events/s, median 6.0 attributes per event.
- **Delivery:** counter · REST JSON (also Firebase SSE)
- **Endpoint:** `https://hacker-news.firebaseio.com/v0/maxitem.json ; /v0/item/<id>.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/HackerNews/API (HTTP 200)
- **Terms / licence:** https://github.com/HackerNews/API (HTTP 200) — “There is currently no rate limit”
- **Measurement note (latest representative round):** item ids allocated over the window

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.20 | 13 | 64 | 6.0 | 6 | 6 |
| 2026-10-13T02:11 | ok | 0.12 | 8 | 65 | 6.0 | 6 | 6 |
| 2026-10-13T03:23 | ok | 0.08 | 5 | 60 | 6.0 | 6 | 6 |

<details><summary>Sample event — 6 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `by` | ‹redacted› |
| `id` | 50065731 |
| `parent` | 50059122 |
| `text` | ‹redacted› |
| `time` | 1791857454 |
| `type` | comment |

</details>

<a id="s-aprs"></a>
### 52. APRS-IS amateur-radio packet network (full feed)

- **Verdict:** Neither — average 0.00 events/s, median — attributes per event.
- **Delivery:** live · Raw TCP text lines
- **Endpoint:** `tcp://rotate.aprs2.net:10152`
- **Request:** `user N0CALL pass -1 vers <app> <ver>`
- **Access:** Read-only login with pass -1
- **Documentation:** https://www.aprs-is.net/Connecting.aspx (HTTP 200)
- **Terms / licence:** https://www.aprs-is.net/Connecting.aspx (HTTP 200) — “-1 is used for receive-only”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T02:11 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |

No event was received, so no sample is available.

<a id="s-bitmex"></a>
### 53. BitMEX realtime trade/quote/instrument

- **Verdict:** Neither — average 0.00 events/s, median — attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.bitmex.com/realtime`
- **Request:** `{"op":"subscribe","args":["trade:XBTUSD","quote:XBTUSD",...]}`
- **Access:** None
- **Documentation:** https://www.bitmex.com/app/wsAPI (HTTP 200)
- **Terms / licence:** https://www.bitmex.com/app/wsAPI (HTTP 200) — “You may subscribe to real-time changes on any available table”

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T02:11 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |

No event was received, so no sample is available.

<a id="s-nostr"></a>
### 54. Nostr public notes (kind 1) across 4 relays

- **Verdict:** Neither — average 0.80 events/s, median 7.0 attributes per event.
- **Delivery:** live · WebSocket (NIP-01)
- **Endpoint:** `wss://nos.lol, wss://relay.primal.net, wss://relay.damus.io, wss://nostr.mom`
- **Request:** `["REQ","sub",{"kinds":[1],"since":<now>}]`
- **Access:** None
- **Documentation:** https://github.com/nostr-protocol/nips/blob/master/01.md (HTTP 200)
- **Terms / licence:** https://github.com/nostr-protocol/nips/blob/master/01.md (HTTP 200) — “inds"},{"level":2,"text":"Communication between clients and relays","anchor":"communication-between-clients-and-relays","htmlText":"Communication between clients and relays"},{"level":3”
- **Measurement note (latest representative round):** kind-1 notes deduplicated by id across relays that accepted the connection: wss://relay.damus.io, wss://nos.lol, wss://relay.primal.net, wss://nostr.mom

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.00 | 60 | 60 | 7.0 | 7 | 7 |
| 2026-10-13T02:11 | ok | 0.63 | 38 | 60 | 7.0 | 7 | 7 |
| 2026-10-13T03:23 | ok | 0.77 | 46 | 60 | 7.0 | 7 | 7 |

<details><summary>Sample event — 7 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `content` | ‹redacted› |
| `created_at` | 1791857418 |
| `id` | ‹redacted› |
| `kind` | 1 |
| `pubkey` | ‹redacted› |
| `sig` | ‹redacted› |
| `tags` | ‹redacted› |

</details>

<a id="s-mbta_sse"></a>
### 55. MBTA V3 API vehicle streaming (Server-Sent Events)

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** live · Server-Sent Events
- **Endpoint:** `https://api-v3.mbta.com/vehicles?filter[route_type]=0,1,2,3`
- **Request:** `GET with Accept: text/event-stream`
- **Access:** Returned 406 without a key
- **Documentation:** https://www.mbta.com/developers/v3-api/streaming (HTTP 200)
- **Terms / licence:** https://www.mbta.com/developers/v3-api/streaming (HTTP 200) — “Specify an API key (either with the X-API-Key header or the api_key query parameter)”
- **Measurement note (latest representative round):**  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | error | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''; 2026-10-13T02:11 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''; 2026-10-13T03:23 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''

No event was received, so no sample is available.

<a id="s-kystverket_ais"></a>
### 56. Kystverket (Norwegian Coastal Administration) open AIS feed

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** live · Raw TCP NMEA 0183 (AIVDM)
- **Endpoint:** `tcp://153.44.253.27:5631`
- **Request:** `connect and read lines`
- **Access:** None
- **Documentation:** https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/ (HTTP 200)
- **Terms / licence:** https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/ (HTTP 200) — “The data are free and universally accessible, and are regulated under the Norwegian Licence for Open Government Data (NLOD)”
- **Measurement note (latest representative round):**  TimeoutError('timed out')

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | error | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 error:  TimeoutError('timed out'); 2026-10-13T02:11 error:  TimeoutError('timed out'); 2026-10-13T03:23 error:  TimeoutError('timed out')

No event was received, so no sample is available.

<a id="s-airplanes_live"></a>
### 57. airplanes.live aircraft API

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** poll · REST JSON
- **Endpoint:** `https://api.airplanes.live/v2/point/19.436/-99.072/250`
- **Request:** `GET`
- **Access:** Rejected (403): operator asks for an e-mail request
- **Documentation:** https://airplanes.live/api-docs/ (HTTP 200)
- **Terms / licence:** https://airplanes.live/terms-of-use/ (HTTP 200) — no matching text found
- **Measurement note (latest representative round):** HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'; 2026-10-13T02:11 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'; 2026-10-13T03:23 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'

No event was received, so no sample is available.

<a id="s-github_api"></a>
### 58. GitHub REST public events (unauthenticated)

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** poll · REST JSON
- **Endpoint:** `https://api.github.com/events`
- **Request:** `GET ?per_page=100`
- **Access:** None, but 60 requests/hour without a token
- **Documentation:** https://docs.github.com/en/rest/activity/events (HTTP 200)
- **Terms / licence:** https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api (HTTP 200) — “60 requests per hour”
- **Measurement note (latest representative round):** HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | limited | — | 100 | — | 18.0 | 123 | 133 |
| 2026-10-13T02:11 | limited | — | 100 | — | 18.0 | 113 | 152 |
| 2026-10-13T03:23 | limited | — | 100 | — | 18.0 | 24 | 28 |

Non-OK rounds: 2026-10-13T02:10 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token; 2026-10-13T02:11 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token; 2026-10-13T03:23 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token

<details><summary>Sample event — 24 attributes (values truncated to 90 characters)</summary>

| Attribute | Example value |
|---|---|
| `id` | 23834301920 |
| `type` | CreateEvent |
| `actor.id` | ‹redacted› |
| `actor.login` | ‹redacted› |
| `actor.display_login` | ‹redacted› |
| `actor.gravatar_id` | ‹redacted› |
| `actor.url` | ‹redacted› |
| `actor.avatar_url` | ‹redacted› |
| `repo.id` | 1409622804 |
| `repo.name` | ortisun/sagat-octopus-orchestrator |
| `repo.url` | https://api.github.com/repos/ortisun/sagat-octopus-orchestrator |
| `payload.ref` | ‹redacted› |
| `payload.ref_type` | ‹redacted› |
| `payload.full_ref` | ‹redacted› |
| `payload.master_branch` | ‹redacted› |
| `payload.description` | ‹redacted› |
| `payload.pusher_type` | ‹redacted› |
| `public` | true |
| `created_at` | 2026-10-11T21:04:15Z |
| `org.id` | 292761479 |
| `org.login` | ortisun |
| `org.gravatar_id` |  |
| `org.url` | https://api.github.com/orgs/ortisun |
| `org.avatar_url` | https://avatars.githubusercontent.com/u/292761479? |

</details>

<a id="s-lasair"></a>
### 59. Rubin Observatory LSST alerts via Lasair broker (Kafka)

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** live · Kafka (kafka.lsst.ac.uk:9092)
- **Endpoint:** `kafka.lsst.ac.uk:9092 (topic per saved filter)`
- **Request:** `Kafka consumer`
- **Access:** Lasair account + saved filter required
- **Documentation:** https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html (HTTP 200)
- **Terms / licence:** https://rubinobservatory.org/for-scientists/data-products/alerts-and-brokers (HTTP 200) — “world public and have no proprietary period”
- **Measurement note (latest representative round):** HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>\n'

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…; 2026-10-13T02:11 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…; 2026-10-13T03:23 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…

No event was received, so no sample is available.

<a id="s-mastodon"></a>
### 60. Mastodon public streaming (mastodon.social)

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** live · WebSocket / SSE
- **Endpoint:** `https://mastodon.social/api/v1/streaming/public`
- **Request:** `GET`
- **Access:** Access token required (401)
- **Documentation:** https://docs.joinmastodon.org/methods/streaming/ (HTTP 200)
- **Terms / licence:** https://docs.joinmastodon.org/methods/streaming/ (HTTP 200) — “ontend guide Components State management CSS and styling Creating themes Design tokens reference Spec compliance ActivityPub WebFinger Security Microformats OAuth Bearcaps REST API Datetime formats Guideli”
- **Measurement note (latest representative round):** HTTP 401: b'{"error":"Missing access token"}'

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 rejected: HTTP 401: b'{"error":"Missing access token"}'; 2026-10-13T02:11 rejected: HTTP 401: b'{"error":"Missing access token"}'; 2026-10-13T03:23 rejected: HTTP 401: b'{"error":"Missing access token"}'

No event was received, so no sample is available.

<a id="s-zkillboard"></a>
### 61. zKillboard (EVE Online kills)

- **Verdict:** Not usable as tested — average — events/s, median — attributes per event.
- **Delivery:** live · WebSocket / RedisQ
- **Endpoint:** `wss://zkillboard.com/websocket/`
- **Request:** `{"action":"sub","channel":"killstream"}`
- **Access:** WebSocket returned 403 to this client
- **Documentation:** https://github.com/zKillboard/zKillboard/wiki (HTTP 200)
- **Terms / licence:** https://github.com/zKillboard/zKillboard/wiki (HTTP 200) — “ref":"/","aria-label":"Homepage "},"notifications":{"indicatorMode":"disabled","websocketChannel":null,"fetchIndicatorSrc":"/notifications/indicator","fetchIndicatorEnabled":false},"issues":{"href":"/issues"},”
- **Measurement note (latest representative round):** HTTP 200: b'[{"attackers":[{"corporation_id":1000125,"damage_done":2880,"final_blow":true,"security_status":0,"ship_type_id":3885}],"killmail_id":139126268,"killmail_time":"2026-10-13T03:18:31Z","solar_system_id"'

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | reachable | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | reachable | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | reachable | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:10 reachable: HTTP 200: b'[{"attackers":[{"alliance_id":99003581,"character_id":2123545746,"corporation_id":98598862,"damage_done":55548,"faction_id":500011,"final_blow":false,"security_status":5,"ship_type_id":47…; 2026-10-13T02:11 reachable: HTTP 200: b'[{"attackers":[{"alliance_id":99003581,"character_id":2123545746,"corporation_id":98598862,"damage_done":55548,"faction_id":500011,"final_blow":false,"security_status":5,"ship_type_id":47…; 2026-10-13T03:23 reachable: HTTP 200: b'[{"attackers":[{"corporation_id":1000125,"damage_done":2880,"final_blow":true,"security_status":0,"ship_type_id":3885}],"killmail_id":139126268,"killmail_time":"2026-10-13T03:18:31Z","sol…

No event was received, so no sample is available.

## 7. Sources that need a free API key

A source is in **Table 7.1** only if all of the following hold on the provider's own pages: the key is obtained by a free sign-up, no paid plan or paid upgrade was found, so the free key is the complete product, and the documented limits still allow the stream to be consumed. Every API with a key states some fair-use limit; the limit is quoted rather than hidden. Sources with a paid plan, a trial-level free plan, or a free plan restricted to a subset are listed in **Table 7.2** with the clause that excludes them. Free keys that do not deliver ≥1 event/s are in **Table 7.3**. aisstream.io (free key) is not repeated because the project document already lists it.

Evidence: 61 verbatim clauses were re-fetched from the providers' pages when this report was generated; 61 were found word for word (✅), 0 were not (❌, see the per-row status). “None found” for paid plans means no paid plan appeared on the pages checked — not a guarantee that none exists. Every sign-up link was fetched too (HTTP status shown next to it). Endpoints were probed without a key: an HTTP 401/403/400 “key missing” answer proves the endpoint is live and that the key is what gates it.

Measured rates use the keyless route of the same provider where one exists (FIRMS public 24 h files, MBTA REST without a key, TfL without a key); the other rows need the key before they can be measured.

### 7.1 Free key, no paid plan found — the free key is the full product

| # | Source | Category | How to get the key | Delivery | Documented limit | Paid plan | Measured ev/s | Attrs/event | Endpoint probe (no key) |
|---|---|---|---|---|---|---|---:|---:|---|
| K1 | [MBTA V3 API — vehicle streaming (Boston subway, bus, commuter rail, ferry)](#k-mbta_key) | Transport | [Developer account; key per app (“Getting a key might take a day”)](https://api-v3.mbta.com/register) (HTTP 200) | Server-Sent Events (Accept: text/event-stream + x-api-key) | 1,000 requests/min with key; increase on request; a streaming connection counts once | None found | 11.31 | 21 | HTTP 406: {"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"vers… |
| K2 | [MTA Bus Time SIRI — every New York City bus](#k-mta_bustime) | Transport | [Web form; key by e-mail (“within half an hour”)](https://register.developer.obanyc.com/) (HTTP 200) | REST JSON/XML (SIRI VehicleMonitoring), polled | No numeric limit stated on the pages checked | None found | — | — | HTTP 401: {"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-12T23:33:33.… |
| K3 | [WMATA — Washington DC Metrorail and Metrobus (train positions, GTFS-RT)](#k-wmata) | Transport | [Developer account; subscribe to a service tier to get keys](https://developer.wmata.com/signup) (HTTP 200) | REST JSON + GTFS-Realtime protobuf, polled (header api_key) | Tier limits are shown only after sign-in (portal is JavaScript-rendered); not verified | None now — WMATA reserves the right to charge in future | — | — | HTTP 401: { "statusCode": 401, "message": "Access denied due to missing subscri… |
| K4 | [Transport for London Unified API — Tube/bus/rail arrival predictions](#k-tfl) | Transport | [Developer account; subscribe to the “500 requests” product](https://api-portal.tfl.gov.uk/signup) (HTTP 200) | REST JSON, polled (app_key query parameter) | “500 requests data plan” (the portal does not state the time unit in the text retrieved) | None found | 2.05 | 26 | HTTP 200: [{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presenta… |
| K5 | [CTA Chicago Bus Tracker and Train Tracker](#k-cta) | Transport | [Application form; CTA reviews it (“we'll review your application”)](https://www.transitchicago.com/developers/bustracker/) (HTTP 200) | REST JSON/XML, polled | Bus Tracker: 100,000 transactions/day (≈1.16 requests/s); increase on request | None found | — | — | HTTP 200:  {"bustime-response": {"error": [ {     "msg": "No API access key s… |
| K6 | [NTA Ireland GTFS-Realtime — national bus and rail vehicles](#k-nta) | Transport | [Developer account (Azure API Management portal)](https://developer.nationaltransport.ie/signup) (HTTP 200) | GTFS-Realtime (protobuf or JSON), polled (header x-api-key) | One call every 60 s per token (each call returns the national feed) | None found | — | — | HTTP 401: { "statusCode": 401, "message": "Access denied due to missing subscri… |
| K7 | [NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS)](#k-firms) | Weather & environment | [E-mail only; MAP_KEY sent by e-mail](https://firms.modaps.eosdis.nasa.gov/api/map_key/) (HTTP 200) | REST CSV by area and day range (near real time) | 5,000 transactions per 10-minute interval; increase on request | None found | 3.28 | 13 | HTTP 400: Invalid MAP_KEY. |
| K8 | [ENTSO-E Transparency Platform — European electricity load, generation, prices](#k-entsoe) | Weather & environment | [Account + e-mail to transparency@entsoe.eu; granted “within 3 working days”](https://transparency.entsoe.eu/) (HTTP 200) | REST XML (IEC 62325), polled | 400 requests/min per token | None found | — | — | HTTP 401: <?xml version="1.0" encoding="UTF-8"?> <Acknowledgement_MarketDocumen… |
| K9 | [Lasair — Rubin Observatory LSST alert broker (Kafka per filter)](#k-lasair) | Science & sensors | [Lasair account; create a filter, then consume its Kafka topic](https://lasair.lsst.ac.uk/) (HTTP 200) | Kafka (kafka.lsst.ac.uk:9092, topic per saved filter) + REST API | REST: 100 calls/h (account), 10,000 calls/h for power users on request; no Kafka limit stated | None found | — | — | Kafka TCP 9092 open |
| K10 | [Fink — Rubin LSST / ZTF alert broker livestream](#k-fink) | Science & sensors | [Web form; credentials sent by the Fink team](https://forms.gle/2td4jysT4e9pkf889) (HTTP 200) | Kafka via fink-client (finkctl) | No limit stated on the pages checked | None found | — | — | — |
| K11 | [Mastodon streaming API — federated public timeline (e.g. mastodon.social)](#k-mastodon) | Games, media & social | [Free user account on an instance; create an application token in settings](https://mastodon.social/auth/sign_up) (HTTP 200) | Server-Sent Events or WebSocket | REST: 300 calls per 5 min per account; streaming not listed | None found | — | — | HTTP 401: {"error":"Missing access token"} |
| K12 | [Global Fishing Watch APIs — vessel events and fishing effort (AIS + VMS)](#k-gfw) | Transport | [Global Fishing Watch account; request an API token](https://globalfishingwatch.org/our-apis/) (HTTP 200) | REST JSON queries (not a push stream) | Non-commercial use only; numeric limits are on a documentation page that did not render | None (commercial use: contact them) | — | — | HTTP 401: {"error":"invalid token"} |

### 7.2 Excluded — paid plan, trial-level free plan, or restricted free subset

| Source | Category | Sign-up | Reason | Evidence (verbatim, re-verified) |
|---|---|---|---|---|
| OpenAQ v3 — air-quality measurements | Weather & environment | [link](https://explore.openaq.org/register) (HTTP 200) | Paid tier for a higher rate | ✅ “we offer a custom pricing option for a higher rate limit” — [https://docs.openaq.org/using-the-api/rate-limits](https://docs.openaq.org/using-the-api/rate-limits) (200)<br>✅ “60 / minute 2,000 / hour” — [https://docs.openaq.org/using-the-api/rate-limits](https://docs.openaq.org/using-the-api/rate-limits) (200) |
| opentransportdata.swiss GTFS-RT | Transport | [link](https://api-manager.opentransportdata.swiss/) (HTTP 200) | Free only below a 2 queries/min limit | ✅ “You can use your key to make a maximum of two queries per minute on the interface” — [https://opentransportdata.swiss/en/cookbook/realtime-predic…](https://opentransportdata.swiss/en/cookbook/realtime-prediction-cookbook/gtfs-rt/) (200)<br>✅ “Use of the data service is free of charge below the limit” — [https://opentransportdata.swiss/en/terms-of-use/](https://opentransportdata.swiss/en/terms-of-use/) (200) |
| Trafiklab GTFS Regional realtime (Sweden) | Transport | [link](https://developer.trafiklab.se/) (HTTP 200) | Entry level capped at 30,000 calls/month | ✅ “Bronze 50 30 000 Silver 250 2 000 000 Gold 500 22 500 000” — [https://www.trafiklab.se/api/gtfs-datasets/gtfs-regional/](https://www.trafiklab.se/api/gtfs-datasets/gtfs-regional/) (200) |
| 511 SF Bay Area transit API | Transport | [link](https://511.org/open-data/token) (HTTP 200) | 60 requests/hour; personal non-commercial use | ✅ “The default rate limit per API token is 60 requests per 3600 seconds” — [https://511.org/open-data/transit](https://511.org/open-data/transit) (200)<br>✅ “for your personal, individual, non-commercial, and non-automated use only” — [https://511.org/about/terms](https://511.org/about/terms) (200) |
| GitHub REST API (personal token) | Internet & software | [link](https://github.com/settings/tokens) (HTTP 200) | Higher limit only for paid Enterprise Cloud | ✅ “All of these requests count towards your personal rate limit of 5,000 requests per hour” — [https://docs.github.com/en/rest/using-the-rest-api/rate-lim…](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) (200)<br>✅ “GitHub Enterprise Cloud organization have a higher rate limit of 15,000 requests per hour” — [https://docs.github.com/en/rest/using-the-rest-api/rate-lim…](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) (200) |
| abuse.ch URLhaus / ThreatFox | Internet & software | [link](https://auth.abuse.ch/) (HTTP 200) | Commercial use may need a paid subscription | ✅ “This API is available free of charge under the fair use principles” — [https://urlhaus.abuse.ch/api/](https://urlhaus.abuse.ch/api/) (200)<br>✅ “may require a paid subscription” — [https://urlhaus.abuse.ch/api/](https://urlhaus.abuse.ch/api/) (200) |
| Alpaca market data | Finance & blockchain | [link](https://app.alpaca.markets/signup) (HTTP 200) | Free plan limited to IEX and 30 symbols; full plan $99/month | ✅ “Basic Algo Trader Plus Pricing Free $99 / month” — [https://docs.alpaca.markets/us/docs/about-market-data-api](https://docs.alpaca.markets/us/docs/about-market-data-api) (200)<br>✅ “Websocket subscriptions 30 symbols Unlimited” — [https://docs.alpaca.markets/us/docs/about-market-data-api](https://docs.alpaca.markets/us/docs/about-market-data-api) (200) |
| Alpha Vantage | Finance & blockchain | [link](https://www.alphavantage.co/support/#api-key) (HTTP 200) | 25 requests/day free; premium plan | ✅ “For use cases that exceed our standard API usage limit (25 API requests per day) or require certain premium API functions, we offer a premium plan” — [https://www.alphavantage.co/premium/](https://www.alphavantage.co/premium/) (200) |
| OpenWeather | Weather & environment | [link](https://home.openweathermap.org/users/sign_up) (HTTP 200) | 1,000 free calls/day, then pay per call | ✅ “First 1,000 API calls per day are FREE” — [https://openweathermap.org/price](https://openweathermap.org/price) (200) |
| Tomorrow.io Weather API | Weather & environment | [link](https://app.tomorrow.io/signup) (HTTP 200) | Limits depend on the paid plan | ✅ “According to your plan, you are limited to a certain amount of requests per hour and day” — [https://docs.tomorrow.io/reference/rate-limiting](https://docs.tomorrow.io/reference/rate-limiting) (200) |
| aviationstack flight data | Transport | [link](https://aviationstack.com/signup/free) (HTTP 200) | Free plan is for trying the API; commercial use and premium features are in paid plans | ✅ “The aviationstack Free Plan offers a way to implement the API in your application and try it out using real-time flight data” — [https://aviationstack.com/pricing](https://aviationstack.com/pricing) (200)<br>✅ “Basic level - commercial use with premium features and up to 10,000 monthly requests” — [https://aviationstack.com/pricing](https://aviationstack.com/pricing) (200) |
| ADS-B Exchange Community API | Transport | [link](https://www.adsbexchange.com/community/developer-hub/) (HTTP 200) | Non-commercial; enterprise plans above the limits | ✅ “The Community API (formerly API Lite) is built for non-commercial use” — [https://www.adsbexchange.com/community/developer-hub/](https://www.adsbexchange.com/community/developer-hub/) (200)<br>✅ “If you start hitting limits or need commercial use, we have Enterprise options for you” — [https://www.adsbexchange.com/community/developer-hub/](https://www.adsbexchange.com/community/developer-hub/) (200) |
| Infura blockchain RPC | Finance & blockchain | [link](https://app.infura.io/register) (HTTP 200) | Free Core plan; paid plans add throughput | ✅ “Developer US$50 / month” — [https://www.infura.io/pricing](https://www.infura.io/pricing) (200) |
| Alchemy blockchain RPC | Finance & blockchain | [link](https://dashboard.alchemy.com/signup) (HTTP 200) | Free 30M compute units/month; pay-as-you-go above | ✅ “Free 30M CU per month” — [https://www.alchemy.com/pricing](https://www.alchemy.com/pricing) (200)<br>✅ “Pay as You Go Pay for what you use” — [https://www.alchemy.com/pricing](https://www.alchemy.com/pricing) (200) |
| X (Twitter) API | Games, media & social | [link](https://console.x.com/) (HTTP 200) | Pay per use | ✅ “The X API uses pay-per-usage pricing with no subscriptions” — [https://docs.x.com/x-api/getting-started/pricing](https://docs.x.com/x-api/getting-started/pricing) (200) |
| The Guardian Open Platform | Games, media & social | [link](https://bonobo.capi.gutools.co.uk/register/developer) (HTTP 200) | Free key only for non-commercial use | ✅ “Free for non-commercial usage” — [https://open-platform.theguardian.com/access/](https://open-platform.theguardian.com/access/) (200) |
| NewsAPI.org | Games, media & social | [link](https://newsapi.org/register) (HTTP 200) | Free only for development | ✅ “Free for development, options if you're commercial” — [https://newsapi.org/pricing](https://newsapi.org/pricing) (200) |
| PurpleAir sensors API | Weather & environment | [link](https://develop.purpleair.com/) (HTTP 200) | Paid points except for your own sensor | ✅ “If you are a PurpleAir sensor owner, you can get data from your own sensor for free” — [https://community.purpleair.com/t/api-pricing/4523](https://community.purpleair.com/t/api-pricing/4523) (200) |

### 7.3 Free key and no paid plan, but not a ≥1 event/s stream

| Source | Category | Sign-up | Why it does not qualify | Evidence (verbatim, re-verified) |
|---|---|---|---|---|
| Stack Exchange API — Stack Overflow questions/answers/comments | Internet & software | [link](https://stackapps.com/apps/oauth/register) (HTTP 200) | Free key (10,000 requests/day), but measured activity is far below 1 event/s. Measured 2026-10-13T03:32:30Z: 29 posts+comments in the last hour on Stack Overflow (0.008/s); the API's own site statistics report 2.53 questions/min and 3.77 answers/min (≈0.10/s) | ✅ “which by default is 10,000” — [https://api.stackexchange.com/docs/throttle](https://api.stackexchange.com/docs/throttle) (200) |
| Banco de México SIE API — FX FIX, rates, indicators (Mexico) | Finance & blockchain | [link](https://www.banxico.org.mx/SieAPIRest/service/v1/token) (HTTP 200) | Free token; economic time series (e.g. the daily FIX), not an event stream | ✅ “Máximo 80 consultas en 1 minuto 40,000 consultas por día” — [https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limite…](https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limiteConsultas) (200)<br>✅ “Todas las solicitudes que se realicen al API requieren enviar un token de consulta” — [https://www.banxico.org.mx/SieAPIRest/service/v1/](https://www.banxico.org.mx/SieAPIRest/service/v1/) (200) |
| US EIA Open Data — hourly electric grid monitor | Weather & environment | [link](https://www.eia.gov/opendata/register.php) (HTTP 200) | Free key; hourly aggregated series, not an event stream | ✅ “Energy Information Administration is committed to its free and open data by making it available through an Application Programming Interface (API)” — [https://www.eia.gov/opendata/](https://www.eia.gov/opendata/) (200) |
| Steam Web API | Games, media & social | [link](https://steamcommunity.com/dev/apikey) (HTTP 200) | Free key; request/response lookups, no public event stream | ✅ “Valve makes the Steam Web API available free” — [https://steamcommunity.com/dev/apiterms](https://steamcommunity.com/dev/apiterms) (200) |

### 7.4 Detail of Table 7.1

<a id="k-mbta_key"></a>
#### K1. MBTA V3 API — vehicle streaming (Boston subway, bus, commuter rail, ferry)

- **Get the key:** https://api-v3.mbta.com/register (HTTP 200) — Developer account; key per app (“Getting a key might take a day”)
- **Delivery:** Server-Sent Events (Accept: text/event-stream + x-api-key)
- **Endpoint:** `https://api-v3.mbta.com/vehicles`
- **Documented limit:** 1,000 requests/min with key; increase on request; a streaming connection counts once
- **Paid plan:** None found
- **Probe without key:** HTTP 406 — `{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}`
- **Measured (2026-10-13T03:31:28Z):** 11.31 events/s (694 events in 61 s), median 21 attributes per event. Keyless REST polling (4 polls, ~20 s apart); counted vehicles whose updated_at changed. The keyed SSE stream pushes the same updates.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “A valid key is required to make a default of 1,000 requests per minute, control the version , and stream requests” — https://www.mbta.com/developers/v3-api (HTTP 200)
  - ✅ “Requests made with a valid API key are limited to 1,000 requests per minute” — https://www.mbta.com/developers/v3-api/best-practices (HTTP 200)
  - ✅ “Currently, only the initial request counts against your API key rate limit” — https://www.mbta.com/developers/v3-api/streaming (HTTP 200)
  - ✅ “Getting a key might take a day” — https://api-v3.mbta.com/ (HTTP 200)

<details><summary>Sample record — 21 attributes</summary>

| Attribute | Example value |
|---|---|
| `attributes.bearing` | 195 |
| `attributes.carriages` | [{"label": "1930", "occupancy_status": "MANY_SEATS_AVAILABLE", "occupancy_percentage": 5}… |
| `attributes.current_status` | IN_TRANSIT_TO |
| `attributes.current_stop_sequence` | 150 |
| `attributes.direction_id` | 0 |
| `attributes.label` | 1930 |
| `attributes.latitude` | 42.30671 |
| `attributes.longitude` | -71.05498 |
| `attributes.occupancy_status` | null |
| `attributes.revenue` | REVENUE |
| `attributes.speed` | null |
| `attributes.updated_at` | 2026-10-12T23:29:55-04:00 |
| `id` | R-548C146D |
| `links.self` | /vehicles/R-548C146D |
| `relationships.route.data.id` | Red |
| `relationships.route.data.type` | route |
| `relationships.stop.data.id` | 70089 |
| `relationships.stop.data.type` | stop |
| `relationships.trip.data.id` | 77928633 |
| `relationships.trip.data.type` | trip |
| `type` | vehicle |

</details>


<a id="k-mta_bustime"></a>
#### K2. MTA Bus Time SIRI — every New York City bus

- **Get the key:** https://register.developer.obanyc.com/ (HTTP 200) — Web form; key by e-mail (“within half an hour”)
- **Delivery:** REST JSON/XML (SIRI VehicleMonitoring), polled
- **Endpoint:** `https://bustime.mta.info/api/siri/vehicle-monitoring.json?key=<KEY>`
- **Documented limit:** No numeric limit stated on the pages checked
- **Paid plan:** None found
- **Probe without key:** HTTP 401 — `{"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-12T23:33:33.268-04:00","VehicleMonitoringDelivery":[{"ResponseTimestamp":"2026-10-12T23:33:33.268-04:00","ErrorCondition":{"OtherError":{"Erro…`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “MTA Bus Time is built with a real-time developer API that anyone can use for free” — https://bustime.mta.info/developers (HTTP 200)
  - ✅ “You will receive one within half an hour” — https://bustime.mta.info/developers (HTTP 200)
  - ✅ “VehicleMonitoring : real-time information about one, many, or all vehicles tracked by the system” — https://bustime.mta.info/developers/siri (HTTP 200)

<a id="k-wmata"></a>
#### K3. WMATA — Washington DC Metrorail and Metrobus (train positions, GTFS-RT)

- **Get the key:** https://developer.wmata.com/signup (HTTP 200) — Developer account; subscribe to a service tier to get keys
- **Delivery:** REST JSON + GTFS-Realtime protobuf, polled (header api_key)
- **Endpoint:** `https://api.wmata.com/TrainPositions/TrainPositions?contentType=json ; https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb`
- **Documented limit:** Tier limits are shown only after sign-in (portal is JavaScript-rendered); not verified
- **Paid plan:** None now — WMATA reserves the right to charge in future
- **Probe without key:** HTTP 401 — `{ "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “Use of our APIs and other data is free of charge!” — https://developer.wmata.com/ (HTTP 200)
  - ✅ “WMATA currently provides the Transit Data, API and GTFS for free, but WMATA reserves the right to charge for the Transit Data, API and/or GTFS in the future” — https://developer.wmata.com/license (HTTP 200)
  - ✅ “You must create a developer account with WMATA and subscribe to one or more Transit Data service tiers” — https://developer.wmata.com/license (HTTP 200)

<a id="k-tfl"></a>
#### K4. Transport for London Unified API — Tube/bus/rail arrival predictions

- **Get the key:** https://api-portal.tfl.gov.uk/signup (HTTP 200) — Developer account; subscribe to the “500 requests” product
- **Delivery:** REST JSON, polled (app_key query parameter)
- **Endpoint:** `https://api.tfl.gov.uk/Mode/tube/Arrivals?app_key=<KEY>`
- **Documented limit:** “500 requests data plan” (the portal does not state the time unit in the text retrieved)
- **Paid plan:** None found
- **Probe without key:** HTTP 200 — `[{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities","id":"-934086842","operationType":1,"vehicleId":"117","naptanId":"940GZZLUKWG","stationName":"Kew Gardens Undergrou…`
- **Measured (2026-10-13T03:32:29Z):** 2.05 events/s (125 events in 61 s), median 26 attributes per event. Keyless polling of /Mode/tube/Arrivals (3 polls, 30 s apart); counted predictions that were new or whose expected arrival/location changed.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “create a subscription for the 500 requests data plan” — https://api-portal.tfl.gov.uk/ (HTTP 200)
  - ✅ “The public TfL data (or 'open data') released here is for open data users to use in their own software and services” — https://api-portal.tfl.gov.uk/ (HTTP 200)

<details><summary>Sample record — 27 attributes</summary>

| Attribute | Example value |
|---|---|
| `$type` | Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities |
| `id` | 1910276506 |
| `operationType` | 1 |
| `vehicleId` | 204 |
| `naptanId` | 940GZZLUVIC |
| `stationName` | Victoria Underground Station |
| `lineId` | victoria |
| `lineName` | Victoria |
| `platformName` | Northbound - Platform 3 |
| `direction` | outbound |
| `bearing` |  |
| `destinationNaptanId` | 940GZZLUWWL |
| `destinationName` | Walthamstow Central Underground Station |
| `timestamp` | 2026-10-13T03:31:07.8365706Z |
| `timeToStation` | 28 |
| `currentLocation` | Victoria Siding |
| `towards` | Walthamstow Central |
| `expectedArrival` | 2026-10-13T03:31:35Z |
| `timeToLive` | 2026-10-13T03:31:35Z |
| `modeName` | tube |
| `timing.$type` | Tfl.Api.Presentation.Entities.PredictionTiming, Tfl.Api.Presentation.Entities |
| `timing.countdownServerAdjustment` | 00:00:00 |
| `timing.source` | 0001-01-01T00:00:00 |
| `timing.insert` | 0001-01-01T00:00:00 |
| `timing.read` | 2026-10-13T03:31:01.822Z |
| `timing.sent` | 2026-10-13T03:31:07Z |
| `timing.received` | 0001-01-01T00:00:00 |

</details>


<a id="k-cta"></a>
#### K5. CTA Chicago Bus Tracker and Train Tracker

- **Get the key:** https://www.transitchicago.com/developers/bustracker/ (HTTP 200) — Application form; CTA reviews it (“we'll review your application”)
- **Delivery:** REST JSON/XML, polled
- **Endpoint:** `https://www.ctabustracker.com/bustime/api/v2/getvehicles?key=<KEY>&rt=<routes>&format=json ; https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=<KEY>&rt=red&outputType=JSON`
- **Documented limit:** Bus Tracker: 100,000 transactions/day (≈1.16 requests/s); increase on request
- **Paid plan:** None found
- **Probe without key:** HTTP 200 — ` {"bustime-response": {"error": [ {     "msg": "No API access key supplied" } ] }}   	`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “By default, the Bus Tracker API has a transaction limit of 100,000* transactions/day” — https://www.transitchicago.com/developers/bustracker/ (HTTP 200)
  - ✅ “Use our API Key Application Form to request a key and we'll review your application as soon as possible” — https://www.transitchicago.com/developers/traintracker/ (HTTP 200)

<a id="k-nta"></a>
#### K6. NTA Ireland GTFS-Realtime — national bus and rail vehicles

- **Get the key:** https://developer.nationaltransport.ie/signup (HTTP 200) — Developer account (Azure API Management portal)
- **Delivery:** GTFS-Realtime (protobuf or JSON), polled (header x-api-key)
- **Endpoint:** `https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json`
- **Documented limit:** One call every 60 s per token (each call returns the national feed)
- **Paid plan:** None found
- **Probe without key:** HTTP 401 — `{ "statusCode": 401, "message": "Access denied due to missing subscription key. Make sure to include subscription key when making requests to an API." }`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “Each Token will be restricted to calling the GTFS Real Time API once every 60 seconds” — https://developer.nationaltransport.ie/usagepolicy (HTTP 200)
  - ✅ “To view and use the API you need to sign up to acquire keys” — https://developer.nationaltransport.ie/ (HTTP 200)

<a id="k-firms"></a>
#### K7. NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS)

- **Get the key:** https://firms.modaps.eosdis.nasa.gov/api/map_key/ (HTTP 200) — E-mail only; MAP_KEY sent by e-mail
- **Delivery:** REST CSV by area and day range (near real time)
- **Endpoint:** `https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/VIIRS_NOAA20_NRT/world/1`
- **Documented limit:** 5,000 transactions per 10-minute interval; increase on request
- **Paid plan:** None found
- **Probe without key:** HTTP 400 — `Invalid MAP_KEY.`
- **Measured (2026-10-13T03:30:27Z):** 3.28 events/s (283,611 events in 86,400 s), median 13 attributes per event. Detections in the public 24 h global files of 4 sensors ÷ 86,400 s; the MAP_KEY API serves the same products by area and day range.
  - Files: VIIRS NOAA-20: 80,005 rows (HTTP 200); VIIRS NOAA-21: 106,679 rows (HTTP 200); VIIRS S-NPP: 77,050 rows (HTTP 200); MODIS: 19,877 rows (HTTP 200)
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “sign up for free MAP_KEY using your email” — https://firms.modaps.eosdis.nasa.gov/api/map_key/ (HTTP 200)
  - ✅ “MAP_KEY limit is 5000 transactions / 10-minute interval” — https://firms.modaps.eosdis.nasa.gov/api/area/ (HTTP 200)
  - ✅ “Contact us if you need limit increase” — https://firms.modaps.eosdis.nasa.gov/api/area/ (HTTP 200)

<details><summary>Sample record — 13 attributes</summary>

| Attribute | Example value |
|---|---|
| `latitude` | -19.08525 |
| `longitude` | -169.85228 |
| `bright_ti4` | 335.75 |
| `scan` | 0.37 |
| `track` | 0.58 |
| `acq_date` | 2026-10-11 |
| `acq_time` | 0026 |
| `satellite` | N20 |
| `confidence` | nominal |
| `version` | 2.0NRT |
| `bright_ti5` | 292.43 |
| `frp` | 2.78 |
| `daynight` | D |

</details>


<a id="k-entsoe"></a>
#### K8. ENTSO-E Transparency Platform — European electricity load, generation, prices

- **Get the key:** https://transparency.entsoe.eu/ (HTTP 200) — Account + e-mail to transparency@entsoe.eu; granted “within 3 working days”
- **Delivery:** REST XML (IEC 62325), polled
- **Endpoint:** `https://web-api.tp.entsoe.eu/api?securityToken=<TOKEN>&documentType=…`
- **Documented limit:** 400 requests/min per token
- **Paid plan:** None found
- **Probe without key:** HTTP 401 — `<?xml version="1.0" encoding="UTF-8"?> <Acknowledgement_MarketDocument 	xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0"> 	<mRID>afb3c20c-d54e-4</mRID> 	<createdDateTime>2026-10-13…`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “You will be granted within 3 working days” — https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token (HTTP 200)
  - ✅ “400 requests per minute” — https://transparencyplatform.zendesk.com/hc/en-us/articles/12783148966036-API-Rate-Limit-Part-1 (HTTP 200)

<a id="k-lasair"></a>
#### K9. Lasair — Rubin Observatory LSST alert broker (Kafka per filter)

- **Get the key:** https://lasair.lsst.ac.uk/ (HTTP 200) — Lasair account; create a filter, then consume its Kafka topic
- **Delivery:** Kafka (kafka.lsst.ac.uk:9092, topic per saved filter) + REST API
- **Endpoint:** `kafka.lsst.ac.uk:9092 (TCP reachable from this host)`
- **Documented limit:** REST: 100 calls/h (account), 10,000 calls/h for power users on request; no Kafka limit stated
- **Paid plan:** None found
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “users with an account get up to 100 calls per hour, but “power” users get up to 10,000 calls per hour” — https://lasair.readthedocs.io/en/main/core_functions/rest-api.html (HTTP 200)
  - ✅ “the process is very similar for Kafka alerts, except that you will fetch the results by machine instead of by email” — https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html (HTTP 200)

<a id="k-fink"></a>
#### K10. Fink — Rubin LSST / ZTF alert broker livestream

- **Get the key:** https://forms.gle/2td4jysT4e9pkf889 (HTTP 200) — Web form; credentials sent by the Fink team
- **Delivery:** Kafka via fink-client (finkctl)
- **Endpoint:** `finkctl topic subscribe -survey lsst -name <topic>`
- **Documented limit:** No limit stated on the pages checked
- **Paid plan:** None found
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “Subscribe to one or more Fink streams by filling this [form](https://forms.gle/2td4jysT4e9pkf889)” — https://raw.githubusercontent.com/astrolabsoftware/fink-client/master/README.md (HTTP 200)
  - ✅ “After filling the form, we will send your credentials” — https://raw.githubusercontent.com/astrolabsoftware/fink-client/master/README.md (HTTP 200)

<a id="k-mastodon"></a>
#### K11. Mastodon streaming API — federated public timeline (e.g. mastodon.social)

- **Get the key:** https://mastodon.social/auth/sign_up (HTTP 200) — Free user account on an instance; create an application token in settings
- **Delivery:** Server-Sent Events or WebSocket
- **Endpoint:** `https://mastodon.social/api/v1/streaming/public (Authorization: Bearer <token>)`
- **Documented limit:** REST: 300 calls per 5 min per account; streaming not listed
- **Paid plan:** None found
- **Probe without key:** HTTP 401 — `{"error":"Missing access token"}`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “All endpoints and methods can be called 300 times within 5 minutes” — https://docs.joinmastodon.org/api/rate-limits/ (HTTP 200)
  - ✅ “an access token must be provided in order to receive events” — https://docs.joinmastodon.org/methods/streaming/ (HTTP 200)

<a id="k-gfw"></a>
#### K12. Global Fishing Watch APIs — vessel events and fishing effort (AIS + VMS)

- **Get the key:** https://globalfishingwatch.org/our-apis/ (HTTP 200) — Global Fishing Watch account; request an API token
- **Delivery:** REST JSON queries (not a push stream)
- **Endpoint:** `https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest`
- **Documented limit:** Non-commercial use only; numeric limits are on a documentation page that did not render
- **Paid plan:** None (commercial use: contact them)
- **Probe without key:** HTTP 401 — `{"error":"invalid token"}`
- **Measured:** not measured — needs the key.
- **Evidence (verbatim, re-verified at generation):**
  - ✅ “Get your free API key” — https://globalfishingwatch.org/our-apis/ (HTTP 200)
  - ✅ “Global Fishing Watch APIs are only available for non-commercial purposes” — https://globalfishingwatch.org/our-apis/documentation/ (HTTP 200)

## 8. Limitations

- Rates come from 3 one-minute windows; event rates of transport, chat and market streams follow local time of day, which is why the spread is reported.
- Polled sources count changed records between polls; a faster poll interval can raise the observed rate up to each provider's limit (adsb.lol answered HTTP 429 at a 5 s interval and is therefore polled every 15 s).
- Attribute counts are on the raw event as delivered; several sources reach ≥10 attributes only after decoding (Certificate Transparency X.509, OpenStreetMap tags) or a join with static metadata (Digitraffic road sensors, GBFS station information) — this is stated per source.
- Licence excerpts are only what the linked page states; a source without an excerpt still needs a manual terms review before students rely on it.
- Access was tested from one host in Mexico City; some providers restrict by region or by client.
- Rounds follow wall-clock hourly targets; when the sampling host was suspended (2026-10-13 02:13–03:08 UTC) the missed hour is absent, never interpolated. The table header lists exactly which rounds exist.
- Bytewax overlap is a domain match; a related service can still appear in that list under another domain (for example Certstream, which redistributes the same Certificate Transparency logs read directly here).
- The sampler (`sampler.py`, `meta.py`, `report.py`) is a throw-away research tool kept outside the repository at `/tmp/opencode/streams/`; raw per-round results are the `rounds/*.jsonl` files there.
