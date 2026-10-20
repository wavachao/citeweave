# Contributing

Please open an issue for substantial behavior changes before implementation. Bug reports should include a minimal reproduction, commit/version, operating system, GPU and driver, and installation method. Remove API keys, access tokens and private source URLs from logs.

## Setup

Use Python 3.12 and uv. `uv sync --frozen --group official` installs the locked development and optional evaluator dependencies. Download application models only for integration work; most contracts do not require a GPU.

```bash
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
uv run pytest -q
```

The CPU CI environment can instead use `uv sync --frozen --only-group ci` with `PYTHONPATH=src`. This intentionally omits inference libraries and model downloads, while checking parsers, evidence identity, authentication, cache persistence, budget guards and evaluation aggregation.

## Validation by change

- Parser/evidence changes: test known/unknown IDs, duplicate images, incomplete outputs and source preservation.
- Serving changes: test bearer and cookie admission, failure responses, request limits and cache identity.
- UI changes: verify a real search, source cards, image zoom, export, keyboard operation, mobile layout and both font families. Use text nodes for untrusted content.
- Model or ranking changes: retain a train/validation split and evaluate on unobserved questions. Record model revisions and failures alongside successful outcomes.
- Judge changes: preserve original versus proxy labels and cache identities. Paid evaluation is explicit and uses a durable budget ledger.

Keep changes focused. Do not commit `.env`, weights, training data, downloaded webpages or runtime caches. `uv.lock` must match `pyproject.toml`. Third-party assets need their original license and attribution.
