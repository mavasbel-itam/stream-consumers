# Rules for agents and maintainers

- Python 3.13, `uv` only (`uv sync`, `uv run ...`); dependencies are pinned in
  `pyproject.toml` and locked in `uv.lock`.
- Hexagonal architecture with split inbound and outbound ports. Every concrete
  class extends a port (an ABC); constructor arguments and return types use the
  abstractions; only `adapters/inbound/cli.py` names concrete classes.
  `tests/unit/test_architecture.py` enforces this.
- A new source is one module in `adapters/outbound/sources/` exposing `FACTORY`,
  added to `sources/__init__.py`, with captured real messages in
  `tests/fixtures/raw/<id>.json` (personal values masked) and a row in
  `tests/unit/test_sources.py::EXPECTED`. A candidate whose key is not available
  yet uses the provider's official documentation examples instead, with
  `origin`, `documentation_url` and `corrections` recorded in the fixture.
- Inclusion rule: median measured rate of at least 1 event/s (GDELT is the
  documented exception). A source that needs a key nobody has configured is a
  candidate (`Group.CANDIDATE`): built and tested, but accepted only after its
  measured median reaches 1 event/s, and removed otherwise.
- Credentials and settings are declared in the descriptor (`Credential`,
  `Setting`); `.env.example` is generated with `stream-consumers keys --template`.
- Never commit `.env`, API keys, or anything under `data/`.
- Before every commit: `uv run ruff check src tests`, `uv run ruff format --check
  src tests`, `uv run pytest --cov` (100 %), and the e2e tier (100 %). Both
  tiers need Docker for the Kafka broker.
- Documentation in English.
