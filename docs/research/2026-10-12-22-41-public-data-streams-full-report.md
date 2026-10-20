# Public real-time data streams for the COM-22102 final project — full detailed report

This is the complete record of the public-data-stream research for the final project: every source probed, how it was measured, what it delivers, how to connect, what it costs, what licence evidence exists, how sources that fall short can be enriched or combined, and the full source code of the measuring tools. It supersedes nothing: the earlier record `docs/research/2026-10-12-21-37-public-data-streams-survey.md` stays as it was; this one is generated from more sampling rounds and adds the sections listed in the contents.

- **Generated:** 2026-10-13 04:43 UTC
- **Sampling rounds:** 4 (first 2026-10-13T02:10Z, last 2026-10-13T04:23Z); one round samples every source concurrently.
- **Sources probed:** 61 across 6 categories.
- **Rounds (UTC start):** 20261013T0210, 20261013T0211, 20261013T0323, 20261013T0423
- **Result:** 33 meet both project requirements on the measured average; 12 meet the rate only; 5 meet the attributes only; 4 meet neither; 7 were not usable as tested.
- **Key-based sources:** see the section *Sources that need a free API key* (free key with no paid plan, excluded paid/limited plans, and free keys below 1 event/s).

- **Host:** Linux-7.1.5+kali-amd64-x86_64-with-glibc2.43 · Python 3.14.8 · measuring packages listed in *Reproduction*.
- **Contents:** Executive summary · Requirements and scope · Definitions · Method · Master table · Endpoints and APIs · Access, cost and licence evidence · Enrichment joins verified · Combining streams · Per-source detail · Sources that need a free API key · Sources excluded because the project document already lists them · Limitations · Reproduction · Appendices A–H (tool source code).

## 0. Executive summary

- **33 of 61** keyless sources meet both requirements (≥1 event/s on average and a median of ≥10 attributes per event) over the rounds listed above.
- **12** reach the rate but not the attributes; the *Enrichment joins verified* section shows 9 of them reaching ≥10 attributes after one documented join, each join fetched live.
- **5** have enough attributes but fewer than 1 event/s; the *Combining streams* section lists measured combinations that reach ≥1 event/s, which the project document allows.
- **5** qualifying sources carry Mexican data or come from a Mexican provider: adsb.fi open data aircraft — 250 NM around Mexico City airport, EcoBici CDMX bike-share station status (GBFS), adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport, NOAA aviationweather.gov METAR observations (global airports), Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN).
- Highest measured average rate per category among the sources that meet both requirements:

| Category | Source | Avg ev/s | Median attrs | Delivery |
|---|---|---:|---:|---|
| Transport | [HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)](#s-hsl) | 816.10 | 22.0 | live · MQTT over WSS |
| Transport | [Entur Norway real-time vehicle positions](#s-entur) | 36.16 | 19.0 | poll · GraphQL over HTTPS (POST), polled every 15 s |
| Transport | [Digitraffic Finland marine AIS vessel locations](#s-dt_marine) | 32.70 | 10.0 | live · MQTT over WSS |
| Weather & environment | [NOAA aviationweather.gov METAR observations (global airports)](#s-metar) | 1.35 | 38.0 | batch · gzip CSV cache file, refreshed every minute |
| Internet & software | [RIPE NCC RIS Live — global BGP routing updates](#s-ris) | 1,709.28 | 11.0 | live · WebSocket (JSON) |
| Internet & software | [RIPE Atlas measurement results stream (ping)](#s-atlas) | 585.29 | 25.0 | live · WebSocket (JSON) |
| Internet & software | [Certificate Transparency logs (RFC 6962), read directly](#s-ct) | 132.76 | 17.0 | counter · REST JSON (get-sth / get-entries) |
| Science & sensors | [PSK Reporter amateur-radio reception reports](#s-pskreporter) | 256.46 | 13.0 | live · MQTT (TCP 1883) |
| Science & sensors | [Sensor.Community citizen air-quality sensors](#s-sensorcomm) | 58.79 | 17.0 | batch · JSON file over HTTPS (last 5 minutes) |
| Science & sensors | [Crossref scholarly metadata (works indexed per day)](#s-crossref) | 6.47 | 42.2 | batch · REST JSON (cursor paging by index date) |
| Finance & blockchain | [Polymarket CLOB market channel (prediction-market prices)](#s-polymarket) | 589.34 | 10.0 | live · WebSocket (JSON) |
| Finance & blockchain | [Base (L2) contract event logs (PublicNode RPC)](#s-base_logs) | 336.87 | 10.0 | live · JSON-RPC over WebSocket (eth_subscribe) |
| Finance & blockchain | [Polygon PoS contract event logs (PublicNode RPC)](#s-polygon_logs) | 333.30 | 10.0 | live · JSON-RPC over WebSocket (eth_subscribe) |
| Games, media & social | [Albion Online Data Project market orders](#s-albion) | 19.89 | 10.0 | live · NATS (TCP 4222) |
| Games, media & social | [Twitch chat (anonymous read-only IRC)](#s-twitch) | 19.35 | 19.0 | live · IRC over WebSocket |

## 1. Requirements and scope

The requirements are quoted from `course-setup/course-documents/03-proyecto-final/proyecto-final-com-22102-otono-2026.pdf` (text extracted with `pdftotext`):

> Los datos del stream deben ser reales. … Cada evento del stream debe contar con al menos 10 atributos distintos. El stream debe producir al menos 1 evento por segundo en promedio. Esta permitido utilizar más de un stream a la vez para conseguir el número de eventos mínimo en promedio.

Excluded because the same document already suggests them: Bluesky Jetstream; Wikimedia EventStreams (recentchange); GDELT; Binance; mempool.space (Bitcoin); aisstream.io; OpenSky Network; Bytewax awesome-public-real-time-datasets list (linked). Overlap with the Bytewax list (linked from the same document) was checked automatically: a source is flagged “yes” when the registered domain of its endpoint, documentation or terms URL appears among the links of the list's README (HTTP 200, 80 distinct domains). Flagged sources are reported, not excluded, because the document links the list without naming them.

## 2. Definitions

Every protocol, format and licence named in this report, with its canonical specification (HTTP status fetched when this report was generated).

| Term | Meaning | Reference (HTTP) |
|---|---|---|
| Event | One record delivered by a stream (one message, one changed record of a polled snapshot, or one row of a batch file). The project counts events per second. | this report, Method (the project document uses the term without defining it) |
| Attribute | One distinct field of an event after flattening nested objects with dotted names (`a.b.c`); a list counts as one attribute. | this report, Method |
| WebSocket | Full-duplex message protocol over one TCP connection, opened with an HTTP upgrade (`ws://`, `wss://` with TLS). | [https://www.rfc-editor.org/rfc/rfc6455](https://www.rfc-editor.org/rfc/rfc6455) (200) |
| MQTT | Publish/subscribe messaging protocol; clients subscribe to topic filters (`+` one level, `#` all remaining levels). | [https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html) (200) |
| Server-Sent Events (SSE) | One-way stream of text events over a long-lived HTTP response with `Content-Type: text/event-stream`. | [https://html.spec.whatwg.org/multipage/server-sent-events.html](https://html.spec.whatwg.org/multipage/server-sent-events.html) (200) |
| NATS | Publish/subscribe messaging system with subject-based addressing. | [https://docs.nats.io/](https://docs.nats.io/) (200) |
| ZeroMQ | Messaging library; the PUB/SUB pattern delivers every published message to all subscribers whose prefix matches. | [https://zeromq.org/](https://zeromq.org/) (200) |
| Apache Kafka | Distributed, partitioned commit log; consumers read topics at their own offset. | [https://kafka.apache.org/documentation/](https://kafka.apache.org/documentation/) (200) |
| REST polling | Repeated HTTP GET of a snapshot; events are the records that are new or changed between two consecutive snapshots. | this report, Method |
| GraphQL | Query language over HTTP in which the client names the fields it wants. | [https://spec.graphql.org/](https://spec.graphql.org/) (200) |
| JSON-RPC 2.0 | Remote procedure call encoded as JSON; used by blockchain nodes, here over WebSocket subscriptions. | [https://www.jsonrpc.org/specification](https://www.jsonrpc.org/specification) (200) |
| Protocol Buffers | Binary serialisation format with a schema; GTFS-Realtime feeds use it. | [https://protobuf.dev/](https://protobuf.dev/) (200) |
| GTFS-Realtime | Standard real-time public-transport feed: vehicle positions, trip updates and alerts. | [https://gtfs.org/documentation/realtime/reference/](https://gtfs.org/documentation/realtime/reference/) (200) |
| GTFS (static) | Standard public-transport schedule as CSV files (stops.txt, routes.txt, trips.txt…); the join target for GTFS-Realtime ids. | [https://gtfs.org/documentation/schedule/reference/](https://gtfs.org/documentation/schedule/reference/) (200) |
| GBFS | General Bikeshare Feed Specification: JSON files such as station_information and station_status. | [https://github.com/MobilityData/gbfs](https://github.com/MobilityData/gbfs) (200) |
| AIS / AIVDM | Automatic Identification System for ships; AIVDM is its NMEA 0183 sentence encoding. | [https://gpsd.gitlab.io/gpsd/AIVDM.html](https://gpsd.gitlab.io/gpsd/AIVDM.html) (200) |
| ADS-B | Automatic Dependent Surveillance–Broadcast: aircraft broadcast position, altitude and speed. | [https://www.faa.gov/air_traffic/technology/adsb](https://www.faa.gov/air_traffic/technology/adsb) (200) |
| METAR | Routine aviation weather observation report issued by airports. | [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/) (200) |
| BGP | Border Gateway Protocol, the routing protocol between Internet networks (autonomous systems). | [https://www.rfc-editor.org/rfc/rfc4271](https://www.rfc-editor.org/rfc/rfc4271) (200) |
| Certificate Transparency | Public append-only logs of issued TLS certificates, read with `get-sth` / `get-entries`. | [https://www.rfc-editor.org/rfc/rfc6962](https://www.rfc-editor.org/rfc/rfc6962) (200) |
| osmChange | OpenStreetMap XML format that lists created, modified and deleted elements. | [https://wiki.openstreetmap.org/wiki/OsmChange](https://wiki.openstreetmap.org/wiki/OsmChange) (200) |
| SeedLink | Real-time seismic data protocol that delivers miniSEED records. | [https://www.seiscomp.de/doc/apps/seedlink.html](https://www.seiscomp.de/doc/apps/seedlink.html) (200) |
| IRC | Internet Relay Chat text protocol; Twitch chat speaks it over WebSocket. | [https://www.rfc-editor.org/rfc/rfc1459](https://www.rfc-editor.org/rfc/rfc1459) (200) |
| CouchDB _changes | Feed of document changes in sequence order; the npm registry replica exposes it. | [https://docs.couchdb.org/en/stable/api/database/changes.html](https://docs.couchdb.org/en/stable/api/database/changes.html) (200) |
| RSS 2.0 | XML feed format listing recent items. | [https://www.rssboard.org/rss-specification](https://www.rssboard.org/rss-specification) (200) |
| CC BY 4.0 | Creative Commons Attribution licence: reuse allowed with attribution. | [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/) (200) |
| ODbL 1.0 | Open Database License: reuse with attribution and share-alike of derived databases. | [https://opendatacommons.org/licenses/odbl/1-0/](https://opendatacommons.org/licenses/odbl/1-0/) (200) |
| NLOD 2.0 | Norwegian Licence for Open Government Data. | [https://data.norge.no/nlod/en/2.0](https://data.norge.no/nlod/en/2.0) (200) |
| CC0 1.0 | Creative Commons public-domain dedication. | [https://creativecommons.org/publicdomain/zero/1.0/](https://creativecommons.org/publicdomain/zero/1.0/) (200) |

## 3. Method

- **Live streams** (WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP, SeedLink): connect, subscribe, count every event for a 60 s window.
- **Polled snapshots** (aircraft, GBFS bike stations, GTFS-Realtime, Entur): poll at the stated interval for 60 s and count records that are new or changed between successive polls — the events a consumer would actually receive.
- **Batch files** (METAR, OSM minutely, GH Archive hourly, Sensor.Community 5-min, Crossref daily, ENA weekly, USGS hourly): events in the file ÷ the period the file covers.
- **Counters** (Certificate Transparency tree size over all 9 usable RFC 6962 logs, npm update sequence, Hacker News max item): growth over a 60 s window.
- **Attributes per event** = number of distinct fields after flattening nested objects (lists count as one field); the table reports the **median per event** over up to 1,000 events per round, plus the maximum and the union across events.
- **Average rate** = mean of the per-round rates; min/median/max show the spread across the day.
- **Links**: every docs and terms URL was fetched live with a browser User-Agent at report time; the HTTP status is shown. Licence/terms evidence is a verbatim excerpt found in that page; “not found” means no matching text was found, not that the data is unlicensed.
- **Personal data**: sample values that identify people (chat users, callsigns, GitHub actors, OSM editors, Nostr keys) are masked as ‹redacted›.

## 4. Master table

| # | Source | Category | Delivery | Access | Avg ev/s | Min – Max ev/s | Attrs/event (median) | Max attrs | Rounds OK | ≥1 ev/s | ≥10 attrs | Verdict | Mexico | In Bytewax list |
|---|---|---|---|---|---:|---|---:|---:|---|:-:|:-:|---|:-:|---|
| 1 | [HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)](#s-hsl) | Transport | live · MQTT over WSS | None | 816.10 | 389.87 – 1,371.53 | 22.0 | 22 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 2 | [Entur Norway real-time vehicle positions](#s-entur) | Transport | poll · GraphQL over HTTPS (POST), polled every 15 s | None (identifying ET-Client-Name header required) | 36.16 | 3.76 – 96.08 | 19.0 | 19 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 3 | [Digitraffic Finland marine AIS vessel locations](#s-dt_marine) | Transport | live · MQTT over WSS | None | 32.70 | 31.50 – 35.20 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 4 | [NDOV Loket Netherlands public transport KV6 (all operators)](#s-ndov) | Transport | live · ZeroMQ PUB/SUB (gzip XML) | None (best-effort relay) | 25.60 | 1.27 – 87.70 | 15.0 | 16 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 5 | [MBTA Boston GTFS-Realtime VehiclePositions](#s-mbta_gtfsrt) | Transport | poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s | None | 13.87 | 13.08 – 14.88 | 18.0 | 18 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 6 | [adsb.fi open data aircraft — 250 NM around Mexico City airport](#s-adsb_fi) | Transport | poll · REST JSON, polled every 5 s | None | 4.22 | 3.04 – 5.24 | 39.0 | 54 | 4/4 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 7 | [Bicing Barcelona bike-share station status (GBFS)](#s-bicing) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 3.37 | 3.02 – 3.73 | 14.0 | 14 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 8 | [EcoBici CDMX bike-share station status (GBFS)](#s-ecobici) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 2.96 | 1.39 – 5.78 | 11.0 | 11 | 4/4 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 9 | [adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport](#s-adsb_lol) | Transport | poll · REST JSON, polled every 15 s | None | 1.76 | 1.48 – 2.12 | 37.8 | 51 | 4/4 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 10 | [Digitraffic Finland train timetables/actuals](#s-dt_rail_trains) | Transport | live · MQTT over WSS | None | 1.08 | 0.82 – 1.38 | 13.0 | 13 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 11 | [NOAA aviationweather.gov METAR observations (global airports)](#s-metar) | Weather & environment | batch · gzip CSV cache file, refreshed every minute | None | 1.35 | 1.33 – 1.37 | 38.0 | 38 | 4/4 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 12 | [RIPE NCC RIS Live — global BGP routing updates](#s-ris) | Internet & software | live · WebSocket (JSON) | None | 1,709.28 | 98.62 – 4,253.95 | 11.0 | 13 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 13 | [RIPE Atlas measurement results stream (ping)](#s-atlas) | Internet & software | live · WebSocket (JSON) | None | 585.29 | 56.65 – 1,291.02 | 25.0 | 26 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 14 | [Certificate Transparency logs (RFC 6962), read directly](#s-ct) | Internet & software | counter · REST JSON (get-sth / get-entries) | None | 132.76 | 103.24 – 161.96 | 17.0 | 17 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 15 | [GH Archive — all public GitHub events (hourly files)](#s-gharchive) | Internet & software | batch · Hourly gzip NDJSON over HTTPS | None | 22.54 | 22.07 – 23.13 | 18.0 | 203 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 16 | [PSK Reporter amateur-radio reception reports](#s-pskreporter) | Science & sensors | live · MQTT (TCP 1883) | None | 256.46 | 211.97 – 299.52 | 13.0 | 13 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 17 | [Sensor.Community citizen air-quality sensors](#s-sensorcomm) | Science & sensors | batch · JSON file over HTTPS (last 5 minutes) | None | 58.79 | 58.66 – 58.94 | 17.0 | 25 | 4/4 | ✅ | ✅ | Meets both |  | yes (sensor.community) |
| 18 | [Crossref scholarly metadata (works indexed per day)](#s-crossref) | Science & sensors | batch · REST JSON (cursor paging by index date) | None | 6.47 | 6.44 – 6.50 | 42.2 | 48 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 19 | [EarthScope (IRIS) SeedLink real-time seismic waveforms](#s-seedlink) | Science & sensors | live · SeedLink 3/4 over TCP (miniSEED records) | None | 2.43 | 2.32 – 2.48 | 12.0 | 12 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 20 | [USGS Water Services instantaneous values (river gauges)](#s-usgs_water) | Science & sensors | batch · REST JSON (WaterML-JSON) | None | 1.83 | 1.79 – 1.87 | 26.0 | 26 | 4/4 | ✅ | ✅ | Meets both |  | yes (usgs.gov) |
| 21 | [Polymarket CLOB market channel (prediction-market prices)](#s-polymarket) | Finance & blockchain | live · WebSocket (JSON) | None | 589.34 | 293.63 – 1,343.25 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 22 | [Base (L2) contract event logs (PublicNode RPC)](#s-base_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 336.87 | 123.93 – 451.50 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 23 | [Polygon PoS contract event logs (PublicNode RPC)](#s-polygon_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 333.30 | 151.87 – 475.30 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 24 | [BNB Smart Chain contract event logs (PublicNode RPC)](#s-bsc_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 262.45 | 0.00 – 480.90 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 25 | [Ethereum mainnet contract event logs (PublicNode RPC)](#s-eth_logs) | Finance & blockchain | live · JSON-RPC over WebSocket (eth_subscribe) | None | 82.21 | 71.33 – 93.43 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 26 | [Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)](#s-bitso) | Finance & blockchain | live · WebSocket (JSON) | None | 35.04 | 17.93 – 47.38 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both | 🇲🇽 | no |
| 27 | [OKX public tickers](#s-okx) | Finance & blockchain | live · WebSocket (JSON) | None | 30.98 | 30.27 – 31.47 | 16.0 | 16 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 28 | [XRP Ledger transactions](#s-xrpl) | Finance & blockchain | live · WebSocket (JSON) | None | 21.92 | 17.68 – 26.58 | 20.0 | 27 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 29 | [Coinbase Exchange ticker](#s-coinbase) | Finance & blockchain | live · WebSocket (JSON) | None | 10.26 | 6.97 – 16.42 | 17.0 | 17 | 4/4 | ✅ | ✅ | Meets both |  | yes (coinbase.com) |
| 30 | [Deribit perpetual futures ticker](#s-deribit) | Finance & blockchain | live · JSON-RPC over WebSocket | None | 5.15 | 4.83 – 5.80 | 24.0 | 24 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 31 | [Bitstamp live trades](#s-bitstamp) | Finance & blockchain | live · WebSocket (JSON) | None | 1.41 | 0.68 – 2.05 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 32 | [Albion Online Data Project market orders](#s-albion) | Games, media & social | live · NATS (TCP 4222) | Published public credentials | 19.89 | 1.02 – 47.73 | 10.0 | 10 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 33 | [Twitch chat (anonymous read-only IRC)](#s-twitch) | Games, media & social | live · IRC over WebSocket | Anonymous (justinfan) read-only login | 19.35 | 13.07 – 24.07 | 19.0 | 28 | 4/4 | ✅ | ✅ | Meets both |  | no |
| 34 | [Digitraffic Finland road traffic (TMS) and road-weather sensors](#s-dt_road) | Transport | live · MQTT over WSS | None | 341.60 | 327.33 – 356.93 | 2.0 | 4 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 35 | [Digitraffic Finland train GPS locations](#s-dt_rail) | Transport | live · MQTT over WSS | None | 47.40 | 30.50 – 77.90 | 8.0 | 8 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 36 | [MTA New York City Subway GTFS-Realtime (A/C/E feed)](#s-mta_gtfsrt) | Transport | poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s | None | 4.86 | 4.58 – 5.41 | 6.5 | 9 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | yes (mta.info) |
| 37 | [OpenStreetMap minutely replication diffs](#s-osm) | Internet & software | batch · gzip osmChange XML, one file per minute | None | 29.75 | 6.37 – 52.80 | 9.0 | 294 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 38 | [npm registry replication changes](#s-npm) | Internet & software | counter · CouchDB-style _changes over HTTPS | None | 2.26 | 1.89 – 3.08 | 3.0 | 3 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 39 | [Reverse Beacon Network (CW/RTTY skimmer spots)](#s-rbn) | Science & sensors | live · Telnet text lines | None | 1.33 | 1.07 – 1.65 | 9.0 | 9 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 40 | [Solana program logs (public mainnet RPC)](#s-solana) | Finance & blockchain | live · JSON-RPC over WebSocket (logsSubscribe) | None (public RPC is rate-limited) | 837.28 | 46.10 – 1,581.57 | 4.0 | 4 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 41 | [Gemini market data v1 (order-book changes + trades)](#s-gemini) | Finance & blockchain | live · WebSocket (JSON) | None | 637.07 | 422.62 – 832.17 | 9.0 | 9 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 42 | [Hyperliquid trades](#s-hyperliquid) | Finance & blockchain | live · WebSocket (JSON) | None | 8.31 | 4.87 – 12.12 | 8.0 | 8 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 43 | [Bybit spot tickers](#s-bybit) | Finance & blockchain | live · WebSocket (JSON) | None | 7.15 | 5.78 – 8.40 | 9.0 | 9 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 44 | [Kraken trades + ticker (v2)](#s-kraken) | Finance & blockchain | live · WebSocket (JSON) | None | 6.01 | 2.85 – 9.47 | 7.0 | 14 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 45 | [Bitfinex trades + ticker (public v2)](#s-bitfinex) | Finance & blockchain | live · WebSocket (JSON arrays) | None | 1.54 | 0.75 – 2.47 | 5.0 | 11 | 4/4 | ✅ | ❌ | Rate only (needs enrichment for ≥10 attributes) |  | no |
| 46 | [Vélib' Métropole Paris bike-share station status (GBFS)](#s-velib) | Transport | poll · GBFS JSON over HTTPS, polled every 10 s | None | 0.90 | 0.81 – 0.98 | 12.0 | 12 | 4/4 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 47 | [PyPI newest releases feed](#s-pypi) | Internet & software | batch · RSS over HTTPS (+ JSON API per release) | None | 0.10 | 0.09 – 0.10 | 33.5 | 34 | 4/4 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 48 | [ENA (EMBL-EBI) sequencing runs made public — DNA/genomics](#s-ena) | Science & sensors | batch · REST (ENA Portal API) | None | 0.15 | 0.15 – 0.15 | 196.0 | 196 | 4/4 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 49 | [Stellar Horizon operations stream](#s-stellar) | Finance & blockchain | live · Server-Sent Events | None | 0.17 | 0.17 – 0.17 | 22.0 | 24 | 4/4 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 50 | [MLB Stats API live game feed](#s-mlb) | Games, media & social | poll · REST JSON (GUMBO), polled every 10 s | None | 0.06 | 0.05 – 0.06 | 44.0 | 48 | 2/4 | ❌ | ✅ | Attributes only (combine to reach ≥1 event/s) |  | no |
| 51 | [Hacker News items (Firebase API)](#s-hn) | Internet & software | counter · REST JSON (also Firebase SSE) | None | 0.11 | 0.02 – 0.20 | 6.0 | 6 | 4/4 | ❌ | ❌ | Neither |  | no |
| 52 | [APRS-IS amateur-radio packet network (full feed)](#s-aprs) | Science & sensors | live · Raw TCP text lines | Read-only login with pass -1 | 0.00 | 0.00 – 0.00 | — | 0 | 4/4 | ❌ | ❌ | Neither |  | no |
| 53 | [BitMEX realtime trade/quote/instrument](#s-bitmex) | Finance & blockchain | live · WebSocket (JSON) | None | 0.00 | 0.00 – 0.00 | — | 0 | 4/4 | ❌ | ❌ | Neither |  | no |
| 54 | [Nostr public notes (kind 1) across 4 relays](#s-nostr) | Games, media & social | live · WebSocket (NIP-01) | None | 0.76 | 0.63 – 1.00 | 7.0 | 7 | 4/4 | ❌ | ❌ | Neither |  | no |
| 55 | [MBTA V3 API vehicle streaming (Server-Sent Events)](#s-mbta_sse) | Transport | live · Server-Sent Events | Returned 406 without a key | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | no |
| 56 | [Kystverket (Norwegian Coastal Administration) open AIS feed](#s-kystverket_ais) | Transport | live · Raw TCP NMEA 0183 (AIVDM) | None | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | yes (kystverket.no) |
| 57 | [airplanes.live aircraft API](#s-airplanes_live) | Transport | poll · REST JSON | Rejected (403): operator asks for an e-mail request | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested | 🇲🇽 | no |
| 58 | [GitHub REST public events (unauthenticated)](#s-github_api) | Internet & software | poll · REST JSON | None, but 60 requests/hour without a token | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | no |
| 59 | [Rubin Observatory LSST alerts via Lasair broker (Kafka)](#s-lasair) | Science & sensors | live · Kafka (kafka.lsst.ac.uk:9092) | Lasair account + saved filter required | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | no |
| 60 | [Mastodon public streaming (mastodon.social)](#s-mastodon) | Games, media & social | live · WebSocket / SSE | Access token required (401) | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | no |
| 61 | [zKillboard (EVE Online kills)](#s-zkillboard) | Games, media & social | live · WebSocket / RedisQ | WebSocket returned 403 to this client | — | — – — | — | — | 0/4 | ❌ | ❌ | Not usable as tested |  | no |

## 5. Endpoints and APIs

| # | Source | Endpoint | Request / subscription | Documentation (HTTP) |
|---|---|---|---|---|
| 1 | HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains) | `wss://mqtt.hsl.fi:443/` | `SUBSCRIBE /hfp/v2/journey/ongoing/vp/#` | [https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/s…](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md) (200) |
| 2 | Entur Norway real-time vehicle positions | `https://api.entur.io/realtime/v2/vehicles/graphql` | `POST {query: vehicles{vehicleId lastUpdated line location speed delay ...}} with header ET-Client-Name` | [https://developer.entur.org/pages-real-time-intro](https://developer.entur.org/pages-real-time-intro) (200) |
| 3 | Digitraffic Finland marine AIS vessel locations | `wss://meri.digitraffic.fi:443/mqtt` | `SUBSCRIBE vessels-v2/+/location (also vessels-v2/+/metadata)` | [https://www.digitraffic.fi/en/marine-traffic/](https://www.digitraffic.fi/en/marine-traffic/) (200) |
| 4 | NDOV Loket Netherlands public transport KV6 (all operators) | `tcp://pubsub.besteffort.ndovloket.nl:7658` | `SUB '' (all envelopes)` | [https://ndovloket.nl/](https://ndovloket.nl/) (200) |
| 5 | MBTA Boston GTFS-Realtime VehiclePositions | `https://cdn.mbta.com/realtime/VehiclePositions.pb` | `GET (also TripUpdates.pb, Alerts.pb)` | [https://www.mbta.com/developers/gtfs-realtime](https://www.mbta.com/developers/gtfs-realtime) (200) |
| 6 | adsb.fi open data aircraft — 250 NM around Mexico City airport | `https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250` | `GET` | [https://github.com/adsbfi/opendata](https://github.com/adsbfi/opendata) (200) |
| 7 | Bicing Barcelona bike-share station status (GBFS) | `https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status` | `GET` | [https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estac…](https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing) (200) |
| 8 | EcoBici CDMX bike-share station status (GBFS) | `https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json` | `GET (station_information.json for names/coordinates)` | [https://ecobici.cdmx.gob.mx/datos-abiertos/](https://ecobici.cdmx.gob.mx/datos-abiertos/) (200) |
| 9 | adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport | `https://api.adsb.lol/v2/point/19.436/-99.072/250` | `GET` | [https://www.adsb.lol/docs/open-data/api/](https://www.adsb.lol/docs/open-data/api/) (200) |
| 10 | Digitraffic Finland train timetables/actuals | `wss://rata.digitraffic.fi:443/mqtt` | `SUBSCRIBE trains/#` | [https://www.digitraffic.fi/en/railway-traffic/](https://www.digitraffic.fi/en/railway-traffic/) (200) |
| 11 | NOAA aviationweather.gov METAR observations (global airports) | `https://aviationweather.gov/data/cache/metars.cache.csv.gz` | `GET` | [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/) (200) |
| 12 | RIPE NCC RIS Live — global BGP routing updates | `wss://ris-live.ripe.net/v1/ws/?client=<identifier>` | `{"type":"ris_subscribe","data":{"type":"UPDATE"}}` | [https://ris-live.ripe.net/manual/](https://ris-live.ripe.net/manual/) (200) |
| 13 | RIPE Atlas measurement results stream (ping) | `wss://atlas-stream.ripe.net/stream/?client=<identifier>` | `["atlas_subscribe",{"streamType":"result","type":"ping"}]` | [https://atlas.ripe.net/docs/apis/streaming-api](https://atlas.ripe.net/docs/apis/streaming-api) (200) |
| 14 | Certificate Transparency logs (RFC 6962), read directly | `<log url>/ct/v1/get-sth and /ct/v1/get-entries; log list https://www.gstatic.com/ct/log_list/v3/log_list.json` | `GET` | [https://www.rfc-editor.org/rfc/rfc6962](https://www.rfc-editor.org/rfc/rfc6962) (200) |
| 15 | GH Archive — all public GitHub events (hourly files) | `https://data.gharchive.org/YYYY-MM-DD-H.json.gz` | `GET` | [https://www.gharchive.org/](https://www.gharchive.org/) (200) |
| 16 | PSK Reporter amateur-radio reception reports | `mqtt://mqtt.pskreporter.info:1883` | `SUBSCRIBE pskr/filter/v2/#` | [https://www.mqtt.pskreporter.info/](https://www.mqtt.pskreporter.info/) (200) |
| 17 | Sensor.Community citizen air-quality sensors | `https://data.sensor.community/static/v2/data.json` | `GET` | [https://github.com/opendata-stuttgart/meta/wiki/EN-APIs](https://github.com/opendata-stuttgart/meta/wiki/EN-APIs) (200) |
| 18 | Crossref scholarly metadata (works indexed per day) | `https://api.crossref.org/works?filter=from-index-date:<d>,until-index-date:<d>` | `GET with mailto=` | [https://www.crossref.org/documentation/retrieve-metadata/rest-api/](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) (200) |
| 19 | EarthScope (IRIS) SeedLink real-time seismic waveforms | `tcp://rtserve.iris.washington.edu:18000` | `STATION <sta> <net> / SELECT BHZ / DATA ... END` | [https://ds.iris.edu/ds/nodes/dmc/services/seedlink/](https://ds.iris.edu/ds/nodes/dmc/services/seedlink/) (200) |
| 20 | USGS Water Services instantaneous values (river gauges) | `https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H` | `GET per state` | [https://waterservices.usgs.gov/](https://waterservices.usgs.gov/) (200) |
| 21 | Polymarket CLOB market channel (prediction-market prices) | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | `{"assets_ids":[...],"type":"market"} (ids from https://gamma-api.polymarket.com/markets)` | [https://docs.polymarket.com/developers/CLOB/websocket/market-channel](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) (200) |
| 22 | Base (L2) contract event logs (PublicNode RPC) | `wss://base-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 23 | Polygon PoS contract event logs (PublicNode RPC) | `wss://polygon-bor-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 24 | BNB Smart Chain contract event logs (PublicNode RPC) | `wss://bsc-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 25 | Ethereum mainnet contract event logs (PublicNode RPC) | `wss://ethereum-rpc.publicnode.com` | `{"method":"eth_subscribe","params":["logs",{}]}` | [https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub](https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub) (200) |
| 26 | Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN) | `wss://ws.bitso.com` | `{"action":"subscribe","book":"btc_mxn","type":"trades"\|"diff-orders"}` | [https://docs.bitso.com/bitso-api/docs](https://docs.bitso.com/bitso-api/docs) (200) |
| 27 | OKX public tickers | `wss://ws.okx.com:8443/ws/v5/public` | `{"op":"subscribe","args":[{"channel":"tickers","instId":"BTC-USDT"},...]}` | [https://www.okx.com/docs-v5/en/](https://www.okx.com/docs-v5/en/) (200) |
| 28 | XRP Ledger transactions | `wss://xrplcluster.com/` | `{"command":"subscribe","streams":["transactions"]}` | [https://xrpl.org/docs/references/http-websocket-apis/public-api-metho…](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe) (200) |
| 29 | Coinbase Exchange ticker | `wss://ws-feed.exchange.coinbase.com` | `{"type":"subscribe","product_ids":[...],"channels":["ticker"]}` | [https://docs.cdp.coinbase.com/exchange/websocket-feed/overview](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) (200) |
| 30 | Deribit perpetual futures ticker | `wss://www.deribit.com/ws/api/v2` | `public/subscribe ["ticker.BTC-PERPETUAL.100ms", ...]` | [https://docs.deribit.com/](https://docs.deribit.com/) (200) |
| 31 | Bitstamp live trades | `wss://ws.bitstamp.net` | `{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}` | [https://www.bitstamp.net/websocket/v2/](https://www.bitstamp.net/websocket/v2/) (200) |
| 32 | Albion Online Data Project market orders | `nats://nats.albion-online-data.com:4222` | `CONNECT user=public pass=thenewalbiondata; SUB marketorders.deduped` | [https://www.albion-online-data.com/](https://www.albion-online-data.com/) (200) |
| 33 | Twitch chat (anonymous read-only IRC) | `wss://irc-ws.chat.twitch.tv:443` | `CAP REQ :twitch.tv/tags; PASS SCHMOOPIIE; NICK justinfanNNNN; JOIN #<channels>` | [https://dev.twitch.tv/docs/chat/irc/](https://dev.twitch.tv/docs/chat/irc/) (200) |
| 34 | Digitraffic Finland road traffic (TMS) and road-weather sensors | `wss://tie.digitraffic.fi:443/mqtt` | `SUBSCRIBE tms-v2/# and weather-v2/#` | [https://www.digitraffic.fi/en/road-traffic/](https://www.digitraffic.fi/en/road-traffic/) (200) |
| 35 | Digitraffic Finland train GPS locations | `wss://rata.digitraffic.fi:443/mqtt` | `SUBSCRIBE train-locations/#` | [https://www.digitraffic.fi/en/railway-traffic/](https://www.digitraffic.fi/en/railway-traffic/) (200) |
| 36 | MTA New York City Subway GTFS-Realtime (A/C/E feed) | `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace` | `GET (7 more subway feeds: gtfs, -bdfm, -g, -jz, -nqrw, -l, -si)` | [https://api.mta.info/](https://api.mta.info/) (200) |
| 37 | OpenStreetMap minutely replication diffs | `https://planet.openstreetmap.org/replication/minute/NNN/NNN/NNN.osc.gz (state.txt gives the sequence)` | `GET` | [https://wiki.openstreetmap.org/wiki/Planet.osm/diffs](https://wiki.openstreetmap.org/wiki/Planet.osm/diffs) (200) |
| 38 | npm registry replication changes | `https://replicate.npmjs.com/registry/_changes` | `GET ?since=<seq>` | [https://github.com/npm/registry-follower-tutorial](https://github.com/npm/registry-follower-tutorial) (200) |
| 39 | Reverse Beacon Network (CW/RTTY skimmer spots) | `telnet://telnet.reversebeacon.net:7000` | `send any callsign at login` | [https://www.reversebeacon.net/](https://www.reversebeacon.net/) (200) |
| 40 | Solana program logs (public mainnet RPC) | `wss://api.mainnet-beta.solana.com` | `{"method":"logsSubscribe","params":["all",{"commitment":"confirmed"}]}` | [https://solana.com/docs/rpc/websocket/logssubscribe](https://solana.com/docs/rpc/websocket/logssubscribe) (200) |
| 41 | Gemini market data v1 (order-book changes + trades) | `wss://api.gemini.com/v1/marketdata/<SYMBOL>` | `connect per symbol (no message)` | [https://developer.gemini.com/websocket/streams.md](https://developer.gemini.com/websocket/streams.md) (200) |
| 42 | Hyperliquid trades | `wss://api.hyperliquid.xyz/ws` | `{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}}` | [https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/we…](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) (200) |
| 43 | Bybit spot tickers | `wss://stream.bybit.com/v5/public/spot` | `{"op":"subscribe","args":["tickers.BTCUSDT",...]}` | [https://bybit-exchange.github.io/docs/v5/websocket/public/ticker](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) (200) |
| 44 | Kraken trades + ticker (v2) | `wss://ws.kraken.com/v2` | `{"method":"subscribe","params":{"channel":"trade"\|"ticker","symbol":[...]}}` | [https://docs.kraken.com/api/docs/websocket-v2/trade](https://docs.kraken.com/api/docs/websocket-v2/trade) (200) |
| 45 | Bitfinex trades + ticker (public v2) | `wss://api-pub.bitfinex.com/ws/2` | `{"event":"subscribe","channel":"trades"\|"ticker","symbol":"tBTCUSD"}` | [https://docs.bitfinex.com/docs/ws-public](https://docs.bitfinex.com/docs/ws-public) (200) |
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

## 6. Access, cost and licence evidence

| # | Source | Access | Terms / licence page (HTTP) | Verbatim excerpt |
|---|---|---|---|---|
| 1 | HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains) | None | [https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/s…](https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md) (200) | “Digitransit makes the data available based on JHS-189 [permission to use the open data] and [Creative Commons name 4.0 (CC BY)](https://creativecommons.org/licenses/by/4.0/) licensing. CC BY is global, gratuitous, non-exclusive, and non” |
| 2 | Entur Norway real-time vehicle positions | None (identifying ET-Client-Name header required) | [https://developer.entur.org/pages-intro-setup-and-access/](https://developer.entur.org/pages-intro-setup-and-access/) (200) | “Norwegian Licence for Open Government Data (NLOD)” |
| 3 | Digitraffic Finland marine AIS vessel locations | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 4 | NDOV Loket Netherlands public transport KV6 (all operators) | None (best-effort relay) | [https://ndovloket.nl/](https://ndovloket.nl/) (200) | “Open Data Bestanden Datasets Realtime Home Projecten FAQ Documentatie Data Incidenten Aanmelden Grenzeloze Openbaar Vervoer Informatie voor Nederland en daar net buiten” |
| 5 | MBTA Boston GTFS-Realtime VehiclePositions | None | [https://www.mbta.com/developers/gtfs-realtime](https://www.mbta.com/developers/gtfs-realtime) (200) | “Use of MBTA data is governed by the MassDOT Developers License Agreement” |
| 6 | adsb.fi open data aircraft — 250 NM around Mexico City airport | None | [https://raw.githubusercontent.com/adsbfi/opendata/main/README.md](https://raw.githubusercontent.com/adsbfi/opendata/main/README.md) (200) | “Please contact us if you have commercial or higher request rate requirements” |
| 7 | Bicing Barcelona bike-share station status (GBFS) | None | [https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estac…](https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing) (200) | “token")” |
| 8 | EcoBici CDMX bike-share station status (GBFS) | None | [https://ecobici.cdmx.gob.mx/datos-abiertos/](https://ecobici.cdmx.gob.mx/datos-abiertos/) (200) | “GBFS (General Bikeshare Feed Specification)” |
| 9 | adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport | None | [https://www.adsb.lol/docs/open-data/api/](https://www.adsb.lol/docs/open-data/api/) (200) | “ODbL 1” |
| 10 | Digitraffic Finland train timetables/actuals | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 11 | NOAA aviationweather.gov METAR observations (global airports) | None | [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/) (200) | “Cache This service facilitates machine-to-machine access to aviation weather information” |
| 12 | RIPE NCC RIS Live — global BGP routing updates | None | [https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-co…](https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions) (200) | “Access to and use of the RIPE Data Repository and the Data for any commercial purposes, for example selling the Data or services based on the Data, is not allowed. [these are the RIPE Data Repository terms; the RIS Live manual itself was not found to state separate terms]” |
| 13 | RIPE Atlas measurement results stream (ping) | None | [https://atlas.ripe.net/legal/terms-conditions/](https://atlas.ripe.net/legal/terms-conditions/) (200) | not found |
| 14 | Certificate Transparency logs (RFC 6962), read directly | None | [https://www.rfc-editor.org/rfc/rfc6962](https://www.rfc-editor.org/rfc/rfc6962) (200) | “publicly auditable, append-only, untrusted logs of all issued certificates” |
| 15 | GH Archive — all public GitHub events (hourly files) | None | [https://www.gharchive.org/](https://www.gharchive.org/) (200) | “public GitHub timeline, archive it , and make it easily accessible for further analysis” |
| 16 | PSK Reporter amateur-radio reception reports | None | [https://www.mqtt.pskreporter.info/](https://www.mqtt.pskreporter.info/) (200) | “A real-time MQTT distribution of every spot reported to pskreporter” |
| 17 | Sensor.Community citizen air-quality sensors | None | [https://sensor.community/en/](https://sensor.community/en/) (200) | “DB Contents License [the site footer link 'DB Contents License' points to https://opendatacommons.org/licenses/dbcl/1-0/ (Open Data Commons DbCL v1.0)]” |
| 18 | Crossref scholarly metadata (works indexed per day) | None | [https://www.crossref.org/documentation/retrieve-metadata/rest-api/](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) (200) | “No sign-up is required to use the REST API, and almost none of the metadata is subject to copyright, and you may use it for any purpose” |
| 19 | EarthScope (IRIS) SeedLink real-time seismic waveforms | None | [https://ds.iris.edu/ds/nodes/dmc/services/seedlink/](https://ds.iris.edu/ds/nodes/dmc/services/seedlink/) (200) | “a publicly accessible SeedLink server on the following host and port: host port rtserve” |
| 20 | USGS Water Services instantaneous values (river gauges) | None | [https://waterservices.usgs.gov/](https://waterservices.usgs.gov/) (200) | “decommissioned February 22nd, 2027 WaterServices will be permanently shut down on February 22nd, 2027” |
| 21 | Polymarket CLOB market channel (prediction-market prices) | None | [https://docs.polymarket.com/developers/CLOB/websocket/market-channel](https://docs.polymarket.com/developers/CLOB/websocket/market-channel) (200) | “public market data your application depends on current without repeated polling” |
| 22 | Base (L2) contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 23 | Polygon PoS contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 24 | BNB Smart Chain contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 25 | Ethereum mainnet contract event logs (PublicNode RPC) | None | [https://www.publicnode.com/](https://www.publicnode.com/) (200) | “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains” |
| 26 | Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN) | None | [https://docs.bitso.com/bitso-api/docs](https://docs.bitso.com/bitso-api/docs) (200) | “s Look Up Orders Cancel an Order List Fees WEBSOCKET API General Trades Channel Diff-Orders Channel Orders Channel Processed-Orders Channel CONVERSIONS Understanding Conversions Request a Conversion Quote Execut” |
| 27 | OKX public tickers | None | [https://www.okx.com/docs-v5/en/](https://www.okx.com/docs-v5/en/) (200) | “Public Channel Public structure block trades channel Public block trades channel Block tickers” |
| 28 | XRP Ledger transactions | None | [https://xrpl.org/docs/tutorials/public-servers](https://xrpl.org/docs/tutorials/public-servers) (200) | “io/ Full history server cluster with Clio InFTF Mainnet https://xrplcluster” |
| 29 | Coinbase Exchange ticker | None | [https://docs.cdp.coinbase.com/exchange/websocket-feed/overview](https://docs.cdp.coinbase.com/exchange/websocket-feed/overview) (200) | “ebSocket Overview Copy page Copy page Copy page Copy page The WebSocket feed is publicly available and provides real-time market data updates for orders and trades” |
| 30 | Deribit perpetual futures ticker | None | [https://docs.deribit.com/](https://docs.deribit.com/) (200) | “agement/private-unsubscribe_all\",\"autogeneratedByOpenApi\":true},{\"title\":\"public/subscribe\",\"description\":\"Subscribe to one or more channels” |
| 31 | Bitstamp live trades | None | [https://www.bitstamp.net/websocket/v2/](https://www.bitstamp.net/websocket/v2/) (200) | not found |
| 32 | Albion Online Data Project market orders | Published public credentials | [https://github.com/ao-data/albiondata-client](https://github.com/ao-data/albiondata-client) (200) | “ternate_user_config_repo","async_conversion_coverage_enabled","billing_billable_licenses_cost_center_bucket_fix","billing_budget_expiration","billing_cost_center_list_assigned_resources","billing_discount_th” |
| 33 | Twitch chat (anonymous read-only IRC) | Anonymous (justinfan) read-only login | [https://legal.twitch.com/legal/developer-agreement/](https://legal.twitch.com/legal/developer-agreement/) (200) | “Chat We consider chat to be an essential component of the broadcast experience on Twitch” |
| 34 | Digitraffic Finland road traffic (TMS) and road-weather sensors | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 35 | Digitraffic Finland train GPS locations | None | [https://www.digitraffic.fi/en/terms-of-service/](https://www.digitraffic.fi/en/terms-of-service/) (200) | “Creative Commons 4.0 By license” |
| 36 | MTA New York City Subway GTFS-Realtime (A/C/E feed) | None | [https://www.mta.info/developers](https://www.mta.info/developers) (403) | “Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to apply for a license. [page refuses scripted requests (HTTP 403); text retrieved with the webfetch tool on 2026-10-13]” |
| 37 | OpenStreetMap minutely replication diffs | None | [https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) (200) | “Open Data Commons Open Database License (ODbL) by the OpenStreetMap Foundation (OSMF)” |
| 38 | npm registry replication changes | None | [https://docs.npmjs.com/policies/open-source-terms](https://docs.npmjs.com/policies/open-source-terms) (200) | “rted Setting up your npm user account Creating a new user account on the public registry Creating a strong password Receiving a one-time password over email About two-factor authentication Configuring two-factor authentication Accessing npm using t” |
| 39 | Reverse Beacon Network (CW/RTTY skimmer spots) | None | [https://www.reversebeacon.net/](https://www.reversebeacon.net/) (200) | “lst about A Short History Telnet servers Get Smart About the RBN Who We Are RBN Value Multipliers ARCluster V6 Filtering Red Pitaya, preparing Guide to the new site (beta) How to get spotted b” |
| 40 | Solana program logs (public mainnet RPC) | None (public RPC is rate-limited) | [https://solana.com/docs/references/clusters](https://solana.com/docs/references/clusters) (200) | “Each of these public endpoints are subject to rate limits, but are available for users and developers to interact with the Solana blockchain” |
| 41 | Gemini market data v1 (order-book changes + trades) | None | [https://developer.gemini.com/websocket/streams.md](https://developer.gemini.com/websocket/streams.md) (200) | “er ID â an obfuscated alias for the numeric order ID ('i'), safe for external/public display \| \| 'c' \| string \| Client order ID” |
| 42 | Hyperliquid trades | None | [https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/we…](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) (200) | “: int , fast: boolean (5 levels if fast, 20 levels if slow) Data format: WsBook trades : Subscription message: { &quot;type&quot;: &quot;trades&quot;, &quot;coin&quot;: &quot;&lt;coin_symbol&gt;&quot; } Dat” |
| 43 | Bybit spot tickers | None | [https://bybit-exchange.github.io/docs/v5/websocket/public/ticker](https://bybit-exchange.github.io/docs/v5/websocket/public/ticker) (200) | “Spot &amp; Option tickers message are snapshot only Push frequency: Derivatives &amp; Options - 100ms , Spot - 50ms Topic: tickers” |
| 44 | Kraken trades + ticker (v2) | None | [https://docs.kraken.com/api/docs/websocket-v2/trade](https://docs.kraken.com/api/docs/websocket-v2/trade) (200) | “base-ui-disable-scrollbar::-webkit-scrollbar{display:none} Trades - Kraken Developers !function(){var b=""; function a(p){if(p==null)return"/";p=""+p;if(""===p)return"/";return"/"===p” |
| 45 | Bitfinex trades + ticker (public v2) | None | [https://docs.bitfinex.com/docs/ws-public](https://docs.bitfinex.com/docs/ws-public) (200) | “Public Channels {"@context":"https://schema” |
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

## 7. Enrichment joins verified

For sources whose raw events carry fewer than 10 attributes, the join a consumer would perform was executed live: the metadata record for the key found in a real sampled event was fetched, flattened, and merged with that event. The counts below are measured, not estimated. A join adds one request per key (cacheable for static metadata such as stations, stops or instruments).

Collisions between event and metadata field names are kept as separate `meta.*` fields, so attributes after the join = raw attributes + metadata attributes. The *median raw* column is the source's median over all sampled events; the join itself was executed on the latest sampled event, whose own attribute count is shown.

| Source | Median raw attrs | Join key | Metadata endpoint (HTTP) | Metadata attrs | Median after join | ≥10 | Verified on event with | Checked (UTC) |
|---|---:|---|---|---:|---:|:-:|---:|---|
| [Digitraffic Finland road traffic (TMS) and road-weather sen…](#s-dt_road) | 2.0 | stationId from the MQTT topic tms-v2/{stationId}/{sensorId} | `https://tie.digitraffic.fi/api/tms/v1/stations/23572` (200) | 39 | 41.0 | ✅ | 4 → 43 | 2026-10-13T04:35:34Z |
| [Digitraffic Finland train GPS locations](#s-dt_rail) | 8.0 | (departureDate, trainNumber) | `https://rata.digitraffic.fi/api/v1/trains/2026-10-13/1` (200) | 13 | 21.0 | ✅ | 8 → 21 | 2026-10-13T04:35:35Z |
| [MTA New York City Subway GTFS-Realtime (A/C/E feed)](#s-mta_gtfsrt) | 6.5 | vehicle.stopId → stops.txt; vehicle.trip.routeId → routes.txt | `https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip` (200) | 16 | 22.5 | ✅ | 9 → 25 | 2026-10-13T04:35:36Z |
| [npm registry replication changes](#s-npm) | 3.0 | id (package name) | `https://registry.npmjs.org/@aztec-labs%2fworld-state/latest` (200) | 27 | 30.0 | ✅ | 3 → 30 | 2026-10-13T04:35:36Z |
| [Gemini market data v1 (order-book changes + trades)](#s-gemini) | 9.0 | symbol | `https://api.gemini.com/v1/symbols/details/btcusd` (200) | 11 | 20.0 | ✅ | 9 → 20 | 2026-10-13T04:35:36Z |
| [Solana program logs (public mainnet RPC)](#s-solana) | 4.0 | value.signature | `https://api.mainnet-beta.solana.com (getTransaction)` (200) | 18 | 22.0 | ✅ | 4 → 22 | 2026-10-13T04:35:36Z |
| [Hyperliquid trades](#s-hyperliquid) | 8.0 | coin | `https://api.hyperliquid.xyz/info {type: metaAndAssetCtxs}` (200) | 14 | 22.0 | ✅ | 8 → 22 | 2026-10-13T04:35:37Z |
| [Bybit spot tickers](#s-bybit) | 9.0 | symbol | `https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=BTCUSDT` (200) | 22 | 31.0 | ✅ | 9 → 31 | 2026-10-13T04:35:37Z |
| [Kraken trades + ticker (v2)](#s-kraken) | 7.0 | symbol (BTC/USD → XBTUSD) | `https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD` (200) | 25 | 32.0 | ✅ | 14 → 39 | 2026-10-13T04:35:38Z |

Digitraffic road events come from two topic families: `tms-v2/{stationId}/{sensorId}` (traffic counts, 4 attributes) joined above with the TMS station, and `weather-v2/{stationId}/{sensorId}` (road weather, 2 attributes), whose station record `https://tie.digitraffic.fi/api/weather/v1/stations/1002` (station 1002 observed in the sampled topic `weather-v2/1002/24`) returned HTTP 200 with 31 attributes when this report was prepared — so both families exceed 10 attributes after the join.

Not joined here: OpenStreetMap minutely diffs already carry each element's tags (`tag:*`), which is where their attributes come from; Reverse Beacon Network spots have no documented metadata API that was tested; Bitfinex pair configuration returns unnamed array positions, so its fields could not be named from documentation and it is not counted.

## 8. Combining streams

The project document allows several streams to be used together to reach the average rate (“Esta permitido utilizar más de un stream a la vez para conseguir el número de eventos mínimo en promedio”). Every event must still have ≥10 attributes, so only sources with a median of ≥10 attributes are combined. Combined rate = sum of the measured average rates.

| Source | Avg ev/s | Median attrs |
|---|---:|---:|
| [Vélib' Métropole Paris bike-share station status (GBFS)](#s-velib) | 0.896 | 12.0 |
| [Stellar Horizon operations stream](#s-stellar) | 0.167 | 22.0 |
| [ENA (EMBL-EBI) sequencing runs made public — DNA/genomics](#s-ena) | 0.151 | 196.0 |
| [PyPI newest releases feed](#s-pypi) | 0.098 | 33.5 |
| [MLB Stats API live game feed](#s-mlb) | 0.057 | 44.0 |

Minimal combinations of these sources alone that reach ≥1 event/s (3; a combination is minimal when no subset of it already reaches 1 event/s):

| Combination | Combined ev/s |
|---|---:|
| Vélib' Métropole Paris bike-share station st… + Stellar Horizon operations stream | 1.063 |
| Vélib' Métropole Paris bike-share station st… + PyPI newest releases feed + MLB Stats API live game feed | 1.051 |
| Vélib' Métropole Paris bike-share station st… + ENA (EMBL-EBI) sequencing runs made public —… | 1.047 |

Any of these can also be combined with a source that already meets both requirements; the rates above are from the sampled windows and vary with the time of day (see each source's per-round table).

## 9. Per-source detail

<a id="s-hsl"></a>
### 1. HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)

- **Verdict:** Meets both — average 816.10 events/s, median 22.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://mqtt.hsl.fi:443/`
- **Request:** `SUBSCRIBE /hfp/v2/journey/ongoing/vp/#`
- **Access:** None
- **Documentation:** https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md (HTTP 200)
- **Terms / licence:** https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md (HTTP 200) — “Digitransit makes the data available based on JHS-189 [permission to use the open data] and [Creative Commons name 4.0 (CC BY)](https://creativecommons.org/licenses/by/4.0/) licensing. CC BY is global, gratuitous, non-exclusive, and non”
- **Measurement note (latest representative round):** example topic: /hfp/v2/journey/ongoing/vp/tram/0040/00458/100HC3/1/Kuusitie/05:49/1140436/5/60;24/19/82/42
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 389.87 | 23,392 | 60 | 22.0 | 22 | 23 |
| 2026-10-13T02:11 | ok | 435.05 | 26,103 | 60 | 22.0 | 22 | 23 |
| 2026-10-13T03:23 | ok | 1,067.97 | 64,078 | 60 | 22.0 | 22 | 23 |
| 2026-10-13T04:23 | ok | 1,371.53 | 82,292 | 60 | 22.0 | 22 | 23 |

<details><summary>Sample event — 22 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `desi` | string | H |
| 2 | `dir` | string (numeric) | 1 |
| 3 | `oper` | integer | 40 |
| 4 | `veh` | integer | 458 |
| 5 | `tst` | string (date/time) | 2026-10-13T02:10:18.256Z |
| 6 | `tsi` | integer | 1791857418 |
| 7 | `spd` | number | 0.0 |
| 8 | `hdg` | null | null |
| 9 | `lat` | number | 60.184476 |
| 10 | `long` | number | 24.922378 |
| 11 | `acc` | number | 0.0 |
| 12 | `dl` | null | null |
| 13 | `odo` | integer | 0 |
| 14 | `drst` | integer | 0 |
| 15 | `oday` | string | 2026-10-13 |
| 16 | `jrn` | integer | 33 |
| 17 | `line` | integer | 1177 |
| 18 | `start` | string | 05:49 |
| 19 | `loc` | string | GPS |
| 20 | `stop` | null | null |
| 21 | `route` | string | 100HC3 |
| 22 | `occu` | integer | 0 |

</details>

<a id="s-entur"></a>
### 2. Entur Norway real-time vehicle positions

- **Verdict:** Meets both — average 36.16 events/s, median 19.0 attributes per event.
- **Delivery:** poll · GraphQL over HTTPS (POST), polled every 15 s
- **Endpoint:** `https://api.entur.io/realtime/v2/vehicles/graphql`
- **Request:** `POST {query: vehicles{vehicleId lastUpdated line location speed delay ...}} with header ET-Client-Name`
- **Access:** None (identifying ET-Client-Name header required)
- **Documentation:** https://developer.entur.org/pages-real-time-intro (HTTP 200)
- **Terms / licence:** https://developer.entur.org/pages-intro-setup-and-access/ (HTTP 200) — “Norwegian Licence for Open Government Data (NLOD)”
- **Measurement note (latest representative round):** 2 polls every 15s; 1026 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 3.76 | 290 | 77 | 19.0 | 19 | 20 |
| 2026-10-13T02:11 | ok | 12.79 | 780 | 61 | 19.0 | 19 | 20 |
| 2026-10-13T03:23 | ok | 31.98 | 1,556 | 49 | 19.0 | 19 | 20 |
| 2026-10-13T04:23 | ok | 96.08 | 4,759 | 50 | 19.0 | 19 | 20 |

<details><summary>Sample event — 19 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `vehicleId` | string (numeric) | 3620703295 |
| 2 | `lastUpdated` | string (date/time) | 2026-10-13T02:09:44Z |
| 3 | `codespace.codespaceId` | string | BRA |
| 4 | `line.lineRef` | string | BRA:Line:4_6119 |
| 5 | `line.publicCode` | string (numeric) | 119 |
| 6 | `line.lineName` | string | Hokksund - Voldstad - Sundet |
| 7 | `location.latitude` | number | 59.7671945951879 |
| 8 | `location.longitude` | number | 9.90892969071865 |
| 9 | `bearing` | null | null |
| 10 | `speed` | null | null |
| 11 | `delay` | number | -11416.0 |
| 12 | `occupancyStatus` | string | noData |
| 13 | `vehicleStatus` | string | ASSIGNED |
| 14 | `inCongestion` | boolean | false |
| 15 | `originName` | string | Sundet |
| 16 | `destinationName` | string | Vestfossen stasjon |
| 17 | `serviceJourney.id` | string | BRA:ServiceJourney:6119_260630061448489_1014 |
| 18 | `operator.operatorRef` | string | BRA:Operator:61 |
| 19 | `mode` | string | BUS |

</details>

<a id="s-dt_marine"></a>
### 3. Digitraffic Finland marine AIS vessel locations

- **Verdict:** Meets both — average 32.70 events/s, median 10.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://meri.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE vessels-v2/+/location (also vessels-v2/+/metadata)`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/marine-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: vessels-v2/636025787/location
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 31.50 | 1,890 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 31.65 | 1,899 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 32.47 | 1,948 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 35.20 | 2,112 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `cog` | number | 74.9 |
| 2 | `heading` | integer | 77 |
| 3 | `lat` | number | 59.721775 |
| 4 | `lon` | number | 24.353438 |
| 5 | `navStat` | integer | 0 |
| 6 | `posAcc` | boolean | true |
| 7 | `raim` | boolean | false |
| 8 | `rot` | integer | 0 |
| 9 | `sog` | number | 11.2 |
| 10 | `time` | integer | 1791857417 |

</details>

<a id="s-ndov"></a>
### 4. NDOV Loket Netherlands public transport KV6 (all operators)

- **Verdict:** Meets both — average 25.60 events/s, median 15.0 attributes per event.
- **Delivery:** live · ZeroMQ PUB/SUB (gzip XML)
- **Endpoint:** `tcp://pubsub.besteffort.ndovloket.nl:7658`
- **Request:** `SUB '' (all envelopes)`
- **Access:** None (best-effort relay)
- **Documentation:** https://ndovloket.nl/ (HTTP 200)
- **Terms / licence:** https://ndovloket.nl/ (HTTP 200) — “Open Data Bestanden Datasets Realtime Home Projecten FAQ Documentatie Data Incidenten Aanmelden Grenzeloze Openbaar Vervoer Informatie voor Nederland en daar net buiten”
- **Measurement note (latest representative round):** KV6 vehicle-journey messages (all operators) on the best-effort ZeroMQ relay
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.30 | 78 | 60 | 15.0 | 16 | 16 |
| 2026-10-13T02:11 | ok | 1.27 | 76 | 60 | 15.0 | 16 | 16 |
| 2026-10-13T03:23 | ok | 12.13 | 728 | 60 | 15.0 | 16 | 19 |
| 2026-10-13T04:23 | ok | 87.70 | 5,262 | 60 | 15.0 | 16 | 19 |

<details><summary>Sample event — 16 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `dataownercode` | string | CXX |
| 2 | `lineplanningnumber` | string | M097 |
| 3 | `operatingday` | string | 2026-10-12 |
| 4 | `journeynumber` | string (numeric) | 4007 |
| 5 | `reinforcementnumber` | string (numeric) | 0 |
| 6 | `omloopnumber` | string (numeric) | 630103 |
| 7 | `userstopcode` | string (numeric) | 56330680 |
| 8 | `passagesequencenumber` | string (numeric) | 0 |
| 9 | `timestamp` | string (date/time) | 2026-10-13T04:10:18+02:00 |
| 10 | `source` | string | VEHICLE |
| 11 | `vehiclenumber` | string (numeric) | 9774 |
| 12 | `punctuality` | string (numeric) | -36 |
| 13 | `distancesincelastuserstop` | string (numeric) | 1244 |
| 14 | `rd-x` | string (numeric) | 107981 |
| 15 | `rd-y` | string (numeric) | 478436 |
| 16 | `messagetype` | string | ONROUTE |

</details>

<a id="s-mbta_gtfsrt"></a>
### 5. MBTA Boston GTFS-Realtime VehiclePositions

- **Verdict:** Meets both — average 13.87 events/s, median 18.0 attributes per event.
- **Delivery:** poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s
- **Endpoint:** `https://cdn.mbta.com/realtime/VehiclePositions.pb`
- **Request:** `GET (also TripUpdates.pb, Alerts.pb)`
- **Access:** None
- **Documentation:** https://www.mbta.com/developers/gtfs-realtime (HTTP 200)
- **Terms / licence:** https://www.mbta.com/developers/gtfs-realtime (HTTP 200) — “Use of MBTA data is governed by the MassDOT Developers License Agreement”
- **Measurement note (latest representative round):** 4 polls every 15s; 342 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 13.08 | 848 | 65 | 18.0 | 18 | 20 |
| 2026-10-13T02:11 | ok | 14.33 | 801 | 56 | 18.0 | 18 | 20 |
| 2026-10-13T03:23 | ok | 14.88 | 686 | 46 | 18.0 | 18 | 20 |
| 2026-10-13T04:23 | ok | 13.18 | 602 | 46 | 18.0 | 18 | 20 |

<details><summary>Sample event — 18 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | string | y2078 |
| 2 | `vehicle.trip.tripId` | string (numeric) | 78273645 |
| 3 | `vehicle.trip.startTime` | string | 21:58:00 |
| 4 | `vehicle.trip.startDate` | string (numeric) | 20261012 |
| 5 | `vehicle.trip.scheduleRelationship` | string | SCHEDULED |
| 6 | `vehicle.trip.routeId` | string (numeric) | 111 |
| 7 | `vehicle.trip.directionId` | integer | 0 |
| 8 | `vehicle.position.latitude` | number | 42.38946 |
| 9 | `vehicle.position.longitude` | number | -71.03907 |
| 10 | `vehicle.position.bearing` | number | 90.0 |
| 11 | `vehicle.currentStopSequence` | integer | 5 |
| 12 | `vehicle.currentStatus` | string | IN_TRANSIT_TO |
| 13 | `vehicle.timestamp` | string (numeric) | 1791857410 |
| 14 | `vehicle.stopId` | string (numeric) | 5613 |
| 15 | `vehicle.vehicle.id` | string | y2078 |
| 16 | `vehicle.vehicle.label` | string (numeric) | 2078 |
| 17 | `vehicle.occupancyStatus` | string | FEW_SEATS_AVAILABLE |
| 18 | `vehicle.occupancyPercentage` | integer | 60 |

</details>

<a id="s-adsb_fi"></a>
### 6. adsb.fi open data aircraft — 250 NM around Mexico City airport

- **Verdict:** Meets both — average 4.22 events/s, median 39.0 attributes per event.
- **Delivery:** poll · REST JSON, polled every 5 s
- **Endpoint:** `https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/adsbfi/opendata (HTTP 200)
- **Terms / licence:** https://raw.githubusercontent.com/adsbfi/opendata/main/README.md (HTTP 200) — “Please contact us if you have commercial or higher request rate requirements”
- **Measurement note (latest representative round):** 9 polls every 5s; 35 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position yes · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.61 | 263 | 57 | 39.0 | 54 | 56 |
| 2026-10-13T02:11 | ok | 5.24 | 293 | 56 | 39.0 | 54 | 56 |
| 2026-10-13T03:23 | ok | 4.00 | 230 | 58 | 39.0 | 52 | 57 |
| 2026-10-13T04:23 | ok | 3.04 | 174 | 57 | 39.0 | 52 | 55 |

<details><summary>Sample event — 54 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `hex` | string | ad6b0e |
| 2 | `type` | string | adsb_icao |
| 3 | `flight` | string | AMX014   |
| 4 | `r` | string | N964AM |
| 5 | `t` | string | B788 |
| 6 | `desc` | string | BOEING 787-8 Dreamliner |
| 7 | `ownOp` | string | WILMINGTON TRUST CO TRUSTEE |
| 8 | `year` | string (numeric) | 2013 |
| 9 | `alt_baro` | integer | 39000 |
| 10 | `alt_geom` | integer | 41525 |
| 11 | `gs` | number | 472.7 |
| 12 | `ias` | integer | 258 |
| 13 | `tas` | integer | 482 |
| 14 | `mach` | number | 0.828 |
| 15 | `wd` | integer | 66 |
| 16 | `ws` | integer | 13 |
| 17 | `oat` | integer | -50 |
| 18 | `tat` | integer | -19 |
| 19 | `track` | number | 103.33 |
| 20 | `track_rate` | number | 0.0 |
| 21 | `roll` | number | -0.18 |
| 22 | `mag_heading` | number | 100.2 |
| 23 | `true_heading` | number | 102.25 |
| 24 | `baro_rate` | integer | 0 |
| 25 | `geom_rate` | integer | 0 |
| 26 | `squawk` | string (numeric) | 3262 |
| 27 | `emergency` | string | none |
| 28 | `category` | string | A5 |
| 29 | `nav_qnh` | number | 1012.8 |
| 30 | `nav_altitude_mcp` | integer | 39008 |
| 31 | `nav_heading` | number | 99.84 |
| 32 | `nav_modes` | list (serialised) | ['autopilot', 'vnav', 'lnav', 'tcas'] |
| 33 | `lat` | number | 18.811981 |
| 34 | `lon` | number | -95.079264 |
| 35 | `nic` | integer | 8 |
| 36 | `rc` | integer | 186 |
| 37 | `seen_pos` | number | 0.056 |
| 38 | `version` | integer | 2 |
| 39 | `nic_baro` | integer | 1 |
| 40 | `nac_p` | integer | 9 |
| 41 | `nac_v` | integer | 1 |
| 42 | `sil` | integer | 3 |
| 43 | `sil_type` | string | perhour |
| 44 | `gva` | integer | 2 |
| 45 | `sda` | integer | 2 |
| 46 | `alert` | integer | 0 |
| 47 | `spi` | integer | 0 |
| 48 | `mlat` | list (serialised) | [] |
| 49 | `tisb` | list (serialised) | [] |
| 50 | `messages` | integer | 11920 |
| 51 | `seen` | number | 0.1 |
| 52 | `rssi` | number | -15.8 |
| 53 | `dst` | number | 229.567 |
| 54 | `dir` | number | 98.7 |

</details>

<a id="s-bicing"></a>
### 7. Bicing Barcelona bike-share station status (GBFS)

- **Verdict:** Meets both — average 3.37 events/s, median 14.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing (HTTP 200)
- **Terms / licence:** https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing (HTTP 200) — “token")”
- **Measurement note (latest representative round):** 6 polls every 10s; 543 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 3.73 | 228 | 61 | 14.0 | 14 | 14 |
| 2026-10-13T02:11 | ok | 3.17 | 173 | 54 | 14.0 | 14 | 14 |
| 2026-10-13T03:23 | ok | 3.54 | 182 | 51 | 14.0 | 14 | 14 |
| 2026-10-13T04:23 | ok | 3.02 | 155 | 51 | 14.0 | 14 | 14 |

<details><summary>Sample event — 14 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `station_id` | string (numeric) | 1 |
| 2 | `num_bikes_available` | integer | 14 |
| 3 | `num_bikes_disabled` | integer | 5 |
| 4 | `is_charging_station` | boolean | true |
| 5 | `status` | string | IN_SERVICE |
| 6 | `traffic` | null | null |
| 7 | `num_docks_available` | integer | 26 |
| 8 | `num_docks_disabled` | integer | 0 |
| 9 | `last_reported` | integer | 1791857315 |
| 10 | `is_installed` | boolean | true |
| 11 | `is_renting` | boolean | true |
| 12 | `is_returning` | boolean | true |
| 13 | `vehicle_docks_available` | list (serialised) | [{'vehicle_type_ids': ['ICONIC', 'BOOST', 'FIT', 'EFIT'], 'count': 26}] |
| 14 | `vehicle_types_available` | string | [{'vehicle_type_id': 'FIT', 'count': 0}, {'vehicle_type_id': 'BOOST', 'count': 4}, {'vehi… |

</details>

<a id="s-ecobici"></a>
### 8. EcoBici CDMX bike-share station status (GBFS)

- **Verdict:** Meets both — average 2.96 events/s, median 11.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json`
- **Request:** `GET (station_information.json for names/coordinates)`
- **Access:** None
- **Documentation:** https://ecobici.cdmx.gob.mx/datos-abiertos/ (HTTP 200)
- **Terms / licence:** https://ecobici.cdmx.gob.mx/datos-abiertos/ (HTTP 200) — “GBFS (General Bikeshare Feed Specification)”
- **Measurement note (latest representative round):** 5 polls every 10s; 677 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.75 | 144 | 52 | 11.0 | 11 | 11 |
| 2026-10-13T02:11 | ok | 5.78 | 322 | 56 | 11.0 | 11 | 11 |
| 2026-10-13T03:23 | ok | 1.90 | 100 | 53 | 11.0 | 11 | 11 |
| 2026-10-13T04:23 | ok | 1.39 | 73 | 52 | 11.0 | 11 | 11 |

<details><summary>Sample event — 11 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `station_id` | string (numeric) | 1 |
| 2 | `num_bikes_available` | integer | 11 |
| 3 | `num_bikes_disabled` | integer | 2 |
| 4 | `num_docks_available` | integer | 26 |
| 5 | `num_docks_disabled` | integer | 0 |
| 6 | `is_installed` | integer | 1 |
| 7 | `is_renting` | integer | 1 |
| 8 | `is_returning` | integer | 1 |
| 9 | `last_reported` | integer | 1791857391 |
| 10 | `eightd_has_available_keys` | boolean | false |
| 11 | `is_charging` | boolean | false |

</details>

<a id="s-adsb_lol"></a>
### 9. adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport

- **Verdict:** Meets both — average 1.76 events/s, median 37.8 attributes per event.
- **Delivery:** poll · REST JSON, polled every 15 s
- **Endpoint:** `https://api.adsb.lol/v2/point/19.436/-99.072/250`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.adsb.lol/docs/open-data/api/ (HTTP 200)
- **Terms / licence:** https://www.adsb.lol/docs/open-data/api/ (HTTP 200) — “ODbL 1”
- **Measurement note (latest representative round):** 3 polls every 15s; 44 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position yes · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.86 | 84 | 45 | 38.0 | 51 | 53 |
| 2026-10-13T02:11 | ok | 2.12 | 119 | 56 | 38.0 | 51 | 53 |
| 2026-10-13T03:23 | ok | 1.48 | 70 | 47 | 37.0 | 51 | 54 |
| 2026-10-13T04:23 | ok | 1.59 | 75 | 47 | 37.5 | 51 | 52 |

<details><summary>Sample event — 51 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `hex` | string | ab761e |
| 2 | `type` | string | adsb_icao |
| 3 | `flight` | string | AMX555   |
| 4 | `r` | string | N838AM |
| 5 | `t` | string | B39M |
| 6 | `alt_baro` | integer | 36000 |
| 7 | `alt_geom` | integer | 38425 |
| 8 | `gs` | number | 470.9 |
| 9 | `ias` | integer | 263 |
| 10 | `tas` | integer | 466 |
| 11 | `mach` | number | 0.792 |
| 12 | `wd` | integer | 142 |
| 13 | `ws` | integer | 10 |
| 14 | `oat` | integer | -45 |
| 15 | `tat` | integer | -17 |
| 16 | `track` | number | 260.96 |
| 17 | `track_rate` | number | 0.0 |
| 18 | `roll` | number | 0.18 |
| 19 | `mag_heading` | number | 257.52 |
| 20 | `true_heading` | number | 259.84 |
| 21 | `baro_rate` | integer | 64 |
| 22 | `geom_rate` | integer | 32 |
| 23 | `squawk` | string (numeric) | 0610 |
| 24 | `emergency` | string | none |
| 25 | `category` | string | A3 |
| 26 | `nav_qnh` | number | 1013.6 |
| 27 | `nav_altitude_mcp` | integer | 36000 |
| 28 | `nav_altitude_fms` | integer | 36000 |
| 29 | `nav_heading` | number | 258.75 |
| 30 | `lat` | number | 19.124451 |
| 31 | `lon` | number | -95.726823 |
| 32 | `nic` | integer | 8 |
| 33 | `rc` | integer | 186 |
| 34 | `seen_pos` | number | 0.215 |
| 35 | `version` | integer | 2 |
| 36 | `nic_baro` | integer | 1 |
| 37 | `nac_p` | integer | 10 |
| 38 | `nac_v` | integer | 2 |
| 39 | `sil` | integer | 3 |
| 40 | `sil_type` | string | perhour |
| 41 | `gva` | integer | 2 |
| 42 | `sda` | integer | 2 |
| 43 | `alert` | integer | 0 |
| 44 | `spi` | integer | 0 |
| 45 | `mlat` | list (serialised) | [] |
| 46 | `tisb` | list (serialised) | [] |
| 47 | `messages` | integer | 10146 |
| 48 | `seen` | number | 0.1 |
| 49 | `rssi` | number | -6.7 |
| 50 | `dst` | number | 190.499 |
| 51 | `dir` | number | 95.1 |

</details>

<a id="s-dt_rail_trains"></a>
### 10. Digitraffic Finland train timetables/actuals

- **Verdict:** Meets both — average 1.08 events/s, median 13.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://rata.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE trains/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/railway-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: trains/2026-10-12/3061/Cargo/T/vr//true/REGULAR
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.82 | 49 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 0.88 | 53 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 1.23 | 74 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T04:23 | ok | 1.38 | 83 | 60 | 13.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `commuterLineID` | string |  |
| 2 | `runningCurrently` | boolean | true |
| 3 | `cancelled` | boolean | false |
| 4 | `version` | integer | 293816082956 |
| 5 | `timetableType` | string | REGULAR |
| 6 | `timetableAcceptanceDate` | string (date/time) | 2025-10-30T06:30:01Z |
| 7 | `departureDate` | string | 2026-10-12 |
| 8 | `trainNumber` | integer | 3061 |
| 9 | `operatorUICCode` | integer | 10 |
| 10 | `operatorShortCode` | string | vr |
| 11 | `timeTableRows` | string | [{'type': 'DEPARTURE', 'commercialTrack': '218', 'cancelled': False, 'scheduledTime': '20… |
| 12 | `trainCategory` | string | Cargo |
| 13 | `trainType` | string | T |

</details>

<a id="s-metar"></a>
### 11. NOAA aviationweather.gov METAR observations (global airports)

- **Verdict:** Meets both — average 1.35 events/s, median 38.0 attributes per event.
- **Delivery:** batch · gzip CSV cache file, refreshed every minute
- **Endpoint:** `https://aviationweather.gov/data/cache/metars.cache.csv.gz`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://aviationweather.gov/data/api/ (HTTP 200)
- **Terms / licence:** https://aviationweather.gov/data/api/ (HTTP 200) — “Cache This service facilitates machine-to-machine access to aviation weather information”
- **Measurement note (latest representative round):** cache file lists 5001 stations; rate = observations stamped within the last hour / 3600
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Weather & environment

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.33 | 4,796 | 3,600 | 38.0 | 38 | 38 |
| 2026-10-13T02:11 | ok | 1.35 | 4,850 | 3,600 | 38.0 | 38 | 38 |
| 2026-10-13T03:23 | ok | 1.37 | 4,920 | 3,600 | 38.0 | 38 | 38 |
| 2026-10-13T04:23 | ok | 1.36 | 4,911 | 3,600 | 38.0 | 38 | 38 |

<details><summary>Sample event — 38 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `raw_text` | string | SPECI CYQV 130208Z AUTO 02004KT 1 3/4SM -RA BKN006 OVC012 04/ A2999 RMK DP MISG SLP181 |
| 2 | `station_id` | string | CYQV |
| 3 | `observation_time` | string (date/time) | 2026-10-13T02:08:00.000Z |
| 4 | `latitude` | string (numeric) | 51.2600 |
| 5 | `longitude` | string (numeric) | -102.4610 |
| 6 | `temp_c` | string (numeric) | 4 |
| 7 | `dewpoint_c` | string |  |
| 8 | `wind_dir_degrees` | string (numeric) | 20 |
| 9 | `wind_speed_kt` | string (numeric) | 4 |
| 10 | `wind_gust_kt` | string |  |
| 11 | `visibility_statute_mi` | string (numeric) | 1.75 |
| 12 | `altim_in_hg` | string (numeric) | 29.99 |
| 13 | `sea_level_pressure_mb` | string (numeric) | 1018.1 |
| 14 | `corrected` | string |  |
| 15 | `auto` | string | TRUE |
| 16 | `auto_station` | string |  |
| 17 | `maintenance_indicator_on` | string |  |
| 18 | `no_signal` | string |  |
| 19 | `lightning_sensor_off` | string |  |
| 20 | `freezing_rain_sensor_off` | string |  |
| 21 | `present_weather_sensor_off` | string |  |
| 22 | `wx_string` | string | -RA |
| 23 | `sky_cover` | string |  |
| 24 | `cloud_base_ft_agl` | string |  |
| 25 | `flight_category` | string | IFR |
| 26 | `three_hr_pressure_tendency_mb` | string |  |
| 27 | `maxT_c` | string |  |
| 28 | `minT_c` | string |  |
| 29 | `maxT24hr_c` | string |  |
| 30 | `minT24hr_c` | string |  |
| 31 | `precip_in` | string |  |
| 32 | `pcp3hr_in` | string |  |
| 33 | `pcp6hr_in` | string |  |
| 34 | `pcp24hr_in` | string |  |
| 35 | `snow_in` | string |  |
| 36 | `vert_vis_ft` | string |  |
| 37 | `metar_type` | string | SPECI |
| 38 | `elevation_m` | string (numeric) | 493 |

</details>

<a id="s-ris"></a>
### 12. RIPE NCC RIS Live — global BGP routing updates

- **Verdict:** Meets both — average 1,709.28 events/s, median 11.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ris-live.ripe.net/v1/ws/?client=<identifier>`
- **Request:** `{"type":"ris_subscribe","data":{"type":"UPDATE"}}`
- **Access:** None
- **Documentation:** https://ris-live.ripe.net/manual/ (HTTP 200)
- **Terms / licence:** https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions (HTTP 200) — “Access to and use of the RIPE Data Repository and the Data for any commercial purposes, for example selling the Data or services based on the Data, is not allowed. [these are the RIPE Data Repository terms; the RIS Live manual itself was not found to state separate terms]”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 98.62 | 5,917 | 60 | 11.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 407.42 | 24,445 | 60 | 11.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 2,077.12 | 124,627 | 60 | 11.0 | 13 | 13 |
| 2026-10-13T04:23 | ok | 4,253.95 | 255,237 | 60 | 11.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `timestamp` | number | 1791857414.62 |
| 2 | `peer` | string | 2001:7f8:30:0:2:1:1:3030 |
| 3 | `peer_asn` | string (numeric) | 13030 |
| 4 | `id` | string | 2001:7f8:30:0:2:1:1:3030-01a1330651dc0000 |
| 5 | `host` | string | rrc05.ripe.net |
| 6 | `type` | string | UPDATE |
| 7 | `path` | list (serialised) | [13030, 6939, 4637, 1221, 132847, 154927] |
| 8 | `community` | list (serialised) | [[6939, 1000], [6939, 7548], [6939, 8826], [6939, 9002], [13030, 51702]] |
| 9 | `origin` | string | IGP |
| 10 | `med` | integer | 1 |
| 11 | `aggregator` | string | 154927:163.52.204.1 |
| 12 | `announcements` | list (serialised) | [{'next_hop': '2001:7f8:30:0:2:1:1:3030,fe80::fe0a:81ff:fefe:2415', 'prefixes': ['2402:76… |
| 13 | `withdrawals` | list (serialised) | [] |

</details>

<a id="s-atlas"></a>
### 13. RIPE Atlas measurement results stream (ping)

- **Verdict:** Meets both — average 585.29 events/s, median 25.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://atlas-stream.ripe.net/stream/?client=<identifier>`
- **Request:** `["atlas_subscribe",{"streamType":"result","type":"ping"}]`
- **Access:** None
- **Documentation:** https://atlas.ripe.net/docs/apis/streaming-api (HTTP 200)
- **Terms / licence:** https://atlas.ripe.net/legal/terms-conditions/ (HTTP 200) — no matching text found
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 56.65 | 3,399 | 60 | 25.0 | 26 | 26 |
| 2026-10-13T02:11 | ok | 208.15 | 12,489 | 60 | 25.0 | 26 | 26 |
| 2026-10-13T03:23 | ok | 785.35 | 47,121 | 60 | 25.0 | 26 | 26 |
| 2026-10-13T04:23 | ok | 1,291.02 | 77,461 | 60 | 25.0 | 26 | 26 |

<details><summary>Sample event — 26 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `fw` | integer | 5120 |
| 2 | `mver` | string | 2.6.4 |
| 3 | `lts` | integer | 40 |
| 4 | `dst_name` | string | d1.awsstatic.com |
| 5 | `ttr` | number | 66.673208 |
| 6 | `af` | integer | 4 |
| 7 | `dst_addr` | string | 13.226.115.78 |
| 8 | `src_addr` | string | 192.168.12.11 |
| 9 | `proto` | string | ICMP |
| 10 | `ttl` | integer | 249 |
| 11 | `size` | integer | 64 |
| 12 | `result` | list (serialised) | [{'rtt': 4.857986}, {'rtt': 4.957526}, {'rtt': 4.931453}] |
| 13 | `dup` | integer | 0 |
| 14 | `rcvd` | integer | 3 |
| 15 | `sent` | integer | 3 |
| 16 | `min` | number | 4.857986 |
| 17 | `max` | number | 4.957526 |
| 18 | `avg` | number | 4.915655 |
| 19 | `msm_id` | integer | 177401165 |
| 20 | `prb_id` | integer | 1015336 |
| 21 | `timestamp` | integer | 1791857388 |
| 22 | `msm_name` | string | Ping |
| 23 | `from` | string | 182.52.241.150 |
| 24 | `type` | string | ping |
| 25 | `group_id` | integer | 177401165 |
| 26 | `step` | integer | 240 |

</details>

<a id="s-ct"></a>
### 14. Certificate Transparency logs (RFC 6962), read directly

- **Verdict:** Meets both — average 132.76 events/s, median 17.0 attributes per event.
- **Delivery:** counter · REST JSON (get-sth / get-entries)
- **Endpoint:** `<log url>/ct/v1/get-sth and /ct/v1/get-entries; log list https://www.gstatic.com/ct/log_list/v3/log_list.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.rfc-editor.org/rfc/rfc6962 (HTTP 200)
- **Terms / licence:** https://www.rfc-editor.org/rfc/rfc6962 (HTTP 200) — “publicly auditable, append-only, untrusted logs of all issued certificates”
- **Measurement note (latest representative round):** 9 RFC 6962 logs (static-CT logs not counted); growth over the window: Google 'Argon2026h2' log: 1381; Google 'Xenon2026h2' log: 1551; Cloudflare 'Nimbus2026': 0; DigiCert 'Wyvern2026h2': 1597; DigiCert 'Sphinx2026h2': 1546; Sectigo 'Elephant2026h2': 0; Sectigo 'Tiger2026h2': 0; TrustAsia 'log2026a': 1254; TrustAsia 'log2026b': 978. Raw entry = leaf_input + extra_data (base64); attributes counted after X.509 decoding of 30 entries.
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 129.59 | 8,307 | 64 | 17.0 | 17 | 17 |
| 2026-10-13T02:11 | ok | 103.24 | 6,595 | 64 | 17.0 | 17 | 17 |
| 2026-10-13T03:23 | ok | 161.96 | 9,894 | 61 | 17.0 | 17 | 17 |
| 2026-10-13T04:23 | ok | 136.23 | 8,320 | 61 | 17.0 | 17 | 17 |

<details><summary>Sample event — 17 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `timestamp_ms` | integer | 1791857354079 |
| 2 | `entry_type` | string | x509 |
| 3 | `serial` | string | 5f4cbfe81911a6c2d03f9e3652096539eda |
| 4 | `subject_cn` | null | null |
| 5 | `subject_o` | null | null |
| 6 | `issuer_cn` | string | YE1 |
| 7 | `issuer_o` | string | Let's Encrypt |
| 8 | `issuer_c` | string | US |
| 9 | `not_before` | string (date/time) | 2026-10-13T01:10:43+00:00 |
| 10 | `not_after` | string (date/time) | 2026-10-19T17:10:42+00:00 |
| 11 | `san_count` | integer | 0 |
| 12 | `san_first` | null | null |
| 13 | `key_type` | string | ECPublicKey |
| 14 | `key_size` | integer | 256 |
| 15 | `signature_algorithm` | string | ecdsa-with-SHA384 |
| 16 | `extensions` | integer | 9 |
| 17 | `log` | string | Google 'Argon2026h2' log |

</details>

<a id="s-gharchive"></a>
### 15. GH Archive — all public GitHub events (hourly files)

- **Verdict:** Meets both — average 22.54 events/s, median 18.0 attributes per event.
- **Delivery:** batch · Hourly gzip NDJSON over HTTPS
- **Endpoint:** `https://data.gharchive.org/YYYY-MM-DD-H.json.gz`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.gharchive.org/ (HTTP 200)
- **Terms / licence:** https://www.gharchive.org/ (HTTP 200) — “public GitHub timeline, archive it , and make it easily accessible for further analysis”
- **Measurement note (latest representative round):** hour file 2026-10-12-23 UTC; payload fields vary by event type (union across 1,000 events reported)
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 22.07 | 79,440 | 3,600 | 18.0 | 203 | 362 |
| 2026-10-13T02:11 | ok | 22.07 | 79,440 | 3,600 | 18.0 | 203 | 362 |
| 2026-10-13T03:23 | ok | 22.88 | 82,370 | 3,600 | 18.0 | 168 | 378 |
| 2026-10-13T04:23 | ok | 23.13 | 83,270 | 3,600 | 18.0 | 153 | 380 |

<details><summary>Sample event — 203 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | string (numeric) | 17051373760 |
| 2 | `type` | string | IssueCommentEvent |
| 3 | `actor.id` | string (redacted) | ‹redacted› |
| 4 | `actor.login` | string (redacted) | ‹redacted› |
| 5 | `actor.display_login` | string (redacted) | ‹redacted› |
| 6 | `actor.gravatar_id` | string (redacted) | ‹redacted› |
| 7 | `actor.url` | string (redacted) | ‹redacted› |
| 8 | `actor.avatar_url` | string (redacted) | ‹redacted› |
| 9 | `repo.id` | integer | 1262518964 |
| 10 | `repo.name` | string | Jonathan-Harris1975/HIVE |
| 11 | `repo.url` | string | https://api.github.com/repos/Jonathan-Harris1975/HIVE |
| 12 | `payload.action` | string (redacted) | ‹redacted› |
| 13 | `payload.issue.url` | string (redacted) | ‹redacted› |
| 14 | `payload.issue.repository_url` | string (redacted) | ‹redacted› |
| 15 | `payload.issue.labels_url` | string (redacted) | ‹redacted› |
| 16 | `payload.issue.comments_url` | string (redacted) | ‹redacted› |
| 17 | `payload.issue.events_url` | string (redacted) | ‹redacted› |
| 18 | `payload.issue.html_url` | string (redacted) | ‹redacted› |
| 19 | `payload.issue.id` | string (redacted) | ‹redacted› |
| 20 | `payload.issue.node_id` | string (redacted) | ‹redacted› |
| 21 | `payload.issue.number` | string (redacted) | ‹redacted› |
| 22 | `payload.issue.title` | string (redacted) | ‹redacted› |
| 23 | `payload.issue.user.login` | string (redacted) | ‹redacted› |
| 24 | `payload.issue.user.id` | string (redacted) | ‹redacted› |
| 25 | `payload.issue.user.node_id` | string (redacted) | ‹redacted› |
| 26 | `payload.issue.user.avatar_url` | string (redacted) | ‹redacted› |
| 27 | `payload.issue.user.gravatar_id` | string (redacted) | ‹redacted› |
| 28 | `payload.issue.user.url` | string (redacted) | ‹redacted› |
| 29 | `payload.issue.user.html_url` | string (redacted) | ‹redacted› |
| 30 | `payload.issue.user.followers_url` | string (redacted) | ‹redacted› |
| 31 | `payload.issue.user.following_url` | string (redacted) | ‹redacted› |
| 32 | `payload.issue.user.gists_url` | string (redacted) | ‹redacted› |
| 33 | `payload.issue.user.starred_url` | string (redacted) | ‹redacted› |
| 34 | `payload.issue.user.subscriptions_url` | string (redacted) | ‹redacted› |
| 35 | `payload.issue.user.organizations_url` | string (redacted) | ‹redacted› |
| 36 | `payload.issue.user.repos_url` | string (redacted) | ‹redacted› |
| 37 | `payload.issue.user.events_url` | string (redacted) | ‹redacted› |
| 38 | `payload.issue.user.received_events_url` | string (redacted) | ‹redacted› |
| 39 | `payload.issue.user.type` | string (redacted) | ‹redacted› |
| 40 | `payload.issue.user.user_view_type` | string (redacted) | ‹redacted› |
| 41 | `payload.issue.user.site_admin` | string (redacted) | ‹redacted› |
| 42 | `payload.issue.labels` | string (redacted) | ‹redacted› |
| 43 | `payload.issue.state` | string (redacted) | ‹redacted› |
| 44 | `payload.issue.locked` | string (redacted) | ‹redacted› |
| 45 | `payload.issue.assignees` | string (redacted) | ‹redacted› |
| 46 | `payload.issue.milestone` | string (redacted) | ‹redacted› |
| 47 | `payload.issue.comments` | string (redacted) | ‹redacted› |
| 48 | `payload.issue.created_at` | string (redacted) | ‹redacted› |
| 49 | `payload.issue.updated_at` | string (redacted) | ‹redacted› |
| 50 | `payload.issue.closed_at` | string (redacted) | ‹redacted› |
| 51 | `payload.issue.assignee` | string (redacted) | ‹redacted› |
| 52 | `payload.issue.active_lock_reason` | string (redacted) | ‹redacted› |
| 53 | `payload.issue.draft` | string (redacted) | ‹redacted› |
| 54 | `payload.issue.pull_request.url` | string (redacted) | ‹redacted› |
| 55 | `payload.issue.pull_request.html_url` | string (redacted) | ‹redacted› |
| 56 | `payload.issue.pull_request.diff_url` | string (redacted) | ‹redacted› |
| 57 | `payload.issue.pull_request.patch_url` | string (redacted) | ‹redacted› |
| 58 | `payload.issue.pull_request.merged_at` | string (redacted) | ‹redacted› |
| 59 | `payload.issue.body` | string (redacted) | ‹redacted› |
| 60 | `payload.issue.reactions.url` | string (redacted) | ‹redacted› |
| 61 | `payload.issue.reactions.total_count` | string (redacted) | ‹redacted› |
| 62 | `payload.issue.reactions.+1` | string (redacted) | ‹redacted› |
| 63 | `payload.issue.reactions.-1` | string (redacted) | ‹redacted› |
| 64 | `payload.issue.reactions.laugh` | string (redacted) | ‹redacted› |
| 65 | `payload.issue.reactions.hooray` | string (redacted) | ‹redacted› |
| 66 | `payload.issue.reactions.confused` | string (redacted) | ‹redacted› |
| 67 | `payload.issue.reactions.heart` | string (redacted) | ‹redacted› |
| 68 | `payload.issue.reactions.rocket` | string (redacted) | ‹redacted› |
| 69 | `payload.issue.reactions.eyes` | string (redacted) | ‹redacted› |
| 70 | `payload.issue.timeline_url` | string (redacted) | ‹redacted› |
| 71 | `payload.issue.performed_via_github_app.id` | string (redacted) | ‹redacted› |
| 72 | `payload.issue.performed_via_github_app.client_id` | string (redacted) | ‹redacted› |
| 73 | `payload.issue.performed_via_github_app.slug` | string (redacted) | ‹redacted› |
| 74 | `payload.issue.performed_via_github_app.node_id` | string (redacted) | ‹redacted› |
| 75 | `payload.issue.performed_via_github_app.owner.login` | string (redacted) | ‹redacted› |
| 76 | `payload.issue.performed_via_github_app.owner.id` | string (redacted) | ‹redacted› |
| 77 | `payload.issue.performed_via_github_app.owner.node_id` | string (redacted) | ‹redacted› |
| 78 | `payload.issue.performed_via_github_app.owner.avatar_url` | string (redacted) | ‹redacted› |
| 79 | `payload.issue.performed_via_github_app.owner.gravatar_id` | string (redacted) | ‹redacted› |
| 80 | `payload.issue.performed_via_github_app.owner.url` | string (redacted) | ‹redacted› |
| 81 | `payload.issue.performed_via_github_app.owner.html_url` | string (redacted) | ‹redacted› |
| 82 | `payload.issue.performed_via_github_app.owner.followers_url` | string (redacted) | ‹redacted› |
| 83 | `payload.issue.performed_via_github_app.owner.following_url` | string (redacted) | ‹redacted› |
| 84 | `payload.issue.performed_via_github_app.owner.gists_url` | string (redacted) | ‹redacted› |
| 85 | `payload.issue.performed_via_github_app.owner.starred_url` | string (redacted) | ‹redacted› |
| 86 | `payload.issue.performed_via_github_app.owner.subscriptions_url` | string (redacted) | ‹redacted› |
| 87 | `payload.issue.performed_via_github_app.owner.organizations_url` | string (redacted) | ‹redacted› |
| 88 | `payload.issue.performed_via_github_app.owner.repos_url` | string (redacted) | ‹redacted› |
| 89 | `payload.issue.performed_via_github_app.owner.events_url` | string (redacted) | ‹redacted› |
| 90 | `payload.issue.performed_via_github_app.owner.received_events_url` | string (redacted) | ‹redacted› |
| 91 | `payload.issue.performed_via_github_app.owner.type` | string (redacted) | ‹redacted› |
| 92 | `payload.issue.performed_via_github_app.owner.user_view_type` | string (redacted) | ‹redacted› |
| 93 | `payload.issue.performed_via_github_app.owner.site_admin` | string (redacted) | ‹redacted› |
| 94 | `payload.issue.performed_via_github_app.name` | string (redacted) | ‹redacted› |
| 95 | `payload.issue.performed_via_github_app.description` | string (redacted) | ‹redacted› |
| 96 | `payload.issue.performed_via_github_app.external_url` | string (redacted) | ‹redacted› |
| 97 | `payload.issue.performed_via_github_app.html_url` | string (redacted) | ‹redacted› |
| 98 | `payload.issue.performed_via_github_app.created_at` | string (redacted) | ‹redacted› |
| 99 | `payload.issue.performed_via_github_app.updated_at` | string (redacted) | ‹redacted› |
| 100 | `payload.issue.performed_via_github_app.permissions.actions` | string (redacted) | ‹redacted› |
| 101 | `payload.issue.performed_via_github_app.permissions.checks` | string (redacted) | ‹redacted› |
| 102 | `payload.issue.performed_via_github_app.permissions.contents` | string (redacted) | ‹redacted› |
| 103 | `payload.issue.performed_via_github_app.permissions.emails` | string (redacted) | ‹redacted› |
| 104 | `payload.issue.performed_via_github_app.permissions.issues` | string (redacted) | ‹redacted› |
| 105 | `payload.issue.performed_via_github_app.permissions.metadata` | string (redacted) | ‹redacted› |
| 106 | `payload.issue.performed_via_github_app.permissions.pull_requests` | string (redacted) | ‹redacted› |
| 107 | `payload.issue.performed_via_github_app.permissions.statuses` | string (redacted) | ‹redacted› |
| 108 | `payload.issue.performed_via_github_app.permissions.workflows` | string (redacted) | ‹redacted› |
| 109 | `payload.issue.performed_via_github_app.events` | string (redacted) | ‹redacted› |
| 110 | `payload.issue.state_reason` | string (redacted) | ‹redacted› |
| 111 | `payload.comment.url` | string (redacted) | ‹redacted› |
| 112 | `payload.comment.html_url` | string (redacted) | ‹redacted› |
| 113 | `payload.comment.issue_url` | string (redacted) | ‹redacted› |
| 114 | `payload.comment.id` | string (redacted) | ‹redacted› |
| 115 | `payload.comment.node_id` | string (redacted) | ‹redacted› |
| 116 | `payload.comment.user.login` | string (redacted) | ‹redacted› |
| 117 | `payload.comment.user.id` | string (redacted) | ‹redacted› |
| 118 | `payload.comment.user.node_id` | string (redacted) | ‹redacted› |
| 119 | `payload.comment.user.avatar_url` | string (redacted) | ‹redacted› |
| 120 | `payload.comment.user.gravatar_id` | string (redacted) | ‹redacted› |
| 121 | `payload.comment.user.url` | string (redacted) | ‹redacted› |
| 122 | `payload.comment.user.html_url` | string (redacted) | ‹redacted› |
| 123 | `payload.comment.user.followers_url` | string (redacted) | ‹redacted› |
| 124 | `payload.comment.user.following_url` | string (redacted) | ‹redacted› |
| 125 | `payload.comment.user.gists_url` | string (redacted) | ‹redacted› |
| 126 | `payload.comment.user.starred_url` | string (redacted) | ‹redacted› |
| 127 | `payload.comment.user.subscriptions_url` | string (redacted) | ‹redacted› |
| 128 | `payload.comment.user.organizations_url` | string (redacted) | ‹redacted› |
| 129 | `payload.comment.user.repos_url` | string (redacted) | ‹redacted› |
| 130 | `payload.comment.user.events_url` | string (redacted) | ‹redacted› |
| 131 | `payload.comment.user.received_events_url` | string (redacted) | ‹redacted› |
| 132 | `payload.comment.user.type` | string (redacted) | ‹redacted› |
| 133 | `payload.comment.user.user_view_type` | string (redacted) | ‹redacted› |
| 134 | `payload.comment.user.site_admin` | string (redacted) | ‹redacted› |
| 135 | `payload.comment.created_at` | string (redacted) | ‹redacted› |
| 136 | `payload.comment.updated_at` | string (redacted) | ‹redacted› |
| 137 | `payload.comment.body` | string (redacted) | ‹redacted› |
| 138 | `payload.comment.reactions.url` | string (redacted) | ‹redacted› |
| 139 | `payload.comment.reactions.total_count` | string (redacted) | ‹redacted› |
| 140 | `payload.comment.reactions.+1` | string (redacted) | ‹redacted› |
| 141 | `payload.comment.reactions.-1` | string (redacted) | ‹redacted› |
| 142 | `payload.comment.reactions.laugh` | string (redacted) | ‹redacted› |
| 143 | `payload.comment.reactions.hooray` | string (redacted) | ‹redacted› |
| 144 | `payload.comment.reactions.confused` | string (redacted) | ‹redacted› |
| 145 | `payload.comment.reactions.heart` | string (redacted) | ‹redacted› |
| 146 | `payload.comment.reactions.rocket` | string (redacted) | ‹redacted› |
| 147 | `payload.comment.reactions.eyes` | string (redacted) | ‹redacted› |
| 148 | `payload.comment.performed_via_github_app.id` | string (redacted) | ‹redacted› |
| 149 | `payload.comment.performed_via_github_app.client_id` | string (redacted) | ‹redacted› |
| 150 | `payload.comment.performed_via_github_app.slug` | string (redacted) | ‹redacted› |
| 151 | `payload.comment.performed_via_github_app.node_id` | string (redacted) | ‹redacted› |
| 152 | `payload.comment.performed_via_github_app.owner.login` | string (redacted) | ‹redacted› |
| 153 | `payload.comment.performed_via_github_app.owner.id` | string (redacted) | ‹redacted› |
| 154 | `payload.comment.performed_via_github_app.owner.node_id` | string (redacted) | ‹redacted› |
| 155 | `payload.comment.performed_via_github_app.owner.avatar_url` | string (redacted) | ‹redacted› |
| 156 | `payload.comment.performed_via_github_app.owner.gravatar_id` | string (redacted) | ‹redacted› |
| 157 | `payload.comment.performed_via_github_app.owner.url` | string (redacted) | ‹redacted› |
| 158 | `payload.comment.performed_via_github_app.owner.html_url` | string (redacted) | ‹redacted› |
| 159 | `payload.comment.performed_via_github_app.owner.followers_url` | string (redacted) | ‹redacted› |
| 160 | `payload.comment.performed_via_github_app.owner.following_url` | string (redacted) | ‹redacted› |
| 161 | `payload.comment.performed_via_github_app.owner.gists_url` | string (redacted) | ‹redacted› |
| 162 | `payload.comment.performed_via_github_app.owner.starred_url` | string (redacted) | ‹redacted› |
| 163 | `payload.comment.performed_via_github_app.owner.subscriptions_url` | string (redacted) | ‹redacted› |
| 164 | `payload.comment.performed_via_github_app.owner.organizations_url` | string (redacted) | ‹redacted› |
| 165 | `payload.comment.performed_via_github_app.owner.repos_url` | string (redacted) | ‹redacted› |
| 166 | `payload.comment.performed_via_github_app.owner.events_url` | string (redacted) | ‹redacted› |
| 167 | `payload.comment.performed_via_github_app.owner.received_events_url` | string (redacted) | ‹redacted› |
| 168 | `payload.comment.performed_via_github_app.owner.type` | string (redacted) | ‹redacted› |
| 169 | `payload.comment.performed_via_github_app.owner.user_view_type` | string (redacted) | ‹redacted› |
| 170 | `payload.comment.performed_via_github_app.owner.site_admin` | string (redacted) | ‹redacted› |
| 171 | `payload.comment.performed_via_github_app.name` | string (redacted) | ‹redacted› |
| 172 | `payload.comment.performed_via_github_app.description` | string (redacted) | ‹redacted› |
| 173 | `payload.comment.performed_via_github_app.external_url` | string (redacted) | ‹redacted› |
| 174 | `payload.comment.performed_via_github_app.html_url` | string (redacted) | ‹redacted› |
| 175 | `payload.comment.performed_via_github_app.created_at` | string (redacted) | ‹redacted› |
| 176 | `payload.comment.performed_via_github_app.updated_at` | string (redacted) | ‹redacted› |
| 177 | `payload.comment.performed_via_github_app.permissions.actions` | string (redacted) | ‹redacted› |
| 178 | `payload.comment.performed_via_github_app.permissions.administration` | string (redacted) | ‹redacted› |
| 179 | `payload.comment.performed_via_github_app.permissions.artifact_metadata` | string (redacted) | ‹redacted› |
| 180 | `payload.comment.performed_via_github_app.permissions.attestations` | string (redacted) | ‹redacted› |
| 181 | `payload.comment.performed_via_github_app.permissions.checks` | string (redacted) | ‹redacted› |
| 182 | `payload.comment.performed_via_github_app.permissions.code_quality` | string (redacted) | ‹redacted› |
| 183 | `payload.comment.performed_via_github_app.permissions.contents` | string (redacted) | ‹redacted› |
| 184 | `payload.comment.performed_via_github_app.permissions.copilot_requests` | string (redacted) | ‹redacted› |
| 185 | `payload.comment.performed_via_github_app.permissions.deployments` | string (redacted) | ‹redacted› |
| 186 | `payload.comment.performed_via_github_app.permissions.discussions` | string (redacted) | ‹redacted› |
| 187 | `payload.comment.performed_via_github_app.permissions.drives` | string (redacted) | ‹redacted› |
| 188 | `payload.comment.performed_via_github_app.permissions.issues` | string (redacted) | ‹redacted› |
| 189 | `payload.comment.performed_via_github_app.permissions.merge_queues` | string (redacted) | ‹redacted› |
| 190 | `payload.comment.performed_via_github_app.permissions.metadata` | string (redacted) | ‹redacted› |
| 191 | `payload.comment.performed_via_github_app.permissions.models` | string (redacted) | ‹redacted› |
| 192 | `payload.comment.performed_via_github_app.permissions.packages` | string (redacted) | ‹redacted› |
| 193 | `payload.comment.performed_via_github_app.permissions.pages` | string (redacted) | ‹redacted› |
| 194 | `payload.comment.performed_via_github_app.permissions.pull_requests` | string (redacted) | ‹redacted› |
| 195 | `payload.comment.performed_via_github_app.permissions.repository_hooks` | string (redacted) | ‹redacted› |
| 196 | `payload.comment.performed_via_github_app.permissions.repository_projects` | string (redacted) | ‹redacted› |
| 197 | `payload.comment.performed_via_github_app.permissions.security_events` | string (redacted) | ‹redacted› |
| 198 | `payload.comment.performed_via_github_app.permissions.statuses` | string (redacted) | ‹redacted› |
| 199 | `payload.comment.performed_via_github_app.permissions.vulnerability_alerts` | string (redacted) | ‹redacted› |
| 200 | `payload.comment.performed_via_github_app.events` | string (redacted) | ‹redacted› |
| 201 | `payload.comment.minimized` | string (redacted) | ‹redacted› |
| 202 | `public` | boolean | true |
| 203 | `created_at` | string (date/time) | 2026-10-12T23:00:06Z |

</details>

<a id="s-pskreporter"></a>
### 16. PSK Reporter amateur-radio reception reports

- **Verdict:** Meets both — average 256.46 events/s, median 13.0 attributes per event.
- **Delivery:** live · MQTT (TCP 1883)
- **Endpoint:** `mqtt://mqtt.pskreporter.info:1883`
- **Request:** `SUBSCRIBE pskr/filter/v2/#`
- **Access:** None
- **Documentation:** https://www.mqtt.pskreporter.info/ (HTTP 200)
- **Terms / licence:** https://www.mqtt.pskreporter.info/ (HTTP 200) — “A real-time MQTT distribution of every spot reported to pskreporter”
- **Measurement note (latest representative round):** example topic: pskr/filter/v2/160m/FT8/AI4UC/K3LR.D/FM19/EN91/291/291
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 265.20 | 15,912 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T02:11 | ok | 299.52 | 17,971 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T03:23 | ok | 211.97 | 12,718 | 60 | 13.0 | 13 | 13 |
| 2026-10-13T04:23 | ok | 249.17 | 14,950 | 60 | 13.0 | 13 | 13 |

<details><summary>Sample event — 13 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `sq` | integer | 73663134648 |
| 2 | `f` | integer | 1840200 |
| 3 | `md` | string | FT8 |
| 4 | `rp` | integer | 34 |
| 5 | `t` | integer | 1791857355 |
| 6 | `t_tx` | integer | 1791857340 |
| 7 | `sc` | string (redacted) | ‹redacted› |
| 8 | `sl` | string (redacted) | ‹redacted› |
| 9 | `rc` | string (redacted) | ‹redacted› |
| 10 | `rl` | string (redacted) | ‹redacted› |
| 11 | `sa` | integer | 291 |
| 12 | `ra` | integer | 291 |
| 13 | `b` | string | 160m |

</details>

<a id="s-sensorcomm"></a>
### 17. Sensor.Community citizen air-quality sensors

- **Verdict:** Meets both — average 58.79 events/s, median 17.0 attributes per event.
- **Delivery:** batch · JSON file over HTTPS (last 5 minutes)
- **Endpoint:** `https://data.sensor.community/static/v2/data.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/opendata-stuttgart/meta/wiki/EN-APIs (HTTP 200)
- **Terms / licence:** https://sensor.community/en/ (HTTP 200) — “DB Contents License [the site footer link 'DB Contents License' points to https://opendatacommons.org/licenses/dbcl/1-0/ (Open Data Commons DbCL v1.0)]”
- **Measurement note (latest representative round):** file = last 5 minutes of all sensors; sensordatavalues expanded per value_type
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects yes
- **In the Bytewax list:** yes (sensor.community) · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 58.66 | 17,599 | 300 | 17.0 | 25 | 33 |
| 2026-10-13T02:11 | ok | 58.68 | 17,603 | 300 | 17.0 | 25 | 33 |
| 2026-10-13T03:23 | ok | 58.87 | 17,661 | 300 | 17.0 | 25 | 33 |
| 2026-10-13T04:23 | ok | 58.94 | 17,681 | 300 | 17.0 | 25 | 33 |

<details><summary>Sample event — 25 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | integer | 31016224013 |
| 2 | `sampling_rate` | null | null |
| 3 | `timestamp` | string (date/time) | 2026-10-13 02:08:11 |
| 4 | `location.id` | integer | 980 |
| 5 | `location.latitude` | string (numeric) | 43.794 |
| 6 | `location.longitude` | string (numeric) | 11.212 |
| 7 | `location.altitude` | string (numeric) | 38.1 |
| 8 | `location.country` | string | IT |
| 9 | `location.exact_location` | integer | 0 |
| 10 | `location.indoor` | integer | 0 |
| 11 | `sensor.id` | integer | 1959 |
| 12 | `sensor.pin` | string (numeric) | 1 |
| 13 | `sensor.sensor_type.id` | integer | 14 |
| 14 | `sensor.sensor_type.name` | string | SDS011 |
| 15 | `sensor.sensor_type.manufacturer` | string | Nova Fitness |
| 16 | `value.N05` | string (numeric) | 15.17 |
| 17 | `value.N1` | string (numeric) | 17.24 |
| 18 | `value.N10` | string (numeric) | 17.28 |
| 19 | `value.N25` | string (numeric) | 17.27 |
| 20 | `value.N4` | string (numeric) | 17.28 |
| 21 | `value.P0` | string (numeric) | 2.16 |
| 22 | `value.P1` | string (numeric) | 2.29 |
| 23 | `value.P2` | string (numeric) | 2.29 |
| 24 | `value.P4` | string (numeric) | 2.29 |
| 25 | `value.TS` | string (numeric) | 0.46 |

</details>

<a id="s-crossref"></a>
### 18. Crossref scholarly metadata (works indexed per day)

- **Verdict:** Meets both — average 6.47 events/s, median 42.2 attributes per event.
- **Delivery:** batch · REST JSON (cursor paging by index date)
- **Endpoint:** `https://api.crossref.org/works?filter=from-index-date:<d>,until-index-date:<d>`
- **Request:** `GET with mailto=`
- **Access:** None
- **Documentation:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/ (HTTP 200)
- **Terms / licence:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/ (HTTP 200) — “No sign-up is required to use the REST API, and almost none of the metadata is subject to copyright, and you may use it for any purpose”
- **Measurement note (latest representative round):** 2026-10-12: 561170 records (re)indexed, of which 39951 newly created (0.462/s)
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 6.50 | 561,204 | 86,400 | 43.0 | 45 | 60 |
| 2026-10-13T02:11 | ok | 6.50 | 561,170 | 86,400 | 45.0 | 48 | 59 |
| 2026-10-13T03:23 | ok | 6.47 | 558,644 | 86,400 | 41.5 | 47 | 59 |
| 2026-10-13T04:23 | ok | 6.44 | 556,427 | 86,400 | 41.5 | 47 | 59 |

<details><summary>Sample event — 48 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `indexed.date-parts` | list (serialised) | [[2026, 10, 12]] |
| 2 | `indexed.date-time` | string (date/time) | 2026-10-12T00:11:22Z |
| 3 | `indexed.timestamp` | integer | 1791763882784 |
| 4 | `indexed.version` | string | 4.3.4 |
| 5 | `reference-count` | integer | 55 |
| 6 | `publisher` | string | The Royal Society |
| 7 | `issue` | string (numeric) | 1955 |
| 8 | `license` | string | [{'start': {'date-parts': [[2021, 7, 21]], 'date-time': '2021-07-21T00:00:00Z', 'timestam… |
| 9 | `funder` | string | [{'name': 'Newkirk Center for Science and Society'}, {'name': 'UCI OCEANS Graduate Resear… |
| 10 | `content-domain.domain` | list (serialised) | ['royalsocietypublishing.org'] |
| 11 | `content-domain.crossmark-restriction` | boolean | true |
| 12 | `short-container-title` | list (serialised) | ['Proc. R. Soc. B.'] |
| 13 | `published-print.date-parts` | list (serialised) | [[2021, 7, 28]] |
| 14 | `abstract` | string | <jats:p>Looking to nature for inspiration has led to many diverse technological advances.… |
| 15 | `DOI` | string | 10.1098/rspb.2021.1359 |
| 16 | `type` | string | journal-article |
| 17 | `created.date-parts` | list (serialised) | [[2021, 7, 21]] |
| 18 | `created.date-time` | string (date/time) | 2021-07-21T07:06:19Z |
| 19 | `created.timestamp` | integer | 1626851179000 |
| 20 | `page` | string (numeric) | 20211359 |
| 21 | `update-policy` | string | https://doi.org/10.1098/crossmark-policy |
| 22 | `source` | string | Crossref |
| 23 | `is-referenced-by-count` | integer | 28 |
| 24 | `title` | list (serialised) | ['Shark spiral intestines may operate as Tesla valves'] |
| 25 | `prefix` | string (numeric) | 10.1098 |
| 26 | `volume` | string (numeric) | 288 |
| 27 | `author` | string (redacted) | ‹redacted› |
| 28 | `member` | string (numeric) | 175 |
| 29 | `published-online.date-parts` | list (serialised) | [[2021, 7, 21]] |
| 30 | `reference` | string | [{'key': 'e_1_3_6_2_2', 'doi-asserted-by': 'publisher', 'DOI': '10.1126/sciadv.aat9533'},… |
| 31 | `container-title` | list (serialised) | ['Proceedings of the Royal Society B: Biological Sciences'] |
| 32 | `language` | string | en |
| 33 | `link` | string | [{'URL': 'https://royalsocietypublishing.org/doi/pdf/10.1098/rspb.2021.1359', 'content-ty… |
| 34 | `deposited.date-parts` | list (serialised) | [[2021, 7, 21]] |
| 35 | `deposited.date-time` | string (date/time) | 2021-07-21T07:08:45Z |
| 36 | `deposited.timestamp` | integer | 1626851325000 |
| 37 | `score` | number | 0.0 |
| 38 | `resource.primary.URL` | string | https://royalsocietypublishing.org/doi/10.1098/rspb.2021.1359 |
| 39 | `issued.date-parts` | list (serialised) | [[2021, 7, 21]] |
| 40 | `references-count` | integer | 55 |
| 41 | `journal-issue.issue` | string (numeric) | 1955 |
| 42 | `journal-issue.published-print.date-parts` | list (serialised) | [[2021, 7, 28]] |
| 43 | `alternative-id` | list (serialised) | ['10.1098/rspb.2021.1359'] |
| 44 | `URL` | string | https://doi.org/10.1098/rspb.2021.1359 |
| 45 | `ISSN` | list (serialised) | ['0962-8452', '1471-2954'] |
| 46 | `issn-type` | list (serialised) | [{'value': '0962-8452', 'type': 'print'}, {'value': '1471-2954', 'type': 'electronic'}] |
| 47 | `published.date-parts` | list (serialised) | [[2021, 7, 21]] |
| 48 | `assertion` | string | [{'value': '2021-06-14', 'order': 0, 'name': 'received', 'label': 'Received', 'group': {'… |

</details>

<a id="s-seedlink"></a>
### 19. EarthScope (IRIS) SeedLink real-time seismic waveforms

- **Verdict:** Meets both — average 2.43 events/s, median 12.0 attributes per event.
- **Delivery:** live · SeedLink 3/4 over TCP (miniSEED records)
- **Endpoint:** `tcp://rtserve.iris.washington.edu:18000`
- **Request:** `STATION <sta> <net> / SELECT BHZ / DATA ... END`
- **Access:** None
- **Documentation:** https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ (HTTP 200)
- **Terms / licence:** https://ds.iris.edu/ds/nodes/dmc/services/seedlink/ (HTTP 200) — “a publicly accessible SeedLink server on the following host and port: host port rtserve”
- **Measurement note (latest representative round):** 12 IU stations, channel BHZ; rate scales with stations selected (each 512-byte miniSEED record carries ~400 samples)
- **Data shape (by attribute name):** geographic position yes · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.45 | 147 | 60 | 12.0 | 12 | 12 |
| 2026-10-13T02:11 | ok | 2.32 | 139 | 60 | 12.0 | 12 | 12 |
| 2026-10-13T03:23 | ok | 2.48 | 149 | 60 | 12.0 | 12 | 12 |
| 2026-10-13T04:23 | ok | 2.45 | 147 | 60 | 12.0 | 12 | 12 |

<details><summary>Sample event — 12 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `seq` | string | 51E631 |
| 2 | `station` | string | MAJO |
| 3 | `location` | string (numeric) | 00 |
| 4 | `channel` | string | BHZ |
| 5 | `network` | string | IU |
| 6 | `year` | integer | 2026 |
| 7 | `doy` | integer | 286 |
| 8 | `hour` | integer | 2 |
| 9 | `minute` | integer | 10 |
| 10 | `second` | integer | 8 |
| 11 | `nsamples` | integer | 412 |
| 12 | `rate_factor` | integer | 40 |

</details>

<a id="s-usgs_water"></a>
### 20. USGS Water Services instantaneous values (river gauges)

- **Verdict:** Meets both — average 1.83 events/s, median 26.0 attributes per event.
- **Delivery:** batch · REST JSON (WaterML-JSON)
- **Endpoint:** `https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H`
- **Request:** `GET per state`
- **Access:** None
- **Documentation:** https://waterservices.usgs.gov/ (HTTP 200)
- **Terms / licence:** https://waterservices.usgs.gov/ (HTTP 200) — “decommissioned February 22nd, 2027 WaterServices will be permanently shut down on February 22nd, 2027”
- **Measurement note (latest representative round):** Texas only: 2677 active series; nationwide is ~50x larger. Legacy service retires 2027-02-22
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects yes
- **In the Bytewax list:** yes (usgs.gov) · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.79 | 6,433 | 3,600 | 26.0 | 26 | 26 |
| 2026-10-13T02:11 | ok | 1.85 | 6,648 | 3,600 | 26.0 | 26 | 26 |
| 2026-10-13T03:23 | ok | 1.83 | 6,592 | 3,600 | 26.0 | 26 | 26 |
| 2026-10-13T04:23 | ok | 1.87 | 6,724 | 3,600 | 26.0 | 26 | 26 |

<details><summary>Sample event — 26 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `siteName` | string | Canadian Rv nr Amarillo, TX |
| 2 | `siteCode` | list (serialised) | [{'value': '07227500', 'network': 'NWIS', 'agencyCode': 'USGS'}] |
| 3 | `timeZoneInfo.defaultTimeZone.zoneOffset` | string | -06:00 |
| 4 | `timeZoneInfo.defaultTimeZone.zoneAbbreviation` | string | CST |
| 5 | `timeZoneInfo.daylightSavingsTimeZone.zoneOffset` | string | -05:00 |
| 6 | `timeZoneInfo.daylightSavingsTimeZone.zoneAbbreviation` | string | CDT |
| 7 | `timeZoneInfo.siteUsesDaylightSavingsTime` | boolean | true |
| 8 | `geoLocation.geogLocation.srs` | string | EPSG:4326 |
| 9 | `geoLocation.geogLocation.latitude` | number | 35.4703261 |
| 10 | `geoLocation.geogLocation.longitude` | number | -101.879628 |
| 11 | `geoLocation.localSiteXY` | list (serialised) | [] |
| 12 | `note` | list (serialised) | [] |
| 13 | `siteType` | list (serialised) | [] |
| 14 | `siteProperty` | list (serialised) | [{'value': 'ST', 'name': 'siteTypeCd'}, {'value': '11090105', 'name': 'hucCd'}, {'value':… |
| 15 | `variableCode` | list (serialised) | [{'value': '00010', 'network': 'NWIS', 'vocabulary': 'NWIS:UnitValues', 'variableID': 458… |
| 16 | `variableName` | string | Temperature, water, &#176;C |
| 17 | `variableDescription` | string | Temperature, water, degrees Celsius |
| 18 | `valueType` | string | Derived Value |
| 19 | `unit.unitCode` | string | deg C |
| 20 | `options.option` | list (serialised) | [{'name': 'Statistic', 'optionCode': '00000'}] |
| 21 | `noDataValue` | number | -999999.0 |
| 22 | `variableProperty` | list (serialised) | [] |
| 23 | `oid` | string (numeric) | 45807042 |
| 24 | `value` | string (numeric) | -999999 |
| 25 | `qualifiers` | list (serialised) | ['P', '***'] |
| 26 | `dateTime` | string (date/time) | 2026-10-12T20:30:00.000-05:00 |

</details>

<a id="s-polymarket"></a>
### 21. Polymarket CLOB market channel (prediction-market prices)

- **Verdict:** Meets both — average 589.34 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws-subscriptions-clob.polymarket.com/ws/market`
- **Request:** `{"assets_ids":[...],"type":"market"} (ids from https://gamma-api.polymarket.com/markets)`
- **Access:** None
- **Documentation:** https://docs.polymarket.com/developers/CLOB/websocket/market-channel (HTTP 200)
- **Terms / licence:** https://docs.polymarket.com/developers/CLOB/websocket/market-channel (HTTP 200) — “public market data your application depends on current without repeated polling”
- **Measurement note (latest representative round):** top 25 markets by 24h volume (50 outcome tokens)
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 408.37 | 24,502 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 293.63 | 17,618 | 60 | 10.0 | 10 | 12 |
| 2026-10-13T03:23 | ok | 1,343.25 | 80,595 | 60 | 10.0 | 10 | 12 |
| 2026-10-13T04:23 | ok | 312.12 | 18,727 | 60 | 10.0 | 10 | 12 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `market` | string | 0xdce84960dce38aa4a5800a5eba7c9ac34d2ce49ba9d44c42572c472d468af264 |
| 2 | `timestamp` | string (numeric) | 1791857418277 |
| 3 | `event_type` | string | price_change |
| 4 | `asset_id` | string (numeric) | 88403451835230950222119400360490338078378790763472355557584611572247419676051 |
| 5 | `price` | string (numeric) | 0.983 |
| 6 | `size` | string (numeric) | 236.4 |
| 7 | `side` | string | BUY |
| 8 | `hash` | string | d6ba9956e422280b97a98e5e7eb4dea8e70eadfd |
| 9 | `best_bid` | string (numeric) | 0.983 |
| 10 | `best_ask` | string (numeric) | 0.984 |

</details>

<a id="s-base_logs"></a>
### 22. Base (L2) contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 336.87 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://base-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 123.93 | 7,436 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 380.93 | 22,856 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 391.12 | 23,467 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 451.50 | 27,090 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `address` | string | 0x4200000000000000000000000000000000000010 |
| 2 | `blockHash` | string | 0x47598f2ac8347851c0764d7bb31c55043f9077bf078dc701a53c9f9098d0660b |
| 3 | `blockNumber` | string | 0x3219b14 |
| 4 | `blockTimestamp` | string | 0x6acd930b |
| 5 | `data` | string | 0x000000000000000000000000de80257eeb34cb3695386f13bdd76e2502d9d0c600000000000000000000000… |
| 6 | `logIndex` | string | 0x0 |
| 7 | `removed` | boolean | false |
| 8 | `topics` | string | ['0xb0444523268717a02698be47d0803aa7468c00acbed2f8bd93a0459cde61dd89', '0x000000000000000… |
| 9 | `transactionHash` | string | 0x676aae0559f3a52d4103fcbc09de32ea24145386300aa7e3be8aa18c451907b8 |
| 10 | `transactionIndex` | string | 0x1 |

</details>

<a id="s-polygon_logs"></a>
### 23. Polygon PoS contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 333.30 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://polygon-bor-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 151.87 | 9,112 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 288.13 | 17,288 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 417.88 | 25,073 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 475.30 | 28,518 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `address` | string | 0x0000000000000000000000000000000000001010 |
| 2 | `blockHash` | string | 0xd35b34e15c0ccbe6489f74bdde1dcffe4b61fc73ceeca63dcbd5f9e3df075c5f |
| 3 | `blockNumber` | string | 0x5b03800 |
| 4 | `blockTimestamp` | string | 0x6acd930a |
| 5 | `data` | string | 0x000000000000000000000000000000000000000000000001e12adbee837008ce00000000000000000000000… |
| 6 | `logIndex` | string | 0x0 |
| 7 | `removed` | boolean | false |
| 8 | `topics` | string | ['0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4', '0x000000000000000… |
| 9 | `transactionHash` | string | 0x518c0ed5373ad72b8f3340a4aa65b687b92250fb27db78b3b458a9d08935a404 |
| 10 | `transactionIndex` | string | 0x0 |

</details>

<a id="s-bsc_logs"></a>
### 24. BNB Smart Chain contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 262.45 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://bsc-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 197.15 | 11,829 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 371.75 | 22,305 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T04:23 | ok | 480.90 | 28,854 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `address` | string | 0x55d398326f99059ff775485246999027b3197955 |
| 2 | `blockHash` | string | 0xd059242f460d65d95e97de0cc6a55964fe6d90e934d8f0c2e3ecce0da78b4284 |
| 3 | `blockNumber` | string | 0x796c14d |
| 4 | `blockTimestamp` | string | 0x6acd9309 |
| 5 | `data` | string | 0x00000000000000000000000000000000000000000000000051e102bd8ece0000 |
| 6 | `logIndex` | string | 0x0 |
| 7 | `removed` | boolean | false |
| 8 | `topics` | string | ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', '0x000000000000000… |
| 9 | `transactionHash` | string | 0xd9840c0eb24a78fae52754f9584d6ff4c1f2ed4310eb27081494e9662803d222 |
| 10 | `transactionIndex` | string | 0x1 |

</details>

<a id="s-eth_logs"></a>
### 25. Ethereum mainnet contract event logs (PublicNode RPC)

- **Verdict:** Meets both — average 82.21 events/s, median 10.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (eth_subscribe)
- **Endpoint:** `wss://ethereum-rpc.publicnode.com`
- **Request:** `{"method":"eth_subscribe","params":["logs",{}]}`
- **Access:** None
- **Documentation:** https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub (HTTP 200)
- **Terms / licence:** https://www.publicnode.com/ (HTTP 200) — “oints Solana Gun NEW Node Snapshots Seed Service Contact RPC Endpoints Fastest, free-est, and privacy first RPC endpoints for 78 blockchains”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 71.33 | 4,280 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 93.43 | 5,606 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 84.62 | 5,077 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 79.45 | 4,767 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `address` | string | 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 |
| 2 | `blockHash` | string | 0xcb0c119dd30a67825166b8e6d442c455f75bbb5ed5beb99d7a868411e4b51c0a |
| 3 | `blockNumber` | string | 0x18f7b8d |
| 4 | `blockTimestamp` | string | 0x6acd930f |
| 5 | `data` | string | 0x0000000000000000000000000000000000000000000000000000000000006d76 |
| 6 | `logIndex` | string | 0x0 |
| 7 | `removed` | boolean | false |
| 8 | `topics` | string | ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', '0x000000000000000… |
| 9 | `transactionHash` | string | 0x4e40b68e6b783d608ec29d2332cdb2f2a18316266e887968f0323ee770c77c1c |
| 10 | `transactionIndex` | string | 0x0 |

</details>

<a id="s-bitso"></a>
### 26. Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)

- **Verdict:** Meets both — average 35.04 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.bitso.com`
- **Request:** `{"action":"subscribe","book":"btc_mxn","type":"trades"|"diff-orders"}`
- **Access:** None
- **Documentation:** https://docs.bitso.com/bitso-api/docs (HTTP 200)
- **Terms / licence:** https://docs.bitso.com/bitso-api/docs (HTTP 200) — “s Look Up Orders Cancel an Order List Fees WEBSOCKET API General Trades Channel Diff-Orders Channel Orders Channel Processed-Orders Channel CONVERSIONS Understanding Conversions Request a Conversion Quote Execut”
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 32.93 | 1,976 | 60 | 10.0 | 10 | 14 |
| 2026-10-13T02:11 | ok | 41.92 | 2,515 | 60 | 10.0 | 10 | 14 |
| 2026-10-13T03:23 | ok | 47.38 | 2,843 | 60 | 10.0 | 10 | 14 |
| 2026-10-13T04:23 | ok | 17.93 | 1,076 | 60 | 10.0 | 10 | 14 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `a` | string (numeric) | 0.10111700 |
| 2 | `d` | integer | 1791857417681 |
| 3 | `o` | string | F67a2CIb7lAnkPkU |
| 4 | `r` | string (numeric) | 1474330 |
| 5 | `s` | string | open |
| 6 | `t` | integer | 0 |
| 7 | `v` | string (numeric) | 149079.82661000 |
| 8 | `z` | integer | 0 |
| 9 | `book` | string | btc_mxn |
| 10 | `type` | string | diff-orders |

</details>

<a id="s-okx"></a>
### 27. OKX public tickers

- **Verdict:** Meets both — average 30.98 events/s, median 16.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.okx.com:8443/ws/v5/public`
- **Request:** `{"op":"subscribe","args":[{"channel":"tickers","instId":"BTC-USDT"},...]}`
- **Access:** None
- **Documentation:** https://www.okx.com/docs-v5/en/ (HTTP 200)
- **Terms / licence:** https://www.okx.com/docs-v5/en/ (HTTP 200) — “Public Channel Public structure block trades channel Public block trades channel Block tickers”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 30.27 | 1,816 | 60 | 16.0 | 16 | 16 |
| 2026-10-13T02:11 | ok | 30.75 | 1,845 | 60 | 16.0 | 16 | 16 |
| 2026-10-13T03:23 | ok | 31.42 | 1,885 | 60 | 16.0 | 16 | 16 |
| 2026-10-13T04:23 | ok | 31.47 | 1,888 | 60 | 16.0 | 16 | 16 |

<details><summary>Sample event — 16 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `instType` | string | SPOT |
| 2 | `instId` | string | BTC-USDT |
| 3 | `last` | string (numeric) | 82497.9 |
| 4 | `lastSz` | string (numeric) | 0.00199 |
| 5 | `askPx` | string (numeric) | 82498 |
| 6 | `askSz` | string (numeric) | 0.10114532 |
| 7 | `bidPx` | string (numeric) | 82497.9 |
| 8 | `bidSz` | string (numeric) | 2.4469972 |
| 9 | `open24h` | string (numeric) | 83683.8 |
| 10 | `high24h` | string (numeric) | 84361.6 |
| 11 | `low24h` | string (numeric) | 81032.8 |
| 12 | `sodUtc0` | string (numeric) | 81853.2 |
| 13 | `sodUtc8` | string (numeric) | 82721.2 |
| 14 | `volCcy24h` | string (numeric) | 543406387.883584829 |
| 15 | `vol24h` | string (numeric) | 6548.61768163 |
| 16 | `ts` | string (numeric) | 1791857417963 |

</details>

<a id="s-xrpl"></a>
### 28. XRP Ledger transactions

- **Verdict:** Meets both — average 21.92 events/s, median 20.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://xrplcluster.com/`
- **Request:** `{"command":"subscribe","streams":["transactions"]}`
- **Access:** None
- **Documentation:** https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe (HTTP 200)
- **Terms / licence:** https://xrpl.org/docs/tutorials/public-servers (HTTP 200) — “io/ Full history server cluster with Clio InFTF Mainnet https://xrplcluster”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 23.35 | 1,401 | 60 | 20.0 | 26 | 63 |
| 2026-10-13T02:11 | ok | 17.68 | 1,061 | 60 | 21.0 | 27 | 63 |
| 2026-10-13T03:23 | ok | 26.58 | 1,595 | 60 | 19.0 | 27 | 64 |
| 2026-10-13T04:23 | ok | 20.08 | 1,205 | 60 | 20.0 | 26 | 59 |

<details><summary>Sample event — 27 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `Account` | string | raRBY29mxKf8oADemdUg5618xL6m5RhMLP |
| 2 | `Amount.currency` | string | BRB |
| 3 | `Amount.issuer` | string | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| 4 | `Amount.value` | string | 9999999999999990e79 |
| 5 | `DeliverMax.currency` | string | BRB |
| 6 | `DeliverMax.issuer` | string | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| 7 | `DeliverMax.value` | string | 9999999999999990e79 |
| 8 | `DeliverMin.currency` | string | BRB |
| 9 | `DeliverMin.issuer` | string | rUkuT9TCDTP2oeAPsrCN7XKcHZfdvHvFkG |
| 10 | `DeliverMin.value` | string (numeric) | 955.649949521643 |
| 11 | `Destination` | string | raRBY29mxKf8oADemdUg5618xL6m5RhMLP |
| 12 | `Fee` | string (numeric) | 12 |
| 13 | `Flags` | integer | 196608 |
| 14 | `LastLedgerSequence` | integer | 107618699 |
| 15 | `Paths` | string | [[{'currency': '4249547800000000000000000000000000000000', 'issuer': 'rBitcoiNXev8VoVxV7p… |
| 16 | `SendMax` | string (numeric) | 164181 |
| 17 | `Sequence` | integer | 103803480 |
| 18 | `SigningPubKey` | string | 03616FF3FCA0EDDD6CD99CDB3E9E34644F56A2DEB27111FEB790939246784FBEA0 |
| 19 | `SourceTag` | integer | 3978681839 |
| 20 | `TransactionType` | string | Payment |
| 21 | `TxnSignature` | string | 3045022100FE72A4E5B01ECF48ED8240CB6865E058C3338986D229238F60284402EE10A9A4022043017462B92… |
| 22 | `date` | integer | 845172721 |
| 23 | `hash` | string | 59014F4144026142DFF4CD2DFD573B007094411748EF334EF34C7F383D5C9E0C |
| 24 | `ledger_index` | integer | 107618680 |
| 25 | `validated` | boolean | true |
| 26 | `close_time_iso` | string (date/time) | 2026-10-13T02:12:01Z |
| 27 | `TransactionResult` | string | tesSUCCESS |

</details>

<a id="s-coinbase"></a>
### 29. Coinbase Exchange ticker

- **Verdict:** Meets both — average 10.26 events/s, median 17.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws-feed.exchange.coinbase.com`
- **Request:** `{"type":"subscribe","product_ids":[...],"channels":["ticker"]}`
- **Access:** None
- **Documentation:** https://docs.cdp.coinbase.com/exchange/websocket-feed/overview (HTTP 200)
- **Terms / licence:** https://docs.cdp.coinbase.com/exchange/websocket-feed/overview (HTTP 200) — “ebSocket Overview Copy page Copy page Copy page Copy page The WebSocket feed is publicly available and provides real-time market data updates for orders and trades”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** yes (coinbase.com) · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.48 | 569 | 60 | 17.0 | 17 | 17 |
| 2026-10-13T02:11 | ok | 16.42 | 985 | 60 | 17.0 | 17 | 17 |
| 2026-10-13T03:23 | ok | 8.17 | 490 | 60 | 17.0 | 17 | 17 |
| 2026-10-13T04:23 | ok | 6.97 | 418 | 60 | 17.0 | 17 | 17 |

<details><summary>Sample event — 17 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `type` | string | ticker |
| 2 | `sequence` | integer | 33062849932 |
| 3 | `product_id` | string | SOL-USD |
| 4 | `price` | string (numeric) | 105.42 |
| 5 | `open_24h` | string (numeric) | 111.9 |
| 6 | `volume_24h` | string (numeric) | 1032296.29463029 |
| 7 | `low_24h` | string (numeric) | 101.55 |
| 8 | `high_24h` | string (numeric) | 113.26 |
| 9 | `volume_30d` | string (numeric) | 26310333.07328899 |
| 10 | `best_bid` | string (numeric) | 105.410 |
| 11 | `best_bid_size` | string (numeric) | 30.25986614 |
| 12 | `best_ask` | string (numeric) | 105.420 |
| 13 | `best_ask_size` | string (numeric) | 8.26913607 |
| 14 | `side` | string | buy |
| 15 | `time` | string (date/time) | 2026-10-13T02:10:15.482827Z |
| 16 | `trade_id` | integer | 357552848 |
| 17 | `last_size` | string (numeric) | 0.0368486 |

</details>

<a id="s-deribit"></a>
### 30. Deribit perpetual futures ticker

- **Verdict:** Meets both — average 5.15 events/s, median 24.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket
- **Endpoint:** `wss://www.deribit.com/ws/api/v2`
- **Request:** `public/subscribe ["ticker.BTC-PERPETUAL.100ms", ...]`
- **Access:** None
- **Documentation:** https://docs.deribit.com/ (HTTP 200)
- **Terms / licence:** https://docs.deribit.com/ (HTTP 200) — “agement/private-unsubscribe_all\",\"autogeneratedByOpenApi\":true},{\"title\":\"public/subscribe\",\"description\":\"Subscribe to one or more channels”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.83 | 290 | 60 | 24.0 | 24 | 24 |
| 2026-10-13T02:11 | ok | 5.80 | 348 | 60 | 24.0 | 24 | 24 |
| 2026-10-13T03:23 | ok | 4.97 | 298 | 60 | 24.0 | 24 | 24 |
| 2026-10-13T04:23 | ok | 4.98 | 299 | 60 | 24.0 | 24 | 24 |

<details><summary>Sample event — 24 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `timestamp` | integer | 1791857417771 |
| 2 | `state` | string | open |
| 3 | `stats.high` | number | 2577.15 |
| 4 | `stats.low` | number | 2406.15 |
| 5 | `stats.price_change` | number | -3.0589 |
| 6 | `stats.volume` | number | 71527.956029 |
| 7 | `stats.volume_usd` | number | 179353118.0 |
| 8 | `stats.volume_notional` | number | 179353118.0 |
| 9 | `index_price` | number | 2463.35 |
| 10 | `instrument_name` | string | ETH-PERPETUAL |
| 11 | `last_price` | number | 2464.05 |
| 12 | `settlement_price` | number | 2561.16 |
| 13 | `min_price` | number | 2427.2 |
| 14 | `max_price` | number | 2501.15 |
| 15 | `open_interest` | integer | 243663246 |
| 16 | `mark_price` | number | 2464.18 |
| 17 | `interest_value` | number | 0.7948244270987193 |
| 18 | `current_funding` | number | 8.7e-05 |
| 19 | `estimated_delivery_price` | number | 2463.35 |
| 20 | `funding_8h` | number | 1.9e-05 |
| 21 | `best_ask_price` | number | 2464.2 |
| 22 | `best_bid_price` | number | 2464.15 |
| 23 | `best_ask_amount` | number | 3.0 |
| 24 | `best_bid_amount` | number | 37713.0 |

</details>

<a id="s-bitstamp"></a>
### 31. Bitstamp live trades

- **Verdict:** Meets both — average 1.41 events/s, median 10.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.bitstamp.net`
- **Request:** `{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}`
- **Access:** None
- **Documentation:** https://www.bitstamp.net/websocket/v2/ (HTTP 200)
- **Terms / licence:** https://www.bitstamp.net/websocket/v2/ (HTTP 200) — no matching text found
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.48 | 89 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 2.05 | 123 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 1.43 | 86 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 0.68 | 41 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | integer | 653888310 |
| 2 | `timestamp` | string (numeric) | 1791857420 |
| 3 | `amount` | number | 21.47412281 |
| 4 | `amount_str` | string (numeric) | 21.47412281 |
| 5 | `price` | number | 1.35372 |
| 6 | `price_str` | string (numeric) | 1.35372 |
| 7 | `type` | integer | 0 |
| 8 | `microtimestamp` | string (numeric) | 1791857420968000 |
| 9 | `buy_order_id` | integer | 2060379940085762 |
| 10 | `sell_order_id` | integer | 2060379938447361 |

</details>

<a id="s-albion"></a>
### 32. Albion Online Data Project market orders

- **Verdict:** Meets both — average 19.89 events/s, median 10.0 attributes per event.
- **Delivery:** live · NATS (TCP 4222)
- **Endpoint:** `nats://nats.albion-online-data.com:4222`
- **Request:** `CONNECT user=public pass=thenewalbiondata; SUB marketorders.deduped`
- **Access:** Published public credentials
- **Documentation:** https://www.albion-online-data.com/ (HTTP 200)
- **Terms / licence:** https://github.com/ao-data/albiondata-client (HTTP 200) — “ternate_user_config_repo","async_conversion_coverage_enabled","billing_billable_licenses_cost_center_bucket_fix","billing_budget_expiration","billing_cost_center_list_assigned_resources","billing_discount_th”
- **Measurement note (latest representative round):** NATS subject marketorders.deduped (Americas server)
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 14.43 | 866 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T02:11 | ok | 1.02 | 61 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T03:23 | ok | 47.73 | 2,864 | 60 | 10.0 | 10 | 10 |
| 2026-10-13T04:23 | ok | 16.37 | 982 | 60 | 10.0 | 10 | 10 |

<details><summary>Sample event — 10 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `Id` | integer | 15454378873 |
| 2 | `ItemTypeId` | string | T4_CAPEITEM_FW_LYMHURST |
| 3 | `ItemGroupTypeId` | string | T4_CAPEITEM_FW_LYMHURST |
| 4 | `LocationId` | integer | 5003 |
| 5 | `QualityLevel` | integer | 3 |
| 6 | `EnchantmentLevel` | integer | 0 |
| 7 | `UnitPriceSilver` | integer | 64996 |
| 8 | `Amount` | integer | 1 |
| 9 | `AuctionType` | string | offer |
| 10 | `Expires` | string (date/time) | 2026-11-11T22:53:42.354584 |

</details>

<a id="s-twitch"></a>
### 33. Twitch chat (anonymous read-only IRC)

- **Verdict:** Meets both — average 19.35 events/s, median 19.0 attributes per event.
- **Delivery:** live · IRC over WebSocket
- **Endpoint:** `wss://irc-ws.chat.twitch.tv:443`
- **Request:** `CAP REQ :twitch.tv/tags; PASS SCHMOOPIIE; NICK justinfanNNNN; JOIN #<channels>`
- **Access:** Anonymous (justinfan) read-only login
- **Documentation:** https://dev.twitch.tv/docs/chat/irc/ (HTTP 200)
- **Terms / licence:** https://legal.twitch.com/legal/developer-agreement/ (HTTP 200) — “Chat We consider chat to be an essential component of the broadcast experience on Twitch”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 24.07 | 1,444 | 60 | 19.0 | 28 | 33 |
| 2026-10-13T02:11 | ok | 22.03 | 1,322 | 60 | 19.0 | 28 | 33 |
| 2026-10-13T03:23 | ok | 18.22 | 1,093 | 60 | 19.0 | 28 | 32 |
| 2026-10-13T04:23 | ok | 13.07 | 784 | 60 | 19.0 | 28 | 32 |

<details><summary>Sample event — 28 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `badge-info` | string |  |
| 2 | `badges` | string | pichu/1 |
| 3 | `client-nonce` | string (redacted) | ‹redacted› |
| 4 | `color` | string | #00FF7F |
| 5 | `display-name` | string (redacted) | ‹redacted› |
| 6 | `emotes` | string |  |
| 7 | `first-msg` | string (numeric) | 0 |
| 8 | `flags` | string |  |
| 9 | `id` | string (redacted) | ‹redacted› |
| 10 | `mod` | string (numeric) | 0 |
| 11 | `reply-parent-display-name` | string (redacted) | ‹redacted› |
| 12 | `reply-parent-msg-body` | string (redacted) | ‹redacted› |
| 13 | `reply-parent-msg-id` | string (redacted) | ‹redacted› |
| 14 | `reply-parent-user-id` | string (redacted) | ‹redacted› |
| 15 | `reply-parent-user-login` | string (redacted) | ‹redacted› |
| 16 | `reply-thread-parent-display-name` | string (redacted) | ‹redacted› |
| 17 | `reply-thread-parent-msg-id` | string (redacted) | ‹redacted› |
| 18 | `reply-thread-parent-user-id` | string (redacted) | ‹redacted› |
| 19 | `reply-thread-parent-user-login` | string (redacted) | ‹redacted› |
| 20 | `returning-chatter` | string (numeric) | 0 |
| 21 | `room-id` | string (redacted) | ‹redacted› |
| 22 | `subscriber` | string (numeric) | 0 |
| 23 | `tmi-sent-ts` | string (numeric) | 1791857421948 |
| 24 | `turbo` | string (numeric) | 0 |
| 25 | `user-id` | string (redacted) | ‹redacted› |
| 26 | `user-type` | string |  |
| 27 | `channel` | string | #xqc |
| 28 | `message` | string (redacted) | ‹redacted› |

</details>

<a id="s-dt_road"></a>
### 34. Digitraffic Finland road traffic (TMS) and road-weather sensors

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 341.60 events/s, median 2.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://tie.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE tms-v2/# and weather-v2/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/road-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Enrichment:** Station and sensor metadata: https://tie.digitraffic.fi/api/tms/v1/stations and /api/weather/v1/stations
- **Measurement note (latest representative round):** example topic: tms-v2/23572/5055
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **Verified enrichment:** join on stationId from the MQTT topic tms-v2/{stationId}/{sensorId} with `https://tie.digitraffic.fi/api/tms/v1/stations/23572` (HTTP 200) → median 2.0 + 39 = **41.0 attributes** after the join (verified on one event: 4 → 43) (station properties joined to each sensor value; checked 2026-10-13T04:35:34Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 327.33 | 19,640 | 60 | 2.0 | 4 | 4 |
| 2026-10-13T02:11 | ok | 356.93 | 21,416 | 60 | 2.0 | 4 | 4 |
| 2026-10-13T03:23 | ok | 330.83 | 19,850 | 60 | 2.0 | 2 | 2 |
| 2026-10-13T04:23 | ok | 351.30 | 21,078 | 60 | 4.0 | 4 | 5 |

<details><summary>Sample event — 4 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `end` | integer | 1791856800 |
| 2 | `start` | integer | 1791853200 |
| 3 | `time` | integer | 1791857431 |
| 4 | `value` | number | 54.0 |

</details>

<a id="s-dt_rail"></a>
### 35. Digitraffic Finland train GPS locations

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 47.40 events/s, median 8.0 attributes per event.
- **Delivery:** live · MQTT over WSS
- **Endpoint:** `wss://rata.digitraffic.fi:443/mqtt`
- **Request:** `SUBSCRIBE train-locations/#`
- **Access:** None
- **Documentation:** https://www.digitraffic.fi/en/railway-traffic/ (HTTP 200)
- **Terms / licence:** https://www.digitraffic.fi/en/terms-of-service/ (HTTP 200) — “Creative Commons 4.0 By license”
- **Measurement note (latest representative round):** example topic: train-locations/2026-10-13/2003
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects yes
- **Verified enrichment:** join on (departureDate, trainNumber) with `https://rata.digitraffic.fi/api/v1/trains/2026-10-13/1` (HTTP 200) → median 8.0 + 13 = **21.0 attributes** after the join (verified on one event: 8 → 21) (train record joined to each GPS fix; checked 2026-10-13T04:35:35Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 30.50 | 1,830 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T02:11 | ok | 32.63 | 1,958 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T03:23 | ok | 48.55 | 2,913 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T04:23 | ok | 77.90 | 4,674 | 60 | 8.0 | 8 | 8 |

<details><summary>Sample event — 8 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `accuracy` | integer | 0 |
| 2 | `isGpsLocation` | boolean | true |
| 3 | `location.type` | string | Point |
| 4 | `location.coordinates` | list (serialised) | [28.495049, 61.122156] |
| 5 | `speed` | integer | 0 |
| 6 | `trainNumber` | integer | 2003 |
| 7 | `departureDate` | string | 2026-10-13 |
| 8 | `timestamp` | string (date/time) | 2026-10-13T01:23:24Z |

</details>

<a id="s-mta_gtfsrt"></a>
### 36. MTA New York City Subway GTFS-Realtime (A/C/E feed)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 4.86 events/s, median 6.5 attributes per event.
- **Delivery:** poll · GTFS-Realtime protobuf over HTTPS, polled every 15 s
- **Endpoint:** `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace`
- **Request:** `GET (7 more subway feeds: gtfs, -bdfm, -g, -jz, -nqrw, -l, -si)`
- **Access:** None
- **Documentation:** https://api.mta.info/ (HTTP 200)
- **Terms / licence:** https://www.mta.info/developers (HTTP 403) — “Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to apply for a license. [page refuses scripted requests (HTTP 403); text retrieved with the webfetch tool on 2026-10-13]”
- **Measurement note (latest representative round):** 4 polls every 15s; 180 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **Verified enrichment:** join on vehicle.stopId → stops.txt; vehicle.trip.routeId → routes.txt with `https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip` (HTTP 200) → median 6.5 + 16 = **22.5 attributes** after the join (verified on one event: 9 → 25) (static GTFS stop and route joined to each vehicle; checked 2026-10-13T04:35:36Z).
- **In the Bytewax list:** yes (mta.info) · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 4.68 | 304 | 65 | 6.5 | 9 | 14 |
| 2026-10-13T02:11 | ok | 5.41 | 303 | 56 | 6.5 | 9 | 14 |
| 2026-10-13T03:23 | ok | 4.78 | 221 | 46 | 6.5 | 9 | 14 |
| 2026-10-13T04:23 | ok | 4.58 | 210 | 46 | 6.5 | 9 | 14 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | string | 000002A |
| 2 | `vehicle.trip.tripId` | string | 124150_A..N55R |
| 3 | `vehicle.trip.startTime` | string | 20:41:30 |
| 4 | `vehicle.trip.startDate` | string (numeric) | 20261012 |
| 5 | `vehicle.trip.routeId` | string | A |
| 6 | `vehicle.currentStopSequence` | integer | 31 |
| 7 | `vehicle.currentStatus` | string | STOPPED_AT |
| 8 | `vehicle.timestamp` | string (numeric) | 1791857397 |
| 9 | `vehicle.stopId` | string | A09N |

</details>

<a id="s-osm"></a>
### 37. OpenStreetMap minutely replication diffs

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 29.75 events/s, median 9.0 attributes per event.
- **Delivery:** batch · gzip osmChange XML, one file per minute
- **Endpoint:** `https://planet.openstreetmap.org/replication/minute/NNN/NNN/NNN.osc.gz (state.txt gives the sequence)`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://wiki.openstreetmap.org/wiki/Planet.osm/diffs (HTTP 200)
- **Terms / licence:** https://www.openstreetmap.org/copyright (HTTP 200) — “Open Data Commons Open Database License (ODbL) by the OpenStreetMap Foundation (OSMF)”
- **Measurement note (latest representative round):** minute diff #7326630; 9 fixed attributes per element + its OSM tags (tag:*), counted per event
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 52.80 | 3,168 | 60 | 9.0 | 18 | 36 |
| 2026-10-13T02:11 | ok | 27.07 | 1,624 | 60 | 9.0 | 15 | 27 |
| 2026-10-13T03:23 | ok | 6.37 | 382 | 60 | 9.0 | 294 | 360 |
| 2026-10-13T04:23 | ok | 32.78 | 1,967 | 60 | 9.0 | 30 | 54 |

<details><summary>Sample event — 294 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | string (numeric) | 424313451 |
| 2 | `version` | string (numeric) | 93 |
| 3 | `timestamp` | string (date/time) | 2026-10-13T03:20:51Z |
| 4 | `uid` | string (redacted) | ‹redacted› |
| 5 | `user` | string (redacted) | ‹redacted› |
| 6 | `changeset` | string (numeric) | 190430503 |
| 7 | `lat` | string (numeric) | 36.5748441 |
| 8 | `lon` | string (numeric) | 139.2394179 |
| 9 | `element` | string | node |
| 10 | `tag:alt_name:eo` | string | Japanujo;Nipono |
| 11 | `tag:alt_name:ja` | string | 日本 |
| 12 | `tag:alt_name:ja-Hira` | string | にっぽん |
| 13 | `tag:alt_name:ja-Latn` | string | Nippon |
| 14 | `tag:alt_name:lfn` | string | Japan |
| 15 | `tag:alt_name:vi` | string | Nhật |
| 16 | `tag:capital_city` | string | Tokyo |
| 17 | `tag:country_code_fips` | string | JA |
| 18 | `tag:country_code_iso3166_1_alpha_2` | string | JP |
| 19 | `tag:int_name` | string | Japan |
| 20 | `tag:name` | string | 日本 |
| 21 | `tag:name:aa` | string | Japan |
| 22 | `tag:name:ab` | string | Иапониа |
| 23 | `tag:name:ace` | string | Jeupun |
| 24 | `tag:name:af` | string | Japan |
| 25 | `tag:name:ak` | string | Gyapan |
| 26 | `tag:name:als` | string | Japan |
| 27 | `tag:name:am` | string | ጃፓን |
| 28 | `tag:name:an` | string | Chapón |
| 29 | `tag:name:ang` | string | Iapan |
| 30 | `tag:name:ar` | string | اليابان |
| 31 | `tag:name:arc` | string | ܝܦܢ |
| 32 | `tag:name:arz` | string | اليابان |
| 33 | `tag:name:as` | string | জাপান |
| 34 | `tag:name:ast` | string | Xapón |
| 35 | `tag:name:ay` | string | Nihun |
| 36 | `tag:name:az` | string | Yaponiya |
| 37 | `tag:name:azb` | string | ژاپون |
| 38 | `tag:name:ba` | string | Япония |
| 39 | `tag:name:bar` | string | Japan |
| 40 | `tag:name:bat-smg` | string | Japuonėjė |
| 41 | `tag:name:bcl` | string | Hapon |
| 42 | `tag:name:be` | string | Японія |
| 43 | `tag:name:be-tarask` | string | Японія |
| 44 | `tag:name:bg` | string | Япония |
| 45 | `tag:name:bjn` | string | Japang |
| 46 | `tag:name:bm` | string | Zapɔn |
| 47 | `tag:name:bn` | string | জাপান |
| 48 | `tag:name:bo` | string | རི་པིན། |
| 49 | `tag:name:bpy` | string | জাপান |
| 50 | `tag:name:br` | string | Japan |
| 51 | `tag:name:bs` | string | Japan |
| 52 | `tag:name:bug` | string | ᨍᨛᨄ |
| 53 | `tag:name:bxr` | string | Жибэн |
| 54 | `tag:name:ca` | string | Japó |
| 55 | `tag:name:cbk-zam` | string | Japón |
| 56 | `tag:name:cdo` | string | Nĭk-buōng |
| 57 | `tag:name:ce` | string | Япони |
| 58 | `tag:name:ceb` | string | Hapon |
| 59 | `tag:name:ch` | string | Chapan |
| 60 | `tag:name:chr` | string | ᏣᏆᏂ |
| 61 | `tag:name:ckb` | string | ژاپۆن |
| 62 | `tag:name:cnr` | string | Japan |
| 63 | `tag:name:crh` | string | Yaponiya |
| 64 | `tag:name:cs` | string | Japonsko |
| 65 | `tag:name:csb` | string | Japòńskô |
| 66 | `tag:name:cu` | string | Ꙗпѡні́ꙗ |
| 67 | `tag:name:cv` | string | Япони |
| 68 | `tag:name:cy` | string | Japan |
| 69 | `tag:name:da` | string | Japan |
| 70 | `tag:name:dak` | string | Kisuƞna Maḳoc̣e |
| 71 | `tag:name:de` | string | Japan |
| 72 | `tag:name:diq` | string | Japonya |
| 73 | `tag:name:dsb` | string | Japańska |
| 74 | `tag:name:dv` | string | ޖަޕާނު |
| 75 | `tag:name:dz` | string | ཇ་པཱན |
| 76 | `tag:name:ee` | string | Japan |
| 77 | `tag:name:el` | string | Ιαπωνία |
| 78 | `tag:name:en` | string | Japan |
| 79 | `tag:name:eo` | string | Japanio |
| 80 | `tag:name:es` | string | Japón |
| 81 | `tag:name:et` | string | Jaapan |
| 82 | `tag:name:eu` | string | Japonia |
| 83 | `tag:name:ext` | string | Japón |
| 84 | `tag:name:fa` | string | ژاپن |
| 85 | `tag:name:ff` | string | Sapoo |
| 86 | `tag:name:fi` | string | Japani |
| 87 | `tag:name:fo` | string | Japan |
| 88 | `tag:name:fr` | string | Japon |
| 89 | `tag:name:frp` | string | J·apon |
| 90 | `tag:name:frr` | string | Japan |
| 91 | `tag:name:fur` | string | Gjapon |
| 92 | `tag:name:fy` | string | Japan |
| 93 | `tag:name:ga` | string | An tSeapáin |
| 94 | `tag:name:gag` | string | Yaponiya |
| 95 | `tag:name:gan` | string | 日本 |
| 96 | `tag:name:gd` | string | Iapan |
| 97 | `tag:name:gl` | string | Xapón - 日本 |
| 98 | `tag:name:glk` | string | ژاپؤن |
| 99 | `tag:name:gn` | string | Hapõ |
| 100 | `tag:name:gu` | string | જાપાન |
| 101 | `tag:name:gv` | string | Yn Çhapaan |
| 102 | `tag:name:ha` | string | Japan |
| 103 | `tag:name:hak` | string | Ngi̍t-pún |
| 104 | `tag:name:haw` | string | Iāpana |
| 105 | `tag:name:he` | string | יפן |
| 106 | `tag:name:hi` | string | जापान |
| 107 | `tag:name:hif` | string | Japan |
| 108 | `tag:name:hr` | string | Japan |
| 109 | `tag:name:hsb` | string | Japanska |
| 110 | `tag:name:ht` | string | Japon |
| 111 | `tag:name:hu` | string | Japán |
| 112 | `tag:name:hy` | string | Ճապոնիա |
| 113 | `tag:name:ia` | string | Japon |
| 114 | `tag:name:id` | string | Jepang |
| 115 | `tag:name:ie` | string | Japan |
| 116 | `tag:name:ii` | string | ꏝꀪ |
| 117 | `tag:name:ilo` | string | Japon |
| 118 | `tag:name:io` | string | Japonia |
| 119 | `tag:name:is` | string | Japan |
| 120 | `tag:name:it` | string | Giappone |
| 121 | `tag:name:iu` | string | ᓃᑉᐊᓐ |
| 122 | `tag:name:iu-Latn` | string | niipan |
| 123 | `tag:name:ja` | string | 日本 |
| 124 | `tag:name:ja-Hira` | string | にほん |
| 125 | `tag:name:ja-Latn` | string | Nihon |
| 126 | `tag:name:jbo` | string | pongu&apos;e |
| 127 | `tag:name:jv` | string | Jepang |
| 128 | `tag:name:ka` | string | იაპონია |
| 129 | `tag:name:kab` | string | Jappu |
| 130 | `tag:name:kbd` | string | Япон |
| 131 | `tag:name:ki` | string | Njabani |
| 132 | `tag:name:kk` | string | Жапония |
| 133 | `tag:name:kl` | string | Japani |
| 134 | `tag:name:km` | string | ជប៉ុន |
| 135 | `tag:name:kmr` | string | ژاپۆن |
| 136 | `tag:name:kn` | string | ಜಪಾನ್ |
| 137 | `tag:name:ko` | string | 일본 |
| 138 | `tag:name:koi` | string | Ниппон |
| 139 | `tag:name:krc` | string | Япония |
| 140 | `tag:name:ks` | string | جاپون |
| 141 | `tag:name:ksh` | string | Japan |
| 142 | `tag:name:ku` | string | Japon |
| 143 | `tag:name:kv` | string | Япония |
| 144 | `tag:name:kw` | string | Nihon |
| 145 | `tag:name:ky` | string | Жапония |
| 146 | `tag:name:la` | string | Iaponia |
| 147 | `tag:name:lb` | string | Japan |
| 148 | `tag:name:lez` | string | Япония |
| 149 | `tag:name:lfn` | string | Nion |
| 150 | `tag:name:lg` | string | Japani |
| 151 | `tag:name:li` | string | Japan |
| 152 | `tag:name:lij` | string | Giappon |
| 153 | `tag:name:lkt` | string | Kisúŋla-Makȟóčhe |
| 154 | `tag:name:lmo` | string | Giapun |
| 155 | `tag:name:ln` | string | Zapɔ́ |
| 156 | `tag:name:lo` | string | ປະເທດຍີ່ປຸ່ນ |
| 157 | `tag:name:lrc` | string | جاپوݩ |
| 158 | `tag:name:lt` | string | Japonija |
| 159 | `tag:name:ltg` | string | Japoneja |
| 160 | `tag:name:lv` | string | Japāna |
| 161 | `tag:name:lzh` | string | 日本 |
| 162 | `tag:name:mdf` | string | Япунмастор |
| 163 | `tag:name:mg` | string | Japana |
| 164 | `tag:name:mhr` | string | Японий |
| 165 | `tag:name:mi` | string | Nipono |
| 166 | `tag:name:min` | string | Japang |
| 167 | `tag:name:mk` | string | Јапонија |
| 168 | `tag:name:ml` | string | ജപ്പാന്‍ |
| 169 | `tag:name:mn` | string | Япон |
| 170 | `tag:name:mo` | string | Жапония |
| 171 | `tag:name:mr` | string | जपान |
| 172 | `tag:name:mrj` | string | Япони |
| 173 | `tag:name:ms` | string | Jepun |
| 174 | `tag:name:mt` | string | Ġappun |
| 175 | `tag:name:mwl` | string | Japon |
| 176 | `tag:name:my` | string | ဂျပန်နိုင်ငံ |
| 177 | `tag:name:mzn` | string | جاپون |
| 178 | `tag:name:na` | string | Djapan |
| 179 | `tag:name:nah` | string | Xapon |
| 180 | `tag:name:nan` | string | Ji̍t-pún |
| 181 | `tag:name:nap` | string | Giappone |
| 182 | `tag:name:nds` | string | Japan |
| 183 | `tag:name:nds-nl` | string | Japan |
| 184 | `tag:name:ne` | string | जापान |
| 185 | `tag:name:new` | string | जापान |
| 186 | `tag:name:nl` | string | Japan |
| 187 | `tag:name:nn` | string | Japan |
| 188 | `tag:name:no` | string | Japan |
| 189 | `tag:name:nov` | string | Japan |
| 190 | `tag:name:nrm` | string | Japon |
| 191 | `tag:name:nso` | string | Japane |
| 192 | `tag:name:nv` | string | Bina&apos;adaałtzózí |
| 193 | `tag:name:oc` | string | Japon |
| 194 | `tag:name:om` | string | Japan |
| 195 | `tag:name:or` | string | ଜାପାନ |
| 196 | `tag:name:os` | string | Япон |
| 197 | `tag:name:pa` | string | ਜਪਾਨ |
| 198 | `tag:name:pam` | string | Hapon |
| 199 | `tag:name:pap` | string | Hapon |
| 200 | `tag:name:pcd` | string | Japon |
| 201 | `tag:name:pdc` | string | Japan |
| 202 | `tag:name:pih` | string | Japan |
| 203 | `tag:name:pl` | string | Japonia |
| 204 | `tag:name:pms` | string | Giapon |
| 205 | `tag:name:pnb` | string | جاپان |
| 206 | `tag:name:ps` | string | جاپان |
| 207 | `tag:name:pt` | string | Japão |
| 208 | `tag:name:qu` | string | Nihun |
| 209 | `tag:name:rm` | string | Giapun |
| 210 | `tag:name:rn` | string | Ubuyapani |
| 211 | `tag:name:ro` | string | Japonia |
| 212 | `tag:name:roa-rup` | string | Japonia |
| 213 | `tag:name:roa-tara` | string | Giappone |
| 214 | `tag:name:ru` | string | Япония |
| 215 | `tag:name:rue` | string | Японія |
| 216 | `tag:name:rw` | string | Ubuyapani |
| 217 | `tag:name:sa` | string | जापान |
| 218 | `tag:name:sah` | string | Дьоппуон |
| 219 | `tag:name:sc` | string | Giapone |
| 220 | `tag:name:scn` | string | Giappuni |
| 221 | `tag:name:sco` | string | Japan |
| 222 | `tag:name:sd` | string | جاپان |
| 223 | `tag:name:se` | string | Japána |
| 224 | `tag:name:sg` | string | Zapöon |
| 225 | `tag:name:sh` | string | Japan |
| 226 | `tag:name:si` | string | ජපානය |
| 227 | `tag:name:sk` | string | Japonsko |
| 228 | `tag:name:sl` | string | Japonska |
| 229 | `tag:name:sm` | string | Iapani |
| 230 | `tag:name:smn` | string | Jaapaan |
| 231 | `tag:name:sms` | string | Japaan |
| 232 | `tag:name:sn` | string | Japan |
| 233 | `tag:name:so` | string | Jabaan |
| 234 | `tag:name:sq` | string | Japonia |
| 235 | `tag:name:sr` | string | Јапан |
| 236 | `tag:name:srn` | string | Japan |
| 237 | `tag:name:ss` | string | IJaphani |
| 238 | `tag:name:stq` | string | Japan |
| 239 | `tag:name:su` | string | Jepang |
| 240 | `tag:name:sv` | string | Japan |
| 241 | `tag:name:sw` | string | Japani |
| 242 | `tag:name:szl` | string | Japōnijŏ |
| 243 | `tag:name:ta` | string | ஜப்பான் |
| 244 | `tag:name:te` | string | జపాన్ |
| 245 | `tag:name:tg` | string | Ҷопон |
| 246 | `tag:name:th` | string | ประเทศญี่ปุ่น |
| 247 | `tag:name:ti` | string | ጃፓን |
| 248 | `tag:name:tk` | string | Ýaponiýa |
| 249 | `tag:name:tl` | string | Hapon |
| 250 | `tag:name:to` | string | Siapani |
| 251 | `tag:name:tok` | string | ma Nijon |
| 252 | `tag:name:tpi` | string | Siapan |
| 253 | `tag:name:tr` | string | Japonya |
| 254 | `tag:name:tt` | string | Япония |
| 255 | `tag:name:tw` | string | Yapan |
| 256 | `tag:name:ty` | string | Tāpōnē |
| 257 | `tag:name:tzl` | string | Cipangu |
| 258 | `tag:name:udm` | string | Япония |
| 259 | `tag:name:ug` | string | ياپونىيە |
| 260 | `tag:name:uk` | string | Японія |
| 261 | `tag:name:ur` | string | جاپان |
| 262 | `tag:name:uz` | string | Yaponiya |
| 263 | `tag:name:vec` | string | Giapòn |
| 264 | `tag:name:vi` | string | Nhật Bản |
| 265 | `tag:name:vo` | string | Yapän |
| 266 | `tag:name:vro` | string | Jaapan |
| 267 | `tag:name:wal` | string | Jaappaane |
| 268 | `tag:name:war` | string | Hapon |
| 269 | `tag:name:wo` | string | Sapoŋ |
| 270 | `tag:name:wuu` | string | 日本 |
| 271 | `tag:name:xal` | string | Японь |
| 272 | `tag:name:xmf` | string | იაპონია |
| 273 | `tag:name:xnb` | string | Ripun |
| 274 | `tag:name:yi` | string | יאפאן |
| 275 | `tag:name:yo` | string | Japan |
| 276 | `tag:name:yue` | string | 日本 |
| 277 | `tag:name:za` | string | Nditbonj |
| 278 | `tag:name:zea` | string | Japan |
| 279 | `tag:name:zh` | string | 日本 |
| 280 | `tag:name:zh-Hans` | string | 日本 |
| 281 | `tag:name:zh-Hant` | string | 日本 |
| 282 | `tag:name:zh-Latn-pinyin` | string | Rìběn |
| 283 | `tag:name:zu` | string | iJapani |
| 284 | `tag:official_name:ar` | string | دولة اليابان |
| 285 | `tag:official_name:ca` | string | Estat del Japó |
| 286 | `tag:official_name:pt` | string | Império do Japão |
| 287 | `tag:old_name:vi` | string | Nhật Bổn |
| 288 | `tag:place` | string | country |
| 289 | `tag:population` | string (numeric) | 127360000 |
| 290 | `tag:source:population` | string | http://www.stat.go.jp/english/data/jinsui/tsuki/index.htm 2010 |
| 291 | `tag:source:sqkm` | string | CIA World Factbook |
| 292 | `tag:sqkm` | string (numeric) | 377915 |
| 293 | `tag:wikidata` | string | Q17 |
| 294 | `tag:wikipedia` | string | en:Japan |

</details>

<a id="s-npm"></a>
### 38. npm registry replication changes

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 2.26 events/s, median 3.0 attributes per event.
- **Delivery:** counter · CouchDB-style _changes over HTTPS
- **Endpoint:** `https://replicate.npmjs.com/registry/_changes`
- **Request:** `GET ?since=<seq>`
- **Access:** None
- **Documentation:** https://github.com/npm/registry-follower-tutorial (HTTP 200)
- **Terms / licence:** https://docs.npmjs.com/policies/open-source-terms (HTTP 200) — “rted Setting up your npm user account Creating a new user account on the public registry Creating a strong password Receiving a one-time password over email About two-factor authentication Configuring two-factor authentication Accessing npm using t”
- **Measurement note (latest representative round):** raw change record; full package metadata needs one extra GET per change
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **Verified enrichment:** join on id (package name) with `https://registry.npmjs.org/@aztec-labs%2fworld-state/latest` (HTTP 200) → median 3.0 + 27 = **30.0 attributes** after the join (verified on one event: 3 → 30) (latest package version document fetched per change; checked 2026-10-13T04:35:36Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 2.18 | 140 | 64 | 3.0 | 3 | 3 |
| 2026-10-13T02:11 | ok | 1.89 | 124 | 65 | 3.0 | 3 | 3 |
| 2026-10-13T03:23 | ok | 1.90 | 115 | 61 | 3.0 | 3 | 3 |
| 2026-10-13T04:23 | ok | 3.08 | 186 | 60 | 3.0 | 3 | 3 |

<details><summary>Sample event — 3 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `seq` | integer | 136460198 |
| 2 | `id` | string | @typescript-eslint/rule-schema-to-typescript-types |
| 3 | `changes` | list (serialised) | [{'rev': '538-e54131f803d620041b0d9f1fe0d25994'}] |

</details>

<a id="s-rbn"></a>
### 39. Reverse Beacon Network (CW/RTTY skimmer spots)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 1.33 events/s, median 9.0 attributes per event.
- **Delivery:** live · Telnet text lines
- **Endpoint:** `telnet://telnet.reversebeacon.net:7000`
- **Request:** `send any callsign at login`
- **Access:** None
- **Documentation:** https://www.reversebeacon.net/ (HTTP 200)
- **Terms / licence:** https://www.reversebeacon.net/ (HTTP 200) — “lst about A Short History Telnet servers Get Smart About the RBN Who We Are RBN Value Multipliers ARCluster V6 Filtering Red Pitaya, preparing Guide to the new site (beta) How to get spotted b”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.65 | 99 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 1.38 | 83 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 1.23 | 74 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T04:23 | ok | 1.07 | 64 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `spotter` | string (redacted) | ‹redacted› |
| 2 | `freq` | string (numeric) | 1836.00 |
| 3 | `dx` | string (redacted) | ‹redacted› |
| 4 | `mode` | string | CW |
| 5 | `snr` | string (numeric) | 4 |
| 6 | `speed` | string (numeric) | 21 |
| 7 | `unit` | string | WPM |
| 8 | `type` | string | CQ |
| 9 | `time` | string (numeric) | 0210 |

</details>

<a id="s-solana"></a>
### 40. Solana program logs (public mainnet RPC)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 837.28 events/s, median 4.0 attributes per event.
- **Delivery:** live · JSON-RPC over WebSocket (logsSubscribe)
- **Endpoint:** `wss://api.mainnet-beta.solana.com`
- **Request:** `{"method":"logsSubscribe","params":["all",{"commitment":"confirmed"}]}`
- **Access:** None (public RPC is rate-limited)
- **Documentation:** https://solana.com/docs/rpc/websocket/logssubscribe (HTTP 200)
- **Terms / licence:** https://solana.com/docs/references/clusters (HTTP 200) — “Each of these public endpoints are subject to rate limits, but are available for users and developers to interact with the Solana blockchain”
- **Data shape (by attribute name):** geographic position no · time field no · nested objects yes
- **Verified enrichment:** join on value.signature with `https://api.mainnet-beta.solana.com (getTransaction)` (HTTP 200) → median 4.0 + 18 = **22.0 attributes** after the join (verified on one event: 4 → 22) (transaction metadata fetched per log notification (one extra RPC call each); checked 2026-10-13T04:35:36Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 46.10 | 2,766 | 60 | 4.0 | 4 | 5 |
| 2026-10-13T02:11 | ok | 504.60 | 30,276 | 60 | 4.0 | 4 | 5 |
| 2026-10-13T03:23 | ok | 1,216.87 | 73,012 | 60 | 4.0 | 4 | 5 |
| 2026-10-13T04:23 | ok | 1,581.57 | 94,894 | 60 | 4.0 | 4 | 5 |

<details><summary>Sample event — 4 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `context.slot` | integer | 456271998 |
| 2 | `value.signature` | string | 4Pn8gD7sYLj7fVHJ4bT9JpXrdERmiGkz9QfhuKPpEUFB3EcStpvGPCuun1AcpaptM9pvxtNo8bMYKFLyYN6aDkYc |
| 3 | `value.err` | null | null |
| 4 | `value.logs` | string | ['Program ComputeBudget111111111111111111111111111111 invoke [1]', 'Program ComputeBudget… |

</details>

<a id="s-gemini"></a>
### 41. Gemini market data v1 (order-book changes + trades)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 637.07 events/s, median 9.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://api.gemini.com/v1/marketdata/<SYMBOL>`
- **Request:** `connect per symbol (no message)`
- **Access:** None
- **Documentation:** https://developer.gemini.com/websocket/streams.md (HTTP 200)
- **Terms / licence:** https://developer.gemini.com/websocket/streams.md (HTTP 200) — “er ID â an obfuscated alias for the numeric order ID ('i'), safe for external/public display \| \| 'c' \| string \| Client order ID”
- **Measurement note (latest representative round):** 3 symbols (BTCUSD, ETHUSD, SOLUSD), v1 market data: order-book changes + trades
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **Verified enrichment:** join on symbol with `https://api.gemini.com/v1/symbols/details/btcusd` (HTTP 200) → median 9.0 + 11 = **20.0 attributes** after the join (verified on one event: 9 → 20) (symbol details joined to each order-book change; checked 2026-10-13T04:35:36Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 832.17 | 49,930 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 786.53 | 47,192 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 422.62 | 25,357 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T04:23 | ok | 506.95 | 30,417 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `delta` | string (numeric) | 0.0843954 |
| 2 | `price` | string (numeric) | 82249.0 |
| 3 | `reason` | string | initial |
| 4 | `remaining` | string (numeric) | 0.0843954 |
| 5 | `side` | string | bid |
| 6 | `type` | string | change |
| 7 | `eventId` | integer | 1764561291336754 |
| 8 | `timestampms` | null | null |
| 9 | `socket_sequence` | integer | 0 |

</details>

<a id="s-hyperliquid"></a>
### 42. Hyperliquid trades

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 8.31 events/s, median 8.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://api.hyperliquid.xyz/ws`
- **Request:** `{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}}`
- **Access:** None
- **Documentation:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions (HTTP 200)
- **Terms / licence:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions (HTTP 200) — “: int , fast: boolean (5 levels if fast, 20 levels if slow) Data format: WsBook trades : Subscription message: { &quot;type&quot;: &quot;trades&quot;, &quot;coin&quot;: &quot;&lt;coin_symbol&gt;&quot; } Dat”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **Verified enrichment:** join on coin with `https://api.hyperliquid.xyz/info {type: metaAndAssetCtxs}` (HTTP 200) → median 8.0 + 14 = **22.0 attributes** after the join (verified on one event: 8 → 22) (asset metadata and live context joined to each trade; checked 2026-10-13T04:35:37Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.68 | 581 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T02:11 | ok | 12.12 | 727 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T03:23 | ok | 4.87 | 292 | 60 | 8.0 | 8 | 8 |
| 2026-10-13T04:23 | ok | 6.57 | 394 | 60 | 8.0 | 8 | 8 |

<details><summary>Sample event — 8 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `coin` | string | BTC |
| 2 | `side` | string | B |
| 3 | `px` | string (numeric) | 82440.0 |
| 4 | `sz` | string (numeric) | 0.00115 |
| 5 | `time` | integer | 1791857404350 |
| 6 | `hash` | string | 0x182acbd523bc9e6219a40446706558020c1300babebfbd34bbf37727e2b0784c |
| 7 | `tid` | integer | 640851645839836 |
| 8 | `users` | string (redacted) | ‹redacted› |

</details>

<a id="s-bybit"></a>
### 43. Bybit spot tickers

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 7.15 events/s, median 9.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://stream.bybit.com/v5/public/spot`
- **Request:** `{"op":"subscribe","args":["tickers.BTCUSDT",...]}`
- **Access:** None
- **Documentation:** https://bybit-exchange.github.io/docs/v5/websocket/public/ticker (HTTP 200)
- **Terms / licence:** https://bybit-exchange.github.io/docs/v5/websocket/public/ticker (HTTP 200) — “Spot &amp; Option tickers message are snapshot only Push frequency: Derivatives &amp; Options - 100ms , Spot - 50ms Topic: tickers”
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **Verified enrichment:** join on symbol with `https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=BTCUSDT` (HTTP 200) → median 9.0 + 22 = **31.0 attributes** after the join (verified on one event: 9 → 31) (instrument metadata joined to each ticker; checked 2026-10-13T04:35:37Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 7.35 | 441 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T02:11 | ok | 8.40 | 504 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T03:23 | ok | 7.08 | 425 | 60 | 9.0 | 9 | 9 |
| 2026-10-13T04:23 | ok | 5.78 | 347 | 60 | 9.0 | 9 | 9 |

<details><summary>Sample event — 9 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `symbol` | string | BTCUSDT |
| 2 | `lastPrice` | string (numeric) | 82505.9 |
| 3 | `highPrice24h` | string (numeric) | 84355.8 |
| 4 | `lowPrice24h` | string (numeric) | 81031.2 |
| 5 | `prevPrice24h` | string (numeric) | 83695.2 |
| 6 | `volume24h` | string (numeric) | 9674.971793 |
| 7 | `turnover24h` | string (numeric) | 801562254.50840967 |
| 8 | `price24hPcnt` | string (numeric) | -0.0142 |
| 9 | `usdIndexPrice` | string (numeric) | 82396.431504 |

</details>

<a id="s-kraken"></a>
### 44. Kraken trades + ticker (v2)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 6.01 events/s, median 7.0 attributes per event.
- **Delivery:** live · WebSocket (JSON)
- **Endpoint:** `wss://ws.kraken.com/v2`
- **Request:** `{"method":"subscribe","params":{"channel":"trade"|"ticker","symbol":[...]}}`
- **Access:** None
- **Documentation:** https://docs.kraken.com/api/docs/websocket-v2/trade (HTTP 200)
- **Terms / licence:** https://docs.kraken.com/api/docs/websocket-v2/trade (HTTP 200) — “base-ui-disable-scrollbar::-webkit-scrollbar{display:none} Trades - Kraken Developers !function(){var b=""; function a(p){if(p==null)return"/";p=""+p;if(""===p)return"/";return"/"===p”
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **Verified enrichment:** join on symbol (BTC/USD → XBTUSD) with `https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD` (HTTP 200) → median 7.0 + 25 = **32.0 attributes** after the join (verified on one event: 14 → 39) (asset-pair metadata joined to each trade/ticker; checked 2026-10-13T04:35:38Z).
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 9.47 | 568 | 60 | 7.0 | 14 | 19 |
| 2026-10-13T02:11 | ok | 7.35 | 441 | 60 | 7.0 | 14 | 19 |
| 2026-10-13T03:23 | ok | 4.38 | 263 | 60 | 7.0 | 14 | 19 |
| 2026-10-13T04:23 | ok | 2.85 | 171 | 60 | 7.0 | 14 | 19 |

<details><summary>Sample event — 14 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `symbol` | string | BTC/USD |
| 2 | `bid` | number | 82399.1 |
| 3 | `bid_qty` | number | 0.40154298 |
| 4 | `ask` | number | 82399.2 |
| 5 | `ask_qty` | number | 0.40687101 |
| 6 | `last` | number | 82399.1 |
| 7 | `volume` | number | 2569.66148165 |
| 8 | `vwap` | number | 82800.7 |
| 9 | `low` | number | 80951.2 |
| 10 | `high` | number | 84250.0 |
| 11 | `change` | number | -1191.7 |
| 12 | `change_pct` | number | -1.43 |
| 13 | `trades` | integer | 162558 |
| 14 | `timestamp` | string (date/time) | 2026-10-13T02:10:19.909591Z |

</details>

<a id="s-bitfinex"></a>
### 45. Bitfinex trades + ticker (public v2)

- **Verdict:** Rate only (needs enrichment for ≥10 attributes) — average 1.54 events/s, median 5.0 attributes per event.
- **Delivery:** live · WebSocket (JSON arrays)
- **Endpoint:** `wss://api-pub.bitfinex.com/ws/2`
- **Request:** `{"event":"subscribe","channel":"trades"|"ticker","symbol":"tBTCUSD"}`
- **Access:** None
- **Documentation:** https://docs.bitfinex.com/docs/ws-public (HTTP 200)
- **Terms / licence:** https://docs.bitfinex.com/docs/ws-public (HTTP 200) — “Public Channels {"@context":"https://schema”
- **Data shape (by attribute name):** geographic position no · time field no · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.60 | 96 | 60 | 5.0 | 11 | 15 |
| 2026-10-13T02:11 | ok | 2.47 | 148 | 60 | 5.0 | 11 | 15 |
| 2026-10-13T03:23 | ok | 1.33 | 80 | 60 | 5.0 | 11 | 15 |
| 2026-10-13T04:23 | ok | 0.75 | 45 | 60 | 5.0 | 11 | 15 |

<details><summary>Sample event — 11 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `BID` | integer | 82491 |
| 2 | `BID_SIZE` | number | 0.72583456 |
| 3 | `ASK` | integer | 82501 |
| 4 | `ASK_SIZE` | number | 0.95128019 |
| 5 | `DAILY_CHANGE` | integer | -1554 |
| 6 | `DAILY_CHANGE_RELATIVE` | number | -0.01848877 |
| 7 | `LAST_PRICE` | integer | 82497 |
| 8 | `VOLUME` | number | 378.42662028 |
| 9 | `HIGH` | integer | 84378 |
| 10 | `LOW` | integer | 81054 |
| 11 | `symbol` | string | tBTCUSD |

</details>

<a id="s-velib"></a>
### 46. Vélib' Métropole Paris bike-share station status (GBFS)

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.90 events/s, median 12.0 attributes per event.
- **Delivery:** poll · GBFS JSON over HTTPS, polled every 10 s
- **Endpoint:** `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel (HTTP 200)
- **Terms / licence:** https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel (HTTP 200) — “Licence Open Data Commons Open Database License (ODbL)”
- **Measurement note (latest representative round):** 5 polls every 10s; 1519 records per snapshot; rate = new/changed records per second
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.86 | 48 | 56 | 12.0 | 12 | 12 |
| 2026-10-13T02:11 | ok | 0.81 | 41 | 50 | 12.0 | 12 | 12 |
| 2026-10-13T03:23 | ok | 0.93 | 51 | 55 | 12.0 | 12 | 12 |
| 2026-10-13T04:23 | ok | 0.98 | 55 | 56 | 12.0 | 12 | 12 |

<details><summary>Sample event — 12 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `station_id` | integer | 213688169 |
| 2 | `num_bikes_available` | integer | 5 |
| 3 | `numBikesAvailable` | integer | 5 |
| 4 | `num_bikes_available_types` | list (serialised) | [{'mechanical': 4}, {'ebike': 1}] |
| 5 | `num_docks_available` | integer | 29 |
| 6 | `numDocksAvailable` | integer | 29 |
| 7 | `is_installed` | integer | 1 |
| 8 | `is_returning` | integer | 1 |
| 9 | `is_renting` | integer | 1 |
| 10 | `last_reported` | integer | 1791855310 |
| 11 | `stationCode` | string (numeric) | 16107 |
| 12 | `station_opening_hours` | null | null |

</details>

<a id="s-pypi"></a>
### 47. PyPI newest releases feed

- **Verdict:** Attributes only (combine to reach ≥1 event/s) — average 0.10 events/s, median 33.5 attributes per event.
- **Delivery:** batch · RSS over HTTPS (+ JSON API per release)
- **Endpoint:** `https://pypi.org/rss/updates.xml ; https://pypi.org/pypi/<name>/<version>/json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://docs.pypi.org/api/feeds/ (HTTP 200)
- **Terms / licence:** https://docs.pypi.org/api/ (HTTP 200) — “s and Datasets Introduction Introduction Table of contents API policies Caching Rate limiting API Preference Integration guide Querying PyPI for Package URLs Official guidance Predictable URLs Index API JSON API Upload API Integrity API Stats API Big”
- **Measurement note (latest representative round):** RSS shows the latest 100 releases (5 raw fields); attributes counted on the per-release JSON enrichment (info.*)
- **Data shape (by attribute name):** geographic position no · time field no · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.10 | 100 | 1,001 | 33.0 | 33 | 33 |
| 2026-10-13T02:11 | ok | 0.09 | 100 | 1,055 | 32.0 | 32 | 32 |
| 2026-10-13T03:23 | ok | 0.10 | 100 | 1,005 | 34.0 | 34 | 34 |
| 2026-10-13T04:23 | ok | 0.10 | 100 | 990 | 34.0 | 34 | 34 |

<details><summary>Sample event — 34 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `author` | string | bissli |
| 2 | `author_email` | null | null |
| 3 | `bugtrack_url` | null | null |
| 4 | `classifiers` | string | ['Development Status :: 5 - Production/Stable', 'Environment :: Console', 'Intended Audie… |
| 5 | `description` | string | # memman  **Persistent memory for Claude Code and Codex.**  memman saves decisions, prefe… |
| 6 | `description_content_type` | string | text/markdown |
| 7 | `docs_url` | null | null |
| 8 | `download_url` | null | null |
| 9 | `downloads.last_day` | integer | -1 |
| 10 | `downloads.last_month` | integer | -1 |
| 11 | `downloads.last_week` | integer | -1 |
| 12 | `dynamic` | null | null |
| 13 | `home_page` | null | null |
| 14 | `keywords` | string | ai, ai-agents, agent-memory, agents, llm, memory, long-term-memory, rag, embeddings, vect… |
| 15 | `license` | string | MIT |
| 16 | `license_expression` | null | null |
| 17 | `license_files` | list (serialised) | ['LICENSE'] |
| 18 | `maintainer` | null | null |
| 19 | `maintainer_email` | null | null |
| 20 | `name` | string | memman |
| 21 | `package_url` | string | https://pypi.org/project/memman/ |
| 22 | `platform` | null | null |
| 23 | `project_url` | string | https://pypi.org/project/memman/ |
| 24 | `project_urls.Documentation` | string | https://github.com/bissli/memman/blob/master/docs/DESIGN.md |
| 25 | `project_urls.Homepage` | string | https://github.com/bissli/memman |
| 26 | `project_urls.Repository` | string | https://github.com/bissli/memman |
| 27 | `provides_extra` | list (serialised) | ['postgres'] |
| 28 | `release_url` | string | https://pypi.org/project/memman/0.50.0/ |
| 29 | `requires_dist` | string | ['click<9.0,>=8.1', 'httpx<0.28,>=0.27', 'numpy<3,>=1.26', 'pgvector<0.6,>=0.3; extra == … |
| 30 | `requires_python` | string | <4.0,>=3.11 |
| 31 | `summary` | string | LLM-supervised persistent memory for Claude Code and Codex - fused keyword, vector and re… |
| 32 | `version` | string | 0.50.0 |
| 33 | `yanked` | boolean | false |
| 34 | `yanked_reason` | null | null |

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
- **Data shape (by attribute name):** geographic position yes · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |
| 2026-10-13T02:11 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |
| 2026-10-13T03:23 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |
| 2026-10-13T04:23 | ok | 0.15 | 91,305 | 604,800 | 196.0 | 196 | 196 |

<details><summary>Sample event — 196 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `run_accession` | string | ERR18022750 |
| 2 | `experiment_title` | string | Revio sequencing |
| 3 | `sample_accession` | string | SAMEA123079245 |
| 4 | `project_name` | string |  |
| 5 | `submission_accession` | string | ERA37358500 |
| 6 | `library_min_fragment_size` | string |  |
| 7 | `bam_md5` | string |  |
| 8 | `assembly_software` | string |  |
| 9 | `library_prep_longitude` | string |  |
| 10 | `library_selection` | string | RANDOM |
| 11 | `pcr_isolation_protocol` | string |  |
| 12 | `chip_protocol` | string |  |
| 13 | `sequencing_primer_provider` | string |  |
| 14 | `serotype` | string |  |
| 15 | `environment_feature` | string | ENVO:01000407 |
| 16 | `last_updated` | string | 2026-10-11 |
| 17 | `submitted_galaxy` | string | ftp.sra.ebi.ac.uk/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| 18 | `extraction_protocol` | string |  |
| 19 | `germline` | string |  |
| 20 | `secondary_project` | string |  |
| 21 | `culture_collection` | string |  |
| 22 | `submission_tool` | string |  |
| 23 | `sra_bytes` | string |  |
| 24 | `read_strand` | string |  |
| 25 | `rna_purity_280_ratio` | string |  |
| 26 | `hi_c_protocol` | string |  |
| 27 | `collected_by` | string |  |
| 28 | `submitted_ftp` | string | ftp.sra.ebi.ac.uk/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| 29 | `restriction_enzyme_target_sequence` | string |  |
| 30 | `isolate` | string |  |
| 31 | `fastq_bytes` | string |  |
| 32 | `instrument_platform` | string | PACBIO_SMRT |
| 33 | `variety` | string |  |
| 34 | `sra_file_role` | string |  |
| 35 | `sequencing_date_format` | string |  |
| 36 | `temperature` | string |  |
| 37 | `sra_aspera` | string |  |
| 38 | `ecotype` | string |  |
| 39 | `submitted_aspera` | string | fasp.sra.ebi.ac.uk:/vol1/run/ERR180/ERR18022750/5482.fastq.gz |
| 40 | `sampling_campaign` | string |  |
| 41 | `bam_ftp` | string |  |
| 42 | `tissue_lib` | string |  |
| 43 | `environmental_sample` | string |  |
| 44 | `control_experiment` | string |  |
| 45 | `sex` | string |  |
| 46 | `submitted_md5` | string | b81ad61ab20a36538b9396e8331a0ae8 |
| 47 | `checklist` | string | ERC000024 |
| 48 | `fastq_galaxy` | string |  |
| 49 | `library_gen_protocol` | string |  |
| 50 | `specimen_voucher` | string |  |
| 51 | `library_prep_latitude` | string |  |
| 52 | `submitted_bytes` | string (numeric) | 3508305175 |
| 53 | `taxonomic_identity_marker` | string |  |
| 54 | `run_date` | string |  |
| 55 | `country` | string | USA |
| 56 | `ncbi_reporting_standard` | string |  |
| 57 | `sample_description` | string |  |
| 58 | `sra_galaxy` | string |  |
| 59 | `sample_prep_interval` | string |  |
| 60 | `fastq_md5` | string |  |
| 61 | `secondary_study_accession` | string | ERP201065 |
| 62 | `experimental_protocol` | string |  |
| 63 | `read_count` | string (numeric) | 0 |
| 64 | `study_title` | string | EDNAID metagenomic study |
| 65 | `bio_material` | string |  |
| 66 | `fastq_file_role` | string |  |
| 67 | `rna_prep_5_protocol` | string |  |
| 68 | `host_body_site` | string |  |
| 69 | `local_environmental_context` | string | ENVO:01000407 |
| 70 | `assembly_quality` | string |  |
| 71 | `collection_date_end` | string | 2026-04-16 |
| 72 | `sample_capture_status` | string |  |
| 73 | `sample_title` | string |  |
| 74 | `host_genotype` | string |  |
| 75 | `host_phenotype` | string |  |
| 76 | `environmental_medium` | string | ENVO:00002149 |
| 77 | `cultivar` | string |  |
| 78 | `instrument_model` | string | Revio |
| 79 | `faang_library_selection` | string |  |
| 80 | `target_gene` | string |  |
| 81 | `bam_bytes` | string |  |
| 82 | `library_max_fragment_size` | string |  |
| 83 | `experiment_target` | string |  |
| 84 | `sequencing_date` | string |  |
| 85 | `description` | string | Revio sequencing |
| 86 | `bam_file_role` | string |  |
| 87 | `nominal_sdev` | string |  |
| 88 | `chip_ab_provider` | string |  |
| 89 | `environment_material` | string | ENVO:00002149 |
| 90 | `host_tax_id` | string |  |
| 91 | `sample_material` | string |  |
| 92 | `sample_storage_processing` | string |  |
| 93 | `sra_md5` | string |  |
| 94 | `cell_type` | string |  |
| 95 | `fastq_ftp` | string |  |
| 96 | `disease` | string |  |
| 97 | `sample_prep_interval_units` | string |  |
| 98 | `broker_name` | string |  |
| 99 | `sub_strain` | string |  |
| 100 | `base_count` | string (numeric) | 0 |
| 101 | `library_strategy` | string | WGS |
| 102 | `restriction_site` | string |  |
| 103 | `serovar` | string |  |
| 104 | `investigation_type` | string |  |
| 105 | `location` | string | 32.8634 N 117.2546 W |
| 106 | `library_source` | string | METAGENOMIC |
| 107 | `sra_ftp` | string |  |
| 108 | `age` | string |  |
| 109 | `library_layout` | string | PAIRED |
| 110 | `experimental_factor` | string |  |
| 111 | `sequencing_primer_catalog` | string |  |
| 112 | `environment_biome` | string | ENVO:00000447 |
| 113 | `rna_purity_230_ratio` | string |  |
| 114 | `dnase_protocol` | string |  |
| 115 | `dev_stage` | string |  |
| 116 | `library_prep_date_format` | string |  |
| 117 | `bam_aspera` | string |  |
| 118 | `binning_software` | string |  |
| 119 | `datahub` | string | dcc_metagenome |
| 120 | `rna_integrity_num` | string |  |
| 121 | `library_prep_date` | string |  |
| 122 | `location_start` | string | 32.8634 N 117.2546 W |
| 123 | `marine_region` | string |  |
| 124 | `aligned` | string |  |
| 125 | `file_location` | string |  |
| 126 | `sample_collection` | string |  |
| 127 | `chip_target` | string |  |
| 128 | `nominal_length` | string |  |
| 129 | `broad_scale_environmental_context` | string | ENVO:00000447 |
| 130 | `sequencing_location` | string |  |
| 131 | `status` | string | public |
| 132 | `completeness_score` | string |  |
| 133 | `lon` | string (numeric) | -117.2546 |
| 134 | `fastq_aspera` | string |  |
| 135 | `tax_lineage` | string | 1;2787823;12908;408169;410657;1561972 |
| 136 | `host_sex` | string |  |
| 137 | `library_pcr_isolation_protocol` | string |  |
| 138 | `sample_alias` | string (numeric) | 3281 |
| 139 | `mating_type` | string |  |
| 140 | `collection_date_start` | string | 2026-04-15 |
| 141 | `sub_species` | string |  |
| 142 | `contamination_score` | string |  |
| 143 | `run_alias` | string | run-5482 |
| 144 | `restriction_enzyme` | string |  |
| 145 | `depth` | string (numeric) | 0.5 |
| 146 | `submitted_file_role` | string | SUBMISSION_FILE |
| 147 | `submitted_read_type` | string | PAIRED |
| 148 | `library_construction_protocol` | string |  |
| 149 | `host_growth_conditions` | string |  |
| 150 | `collection_date` | string | 2026-04-16 |
| 151 | `experiment_alias` | string (numeric) | 30481 |
| 152 | `host_gravidity` | string |  |
| 153 | `center_name` | string | University of California San Diego Microbiome Initiative;UCSDMI |
| 154 | `identified_by` | string |  |
| 155 | `cell_line` | string |  |
| 156 | `sampling_site` | string |  |
| 157 | `host` | string |  |
| 158 | `library_name` | string |  |
| 159 | `tag` | string | env_tax:marine;env_geo;env_geo:coastal;env_geo:terrestrial;env_tax |
| 160 | `first_created` | string | 2026-10-06 |
| 161 | `lat` | string (numeric) | 32.8634 |
| 162 | `strain` | string |  |
| 163 | `experiment_accession` | string | ERX17413712 |
| 164 | `scientific_name` | string | seawater metagenome |
| 165 | `host_status` | string |  |
| 166 | `tax_id` | string (numeric) | 1561972 |
| 167 | `study_accession` | string | PRJEB120985 |
| 168 | `submitted_format` | string | FASTQ |
| 169 | `submitted_host_sex` | string |  |
| 170 | `surveillance_target` | string |  |
| 171 | `bisulfite_protocol` | string |  |
| 172 | `altitude` | string |  |
| 173 | `rt_prep_protocol` | string |  |
| 174 | `host_scientific_name` | string |  |
| 175 | `bam_galaxy` | string |  |
| 176 | `accession` | string | ERR18022750 |
| 177 | `secondary_sample_accession` | string | ERS30780806 |
| 178 | `sample_storage` | string |  |
| 179 | `cage_protocol` | string |  |
| 180 | `sampling_platform` | string |  |
| 181 | `taxonomic_classification` | string |  |
| 182 | `location_end` | string | 32.8634 N 117.2546 W |
| 183 | `protocol_label` | string |  |
| 184 | `elevation` | string |  |
| 185 | `salinity` | string |  |
| 186 | `sequencing_method` | string |  |
| 187 | `sequencing_primer_lot` | string |  |
| 188 | `first_public` | string | 2026-10-11 |
| 189 | `transposase_protocol` | string |  |
| 190 | `study_alias` | string (numeric) | 25006 |
| 191 | `library_prep_location` | string |  |
| 192 | `rna_prep_3_protocol` | string |  |
| 193 | `ph` | string |  |
| 194 | `sequencing_longitude` | string |  |
| 195 | `tissue_type` | string |  |
| 196 | `isolation_source` | string |  |

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
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.17 | 10 | 60 | 22.0 | 22 | 24 |
| 2026-10-13T02:11 | ok | 0.17 | 10 | 60 | 22.0 | 24 | 24 |
| 2026-10-13T03:23 | ok | 0.17 | 10 | 60 | 17.0 | 22 | 25 |
| 2026-10-13T04:23 | ok | 0.17 | 10 | 60 | 22.0 | 22 | 24 |

<details><summary>Sample event — 24 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `_links.self.href` | string | https://horizon.stellar.org/operations/278804997406212097 |
| 2 | `_links.transaction.href` | string | https://horizon.stellar.org/transactions/7e0e234cb85de906bcab19b1dcb0e2485c86de85ec8054fc… |
| 3 | `_links.effects.href` | string | https://horizon.stellar.org/operations/278804997406212097/effects |
| 4 | `_links.succeeds.href` | string | https://horizon.stellar.org/effects?order=desc&cursor=278804997406212097 |
| 5 | `_links.precedes.href` | string | https://horizon.stellar.org/effects?order=asc&cursor=278804997406212097 |
| 6 | `id` | string (numeric) | 278804997406212097 |
| 7 | `paging_token` | string (numeric) | 278804997406212097 |
| 8 | `transaction_successful` | boolean | true |
| 9 | `source_account` | string | GAPLYDVLMPHXGWPXHTSWUKG7R5FVVXNRXHDPMDVADJTPNSGOR7HRVYJD |
| 10 | `type` | string | manage_sell_offer |
| 11 | `type_i` | integer | 3 |
| 12 | `created_at` | string (date/time) | 2026-10-13T02:11:57Z |
| 13 | `transaction_hash` | string | 7e0e234cb85de906bcab19b1dcb0e2485c86de85ec8054fc19a9beacd545f1bf |
| 14 | `amount` | string (numeric) | 0.1911935 |
| 15 | `price` | string (numeric) | 1.0000944 |
| 16 | `price_r.n` | integer | 125011800 |
| 17 | `price_r.d` | integer | 125000000 |
| 18 | `buying_asset_type` | string | credit_alphanum12 |
| 19 | `buying_asset_code` | string | PYUSD |
| 20 | `buying_asset_issuer` | string | GDQE7IXJ4HUHV6RQHIUPRJSEZE4DRS5WY577O2FY6YQ5LVWZ7JZTU2V5 |
| 21 | `selling_asset_type` | string | credit_alphanum4 |
| 22 | `selling_asset_code` | string | USDC |
| 23 | `selling_asset_issuer` | string | GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN |
| 24 | `offer_id` | string (numeric) | 1861295388 |

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
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.05 | 3 | 56 | 44.0 | 48 | 48 |
| 2026-10-13T02:11 | ok | 0.06 | 3 | 50 | 44.0 | 47 | 48 |
| 2026-10-13T03:23 | idle | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | idle | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T03:23 idle: 2 games scheduled, none live at sampling time; 2026-10-13T04:23 idle: 2 games scheduled, none live at sampling time

<details><summary>Sample event — 48 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `result.type` | string | atBat |
| 2 | `result.event` | string | Flyout |
| 3 | `result.eventType` | string | field_out |
| 4 | `result.description` | string | Jonathan Aranda flies out sharply to center fielder Steven Kwan. |
| 5 | `result.rbi` | integer | 0 |
| 6 | `result.awayScore` | integer | 2 |
| 7 | `result.homeScore` | integer | 2 |
| 8 | `result.isOut` | boolean | true |
| 9 | `about.atBatIndex` | integer | 56 |
| 10 | `about.halfInning` | string | bottom |
| 11 | `about.isTopInning` | boolean | false |
| 12 | `about.inning` | integer | 7 |
| 13 | `about.startTime` | string (date/time) | 2026-10-13T02:09:31.364Z |
| 14 | `about.endTime` | string (date/time) | 2026-10-13T02:10:46.864Z |
| 15 | `about.isComplete` | boolean | true |
| 16 | `about.isScoringPlay` | boolean | false |
| 17 | `about.hasReview` | boolean | false |
| 18 | `about.hasOut` | boolean | true |
| 19 | `about.captivatingIndex` | integer | 0 |
| 20 | `count.balls` | integer | 1 |
| 21 | `count.strikes` | integer | 1 |
| 22 | `count.outs` | integer | 2 |
| 23 | `matchup.batter.id` | integer | 666018 |
| 24 | `matchup.batter.fullName` | string | Jonathan Aranda |
| 25 | `matchup.batter.link` | string | /api/v1/people/666018 |
| 26 | `matchup.batSide.code` | string | L |
| 27 | `matchup.batSide.description` | string | Left |
| 28 | `matchup.pitcher.id` | integer | 683769 |
| 29 | `matchup.pitcher.fullName` | string | Hunter Gaddis |
| 30 | `matchup.pitcher.link` | string | /api/v1/people/683769 |
| 31 | `matchup.pitchHand.code` | string | R |
| 32 | `matchup.pitchHand.description` | string | Right |
| 33 | `matchup.postOnFirst.id` | integer | 650490 |
| 34 | `matchup.postOnFirst.fullName` | string | Yandy Díaz |
| 35 | `matchup.postOnFirst.link` | string | /api/v1/people/650490 |
| 36 | `matchup.batterHotColdZoneStats.stats` | string | [{'type': {'displayName': 'hotColdZones'}, 'group': {'displayName': 'hitting'}, 'exemptio… |
| 37 | `matchup.batterHotColdZones` | string | [{'zone': '01', 'color': 'rgba(255, 255, 255, 0.55)', 'temp': 'lukewarm', 'value': '-'}, … |
| 38 | `matchup.pitcherHotColdZones` | list (serialised) | [] |
| 39 | `matchup.splits.batter` | string | vs_RHP |
| 40 | `matchup.splits.pitcher` | string | vs_LHB |
| 41 | `matchup.splits.menOnBase` | string | Men_On |
| 42 | `pitchIndex` | list (serialised) | [0, 1, 2] |
| 43 | `actionIndex` | list (serialised) | [] |
| 44 | `runnerIndex` | list (serialised) | [0] |
| 45 | `runners` | string | [{'movement': {'originBase': None, 'start': None, 'end': None, 'outBase': '1B', 'isOut': … |
| 46 | `playEvents` | string | [{'details': {'call': {'code': 'S', 'description': 'Swinging Strike'}, 'description': 'Sw… |
| 47 | `playEndTime` | string (date/time) | 2026-10-13T02:10:46.864Z |
| 48 | `atBatIndex` | integer | 56 |

</details>

<a id="s-hn"></a>
### 51. Hacker News items (Firebase API)

- **Verdict:** Neither — average 0.11 events/s, median 6.0 attributes per event.
- **Delivery:** counter · REST JSON (also Firebase SSE)
- **Endpoint:** `https://hacker-news.firebaseio.com/v0/maxitem.json ; /v0/item/<id>.json`
- **Request:** `GET`
- **Access:** None
- **Documentation:** https://github.com/HackerNews/API (HTTP 200)
- **Terms / licence:** https://github.com/HackerNews/API (HTTP 200) — “There is currently no rate limit”
- **Measurement note (latest representative round):** item ids allocated over the window
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.20 | 13 | 64 | 6.0 | 6 | 6 |
| 2026-10-13T02:11 | ok | 0.12 | 8 | 65 | 6.0 | 6 | 6 |
| 2026-10-13T03:23 | ok | 0.08 | 5 | 60 | 6.0 | 6 | 6 |
| 2026-10-13T04:23 | ok | 0.02 | 1 | 60 | 6.0 | 6 | 6 |

<details><summary>Sample event — 6 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `by` | string (redacted) | ‹redacted› |
| 2 | `id` | integer | 50065731 |
| 3 | `parent` | integer | 50059122 |
| 4 | `text` | string (redacted) | ‹redacted› |
| 5 | `time` | integer | 1791857454 |
| 6 | `type` | string | comment |

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
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T02:11 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T04:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |

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
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Finance & blockchain

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T02:11 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T03:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |
| 2026-10-13T04:23 | ok | 0.00 | 0 | 60 | 0.0 | 0 | 0 |

No event was received, so no sample is available.

<a id="s-nostr"></a>
### 54. Nostr public notes (kind 1) across 4 relays

- **Verdict:** Neither — average 0.76 events/s, median 7.0 attributes per event.
- **Delivery:** live · WebSocket (NIP-01)
- **Endpoint:** `wss://nos.lol, wss://relay.primal.net, wss://relay.damus.io, wss://nostr.mom`
- **Request:** `["REQ","sub",{"kinds":[1],"since":<now>}]`
- **Access:** None
- **Documentation:** https://github.com/nostr-protocol/nips/blob/master/01.md (HTTP 200)
- **Terms / licence:** https://github.com/nostr-protocol/nips/blob/master/01.md (HTTP 200) — “inds"},{"level":2,"text":"Communication between clients and relays","anchor":"communication-between-clients-and-relays","htmlText":"Communication between clients and relays"},{"level":3”
- **Measurement note (latest representative round):** kind-1 notes deduplicated by id across relays that accepted the connection: wss://relay.damus.io, wss://nos.lol, wss://relay.primal.net, wss://nostr.mom
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects no
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | ok | 1.00 | 60 | 60 | 7.0 | 7 | 7 |
| 2026-10-13T02:11 | ok | 0.63 | 38 | 60 | 7.0 | 7 | 7 |
| 2026-10-13T03:23 | ok | 0.77 | 46 | 60 | 7.0 | 7 | 7 |
| 2026-10-13T04:23 | ok | 0.65 | 39 | 60 | 7.0 | 7 | 7 |

<details><summary>Sample event — 7 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `content` | string (redacted) | ‹redacted› |
| 2 | `created_at` | integer | 1791857418 |
| 3 | `id` | string (redacted) | ‹redacted› |
| 4 | `kind` | integer | 1 |
| 5 | `pubkey` | string (redacted) | ‹redacted› |
| 6 | `sig` | string (redacted) | ‹redacted› |
| 7 | `tags` | string (redacted) | ‹redacted› |

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
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | error | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''; 2026-10-13T03:23 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''; 2026-10-13T04:23 error:  'HTTP 406 b\'{"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"version":"1.0"}}\''

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
- **In the Bytewax list:** yes (kystverket.no) · **Mexican data or provider:** no · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | error | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | error | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 error:  TimeoutError('timed out'); 2026-10-13T03:23 error:  TimeoutError('timed out'); 2026-10-13T04:23 error:  TimeoutError('timed out')

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
- **In the Bytewax list:** no · **Mexican data or provider:** yes · **Category:** Transport

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'; 2026-10-13T03:23 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'; 2026-10-13T04:23 rejected: HTTP 403: b'{"error": "Please contact us at contact@airplanes.live. Your email MUST include any links, a description of the project, and any information you deem appropriate."}'

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
- **Data shape (by attribute name):** geographic position no · time field yes · nested objects yes
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Internet & software

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | limited | — | 100 | — | 18.0 | 123 | 133 |
| 2026-10-13T02:11 | limited | — | 100 | — | 18.0 | 113 | 152 |
| 2026-10-13T03:23 | limited | — | 100 | — | 18.0 | 24 | 28 |
| 2026-10-13T04:23 | limited | — | 100 | — | 18.0 | 81 | 91 |

Non-OK rounds: 2026-10-13T02:11 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token; 2026-10-13T03:23 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token; 2026-10-13T04:23 limited: HTTP 200; unauthenticated limit 60 requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token

<details><summary>Sample event — 81 attributes (values truncated to 90 characters; type observed in the sample value)</summary>

| # | Attribute | Observed type | Example value |
|---:|---|---|---|
| 1 | `id` | string (numeric) | 17066343840 |
| 2 | `type` | string | PullRequestReviewCommentEvent |
| 3 | `actor.id` | string (redacted) | ‹redacted› |
| 4 | `actor.login` | string (redacted) | ‹redacted› |
| 5 | `actor.display_login` | string (redacted) | ‹redacted› |
| 6 | `actor.gravatar_id` | string (redacted) | ‹redacted› |
| 7 | `actor.url` | string (redacted) | ‹redacted› |
| 8 | `actor.avatar_url` | string (redacted) | ‹redacted› |
| 9 | `repo.id` | integer | 1413549354 |
| 10 | `repo.name` | string | opengeos/RustGIS |
| 11 | `repo.url` | string | https://api.github.com/repos/opengeos/RustGIS |
| 12 | `payload.action` | string (redacted) | ‹redacted› |
| 13 | `payload.comment.url` | string (redacted) | ‹redacted› |
| 14 | `payload.comment.pull_request_review_id` | string (redacted) | ‹redacted› |
| 15 | `payload.comment.id` | string (redacted) | ‹redacted› |
| 16 | `payload.comment.node_id` | string (redacted) | ‹redacted› |
| 17 | `payload.comment.diff_hunk` | string (redacted) | ‹redacted› |
| 18 | `payload.comment.path` | string (redacted) | ‹redacted› |
| 19 | `payload.comment.commit_id` | string (redacted) | ‹redacted› |
| 20 | `payload.comment.original_commit_id` | string (redacted) | ‹redacted› |
| 21 | `payload.comment.user.login` | string (redacted) | ‹redacted› |
| 22 | `payload.comment.user.id` | string (redacted) | ‹redacted› |
| 23 | `payload.comment.user.node_id` | string (redacted) | ‹redacted› |
| 24 | `payload.comment.user.avatar_url` | string (redacted) | ‹redacted› |
| 25 | `payload.comment.user.gravatar_id` | string (redacted) | ‹redacted› |
| 26 | `payload.comment.user.url` | string (redacted) | ‹redacted› |
| 27 | `payload.comment.user.html_url` | string (redacted) | ‹redacted› |
| 28 | `payload.comment.user.followers_url` | string (redacted) | ‹redacted› |
| 29 | `payload.comment.user.following_url` | string (redacted) | ‹redacted› |
| 30 | `payload.comment.user.gists_url` | string (redacted) | ‹redacted› |
| 31 | `payload.comment.user.starred_url` | string (redacted) | ‹redacted› |
| 32 | `payload.comment.user.subscriptions_url` | string (redacted) | ‹redacted› |
| 33 | `payload.comment.user.organizations_url` | string (redacted) | ‹redacted› |
| 34 | `payload.comment.user.repos_url` | string (redacted) | ‹redacted› |
| 35 | `payload.comment.user.events_url` | string (redacted) | ‹redacted› |
| 36 | `payload.comment.user.received_events_url` | string (redacted) | ‹redacted› |
| 37 | `payload.comment.user.type` | string (redacted) | ‹redacted› |
| 38 | `payload.comment.user.user_view_type` | string (redacted) | ‹redacted› |
| 39 | `payload.comment.user.site_admin` | string (redacted) | ‹redacted› |
| 40 | `payload.comment.body` | string (redacted) | ‹redacted› |
| 41 | `payload.comment.created_at` | string (redacted) | ‹redacted› |
| 42 | `payload.comment.updated_at` | string (redacted) | ‹redacted› |
| 43 | `payload.comment.html_url` | string (redacted) | ‹redacted› |
| 44 | `payload.comment.pull_request_url` | string (redacted) | ‹redacted› |
| 45 | `payload.comment._links.self.href` | string (redacted) | ‹redacted› |
| 46 | `payload.comment._links.html.href` | string (redacted) | ‹redacted› |
| 47 | `payload.comment._links.pull_request.href` | string (redacted) | ‹redacted› |
| 48 | `payload.comment.reactions.url` | string (redacted) | ‹redacted› |
| 49 | `payload.comment.reactions.total_count` | string (redacted) | ‹redacted› |
| 50 | `payload.comment.reactions.+1` | string (redacted) | ‹redacted› |
| 51 | `payload.comment.reactions.-1` | string (redacted) | ‹redacted› |
| 52 | `payload.comment.reactions.laugh` | string (redacted) | ‹redacted› |
| 53 | `payload.comment.reactions.hooray` | string (redacted) | ‹redacted› |
| 54 | `payload.comment.reactions.confused` | string (redacted) | ‹redacted› |
| 55 | `payload.comment.reactions.heart` | string (redacted) | ‹redacted› |
| 56 | `payload.comment.reactions.rocket` | string (redacted) | ‹redacted› |
| 57 | `payload.comment.reactions.eyes` | string (redacted) | ‹redacted› |
| 58 | `payload.comment.in_reply_to_id` | string (redacted) | ‹redacted› |
| 59 | `payload.comment.original_position` | string (redacted) | ‹redacted› |
| 60 | `payload.comment.position` | string (redacted) | ‹redacted› |
| 61 | `payload.comment.subject_type` | string (redacted) | ‹redacted› |
| 62 | `payload.pull_request.url` | string (redacted) | ‹redacted› |
| 63 | `payload.pull_request.id` | string (redacted) | ‹redacted› |
| 64 | `payload.pull_request.number` | string (redacted) | ‹redacted› |
| 65 | `payload.pull_request.head.ref` | string (redacted) | ‹redacted› |
| 66 | `payload.pull_request.head.sha` | string (redacted) | ‹redacted› |
| 67 | `payload.pull_request.head.repo.id` | string (redacted) | ‹redacted› |
| 68 | `payload.pull_request.head.repo.url` | string (redacted) | ‹redacted› |
| 69 | `payload.pull_request.head.repo.name` | string (redacted) | ‹redacted› |
| 70 | `payload.pull_request.base.ref` | string (redacted) | ‹redacted› |
| 71 | `payload.pull_request.base.sha` | string (redacted) | ‹redacted› |
| 72 | `payload.pull_request.base.repo.id` | string (redacted) | ‹redacted› |
| 73 | `payload.pull_request.base.repo.url` | string (redacted) | ‹redacted› |
| 74 | `payload.pull_request.base.repo.name` | string (redacted) | ‹redacted› |
| 75 | `public` | boolean | true |
| 76 | `created_at` | string (date/time) | 2026-10-13T04:18:39Z |
| 77 | `org.id` | integer | 129896036 |
| 78 | `org.login` | string | opengeos |
| 79 | `org.gravatar_id` | string |  |
| 80 | `org.url` | string | https://api.github.com/orgs/opengeos |
| 81 | `org.avatar_url` | string | https://avatars.githubusercontent.com/u/129896036? |

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
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Science & sensors

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…; 2026-10-13T03:23 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…; 2026-10-13T04:23 rejected: HTTP 404: b'\n<!doctype html>\n<html lang="en">\n<head>\n  <title>Not Found</title>\n</head>\n<body>\n  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>\n</body>\n</html>…

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
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | rejected | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | rejected | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 rejected: HTTP 401: b'{"error":"Missing access token"}'; 2026-10-13T03:23 rejected: HTTP 401: b'{"error":"Missing access token"}'; 2026-10-13T04:23 rejected: HTTP 401: b'{"error":"Missing access token"}'

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
- **Measurement note (latest representative round):** HTTP 200: b'[{"attackers":[{"alliance_id":99014522,"character_id":1036113213,"corporation_id":366498483,"damage_done":9204,"final_blow":true,"security_status":0.4,"ship_type_id":12023,"weapon_type_id":3146}],"kil'
- **In the Bytewax list:** no · **Mexican data or provider:** no · **Category:** Games, media & social

| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-10-13T02:10 | reachable | — | — | — | — | 0 | 0 |
| 2026-10-13T02:11 | reachable | — | — | — | — | 0 | 0 |
| 2026-10-13T03:23 | reachable | — | — | — | — | 0 | 0 |
| 2026-10-13T04:23 | reachable | — | — | — | — | 0 | 0 |

Non-OK rounds: 2026-10-13T02:11 reachable: HTTP 200: b'[{"attackers":[{"alliance_id":99003581,"character_id":2123545746,"corporation_id":98598862,"damage_done":55548,"faction_id":500011,"final_blow":false,"security_status":5,"ship_type_id":47…; 2026-10-13T03:23 reachable: HTTP 200: b'[{"attackers":[{"corporation_id":1000125,"damage_done":2880,"final_blow":true,"security_status":0,"ship_type_id":3885}],"killmail_id":139126268,"killmail_time":"2026-10-13T03:18:31Z","sol…; 2026-10-13T04:23 reachable: HTTP 200: b'[{"attackers":[{"alliance_id":99014522,"character_id":1036113213,"corporation_id":366498483,"damage_done":9204,"final_blow":true,"security_status":0.4,"ship_type_id":12023,"weapon_type_id…

No event was received, so no sample is available.

## 10. Sources that need a free API key

A source is in **Table 10.1** only if all of the following hold on the provider's own pages: the key is obtained by a free sign-up, no paid plan or paid upgrade was found, so the free key is the complete product, and the documented limits still allow the stream to be consumed. Every API with a key states some fair-use limit; the limit is quoted rather than hidden. Sources with a paid plan, a trial-level free plan, or a free plan restricted to a subset are listed in **Table 10.2** with the clause that excludes them. Free keys that do not deliver ≥1 event/s are in **Table 10.3**. aisstream.io (free key) is not repeated because the project document already lists it.

Evidence: 61 verbatim clauses were re-fetched from the providers' pages when this report was generated; 61 were found word for word (✅), 0 were not (❌, see the per-row status). “None found” for paid plans means no paid plan appeared on the pages checked — not a guarantee that none exists. Every sign-up link was fetched too (HTTP status shown next to it). Endpoints were probed without a key: an HTTP 401/403/400 “key missing” answer proves the endpoint is live and that the key is what gates it.

Measured rates use the keyless route of the same provider where one exists (FIRMS public 24 h files, MBTA REST without a key, TfL without a key); the other rows need the key before they can be measured.

### 10.1 Free key, no paid plan found — the free key is the full product

| # | Source | Category | How to get the key | Delivery | Documented limit | Paid plan | Measured ev/s | Attrs/event | Endpoint probe (no key) |
|---|---|---|---|---|---|---|---:|---:|---|
| K1 | [MBTA V3 API — vehicle streaming (Boston subway, bus, commuter rail, ferry)](#k-mbta_key) | Transport | [Developer account; key per app (“Getting a key might take a day”)](https://api-v3.mbta.com/register) (HTTP 200) | Server-Sent Events (Accept: text/event-stream + x-api-key) | 1,000 requests/min with key; increase on request; a streaming connection counts once | None found | 11.31 | 21 | HTTP 406: {"errors":[{"code":"not_acceptable","status":"406"}],"jsonapi":{"vers… |
| K2 | [MTA Bus Time SIRI — every New York City bus](#k-mta_bustime) | Transport | [Web form; key by e-mail (“within half an hour”)](https://register.developer.obanyc.com/) (HTTP 200) | REST JSON/XML (SIRI VehicleMonitoring), polled | No numeric limit stated on the pages checked | None found | — | — | HTTP 401: {"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-13T00:42:40.… |
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

### 10.2 Excluded — paid plan, trial-level free plan, or restricted free subset

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

### 10.3 Free key and no paid plan, but not a ≥1 event/s stream

| Source | Category | Sign-up | Why it does not qualify | Evidence (verbatim, re-verified) |
|---|---|---|---|---|
| Stack Exchange API — Stack Overflow questions/answers/comments | Internet & software | [link](https://stackapps.com/apps/oauth/register) (HTTP 200) | Free key (10,000 requests/day), but measured activity is far below 1 event/s. Measured 2026-10-13T03:32:30Z: 29 posts+comments in the last hour on Stack Overflow (0.008/s); the API's own site statistics report 2.53 questions/min and 3.77 answers/min (≈0.10/s) | ✅ “which by default is 10,000” — [https://api.stackexchange.com/docs/throttle](https://api.stackexchange.com/docs/throttle) (200) |
| Banco de México SIE API — FX FIX, rates, indicators (Mexico) | Finance & blockchain | [link](https://www.banxico.org.mx/SieAPIRest/service/v1/token) (HTTP 200) | Free token; economic time series (e.g. the daily FIX), not an event stream | ✅ “Máximo 80 consultas en 1 minuto 40,000 consultas por día” — [https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limite…](https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limiteConsultas) (200)<br>✅ “Todas las solicitudes que se realicen al API requieren enviar un token de consulta” — [https://www.banxico.org.mx/SieAPIRest/service/v1/](https://www.banxico.org.mx/SieAPIRest/service/v1/) (200) |
| US EIA Open Data — hourly electric grid monitor | Weather & environment | [link](https://www.eia.gov/opendata/register.php) (HTTP 200) | Free key; hourly aggregated series, not an event stream | ✅ “Energy Information Administration is committed to its free and open data by making it available through an Application Programming Interface (API)” — [https://www.eia.gov/opendata/](https://www.eia.gov/opendata/) (200) |
| Steam Web API | Games, media & social | [link](https://steamcommunity.com/dev/apikey) (HTTP 200) | Free key; request/response lookups, no public event stream | ✅ “Valve makes the Steam Web API available free” — [https://steamcommunity.com/dev/apiterms](https://steamcommunity.com/dev/apiterms) (200) |

### 10.4 Detail of Table 10.1

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
- **Probe without key:** HTTP 401 — `{"Siri":{"ServiceDelivery":{"ResponseTimestamp":"2026-10-13T00:42:40.254-04:00","VehicleMonitoringDelivery":[{"ResponseTimestamp":"2026-10-13T00:42:40.254-04:00","ErrorCondition":{"OtherError":{"Erro…`
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
- **Probe without key:** HTTP 200 — `[{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities","id":"1723383418","operationType":1,"vehicleId":"203","naptanId":"940GZZLUBNK","stationName":"Bank Underground Stat…`
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
- **Probe without key:** HTTP 401 — `<?xml version="1.0" encoding="UTF-8"?> <Acknowledgement_MarketDocument 	xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0"> 	<mRID>5c53fb1c-1472-4</mRID> 	<createdDateTime>2026-10-13…`
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

## 11. Sources excluded because the project document already lists them

Not probed, by the scope of the request (new sources only): Bluesky Jetstream; Wikimedia EventStreams (recentchange); GDELT; Binance; mempool.space (Bitcoin); aisstream.io; OpenSky Network; Bytewax awesome-public-real-time-datasets list (linked).

## 12. Limitations

- Rates come from 4 sampling rounds of about one minute each; event rates of transport, chat and market streams follow local time of day, which is why the spread is reported.
- Polled sources count changed records between polls; a faster poll interval can raise the observed rate up to each provider's limit (adsb.lol answered HTTP 429 at a 5 s interval and is therefore polled every 15 s).
- Attribute counts are on the raw event as delivered; several sources reach ≥10 attributes only after decoding (Certificate Transparency X.509, OpenStreetMap tags) or a join with static metadata (Digitraffic road sensors, GBFS station information) — this is stated per source.
- Licence excerpts are only what the linked page states; a source without an excerpt still needs a manual terms review before students rely on it.
- Access was tested from one host (the course workstation, one public IP address); some providers restrict by region or by client, so results from other networks can differ.
- Rounds follow wall-clock hourly targets; when the sampling host was suspended (2026-10-13 02:13–03:08 UTC) the missed hour is absent, never interpolated. The table header lists exactly which rounds exist.
- Bytewax overlap is a domain match; a related service can still appear in that list under another domain (for example Certstream, which redistributes the same Certificate Transparency logs read directly here).
- Enrichment joins were each verified on one real event; a production consumer must handle keys missing from the metadata (for example a stop id absent from the static GTFS).
- Free-key sources marked “Needs key” were not measured because no key was created; their limits are quoted from the providers.
- The sampler is a research tool kept outside the repository at `/tmp/opencode/streams/`; raw per-round results are the `rounds/*.jsonl` files there, and the full tool source is in the appendices.

## 13. Reproduction

The tools live outside the repository at `/tmp/opencode/streams/` (volatile); their complete source is reproduced in Appendices A–H so the measurement can be repeated from this document alone.

```bash
mkdir -p /tmp/opencode/streams/rounds && cd /tmp/opencode/streams   # save Appendices A-H here under their file names
# one sampling round of the 61 keyless sources (60 s window each, all concurrently)
uv run --no-project --with websockets --with aiohttp --with paho-mqtt --with pyzmq --with pyais --with gtfs-realtime-bindings --with cryptography python sampler.py
bash loop.sh 23            # hourly rounds on wall-clock targets
uv run --no-project --with requests python keyed_measure.py   # keyless measurements of key-based providers
uv run --no-project --with requests python keyed_probe.py     # key-based endpoints probed without a key
uv run --no-project --with requests python enrich.py          # enrichment joins
uv run --no-project --with requests python full_report.py <output.md>   # needs meta.py and keyed_meta.py beside it
```

Environment at generation: Linux-7.1.5+kali-amd64-x86_64-with-glibc2.43, Python 3.14.8 (report generator), uv 0.13.0 (x86_64-unknown-linux-gnu). Packages resolved by uv for the measuring tools:

| Package | Version |
|---|---|
| websockets | 17.2 |
| aiohttp | 3.14.5 |
| paho-mqtt | 2.1.0 |
| pyzmq | 27.2.0 |
| pyais | 3.3.1 |
| gtfs-realtime-bindings | 3.0.0 |
| protobuf | 7.36.2 |
| cryptography | 50.0.2 |
| requests | 2.34.2 |

## Appendix A. `sampler.py`

Sampler: connects to all 61 keyless sources concurrently and writes one round. 761 lines.

````python
"""One sampling round over every candidate public data stream.

Writes one JSON line per source to rounds/round-<UTC>.jsonl.
Throwaway research tool (not part of any repository).
"""
import asyncio, json, time, socket, gzip, re, zlib, csv, struct, hashlib, statistics, sys, os
from datetime import datetime, timezone, timedelta
import aiohttp, websockets
import paho.mqtt.client as mqtt

W = int(os.environ.get("WINDOW", "60"))
UA = "ITAM-COM22102-stream-survey/0.2 (course research; contact mavasbel)"
H = {"User-Agent": UA}
ROUND_TS = datetime.now(timezone.utc)


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and v:
                out.update(flat(v, f"{p}{k}."))
            else:
                out[f"{p}{k}"] = v
    return out


class Acc:
    def __init__(self):
        self.n, self.best, self.union, self.seen, self.counts = 0, {}, set(), 0, []

    def add(self, ev):
        if not isinstance(ev, dict):
            return
        self.n += 1
        if self.seen < 1000:
            self.seen += 1
            f = flat(ev)
            self.union |= set(f)
            self.counts.append(len(f))
            if len(f) > len(self.best):
                self.best = f


def result(acc=None, rate=None, window=None, note="", status="ok", sample=None, attrs=None, union=None, n=None):
    best = sample if sample is not None else (acc.best if acc else {})
    return dict(status=status, n=n if n is not None else (acc.n if acc else None), window_s=window,
                rate=rate if rate is not None else (round(acc.n / window, 3) if acc and window else None),
                attrs_per_event=attrs if attrs is not None else len(best),
                attrs_union=union if union is not None else (len(acc.union) if acc else len(best)),
                attrs_median=(statistics.median(acc.counts) if acc and acc.counts else len(best)),
                events_inspected=(acc.seen if acc else None), keys=list(best.keys()), sample=best, note=note)


def err(e, note=""):
    return dict(status="error", rate=None, attrs_per_event=0, attrs_union=0, keys=[], sample={}, note=(note + " " + repr(e))[:400])


# ---------------------------------------------------------------- live transports
async def ws_live(url, subs, extract, headers=None, text_lines=False, ping=None):
    acc = Acc()
    async with websockets.connect(url, open_timeout=25, max_size=2**26, additional_headers=headers or {"User-Agent": UA}, ping_interval=None) as ws:
        for s in subs:
            await ws.send(s if isinstance(s, str) else json.dumps(s))
        end, lp = time.time() + W, time.time()
        while time.time() < end:
            if ping and time.time() - lp > 15:
                await ws.send(ping if isinstance(ping, str) else json.dumps(ping)); lp = time.time()
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - time.time()))
            except asyncio.TimeoutError:
                break
            parts = raw.split("\r\n") if text_lines and isinstance(raw, str) else [raw]
            for part in parts:
                if not part:
                    continue
                if text_lines:
                    m = part
                    if part.startswith("PING"):
                        await ws.send("PONG :tmi.twitch.tv")
                else:
                    try:
                        m = json.loads(part)
                    except Exception:
                        continue
                for ev in extract(m) or []:
                    acc.add(ev)
    return result(acc, window=W)


def mqtt_live(host, port, topics, transport="websockets", tls=True, path="/mqtt", unwrap=False):
    acc, st = Acc(), {"topic": None}

    def on_msg(c, u, msg):
        try:
            p = json.loads(msg.payload)
        except Exception:
            p = {"raw": msg.payload[:60].decode(errors="replace")}
        if unwrap and isinstance(p, dict) and len(p) == 1 and isinstance(next(iter(p.values())), dict):
            p = next(iter(p.values()))
        st["topic"] = st["topic"] or msg.topic
        acc.add(p if isinstance(p, dict) else {"value": p})

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport=transport)
    if transport == "websockets":
        c.ws_set_options(path=path)
    if tls:
        c.tls_set()
    c.on_message = on_msg
    c.on_connect = lambda c, u, f, rc, p=None: [c.subscribe(t) for t in topics]
    c.connect(host, port, 30); c.loop_start(); time.sleep(W); c.loop_stop(); c.disconnect()
    return result(acc, window=W, note=f"example topic: {st['topic']}")


def tcp_lines(host, port, login, parse, connect_timeout=25):
    acc = Acc()
    sk = socket.create_connection((host, port), timeout=connect_timeout)
    if login:
        sk.sendall(login)
    buf, end = b"", time.time() + W
    sk.settimeout(2)
    while time.time() < end:
        try:
            c = sk.recv(65536)
        except socket.timeout:
            continue
        if not c:
            break
        buf += c
        *lines, buf = buf.split(b"\n")
        for l in lines:
            ev = parse(l.decode(errors="replace").strip())
            if ev:
                acc.add(ev)
    sk.close()
    return result(acc, window=W)


async def sse_live(url, wanted=None, headers=None):
    acc = Acc()
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers={"Accept": "text/event-stream", **(headers or {})}, timeout=aiohttp.ClientTimeout(total=W + 30)) as r:
            if r.status != 200:
                return err(f"HTTP {r.status} {(await r.read())[:150]!r}")
            end, ev = time.time() + W, None
            async for line in r.content:
                if time.time() > end:
                    break
                line = line.decode(errors="replace").strip()
                if line.startswith("event:"):
                    ev = line[6:].strip()
                elif line.startswith("data:"):
                    try:
                        d = json.loads(line[5:])
                    except Exception:
                        continue
                    if wanted is None or ev in wanted:
                        for it in (d if isinstance(d, list) else [d]):
                            if isinstance(it, dict):
                                acc.add(it)
    return result(acc, window=W)


# ---------------------------------------------------------------- polled transports
async def change_poll(fetch, items, key, sig, interval, duration=W):
    """Count new or changed records between successive polls (records/s)."""
    acc, prev, changed, t0, polls = Acc(), None, 0, time.time(), 0
    while True:
        data = await fetch(); polls += 1
        cur = {}
        for it in items(data):
            cur[key(it)] = sig(it)
            if acc.seen < 1000:
                acc.add(it)
        if prev is not None:
            changed += sum(1 for k, v in cur.items() if prev.get(k) != v)
        prev = cur
        if time.time() - t0 + interval > duration:
            break
        await asyncio.sleep(interval)
    el = time.time() - t0
    r = result(acc, window=round(el), rate=round(changed / el, 3) if el else None, n=changed,
               note=f"{polls} polls every {interval}s; {len(prev)} records per snapshot; rate = new/changed records per second")
    return r


async def get(s, url, **kw):
    async with s.get(url, headers=kw.pop("headers", H), timeout=aiohttp.ClientTimeout(total=120), **kw) as r:
        return r.status, await r.read(), r.headers


# ---------------------------------------------------------------- extractors
def ris(m): return [m.get("data")] if isinstance(m, dict) and m.get("type") == "ris_message" else []
def atlas(m): return [m[1]] if isinstance(m, list) and m and m[0] == "atlas_result" else []
def xrpl(m):
    if isinstance(m, dict) and m.get("type") == "transaction":
        tx = dict(m.get("tx_json") or m.get("transaction") or {})
        tx.update(ledger_index=m.get("ledger_index"), validated=m.get("validated"), close_time_iso=m.get("close_time_iso"),
                  TransactionResult=(m.get("meta") or {}).get("TransactionResult"))
        return [tx]
    return []
def kraken(m): return m.get("data", []) if isinstance(m, dict) and m.get("channel") in ("trade", "ticker") and m.get("type") == "update" else []
def hyper(m): return m.get("data", []) if isinstance(m, dict) and m.get("channel") == "trades" else []
def nostr(m): return [m[2]] if isinstance(m, list) and len(m) > 2 and m[0] == "EVENT" else []
def twitch(m):
    if isinstance(m, str) and m.startswith("@") and " PRIVMSG " in m:
        tags = dict(kv.split("=", 1) for kv in m[1:].split(" ", 1)[0].split(";") if "=" in kv)
        tags["channel"] = m.split(" PRIVMSG ", 1)[1].split(" ", 1)[0]
        tags["message"] = m.split(" :", 2)[-1]
        return [tags]
    return []
def polymarket(m):
    out = []
    for e in (m if isinstance(m, list) else [m]):
        if isinstance(e, dict) and e.get("event_type") == "price_change":
            for pc in e.get("price_changes", []):
                out.append({"market": e.get("market"), "timestamp": e.get("timestamp"), "event_type": "price_change", **pc})
        elif isinstance(e, dict) and e.get("event_type") in ("last_trade_price", "tick_size_change"):
            out.append(e)
    return out
def bitso(m): return [dict(x, book=m.get("book"), type=m.get("type")) for x in m.get("payload")] if isinstance(m, dict) and isinstance(m.get("payload"), list) else []
def okx(m): return m.get("data") if isinstance(m, dict) and isinstance(m.get("data"), list) else []
def bybit(m): return [m["data"]] if isinstance(m, dict) and str(m.get("topic", "")).startswith(("tickers", "publicTrade")) and isinstance(m.get("data"), dict) else (m.get("data") if isinstance(m, dict) and str(m.get("topic", "")).startswith("publicTrade") else [])
def coinbase(m): return [m] if isinstance(m, dict) and m.get("type") in ("ticker", "match") else []
def bitstamp(m): return [m["data"]] if isinstance(m, dict) and m.get("event") == "trade" else []
def deribit(m): return [m["params"]["data"]] if isinstance(m, dict) and m.get("method") == "subscription" else []
def bitmex(m): return m.get("data", []) if isinstance(m, dict) and m.get("action") in ("insert", "update") else []
def evm(m): return [m["params"]["result"]] if isinstance(m, dict) and m.get("method") == "eth_subscription" else []
def solana(m): return [flat(m["params"]["result"])] if isinstance(m, dict) and m.get("method") == "logsNotification" else []
def gemini(m):
    if isinstance(m, dict) and m.get("type") == "update":
        return [dict(e, eventId=m.get("eventId"), timestampms=m.get("timestampms"), socket_sequence=m.get("socket_sequence")) for e in m.get("events", [])]
    return []

BFX_FIELDS = {"trades": ["ID", "MTS", "AMOUNT", "PRICE"],
              "ticker": ["BID", "BID_SIZE", "ASK", "ASK_SIZE", "DAILY_CHANGE", "DAILY_CHANGE_RELATIVE", "LAST_PRICE", "VOLUME", "HIGH", "LOW"]}
def make_bitfinex():
    chans = {}
    def ex(m):
        if isinstance(m, dict) and m.get("event") == "subscribed":
            chans[m["chanId"]] = (m["channel"], m.get("symbol")); return []
        if isinstance(m, list) and len(m) >= 2 and m[0] in chans and m[1] != "hb":
            ch, sym = chans[m[0]]
            if ch == "trades" and m[1] in ("te",) and isinstance(m[2], list):
                return [dict(zip(BFX_FIELDS["trades"], m[2]), symbol=sym)]
            if ch == "ticker" and isinstance(m[1], list):
                return [dict(zip(BFX_FIELDS["ticker"], m[1]), symbol=sym)]
        return []
    return ex


def aprs(l):
    if l.startswith("#") or ">" not in l or ":" not in l:
        return None
    head, body = l.split(":", 1); src, rest = head.split(">", 1); path = rest.split(",")
    return {"src": src, "dst": path[0], "path": ",".join(path[1:]), "type": body[:1], "body": body[1:60]}


def rbn(l):
    m = re.match(r"DX de (\S+):\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(-?\d+) dB\s+(\d+) (WPM|BPS)\s+(.+?)\s+(\d{4})Z", l)
    return dict(zip(["spotter", "freq", "dx", "mode", "snr", "speed", "unit", "type", "time"], m.groups())) if m else None


def ais(l):
    try:
        from pyais import decode
        if "!AIVDM" not in l and "!BSVDM" not in l:
            return None
        s = l[l.index("!"):]
        if s.split(",")[1] != "1":
            return None
        return {k: (v.value if hasattr(v, "value") else v) for k, v in decode(s).asdict().items()}
    except Exception:
        return None


# ---------------------------------------------------------------- bespoke probes
def decode_ct(e):
    import base64
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    leaf = base64.b64decode(e["leaf_input"]); extra = base64.b64decode(e["extra_data"])
    ts = int.from_bytes(leaf[2:10], "big"); et = int.from_bytes(leaf[10:12], "big")
    if et == 0:
        ln = int.from_bytes(leaf[12:15], "big"); der = leaf[15:15 + ln]
    else:
        ln = int.from_bytes(extra[0:3], "big"); der = extra[3:3 + ln]
    c = x509.load_der_x509_certificate(der)
    def nm(n, oid):
        v = n.get_attributes_for_oid(oid); return v[0].value if v else None
    try:
        san = c.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value.get_values_for_type(x509.DNSName)
    except Exception:
        san = []
    pk = c.public_key()
    return {"timestamp_ms": ts, "entry_type": "precert" if et == 1 else "x509", "serial": format(c.serial_number, "x"),
            "subject_cn": nm(c.subject, NameOID.COMMON_NAME), "subject_o": nm(c.subject, NameOID.ORGANIZATION_NAME),
            "issuer_cn": nm(c.issuer, NameOID.COMMON_NAME), "issuer_o": nm(c.issuer, NameOID.ORGANIZATION_NAME), "issuer_c": nm(c.issuer, NameOID.COUNTRY_NAME),
            "not_before": c.not_valid_before_utc.isoformat(), "not_after": c.not_valid_after_utc.isoformat(), "san_count": len(san), "san_first": san[0] if san else None,
            "key_type": type(pk).__name__, "key_size": getattr(pk, "key_size", None) or getattr(getattr(pk, "curve", None), "key_size", None),
            "signature_algorithm": c.signature_algorithm_oid._name, "extensions": len(c.extensions)}


async def p_nostr():
    relays = ["wss://nos.lol", "wss://relay.primal.net", "wss://relay.damus.io", "wss://nostr.mom"]
    seen, acc, ok = set(), Acc(), []
    async def one(u):
        try:
            async with websockets.connect(u, open_timeout=20, ping_interval=None) as ws:
                await ws.send(json.dumps(["REQ", "probe", {"kinds": [1], "since": int(time.time())}])); ok.append(u)
                end = time.time() + W
                while time.time() < end:
                    try:
                        m = json.loads(await asyncio.wait_for(ws.recv(), end - time.time()))
                    except asyncio.TimeoutError:
                        break
                    if isinstance(m, list) and m and m[0] == "EVENT" and m[2]["id"] not in seen:
                        seen.add(m[2]["id"]); acc.add(m[2])
        except Exception:
            pass
    await asyncio.gather(*[one(u) for u in relays])
    return result(acc, window=W, note=f"kind-1 notes deduplicated by id across relays that accepted the connection: {', '.join(ok)}")

async def p_seedlink():
    stations = [("IU", s) for s in ("ANMO", "TEIG", "HRV", "COLA", "KONO", "MAJO", "PET", "SNZO", "CTAO", "TATO", "PAB", "RSSD")]
    def run():
        sk = socket.create_connection(("rtserve.iris.washington.edu", 18000), timeout=20)
        cmd = lambda c: sk.sendall((c + "\r\n").encode())
        cmd("HELLO"); time.sleep(1); sk.recv(4096)
        for net, sta in stations:
            cmd(f"STATION {sta} {net}"); cmd("SELECT BHZ"); cmd("DATA")
        time.sleep(3); sk.settimeout(1)
        try:
            sk.recv(65536)
        except socket.timeout:
            pass
        cmd("END")
        acc, buf, end = Acc(), b"", time.time() + W
        sk.settimeout(2)
        while time.time() < end:
            try:
                c = sk.recv(65536)
            except socket.timeout:
                continue
            buf += c
            while len(buf) >= 520:
                pkt, buf = buf[:520], buf[520:]
                if pkt[:2] == b"SL":
                    h = pkt[8:]
                    acc.add(dict(seq=pkt[2:8].decode(errors="replace"), station=h[8:13].decode().strip(), location=h[13:15].decode().strip(),
                                 channel=h[15:18].decode(), network=h[18:20].decode(), year=struct.unpack(">H", h[20:22])[0],
                                 doy=struct.unpack(">H", h[22:24])[0], hour=h[24], minute=h[25], second=h[26],
                                 nsamples=struct.unpack(">H", h[30:32])[0], rate_factor=struct.unpack(">h", h[32:34])[0]))
        sk.close()
        return result(acc, window=W, note=f"{len(stations)} IU stations, channel BHZ; rate scales with stations selected (each 512-byte miniSEED record carries ~400 samples)")
    return await asyncio.to_thread(run)


async def p_albion():
    def run():
        sk = socket.create_connection(("nats.albion-online-data.com", 4222), timeout=20)
        sk.recv(4096)
        sk.sendall(b'CONNECT {"user":"public","pass":"thenewalbiondata","verbose":false,"pedantic":false}\r\nSUB marketorders.deduped 1\r\nPING\r\n')
        acc, buf, end = Acc(), b"", time.time() + W
        sk.settimeout(2)
        while time.time() < end:
            try:
                c = sk.recv(1 << 20)
            except socket.timeout:
                continue
            buf += c
            while True:
                i = buf.find(b"\r\n")
                if i < 0:
                    break
                line = buf[:i].decode(errors="replace")
                if line.startswith("MSG "):
                    size = int(line.split()[-1])
                    if len(buf) < i + 4 + size:
                        break
                    payload = buf[i + 2:i + 2 + size]; buf = buf[i + 4 + size:]
                    try:
                        d = json.loads(payload)
                        for o in (d.get("Orders") if isinstance(d, dict) and "Orders" in d else (d if isinstance(d, list) else [d])):
                            acc.add(o)
                    except Exception:
                        pass
                else:
                    if line.startswith("PING"):
                        sk.sendall(b"PONG\r\n")
                    buf = buf[i + 2:]
        sk.close()
        return result(acc, window=W, note="NATS subject marketorders.deduped (Americas server)")
    return await asyncio.to_thread(run)


async def p_ndov():
    def run():
        import zmq
        ctx = zmq.Context(); s = ctx.socket(zmq.SUB)
        s.connect("tcp://pubsub.besteffort.ndovloket.nl:7658"); s.setsockopt(zmq.SUBSCRIBE, b""); s.setsockopt(zmq.RCVTIMEO, 2000)
        acc, end = Acc(), time.time() + W
        while time.time() < end:
            try:
                parts = s.recv_multipart()
            except zmq.Again:
                continue
            try:
                x = gzip.decompress(parts[-1]).decode("utf-8", "replace")
            except Exception:
                continue
            for m in re.finditer(r"<tmi8:(ONROUTE|DEPARTURE|ARRIVAL|ONSTOP|INIT|END|OFFROUTE|DELAY)>(.*?)</tmi8:\1>", x, re.S):
                acc.add(dict(re.findall(r"<tmi8:([\w-]+)>([^<]*)</tmi8:\1>", m.group(2)), messagetype=m.group(1)))
        s.close(); ctx.term()
        return result(acc, window=W, note="KV6 vehicle-journey messages (all operators) on the best-effort ZeroMQ relay")
    return await asyncio.to_thread(run)


async def p_osm(s):
    st, b, _ = await get(s, "https://planet.openstreetmap.org/replication/minute/state.txt")
    seq = int(re.search(rb"sequenceNumber=(\d+)", b).group(1)) - 1
    p = f"{seq:09d}"
    st, b, _ = await get(s, f"https://planet.openstreetmap.org/replication/minute/{p[0:3]}/{p[3:6]}/{p[6:9]}.osc.gz")
    x = gzip.decompress(b).decode()
    acc, fixed = Acc(), 0
    for m in re.finditer(r"<(node|way|relation) ([^>]*?)(/>|>(.*?)</\1>)", x, re.S):
        if acc.seen >= 1000:
            acc.n += 1; continue
        base = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)), element=m.group(1)); fixed = max(fixed, len(base))
        tags = {f"tag:{k}": v for k, v in re.findall(r'<tag k="([^"]*)" v="([^"]*)"', m.group(4) or "")}
        acc.add({**base, **tags})
    r = result(acc, window=60, note=f"minute diff #{seq}; {fixed} fixed attributes per element + its OSM tags (tag:*), counted per event")
    return r


async def p_ct(s):
    st, b, _ = await get(s, "https://www.gstatic.com/ct/log_list/v3/log_list.json"); ll = json.loads(b)
    today = ROUND_TS.strftime("%Y-%m-%dT%H:%M:%SZ")
    logs = [l for op in ll["operators"] for l in op.get("logs", []) if "usable" in l.get("state", {})
            and l.get("temporal_interval", {}).get("start_inclusive", "") <= today < l.get("temporal_interval", {}).get("end_exclusive", "")]
    async def sth(l):
        try:
            st, b, _ = await get(s, l["url"].rstrip("/") + "/ct/v1/get-sth"); return json.loads(b)["tree_size"]
        except Exception:
            return None
    a = await asyncio.gather(*[sth(l) for l in logs]); t1 = time.time()
    await asyncio.sleep(W)
    c = await asyncio.gather(*[sth(l) for l in logs]); el = time.time() - t1
    per = {l["description"]: (y - x) for l, x, y in zip(logs, a, c) if x is not None and y is not None}
    total = sum(per.values())
    acc = Acc()
    try:
        l0 = next(l for l in logs if "Argon" in l["description"]); i0 = a[logs.index(l0)]
        st, b, _ = await get(s, l0["url"].rstrip("/") + f"/ct/v1/get-entries?start={i0 - 64}&end={i0 - 1}")
        for e in json.loads(b)["entries"]:
            d = decode_ct(e)
            if d:
                acc.add(dict(d, log=l0["description"]))
    except Exception as ex:
        acc.best = {"decode_error": repr(ex)[:120]}
    r = result(acc, window=round(el), rate=round(total / el, 3), n=total,
               note=f"{len(per)} RFC 6962 logs (static-CT logs not counted); growth over the window: " + "; ".join(f"{k}: {v}" for k, v in per.items())
               + f". Raw entry = leaf_input + extra_data (base64); attributes counted after X.509 decoding of {acc.seen} entries.")
    r["n"] = total
    return r


async def p_gbfs(s, url):
    async def fetch():
        st, b, _ = await get(s, url); return json.loads(b)
    return await change_poll(fetch, lambda d: d["data"]["stations"], lambda x: x["station_id"],
                             lambda x: (x.get("last_reported"), x.get("num_bikes_available"), x.get("num_docks_available")), 10)


async def p_adsb(s, url, interval=5):
    async def fetch():
        st, b, _ = await get(s, url)
        if st != 200:
            raise RuntimeError(f"HTTP {st} {b[:120]!r}")
        return json.loads(b)
    return await change_poll(fetch, lambda d: d.get("ac") or d.get("aircraft") or [], lambda x: x.get("hex"),
                             lambda x: (x.get("lat"), x.get("lon"), x.get("alt_baro"), x.get("gs"), x.get("track")), interval)


async def p_entur(s):
    q = "{ vehicles { vehicleId lastUpdated codespace { codespaceId } line { lineRef publicCode lineName } location { latitude longitude } bearing speed delay occupancyStatus vehicleStatus inCongestion originName destinationName serviceJourney { id } operator { operatorRef } mode } }"
    async def fetch():
        async with s.post("https://api.entur.io/realtime/v2/vehicles/graphql", json={"query": q},
                          headers={**H, "ET-Client-Name": "itam-com22102-course-survey"}, timeout=aiohttp.ClientTimeout(total=90)) as r:
            return await r.json()
    return await change_poll(fetch, lambda d: d["data"]["vehicles"], lambda x: x["vehicleId"], lambda x: x.get("lastUpdated"), 15)


async def p_gtfsrt(s, url, headers=None):
    from google.transit import gtfs_realtime_pb2
    from google.protobuf.json_format import MessageToDict
    async def fetch():
        st, b, _ = await get(s, url, headers={**H, **(headers or {})})
        if st != 200:
            raise RuntimeError(f"HTTP {st}")
        f = gtfs_realtime_pb2.FeedMessage(); f.ParseFromString(b)
        return [MessageToDict(e) for e in f.entity]
    return await change_poll(fetch, lambda d: d, lambda e: e.get("id"), lambda e: json.dumps(e, sort_keys=True), 15)


async def p_metar(s):
    st, b, _ = await get(s, "https://aviationweather.gov/data/cache/metars.cache.csv.gz")
    lines = gzip.decompress(b).decode().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("raw_text"))
    rows = list(csv.DictReader(lines[i:]))
    now = time.time()
    ts = [datetime.fromisoformat(r["observation_time"].replace("Z", "+00:00")).timestamp() for r in rows if r.get("observation_time")]
    hr = sum(1 for t in ts if now - t <= 3600)
    acc = Acc()
    for r in rows[:1000]:
        acc.add({k: v for k, v in r.items() if k})
    return result(acc, window=3600, rate=round(hr / 3600, 3), n=hr, note=f"cache file lists {len(rows)} stations; rate = observations stamped within the last hour / 3600")


async def p_usgs(s):
    st, b, _ = await get(s, "https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H&siteStatus=active")
    ts = json.loads(b)["value"]["timeSeries"]; vals = sum(len(v["values"][0]["value"]) for v in ts)
    acc = Acc()
    for v0 in ts[:300]:
        if v0["values"][0]["value"]:
            acc.add({"siteName": v0["sourceInfo"]["siteName"], **flat(v0["sourceInfo"]), **flat(v0["variable"]), **v0["values"][0]["value"][0]})
    return result(acc, window=3600, rate=round(vals / 3600, 3), n=vals, note=f"Texas only: {len(ts)} active series; nationwide is ~50x larger. Legacy service retires 2027-02-22")


async def p_sensorcomm(s):
    st, b, _ = await get(s, "https://data.sensor.community/static/v2/data.json"); j = json.loads(b)
    acc = Acc()
    for x in j[:1000]:
        x = dict(x); vals = {f"value.{v['value_type']}": v["value"] for v in x.pop("sensordatavalues", [])}
        acc.add({**x, **vals})
    return result(acc, window=300, rate=round(len(j) / 300, 3), n=len(j), note="file = last 5 minutes of all sensors; sensordatavalues expanded per value_type")


async def p_crossref(s):
    day = (ROUND_TS - timedelta(days=1)).strftime("%Y-%m-%d")
    st, b, _ = await get(s, f"https://api.crossref.org/works?filter=from-index-date:{day},until-index-date:{day}&rows=20&mailto=<masked>")
    j = json.loads(b)["message"]
    st, b2, _ = await get(s, f"https://api.crossref.org/works?filter=from-created-date:{day},until-created-date:{day}&rows=0&mailto=<masked>")
    nc = json.loads(b2)["message"]["total-results"]
    acc = Acc()
    for it in j["items"]:
        acc.add(it)
    return result(acc, window=86400, rate=round(j["total-results"] / 86400, 3), n=j["total-results"],
                  note=f"{day}: {j['total-results']} records (re)indexed, of which {nc} newly created ({round(nc / 86400, 3)}/s)")


async def p_gharchive(s):
    hr = (ROUND_TS - timedelta(hours=3)).strftime("%Y-%m-%d-%-H")
    n, first = 0, b""
    async with s.get(f"https://data.gharchive.org/{hr}.json.gz", headers=H, timeout=aiohttp.ClientTimeout(total=300)) as r:
        if r.status != 200:
            return err(f"HTTP {r.status} for {hr}")
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        async for chunk in r.content.iter_chunked(1 << 20):
            out = d.decompress(chunk); n += out.count(b"\n")
            if len(first) < 3_000_000:
                first += out
    acc = Acc()
    for line in first.split(b"\n")[:1000]:
        try:
            acc.add(json.loads(line))
        except Exception:
            pass
    return result(acc, window=3600, rate=round(n / 3600, 3), n=n, note=f"hour file {hr} UTC; payload fields vary by event type (union across 1,000 events reported)")


async def p_ena(s):
    a = (ROUND_TS - timedelta(days=8)).strftime("%Y-%m-%d"); z = (ROUND_TS - timedelta(days=2)).strftime("%Y-%m-%d")
    st, b, _ = await get(s, f"https://www.ebi.ac.uk/ena/portal/api/count?result=read_run&query=first_public%3E%3D{a}%20AND%20first_public%3C%3D{z}")
    n = int(b.decode().strip().splitlines()[-1])
    st, b, _ = await get(s, f"https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=first_public%3E%3D{z}&limit=20&fields=all&format=json")
    acc = Acc()
    for it in json.loads(b):
        acc.add(it)
    return result(acc, window=7 * 86400, rate=round(n / (7 * 86400), 3), n=n, note=f"runs first made public {a}..{z} (7 days)")


async def p_counter(s, name):
    if name == "npm":
        f = lambda b: int(str(json.loads(b)["update_seq"]).split("-")[0]); url = "https://replicate.npmjs.com/registry/"
    else:
        f = lambda b: int(b); url = "https://hacker-news.firebaseio.com/v0/maxitem.json"
    st, b, _ = await get(s, url); a = f(b); t = time.time()
    await asyncio.sleep(W)
    st, b, _ = await get(s, url); c = f(b); el = time.time() - t
    sample = {}
    if name == "hn":
        st, b, _ = await get(s, f"https://hacker-news.firebaseio.com/v0/item/{c}.json"); sample = json.loads(b) or {}
    else:
        st, b, _ = await get(s, "https://replicate.npmjs.com/registry/_changes?limit=1&descending=true")
        sample = (json.loads(b).get("results") or [{}])[0]
    return result(rate=round((c - a) / el, 3), n=c - a, window=round(el), sample=flat(sample),
                  note="raw change record; full package metadata needs one extra GET per change" if name == "npm" else "item ids allocated over the window")


async def p_pypi(s):
    st, b, _ = await get(s, "https://pypi.org/rss/updates.xml")
    x = b.decode()
    items = re.findall(r"<item>(.*?)</item>", x, re.S)
    ts = sorted(datetime.strptime(re.search(r"<pubDate>(.*?)</pubDate>", i).group(1), "%a, %d %b %Y %H:%M:%S %Z").timestamp() for i in items)
    span = ts[-1] - ts[0] if len(ts) > 1 else 0
    title = re.search(r"<title>(.*?)</title>", items[0]).group(1)
    name, ver = title.rsplit(" ", 1)
    st, b, _ = await get(s, f"https://pypi.org/pypi/{name}/{ver}/json")
    info = json.loads(b).get("info", {}) if st == 200 else {}
    return result(rate=round((len(ts) - 1) / span, 3) if span else None, n=len(ts), window=round(span), sample=flat(info),
                  note=f"RSS shows the latest {len(items)} releases (5 raw fields); attributes counted on the per-release JSON enrichment (info.*)")


async def p_github_api(s):
    st, b, h = await get(s, "https://api.github.com/events?per_page=100")
    j = json.loads(b) if st == 200 else []
    acc = Acc()
    for e in j:
        acc.add(e)
    return result(acc, window=None, rate=None, status="limited",
                  note=f"HTTP {st}; unauthenticated limit {h.get('X-RateLimit-Limit')} requests/hour; the endpoint is cached and delayed, so it cannot be a real-time source without a token")


async def p_status(s, url, headers=None):
    try:
        async with s.get(url, headers={**H, **(headers or {})}, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = (await r.read())[:200]
            return dict(status="rejected" if r.status >= 400 else "reachable", rate=None, attrs_per_event=0, attrs_union=0, keys=[], sample={},
                        note=f"HTTP {r.status}: {body!r}")
    except Exception as e:
        return err(e)


async def p_mlb(s):
    st, b, _ = await get(s, f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={(ROUND_TS - timedelta(hours=6)).strftime('%Y-%m-%d')}")
    g = [x for d in json.loads(b).get("dates", []) for x in d["games"]]
    live = [x for x in g if x["status"]["abstractGameState"] == "Live"]
    if not live:
        return dict(status="idle", rate=None, attrs_per_event=0, attrs_union=0, keys=[], sample={}, note=f"{len(g)} games scheduled, none live at sampling time")
    pk = live[0]["gamePk"]
    async def fetch():
        st, b, _ = await get(s, f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"); return json.loads(b)
    r = await change_poll(fetch, lambda d: d["liveData"]["plays"]["allPlays"][-5:], lambda p: p["atBatIndex"], lambda p: len(p.get("playEvents", [])), 10)
    r["note"] += f"; game {pk} ({len(live)} live)"
    return r


# ---------------------------------------------------------------- registry
def registry(s):
    T = asyncio.to_thread
    return {
        "hsl": lambda: T(mqtt_live, "mqtt.hsl.fi", 443, ["/hfp/v2/journey/ongoing/vp/#"], "websockets", True, "/", True),
        "entur": lambda: p_entur(s),
        "ndov": p_ndov,
        "mta_gtfsrt": lambda: p_gtfsrt(s, "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"),
        "mbta_gtfsrt": lambda: p_gtfsrt(s, "https://cdn.mbta.com/realtime/VehiclePositions.pb"),
        "mbta_sse": lambda: sse_live("https://api-v3.mbta.com/vehicles?filter%5Broute_type%5D=0,1,2,3", {"update", "add"}),
        "dt_marine": lambda: T(mqtt_live, "meri.digitraffic.fi", 443, ["vessels-v2/+/location"]),
        "dt_rail": lambda: T(mqtt_live, "rata.digitraffic.fi", 443, ["train-locations/#"]),
        "dt_rail_trains": lambda: T(mqtt_live, "rata.digitraffic.fi", 443, ["trains/#"]),
        "dt_road": lambda: T(mqtt_live, "tie.digitraffic.fi", 443, ["tms-v2/#", "weather-v2/#"]),
        "kystverket_ais": lambda: T(tcp_lines, "153.44.253.27", 5631, None, ais, 30),
        "adsb_lol": lambda: p_adsb(s, "https://api.adsb.lol/v2/point/19.436/-99.072/250", 15),
        "adsb_fi": lambda: p_adsb(s, "https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250"),
        "airplanes_live": lambda: p_status(s, "https://api.airplanes.live/v2/point/19.436/-99.072/250"),
        "ecobici": lambda: p_gbfs(s, "https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json"),
        "bicing": lambda: p_gbfs(s, "https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status"),
        "velib": lambda: p_gbfs(s, "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"),
        "metar": lambda: p_metar(s),
        "ris": lambda: ws_live("wss://ris-live.ripe.net/v1/ws/?client=itam-com22102-survey", [{"type": "ris_subscribe", "data": {"type": "UPDATE"}}], ris),
        "atlas": lambda: ws_live("wss://atlas-stream.ripe.net/stream/?client=itam-com22102-survey", [json.dumps(["atlas_subscribe", {"streamType": "result", "type": "ping"}])], atlas),
        "ct": lambda: p_ct(s),
        "gharchive": lambda: p_gharchive(s),
        "github_api": lambda: p_github_api(s),
        "osm": lambda: p_osm(s),
        "npm": lambda: p_counter(s, "npm"),
        "pypi": lambda: p_pypi(s),
        "hn": lambda: p_counter(s, "hn"),
        "pskreporter": lambda: T(mqtt_live, "mqtt.pskreporter.info", 1883, ["pskr/filter/v2/#"], "tcp", False),
        "aprs": lambda: T(tcp_lines, "rotate.aprs2.net", 10152, b"user N0CALL pass -1 vers itam-survey 0.2\r\n", aprs),
        "rbn": lambda: T(tcp_lines, "telnet.reversebeacon.net", 7000, b"N0CALL\r\n", rbn),
        "sensorcomm": lambda: p_sensorcomm(s),
        "usgs_water": lambda: p_usgs(s),
        "seedlink": p_seedlink,
        "crossref": lambda: p_crossref(s),
        "ena": lambda: p_ena(s),
        "xrpl": lambda: ws_live("wss://xrplcluster.com/", [{"command": "subscribe", "streams": ["transactions"]}], xrpl),
        "stellar": lambda: sse_live("https://horizon.stellar.org/operations?cursor=now"),
        "eth_logs": lambda: ws_live("wss://ethereum-rpc.publicnode.com", [{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {}]}], evm),
        "polygon_logs": lambda: ws_live("wss://polygon-bor-rpc.publicnode.com", [{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {}]}], evm),
        "base_logs": lambda: ws_live("wss://base-rpc.publicnode.com", [{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {}]}], evm),
        "bsc_logs": lambda: ws_live("wss://bsc-rpc.publicnode.com", [{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {}]}], evm),
        "solana": lambda: ws_live("wss://api.mainnet-beta.solana.com", [{"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe", "params": ["all", {"commitment": "confirmed"}]}], solana),
        "nostr": p_nostr,
        "polymarket": lambda: p_polymarket(s),
        "okx": lambda: ws_live("wss://ws.okx.com:8443/ws/v5/public", [{"op": "subscribe", "args": [{"channel": "tickers", "instId": i} for i in ("BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "DOGE-USDT")]}], okx, ping="ping"),
        "coinbase": lambda: ws_live("wss://ws-feed.exchange.coinbase.com", [{"type": "subscribe", "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"], "channels": ["ticker"]}], coinbase),
        "deribit": lambda: ws_live("wss://www.deribit.com/ws/api/v2", [{"jsonrpc": "2.0", "id": 1, "method": "public/subscribe", "params": {"channels": ["ticker.BTC-PERPETUAL.100ms", "ticker.ETH-PERPETUAL.100ms"]}}], deribit),
        "bybit": lambda: ws_live("wss://stream.bybit.com/v5/public/spot", [{"op": "subscribe", "args": [f"tickers.{p}" for p in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT")]}], bybit, ping={"op": "ping"}),
        "kraken": lambda: ws_live("wss://ws.kraken.com/v2", [{"method": "subscribe", "params": {"channel": c, "symbol": ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD"]}} for c in ("trade", "ticker")], kraken),
        "hyperliquid": lambda: ws_live("wss://api.hyperliquid.xyz/ws", [{"method": "subscribe", "subscription": {"type": "trades", "coin": c}} for c in ("BTC", "ETH", "SOL")], hyper),
        "bitso": lambda: ws_live("wss://ws.bitso.com", [{"action": "subscribe", "book": b, "type": t} for b in ("btc_mxn", "usd_mxn", "eth_mxn") for t in ("trades", "diff-orders")], bitso),
        "bitstamp": lambda: ws_live("wss://ws.bitstamp.net", [{"event": "bts:subscribe", "data": {"channel": f"live_trades_{p}"}} for p in ("btcusd", "ethusd", "xrpusd", "btceur", "solusd")], bitstamp),
        "bitfinex": lambda: ws_live("wss://api-pub.bitfinex.com/ws/2", [{"event": "subscribe", "channel": c, "symbol": sym} for c in ("trades", "ticker") for sym in ("tBTCUSD", "tETHUSD", "tSOLUSD")], make_bitfinex()),
        "gemini": lambda: p_gemini(),
        "bitmex": lambda: ws_live("wss://ws.bitmex.com/realtime", [{"op": "subscribe", "args": ["trade:XBTUSD", "instrument:XBTUSD", "quote:XBTUSD", "trade:ETHUSD", "quote:ETHUSD"]}], bitmex),
        "albion": p_albion,
        "twitch": lambda: ws_live("wss://irc-ws.chat.twitch.tv:443", ["CAP REQ :twitch.tv/tags", "PASS SCHMOOPIIE", "NICK justinfan48213",
                                  "JOIN #ibai,#elxokas,#auronplay,#rivers_gg,#kaicenat,#xqc,#caseoh_,#jynxzi,#zackrawrr,#tarik,#elspreen,#juansguarnizo"], twitch, text_lines=True),
        "mlb": lambda: p_mlb(s),
        "mastodon": lambda: p_status(s, "https://mastodon.social/api/v1/streaming/public"),
        "zkillboard": lambda: p_status(s, "https://zkillboard.com/api/kills/"),
        "lasair": lambda: p_status(s, "https://lasair.lsst.ac.uk/api/objects/?objectIds=ZTF19abiietd&format=json"),
    }


async def p_polymarket(s=None):
    async with aiohttp.ClientSession() as s2:
        st, b, _ = await get(s2, "https://gamma-api.polymarket.com/markets?active=true&closed=false&order=volume24hr&ascending=false&limit=25")
    ids = [t for m in json.loads(b) for t in json.loads(m.get("clobTokenIds") or "[]")]
    r = await ws_live("wss://ws-subscriptions-clob.polymarket.com/ws/market", [{"assets_ids": ids, "type": "market"}], polymarket, ping="PING")
    r["note"] = f"top 25 markets by 24h volume ({len(ids)} outcome tokens)"
    return r


async def p_gemini():
    accs = await asyncio.gather(*[ws_live(f"wss://api.gemini.com/v1/marketdata/{sym}", [], gemini) for sym in ("BTCUSD", "ETHUSD", "SOLUSD")])
    n = sum(a["n"] for a in accs); best = max(accs, key=lambda a: a["attrs_per_event"])
    best.update(n=n, rate=round(n / W, 3), note="3 symbols (BTCUSD, ETHUSD, SOLUSD), v1 market data: order-book changes + trades")
    return best


async def main():
    only = set(sys.argv[1:])
    os.makedirs("/tmp/opencode/streams/rounds", exist_ok=True)
    out = f"/tmp/opencode/streams/rounds/round-{ROUND_TS.strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    async with aiohttp.ClientSession() as s:
        reg = registry(s)
        ids = [k for k in reg if not only or k in only]
        async def one(k):
            t0 = time.time()
            try:
                r = await asyncio.wait_for(reg[k](), timeout=W + 300)
            except Exception as e:
                r = err(e)
            r.update(id=k, started=ROUND_TS.isoformat(), elapsed_s=round(time.time() - t0, 1))
            if not isinstance(r.get("sample"), dict):
                r["sample"] = {}
            r["sample"] = {k2: (v if isinstance(v, (int, float, bool)) or v is None else str(v)[:160]) for k2, v in r["sample"].items()}
            return r
        res = await asyncio.gather(*[one(k) for k in ids])
    with open(out, "w") as f:
        for r in res:
            f.write(json.dumps(r, default=str) + "\n")
    for r in sorted(res, key=lambda r: r["id"]):
        print(f"{r['id']:15} {r['status']:9} rate={r['rate']!s:10} attrs={r['attrs_per_event']:3}/{r['attrs_union']:3} {r['note'][:150]}")
    print("written", out)

if __name__ == "__main__":
    asyncio.run(main())
````

## Appendix B. `meta.py`

Source registry: endpoints, documentation and terms URLs, licence patterns. 219 lines.

````python
"""Static description of every probed source (endpoints, docs, terms)."""

# kind: live = pushed stream; poll = snapshot polled and diffed; batch = periodic file; counter = id/sequence growth
# terms_pattern: regex searched in the terms/docs page text to quote licence/access evidence
# bytewax: keywords looked up in the Bytewax awesome-public-real-time-datasets README
# redact: flattened keys whose sample values are masked in the report (personal data)
M = {
 # ------------------------------------------------------------- transport & mobility
 "hsl": dict(name="HSL Helsinki High-Frequency Positioning (buses, trams, metro, trains)", cat="Transport", kind="live", proto="MQTT over WSS",
   endpoint="wss://mqtt.hsl.fi:443/", request="SUBSCRIBE /hfp/v2/journey/ongoing/vp/#", auth="None",
   docs="https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/5-realtime-api/vehicle-positions/high-frequency-positioning/index.md",
   terms="https://raw.githubusercontent.com/HSLdevcom/digitransit-site/master/src/pages/en/developers/apis/7-terms-of-use/index.md", terms_pattern=r"Digitransit makes the data available[^\n]{0,200}", bytewax=["hsl", "helsinki"], mx=False),
 "entur": dict(name="Entur Norway real-time vehicle positions", cat="Transport", kind="poll", proto="GraphQL over HTTPS (POST), polled every 15 s",
   endpoint="https://api.entur.io/realtime/v2/vehicles/graphql", request="POST {query: vehicles{vehicleId lastUpdated line location speed delay ...}} with header ET-Client-Name",
   auth="None (identifying ET-Client-Name header required)", docs="https://developer.entur.org/pages-real-time-intro",
   terms="https://developer.entur.org/pages-intro-setup-and-access/", terms_pattern=r"NLOD[^.]{0,160}|Norwegian Licence[^.]{0,120}|ET-Client-Name[^.]{0,120}", bytewax=["entur"], mx=False),
 "ndov": dict(name="NDOV Loket Netherlands public transport KV6 (all operators)", cat="Transport", kind="live", proto="ZeroMQ PUB/SUB (gzip XML)",
   endpoint="tcp://pubsub.besteffort.ndovloket.nl:7658", request="SUB '' (all envelopes)", auth="None (best-effort relay)",
   docs="https://ndovloket.nl/", terms="https://ndovloket.nl/", terms_pattern=r"open data[^.]{0,160}|besteffort[^.]{0,160}", bytewax=["ndov", "netherlands"], mx=False),
 "mta_gtfsrt": dict(name="MTA New York City Subway GTFS-Realtime (A/C/E feed)", cat="Transport", kind="poll", proto="GTFS-Realtime protobuf over HTTPS, polled every 15 s",
   endpoint="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace", request="GET (7 more subway feeds: gtfs, -bdfm, -g, -jz, -nqrw, -l, -si)", auth="None",
   docs="https://api.mta.info/", terms="https://www.mta.info/developers", terms_pattern=r"Our data feeds are free to use[^.]*",
   manual=("Our data feeds are free to use. But to use our logos, maps, symbols or other intellectual property, you need to apply for a license.", "page refuses scripted requests (HTTP 403); text retrieved with the webfetch tool on 2026-10-13"), bytewax=["mta"], mx=False),
 "mbta_gtfsrt": dict(name="MBTA Boston GTFS-Realtime VehiclePositions", cat="Transport", kind="poll", proto="GTFS-Realtime protobuf over HTTPS, polled every 15 s",
   endpoint="https://cdn.mbta.com/realtime/VehiclePositions.pb", request="GET (also TripUpdates.pb, Alerts.pb)", auth="None",
   docs="https://www.mbta.com/developers/gtfs-realtime", terms="https://www.mbta.com/developers/gtfs-realtime", terms_pattern=r"Use of MBTA data is governed by the MassDOT Developers License Agreement", bytewax=["mbta"], mx=False),
 "mbta_sse": dict(name="MBTA V3 API vehicle streaming (Server-Sent Events)", cat="Transport", kind="live", proto="Server-Sent Events",
   endpoint="https://api-v3.mbta.com/vehicles?filter[route_type]=0,1,2,3", request="GET with Accept: text/event-stream", auth="Returned 406 without a key",
   docs="https://www.mbta.com/developers/v3-api/streaming", terms="https://www.mbta.com/developers/v3-api/streaming", terms_pattern=r"Specify an API key[^.]{0,160}", bytewax=["mbta"], mx=False),
 "dt_marine": dict(name="Digitraffic Finland marine AIS vessel locations", cat="Transport", kind="live", proto="MQTT over WSS",
   endpoint="wss://meri.digitraffic.fi:443/mqtt", request="SUBSCRIBE vessels-v2/+/location (also vessels-v2/+/metadata)", auth="None",
   docs="https://www.digitraffic.fi/en/marine-traffic/", terms="https://www.digitraffic.fi/en/terms-of-service/", terms_pattern=r"Creative Commons 4\.0 By[^.]{0,120}", bytewax=["digitraffic"], mx=False),
 "dt_rail": dict(name="Digitraffic Finland train GPS locations", cat="Transport", kind="live", proto="MQTT over WSS",
   endpoint="wss://rata.digitraffic.fi:443/mqtt", request="SUBSCRIBE train-locations/#", auth="None",
   docs="https://www.digitraffic.fi/en/railway-traffic/", terms="https://www.digitraffic.fi/en/terms-of-service/", terms_pattern=r"Creative Commons 4\.0 By[^.]{0,120}", bytewax=["digitraffic"], mx=False),
 "dt_rail_trains": dict(name="Digitraffic Finland train timetables/actuals", cat="Transport", kind="live", proto="MQTT over WSS",
   endpoint="wss://rata.digitraffic.fi:443/mqtt", request="SUBSCRIBE trains/#", auth="None",
   docs="https://www.digitraffic.fi/en/railway-traffic/", terms="https://www.digitraffic.fi/en/terms-of-service/", terms_pattern=r"Creative Commons 4\.0 By[^.]{0,120}", bytewax=["digitraffic"], mx=False),
 "dt_road": dict(name="Digitraffic Finland road traffic (TMS) and road-weather sensors", cat="Transport", kind="live", proto="MQTT over WSS",
   endpoint="wss://tie.digitraffic.fi:443/mqtt", request="SUBSCRIBE tms-v2/# and weather-v2/#", auth="None",
   docs="https://www.digitraffic.fi/en/road-traffic/", terms="https://www.digitraffic.fi/en/terms-of-service/", terms_pattern=r"Creative Commons 4\.0 By[^.]{0,120}", bytewax=["digitraffic"], mx=False,
   enrich="Station and sensor metadata: https://tie.digitraffic.fi/api/tms/v1/stations and /api/weather/v1/stations"),
 "kystverket_ais": dict(name="Kystverket (Norwegian Coastal Administration) open AIS feed", cat="Transport", kind="live", proto="Raw TCP NMEA 0183 (AIVDM)",
   endpoint="tcp://153.44.253.27:5631", request="connect and read lines", auth="None",
   docs="https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/", terms="https://www.kystverket.no/en/sea-transport-and-ports/ais/access-to-ais-data/",
   terms_pattern=r"[^.]{0,160}NLOD\)|AIS data are also available at the following IP address: 153\.44\S*", bytewax=["kystverket"], mx=False),
 "adsb_lol": dict(name="adsb.lol aircraft (ADS-B) — 250 NM around Mexico City airport", cat="Transport", kind="poll", proto="REST JSON, polled every 15 s",
   endpoint="https://api.adsb.lol/v2/point/19.436/-99.072/250", request="GET", auth="None",
   docs="https://www.adsb.lol/docs/open-data/api/", terms="https://www.adsb.lol/docs/open-data/api/", terms_pattern=r"ODbL[^.]{0,120}", bytewax=["adsb.lol"], mx=True),
 "adsb_fi": dict(name="adsb.fi open data aircraft — 250 NM around Mexico City airport", cat="Transport", kind="poll", proto="REST JSON, polled every 5 s",
   endpoint="https://opendata.adsb.fi/api/v2/lat/19.436/lon/-99.072/dist/250", request="GET", auth="None",
   docs="https://github.com/adsbfi/opendata", terms="https://raw.githubusercontent.com/adsbfi/opendata/main/README.md", terms_pattern=r"[^.]{0,80}1 request[^.]{0,120}|[^.]{0,60}commercial[^.]{0,160}", bytewax=["adsb.fi"], mx=True),
 "airplanes_live": dict(name="airplanes.live aircraft API", cat="Transport", kind="poll", proto="REST JSON",
   endpoint="https://api.airplanes.live/v2/point/19.436/-99.072/250", request="GET", auth="Rejected (403): operator asks for an e-mail request",
   docs="https://airplanes.live/api-docs/", terms="https://airplanes.live/terms-of-use/", terms_pattern=r"non-commercial[^.]{0,160}|rate limit[^.]{0,120}", bytewax=["airplanes.live"], mx=True),
 "ecobici": dict(name="EcoBici CDMX bike-share station status (GBFS)", cat="Transport", kind="poll", proto="GBFS JSON over HTTPS, polled every 10 s",
   endpoint="https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json", request="GET (station_information.json for names/coordinates)", auth="None",
   docs="https://ecobici.cdmx.gob.mx/datos-abiertos/", terms="https://ecobici.cdmx.gob.mx/datos-abiertos/", terms_pattern=r"GBFS[^.]{0,200}", bytewax=["ecobici"], mx=True),
 "bicing": dict(name="Bicing Barcelona bike-share station status (GBFS)", cat="Transport", kind="poll", proto="GBFS JSON over HTTPS, polled every 10 s",
   endpoint="https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status", request="GET", auth="None",
   docs="https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing", terms="https://opendata-ajuntament.barcelona.cat/data/en/dataset/estat-estacions-bicing",
   terms_pattern=r"CC BY[^.]{0,80}|Creative Commons[^.]{0,120}|token[^.]{0,120}", bytewax=["bicing", "barcelona"], mx=False),
 "velib": dict(name="Vélib' Métropole Paris bike-share station status (GBFS)", cat="Transport", kind="poll", proto="GBFS JSON over HTTPS, polled every 10 s",
   endpoint="https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json", request="GET", auth="None",
   docs="https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel", terms="https://www.data.gouv.fr/datasets/velib-velos-et-bornes-disponibilite-temps-reel",
   terms_pattern=r"Licence Open Data Commons Open Database License \(ODbL\)", bytewax=["velib"], mx=False),
 "metar": dict(name="NOAA aviationweather.gov METAR observations (global airports)", cat="Weather & environment", kind="batch", proto="gzip CSV cache file, refreshed every minute",
   endpoint="https://aviationweather.gov/data/cache/metars.cache.csv.gz", request="GET", auth="None",
   docs="https://aviationweather.gov/data/api/", terms="https://aviationweather.gov/data/api/", terms_pattern=r"Cache[^.]{0,200}|limited in scope[^.]{0,120}", bytewax=["metar", "aviationweather"], mx=True),
 # ------------------------------------------------------------- internet & software
 "ris": dict(name="RIPE NCC RIS Live — global BGP routing updates", cat="Internet & software", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ris-live.ripe.net/v1/ws/?client=<identifier>", request='{"type":"ris_subscribe","data":{"type":"UPDATE"}}', auth="None",
   docs="https://ris-live.ripe.net/manual/", terms="https://www.ripe.net/about-us/legal/ripe-data-repository-terms-and-conditions", terms_pattern=r"Access to and use of the RIPE Data Repository and the Data for any commercial purposes[^.]*\.",
   terms_note="these are the RIPE Data Repository terms; the RIS Live manual itself was not found to state separate terms", bytewax=["ris live", "ripe"], mx=False),
 "atlas": dict(name="RIPE Atlas measurement results stream (ping)", cat="Internet & software", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://atlas-stream.ripe.net/stream/?client=<identifier>", request='["atlas_subscribe",{"streamType":"result","type":"ping"}]', auth="None",
   docs="https://atlas.ripe.net/docs/apis/streaming-api", terms="https://atlas.ripe.net/legal/terms-conditions/", terms_pattern=r"[^.]{0,100}publicly available[^.]{0,160}|[^.]{0,60}public[^.]{0,30}data[^.]{0,160}", bytewax=["ripe atlas"], mx=False),
 "ct": dict(name="Certificate Transparency logs (RFC 6962), read directly", cat="Internet & software", kind="counter", proto="REST JSON (get-sth / get-entries)",
   endpoint="<log url>/ct/v1/get-sth and /ct/v1/get-entries; log list https://www.gstatic.com/ct/log_list/v3/log_list.json", request="GET", auth="None",
   docs="https://www.rfc-editor.org/rfc/rfc6962", terms="https://www.rfc-editor.org/rfc/rfc6962", terms_pattern=r"publicly auditable[^.]{0,120}", bytewax=["certstream", "certificate transparency"], mx=False),
 "gharchive": dict(name="GH Archive — all public GitHub events (hourly files)", cat="Internet & software", kind="batch", proto="Hourly gzip NDJSON over HTTPS",
   endpoint="https://data.gharchive.org/YYYY-MM-DD-H.json.gz", request="GET", auth="None",
   docs="https://www.gharchive.org/", terms="https://www.gharchive.org/", terms_pattern=r"public GitHub timeline[^.]{0,120}", bytewax=["gharchive", "gh archive"], mx=False,
   redact=["actor.login", "actor.display_login", "actor.avatar_url", "actor.url", "actor.gravatar_id", "actor.id", "payload.*"]),
 "github_api": dict(name="GitHub REST public events (unauthenticated)", cat="Internet & software", kind="poll", proto="REST JSON",
   endpoint="https://api.github.com/events", request="GET ?per_page=100", auth="None, but 60 requests/hour without a token",
   docs="https://docs.github.com/en/rest/activity/events", terms="https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api", terms_pattern=r"60 requests per hour[^.]{0,120}", bytewax=["github"], mx=False,
   redact=["actor.login", "actor.display_login", "actor.avatar_url", "actor.url", "actor.gravatar_id", "actor.id", "payload.*"]),
 "osm": dict(name="OpenStreetMap minutely replication diffs", cat="Internet & software", kind="batch", proto="gzip osmChange XML, one file per minute",
   endpoint="https://planet.openstreetmap.org/replication/minute/NNN/NNN/NNN.osc.gz (state.txt gives the sequence)", request="GET", auth="None",
   docs="https://wiki.openstreetmap.org/wiki/Planet.osm/diffs", terms="https://www.openstreetmap.org/copyright", terms_pattern=r"Open Data Commons Open Database License[^.]{0,80}", bytewax=["openstreetmap", "osm"], mx=False,
   redact=["user", "uid"]),
 "npm": dict(name="npm registry replication changes", cat="Internet & software", kind="counter", proto="CouchDB-style _changes over HTTPS",
   endpoint="https://replicate.npmjs.com/registry/_changes", request="GET ?since=<seq>", auth="None",
   docs="https://github.com/npm/registry-follower-tutorial", terms="https://docs.npmjs.com/policies/open-source-terms", terms_pattern=r"[^.]{0,80}registry[^.]{0,160}", bytewax=["npm"], mx=False),
 "pypi": dict(name="PyPI newest releases feed", cat="Internet & software", kind="batch", proto="RSS over HTTPS (+ JSON API per release)",
   endpoint="https://pypi.org/rss/updates.xml ; https://pypi.org/pypi/<name>/<version>/json", request="GET", auth="None",
   docs="https://docs.pypi.org/api/feeds/", terms="https://docs.pypi.org/api/", terms_pattern=r"[^.]{0,80}rate limit[^.]{0,160}|[^.]{0,80}mirror[^.]{0,120}", bytewax=["pypi"], mx=False),
 "hn": dict(name="Hacker News items (Firebase API)", cat="Internet & software", kind="counter", proto="REST JSON (also Firebase SSE)",
   endpoint="https://hacker-news.firebaseio.com/v0/maxitem.json ; /v0/item/<id>.json", request="GET", auth="None",
   docs="https://github.com/HackerNews/API", terms="https://github.com/HackerNews/API", terms_pattern=r"[^.]{0,60}rate limit[^.]{0,120}", bytewax=["hacker news"], mx=False, redact=["by", "text"]),
 # ------------------------------------------------------------- science & sensors
 "pskreporter": dict(name="PSK Reporter amateur-radio reception reports", cat="Science & sensors", kind="live", proto="MQTT (TCP 1883)",
   endpoint="mqtt://mqtt.pskreporter.info:1883", request="SUBSCRIBE pskr/filter/v2/#", auth="None",
   docs="https://www.mqtt.pskreporter.info/", terms="https://www.mqtt.pskreporter.info/", terms_pattern=r"A real-time MQTT distribution of every spot reported to pskreporter", bytewax=["pskreporter", "psk reporter"], mx=False, redact=["sc", "rc", "sl", "rl"]),
 "aprs": dict(name="APRS-IS amateur-radio packet network (full feed)", cat="Science & sensors", kind="live", proto="Raw TCP text lines",
   endpoint="tcp://rotate.aprs2.net:10152", request="user N0CALL pass -1 vers <app> <ver>", auth="Read-only login with pass -1",
   docs="https://www.aprs-is.net/Connecting.aspx", terms="https://www.aprs-is.net/Connecting.aspx", terms_pattern=r"[^.]{0,80}-1[^.]{0,160}", bytewax=["aprs"], mx=False, redact=["src", "body", "path"]),
 "rbn": dict(name="Reverse Beacon Network (CW/RTTY skimmer spots)", cat="Science & sensors", kind="live", proto="Telnet text lines",
   endpoint="telnet://telnet.reversebeacon.net:7000", request="send any callsign at login", auth="None",
   docs="https://www.reversebeacon.net/", terms="https://www.reversebeacon.net/", terms_pattern=r"[^.]{0,60}telnet[^.]{0,160}", bytewax=["reverse beacon"], mx=False, redact=["spotter", "dx"]),
 "sensorcomm": dict(name="Sensor.Community citizen air-quality sensors", cat="Science & sensors", kind="batch", proto="JSON file over HTTPS (last 5 minutes)",
   endpoint="https://data.sensor.community/static/v2/data.json", request="GET", auth="None",
   docs="https://github.com/opendata-stuttgart/meta/wiki/EN-APIs", terms="https://sensor.community/en/", terms_pattern=r"DB Contents License",
   terms_note="the site footer link 'DB Contents License' points to https://opendatacommons.org/licenses/dbcl/1-0/ (Open Data Commons DbCL v1.0)", bytewax=["sensor.community", "luftdaten"], mx=False),
 "usgs_water": dict(name="USGS Water Services instantaneous values (river gauges)", cat="Science & sensors", kind="batch", proto="REST JSON (WaterML-JSON)",
   endpoint="https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=tx&period=PT1H", request="GET per state", auth="None",
   docs="https://waterservices.usgs.gov/", terms="https://waterservices.usgs.gov/", terms_pattern=r"decommissioned[^.]{0,200}", bytewax=["usgs"], mx=False),
 "seedlink": dict(name="EarthScope (IRIS) SeedLink real-time seismic waveforms", cat="Science & sensors", kind="live", proto="SeedLink 3/4 over TCP (miniSEED records)",
   endpoint="tcp://rtserve.iris.washington.edu:18000", request="STATION <sta> <net> / SELECT BHZ / DATA ... END", auth="None",
   docs="https://ds.iris.edu/ds/nodes/dmc/services/seedlink/", terms="https://ds.iris.edu/ds/nodes/dmc/services/seedlink/", terms_pattern=r"[^.]{0,80}rtserve[^.]{0,160}", bytewax=["seedlink", "iris", "earthscope"], mx=False),
 "crossref": dict(name="Crossref scholarly metadata (works indexed per day)", cat="Science & sensors", kind="batch", proto="REST JSON (cursor paging by index date)",
   endpoint="https://api.crossref.org/works?filter=from-index-date:<d>,until-index-date:<d>", request="GET with mailto=", auth="None",
   docs="https://www.crossref.org/documentation/retrieve-metadata/rest-api/", terms="https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
   terms_pattern=r"No sign-up is required[^.]{0,160}", bytewax=["crossref"], mx=False, redact=["author"]),
 "ena": dict(name="ENA (EMBL-EBI) sequencing runs made public — DNA/genomics", cat="Science & sensors", kind="batch", proto="REST (ENA Portal API)",
   endpoint="https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=first_public>=<date>", request="GET", auth="None",
   docs="https://www.ebi.ac.uk/ena/portal/api/", terms="https://www.ebi.ac.uk/about/terms-of-use/", terms_pattern=r"[^.]{0,80}freely available[^.]{0,120}|[^.]{0,60}without restriction[^.]{0,80}", bytewax=["ena", "ebi"], mx=False),
 "lasair": dict(name="Rubin Observatory LSST alerts via Lasair broker (Kafka)", cat="Science & sensors", kind="live", proto="Kafka (kafka.lsst.ac.uk:9092)",
   endpoint="kafka.lsst.ac.uk:9092 (topic per saved filter)", request="Kafka consumer", auth="Lasair account + saved filter required",
   docs="https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html", terms="https://rubinobservatory.org/for-scientists/data-products/alerts-and-brokers",
   terms_pattern=r"world public[^.]{0,120}", bytewax=["lasair", "rubin", "lsst"], mx=False),
 # ------------------------------------------------------------- finance & blockchain
 "xrpl": dict(name="XRP Ledger transactions", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://xrplcluster.com/", request='{"command":"subscribe","streams":["transactions"]}', auth="None",
   docs="https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe", terms="https://xrpl.org/docs/tutorials/public-servers",
   terms_pattern=r"[^.]{0,80}xrplcluster[^.]{0,160}", bytewax=["xrp", "ripple"], mx=False),
 "stellar": dict(name="Stellar Horizon operations stream", cat="Finance & blockchain", kind="live", proto="Server-Sent Events",
   endpoint="https://horizon.stellar.org/operations?cursor=now", request="GET with Accept: text/event-stream", auth="None",
   docs="https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming", terms="https://developers.stellar.org/docs/data/apis/horizon/api-reference/structure/streaming",
   terms_pattern=r"[^.]{0,80}stream[^.]{0,160}", bytewax=["stellar"], mx=False),
 "eth_logs": dict(name="Ethereum mainnet contract event logs (PublicNode RPC)", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket (eth_subscribe)",
   endpoint="wss://ethereum-rpc.publicnode.com", request='{"method":"eth_subscribe","params":["logs",{}]}', auth="None",
   docs="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub", terms="https://www.publicnode.com/", terms_pattern=r"[^.]{0,80}free[^.]{0,160}", bytewax=["ethereum"], mx=False),
 "polygon_logs": dict(name="Polygon PoS contract event logs (PublicNode RPC)", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket (eth_subscribe)",
   endpoint="wss://polygon-bor-rpc.publicnode.com", request='{"method":"eth_subscribe","params":["logs",{}]}', auth="None",
   docs="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub", terms="https://www.publicnode.com/", terms_pattern=r"[^.]{0,80}free[^.]{0,160}", bytewax=["polygon"], mx=False),
 "base_logs": dict(name="Base (L2) contract event logs (PublicNode RPC)", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket (eth_subscribe)",
   endpoint="wss://base-rpc.publicnode.com", request='{"method":"eth_subscribe","params":["logs",{}]}', auth="None",
   docs="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub", terms="https://www.publicnode.com/", terms_pattern=r"[^.]{0,80}free[^.]{0,160}", bytewax=["base chain"], mx=False),
 "bsc_logs": dict(name="BNB Smart Chain contract event logs (PublicNode RPC)", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket (eth_subscribe)",
   endpoint="wss://bsc-rpc.publicnode.com", request='{"method":"eth_subscribe","params":["logs",{}]}', auth="None",
   docs="https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub", terms="https://www.publicnode.com/", terms_pattern=r"[^.]{0,80}free[^.]{0,160}", bytewax=["bnb", "bsc"], mx=False),
 "solana": dict(name="Solana program logs (public mainnet RPC)", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket (logsSubscribe)",
   endpoint="wss://api.mainnet-beta.solana.com", request='{"method":"logsSubscribe","params":["all",{"commitment":"confirmed"}]}', auth="None (public RPC is rate-limited)",
   docs="https://solana.com/docs/rpc/websocket/logssubscribe", terms="https://solana.com/docs/references/clusters", terms_pattern=r"[^.]{0,80}rate limit[^.]{0,160}|[^.]{0,60}not intended for production[^.]{0,120}", bytewax=["solana"], mx=False),
 "polymarket": dict(name="Polymarket CLOB market channel (prediction-market prices)", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws-subscriptions-clob.polymarket.com/ws/market", request='{"assets_ids":[...],"type":"market"} (ids from https://gamma-api.polymarket.com/markets)', auth="None",
   docs="https://docs.polymarket.com/developers/CLOB/websocket/market-channel", terms="https://docs.polymarket.com/developers/CLOB/websocket/market-channel",
   terms_pattern=r"public market data[^.]{0,120}", bytewax=["polymarket"], mx=False),
 "okx": dict(name="OKX public tickers", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws.okx.com:8443/ws/v5/public", request='{"op":"subscribe","args":[{"channel":"tickers","instId":"BTC-USDT"},...]}', auth="None",
   docs="https://www.okx.com/docs-v5/en/", terms="https://www.okx.com/docs-v5/en/", terms_pattern=r"Public Channel[^.]{0,80}", bytewax=["okx"], mx=False),
 "coinbase": dict(name="Coinbase Exchange ticker", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws-feed.exchange.coinbase.com", request='{"type":"subscribe","product_ids":[...],"channels":["ticker"]}', auth="None",
   docs="https://docs.cdp.coinbase.com/exchange/websocket-feed/overview", terms="https://docs.cdp.coinbase.com/exchange/websocket-feed/overview", terms_pattern=r"[^.]{0,80}public[^.]{0,120}", bytewax=["coinbase"], mx=False),
 "deribit": dict(name="Deribit perpetual futures ticker", cat="Finance & blockchain", kind="live", proto="JSON-RPC over WebSocket",
   endpoint="wss://www.deribit.com/ws/api/v2", request='public/subscribe ["ticker.BTC-PERPETUAL.100ms", ...]', auth="None",
   docs="https://docs.deribit.com/", terms="https://docs.deribit.com/", terms_pattern=r"[^.]{0,80}public/subscribe[^.]{0,120}", bytewax=["deribit"], mx=False),
 "bybit": dict(name="Bybit spot tickers", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://stream.bybit.com/v5/public/spot", request='{"op":"subscribe","args":["tickers.BTCUSDT",...]}', auth="None",
   docs="https://bybit-exchange.github.io/docs/v5/websocket/public/ticker", terms="https://bybit-exchange.github.io/docs/v5/websocket/public/ticker", terms_pattern=r"[^.]{0,80}Push frequency[^.]{0,80}", bytewax=["bybit"], mx=False),
 "kraken": dict(name="Kraken trades + ticker (v2)", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws.kraken.com/v2", request='{"method":"subscribe","params":{"channel":"trade"|"ticker","symbol":[...]}}', auth="None",
   docs="https://docs.kraken.com/api/docs/websocket-v2/trade", terms="https://docs.kraken.com/api/docs/websocket-v2/trade", terms_pattern=r"[^.]{0,80}trade[^.]{0,120}", bytewax=["kraken"], mx=False),
 "hyperliquid": dict(name="Hyperliquid trades", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://api.hyperliquid.xyz/ws", request='{"method":"subscribe","subscription":{"type":"trades","coin":"BTC"}}', auth="None",
   docs="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions", terms="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions",
   terms_pattern=r"[^.]{0,80}trades[^.]{0,120}", bytewax=["hyperliquid"], mx=False, redact=["users"]),
 "bitso": dict(name="Bitso (Mexico) trades + order-book diffs (BTC/MXN, USD/MXN, ETH/MXN)", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws.bitso.com", request='{"action":"subscribe","book":"btc_mxn","type":"trades"|"diff-orders"}', auth="None",
   docs="https://docs.bitso.com/bitso-api/docs", terms="https://docs.bitso.com/bitso-api/docs", terms_pattern=r"[^.]{0,80}diff-orders[^.]{0,120}", bytewax=["bitso"], mx=True),
 "bitstamp": dict(name="Bitstamp live trades", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws.bitstamp.net", request='{"event":"bts:subscribe","data":{"channel":"live_trades_btcusd"}}', auth="None",
   docs="https://www.bitstamp.net/websocket/v2/", terms="https://www.bitstamp.net/websocket/v2/", terms_pattern=r"[^.]{0,80}live_trades[^.]{0,120}", bytewax=["bitstamp"], mx=False),
 "bitfinex": dict(name="Bitfinex trades + ticker (public v2)", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON arrays)",
   endpoint="wss://api-pub.bitfinex.com/ws/2", request='{"event":"subscribe","channel":"trades"|"ticker","symbol":"tBTCUSD"}', auth="None",
   docs="https://docs.bitfinex.com/docs/ws-public", terms="https://docs.bitfinex.com/docs/ws-public", terms_pattern=r"[^.]{0,80}public channels[^.]{0,120}", bytewax=["bitfinex"], mx=False),
 "gemini": dict(name="Gemini market data v1 (order-book changes + trades)", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://api.gemini.com/v1/marketdata/<SYMBOL>", request="connect per symbol (no message)", auth="None",
   docs="https://developer.gemini.com/websocket/streams.md", terms="https://developer.gemini.com/websocket/streams.md", terms_pattern=r"[^.]{0,80}public[^.]{0,120}", bytewax=["gemini"], mx=False),
 "bitmex": dict(name="BitMEX realtime trade/quote/instrument", cat="Finance & blockchain", kind="live", proto="WebSocket (JSON)",
   endpoint="wss://ws.bitmex.com/realtime", request='{"op":"subscribe","args":["trade:XBTUSD","quote:XBTUSD",...]}', auth="None",
   docs="https://www.bitmex.com/app/wsAPI", terms="https://www.bitmex.com/app/wsAPI", terms_pattern=r"[^.]{0,80}subscribe[^.]{0,120}", bytewax=["bitmex"], mx=False),
 # ------------------------------------------------------------- games, media, social
 "albion": dict(name="Albion Online Data Project market orders", cat="Games, media & social", kind="live", proto="NATS (TCP 4222)",
   endpoint="nats://nats.albion-online-data.com:4222", request="CONNECT user=public pass=thenewalbiondata; SUB marketorders.deduped", auth="Published public credentials",
   docs="https://www.albion-online-data.com/", terms="https://github.com/ao-data/albiondata-client", terms_pattern=r"[^.]{0,80}NATS[^.]{0,160}|[^.]{0,80}license[^.]{0,120}", bytewax=["albion"], mx=False),
 "twitch": dict(name="Twitch chat (anonymous read-only IRC)", cat="Games, media & social", kind="live", proto="IRC over WebSocket",
   endpoint="wss://irc-ws.chat.twitch.tv:443", request="CAP REQ :twitch.tv/tags; PASS SCHMOOPIIE; NICK justinfanNNNN; JOIN #<channels>", auth="Anonymous (justinfan) read-only login",
   docs="https://dev.twitch.tv/docs/chat/irc/", terms="https://legal.twitch.com/legal/developer-agreement/", terms_pattern=r"Chat We consider chat[^.]{0,160}", bytewax=["twitch"], mx=False,
   redact=["display-name", "user-id", "id", "client-nonce", "message", "reply-*", "room-id"]),
 "nostr": dict(name="Nostr public notes (kind 1) across 4 relays", cat="Games, media & social", kind="live", proto="WebSocket (NIP-01)",
   endpoint="wss://nos.lol, wss://relay.primal.net, wss://relay.damus.io, wss://nostr.mom", request='["REQ","sub",{"kinds":[1],"since":<now>}]', auth="None",
   docs="https://github.com/nostr-protocol/nips/blob/master/01.md", terms="https://github.com/nostr-protocol/nips/blob/master/01.md", terms_pattern=r"[^.]{0,60}relay[^.]{0,120}", bytewax=["nostr"], mx=False,
   redact=["pubkey", "content", "sig", "id", "tags"]),
 "mlb": dict(name="MLB Stats API live game feed", cat="Games, media & social", kind="poll", proto="REST JSON (GUMBO), polled every 10 s",
   endpoint="https://statsapi.mlb.com/api/v1.1/game/<gamePk>/feed/live", request="GET (schedule: /api/v1/schedule?sportId=1&date=...)", auth="None",
   docs="https://statsapi.mlb.com/", terms="https://gdx.mlb.com/components/copyright.txt", terms_pattern=r"[^.]{0,80}non-commercial[^.]{0,160}|[^.]{0,60}individual[^.]{0,160}", bytewax=["mlb"], mx=False),
 "mastodon": dict(name="Mastodon public streaming (mastodon.social)", cat="Games, media & social", kind="live", proto="WebSocket / SSE",
   endpoint="https://mastodon.social/api/v1/streaming/public", request="GET", auth="Access token required (401)",
   docs="https://docs.joinmastodon.org/methods/streaming/", terms="https://docs.joinmastodon.org/methods/streaming/", terms_pattern=r"[^.]{0,80}token[^.]{0,120}", bytewax=["mastodon"], mx=False),
 "zkillboard": dict(name="zKillboard (EVE Online kills)", cat="Games, media & social", kind="live", proto="WebSocket / RedisQ",
   endpoint="wss://zkillboard.com/websocket/", request='{"action":"sub","channel":"killstream"}', auth="WebSocket returned 403 to this client",
   docs="https://github.com/zKillboard/zKillboard/wiki", terms="https://github.com/zKillboard/zKillboard/wiki", terms_pattern=r"[^.]{0,80}websocket[^.]{0,120}", bytewax=["zkillboard"], mx=False),
}

ALREADY_IN_PROJECT_DOC = ["Bluesky Jetstream", "Wikimedia EventStreams (recentchange)", "GDELT", "Binance", "mempool.space (Bitcoin)", "aisstream.io", "OpenSky Network",
                          "Bytewax awesome-public-real-time-datasets list (linked)"]
````

## Appendix C. `loop.sh`

Hourly round driver. 13 lines.

````bash
#!/usr/bin/env bash
# Hourly sampling rounds on wall-clock targets (robust to suspend: a missed slot runs as soon as the host is awake).
cd /tmp/opencode/streams
N=${1:-23}; t0=$(date +%s)
for i in $(seq 1 "$N"); do
  target=$(( t0 + (i - 1) * 3600 ))
  while [ "$(date +%s)" -lt "$target" ]; do sleep 30; done
  echo "=== round $i target $(date -u -d @$target +%FT%TZ) start $(date -u +%FT%TZ)" >> loop.log
  timeout 900 uv run --no-project -q --with websockets --with aiohttp --with paho-mqtt --with pyzmq --with pyais \
    --with gtfs-realtime-bindings --with cryptography python sampler.py >> loop.log 2>&1
  echo "=== round $i end $(date -u +%FT%TZ) rc=$?" >> loop.log
done
echo "=== DONE $(date -u +%FT%TZ)" >> loop.log
````

## Appendix D. `keyed_meta.py`

Key-based sources: classification and verbatim evidence. 148 lines.

````python
"""Key-based sources: verbatim evidence (re-verified live by report.py) and classification.

group A: free key from a simple sign-up, no paid plan found on the provider pages checked, so the free key IS the full product.
group B: excluded — a paid plan exists, or the free plan is a restricted version.
group C: free key with no paid plan, but not a >=1 event/s real-time source.
Each evidence item is (url, verbatim quote); report.py fetches the url and checks the quote is present.
"""

K = [
 # ---------------------------------------------------------------- group A
 dict(id="mbta_key", group="A", name="MBTA V3 API — vehicle streaming (Boston subway, bus, commuter rail, ferry)", cat="Transport",
      signup="https://api-v3.mbta.com/register", access="Developer account; key per app (“Getting a key might take a day”)",
      delivery="Server-Sent Events (Accept: text/event-stream + x-api-key)", endpoint="https://api-v3.mbta.com/vehicles", probe="mbta_sse",
      limit="1,000 requests/min with key; increase on request; a streaming connection counts once",
      paid="None found", measure="mbta",
      ev=[("https://www.mbta.com/developers/v3-api", "A valid key is required to make a default of 1,000 requests per minute, control the version , and stream requests"),
          ("https://www.mbta.com/developers/v3-api/best-practices", "Requests made with a valid API key are limited to 1,000 requests per minute"),
          ("https://www.mbta.com/developers/v3-api/streaming", "Currently, only the initial request counts against your API key rate limit"),
          ("https://api-v3.mbta.com/", "Getting a key might take a day")]),
 dict(id="mta_bustime", group="A", name="MTA Bus Time SIRI — every New York City bus", cat="Transport",
      signup="https://register.developer.obanyc.com/", access="Web form; key by e-mail (“within half an hour”)",
      delivery="REST JSON/XML (SIRI VehicleMonitoring), polled", endpoint="https://bustime.mta.info/api/siri/vehicle-monitoring.json?key=<KEY>", probe="mta_bustime",
      limit="No numeric limit stated on the pages checked", paid="None found", measure=None,
      ev=[("https://bustime.mta.info/developers", "MTA Bus Time is built with a real-time developer API that anyone can use for free"),
          ("https://bustime.mta.info/developers", "You will receive one within half an hour"),
          ("https://bustime.mta.info/developers/siri", "VehicleMonitoring : real-time information about one, many, or all vehicles tracked by the system")]),
 dict(id="wmata", group="A", name="WMATA — Washington DC Metrorail and Metrobus (train positions, GTFS-RT)", cat="Transport",
      signup="https://developer.wmata.com/signup", access="Developer account; subscribe to a service tier to get keys",
      delivery="REST JSON + GTFS-Realtime protobuf, polled (header api_key)", endpoint="https://api.wmata.com/TrainPositions/TrainPositions?contentType=json ; https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb", probe="wmata",
      limit="Tier limits are shown only after sign-in (portal is JavaScript-rendered); not verified", paid="None now — WMATA reserves the right to charge in future",
      measure=None,
      ev=[("https://developer.wmata.com/", "Use of our APIs and other data is free of charge!"),
          ("https://developer.wmata.com/license", "WMATA currently provides the Transit Data, API and GTFS for free, but WMATA reserves the right to charge for the Transit Data, API and/or GTFS in the future"),
          ("https://developer.wmata.com/license", "You must create a developer account with WMATA and subscribe to one or more Transit Data service tiers")]),
 dict(id="tfl", group="A", name="Transport for London Unified API — Tube/bus/rail arrival predictions", cat="Transport",
      signup="https://api-portal.tfl.gov.uk/signup", access="Developer account; subscribe to the “500 requests” product",
      delivery="REST JSON, polled (app_key query parameter)", endpoint="https://api.tfl.gov.uk/Mode/tube/Arrivals?app_key=<KEY>", probe="tfl",
      limit="“500 requests data plan” (the portal does not state the time unit in the text retrieved)", paid="None found", measure="tfl",
      ev=[("https://api-portal.tfl.gov.uk/", "create a subscription for the 500 requests data plan"),
          ("https://api-portal.tfl.gov.uk/", "The public TfL data (or 'open data') released here is for open data users to use in their own software and services")]),
 dict(id="cta", group="A", name="CTA Chicago Bus Tracker and Train Tracker", cat="Transport",
      signup="https://www.transitchicago.com/developers/bustracker/", access="Application form; CTA reviews it (“we'll review your application”)",
      delivery="REST JSON/XML, polled", endpoint="https://www.ctabustracker.com/bustime/api/v2/getvehicles?key=<KEY>&rt=<routes>&format=json ; https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=<KEY>&rt=red&outputType=JSON", probe="cta_bus",
      limit="Bus Tracker: 100,000 transactions/day (≈1.16 requests/s); increase on request", paid="None found", measure=None,
      ev=[("https://www.transitchicago.com/developers/bustracker/", "By default, the Bus Tracker API has a transaction limit of 100,000* transactions/day"),
          ("https://www.transitchicago.com/developers/traintracker/", "Use our API Key Application Form to request a key and we'll review your application as soon as possible")]),
 dict(id="nta", group="A", name="NTA Ireland GTFS-Realtime — national bus and rail vehicles", cat="Transport",
      signup="https://developer.nationaltransport.ie/signup", access="Developer account (Azure API Management portal)",
      delivery="GTFS-Realtime (protobuf or JSON), polled (header x-api-key)", endpoint="https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json", probe="nta",
      limit="One call every 60 s per token (each call returns the national feed)", paid="None found", measure=None,
      ev=[("https://developer.nationaltransport.ie/usagepolicy", "Each Token will be restricted to calling the GTFS Real Time API once every 60 seconds"),
          ("https://developer.nationaltransport.ie/", "To view and use the API you need to sign up to acquire keys")]),
 dict(id="firms", group="A", name="NASA FIRMS — satellite active-fire detections (VIIRS ×3, MODIS)", cat="Weather & environment",
      signup="https://firms.modaps.eosdis.nasa.gov/api/map_key/", access="E-mail only; MAP_KEY sent by e-mail",
      delivery="REST CSV by area and day range (near real time)", endpoint="https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/VIIRS_NOAA20_NRT/world/1", probe="firms_api",
      limit="5,000 transactions per 10-minute interval; increase on request", paid="None found", measure="firms",
      ev=[("https://firms.modaps.eosdis.nasa.gov/api/map_key/", "sign up for free MAP_KEY using your email"),
          ("https://firms.modaps.eosdis.nasa.gov/api/area/", "MAP_KEY limit is 5000 transactions / 10-minute interval"),
          ("https://firms.modaps.eosdis.nasa.gov/api/area/", "Contact us if you need limit increase")]),
 dict(id="entsoe", group="A", name="ENTSO-E Transparency Platform — European electricity load, generation, prices", cat="Weather & environment",
      signup="https://transparency.entsoe.eu/", access="Account + e-mail to transparency@entsoe.eu; granted “within 3 working days”",
      delivery="REST XML (IEC 62325), polled", endpoint="https://web-api.tp.entsoe.eu/api?securityToken=<TOKEN>&documentType=…", probe="entsoe",
      limit="400 requests/min per token", paid="None found", measure=None,
      ev=[("https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token", "You will be granted within 3 working days"),
          ("https://transparencyplatform.zendesk.com/hc/en-us/articles/12783148966036-API-Rate-Limit-Part-1", "400 requests per minute")]),
 dict(id="lasair", group="A", name="Lasair — Rubin Observatory LSST alert broker (Kafka per filter)", cat="Science & sensors",
      signup="https://lasair.lsst.ac.uk/", access="Lasair account; create a filter, then consume its Kafka topic",
      delivery="Kafka (kafka.lsst.ac.uk:9092, topic per saved filter) + REST API", endpoint="kafka.lsst.ac.uk:9092 (TCP reachable from this host)", probe=None,
      limit="REST: 100 calls/h (account), 10,000 calls/h for power users on request; no Kafka limit stated", paid="None found", measure=None,
      ev=[("https://lasair.readthedocs.io/en/main/core_functions/rest-api.html", "users with an account get up to 100 calls per hour, but “power” users get up to 10,000 calls per hour"),
          ("https://lasair.readthedocs.io/en/main/core_functions/alert-streams.html", "the process is very similar for Kafka alerts, except that you will fetch the results by machine instead of by email")]),
 dict(id="fink", group="A", name="Fink — Rubin LSST / ZTF alert broker livestream", cat="Science & sensors",
      signup="https://forms.gle/2td4jysT4e9pkf889", access="Web form; credentials sent by the Fink team",
      delivery="Kafka via fink-client (finkctl)", endpoint="finkctl topic subscribe -survey lsst -name <topic>", probe=None,
      limit="No limit stated on the pages checked", paid="None found", measure=None,
      ev=[("https://raw.githubusercontent.com/astrolabsoftware/fink-client/master/README.md", "Subscribe to one or more Fink streams by filling this [form](https://forms.gle/2td4jysT4e9pkf889)"),
          ("https://raw.githubusercontent.com/astrolabsoftware/fink-client/master/README.md", "After filling the form, we will send your credentials")]),
 dict(id="mastodon", group="A", name="Mastodon streaming API — federated public timeline (e.g. mastodon.social)", cat="Games, media & social",
      signup="https://mastodon.social/auth/sign_up", access="Free user account on an instance; create an application token in settings",
      delivery="Server-Sent Events or WebSocket", endpoint="https://mastodon.social/api/v1/streaming/public (Authorization: Bearer <token>)", probe="mastodon",
      limit="REST: 300 calls per 5 min per account; streaming not listed", paid="None found", measure=None,
      ev=[("https://docs.joinmastodon.org/api/rate-limits/", "All endpoints and methods can be called 300 times within 5 minutes"),
          ("https://docs.joinmastodon.org/methods/streaming/", "an access token must be provided in order to receive events")]),
 dict(id="gfw", group="A", name="Global Fishing Watch APIs — vessel events and fishing effort (AIS + VMS)", cat="Transport",
      signup="https://globalfishingwatch.org/our-apis/", access="Global Fishing Watch account; request an API token",
      delivery="REST JSON queries (not a push stream)", endpoint="https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest", probe="gfw",
      limit="Non-commercial use only; numeric limits are on a documentation page that did not render", paid="None (commercial use: contact them)", measure=None,
      ev=[("https://globalfishingwatch.org/our-apis/", "Get your free API key"),
          ("https://globalfishingwatch.org/our-apis/documentation/", "Global Fishing Watch APIs are only available for non-commercial purposes")]),
 # ---------------------------------------------------------------- group B (excluded)
 dict(id="openaq", group="B", name="OpenAQ v3 — air-quality measurements", cat="Weather & environment", signup="https://explore.openaq.org/register",
      why="Paid tier for a higher rate", ev=[("https://docs.openaq.org/using-the-api/rate-limits", "we offer a custom pricing option for a higher rate limit"),
                                           ("https://docs.openaq.org/using-the-api/rate-limits", "60 / minute 2,000 / hour")]),
 dict(id="swiss", group="B", name="opentransportdata.swiss GTFS-RT", cat="Transport", signup="https://api-manager.opentransportdata.swiss/",
      why="Free only below a 2 queries/min limit", ev=[("https://opentransportdata.swiss/en/cookbook/realtime-prediction-cookbook/gtfs-rt/", "You can use your key to make a maximum of two queries per minute on the interface"),
                                                      ("https://opentransportdata.swiss/en/terms-of-use/", "Use of the data service is free of charge below the limit")]),
 dict(id="trafiklab", group="B", name="Trafiklab GTFS Regional realtime (Sweden)", cat="Transport", signup="https://developer.trafiklab.se/",
      why="Entry level capped at 30,000 calls/month", ev=[("https://www.trafiklab.se/api/gtfs-datasets/gtfs-regional/", "Bronze 50 30 000 Silver 250 2 000 000 Gold 500 22 500 000")]),
 dict(id="sf511", group="B", name="511 SF Bay Area transit API", cat="Transport", signup="https://511.org/open-data/token",
      why="60 requests/hour; personal non-commercial use", ev=[("https://511.org/open-data/transit", "The default rate limit per API token is 60 requests per 3600 seconds"),
                                                              ("https://511.org/about/terms", "for your personal, individual, non-commercial, and non-automated use only")]),
 dict(id="github", group="B", name="GitHub REST API (personal token)", cat="Internet & software", signup="https://github.com/settings/tokens",
      why="Higher limit only for paid Enterprise Cloud", ev=[("https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api", "All of these requests count towards your personal rate limit of 5,000 requests per hour"),
                                                            ("https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api", "GitHub Enterprise Cloud organization have a higher rate limit of 15,000 requests per hour")]),
 dict(id="abusech", group="B", name="abuse.ch URLhaus / ThreatFox", cat="Internet & software", signup="https://auth.abuse.ch/",
      why="Commercial use may need a paid subscription", ev=[("https://urlhaus.abuse.ch/api/", "This API is available free of charge under the fair use principles"),
                                                            ("https://urlhaus.abuse.ch/api/", "may require a paid subscription")]),
 dict(id="alpaca", group="B", name="Alpaca market data", cat="Finance & blockchain", signup="https://app.alpaca.markets/signup",
      why="Free plan limited to IEX and 30 symbols; full plan $99/month", ev=[("https://docs.alpaca.markets/us/docs/about-market-data-api", "Basic Algo Trader Plus Pricing Free $99 / month"),
                                                                             ("https://docs.alpaca.markets/us/docs/about-market-data-api", "Websocket subscriptions 30 symbols Unlimited")]),
 dict(id="alphavantage", group="B", name="Alpha Vantage", cat="Finance & blockchain", signup="https://www.alphavantage.co/support/#api-key",
      why="25 requests/day free; premium plan", ev=[("https://www.alphavantage.co/premium/", "For use cases that exceed our standard API usage limit (25 API requests per day) or require certain premium API functions, we offer a premium plan")]),
 dict(id="openweather", group="B", name="OpenWeather", cat="Weather & environment", signup="https://home.openweathermap.org/users/sign_up",
      why="1,000 free calls/day, then pay per call", ev=[("https://openweathermap.org/price", "First 1,000 API calls per day are FREE")]),
 dict(id="tomorrow", group="B", name="Tomorrow.io Weather API", cat="Weather & environment", signup="https://app.tomorrow.io/signup",
      why="Limits depend on the paid plan", ev=[("https://docs.tomorrow.io/reference/rate-limiting", "According to your plan, you are limited to a certain amount of requests per hour and day")]),
 dict(id="aviationstack", group="B", name="aviationstack flight data", cat="Transport", signup="https://aviationstack.com/signup/free",
      why="Free plan is for trying the API; commercial use and premium features are in paid plans", ev=[("https://aviationstack.com/pricing", "The aviationstack Free Plan offers a way to implement the API in your application and try it out using real-time flight data"),
                                                                                   ("https://aviationstack.com/pricing", "Basic level - commercial use with premium features and up to 10,000 monthly requests")]),
 dict(id="adsbx", group="B", name="ADS-B Exchange Community API", cat="Transport", signup="https://www.adsbexchange.com/community/developer-hub/",
      why="Non-commercial; enterprise plans above the limits", ev=[("https://www.adsbexchange.com/community/developer-hub/", "The Community API (formerly API Lite) is built for non-commercial use"), ("https://www.adsbexchange.com/community/developer-hub/", "If you start hitting limits or need commercial use, we have Enterprise options for you")]),
 dict(id="infura", group="B", name="Infura blockchain RPC", cat="Finance & blockchain", signup="https://app.infura.io/register",
      why="Free Core plan; paid plans add throughput", ev=[("https://www.infura.io/pricing", "Developer US$50 / month")]),
 dict(id="alchemy", group="B", name="Alchemy blockchain RPC", cat="Finance & blockchain", signup="https://dashboard.alchemy.com/signup",
      why="Free 30M compute units/month; pay-as-you-go above", ev=[("https://www.alchemy.com/pricing", "Free 30M CU per month"), ("https://www.alchemy.com/pricing", "Pay as You Go Pay for what you use")]),
 dict(id="x", group="B", name="X (Twitter) API", cat="Games, media & social", signup="https://console.x.com/",
      why="Pay per use", ev=[("https://docs.x.com/x-api/getting-started/pricing", "The X API uses pay-per-usage pricing with no subscriptions")]),
 dict(id="guardian", group="B", name="The Guardian Open Platform", cat="Games, media & social", signup="https://bonobo.capi.gutools.co.uk/register/developer",
      why="Free key only for non-commercial use", ev=[("https://open-platform.theguardian.com/access/", "Free for non-commercial usage")]),
 dict(id="newsapi", group="B", name="NewsAPI.org", cat="Games, media & social", signup="https://newsapi.org/register",
      why="Free only for development", ev=[("https://newsapi.org/pricing", "Free for development, options if you're commercial")]),
 dict(id="purpleair", group="B", name="PurpleAir sensors API", cat="Weather & environment", signup="https://develop.purpleair.com/",
      why="Paid points except for your own sensor", ev=[("https://community.purpleair.com/t/api-pricing/4523", "If you are a PurpleAir sensor owner, you can get data from your own sensor for free")]),
 # ---------------------------------------------------------------- group C (free, no paid tier, but not a >=1 ev/s stream)
 dict(id="stackexchange", group="C", name="Stack Exchange API — Stack Overflow questions/answers/comments", cat="Internet & software", signup="https://stackapps.com/apps/oauth/register",
      why="Free key (10,000 requests/day), but measured activity is far below 1 event/s", measure="stackexchange",
      ev=[("https://api.stackexchange.com/docs/throttle", "which by default is 10,000")]),
 dict(id="banxico", group="C", name="Banco de México SIE API — FX FIX, rates, indicators (Mexico)", cat="Finance & blockchain", signup="https://www.banxico.org.mx/SieAPIRest/service/v1/token",
      why="Free token; economic time series (e.g. the daily FIX), not an event stream", measure=None,
      ev=[("https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limiteConsultas", "Máximo 80 consultas en 1 minuto 40,000 consultas por día"),
          ("https://www.banxico.org.mx/SieAPIRest/service/v1/", "Todas las solicitudes que se realicen al API requieren enviar un token de consulta")]),
 dict(id="eia", group="C", name="US EIA Open Data — hourly electric grid monitor", cat="Weather & environment", signup="https://www.eia.gov/opendata/register.php",
      why="Free key; hourly aggregated series, not an event stream", measure=None,
      ev=[("https://www.eia.gov/opendata/", "Energy Information Administration is committed to its free and open data by making it available through an Application Programming Interface (API)")]),
 dict(id="steam", group="C", name="Steam Web API", cat="Games, media & social", signup="https://steamcommunity.com/dev/apikey",
      why="Free key; request/response lookups, no public event stream", measure=None,
      ev=[("https://steamcommunity.com/dev/apiterms", "Valve makes the Steam Web API available free")]),
]
````

## Appendix E. `keyed_measure.py`

Keyless measurements of key-based providers (FIRMS files, MBTA, TfL, Stack Exchange). 109 lines.

````python
"""Measure key-based sources through the keyless path of the same provider, where one exists."""
import csv, io, json, time, statistics
from datetime import datetime, timezone
import requests

B = {"User-Agent": "COM-22102-stream-survey/1.0 (course research; contact via ITAM)"}
OUT = {}


def flat(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and v:
                o.update(flat(v, f"{p}{k}."))
            else:
                o[f"{p}{k}"] = v
    return o


def rec(k, **kw):
    kw["measured_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT[k] = kw
    print(k, json.dumps({x: y for x, y in kw.items() if x != "sample"})[:400])


# 1. NASA FIRMS — public 24 h global CSVs (same products the MAP_KEY API serves)
try:
    files = {"VIIRS NOAA-20": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv",
             "VIIRS NOAA-21": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv",
             "VIIRS S-NPP": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
             "MODIS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"}
    per, tot, cols, sample, mx = {}, 0, None, None, 0
    for n, u in files.items():
        r = requests.get(u, headers=B, timeout=120)
        rows = list(csv.DictReader(io.StringIO(r.text)))
        per[n] = dict(http=r.status_code, rows=len(rows))
        tot += len(rows)
        if rows and (cols is None or len(rows[0]) > len(cols)):
            cols, sample = list(rows[0]), rows[0]
        if rows:
            mx = max(mx, len(rows[0]))
    rec("firms", rate=tot / 86400, n=tot, window_s=86400, attrs=len(cols or []), per_file=per, sample=sample,
        note="Detections in the public 24 h global files of 4 sensors ÷ 86,400 s; the MAP_KEY API serves the same products by area and day range.")
except Exception as e:
    rec("firms", error=repr(e)[:200])

# 2. MBTA V3 /vehicles — keyless (20 req/min), 4 polls 20 s apart, count vehicles whose updated_at changed
try:
    seen, changed, polls, sample, attrs = {}, 0, 0, None, []
    t0 = time.time()
    for i in range(4):
        r = requests.get("https://api-v3.mbta.com/vehicles", headers=B, timeout=40)
        polls += 1
        for v in r.json()["data"]:
            f = flat(v)
            attrs.append(len(f))
            key, ts = v["id"], v["attributes"].get("updated_at")
            if key in seen and seen[key] != ts:
                changed += 1
            seen[key] = ts
            sample = sample or f
        if i < 3:
            time.sleep(20)
    win = time.time() - t0
    rec("mbta", rate=changed / win, n=changed, window_s=round(win), attrs=statistics.median(attrs), vehicles=len(seen), sample=sample,
        note="Keyless REST polling (4 polls, ~20 s apart); counted vehicles whose updated_at changed. The keyed SSE stream pushes the same updates.")
except Exception as e:
    rec("mbta", error=repr(e)[:200])

# 3. TfL Unified API — tube arrivals, keyless, 3 polls 30 s apart, count predictions new or changed
try:
    seen, changed, sample, attrs = {}, 0, None, []
    t0 = time.time()
    for i in range(3):
        r = requests.get("https://api.tfl.gov.uk/Mode/tube/Arrivals", headers=B, timeout=60)
        data = r.json()
        for p in data:
            f = flat(p)
            attrs.append(len(f))
            key, val = p.get("id"), (p.get("expectedArrival"), p.get("currentLocation"))
            if i > 0 and seen.get(key) != val:
                changed += 1
            seen[key] = val
            sample = sample or f
        if i < 2:
            time.sleep(30)
    win = time.time() - t0
    rec("tfl", rate=changed / win, n=changed, window_s=round(win), attrs=statistics.median(attrs), predictions=len(data), http=r.status_code, sample=sample,
        note="Keyless polling of /Mode/tube/Arrivals (3 polls, 30 s apart); counted predictions that were new or whose expected arrival/location changed.")
except Exception as e:
    rec("tfl", error=repr(e)[:200])

# 4. Stack Exchange — totals created on Stack Overflow in the last hour (keyless quota 300/day)
try:
    now = int(time.time()); frm = now - 3600
    tot = {}
    for kind in ("questions", "answers", "comments"):
        r = requests.get(f"https://api.stackexchange.com/2.3/{kind}", params=dict(site="stackoverflow", fromdate=frm, todate=now, filter="total"), headers=B, timeout=40)
        tot[kind] = r.json().get("total")
    r = requests.get("https://api.stackexchange.com/2.3/questions", params=dict(site="stackoverflow", pagesize=1, filter="withbody"), headers=B, timeout=40)
    s = flat(r.json()["items"][0])
    n = sum(v or 0 for v in tot.values())
    rec("stackexchange", rate=n / 3600, n=n, window_s=3600, attrs=len(s), per_kind=tot, sample=s,
        note="Stack Overflow only (largest of the network's sites): questions + answers + comments created in the last hour, from the API's own 'total' filter.")
except Exception as e:
    rec("stackexchange", error=repr(e)[:200])

json.dump(OUT, open("/tmp/opencode/streams/keyed_measure.json", "w"), indent=1, default=str)
````

## Appendix F. `keyed_probe.py`

Endpoint probes of key-based providers without a key. 40 lines.

````python
"""Probe key-based endpoints WITHOUT a key: a 'key missing' answer proves the endpoint is live and gated by the key."""
import json, concurrent.futures as cf
import requests

B = {"User-Agent": "COM-22102-stream-survey/1.0"}
P = {
 "mbta_sse": ("https://api-v3.mbta.com/vehicles", {"Accept": "text/event-stream"}),
 "mta_bustime": ("https://bustime.mta.info/api/siri/vehicle-monitoring.json", {}),
 "wmata": ("https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb", {}),
 "wmata_rail": ("https://api.wmata.com/TrainPositions/TrainPositions?contentType=json", {}),
 "cta_bus": ("https://www.ctabustracker.com/bustime/api/v2/getvehicles?rt=22&format=json", {}),
 "cta_train": ("https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?rt=red&outputType=JSON", {}),
 "nta": ("https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json", {}),
 "firms_api": ("https://firms.modaps.eosdis.nasa.gov/api/area/csv/INVALIDKEY/VIIRS_NOAA20_NRT/world/1", {}),
 "entsoe": ("https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&outBiddingZone_Domain=10YCZ-CEPS-----N&periodStart=202610120000&periodEnd=202610130000", {}),
 "mastodon": ("https://mastodon.social/api/v1/streaming/public", {"Accept": "text/event-stream"}),
 "gfw": ("https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events:latest&limit=1&offset=0", {}),
 "stackex": ("https://api.stackexchange.com/2.3/info?site=stackoverflow", {}),
 "banxico": ("https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/oportuno", {}),
 "eia": ("https://api.eia.gov/v2/electricity/rto/region-data/data/", {}),
 "tfl": ("https://api.tfl.gov.uk/Mode/tube/Arrivals", {}),
}


def probe(k):
    u, h = P[k]
    try:
        r = requests.get(u, headers={**B, **h}, timeout=30, stream=True)
        body = next(r.iter_content(300), b"")[:220]
        r.close()
        return k, r.status_code, body.decode("utf-8", "replace").replace("\n", " ")
    except Exception as e:
        return k, "ERR", repr(e)[:150]


with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(probe, P))
for k, s, b in res:
    print(f"{k:12} {s} {b[:200]}")
json.dump({k: [s, b] for k, s, b in res}, open("/tmp/opencode/streams/keyed_probe.json", "w"), indent=1)
````

## Appendix G. `enrich.py`

Enrichment joins. 138 lines.

````python
"""Verify enrichment joins for 'rate only' sources: fetch the metadata record a consumer would join, count attributes after the join."""
import csv, io, json, glob, zipfile
from datetime import datetime, timezone
import requests

H = {"User-Agent": "ITAM-COM22102-stream-survey/0.2 (course research)"}
last = sorted(glob.glob("/tmp/opencode/streams/rounds/round-*.jsonl"))[-1]
S = {json.loads(l)["id"]: json.loads(l) for l in open(last)}


def flat(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and v:
                o.update(flat(v, f"{p}{k}."))
            else:
                o[f"{p}{k}"] = v
    return o


OUT = {}


def rec(sid, join_url, key, meta, how, http):
    ev = S[sid].get("sample") or {}
    mf = flat(meta)
    merged = dict(ev)
    for k, v in mf.items():
        merged.setdefault(k if k not in ev else f"meta.{k}", v)
    OUT[sid] = dict(event_attrs=len(ev), meta_attrs=len(mf), joined_attrs=len(merged), join_url=join_url, join_key=key, how=how, http=http,
                    meta_keys=list(mf)[:60], checked=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    print(f"{sid:12} http={http} event={len(ev)} meta={len(mf)} joined={len(merged)} key={key}")


def safe(sid, f):
    try:
        f()
    except Exception as e:
        OUT[sid] = dict(error=repr(e)[:200]); print(sid, "ERROR", repr(e)[:200])


def dt_road():
    sid = 23572  # station id observed in the sampled topic tms-v2/23572/5055
    u2 = f"https://tie.digitraffic.fi/api/tms/v1/stations/{sid}"
    r2 = requests.get(u2, headers={**H, "Digitraffic-User": "ITAM-COM22102"}, timeout=60)
    d = r2.json(); d.pop("geometry", None)
    rec("dt_road", u2, "stationId from the MQTT topic tms-v2/{stationId}/{sensorId}", d, "station properties joined to each sensor value", r2.status_code)


def dt_rail():
    ev = S["dt_rail"]["sample"]
    u = f"https://rata.digitraffic.fi/api/v1/trains/{ev['departureDate']}/{ev['trainNumber']}"
    r = requests.get(u, headers={**H, "Digitraffic-User": "ITAM-COM22102"}, timeout=60)
    t = r.json()[0]; t["timeTableRows"] = f"{len(t['timeTableRows'])} rows"
    rec("dt_rail", u, "(departureDate, trainNumber)", t, "train record joined to each GPS fix", r.status_code)


def mta():
    ev = S["mta_gtfsrt"]["sample"]
    u = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
    r = requests.get(u, headers=H, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    stops = {x["stop_id"]: x for x in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"), "utf-8-sig"))}
    routes = {x["route_id"]: x for x in csv.DictReader(io.TextIOWrapper(z.open("routes.txt"), "utf-8-sig"))}
    meta = {"stop": stops.get(ev["vehicle.stopId"], {}), "route": routes.get(ev["vehicle.trip.routeId"], {})}
    rec("mta_gtfsrt", u, "vehicle.stopId → stops.txt; vehicle.trip.routeId → routes.txt", meta, "static GTFS stop and route joined to each vehicle", r.status_code)


def npm():
    ev = S["npm"]["sample"]
    u = f"https://registry.npmjs.org/{ev['id'].replace('/', '%2f')}/latest"
    r = requests.get(u, headers=H, timeout=60)
    d = r.json()
    for k in list(d):
        if isinstance(d[k], (dict, list)) and k not in ("repository", "dist", "author"):
            d[k] = f"{len(d[k])} entries"
    rec("npm", u, "id (package name)", d, "latest package version document fetched per change", r.status_code)


def gemini():
    u = "https://api.gemini.com/v1/symbols/details/btcusd"
    r = requests.get(u, headers=H, timeout=60)
    rec("gemini", u, "symbol", r.json(), "symbol details joined to each order-book change", r.status_code)


def solana():
    sig = S["solana"]["sample"]["value.signature"]
    u = "https://api.mainnet-beta.solana.com"
    r = requests.post(u, json={"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}]}, headers=H, timeout=60)
    t = r.json().get("result") or {}
    for k in ("transaction",):
        t.pop(k, None)
    m = t.get("meta") or {}
    for k in list(m):
        if isinstance(m[k], list):
            m[k] = f"{len(m[k])} entries"
    rec("solana", u + " (getTransaction)", "value.signature", t, "transaction metadata fetched per log notification (one extra RPC call each)", r.status_code)


def hyperliquid():
    u = "https://api.hyperliquid.xyz/info"
    r = requests.post(u, json={"type": "metaAndAssetCtxs"}, headers=H, timeout=60)
    meta, ctxs = r.json()
    i = next(j for j, a in enumerate(meta["universe"]) if a["name"] == "BTC")
    rec("hyperliquid", u + " {type: metaAndAssetCtxs}", "coin", {"asset": meta["universe"][i], "ctx": ctxs[i]}, "asset metadata and live context joined to each trade", r.status_code)


def bybit():
    u = "https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=BTCUSDT"
    r = requests.get(u, headers=H, timeout=60)
    rec("bybit", u, "symbol", r.json()["result"]["list"][0], "instrument metadata joined to each ticker", r.status_code)


def kraken():
    u = "https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD"
    r = requests.get(u, headers=H, timeout=60)
    d = next(iter(r.json()["result"].values()))
    for k in list(d):
        if isinstance(d[k], list):
            d[k] = f"{len(d[k])} entries"
    rec("kraken", u, "symbol (BTC/USD → XBTUSD)", d, "asset-pair metadata joined to each trade/ticker", r.status_code)


def bitfinex():
    u = "https://api-pub.bitfinex.com/v2/conf/pub:info:pair"
    r = requests.get(u, headers=H, timeout=60)
    row = next(x for x in r.json()[0] if x[0] == "BTCUSD")
    names = ["pair", "_1", "_2", "_3", "min_order_size", "max_order_size", "_6", "_7", "initial_margin", "min_margin"]
    vals = [row[0]] + row[1]
    meta = {n: v for n, v in zip(names, vals) if not n.startswith("_")}
    rec("bitfinex", u, "symbol (tBTCUSD → BTCUSD)", meta, "pair configuration joined to each trade/ticker (field names from position)", r.status_code)


for k, f in [("dt_road", dt_road), ("dt_rail", dt_rail), ("mta_gtfsrt", mta), ("npm", npm), ("gemini", gemini), ("solana", solana),
             ("hyperliquid", hyperliquid), ("bybit", bybit), ("kraken", kraken)]:
    safe(k, f)
json.dump(OUT, open("/tmp/opencode/streams/enrich.json", "w"), indent=1, default=str)
````

## Appendix H. `full_report.py`

Report generator (this document). 515 lines.

````python
"""Aggregate sampling rounds + live link/terms checks into a Markdown report."""
import json, glob, os, re, sys, statistics, time, concurrent.futures as cf
from datetime import datetime, timezone
import requests
sys.path.insert(0, "/tmp/opencode/streams")
from meta import M, ALREADY_IN_PROJECT_DOC

OUT = sys.argv[1]
BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0", "Accept": "text/html,application/xhtml+xml,*/*"}

rounds = sorted(glob.glob("/tmp/opencode/streams/rounds/round-*.jsonl"))
data = {}
for f in rounds:
    for line in open(f):
        r = json.loads(line); data.setdefault(r["id"], []).append(r)


def check(url):
    for attempt in range(2):
        try:
            r = requests.get(url, headers=BROWSER, timeout=40, allow_redirects=True)
            return r.status_code, r.text
        except Exception as e:
            err = repr(e)[:80]
            time.sleep(2)
    return f"ERR {err}", ""


urls = sorted({u for m in M.values() for u in (m["docs"], m["terms"])})
with cf.ThreadPoolExecutor(8) as ex:
    res = dict(zip(urls, ex.map(check, urls)))
status = {u: res[u][0] for u in urls}
text = {u: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", res[u][1])) for u in urls}

bw_status, bw = check("https://raw.githubusercontent.com/bytewax/awesome-public-real-time-datasets/main/README.md")
bw_l = bw.lower()
from urllib.parse import urlparse
GENERIC = {"github.com", "githubusercontent.com", "readthedocs.io", "gitbook.io", "medium.com", "google.com", "gstatic.com", "rfc-editor.org", "github.io"}
def regdom(u):
    h = urlparse(u if "://" in u else "x://" + u).hostname or ""
    parts = h.split(".")
    return ".".join(parts[-3:]) if len(parts) >= 3 and parts[-2] in ("co", "com", "gov", "gob", "ac") else ".".join(parts[-2:])
bw_doms = {regdom(u) for u in re.findall(r"https?://[^\s)\]>\"']+", bw)} - GENERIC


def evidence(m):
    t = text[m["terms"]]
    hits = [h.group(0).strip() for h in re.finditer(m["terms_pattern"], t, re.I)][:1]
    if hits:
        return hits[0][:260] + (f" [{m['terms_note']}]" if m.get("terms_note") else "")
    if m.get("manual"):
        return f"{m['manual'][0]} [{m['manual'][1]}]"
    return None


def overlap(m):
    doms = {regdom(u) for u in re.findall(r"(?:wss?|https?|tcp|mqtt|nats|telnet)://[^\s`,;<>()]+", " ".join((m["endpoint"], m["docs"], m["terms"])))} - GENERIC
    hits = sorted(d for d in doms if d in bw_doms)
    return "yes (" + ", ".join(hits) + ")" if hits else "no"


def redact(sid, sample):
    pats = M[sid].get("redact", [])
    out = {}
    for k, v in sample.items():
        masked = any(k == p or (p.endswith("*") and k.startswith(p[:-1])) for p in pats)
        out[k] = "‹redacted›" if masked else v
    return out


def esc(v, n=90):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    s = s.replace("|", "\\|").replace("\n", " ").replace("`", "'")
    return s if len(s) <= n else s[: n - 1] + "…"


def fmt(x, d=2):
    return "—" if x is None else (f"{x:,.{d}f}" if isinstance(x, (int, float)) else str(x))



import platform, subprocess, itertools
ENR = json.load(open("/tmp/opencode/streams/enrich.json"))
GLOSS = [
 ("Event", "One record delivered by a stream (one message, one changed record of a polled snapshot, or one row of a batch file). The project counts events per second.", "this report, Method (the project document uses the term without defining it)"),
 ("Attribute", "One distinct field of an event after flattening nested objects with dotted names (`a.b.c`); a list counts as one attribute.", "this report, Method"),
 ("WebSocket", "Full-duplex message protocol over one TCP connection, opened with an HTTP upgrade (`ws://`, `wss://` with TLS).", "https://www.rfc-editor.org/rfc/rfc6455"),
 ("MQTT", "Publish/subscribe messaging protocol; clients subscribe to topic filters (`+` one level, `#` all remaining levels).", "https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html"),
 ("Server-Sent Events (SSE)", "One-way stream of text events over a long-lived HTTP response with `Content-Type: text/event-stream`.", "https://html.spec.whatwg.org/multipage/server-sent-events.html"),
 ("NATS", "Publish/subscribe messaging system with subject-based addressing.", "https://docs.nats.io/"),
 ("ZeroMQ", "Messaging library; the PUB/SUB pattern delivers every published message to all subscribers whose prefix matches.", "https://zeromq.org/"),
 ("Apache Kafka", "Distributed, partitioned commit log; consumers read topics at their own offset.", "https://kafka.apache.org/documentation/"),
 ("REST polling", "Repeated HTTP GET of a snapshot; events are the records that are new or changed between two consecutive snapshots.", "this report, Method"),
 ("GraphQL", "Query language over HTTP in which the client names the fields it wants.", "https://spec.graphql.org/"),
 ("JSON-RPC 2.0", "Remote procedure call encoded as JSON; used by blockchain nodes, here over WebSocket subscriptions.", "https://www.jsonrpc.org/specification"),
 ("Protocol Buffers", "Binary serialisation format with a schema; GTFS-Realtime feeds use it.", "https://protobuf.dev/"),
 ("GTFS-Realtime", "Standard real-time public-transport feed: vehicle positions, trip updates and alerts.", "https://gtfs.org/documentation/realtime/reference/"),
 ("GTFS (static)", "Standard public-transport schedule as CSV files (stops.txt, routes.txt, trips.txt…); the join target for GTFS-Realtime ids.", "https://gtfs.org/documentation/schedule/reference/"),
 ("GBFS", "General Bikeshare Feed Specification: JSON files such as station_information and station_status.", "https://github.com/MobilityData/gbfs"),
 ("AIS / AIVDM", "Automatic Identification System for ships; AIVDM is its NMEA 0183 sentence encoding.", "https://gpsd.gitlab.io/gpsd/AIVDM.html"),
 ("ADS-B", "Automatic Dependent Surveillance–Broadcast: aircraft broadcast position, altitude and speed.", "https://www.faa.gov/air_traffic/technology/adsb"),
 ("METAR", "Routine aviation weather observation report issued by airports.", "https://aviationweather.gov/data/api/"),
 ("BGP", "Border Gateway Protocol, the routing protocol between Internet networks (autonomous systems).", "https://www.rfc-editor.org/rfc/rfc4271"),
 ("Certificate Transparency", "Public append-only logs of issued TLS certificates, read with `get-sth` / `get-entries`.", "https://www.rfc-editor.org/rfc/rfc6962"),
 ("osmChange", "OpenStreetMap XML format that lists created, modified and deleted elements.", "https://wiki.openstreetmap.org/wiki/OsmChange"),
 ("SeedLink", "Real-time seismic data protocol that delivers miniSEED records.", "https://www.seiscomp.de/doc/apps/seedlink.html"),
 ("IRC", "Internet Relay Chat text protocol; Twitch chat speaks it over WebSocket.", "https://www.rfc-editor.org/rfc/rfc1459"),
 ("CouchDB _changes", "Feed of document changes in sequence order; the npm registry replica exposes it.", "https://docs.couchdb.org/en/stable/api/database/changes.html"),
 ("RSS 2.0", "XML feed format listing recent items.", "https://www.rssboard.org/rss-specification"),
 ("CC BY 4.0", "Creative Commons Attribution licence: reuse allowed with attribution.", "https://creativecommons.org/licenses/by/4.0/"),
 ("ODbL 1.0", "Open Database License: reuse with attribution and share-alike of derived databases.", "https://opendatacommons.org/licenses/odbl/1-0/"),
 ("NLOD 2.0", "Norwegian Licence for Open Government Data.", "https://data.norge.no/nlod/en/2.0"),
 ("CC0 1.0", "Creative Commons public-domain dedication.", "https://creativecommons.org/publicdomain/zero/1.0/"),
]
_gl = [g[2] for g in GLOSS if g[2].startswith("http")]
with cf.ThreadPoolExecutor(8) as ex:
    GST = dict(zip(_gl, ex.map(lambda u: check(u)[0], _gl)))
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
def otype(v):
    if v is None: return "null"
    if isinstance(v, bool): return "boolean"
    if isinstance(v, int): return "integer"
    if isinstance(v, float): return "number"
    if isinstance(v, str):
        if v == "‹redacted›": return "string (redacted)"
        if v.startswith("[") and v.endswith("]"): return "list (serialised)"
        if ISO.match(v): return "string (date/time)"
        if re.fullmatch(r"-?\d+(\.\d+)?", v): return "string (numeric)"
        return "string"
    return type(v).__name__
GEO = re.compile(r"(^|[._])(lat|lon|long|lng|latitude|longitude|coordinates|location)($|[._])", re.I)
TIM = re.compile(r"(time|timestamp|date|tst|tsi|ts|created|updated|reported|mts)", re.I)
def shape(keys):
    k = list(keys or [])
    return dict(geo=any(GEO.search(x) for x in k), time=any(TIM.search(x) for x in k), nested=any("." in x for x in k))
def EXTRA_HEADER():
    w(f"- **Host:** {platform.platform()} · Python {platform.python_version()} · measuring packages listed in *Reproduction*.")
    w("- **Contents:** Executive summary · Requirements and scope · Definitions · Method · Master table · Endpoints and APIs · Access, cost and licence evidence · "
      "Enrichment joins verified · Combining streams · Per-source detail · Sources that need a free API key · Sources excluded because the project document already lists them · Limitations · Reproduction · Appendices A–H (tool source code).\n")
    w("## 0. Executive summary\n")
    both = [r for r in rows if r["verdict"] == "Meets both"]
    w(f"- **{len(both)} of {len(rows)}** keyless sources meet both requirements (≥1 event/s on average and a median of ≥10 attributes per event) over the rounds listed above.")
    w(f"- **{len([r for r in rows if r['verdict'].startswith('Rate only')])}** reach the rate but not the attributes; the *Enrichment joins verified* section shows {sum(1 for k, v in ENR.items() if "meta_attrs" in v and (next(r for r in rows if r["sid"] == k)["amed"] or 0) + v["meta_attrs"] >= 10)} of them reaching ≥10 attributes after one documented join, each join fetched live.")
    w(f"- **{len([r for r in rows if r['verdict'].startswith('Attributes only')])}** have enough attributes but fewer than 1 event/s; the *Combining streams* section lists measured combinations that reach ≥1 event/s, which the project document allows.")
    w(f"- **{sum(1 for r in both if r['m']['mx'])}** qualifying sources carry Mexican data or come from a Mexican provider: " + ", ".join(r['m']['name'] for r in both if r['m']['mx']) + ".")
    w("- Highest measured average rate per category among the sources that meet both requirements:\n")
    w("| Category | Source | Avg ev/s | Median attrs | Delivery |")
    w("|---|---|---:|---:|---|")
    for c in cats:
        cs = sorted([r for r in both if r["m"]["cat"] == c], key=lambda r: -(r["mean"] or 0))[:3]
        for r in cs:
            w(f"| {c} | [{esc(r['m']['name'], 90)}](#s-{r['sid']}) | {fmt(r['mean'])} | {fmt(r['amed'], 1)} | {r['m']['kind']} · {esc(r['m']['proto'], 50)} |")
    w("")
def SECTION_DEFS():
    w("## 3. Definitions\n")
    w("Every protocol, format and licence named in this report, with its canonical specification (HTTP status fetched when this report was generated).\n")
    w("| Term | Meaning | Reference (HTTP) |")
    w("|---|---|---|")
    for t, d, u in GLOSS:
        ref = f"[{u}]({u}) ({GST[u]})" if u.startswith("http") else u
        w(f"| {t} | {d} | {ref} |")
    w("")
def SECTION_ENRICH():
    w("## 8. Enrichment joins verified\n")
    w("For sources whose raw events carry fewer than 10 attributes, the join a consumer would perform was executed live: the metadata record for the key found in a real sampled event was fetched, flattened, and merged with that event. "
      "The counts below are measured, not estimated. A join adds one request per key (cacheable for static metadata such as stations, stops or instruments).\n")
    w("Collisions between event and metadata field names are kept as separate `meta.*` fields, so attributes after the join = raw attributes + metadata attributes. "
      "The *median raw* column is the source's median over all sampled events; the join itself was executed on the latest sampled event, whose own attribute count is shown.\n")
    w("| Source | Median raw attrs | Join key | Metadata endpoint (HTTP) | Metadata attrs | Median after join | ≥10 | Verified on event with | Checked (UTC) |")
    w("|---|---:|---|---|---:|---:|:-:|---:|---|")
    name = {r["sid"]: r for r in rows}
    for sid, e in ENR.items():
        if "error" in e:
            w(f"| {esc(M[sid]['name'], 60)} | — | — | error: {esc(e['error'], 120)} | — | — | ❌ | — |"); continue
        med = name[sid]["amed"] or 0; tot = med + e["meta_attrs"]
        w(f"| [{esc(M[sid]['name'], 60)}](#s-{sid}) | {fmt(med, 1)} | {esc(e['join_key'], 80)} | `{esc(e['join_url'], 110)}` ({e['http']}) | {e['meta_attrs']} | {fmt(tot, 1)} | {'✅' if tot >= 10 else '❌'} | {e['event_attrs']} → {e['joined_attrs']} | {e['checked']} |")
    w("\nDigitraffic road events come from two topic families: `tms-v2/{stationId}/{sensorId}` (traffic counts, 4 attributes) joined above with the TMS station, and `weather-v2/{stationId}/{sensorId}` (road weather, 2 attributes), whose station record `https://tie.digitraffic.fi/api/weather/v1/stations/1002` (station 1002 observed in the sampled topic `weather-v2/1002/24`) returned HTTP 200 with 31 attributes when this report was prepared — so both families exceed 10 attributes after the join.")
    w("\nNot joined here: OpenStreetMap minutely diffs already carry each element's tags (`tag:*`), which is where their attributes come from; Reverse Beacon Network spots have no documented metadata API that was tested; Bitfinex pair configuration returns unnamed array positions, so its fields could not be named from documentation and it is not counted.\n")
def SECTION_COMBOS():
    w("## 9. Combining streams\n")
    w("The project document allows several streams to be used together to reach the average rate (“Esta permitido utilizar más de un stream a la vez para conseguir el número de eventos mínimo en promedio”). "
      "Every event must still have ≥10 attributes, so only sources with a median of ≥10 attributes are combined. Combined rate = sum of the measured average rates.\n")
    att = sorted([r for r in rows if r["verdict"].startswith("Attributes only")], key=lambda r: -(r["mean"] or 0))
    w("| Source | Avg ev/s | Median attrs |")
    w("|---|---:|---:|")
    for r in att:
        w(f"| [{esc(r['m']['name'], 90)}](#s-{r['sid']}) | {fmt(r['mean'], 3)} | {fmt(r['amed'], 1)} |")
    combos = []
    for n in (2, 3):
        for c in itertools.combinations(att, n):
            s = sum(r["mean"] or 0 for r in c)
            if s >= 1 and not any(sum(x["mean"] or 0 for x in sub) >= 1 for k in range(1, n) for sub in itertools.combinations(c, k)):
                combos.append((s, c))
    w(f"\nMinimal combinations of these sources alone that reach ≥1 event/s ({len(combos)}; a combination is minimal when no subset of it already reaches 1 event/s):\n")
    w("| Combination | Combined ev/s |")
    w("|---|---:|")
    for s, c in sorted(combos, key=lambda x: -x[0]):
        w(f"| {' + '.join(esc(r['m']['name'], 45) for r in c)} | {s:.3f} |")
    w("\nAny of these can also be combined with a source that already meets both requirements; the rates above are from the sampled windows and vary with the time of day (see each source's per-round table).\n")
def SECTION_EXCLUDED():
    w("## 12. Sources excluded because the project document already lists them\n")
    w("Not probed, by the scope of the request (new sources only): " + "; ".join(ALREADY_IN_PROJECT_DOC) + ".\n")
def SECTION_REPRO():
    w("## 14. Reproduction\n")
    w("The tools live outside the repository at `/tmp/opencode/streams/` (volatile); their complete source is reproduced in Appendices A–H so the measurement can be repeated from this document alone.\n")
    w("```bash")
    w("mkdir -p /tmp/opencode/streams/rounds && cd /tmp/opencode/streams   # save Appendices A-H here under their file names")
    w("# one sampling round of the 61 keyless sources (60 s window each, all concurrently)")
    w("uv run --no-project --with websockets --with aiohttp --with paho-mqtt --with pyzmq --with pyais --with gtfs-realtime-bindings --with cryptography python sampler.py")
    w("bash loop.sh 23            # hourly rounds on wall-clock targets")
    w("uv run --no-project --with requests python keyed_measure.py   # keyless measurements of key-based providers")
    w("uv run --no-project --with requests python keyed_probe.py     # key-based endpoints probed without a key")
    w("uv run --no-project --with requests python enrich.py          # enrichment joins")
    w("uv run --no-project --with requests python full_report.py <output.md>   # needs meta.py and keyed_meta.py beside it")
    w("```\n")
    vers = subprocess.run(["uv", "run", "--no-project", "-q", "--with", "websockets", "--with", "aiohttp", "--with", "paho-mqtt", "--with", "pyzmq", "--with", "pyais",
                           "--with", "gtfs-realtime-bindings", "--with", "cryptography", "--with", "requests", "python", "-c",
                           "import importlib.metadata as m\nfor p in ['websockets','aiohttp','paho-mqtt','pyzmq','pyais','gtfs-realtime-bindings','protobuf','cryptography','requests']: print(p, m.version(p))"],
                          capture_output=True, text=True).stdout.split("\n")
    uvv = subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip()
    w(f"Environment at generation: {platform.platform()}, Python {platform.python_version()} (report generator), {uvv}. Packages resolved by uv for the measuring tools:\n")
    w("| Package | Version |")
    w("|---|---|")
    for v in vers:
        if v.strip():
            p, x = v.split(" ", 1); w(f"| {p} | {x} |")
    w("")
def SECTION_APPENDIX():
    files = [("A", "sampler.py", "python", "Sampler: connects to all 61 keyless sources concurrently and writes one round."),
             ("B", "meta.py", "python", "Source registry: endpoints, documentation and terms URLs, licence patterns."),
             ("C", "loop.sh", "bash", "Hourly round driver."),
             ("D", "keyed_meta.py", "python", "Key-based sources: classification and verbatim evidence."),
             ("E", "keyed_measure.py", "python", "Keyless measurements of key-based providers (FIRMS files, MBTA, TfL, Stack Exchange)."),
             ("F", "keyed_probe.py", "python", "Endpoint probes of key-based providers without a key."),
             ("G", "enrich.py", "python", "Enrichment joins."),
             ("H", "full_report.py", "python", "Report generator (this document).")]
    for a, f, lang, d in files:
        p = "/tmp/opencode/streams/" + f
        body = open(p).read()
        w(f"## Appendix {a}. `{f}`\n")
        w(f"{d} {len(body.splitlines())} lines.\n")
        w("````" + lang)
        w(body.rstrip("\n"))
        w("````\n")

rows = []
for sid, m in M.items():
    rs = data.get(sid, [])
    ok = [r for r in rs if r["status"] == "ok" and r.get("rate") is not None]
    rates = [r["rate"] for r in ok]
    att = [r.get("attrs_median", r["attrs_per_event"]) for r in ok if r["attrs_per_event"]]
    best = max(ok, key=lambda r: len(r["keys"]), default=(rs[-1] if rs else None))
    mean = statistics.fmean(rates) if rates else None
    amed = statistics.median(att) if att else None
    r_ok, a_ok = (mean is not None and mean >= 1), (amed is not None and amed >= 10)
    if not ok:
        verdict = "Not usable as tested"
    elif r_ok and a_ok:
        verdict = "Meets both"
    elif r_ok:
        verdict = "Rate only (needs enrichment for ≥10 attributes)"
    elif a_ok:
        verdict = "Attributes only (combine to reach ≥1 event/s)"
    else:
        verdict = "Neither"
    rows.append(dict(sid=sid, m=m, rs=rs, ok=ok, rates=rates, mean=mean, mn=min(rates) if rates else None, mx=max(rates) if rates else None,
                     med=statistics.median(rates) if rates else None, amed=amed, amax=max((r["attrs_per_event"] for r in ok), default=None),
                     union=max((r["attrs_union"] for r in ok), default=None), best=best, verdict=verdict, r_ok=r_ok, a_ok=a_ok))

order = {"Meets both": 0, "Rate only (needs enrichment for ≥10 attributes)": 1, "Attributes only (combine to reach ≥1 event/s)": 2, "Neither": 3, "Not usable as tested": 4}
cats = ["Transport", "Weather & environment", "Internet & software", "Science & sensors", "Finance & blockchain", "Games, media & social"]
rows.sort(key=lambda r: (order[r["verdict"]], cats.index(r["m"]["cat"]), -(r["mean"] or 0)))
for i, r in enumerate(rows, 1):
    r["n"] = i

first = min((r["started"] for v in data.values() for r in v), default="")
last = max((r["started"] for v in data.values() for r in v), default="")
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
cnt = {k: sum(1 for r in rows if r["verdict"] == k) for k in order}

L = []
w = L.append
w("# Public real-time data streams for the COM-22102 final project — full detailed report\n")
w("This is the complete record of the public-data-stream research for the final project: every source probed, how it was measured, what it delivers, how to connect, what it costs, what licence evidence exists, how sources that fall short can be enriched or combined, and the full source code of the measuring tools. "
  "It supersedes nothing: the earlier record `docs/research/2026-10-12-21-37-public-data-streams-survey.md` stays as it was; this one is generated from more sampling rounds and adds the sections listed in the contents.\n")
w(f"- **Generated:** {now}")
w(f"- **Sampling rounds:** {len(rounds)} (first {first[:16]}Z, last {last[:16]}Z); one round samples every source concurrently.")
w(f"- **Sources probed:** {len(rows)} across {len(cats)} categories.")
w("- **Rounds (UTC start):** " + ", ".join(os.path.basename(f)[6:19] for f in rounds))
w(f"- **Result:** {cnt['Meets both']} meet both project requirements on the measured average; {cnt['Rate only (needs enrichment for ≥10 attributes)']} meet the rate only; "
  f"{cnt['Attributes only (combine to reach ≥1 event/s)']} meet the attributes only; {cnt['Neither']} meet neither; {cnt['Not usable as tested']} were not usable as tested.")
w("- **Key-based sources:** see the section *Sources that need a free API key* (free key with no paid plan, excluded paid/limited plans, and free keys below 1 event/s).\n")
EXTRA_HEADER()
w("## 1. Requirements and scope\n")
w("The requirements are quoted from `course-setup/course-documents/03-proyecto-final/proyecto-final-com-22102-otono-2026.pdf` (text extracted with `pdftotext`):\n")
w("> Los datos del stream deben ser reales. … Cada evento del stream debe contar con al menos 10 atributos distintos. El stream debe producir al menos 1 evento por segundo en promedio. "
  "Esta permitido utilizar más de un stream a la vez para conseguir el número de eventos mínimo en promedio.\n")
w("Excluded because the same document already suggests them: " + "; ".join(ALREADY_IN_PROJECT_DOC) + ". "
  f"Overlap with the Bytewax list (linked from the same document) was checked automatically: a source is flagged “yes” when the registered domain of its endpoint, documentation or terms URL appears among the links of the list's README (HTTP {bw_status}, {len(bw_doms)} distinct domains). Flagged sources are reported, not excluded, because the document links the list without naming them.\n")
SECTION_DEFS()
w("## 2. Method\n")
w("- **Live streams** (WebSocket, MQTT, SSE, NATS, ZeroMQ, TCP, SeedLink): connect, subscribe, count every event for a 60 s window.")
w("- **Polled snapshots** (aircraft, GBFS bike stations, GTFS-Realtime, Entur): poll at the stated interval for 60 s and count records that are new or changed between successive polls — the events a consumer would actually receive.")
w("- **Batch files** (METAR, OSM minutely, GH Archive hourly, Sensor.Community 5-min, Crossref daily, ENA weekly, USGS hourly): events in the file ÷ the period the file covers.")
w("- **Counters** (Certificate Transparency tree size over all 9 usable RFC 6962 logs, npm update sequence, Hacker News max item): growth over a 60 s window.")
w("- **Attributes per event** = number of distinct fields after flattening nested objects (lists count as one field); the table reports the **median per event** over up to 1,000 events per round, plus the maximum and the union across events.")
w("- **Average rate** = mean of the per-round rates; min/median/max show the spread across the day.")
w("- **Links**: every docs and terms URL was fetched live with a browser User-Agent at report time; the HTTP status is shown. Licence/terms evidence is a verbatim excerpt found in that page; “not found” means no matching text was found, not that the data is unlicensed.")
w("- **Personal data**: sample values that identify people (chat users, callsigns, GitHub actors, OSM editors, Nostr keys) are masked as ‹redacted›.\n")

w("## 3. Master table\n")
w("| # | Source | Category | Delivery | Access | Avg ev/s | Min – Max ev/s | Attrs/event (median) | Max attrs | Rounds OK | ≥1 ev/s | ≥10 attrs | Verdict | Mexico | In Bytewax list |")
w("|---|---|---|---|---|---:|---|---:|---:|---|:-:|:-:|---|:-:|---|")
for r in rows:
    m = r["m"]
    w(f"| {r['n']} | [{esc(m['name'], 120)}](#s-{r['sid']}) | {m['cat']} | {m['kind']} · {esc(m['proto'], 60)} | {esc(m['auth'], 60)} | {fmt(r['mean'])} | "
      f"{fmt(r['mn'])} – {fmt(r['mx'])} | {fmt(r['amed'], 1)} | {fmt(r['amax'], 0)} | {len(r['ok'])}/{len(r['rs'])} | {'✅' if r['r_ok'] else '❌'} | {'✅' if r['a_ok'] else '❌'} | "
      f"{r['verdict']} | {'🇲🇽' if m['mx'] else ''} | {overlap(m)} |")

w("\n## 4. Endpoints and APIs\n")
w("| # | Source | Endpoint | Request / subscription | Documentation (HTTP) |")
w("|---|---|---|---|---|")
for r in rows:
    m = r["m"]
    w(f"| {r['n']} | {esc(m['name'], 70)} | `{esc(m['endpoint'], 140)}` | `{esc(m['request'], 160)}` | [{esc(m['docs'], 70)}]({m['docs']}) ({status[m['docs']]}) |")

w("\n## 5. Access, cost and licence evidence\n")
w("| # | Source | Access | Terms / licence page (HTTP) | Verbatim excerpt |")
w("|---|---|---|---|---|")
for r in rows:
    m = r["m"]; ev = evidence(m)
    w(f"| {r['n']} | {esc(m['name'], 70)} | {esc(m['auth'], 80)} | [{esc(m['terms'], 70)}]({m['terms']}) ({status[m['terms']]}) | {('“' + esc(ev, 420) + '”') if ev else 'not found'} |")

w("")
SECTION_ENRICH()
SECTION_COMBOS()
w("## 6. Per-source detail\n")
for r in rows:
    m, b = r["m"], r["best"]
    w(f"<a id=\"s-{r['sid']}\"></a>\n### {r['n']}. {m['name']}\n")
    w(f"- **Verdict:** {r['verdict']} — average {fmt(r['mean'])} events/s, median {fmt(r['amed'], 1)} attributes per event.")
    w(f"- **Delivery:** {m['kind']} · {m['proto']}")
    w(f"- **Endpoint:** `{m['endpoint']}`")
    w(f"- **Request:** `{m['request']}`")
    w(f"- **Access:** {m['auth']}")
    w(f"- **Documentation:** {m['docs']} (HTTP {status[m['docs']]})")
    w(f"- **Terms / licence:** {m['terms']} (HTTP {status[m['terms']]})" + (f" — “{esc(evidence(m), 420)}”" if evidence(m) else " — no matching text found"))
    if m.get("enrich"):
        w(f"- **Enrichment:** {m['enrich']}")
    if b and b.get("note"):
        w(f"- **Measurement note (latest representative round):** {esc(b['note'], 600)}")
    sh = shape(b.get("keys") if b else [])
    if b and b.get("keys"):
        w(f"- **Data shape (by attribute name):** geographic position {'yes' if sh['geo'] else 'no'} · time field {'yes' if sh['time'] else 'no'} · nested objects {'yes' if sh['nested'] else 'no'}")
    e = ENR.get(r["sid"])
    if e and "error" not in e:
        w(f"- **Verified enrichment:** join on {e['join_key']} with `{e['join_url']}` (HTTP {e['http']}) → median {fmt(r['amed'], 1)} + {e['meta_attrs']} = **{fmt((r['amed'] or 0) + e['meta_attrs'], 1)} attributes** after the join (verified on one event: {e['event_attrs']} → {e['joined_attrs']}) ({e['how']}; checked {e['checked']}).")
    w(f"- **In the Bytewax list:** {overlap(m)} · **Mexican data or provider:** {'yes' if m['mx'] else 'no'} · **Category:** {m['cat']}")
    w("\n| Round (UTC) | Status | Events/s | Events counted | Window (s) | Attrs/event median | Max | Union |")
    w("|---|---|---:|---:|---:|---:|---:|---:|")
    for x in sorted(r["rs"], key=lambda x: x["started"]):
        w(f"| {x['started'][:16]} | {x['status']} | {fmt(x.get('rate'))} | {fmt(x.get('n'), 0)} | {fmt(x.get('window_s'), 0)} | {fmt(x.get('attrs_median'), 1)} | "
          f"{fmt(x.get('attrs_per_event'), 0)} | {fmt(x.get('attrs_union'), 0)} |")
    errs = [x for x in r["rs"] if x["status"] != "ok"]
    if errs:
        w("\nNon-OK rounds: " + "; ".join(f"{x['started'][:16]} {x['status']}: {esc(x['note'], 200)}" for x in errs[-3:]))
    if b and b.get("sample"):
        s = redact(r["sid"], b["sample"])
        w(f"\n<details><summary>Sample event — {len(s)} attributes (values truncated to 90 characters; type observed in the sample value)</summary>\n")
        w("| # | Attribute | Observed type | Example value |")
        w("|---:|---|---|---|")
        for j, (k, v) in enumerate(s.items(), 1):
            w(f"| {j} | `{esc(k, 80)}` | {otype(v)} | {esc(v)} |")
        w("\n</details>\n")
    else:
        w("\nNo event was received, so no sample is available.\n")


# ---------------------------------------------------------------- key-based sources
import html as _html
from keyed_meta import K
KM = json.load(open("/tmp/opencode/streams/keyed_measure.json"))
KP = json.load(open("/tmp/opencode/streams/keyed_probe.json"))
def _norm(s):
    s = _html.unescape(s).replace("\u2019", "'").replace("\u2018", "'").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()
def _page(u):
    try:
        rr = requests.get(u, headers=BROWSER, timeout=40, allow_redirects=True)
        t = rr.content.decode("utf-8", "replace")
        t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
        return rr.status_code, _norm(re.sub(r"<[^>]+>", " ", t))
    except Exception as e:
        return f"ERR {type(e).__name__}", ""
_eu = sorted({u for k in K for u, _ in k["ev"]} | {k["signup"] for k in K})
with cf.ThreadPoolExecutor(8) as ex:
    _pages = dict(zip(_eu, ex.map(_page, _eu)))
def _su(k):
    return f"HTTP {_pages[k['signup']][0]}"
def _ev(k):
    out = []
    for u, q in k["ev"]:
        st, t = _pages[u]
        out.append((u, q, st, _norm(q) in t))
    return out
try:
    se_info = requests.get("https://api.stackexchange.com/2.3/info?site=stackoverflow", timeout=30).json()["items"][0]
except Exception:
    se_info = {}
ver_total = sum(len(k["ev"]) for k in K); ver_ok = sum(ok for k in K for *_, ok in _ev(k))
KA = [k for k in K if k["group"] == "A"]; KB = [k for k in K if k["group"] == "B"]; KC = [k for k in K if k["group"] == "C"]

w("## 7. Sources that need a free API key\n")
w("A source is in **Table 10.1** only if all of the following hold on the provider's own pages: the key is obtained by a free sign-up, "
  "no paid plan or paid upgrade was found, so the free key is the complete product, and the documented limits still allow the stream to be consumed. "
  "Every API with a key states some fair-use limit; the limit is quoted rather than hidden. Sources with a paid plan, a trial-level free plan, "
  "or a free plan restricted to a subset are listed in **Table 10.2** with the clause that excludes them. Free keys that do not deliver ≥1 event/s are in **Table 10.3**. "
  "aisstream.io (free key) is not repeated because the project document already lists it.\n")
w(f"Evidence: {ver_total} verbatim clauses were re-fetched from the providers' pages when this report was generated; {ver_ok} were found word for word (✅), "
  f"{ver_total - ver_ok} were not (❌, see the per-row status). “None found” for paid plans means no paid plan appeared on the pages checked — not a guarantee that none exists. "
  "Every sign-up link was fetched too (HTTP status shown next to it). Endpoints were probed without a key: an HTTP 401/403/400 “key missing” answer proves the endpoint is live and that the key is what gates it.\n")
w("Measured rates use the keyless route of the same provider where one exists (FIRMS public 24 h files, MBTA REST without a key, TfL without a key); "
  "the other rows need the key before they can be measured.\n")
w("### 7.1 Free key, no paid plan found — the free key is the full product\n")
w("| # | Source | Category | How to get the key | Delivery | Documented limit | Paid plan | Measured ev/s | Attrs/event | Endpoint probe (no key) |")
w("|---|---|---|---|---|---|---|---:|---:|---|")
for i, k in enumerate(KA, 1):
    m = KM.get(k.get("measure") or "", {})
    pr = KP.get(k.get("probe") or "")
    prs = f"HTTP {pr[0]}: {esc(pr[1], 70)}" if pr else ("Kafka TCP 9092 open" if k["id"] == "lasair" else "—")
    w(f"| K{i} | [{esc(k['name'], 110)}](#k-{k['id']}) | {k['cat']} | [{esc(k['access'], 90)}]({k['signup']}) ({_su(k)}) | {esc(k['delivery'], 70)} | {esc(k['limit'], 120)} | "
      f"{esc(k['paid'], 60)} | {fmt(m.get('rate'))} | {fmt(m.get('attrs'), 0)} | {prs} |")
w("\n### 7.2 Excluded — paid plan, trial-level free plan, or restricted free subset\n")
w("| Source | Category | Sign-up | Reason | Evidence (verbatim, re-verified) |")
w("|---|---|---|---|---|")
for k in KB:
    ev = "<br>".join(f"{'✅' if ok else '❌'} “{esc(q, 200)}” — [{esc(u, 60)}]({u}) ({st})" for u, q, st, ok in _ev(k))
    w(f"| {esc(k['name'], 70)} | {k['cat']} | [link]({k['signup']}) ({_su(k)}) | {k['why']} | {ev} |")
w("\n### 7.3 Free key and no paid plan, but not a ≥1 event/s stream\n")
w("| Source | Category | Sign-up | Why it does not qualify | Evidence (verbatim, re-verified) |")
w("|---|---|---|---|---|")
for k in KC:
    ev = "<br>".join(f"{'✅' if ok else '❌'} “{esc(q, 200)}” — [{esc(u, 60)}]({u}) ({st})" for u, q, st, ok in _ev(k))
    why = k["why"]
    if k["id"] == "stackexchange":
        m = KM.get("stackexchange", {})
        why += (f". Measured {m.get('measured_at', '')}: {m.get('n')} posts+comments in the last hour on Stack Overflow ({fmt(m.get('rate'), 3)}/s); "
                f"the API's own site statistics report {se_info.get('questions_per_minute')} questions/min and {se_info.get('answers_per_minute')} answers/min "
                f"(≈{((se_info.get('questions_per_minute') or 0) + (se_info.get('answers_per_minute') or 0)) / 60:.2f}/s)")
    w(f"| {esc(k['name'], 70)} | {k['cat']} | [link]({k['signup']}) ({_su(k)}) | {esc(why, 400)} | {ev} |")
w("\n### 7.4 Detail of Table 10.1\n")
for i, k in enumerate(KA, 1):
    m = KM.get(k.get("measure") or "", {})
    w(f"<a id=\"k-{k['id']}\"></a>\n#### K{i}. {k['name']}\n")
    w(f"- **Get the key:** {k['signup']} ({_su(k)}) — {k['access']}")
    w(f"- **Delivery:** {k['delivery']}")
    w(f"- **Endpoint:** `{k['endpoint']}`")
    w(f"- **Documented limit:** {k['limit']}")
    w(f"- **Paid plan:** {k['paid']}")
    pr = KP.get(k.get("probe") or "")
    if pr:
        w(f"- **Probe without key:** HTTP {pr[0]} — `{esc(pr[1], 200)}`")
    if m.get("rate") is not None:
        w(f"- **Measured ({m['measured_at']}):** {fmt(m['rate'])} events/s ({m['n']:,} events in {m['window_s']:,} s), median {fmt(m['attrs'], 0)} attributes per event. {m['note']}")
        if m.get("per_file"):
            w("  - Files: " + "; ".join(f"{n}: {v['rows']:,} rows (HTTP {v['http']})" for n, v in m["per_file"].items()))
    else:
        w("- **Measured:** not measured — needs the key.")
    w("- **Evidence (verbatim, re-verified at generation):**")
    for u, q, st, ok in _ev(k):
        w(f"  - {'✅' if ok else '❌'} “{q}” — {u} (HTTP {st})")
    if m.get("sample"):
        w(f"\n<details><summary>Sample record — {len(m['sample'])} attributes</summary>\n")
        w("| Attribute | Example value |")
        w("|---|---|")
        for a, v in m["sample"].items():
            w(f"| `{esc(a, 80)}` | {esc(v)} |")
        w("\n</details>\n")
    w("")
print("keyed evidence verified", ver_ok, "/", ver_total)
for k in K:
    for u, q, st, ok in _ev(k):
        if not ok: print("  NOT VERIFIED", k["id"], st, u, "::", q[:90])

SECTION_EXCLUDED()
w("## 8. Limitations\n")
w(f"- Rates come from {len(rounds)} sampling rounds of about one minute each; event rates of transport, chat and market streams follow local time of day, which is why the spread is reported.")
w("- Polled sources count changed records between polls; a faster poll interval can raise the observed rate up to each provider's limit (adsb.lol answered HTTP 429 at a 5 s interval and is therefore polled every 15 s).")
w("- Attribute counts are on the raw event as delivered; several sources reach ≥10 attributes only after decoding (Certificate Transparency X.509, OpenStreetMap tags) or a join with static metadata (Digitraffic road sensors, GBFS station information) — this is stated per source.")
w("- Licence excerpts are only what the linked page states; a source without an excerpt still needs a manual terms review before students rely on it.")
w("- Access was tested from one host (the course workstation, one public IP address); some providers restrict by region or by client, so results from other networks can differ.")
w("- Rounds follow wall-clock hourly targets; when the sampling host was suspended (2026-10-13 02:13–03:08 UTC) the missed hour is absent, never interpolated. The table header lists exactly which rounds exist.")
w("- Bytewax overlap is a domain match; a related service can still appear in that list under another domain (for example Certstream, which redistributes the same Certificate Transparency logs read directly here).")
w("- Enrichment joins were each verified on one real event; a production consumer must handle keys missing from the metadata (for example a stop id absent from the static GTFS).")
w("- Free-key sources marked “Needs key” were not measured because no key was created; their limits are quoted from the providers.")
w("- The sampler is a research tool kept outside the repository at `/tmp/opencode/streams/`; raw per-round results are the `rounds/*.jsonl` files there, and the full tool source is in the appendices.\n")
SECTION_REPRO()
SECTION_APPENDIX()

_n, _map, _out = 0, {}, []
for line in "\n".join(L).split("\n"):
    mm = re.match(r"^## (\d+)\. (.*)$", line)
    if mm:
        _map[mm.group(1)] = str(_n); line = f"## {_n}. {mm.group(2)}"; _n += 1
    else:
        ms = re.match(r"^### (\d+)\.(\d+) (.*)$", line)
        if ms and ms.group(1) in _map:
            line = f"### {_map[ms.group(1)]}.{ms.group(2)} {ms.group(3)}"
    _out.append(line)
_txt = "\n".join(_out) + "\n"
open(OUT, "w").write(_txt)
print("written", OUT, "rows", len(rows), cnt, "rounds", len(rounds))
bad = {u: s for u, s in status.items() if s != 200}
print("non-200 links:", json.dumps(bad, indent=1))
print("no evidence:", [sid for sid, m in M.items() if not evidence(m)])
````


## Addendum 2026-10-20: personal value masked

The repository became public. The contact e-mail address that the measurement
code sent to Crossref as `mailto=` (twice, in `p_crossref` of Appendix A, `sampler.py`) is a
personal value and is shown as `<masked>`; nothing else in this record changed.
