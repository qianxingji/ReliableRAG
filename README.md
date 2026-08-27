# ReliableRAG — Codex Research Workspace

This workspace is prepared for an SCI Q1 / CCF-level RAG research project under a single RTX 5060 Ti 16GB constraint.

## First Codex instruction
Open this repository in Codex and send only:

> Read AGENTS.md and CODEX_TASK_PHASE0.md, then execute Phase 0 exactly as specified. Stop after Phase 0.

Do not ask Codex to implement the full method before the oracle headroom audit in Phase 2.

## Phase 0 dataset verification

Phase 0 contains only dataset loading, normalization, documentation, and smoke
tests. It does not implement retrieval, generation, or evidence intervention.

From the repository root with Python 3.10 or newer:

```powershell
python -m unittest discover -s tests -v
python -m scripts.smoke_datasets --limit 10
```

See `docs/DATASETS.md` for sources, schema, annotation boundaries, and caveats.
