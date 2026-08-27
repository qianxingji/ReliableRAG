# Codex Task — Phase 0 Only

Read `AGENTS.md` and `docs/RESEARCH_PLAN.md` completely before making any changes.

We are beginning **Phase 0 only**.

Do NOT implement the proposed RAG method yet.

## Task
Prepare and validate the research repository.

1. Inspect the current repository.
2. Create/complete a clean Python project structure consistent with `AGENTS.md`.
3. Create `requirements.txt` or `pyproject.toml` with only necessary dependencies.
4. Implement dataset loaders for:
   - HotpotQA
   - 2WikiMultiHopQA
5. Download or load the datasets through official/public sources.
6. Normalize them into a common internal schema containing at least:
   - id
   - question
   - answer
   - context/documents
   - gold supporting facts when available
7. Gold supporting facts must be clearly marked `evaluation_only` and must not accidentally enter runtime retrieval components.
8. Add a smoke-test script that loads 10 samples from each dataset and prints a structured summary.
9. Add tests for dataset normalization.
10. Create `docs/DATASETS.md` documenting:
    - source
    - split
    - available annotations
    - how supporting facts are represented
    - dataset-specific caveats
11. Actually run the smoke tests.
12. Do not claim something works unless you have executed it.
13. Do not implement retrieval, generation, intervention, or paper writing yet.

## Before Coding
Inspect the existing implementation and reuse working components.

## After Coding
Actually execute the relevant tests and at least one end-to-end smoke run.
Never report estimated experimental results as measured results.
If the requested scientific assumption appears invalid based on actual results, report it instead of changing the experiment to force a positive result.

## Completion Report
At completion report:
- files created
- commands executed
- tests passed/failed
- dataset fields discovered
- unresolved issues
- exact command to reproduce Phase 0

Stop after Phase 0.
