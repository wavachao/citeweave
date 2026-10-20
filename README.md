# CiteWeave

**Multimodal web search. Useful images. Traceable answers.**

[![Checks](https://github.com/wavachao/citeweave/actions/workflows/ci.yml/badge.svg)](https://github.com/wavachao/citeweave/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-235c45)](LICENSE)

[简体中文](README.zh-CN.md) · [Deployment](docs/DEPLOYMENT.md) · [Configuration](docs/CONFIGURATION.md) · [API](docs/API.md) · [Evaluation](docs/RESULTS.md)

CiteWeave is a self-hosted search application that turns public webpages into answers with relevant illustrations and inspectable sources. It retrieves actual images, describes their visible content, selects useful figures, and places them alongside the explanation. Every displayed image retains a path back to its original webpage.

![CiteWeave search workspace](docs/screenshots/workspace.png)

## What it does

- **Search and read the web** — automatic discovery or up to five explicit public source URLs; no benchmark dataset is needed to use the application.
- **Explain with images** — local visual descriptions, query–caption ranking, redundancy control, and illustrations placed next to related paragraphs.
- **Keep evidence inspectable** — paragraph citations, source cards, image previews, original-page links, and an image viewer.
- **Support everyday use** — browser-local search history, reusable answers, copy, Markdown export, and explicit refresh.
- **Run in your own environment** — local Qwen models on one NVIDIA GPU, or optional DeepSeek text generation. Fonts and interface assets are self-hosted.
- **Operate as a protected workspace** — bearer-token/API access, HttpOnly browser sessions, request limits, bounded SQLite answer caching, health checks, and a non-root container definition.

English typography uses **Inter**; Chinese text uses **LXGW WenKai / 霞鹜文楷**. Both font distributions include their licenses.

## Quick start

### Requirements

- Linux, Python 3.12, and [uv](https://docs.astral.sh/uv/).
- A CUDA-capable NVIDIA GPU. The complete local pipeline has been exercised on a **24 GB RTX 4090 D**. Other hardware is not yet validated.
- A driver compatible with the locked PyTorch CUDA 12.8 wheels, about **50 GB free disk**, and outbound access to model downloads and public webpages.

```bash
git clone https://github.com/wavachao/citeweave.git
cd citeweave
uv sync --frozen
cp .env.example .env
uv run python scripts/download_models.py
uv run python -m citeweave serve
```

Open **http://127.0.0.1:8765**. Ask a question or supply specific source URLs. The first request loads models and may take longer than subsequent searches.

The default model download installs the three application models only. Training data, benchmark images, and the reference implementation are optional research resources. Model revisions are pinned; inference loads local files.

### Add the trained image ranker

The application works with a cosine-similarity fallback. To use the released task-tuned query–caption cross-encoder:

```bash
uv run python scripts/download_ranker.py
```

The downloader verifies the release archive and weight hashes before installing into `runs/crossencoder/`. The ranker is derived from MS MARCO MiniLM and uses Apache-2.0; application code uses MIT. See [model provenance](docs/MODELS.md).

### Deploy a workspace

Set a random `CITEWEAVE_ACCESS_TOKEN` with at least 32 characters in `.env`. For example, generate a value locally with `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"`.

```bash
docker compose up --build -d
```

The supplied Compose configuration requires NVIDIA Container Toolkit, persists cached answers/images, mounts model resources read-only, and binds the host port to loopback. A reverse proxy can provide HTTPS for a team workspace. Network binding requires an access token. **Use one application worker per GPU.** Follow the [deployment guide](docs/DEPLOYMENT.md) for setup, readiness checks, backups, and operating limits.

## How it works

```mermaid
flowchart LR
    Q[Question and optional URLs] --> R[Public web retrieval]
    R --> E[Source text and images]
    E --> V[Local image descriptions]
    V --> S[Relevance ranking and deduplication]
    E --> P[Text evidence packing]
    S --> G[Grounded answer generation]
    P --> G
    G --> B[Resolve known source and image IDs]
    B --> U[Interleaved answer and source cards]
```

The application resolves generated markers against retrieved evidence. It never accepts model-generated image URLs as new evidence. Image descriptions distinguish visible content from publisher captions. Pictures are illustrations, not independent proof of measurements or causal claims.

The backend uses FastAPI, PyTorch, Transformers, sentence-transformers and SQLite. The browser interface uses plain HTML, CSS and JavaScript, with no frontend build step. See [architecture](docs/ARCHITECTURE.md).

## DeepSeek Harness

The [CiteWeave Harness plugin](plugins/deepseek-harness/README.md) adds sourced illustrations to agent answers using Harness's existing Markdown image renderer. It calls the evidence API, imports selected image files into Harness, and gives its answer model the retrieved text, visual descriptions and original source links. CiteWeave does not generate a second answer in this mode. The Python GPU service remains a separate deployment.

## API

```bash
curl http://127.0.0.1:8765/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CITEWEAVE_ACCESS_TOKEN" \
  -d '{"query":"How did Eratosthenes measure Earth?","urls":["https://en.wikipedia.org/wiki/Eratosthenes"],"verify_images":true}'
```

Responses contain answer blocks, resolved image/source IDs, source metadata and timing. `refresh: true` bypasses the recent-answer cache. See the [API reference](docs/API.md) or `/docs` on your own deployment.

## Evaluation and reproducibility

CiteWeave includes the pinned original M²RAG baseline, controlled generation, training scripts, input validation, explicit failure records, and separate original/proxy judge protocols.

| Measurement | Reference | CiteWeave |
|---|---:|---:|
| Image ranking, graded NDCG@5¹ | 0.72445 cosine | 0.75981 trained cross-encoder |
| Median generation time, 194 questions² | 30.71 s original multi-stage | 8.04 s |
| Overall DeepSeek proxy, 20 paired questions³ | 0.72718 original multi-stage | 0.71914 |

¹ 186 defined held-out questions, released VLM weak relevance labels. The paired difference interval is [0.01451, 0.05655]. This measures ranking, not answer quality.

² Same 7B model and recorded generation budgets on one 4090 D. CiteWeave inserts fewer images and has lower image coverage; the speed result is not an overall quality claim.

³ Reuses original metrics with a different judge. The overall difference interval [-0.06090, 0.04762] includes zero. **No claim of exceeding M²RAG or reproducing the paper's GPT-4o scores is made.** Full settings, failures, and all eight metrics are in [measured results](docs/RESULTS.md) and [the protocol](docs/PROTOCOL.md).

## Development

```bash
uv sync --frozen --group official
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
uv run pytest -q
```

CI runs the CPU-only contract suite without downloading model weights. A GPU deployment must also pass a real retrieval/generation check. Contributing instructions, test scope, and checks for changes are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Operating boundaries

- The shipped service is a **single-workspace, single-GPU application**. It serializes expensive work and returns a retryable busy response. It is not a multi-tenant inference cluster.
- Web access depends on upstream availability. For a managed deployment, configure a controlled SearXNG endpoint rather than relying on the default DDGS discovery service.
- Dynamic pages, paywalls, missing images, and insufficient evidence can limit answers. Always inspect sources for consequential decisions.
- Browser history stays on the device; server answers and images are cached on the deployment volume. Configure retention and avoid entering secrets in queries.

## License and acknowledgments

Application code: [MIT](LICENSE). Models, fonts, datasets, and retrieved material retain their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md). Documentation screenshots containing the attributed Wikimedia diagram use CC BY-SA 4.0.

Built with [Qwen](https://github.com/QwenLM), [BGE](https://github.com/FlagOpen/FlagEmbedding), and the [M²RAG reference implementation](https://github.com/maziao/M2RAG).
