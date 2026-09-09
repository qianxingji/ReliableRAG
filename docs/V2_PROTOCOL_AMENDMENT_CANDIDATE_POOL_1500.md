# DAA-V2 prospective amendment — 1,500-row shared candidate pools

## Status

**Prospective protocol amendment recorded after the 4,500-ID cohort freeze and before candidate-pool construction, retrieval, generation, scoring, action selection, or fresh-label access.**

This amendment fixes the candidate-pool contributor rule for the prospective DAA-V2 fresh confirmatory study. It does not change the frozen evaluation IDs, DAA-V2 architecture, HGB backbone, GbV comparator, action budget, model parameters, statistical tests, or success criteria.

## Why this clarification is required

The historical main study used bounded selected-split pooled candidate corpora built from the selected evaluation rows. A later small Fresh-ID extension used 200 evaluation rows plus 800 corpus-only contributors per dataset to keep a 1,000-row contributor scale. The new confirmatory cohort is larger: 1,500 frozen evaluation questions per dataset.

Carrying the old `200 + 800` rule forward is impossible without changing the evaluation cohort, while choosing a new arbitrary set of extra corpus-only contributors would introduce another discretionary selection step after the final evaluation IDs are already frozen.

Therefore the primary prospective candidate-pool rule is fixed as follows.

## Frozen contributor rule

For each dataset, the candidate-pool contributor set is **exactly the 1,500 already frozen evaluation question IDs for that dataset**.

- HotpotQA contributors: the 1,500 frozen HotpotQA evaluation IDs from the full distractor-validation source.
- 2WikiMultiHopQA contributors: the 1,500 frozen 2WikiMultiHopQA evaluation IDs from the corrected development source.
- MuSiQue contributors: the 1,500 frozen MuSiQue evaluation IDs from the accepted train source.

No additional corpus-only contributor rows are added to the primary pool. No frozen evaluation row is removed. No contributor is selected using retrieval quality, answer correctness, supporting facts, model outputs, or any other outcome-dependent signal.

The contributor set is therefore an exact deterministic function of the already sealed `selected_fresh_ids.jsonl`.

## Runtime-only source projection

Candidate-pool construction may read only the runtime fields required by the accepted retrieval pipeline:

- stable question ID;
- question text, where needed for binding the selected runtime cohort;
- context/passage title;
- ordered context/passage sentence or paragraph text;
- source-local structural indices required to preserve deterministic passage order.

The following are forbidden from the runtime projection and candidate-pool construction path:

- answer or answer aliases;
- supporting-fact labels or supporting flags;
- decomposition/evidence annotations;
- correctness, EM, F1, recovery, damage, or any derived outcome;
- any Gold-aware retrieval score or oracle signal.

The field-level guard must fail closed if a prohibited field is emitted to the pool-freeze namespace.

## Candidate-pool construction rule

Reuse the already validated private Phase10 source-projection and pooled-corpus construction implementation rather than reimplementing corpus semantics for V2.

The pool construction must preserve the accepted behavior:

- pool passages from all contributor rows within one dataset;
- strip Gold/evaluation annotations before corpus construction;
- deduplicate by the accepted normalized title plus passage/sentence-content rule;
- preserve deterministic canonical text rendering and document ordering/ID construction from the accepted implementation;
- build one shared pool per dataset;
- use that same dataset pool for BM25, Dense, Hybrid/RRF, and the later missing-information repair retrieval.

If the accepted Phase10 construction implementation cannot be located and hash/provenance-verified, stop. Do not silently recreate a similar corpus builder.

## Shared-method fairness

DAA-V2, raw HGB, and GbV do not receive separate retrieval corpora or separate answer branches. The later experiment must use exactly the same frozen dataset pool, retriever outputs, original evidence, repaired evidence, original answer, and repaired answer for every arbitration method.

The scientific comparison remains a post-repair arbitration comparison, not a comparison of separately tuned retrieval pipelines.

## Pool scope and interpretation

The primary candidate pools remain **bounded and transductive with respect to candidate availability** because the frozen evaluation rows themselves contribute candidate passages to their dataset pool. This is deliberate continuity with the historical bounded selected-split design and must be disclosed in the manuscript.

This amendment does not create or imply a FullWiki/open-domain result.

The contributor scale is now 1,500 rows per dataset rather than the historical 1,000-row main/fresh-extension scale. This follows mechanically from the larger frozen evaluation cohort and must be reported as a prospective design change, not hidden as an unchanged corpus size.

## Freeze outputs required before retrieval

Before any retriever is run, save and independently validate:

- exact contributor ID ledger for each dataset;
- runtime-only source projection hash for each dataset;
- candidate document count before and after deduplication;
- exact candidate-pool content SHA-256/fingerprint for each dataset;
- source raw/cache digest references;
- source-projection implementation hash;
- corpus-construction implementation hash;
- deduplication/canonicalization configuration hash;
- a candidate-pool freeze seal binding all of the above to the frozen 4,500-ID cohort.

A clean second construction from the same immutable inputs must reproduce the exact same candidate-pool fingerprints before the freeze is accepted.

## Hard stop

Candidate-pool freeze does **not** authorize BM25/Dense/Hybrid retrieval, dense embedding/index construction, reader generation, repair-query generation, likelihood scoring, V2/HGB/GbV scoring, action selection, Gold mapping, or evaluation.

Each later stage requires a new explicit author instruction.
