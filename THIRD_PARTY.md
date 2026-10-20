# Third-party resources

- M²RAG code, prompts and original baseline implementation: https://github.com/maziao/M2RAG (MIT). The downloaded checkout retains its original LICENSE. Reference commit: `ea6b9977f5a153215b38cd9a6aa3e4702ffbda22`.
- M²RAG benchmark and distilled training resources: https://huggingface.co/collections/ylwt/m2rag-674695ac8d94d45f6b801482. Respect upstream dataset terms and the original rights of retrieved webpage/image owners. Images are not newly licensed by this project.
- Qwen2.5-7B-Instruct and Qwen2.5-VL-3B-Instruct: upstream model cards and licenses remain applicable. Model revisions are stored in each downloaded model's `source.json`.
- BAAI/bge-small-en-v1.5: upstream model card and license apply.
- cross-encoder/ms-marco-MiniLM-L-6-v2: upstream model card and Apache-2.0 license apply; the task-specific fine-tuning uses the training-only annotations described in the protocol.

- Inter Variable v4.1: https://github.com/rsms/inter, SIL Open Font License 1.1. Font and license are included in `src/citeweave/static/fonts/`.
- LXGW WenKai webfont package v1.7.0: https://github.com/chawyehsu/lxgw-wenkai-webfont. Font: SIL Open Font License 1.1; package CSS: MIT. Unmodified regular-weight webfont subsets, both licenses, and integrity/hash metadata are included in `src/citeweave/static/fonts/`. Original typeface: https://github.com/lxgw/LxgwWenKai.

The new application code is separate from the reference checkout. No model weights, training data, user credentials or benchmark image archives are bundled in the source distribution. The optional release ranker asset has a separate Apache-2.0 license and provenance manifest.

Documentation screenshots show the application with a public Wikipedia source and its retrieved diagram. Source links are visible in the UI. Third-party page/image content retains its original rights and is not covered by the application code's MIT license.

The diagram in `docs/screenshots/answer.png`, `sources.png` and `workspace.png` is [Eratosthenes measure of Earth circumference](https://commons.wikimedia.org/wiki/File:Eratosthenes_measure_of_Earth_circumference.svg), credited by Wikimedia Commons to cmglee, David Monniaux and jimht at shaw dot ca under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Changes: resized for webpage display and captured within the application UI; the diagram's content is unchanged. These screenshot files, including the new composition, are distributed under CC BY-SA 4.0. This does not change the MIT license of the application code. No endorsement by the diagram's authors is implied.
