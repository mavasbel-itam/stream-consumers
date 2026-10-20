# Rules for agents and maintainers

- Python 3.13, `uv` only (`uv sync`, `uv run ...`); dependencies are pinned in
  `pyproject.toml` and locked in `uv.lock`.
- Hexagonal architecture with split inbound and outbound ports. Every concrete
  class extends a port (an ABC); constructor arguments and return types use the
  abstractions; only `adapters/inbound/cli.py` names concrete classes.
  `tests/unit/test_architecture.py` enforces this.
- Outbound ports and adapters are grouped by purpose, one group per port module:
  `ports/outbound/providers.py` with `adapters/outbound/providers/` (the data
  providers: sources, transports, decoders, HTTP, auth, registry, held keys),
  `ports/outbound/outputs.py` with `adapters/outbound/outputs/` (event sinks,
  reports, sampling history) and `ports/outbound/system.py` with
  `adapters/outbound/system/` (clock, environment). An adapter implements a port
  of its own group and never imports another group; sources are outbound
  (driven) because the application opens them, pulls their events and stops
  them. `tests/unit/test_architecture.py` enforces this.
- A new source is one module in `adapters/outbound/providers/sources/` exposing `FACTORY`,
  added to `sources/__init__.py`, with captured real messages in
  `tests/fixtures/raw/<id>.json` (personal values masked) and a row in
  `tests/unit/test_sources.py::EXPECTED`. A candidate whose key is not available
  yet uses the provider's official documentation examples instead, with
  `origin`, `documentation_url` and `corrections` recorded in the fixture, and
  is replaced by a capture (`captured_at`, key not stored) once the key works.
- A source's credentials get a row in the README key table and its settings a
  place in the README settings list (`tests/unit/test_documentation.py`); a CLI
  option with a default states it in its help (`tests/unit/test_cli.py`).
- The README's "Reference links" section lists every source's documentation,
  terms and sign-up link and links every page under `docs/`; "Running the
  consumers" documents every command and every option with its default. The
  same `tests/unit/test_documentation.py` fails when one is missing; a new
  source, `docs/` page or CLI option adds its row in the same change.
- An output is a text format (`EventFormatPort`, in `outputs/formats.py`) or a
  destination (`EventSinkPort`, registered by URI scheme in the CLI's `SINKS`).
  Databases and brokers extend `BatchingEventSink`; a destination that cannot
  be opened or written raises `OutputError` (exit code 1, never a source
  failure) and refuses every `--out` part it does not use
  (`domain.outputs.check_target`). Every format and scheme is documented
  in the README section "Outputs" (enforced by `test_documentation.py`), is
  unit-tested on the real captured payloads of every source, and a destination
  is tested by writing into a real server and reading back with that server's
  own client. The event loop is never blocked: blocking drivers run in a
  worker thread.
- Database outputs write only under the name `stream_consumers` (database,
  keyspace, key prefix, index prefix, `Stream*` labels), use the client
  versions labs-setup locks and are tested (`-m databases`, their own CI job)
  against the labs-setup images pinned in `tests/databases.py`. A class that
  plugs into a client library through the library's own abstraction instead of
  a port is listed in `LIBRARY_EXTENSIONS` of `tests/unit/test_architecture.py`.
- Inclusion rule: median measured rate of at least 1 event/s (GDELT is the
  documented exception). A source that needs a key nobody has configured is a
  candidate (`Group.CANDIDATE`): built and tested, but accepted only after its
  measured median reaches 1 event/s, and moved to group E (`Group.LOW_RATE`)
  otherwise. A source measured below 1 event/s is not deleted: it goes to group
  E, keeps its tests, gets a row in the README section "Sources Below 1
  Event/s" and in `docs/reference/2026-10-19-18-27-sub-threshold-sources.md`
  with the evidence, and is left out of `check`, `sample` and `profile` unless
  named (`Group.active`).
- Every number or cause written in a document comes from a report under
  `data/`, a descriptor, a research record or a live check, cited next to it;
  never write an estimate or an explanation that no record supports.
- Credentials and settings are declared in the descriptor (`Credential`,
  `Setting`); `.env.example` is generated with `stream-consumers keys --template`.
- Never commit `.env`, API keys, or anything under `data/`.
- Before every commit: `uv run ruff check src tests`, `uv run ruff format --check
  src tests`, `uv run pytest --cov` (100 %), and the e2e tier (100 %). Both
  tiers need Docker for the Kafka broker.
- Documentation in English.
- Decision records go in `docs/plans/`, `docs/research/` and `docs/reference/`,
  named `YYYY-MM-DD-HH-MM-<name>.md` from the system clock (UTC), and are listed
  in `docs/README.md`. Plans and research are historical: never rewrite them,
  add dated addenda. Reference pages are status pages updated in place with a
  change-log row. No key value, token or personal value in any document.
