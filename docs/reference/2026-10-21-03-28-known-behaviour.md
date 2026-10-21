# Known behaviour of the sources: the evidence

Status page, updated in place (change log at the end). Created 2026-10-21
03:28 UTC, when the README's "Known behaviour" section became one line per
source; the dated measurements behind each line moved here unchanged, with the
record or report each comes from.

Times are UTC. Reports are under the git-ignored `data/` directory.

## `albion`

Albion Online market orders arrive in bursts. On 2026-10-19 the subject
`marketorders.deduped` was silent for 50 s and then carried 350 orders in
30 s, so 60-s windows at 03:53 and 04:10 read 0 events and one at 04:24 read
4.1 events/s; 1 of the 24 rounds of 2026-10-17/18 read 0. On 2026-10-20 two
30-s windows at 16:07 and 16:08 read 0, and a 45-s window at 16:10 read 1,009
orders, exactly what a direct NATS subscription counted beside it.

## `citibike`

The feed is regenerated every 60 s (`ttl` 60) behind a CloudFront cache: a
60-s check on 2026-10-19 02:13 polled only copies of one version and measured
0 events/s, so its minimum window is 150 s.

## `coinpaprika`, `sharpe`

Both refresh their whole snapshot together about every 5 min (CoinPaprika:
"up to 10 min"; Sharpe's freshness SLA is 600 s), so their minimum windows are
630 s.

## `dt_road`

Digitraffic road sensors publish in bursts; a short window can see none.

## `eth_logs`

PublicNode's Ethereum endpoint can acknowledge the unfiltered
`eth_subscribe("logs")` and then send no logs. On 2026-10-19 it sent none in
60-s windows at 03:53, 04:10, 04:24 and 05:45 nor in a 180-s window at 06:01,
while `eth_getLogs` returned 666 logs for the latest block, a subscription
filtered by one contract address received 252 logs in 40 s, and the BSC, Base
and Polygon endpoints delivered (3 of the 24 rounds of 2026-10-17/18 read 0;
median 43.8 events/s). It recovered without any change here: on 2026-10-19
14:44 the unfiltered subscription delivered 58.5 logs/s over 40 s and
`check eth_logs` read 96.3 events/s. On 2026-10-20 its 30-s window in the full
`check` of 17:54–18:12 read 0, and a 60-s `consume` at 18:14 read 3,534
events.

## `fink`

ZTF alerts arrive only during the observing night. The broker's own per-hour
offsets from 2026-10-17 00:00 to 2026-10-21 00:00 (`data/fink-ztf-20261021`)
show alerts only between about 02:00 and 15:00, nothing the rest of the day;
the four 24-h rates were 0.031, 0.595, 0.582 and 0.625 events/s. The evidence is on the
[sub-threshold page](2026-10-19-18-27-sub-threshold-sources.md) and the
[API-key page](2026-10-17-15-13-api-key-gated-sources.md).

## `firms`, `sensorcomm`

Their whole files must arrive before the first event. On 2026-10-19 the
servers sent them at 0.05–0.09 MB/s (first event after 462 s and 297 s for
`firms`, 155 s for `sensorcomm`, in 600-s checks), while the 2026-10-17/18
rounds needed at most 73 s and 50 s; their minimum windows are 600 s.

Until 2026-10-19 the HTTP client also cut every request at 120 s in total, so
a slow but steady download (Sensor.Community's 8.5 MB in 175 s) failed and the
round counted 0 events/s (both sources: 6 consecutive rounds on 2026-10-18
00:01–04:45, and 3 rounds of the `d2` run on 2026-10-19 01:35–02:35). The
120 s now bound connecting and each wait for bytes; a whole request is capped
at 900 s.

## `mastodon`

The default `MASTODON_INSTANCE` is social.vivaldi.net (since 2026-10-19;
measured with its token since 2026-10-18). mastodon.social reports
`configuration.timelines_access.live_feeds` local and remote `disabled`
(`GET /api/v2/instance`, 2026-10-18), so its public stream carries only
`delete` events; social.vivaldi.net and mastodon.world report both `public`.
A token works only on the instance that issued it (the social.vivaldi.net
token got HTTP 401 on mastodon.world). mastodon.world was measured as a second
option (median 1.833 events/s over its first 5 rounds, 2026-10-18/19).

## `mbta_v3`

With `MBTA_API_KEY`, `mbta_v3` streams: the first `reset` message lists every
vehicle (245 on 2026-10-18 04:54). It is the starting state, not a change, so
it yields no events, like the first poll of a polled feed. Until 2026-10-18 it
was counted: 37.3 vs 32.3 events/s live-only that minute.

## `mta_bustime`

The GTFS-Realtime feed answered the same with no key or a wrong key on
2026-10-18 (its SIRI API refuses them: 401 / 403); the source still sends the
key, as the provider's documentation requires.

## `nta`

One call every 60 s is allowed, so two polls need more than 60 s; its minimum
window is 150 s.

## `seedlink`

EarthScope moved its SeedLink service from `rtserve.iris.washington.edu` to
`rtserve.earthscope.org` (news item of 2026-05-14, updated 2026-06-08:
<https://www.earthscope.org/news/seedlink-service-is-moving-as-part-of-our-cloud-transition/>),
while its SeedLink page (the source's documentation link) still names the old
host. On 2026-10-21 the old name had no DNS record: 1.1.1.1, 8.8.8.8 and the
zone's authoritative server `hanna.cac.washington.edu` answered NXDOMAIN (zone
`iris.washington.edu` serial 2026102007), so the full `check` of 03:22–03:40
UTC read 0 events and `consume seedlink` at 03:40 failed with
`Name or service not known`. With the new host, `consume seedlink --seconds 60`
at 03:43 UTC read 133 events (2.217 events/s).

## `tfl`

TfL answers carry `Cache-Control: ... s-maxage=60` and a shared cache serves
them with or without a key, so a poll 30 s after a fresh answer can return the
same copy (`X-Cache: HIT`); a 60-s round then measures 0 events/s (5 of 24
rounds on 2026-10-17/18). Its minimum window is 150 s.

## `ukflood`

Polled every 15 min, so its minimum window is 960 s.

## `usgs_water`

The USGS legacy Water Services announce their retirement on 2027-02-22.

## Change log

| Date (UTC) | Change |
|---|---|
| 2026-10-21 03:28 | Created from the README's "Known behaviour" section, unchanged, plus the `fink` observing night |
| 2026-10-21 03:45 | `seedlink`: the service host moved to `rtserve.earthscope.org` |
