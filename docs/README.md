# Decision records

Why each source is in the catalog, how it was measured and how every API key
was obtained and tested.

| Path | Kind | What it holds |
|---|---|---|
| `research/2026-10-12-21-37-public-data-streams-survey.md` | research | First survey of public real-time streams: endpoints, access, terms, measured rates, sample events |
| `research/2026-10-12-22-41-public-data-streams-full-report.md` | research | Full report of the same survey, with the measurement code and every field of every sample event |
| `research/2026-10-13-18-54-stream-consumers-and-api-keys-record.md` | research | How this repository was built and validated, and the record of the API keys |
| `research/2026-10-19-02-46-bytewax-real-time-list-screening.md` | research | Screening of the 69 free entries of Bytewax's real-time data list, with the final status of the seven sources added |
| `reference/2026-10-17-15-13-api-key-gated-sources.md` | reference | Status of every API key and every keyed source, how to get each key, test results, change log |
| `reference/2026-10-19-18-27-sub-threshold-sources.md` | reference | Group E: the 8 sources kept in the code below 1 event/s, the evidence for each, and every other stream measured or screened below 1 event/s, with change log |
| `plans/2026-10-19-03-07-stream-consumers-provisional-release-plan.md` | plan | Plan for releasing while the last sampling runs were still going |
| `plans/2026-10-20-00-11-event-outputs-plan.md` | plan | Plan for the event outputs: text formats, SQLite, message brokers and the course databases |
| `plans/2026-10-20-06-41-graceful-stop-and-readme-plan.md` | plan | Plan for stopping every command cleanly on Ctrl+C or SIGTERM, a fresh live check, and the README rewrite |

File names follow `YYYY-MM-DD-HH-MM-<name>.md` (UTC time of writing).

- `plans/` and `research/` are historical: they are not rewritten to match the
  present; later facts are added as dated addenda.
- `reference/` pages are status pages, updated in place, each with a change log.
- None of these files holds a key value or a personal value; personal fields
  in sample events are shown as `‹redacted›` or `<masked>`.

These files were written in the course repository and moved here on
2026-10-19 15:00 UTC, unchanged except for the key page's status update, the
dated addendum of the Bytewax screening, the contact e-mail address masked in the
full report on 2026-10-20 (its addendum), and the course repository's current name
(`non-relational-dbs`, renamed from `2026-02-non-relational-dbs` on 2026-10-18)
in the stream-consumers record. Paths inside them that name the course
repository, its worktree or branch `claude-course-streams` (deleted on
2026-10-19) or `/tmp/opencode/` refer to where the work was done at the time. The evidence they cite under `data/` is in this repository's
git-ignored `data/` directory, except `data/credentials/`, removed on 2026-10-18
when every key moved into `.env` (key page, section 11).

The GitHub repository is `mavasbel-itam/stream-consumers` (that organisation was
created on 2026-10-19 14:49 UTC); records written before then call it
`non-relational-dbs/stream-consumers`, which GitHub now redirects.

## Commit IDs before 2026-10-20

On 2026-10-20 the whole history was rewritten (`git filter-repo
--sensitive-data-removal`) and force-pushed, to remove the owner's personal
e-mail addresses from the public repository: every author and committer became
GitHub's no-reply address of the owner's account, and the institutional address
in two lines of the full survey report became `<masked>` in every commit. Names,
dates, messages and every other byte are unchanged (one message's citation of
`e32490d` was updated to the new ID), and the tree of the last commit is
identical. The records above, written before the rewrite, cite the old IDs;
this table gives the new one for each:

| Old ID | New ID | Date | Subject |
|---|---|---|---|
| `8448b64` | `32654c0` | 2026-10-13 | docs: initial README |
| `9c37757` | `a895849` | 2026-10-13 | Consumers for 54 public real-time data streams |
| `e719191` | `8fc6c08` | 2026-10-13 | CI: setup-uv has no major tag; pin v10.3.0 |
| `f4af707` | `61206b8` | 2026-10-13 | Key-ready candidates, .env configuration and a cancellation fix |
| `bc3a7fb` | `796631b` | 2026-10-17 | Silent rounds count as 0, Vélib' Paris re-added, CTA Bus fixtures captured with a key |
| `908953b` | `92570bb` | 2026-10-18 | Sampling results: remove gfw, bitstamp, npm, dt_rail_trains, lasair, fink; per-source minimum window; real keyed fixtures |
| `7d9012a` | `ccd9f36` | 2026-10-18 | Held keys: every key the project has lives in .env; keys lists them; live test checks each key against its provider |
| `199e43a` | `afb7197` | 2026-10-18 | Early stop: verdict per source fixed once missing rounds cannot cross 1 event/s; sample --stop-when-settled/--continue-from; verdict command; e2e covers held keys |
| `2dda597` | `3d678f1` | 2026-10-18 | GDELT: record the 2026-10-17/18 median (0.772 events/s) next to 2026-10-13's |
| `66c07da` | `496069b` | 2026-10-18 | Hold the Bitso private API key and secret in .env; live probe signs GET /api/v3/balance/ (HMAC-SHA256) |
| `7c93797` | `d3e7a64` | 2026-10-18 | Add seven keyless sources from the Bytewax real-time list: blockchain, citibike, coinpaprika, ndbc, ogn, sharpe, ukflood |
| `75a87fd` | `00c4978` | 2026-10-18 | Hold the Binance key pair (read-only) and probe it live |
| `e0ab8dd` | `dd8a7ba` | 2026-10-18 | Accept the keyed sources measured with their keys; fix slow-download false zeros |
| `2d5a9e6` | `5e23223` | 2026-10-19 | Profile: field classes, event sizes, duplicates and natural key; drop ndbc (0.268 events/s); stopped runs decide the rest |
| `ee7d938` | `25d2be7` | 2026-10-19 | Document every CLI option, the verdict and held-key ports, the 2026-10-19 fixtures, the course decision records and eth_logs' recovery |
| `f9f0120` | `81edac2` | 2026-10-19 | Make the repository self-contained: move the decision records into docs/, update the key status page and the Bytewax screening with the final results |
| `bcc7d83` | `29d016c` | 2026-10-19 | docs: course repository's current name in the stream-consumers record; note the deleted course branch |
| `e32490d` | `d579e61` | 2026-10-19 | Retain sub-1 event/s sources in Group.LOW_RATE; document in dedicated catalog section |
| `5d74f37` | `e1578f8` | 2026-10-19 | Group E: leave low-rate sources out of bulk commands; correct their documentation |
| `0d1fb03` | `1025982` | 2026-10-19 | Document every key and setting, capture entsoe and gfw fixtures with their keys, state CLI defaults |
| `6a0514d` | `fc2bf35` | 2026-10-19 | Stop an always-ready source from starving the sources consumed beside it |
| `c1b3617` | `469a2e4` | 2026-10-19 | Give each e2e Kafka source its own consumer group |
| `f94bf7d` | `4328b47` | 2026-10-19 | Document how to run the consumers and list every reference link |
| `fc14ce7` | `b283f70` | 2026-10-19 | Group the outbound ports and adapters by purpose: providers, outputs, system |
| `68f8225` | `f1e8977` | 2026-10-19 | Event outputs, stage 1: async sink port, text formats (jsonl, csv, tsv, json, pretty) and SQLite |
| `9755519` | `9447e3a` | 2026-10-19 | Outputs stage 2: Kafka, MQTT, NATS and ZeroMQ destinations |
| `a241b80` | `ea54f8e` | 2026-10-19 | Outputs stage 3: MongoDB, Cassandra, Redis, Neo4j and OpenSearch destinations |
| `8dd4e60` | `a1a051a` | 2026-10-20 | Ctrl+C and SIGTERM stop every command cleanly |
| `741e38f` | `4c09717` | 2026-10-20 | README rewritten: each fact once, configuration, recipes, stopping a run |
