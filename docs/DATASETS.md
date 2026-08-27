# Phase 0 datasets

Phase 0 validates the public development data for HotpotQA and
2WikiMultiHopQA. Raw downloads live under `data/raw/` and are ignored by Git.
No dataset statistics in this document are inferred from unexecuted runs.

## Common normalized schema

Both loaders return `NormalizedExample` records with these fields:

- `id`: source question identifier.
- `dataset`: canonical dataset name.
- `split`: the loaded split name.
- `question`: question text.
- `answer`: reference answer.
- `documents`: ordered titled documents, each retaining its ordered sentences.
- `evaluation_only`: gold supporting facts and source-specific annotations.

Each gold supporting fact is a `(title, sentence_index)` reference, represented
as an object with `title` and zero-based `sentence_index`. It is stored only at
`evaluation_only.gold_supporting_facts`.

Runtime retrieval code must consume `RuntimeExample`, created by
`NormalizedExample.runtime_view()`. That type contains `id`, `dataset`,
`split`, `question`, and `documents`; it contains neither the reference answer
nor any evaluation-only annotation. This is the Phase 0 label-leakage boundary.

## HotpotQA

- Public source: the [official HotpotQA project](https://hotpotqa.github.io/)
  and its [official repository](https://github.com/hotpotqa/hotpot).
- Phase 0 split: distractor development
  (`hotpot_dev_distractor_v1.json`).
- Download: the official CMU-hosted JSON linked by the project. If that legacy
  host is unavailable, the Phase 0 utility falls back to the public HotpotQA
  Hugging Face dataset viewer's validation preview. The fallback is stored
  with `_hf_preview` in its filename and is sufficient only for the 10-row
  smoke check; it is not presented as a complete development split.
- Available annotations: `_id`, `question`, `answer`, `context`,
  `supporting_facts`, `type`, and `level` in the validated development file.
- Supporting facts: `[title, sentence_id]` pairs, where `sentence_id` is a
  zero-based index into the sentence list of the titled context paragraph.
- Caveats: the distractor setting supplies ten context paragraphs, including
  gold paragraphs and distractors. These supplied contexts are dataset inputs,
  not evidence retrieved by a future open-domain retriever. `type` and `level`
  are retained inside `evaluation_only.source_fields`. The full-wiki dev file
  instead contains paragraphs returned by the dataset authors' retrieval
  system and may omit gold paragraphs; Phase 0 does not use it.

HotpotQA data is distributed by its authors under CC BY-SA 4.0.

## 2WikiMultiHopQA

- Public source: the authors'
  [official repository](https://github.com/Alab-NII/2wikimultihop), which links
  the public Dropbox archives.
- Phase 0 split: development (`dev.json`) from the authors' April 7, 2021
  corrected archive (`data_ids_april7.zip`). If Dropbox is unavailable, the
  smoke utility falls back to a public Hugging Face repackaging whose dataset
  card states that the underlying questions, answers, and contexts are
  unaltered. The fallback is stored with `_hf_preview` in its filename and is
  sufficient only for the 10-row smoke check; it is not presented as a
  complete development split.
- Available annotations in the validated file: `_id`, `question`, `answer`,
  `context`, `supporting_facts`, `evidences`, `type`, `entity_ids`,
  `evidences_id`, and `answer_id`.
- Supporting facts: `[title, sentence_id]` pairs following the same zero-based
  paragraph-sentence convention as HotpotQA.
- Caveats: the dataset has four reasoning types: comparison, inference,
  compositional, and bridge-comparison. The April 2021 archive fixes paragraph
  sentence-segmentation inconsistencies; older mirrors may not match its
  indices. Structured evidence triples and Wikidata IDs are gold annotations,
  so the loader retains them only inside `evaluation_only.source_fields`.
  Dataset test rows do not contain answer or supporting-fact labels and are not
  part of the Phase 0 smoke run.

## Reproduction

From the repository root with Python 3.10 or newer:

```powershell
python -m unittest discover -s tests -v
python -m scripts.smoke_datasets --limit 10
```

The smoke command downloads the two public development sources when they are
absent, normalizes ten rows from each, validates the expected count, and prints
a JSON summary including the raw fields actually discovered.
