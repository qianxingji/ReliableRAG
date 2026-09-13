# P0-E provenance, contamination, adaptation and failure disclosures

Decision: **PASS_FROZEN_Q3_DISCLOSURE_BOUNDARY.** These statements are mandatory
for the manuscript, supplement and release documentation. The PASS means the
known evidence and gaps are stated without inflation; it does not prove semantic
decontamination, complete historical training provenance or reader transfer.

## Data and cohort provenance

The study uses benchmark-supplied source frames for HotpotQA,
2WikiMultiHopQA and MuSiQue. The 6,000-question evaluation cohort is a
deterministic, prospectively fixed hash-order selection of 2,000 IDs per dataset
from the available frames after excluding the authenticated historical/opened-ID
union. It is neither a probability sample nor an independent draw from a new
domain.

The selected cohort has zero observed dataset/ID overlap with the known
18,600-question exclusion union. All three retrieval siblings share one question
identity and remain together in statistical resampling. ID separation establishes
only separation from the recorded project questions. It does not prove semantic
non-overlap, absence of paraphrases, absence from pretrained model corpora or
absence of unknown unlogged historical use.

Candidate pools are constructed independently for each dataset from the selected
benchmark contexts using field-restricted, Gold-free projections. Their accepted
sizes are 19,352 HotpotQA, 11,746 2WikiMultiHopQA and 23,618 MuSiQue documents.
They are bounded benchmark-derived pools, not full Wikipedia or a production
corpus. Questions and retrieved evidence may therefore share benchmark-specific
structure with their answers even though answers, supporting-fact labels and
decompositions were not used to build the pools.

## Development, supervision and outcome firewall

The five supervised heads use 4,500 previously opened development questions,
split by a frozen within-dataset hash order into 3,600 fit and 900 disjoint
calibration questions. The accepted 6,000-question cohort is disjoint by recorded
dataset/ID from that development set and from the wider exclusion union. The
seven historical upstream estimators and V2 have different earlier training
histories; only the five current heads are supervision matched.

For the evaluation cohort, candidate acquisition, label-free scoring,
eligibility and complete action memberships were sealed before the separate
outcome mapper read the selected reference sets. The later analysis used only
numeric `a0/a1` EM and F1 outcomes and could not change actions. This is strong
evidence for the documented pre-outcome order. It does not prove that no unknown
process outside the authenticated execution graph ever accessed outcomes.

## Historical upstream provenance

The seven learned upstream inputs are bound to authenticated saved estimator
bytes and to the historical `mars_full/models` source. Preserved ledgers and
source reconstruct 601 fit traces / 518 question groups within a 7,200-trace /
4,800-question development universe. Those 4,800 groups are in the exclusion
union and have zero recorded ID overlap with the current five-head development
questions. V2 used 3,000 earlier questions, also with zero recorded overlap.

The following evidence is missing and must remain explicit:

- one original fit-time ID receipt and one original fit-time matrix receipt for
  each of the seven historical estimators;
- an independent witness of the original historical fit execution;
- an independently recovered earlier pin for the complete old `mars_full`
  manifest; and
- evidence ruling out unknown unlogged activity or pretraining overlap.

Saved-parameter replay and independent arithmetic reproduce the preserved
predictions/actions at zero reported numerical error within the accepted scope.
That result authenticates the saved computation; it is not an original-training
replay and cannot fill the missing fit-time receipts.

## Pretrained model and contamination boundary

The reader, dense encoder and verifier are exact pinned revisions:

- `Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`;
- `BAAI/bge-base-en-v1.5@a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`;
- DeBERTa verifier revision
  `5a4338ab2151dc8db04ad53b42b6153382bf4f99`.

The project did not perform pretraining-corpus decontamination for these models.
Model cards, different developer lineages and benchmark ID exclusion cannot
establish absence of benchmark content from pretraining. No clean-room training,
training-corpus independence, or contamination-free Claim is allowed.

## Published-method adaptation boundary

GbV must be described as the **paired adaptation of Generate but Verify
Post-Answering NLI**. The published work motivates a question/answer hypothesis,
passage premises, overlapping chunks and maximum entailment score. The local
project computes branch-specific `F0(a0,E0)` and `F1(a1,E1)` and uses
`gbv_margin=F1-F0` under its own fixed action policy. This paired margin, the
exact pinned revision/runtime, the common eligibility mask and global `K=900`
are project choices. They are not an author-supplied paired-policy formula,
author-code reproduction or published threshold protocol.

EM and token F1 assess answer correctness. Recovery and Damage are normalized-EM
transitions. None directly validates faithfulness, factual grounding or citation
quality. The manuscript must not rename an EM/Damage result as a faithfulness
improvement.

## Terminal extension records

Phi is retained as authentic runtime/failure evidence only. Its V4 acquisition
completed 13,500 traces and fixed replay matched 180 traces, but the frozen
semantic validator failed because 6,573 of 9,120 stored dense query vectors were
outside the predeclared `1e-3` unit-norm tolerance; the maximum deviation was
`0.0041683525287623535`. A post-outcome-compatible `5e-3` tolerance cannot replace
the frozen threshold. No successful semantic acceptance exists, so Phi provides
no scientific effect, robustness or replication result.

Mistral was stopped before engineering or model execution. Its draft protocol
did not close value, runtime, resource, witness and numerical-tolerance gates.
It supplies no trace, score, outcome or replication evidence. Neither Phi nor
Mistral can be counted as an additional reader in the paper.

All preserved failed attempts remain part of the audit chronology. A technical
failure is not evidence for or against the scientific effect, and a successful
runtime receipt does not override a failed frozen semantic gate.

## Mandatory disclosure checklist

The main paper or supplement must state:

1. exact reader/encoder/verifier identities and the single accepted reader;
2. benchmark-derived bounded pools and deterministic cohort selection;
3. recorded-ID exclusion scope and absence of semantic/pretraining
   decontamination;
4. supervision matching only among the five current heads;
5. all seven missing historical fit-time ID/matrix receipts, missing independent
   original-fit witness and missing earlier whole-manifest pin;
6. saved-parameter replay scope versus original-training replay;
7. GbV's project-specific paired adaptation and correctness-only outcomes;
8. pre-outcome action sealing and its authenticated-graph scope;
9. Phi's terminal semantic failure and exclusion from scientific results; and
10. Mistral's pre-engineering stop and absence of effect data.

These disclosures may be shortened for page limits only if the supplement and
release map retain the full wording and the main paper points to them. None may
be converted to a positive generalization, robustness, contamination-free or
faithfulness Claim.

Primary authorities: `../cas_q2/P0_1_CLIENT_ACCEPTANCE.md`,
`../cas_q2/EMPIRICAL_AB_ACCEPTANCE.md`,
`../cas_q2/EMPIRICAL_C1_ACCEPTANCE.md`,
`../cas_q2/GBV_SOURCE_FIDELITY_REVIEW.md`,
`../cas_q2/EMPIRICAL_OUTCOME_ACCEPTANCE.md`,
`../cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md`, and
`../cas_q2/MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md`.

**CAS Q3 STATUS: NOT READY.** P0-E is closed. P0-F through P0-I remain.
