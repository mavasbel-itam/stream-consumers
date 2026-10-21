# Plan: the README regenerated from scratch

Written 2026-10-21 03:03 UTC from `main` = `origin/main` = `da6beda`, with the
Fink commit `38bd9ea` (ZTF credentials, NaN written as `null`) committed
locally and waiting for the night's ZTF alerts before it is pushed. Historical
record: once executed, later facts are added as dated addenda, never by
rewriting this text.

Owner's request (2026-10-21): regenerate `README.md` from scratch so that it is
beautiful, readable, with a very good user experience, very clear and
consistent. Approved with the recommended choices: one 73-row sources table
with a links column; only elements GitHub renders itself; the Fink commit first,
the README as its own commit.

## 1. The README before this plan (measured on `38bd9ea`)

| Finding | Evidence |
|---|---|
| Long and flat | 1,281 lines, 11 sections at level 2, 62 code fences; long outputs always expanded |
| Dense opening | the first paragraph is 16 lines and mixes what the tool is, the 2026-10-19 rename, the public-repository rule and the secret gate |
| Recipes cannot be linked | the 12 recipes are bold paragraphs, not headings: no entry in the contents, no anchor |
| Wide tables | sources 7 columns (name, provider and three links in separate columns); measurements 8 columns; the group legend is one 9-line sentence |
| History inside present-state text | "called … until 2026-10-19", "empty since 2026-10-19", dated runs in "Known behaviour" (`albion`, `eth_logs`, `mbta_v3`, the HTTP limit before 2026-10-19) |
| No visual structure | no callouts, no CI status, no overview of what the tool offers |

The guards that must keep passing are the 18 tests of
`tests/unit/test_documentation.py`. They find sections by heading (API keys,
Settings, Held keys, Variables read only by the tests, Sources, Measurements,
Running the consumers, Stopping a run, Exit codes and troubleshooting,
Outputs, Text formats, Destinations, Decision records) and read exact cells;
the code links `README.md#outputs` (`.env.example`, `keys`).

## 2. Structure

1. Header: name, one-line description, GitHub's own CI badge
   (`actions/workflows/tests.yml/badge.svg`).
2. At a glance: sources and groups, commands, text formats, destinations, the
   coverage gate.
3. Contents, two levels, every recipe included.
4. Quick start: four commands with real output.
5. Requirements.
6. Configuration: where values come from, API keys, settings, output
   password, held keys, checking the configuration, variables read only by
   the tests, terms worth reading.
7. Running the consumers: command overview, options and defaults, what the
   output looks like, stopping a run, recipes (each a level-4 heading, with an
   index table), exit codes and troubleshooting.
8. Outputs: formats table, destinations table, then one subsection per
   destination with the same order: what it writes, the URI, the command run,
   what was read back.
9. Sources: a group legend table (group, meaning, count, run by default), then
   the 73-row table with at most 6 columns: the name links to the
   documentation, one cell carries the key and its sign-up link, one the terms.
10. Measurements: the inclusion rule as a callout, the 73-row table with at
    most 6 columns, how rates are measured, why 24 rounds, settled verdicts.
11. Known behaviour: one line per source; the dated evidence moves to a new
    reference page, so nothing is lost.
12. Architecture: the Mermaid diagram and the package tree.
13. Tests: the tiers, their commands and what each needs.
14. Publishing safely: the public repository, `.env`, the secret check.
15. Decision records: every `docs/` page, the rename history, the link check.

## 3. Style rules

- Headings in sentence case; paragraphs of at most 4 lines; present state
  only, history in the decision records; one term per concept (source id,
  event, group label, destination URI).
- Code blocks: `console` with `$` when the output is shown, `bash` when it is
  not; every shown output says when it was run; long outputs inside
  `<details>`.
- GitHub callouts: `[!WARNING]` for never committing keys and for Ctrl+C in a
  shell loop under `uv run`; `[!NOTE]` for group E sources not running by
  default and for the inclusion rule.
- Tables at most 6 columns, rows ordered by source id.

## 4. How it is built and verified

1. Catalog tables are generated from `FACTORIES` and `HELD_KEYS` by a scratch
   script, never typed; the measurement values are carried over from the
   current README's table, which was generated from the `verdict` reports.
2. Every command shown with its output is run again on the final code (quick
   start, output sample, stop, every recipe, every destination against the
   test containers of `tests/servers.py` and `tests/databases.py`).
3. Nothing is dropped silently: section 6 of this plan, written once the
   README is done, maps every passage of the old README to where its fact now
   lives.
4. Guards in `tests/unit/test_documentation.py` are updated (column positions
   of the two tables) and extended: every recipe heading is in the recipe
   index, every code fence names a language, no table has more than 6 columns,
   no section before "Decision records" carries "until 20…" history. Each new
   guard is shown to fail on a deliberately broken copy.
5. The README is rendered by GitHub's `POST /markdown` API (anchors, Mermaid,
   callouts, `<details>`) and every external link is fetched.
6. A read-through from the top as a new user, then the secret check, lint,
   100 % coverage, end-to-end three times, push, CI green.

## 5. Order

1. Push the Fink commit once `check fink` and the live test of all 73 sources
   pass during the ZTF night.
2. The README commit on top of it.

## 6. Addendum (2026-10-21): where every passage of the old README went

The old README is `README.md` at `67c33ec`. Every passage is listed in its
order there.

| Old passage | Where its facts are now |
|---|---|
| Opening paragraph: what the tool is | header line and the paragraph under it |
| Opening: public repository, `.env`, the secret check | the warning under the header, and "Publishing safely" |
| Opening: called `non-relational-dbs/stream-consumers` until 2026-10-19 | "Decision records" |
| Opening: link to the decision records | "Decision records" (in the contents) |
| Contents (level 2 only) | "Contents", now with level 3 and every recipe |
| Requirements | "Requirements", first section; jq and sqlite3 added (the quick start and recipes use them) |
| Quick start | "Quick start", with its `keys` and `consume` output shown (run 2026-10-21) |
| Configuration: where values come from | same section, as a numbered order |
| API keys table | same table, carried over unchanged |
| Settings table | same table, generated from the descriptors |
| Output password | same section |
| Held keys table and the key-probe paragraph | same section, table generated from `HELD_KEYS` |
| Checking the configuration: the six-line `keys` output of 2026-10-20 17:26 UTC | a column table; the output is the quick start's (2026-10-21) |
| Variables read only by the tests | same table |
| Terms worth reading | same facts as a list |
| Running the consumers: command table and the A–D note | same table; the note as a callout |
| Options and defaults | same table, carried over unchanged |
| What the output looks like: `consume coinbase --max-events 2` of 2026-10-19 23:10 UTC | the same command run 2026-10-21, in a collapsible block, plus a table of the run report's fields |
| `check wikimedia coinbase --seconds 10` of 2026-10-19 23:15 UTC | the same command run 2026-10-21 |
| Masking and `data/` paragraph | same paragraph |
| `profile` report and field classes paragraph | paragraph plus a table of the classes, same order |
| Stopping a run: the bullet list | a table, one row per command or output; the program's message stays in prose (`test_stopping_a_run_quotes_what_the_program_prints`) |
| Shell loop measurement of 2026-10-20 | a warning callout plus a table, measured again 2026-10-21 03:18–03:20 UTC on a pseudo-terminal: `.venv/bin` stopped the loop; `uv run` ran 2 and 3; `|| break` and `set -e` stopped it |
| Second signal and the `timeout` double delivery (2026-10-20) | same paragraph, dated |
| `list`, `keys`, `verdict` interrupted at once | a row of the stop table |
| Background runs, SIGINT ignored, the 65-source SIGTERM measurement of 2026-10-20 19:05 UTC | same paragraph, dated |
| Ctrl+C example of 2026-10-20 17:35 UTC | the same command typed on a pseudo-terminal 2026-10-21 03:18 UTC |
| The 13 recipes (bold paragraphs) | 14 level-4 headings with an index table: every recipe kept and run again 2026-10-21, plus "Read Fink alerts as valid JSON" |
| `eth_logs` note under the full `check` | replaced by the note on that recipe's own run |
| Exit codes and troubleshooting | same table |
| Outputs, text formats, CSV rules, CSV sample of 2026-10-20 00:53 UTC | same sections; the rules as a list; the CSV sample run again 2026-10-21 |
| Destinations table and rules paragraph | same table; the rules as a list; the password advice as a warning callout |
| SQLite example of 2026-10-20 00:53 UTC (read with Python's `sqlite3`) | run again 2026-10-21 with the `sqlite3` command-line shell |
| Kafka example of 2026-10-20 01:10 UTC | run again 2026-10-21 against the test image, read back with aiokafka |
| MQTT, NATS, ZeroMQ (no example before) | each now has a run and its read-back (2026-10-21) |
| Course databases: the five examples of 2026-10-20 02:05 UTC | run again 2026-10-21 against the images of `tests/databases.py`, each read back with its own client |
| Sources: the 9-line group sentence ("empty since 2026-10-19" for D) | the "Groups" table (D: 0 sources) |
| Sources table, 7 columns | 6 columns: the key and its sign-up link share the cell with the terms link; order of the links unchanged |
| Measurements: rule, exception, run choice, reading guide, read-at time | a callout for the rule and the GDELT exception, then the same facts as paragraphs and a list; run names written in full |
| Measurements table, 8 columns | 6 columns: "Rounds" and "Rounds ≥ 1/s" became "N of M", run and span share a cell; every value unchanged |
| `<!-- results-read-at -->`, `<!-- results-table -->` | dropped; no code reads them (searched the repository) |
| How rates are measured, Why 24 rounds, Settled verdicts | same sections (Kafka added to the push examples) |
| Known behaviour, 9 bullets with dated runs | one table row per source; every dated measurement moved unchanged to `docs/reference/2026-10-21-03-28-known-behaviour.md` |
| Architecture: paragraph, diagram, package tree, transports, rules | same; the paragraph as two bullets, the tree collapsible, the rules as a list |
| Tests: tier table, commands, Docker images, amqtt finding, CI | same table (with what each tier needs) and commands; the images as a collapsible table; CI in one sentence |
| `.coveragerc.e2e` exclusions | same paragraph |
| Fixtures paragraph | same text, collapsible |
| Decision records table | same, plus this plan and the known-behaviour page |
| Link checks of 2026-10-20, 2026-10-19 and 2026-10-13 | a collapsible "Link check" with the new check of 2026-10-21 and the earlier totals |

Found while running the recipes, fixed in their own commits:

- `seedlink` read 0 events in the full `check`: EarthScope moved SeedLink to
  `rtserve.earthscope.org` and the old host has no DNS record any more
  (`89724d7`; evidence on the known-behaviour page).
- `tests/live/test_sources_live.py` required `ok` or `key-pending` from every
  source, while `AGENTS.md` says the live source test accepts `no-events` from
  group E; it now does (in `67c33ec`).
