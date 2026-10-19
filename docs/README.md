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

File names follow `YYYY-MM-DD-HH-MM-<name>.md` (UTC time of writing).

- `plans/` and `research/` are historical: they are not rewritten to match the
  present; later facts are added as dated addenda.
- `reference/` pages are status pages, updated in place, each with a change log.
- None of these files holds a key value or a personal value; personal fields
  in sample events are shown as `‹redacted›` or `<masked>`.

These files were written in the course repository and moved here on
2026-10-19 15:00 UTC, unchanged except for the key page's status update, the
dated addendum of the Bytewax screening and the course repository's current name
(`non-relational-dbs`, renamed from `2026-02-non-relational-dbs` on 2026-10-18)
in the stream-consumers record. Paths inside them that name the course
repository, its worktree or branch `claude-course-streams` (deleted on
2026-10-19) or `/tmp/opencode/` refer to where the work was done at the time. The evidence they cite under `data/` is in this repository's
git-ignored `data/` directory, except `data/credentials/`, removed on 2026-10-18
when every key moved into `.env` (key page, section 11).

The GitHub repository is `mavasbel-itam/stream-consumers` (that organisation was
created on 2026-10-19 14:49 UTC); records written before then call it
`non-relational-dbs/stream-consumers`, which GitHub now redirects.
