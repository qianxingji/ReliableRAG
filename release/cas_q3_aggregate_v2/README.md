# Paired RAG Repair: Apache-2.0-aware aggregate verification candidate

This package verifies the reporting layer for a fixed empirical study of
whether a repaired RAG answer should replace its original answer. It is the
second, Apache-2.0-aware anonymous aggregate release candidate. It contains no author identity,
Git history, benchmark questions, reference answers, generated answers,
per-question outcomes, model weights or bootstrap multiplicities.

## Supported result

The study contains 6,000 question groups and 18,000 traces across three
datasets and three retrievers. Every non-Keep policy receives the same global
action allocation of 900 traces. The primary family uses 20,000
dataset-stratified question-cluster bootstrap draws and six endpoints: EM and
Damage for each of three ordered comparisons.

The only supported joint positive comparison is `HGB_GBV_R` versus
`GBV_ONLY_R`. The package does not establish a joint advantage over
`HGB_ONLY_R`, advancement of `ROA-FULL`, transfer to another reader or domain,
faithfulness improvement, a deployment speedup, or a new selector algorithm.

## Verify

Use Python 3.10 or newer from the package root:

```text
python scripts/verify_cas_q3_claim_statistics.py
```

The command uses only the Python standard library. Its JSON output must contain
`"status": "PASS_CAS_Q3_STATISTICAL_STATEMENT_VERIFICATION"` and
`"checks": 129`.

The verifier authenticates the three aggregate inputs by SHA-256, checks the
nine-policy arithmetic and comparison directions, and confirms the frozen
bootstrap description in the archived analysis source. It does not recompute
the bootstrap or inspect raw outcomes.

## Reproduction boundary

This package supports aggregate reporting verification only. The original
study used private, hash-bound benchmark assets, pretrained snapshots,
environments and sealed execution outputs. Those materials are outside this
package. The completed 180-trace neural replay was a bounded witness and was not
a second full 18,000-trace neural execution.

Seven historical upstream estimators lack their original per-estimator
fit-time ID/matrix receipts and an independent original-fit witness. The study
also lacks standalone policy latency, uniform end-to-end latency, canonical
peak memory for all stages and FLOP measurements. These limits remain part of
the scientific record.

## License and distribution status

`MANIFEST.json` is authoritative for package membership and content classes.
The included `LICENSE` is Apache License 2.0 and applies to the project-authored
code identified by the manifest. It does not grant rights to benchmark data,
model weights, model outputs, third-party software, aggregate evidence or
documentation outside that stated scope. None of the excluded third-party
payloads is included here.

This candidate is not authorized for public distribution. Legal holder/year,
institutional release review, the Qwen and DeBERTa boundary reviews, selected-
journal reviewer access, and a persistent archive identifier remain open. See
`THIRD_PARTY_NOTICES.md` for the upstream inventory and required release action.
