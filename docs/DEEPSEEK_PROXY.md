# DeepSeek evaluation

The DeepSeek adapter runs the M²RAG evaluator's prompts and eight metrics with `deepseek-flash`. Both compared methods share judge settings, context trimming and pooling. Results are stored under a separate `deepseek` protocol identity.

The [Vision documentation](https://api-docs.deepseek.com/guides/vision/) describes image support. The recorded 2026-10-19 [pricing snapshot](https://api-docs.deepseek.com/quick_start/pricing/) maps `deepseek-flash` to DeepSeek-V4.1-Flash-1017. Returned model names, system fingerprints and adapter settings are recorded with each evaluation.

## Recorded paired pilot

The pilot evaluates 20 identical questions per method: base M²RAG multi-stage and base CiteWeave, using 40 existing answers. IDs are ordered by SHA256(`42:query_id`); copied predictions retain parent bytes and hashes.

| Measurement | Value |
|---|---:|
| M²RAG multi-stage overall | 0.7271848 |
| CiteWeave overall | 0.7191391 |
| Paired difference | -0.0080457 |
| 95% paired query-bootstrap interval | [-0.0609008, 0.0476231] |
| Completed-protocol requests | 700, all ending with `stop` |
| Shared budget | USD 2 |
| Ledger cost upper bound, including earlier attempt | USD 1.2502971 |

Both methods returned the same system fingerprint. Full metrics and image counts are in [evaluation results](RESULTS.md#deepseek-judged-paired-comparison).

## Run an evaluation

Install evaluator dependencies with `uv sync --frozen --group official` and fetch the pinned reference with `bash scripts/fetch_reference.sh`. Prepare benchmark data, images and model resources before generating predictions; see [models](MODELS.md) and the [protocol](PROTOCOL.md). Set `DEEPSEEK_API_KEY` in `.env` for paid execution.

For existing full generation runs, create paired subsets with:

```bash
uv run --group official python scripts/prepare_paired_subset.py runs/comparison-v1-base-multi runs/comparison-v1-base-citeweave --count 20 --seed 42
```

Use the resulting prediction directories as `BASELINE_RUN` and `CITEWEAVE_RUN`. The same batch name shares a spending ledger across both methods:

```bash
BASELINE_RUN=runs/comparison-v1-base-multi-proxy-pilot-v1
CITEWEAVE_RUN=runs/comparison-v1-base-citeweave-proxy-pilot-v1

# Validate and stage inputs without API requests.
uv run --group official python scripts/evaluate_official.py "$BASELINE_RUN" --judge-protocol deepseek --prepare-only
uv run --group official python scripts/evaluate_official.py "$CITEWEAVE_RUN" --judge-protocol deepseek --prepare-only

# Paid judging: USD 2 total, shared by both methods.
uv run --group official python scripts/evaluate_official.py "$BASELINE_RUN" --judge-protocol deepseek --allow-paid-evaluation --budget-usd 2 --budget-batch paired-proxy-pilot-v1
uv run --group official python scripts/evaluate_official.py "$CITEWEAVE_RUN" --judge-protocol deepseek --allow-paid-evaluation --budget-usd 2 --budget-batch paired-proxy-pilot-v1
uv run --group official python scripts/official_quality_report.py "$BASELINE_RUN" "$CITEWEAVE_RUN" --judge-protocol deepseek
```

These paths refer to generated run artifacts, which are excluded from the source repository. For a new experiment, use new prediction directories and a new batch identity; retain the existing ledger when resuming a run.

## Adapter and spending limit

The adapter disables thinking and SDK retries, caps outputs at 8,192 tokens and serializes requests through a cross-process lock. RAGAS retains its original prompts; context trimming uses the reference wrapper's approximate `cl100k_base` fallback. These settings enter the protocol fingerprint.

Before a request, the adapter reserves USD 0.3244032, calculated from the recorded 1,048,576-token context at USD 0.30/M input and 8,192 tokens at USD 1.20/M output. Metered responses refund unused reservation using peak cache-miss rates. Unknown, failed or interrupted requests retain their reservation. The ledger represents a conservative spending bound at the recorded prices.

Requests stop when the next reservation exceeds the remaining budget or the batch reaches 10,000 requests. Ledger profile changes are rejected. Resume with the same batch and ledger so interrupted calls remain accounted for. Review prices and model aliases before a new experiment.

The pilot ledger contains 849 started requests: 848 metered and one interrupted request with unknown usage. Metered usage totals USD 0.9332667 at the recorded rates; the retained reservation is USD 0.3170304. The earlier 2,048-token attempt had 12 truncated responses among 149 started requests. Its cache is separate from the completed 8,192-token protocol.

## Validation and output files

Proxy files use `work/deepseek-proxy/` and `runs/deepseek-proxy-evaluation/`. Reports require `--judge-protocol deepseek`; original-judge reports reject proxy cache identities. Proxy completion keeps `official_judge_completed` false.

```bash
uv run --group official python scripts/check_evaluator_transport.py --judge-protocol deepseek
```

The offline transport check intercepts an archived image after the reference 512-pixel resize/base64 conversion. It verifies the model, disabled thinking and token cap using a dummy key and a synthetic response. Contract tests cover sync/async calls, cancellation, unknown billing, retry behavior, spending limits and protocol isolation.
