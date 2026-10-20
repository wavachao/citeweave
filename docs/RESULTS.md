# Evaluation results

Evaluated on 2026-10-19 with an NVIDIA RTX 4090 D (24,564 MiB), Python 3.12, PyTorch 2.7.1+cu128 and Transformers 4.57.6. The tables cover image ranking, local generation and a 20-query DeepSeek-judged comparison. Dataset splits and metric definitions are in the [experiment protocol](PROTOCOL.md).

## Image ranking

The training snapshot contains 1,146 usable query groups. A deterministic query-level split assigns 1,024 groups / 11,403 image pairs to training and 122 groups / 1,292 pairs to validation. Positive examples have released VLM relevance scores ≥8, negatives ≤3; intermediate scores are excluded. The recorded audit found zero benchmark-query overlap.

| Ranker | Validation NDCG@5 |
|---|---:|
| Frozen BGE-small cosine similarity | 0.73963 |
| Pointwise MLP on frozen embeddings | 0.71382 |
| Pairwise cosine residual head | 0.73963 |
| Pretrained MS MARCO MiniLM cross-encoder | 0.73828 |
| Task-tuned cross-encoder, selected epoch 1 of 3 | 0.74961 |

The validation difference over cosine is +0.00998, with a descriptive paired-bootstrap 95% interval of [-0.03172, 0.05366] (10,000 resamples, seed 42). This is the same validation split used for checkpoint selection.

The selected relevance threshold is **0.55**, chosen by validation micro-F1. At this threshold, precision is 0.5151 and recall is 0.6373. Lowering it to 0.40 raises recall to 0.7390 and reduces precision to 0.4386.

### Held-out component test

After checkpoint and threshold selection, the frozen ranker was tested on level-1 image captions. Candidates include all valid captioned, scored images, deduplicated by archive URL. Unlike the generation comparison, this test does not apply the reference top-k prefilter.

Of 194 questions, 186 have a defined positive-gain ranking target, covering 2,491 image pairs; eight empty or zero-gain cases are listed in the report. This test uses linear gains from the released 0–10 VLM relevance labels; validation uses binary labels.

| Ranker | Test graded NDCG@5 |
|---|---:|
| Frozen BGE cosine | 0.724448 |
| Task-tuned cross-encoder | 0.759809 |
| Paired difference | +0.035361 |

The paired query-bootstrap 95% interval is **[0.014515, 0.056550]** (10,000 resamples, seed 42). Independent scikit-learn recomputation agrees within 4.45e-16. Weights remained unchanged during testing.

## Generation comparison

All five tracks attempted the same 194 held-out level-1 questions. They use Qwen2.5-7B-Instruct, a shared candidate prefilter, a 24,576-token input limit and a 1,600-token output limit. Distilled tracks additionally load the same released adapter. Image selection follows each method's own policy; output counts are measured below.

| Method | Execution successes | Valid evaluator inputs | Median generation time | Mean unique images | Diagnostic image recall |
|---|---:|---:|---:|---:|---:|
| M²RAG single-stage | 194/194 | 191/194 | 16.86 s | 2.129 | 0.8836 |
| CiteWeave | 194/194 | 194/194 | 8.04 s | 0.871 | 0.7241 |
| M²RAG multi-stage | 194/194 | 194/194 | 30.71 s | 3.216 | 0.9865 |
| Distilled M²RAG single-stage | 194/194 | 187/194 | 19.78 s | 1.923 | 0.8182 |
| Distilled CiteWeave | 189/194 | 189/194 | 11.66 s* | 1.492* | 0.8220* |

*Distilled CiteWeave summaries cover its 189 successful predictions. Five answers reached the output cap: `1jphmq`, `1vtk4p`, `407zex`, `7ixgmx`, `j2ozz`.

Diagnostic recall deduplicates positive image URLs and assigns 1 to questions without a positive image. The quality evaluator instead retains the original positive-image list denominator. Output-cap counts are 2 for each base M²RAG track, 0 for base CiteWeave, 25 for distilled single-stage and 5 for distilled CiteWeave. No input truncations were recorded across the five tracks.

### Image selection and coverage

CiteWeave produced 72 answers without images, compared with 25 for M²RAG multi-stage. The attribution audit accounts for all 72:

| Cause | Questions |
|---|---:|
| No candidates after the shared reference prefilter | 23 |
| Every candidate below the selector's relevance threshold | 49 |
| Selected images lost during placement | 0 |

The selector favors relevance over a fixed number of illustrations. Its threshold was calibrated on training validation data. This yields fewer images and lower coverage in the generation comparison. A count-matched comparison would require a separate selection policy and new generation runs at a fixed per-question image count; the recorded runs use each method's native policy.

### Parser controls

The original single-stage parser discarded three nonempty base-model answers and produced seven inconsistent distilled image-placeholder exports. Supplementary controls reprocess the same raw generations:

| Control | Base single-stage | Distilled single-stage |
|---|---|---|
| Outer-fence repair (v1) | 71 exports changed; 3 empty answers recovered | No export changes; 7 inconsistencies remain |
| Outer-fence and duplicate-marker repair (v2) | 71 exports changed; 2 repeated markers removed | 7 exports changed; 40 repeated markers removed |

Both v2 controls yield 194 valid evaluator inputs. Integrity checks preserve parent model inputs, raw responses, evidence, usage and call records. The generation table reports the original exports; repaired exports have separate run identities. Output-cap flags remain attached to their parent predictions.

## DeepSeek-judged paired comparison

A deterministic SHA256(`42:query_id`) ordering selects 20 of the 194 questions for each method. The comparison evaluates 40 existing base-model answers using the original eight metrics, prompts and pooling with a DeepSeek judge. The baseline contains 58 output images and CiteWeave 16; answers without images number 3 and 8, respectively.

| Metric (0–1) | M²RAG multi-stage | CiteWeave | Difference |
|---|---:|---:|---:|
| Fluency | 0.70500 | 0.69000 | -0.01500 |
| Response relevancy | 0.84500 | 0.89000 | +0.04500 |
| Context precision | 0.54438 | 0.42502 | -0.11937 |
| Faithfulness | 0.65068 | 0.71060 | +0.05991 |
| Image coherence | 0.74310 | 0.78750 | +0.04440 |
| Image helpfulness | 0.63966 | 0.73125 | +0.09159 |
| Image reference | 0.73966 | 0.75625 | +0.01659 |
| Image recall | 0.95000 | 0.76250 | -0.18750 |
| Overall | 0.72718 | 0.71914 | -0.00805 |

The paired query-bootstrap 95% interval for the overall difference is **[-0.06090, 0.04762]** (10,000 resamples, seed 42). CiteWeave has higher observed relevancy and faithfulness, with lower context precision and image recall. Image coherence, helpfulness and reference scores are pooled over each method's output images. These exploratory estimates cover 20 questions; the overall difference remains uncertain at this sample size.

The pilot uses `deepseek-flash` with thinking disabled and an 8,192-token output cap. All 700 requests in the completed protocol ended with `stop`, and both methods returned the same system fingerprint. An earlier 2,048-token attempt encountered 12 truncated responses among 149 started requests; its cache is separate. The shared ledger's conservative cost bound is USD 1.2502971, including a reservation for one interrupted request. See [DeepSeek evaluation](DEEPSEEK_PROXY.md) for the adapter and budget calculation.

The original GPT-4o/GPT-4o-mini judge configuration is available through the evaluator bridge. The recorded quality evaluation covers the 20-query DeepSeek pilot; the remaining predictions have been generated and staged for evaluation.

## Reproduction artifacts

The generation source is archived with the [v0.1.0 release](https://github.com/wavachao/citeweave/releases/tag/v0.1.0). Its hashes and reference commit are listed in the [protocol](PROTOCOL.md). The application has continued to receive serving and parsing fixes after that snapshot.

Training and evaluation scripts write the following artifacts under the project root. Runtime logs and downloaded datasets are excluded from the source repository.

| Path | Contents |
|---|---|
| `runs/data-audit.json` | Dataset and query-overlap audit |
| `runs/crossencoder/` | Training report, selected checkpoint and calibration diagnostics |
| `runs/ranker-test-level1-v1/` | Frozen ranker manifest, report and per-query scores |
| `runs/comparison-plan.json` | Frozen generation settings and track definitions |
| `runs/comparison-v1-*/` | Predictions, failures, usage and image-selection diagnostics |
| `runs/official-evaluation/` | Staged judge inputs and identity manifests |
| `runs/deepseek-proxy-evaluation/` | Paired report and pilot integrity audit |
