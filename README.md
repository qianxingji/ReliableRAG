# ReliableRAG

ReliableRAG studies whether a fixed repaired RAG answer should replace the
original answer. The current paper is a controlled empirical study of accuracy
and damage under supervision-matched selection.

**Target: CAS Journal Ranking Q3 Submission Ready.** CAS ranking is distinct from
JCR quartiles. The applicable CAS year, category and institutional recognition
rule still require a named journal.

**CAS Q3 STATUS: NOT READY.** The Qwen scientific core and P0-A through P0-F are
closed. P0-G now has a deterministic anonymous aggregate candidate and clean
round-trip proof, but distribution remains withheld pending a project license
and final journal policy. Target-journal certification and the manuscript/final
independent audits remain open.

## Current scientific object

For each fixed original/repaired answer pair `(a0,a1)`, a policy chooses Keep or
Repair after both candidates and all scores have been acquired. The accepted
study contains:

- `Qwen/Qwen2.5-3B-Instruct` at revision
  `aa8e72537993ba99e69dfaafa59ed015b17504d1`;
- 6,000 question groups and 18,000 BM25/dense/hybrid traces from HotpotQA,
  2WikiMultiHopQA and MuSiQue;
- three fixed dataset-specific bounded candidate pools;
- one global action allocation of `K=900` traces;
- nine policies, including five supervision-matched fitted heads; and
- 20,000 dataset-stratified question-cluster bootstrap draws.

The focal policy `HGB_GBV_R` is an ordinary two-input calibrated logistic head.
HGB is an upstream signal and comparator. GbV is a project-specific paired
adaptation of Generate but Verify Post-Answering NLI. The project does not claim
a new selector architecture or a novel top-level algorithm.

## Accepted result boundary

The primary family contains three ordered comparisons, each with EM and Damage
endpoints. Adjusted ranges use the frozen six-endpoint family and reallocate the
global top-K within each bootstrap draw.

| Ordered comparison | EM difference, pp | Damage difference, pp | Joint rule |
|---|---:|---:|---|
| ROA-FULL - HGB_GBV_R | +0.0444 `[-0.1333,+0.2037]` | +0.0611 `[+0.0000,+0.1278]` | Not met |
| HGB_GBV_R - HGB_ONLY_R | +0.0556 `[-0.1556,+0.3167]` | -0.0833 `[-0.1833,-0.0056]` | Not met |
| HGB_GBV_R - GBV_ONLY_R | +0.2333 `[+0.0722,+0.4333]` | -0.0722 `[-0.1444,-0.0278]` | Met |

The supported positive statement is limited to HGB_GBV_R versus GBV_ONLY_R on
this fixed Qwen cohort. The result does not establish joint improvement over
HGB_ONLY_R, advancement of ROA-FULL, reader transfer, unseen-domain transfer,
faithfulness improvement, a risk guarantee or deployment speedup.

## Evidence map

Start with:

- [Q3 project charter](docs/cas_q3/PROJECT_CHARTER.md)
- [Current task and gates](docs/cas_q3/CURRENT_TASK.md)
- [Current method and Claim boundary](docs/cas_q3/CURRENT_METHOD.md)
- [Evidence index](docs/cas_q3/EVIDENCE_INDEX.json)
- [Direct-neighbor literature audit](docs/cas_q3/P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md)
- [Complete result and Claim map](docs/cas_q3/P0_B_RESULT_CLAIM_MAP.md)
- [Method and fairness account](docs/cas_q3/P0_C_METHOD_FAIRNESS_ACCOUNT.md)
- [Statistical statement verification](docs/cas_q3/P0_D_STATISTICAL_STATEMENT_VERIFICATION.md)
- [Provenance, contamination, adaptation and failure disclosures](docs/cas_q3/P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md)
- [Claim-scoped cost table](docs/cas_q3/P0_F_CLAIM_SCOPED_COST_TABLE.md)
- [Reviewer release, license and anonymization audit](docs/cas_q3/P0_G_REVIEWER_RELEASE_LICENSE_ANONYMIZATION_AUDIT.md)

The full `docs/cas_q2/` tree is retained as historical execution and acceptance
evidence. Its old target/status and next-step language is superseded by the Q3
authority tree; scientific receipts and failures remain unchanged.

## Recheck the frozen reporting layer

The aggregate-only verifier reads three sealed empirical-analysis files and the
frozen analysis source. It does not read Gold, references, answer payloads,
per-question outcomes, actions or bootstrap multiplicities.

```powershell
python scripts/verify_cas_q3_claim_statistics.py
python -m unittest tests.test_empirical_analysis
```

The verifier checks exact input hashes, nine-policy arithmetic, units,
comparison points, interval roles, multiplicity metadata, endpoint direction and
the strict joint rule. The earlier full independent D validator separately
checked all 20,000 draws and explicit-copy allocations; see
[empirical D acceptance](docs/cas_q2/EMPIRICAL_D_ACCEPTANCE.md).

## Data, models and private evidence

Raw benchmark material, answer payloads, model assets, private evidence kits and
large scientific outputs are intentionally excluded from Git. The repository
tracks only `.gitkeep` placeholders under `data/` and `outputs/`. Existing
private delivery/runbook evidence remains local and hash-bound.

Exact pretrained revisions and dependency locks are documented in the evidence
tree and `requirements/`. Benchmark use and model redistribution remain subject
to their upstream terms. A public or double-blind reviewer package must be
audited before release; the Git repository itself is not yet that package.

## Known limits

- One accepted reader condition.
- No novel top-level method and no joint advantage over HGB_ONLY_R.
- Seven original upstream estimators lack their original per-estimator fit-time
  ID/matrix receipts and an independent original-fit witness.
- Recorded ID exclusion is not semantic or pretraining decontamination.
- Phi failed its frozen semantic validation gate; Mistral stopped before
  engineering. Neither supplies effect or robustness evidence.
- Standalone policy latency, canonical C2/C3 accelerator peaks, uniform
  end-to-end latency and FLOPs were not measured.
- A top-level project license and an anonymized reviewer export remain pending.

See [AGENTS.md](AGENTS.md) for repository working rules. Historical task cards
are evidence records rather than current execution instructions.
