# Mistral GbV SentencePiece dependency recovery

Date: 2026-09-17
CAS Q3 status: **NOT READY**

## Scope

This record covers an engineering dependency check performed before the Mistral
development GbV stage was committed or executed. It is not a scientific result,
does not authorize the stage, and does not change the frozen reader, verifier,
cohort, eligibility rule, endpoint family or development tuning budget.

## Preserved failure

The first local slow-tokenizer smoke check used
`E:/paper/ReliableRAG/.venv/Scripts/python.exe` without the historical
SentencePiece package directory on `PYTHONPATH`. Loading the exact local
DeBERTa-v3 tokenizer stopped with:

```text
ImportError: DebertaV2Tokenizer requires the SentencePiece library
```

The attempt created no scientific output namespace and made no model forward,
fit, Gold or test access. It established that the original virtual environment
alone is insufficient; the failure must not be hidden by installing an
unrecorded replacement package.

## Hash-bound recovery

The accepted historical preflight already records SentencePiece 0.2.1 under:

```text
E:/paper/ReliableRAG/outputs/published_baseline_gbv_nli_v1/infrastructure/python_packages
```

With that exact directory as the sole `PYTHONPATH` value, a fresh process loaded:

```text
sentencepiece 0.2.1
DebertaV2Tokenizer vocabulary size 128001
transformers 4.53.2
```

The producer and independent validator now both:

1. rehash all 17 preflight-listed SentencePiece package files;
2. rehash the historical package provenance record;
3. rehash all seven local DeBERTa snapshot files and the source/preflight pins;
4. require the imported module to resolve inside the authenticated package root
   with version exactly 0.2.1; and
5. bind the exact package root into the executable freeze as `PYTHONPATH`.

No global or virtual-environment installation was performed. The recovered
tokenizer check and both independent asset-validation paths passed. The complete
Mistral-focused suite passed 61 tests. The GbV scientific stage remains
unexecuted and blocked on independent acceptance of every predecessor stage.

## Evidence boundary

This recovery proves only that the fixed local tokenizer dependency is available
and hash-bound. It does not prove NLI numerical replay, Mistral reader validity,
an effect over HGB-only, cross-reader robustness or submission readiness.
