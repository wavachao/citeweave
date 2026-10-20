# Experiment protocol

This document defines the datasets, generation settings and evaluation procedures behind the [reported results](RESULTS.md). Live-web requests use newly retrieved sources; benchmark runs use the released M²RAG evidence snapshot.

## Data and splits

The released `dev_set.jsonl` contains 750 unique questions: 200 at level 1, 300 at level 2 and 250 at level 3. The reference generation configuration selects level 1.

Six questions used during format development and UI checks are excluded: `14v6kn`, `1847u5`, `18amxd`, `2xhua3`, `5ajwkl`, `1zghby`. This leaves **194 level-1 questions**, or 744 across all levels. `--include-pilot` restores the excluded questions for full-subset runs.

The released training snapshot contains 1,605 records. Ranker training uses the training-only BSON relevance labels: scores ≥8 are positive, ≤3 negative, and intermediate scores are excluded. Query deduplication and a SHA-256 split of normalized questions produce 1,024 training and 122 validation groups. Labels come from the released VLM annotations.

Benchmark-query overlap is checked before training. Checkpoint selection and relevance-threshold calibration use the training validation split. Benchmark relevance scores and evaluator rationales are excluded from inference features. The observed 20-query pilot is a development result for subsequent method changes; future confirmatory tests need unobserved questions.

## Generation tracks

The five tracks are M²RAG single-stage, M²RAG multi-stage, CiteWeave, distilled M²RAG single-stage and distilled CiteWeave. Reference classes and prompts come from commit `ea6b9977f5a153215b38cd9a6aa3e4702ffbda22` of [M²RAG](https://github.com/maziao/M2RAG).

| Setting | Value |
|---|---|
| Base generator | Qwen2.5-7B-Instruct |
| Distilled tracks | Same released M²RAG adapter |
| Hardware | One NVIDIA RTX 4090 D |
| Text/vision/adapter precision | BF16 |
| Ranking encoder precision | FP32 |
| Input token limit | 24,576 |
| Output token limit | 1,600 |
| Candidate image cap | 10 |
| Candidate prefilter | Shared original prefilter using released relevance annotations |
| Output image count | Selected independently by each method |

The annotation-based prefilter is part of the reference benchmark setup. CiteWeave receives the resulting candidate pool without relevance labels. Base and distilled results are reported separately.

CiteWeave generates paragraphs with source/image ID markers, resolves known IDs and removes duplicate image placements. If the answer contains no valid image marker, semantic paragraph matching can place preselected illustrations above similarity 0.3. The reference tracks retain their original prompts, stage logic and parsing behavior.

Decoding computes last-token logits to reduce prefill memory. CiteWeave records output-cap exhaustion as an incomplete-answer failure. All tracks retain cap flags, failed predictions, image counts, timing and input-truncation diagnostics.

## Ranking component test

The frozen ranker is tested on the 194 held-out level-1 questions using all valid captioned, scored images, deduplicated by archive URL. This component test omits the generation prefilter. Model inputs are question/caption text; released relevance scores supply the test labels.

Test NDCG@5 uses linear gains from the released 0–10 scores. Training-validation NDCG uses binary labels. Empty or zero-gain test cases are listed explicitly and excluded from the defined-case ranking mean. The paired query bootstrap uses 10,000 resamples and seed 42.

## Quality metrics and judges

The evaluator retains the original eight normalized metrics:

- Text: fluency, response relevancy, context precision and faithfulness.
- Images: coherence, helpfulness, reference and recall.

Text metrics and image recall are averaged over questions. The three image precision metrics are pooled over output images. Recall divides the number of matching positive URLs by the original positive-image list length, preserving duplicate entries in the denominator; questions with no positive image receive 1. Overall is the mean of the eight aggregate metrics. Generation-only diagnostic recall deduplicates that denominator and is reported separately.

| Judge protocol | Configuration | Recorded coverage |
|---|---|---|
| Original | `gpt-4o-2024-08-06`; `gpt-4o-mini-2024-07-18` for RAGAS | Inputs staged |
| DeepSeek proxy | `deepseek-flash`, thinking disabled, 8,192 output tokens | 20 paired questions |

The DeepSeek protocol retains the original prompts, metric code and pooling. Context trimming uses the reference wrapper's approximate `cl100k_base` fallback. Pilot selection orders questions by SHA256(`42:query_id`) and takes 20 before reading scores. The [adapter guide](DEEPSEEK_PROXY.md) covers execution and spending limits.

Confidence intervals resample paired questions and recompute pooled image metrics on each draw. Per-metric intervals are exploratory, without multiplicity correction. Each report identifies its question subset, judge protocol, output counts and failures.

## Input validation and cache identity

Preflight checks planned predictions, nonempty answers, image IDs, placeholder counts, archive locations and image decoding. CiteWeave `iN` markers are mapped to original numeric IDs in evaluator input copies after candidate-index and URL checks. Parent predictions remain unchanged.

Request manifests hash raw predictions, staged inputs, image files and judge settings, including the reference commit, package versions and endpoint identity. Cache reuse requires matching identities. Credentials are excluded. Completion requires finite, correctly normalized scores for every expected task and agreement between recomputed aggregates and the original summary table.

`--prepare-only` validates and stages inputs without calling a judge. Paid runs require `--allow-paid-evaluation`. Original and DeepSeek protocols use separate caches and completion flags. Transport contract checks use intercepted requests and synthetic responses.

## Frozen source

The generation snapshot is distributed as `citeweave-generation-v1-source.tar.gz` in the [v0.1.0 release](https://github.com/wavachao/citeweave/releases/tag/v0.1.0).

| Artifact | SHA-256 |
|---|---|
| Generation implementation | `21b3848cb3d79e0419898923f563913b211fb488379beda224d9ef959f565d1f` |
| Generation uv lock | `a87433dc263e4b5bf57a95c3a2c7b1dc6daf4275b528b9dd85d501341839e7bd` |
| Source archive | `ecd76fc8da8f385d407f4cc6602eea960670ec9316b2f0fef090f3169da40bd2` |

Every prediction manifest records implementation and lock hashes, model revisions, precision, question IDs and generation settings. The archived source is loaded through `PYTHONPATH` for snapshot reproduction. Later application changes have their own implementation identities.

## Supplementary parser controls

The v1 single-stage control strips only an outer Markdown fence, preserving interior code fences and surrounding prose. V2 additionally removes repeated valid image-ID markers before the original handler, keeping the first occurrence. This addresses the upstream global-replacement mismatch between placeholder count and the unique output-image list.

Controls have separate output directories, parent prediction hashes and helper-source hashes. Integrity audits compare model inputs, raw responses, evidence, usage and calls against their parents. Existing run directories and output-cap flags are preserved. The [results](RESULTS.md#parser-controls) list export changes for each control.
