# DAA-V2 prospective source amendment — HotpotQA full distractor validation

Status: **prospective amendment before fresh-ID selection, retrieval, generation, scoring, or Gold access**.

## Trigger

The identifier-only availability audit dated 2026-09-09 failed solely because the accepted local HotpotQA materialization contains 4,000 distractor-validation IDs, of which 3,800 intersect the frozen forbidden union, leaving 200 available IDs. The same audit found 8,776 available 2WikiMultiHopQA IDs and 19,338 available MuSiQue-train IDs. Historical private-artifact verification passed, the forbidden-ID union passed, and the audit selected zero questions with zero retrieval, generation, model, and fresh-label accesses.

This is therefore a **local source-materialization shortfall**, not evidence that the complete HotpotQA distractor-validation split lacks enough unused IDs.

## Amendment

The prospective HotpotQA source remains the **distractor validation split**. The scientific split is not changed to HotpotQA train, fullwiki, or another benchmark.

The only allowed change is to expand the accepted local 4,000-row materialization to the complete distractor-validation source, expected to contain 7,405 unique question IDs.

This amendment does not change:

- DAA-V2 architecture or feature set;
- HGB backbone or historical model binaries;
- lambda, alpha, grouped folds, or model seed;
- 5% primary action rate;
- GbV implementation, model revision, or comparator hierarchy;
- forbidden-ID categories or the frozen union rule;
- target of 1,500 fresh evaluation questions per dataset;
- question-cluster statistical unit;
- bootstrap seed or analysis code;
- success criteria;
- the rule that no fresh Gold/correctness/outcome is accessed before action sealing.

## Feasibility bound

The current HotpotQA forbidden union contains 5,600 unique IDs. If the complete distractor-validation source contains 7,405 unique IDs, then even the maximal possible overlap with that union leaves at least

`7405 - 5600 = 1805`

source IDs outside the forbidden union. Therefore the 1,500-question target is mathematically feasible **if and only if** the complete 7,405-ID distractor-validation source can be established under the provenance checks below. The actual overlap must still be recomputed; the 1,805 value is only a lower-bound argument, not a selected cohort count.

## Source provenance preference order

Use the following order and stop at the first valid complete source.

1. An already-present local copy/cache of the complete official `hotpot_dev_distractor_v1.json` whose SHA-256 matches the historically recorded official-download checksum, if available.
2. An already-present local Hugging Face cache/materialization of `hotpotqa/hotpot_qa`, configuration `distractor`, split `validation`, provided it contains exactly 7,405 unique IDs and passes the overlap-consistency checks below.
3. A newly acquired pinned Hugging Face `hotpotqa/hotpot_qa` distractor-validation materialization, only if local acquisition is authorized and the exact dataset revision/source metadata are recorded before projecting IDs.

Do not substitute HotpotQA train, fullwiki, BEIR HotpotQA, another mirror, synthetic HotpotQA, or a reduced target merely to make the audit pass.

## Required equivalence checks for a full-source materialization

Before it may replace the 4,000-row audit source inventory:

- exactly 7,405 unique HotpotQA distractor-validation IDs must be present;
- duplicate IDs must be zero;
- all 4,000 IDs in the previously accepted local materialization must be contained in the full ID set;
- for those shared 4,000 IDs, the label-free runtime projection (`id`, question, ordered context titles/sentences) must match the accepted local materialization under canonical serialization/hashing;
- no answer, supporting-fact, correctness, or other Gold/evaluation value may be copied into the audit namespace;
- source transport/revision/hash evidence must be saved;
- the old 4,000-row source and previous failed audit must remain byte-unchanged.

If the 4,000-row shared runtime projection does not match, stop and report source-equivalence failure rather than silently proceeding.

## Audit rerun

After a valid complete HotpotQA source is established:

1. regenerate only the HotpotQA identifier-only source ledger;
2. reuse the frozen 2WikiMultiHopQA and MuSiQue source-ledger hashes unless an integrity check shows they changed;
3. reuse the exact forbidden-union SHA-256 unless the provenance correction requires a semantically identical regenerated union; any changed union requires explicit explanation and independent recount;
4. rerun the availability selector with `--per-dataset 0`;
5. run the schema-complete `finalize_v2_availability_audit.py`;
6. independently validate the final audit record;
7. stop.

PASS requires at least 1,500 available IDs for all three datasets and the same zero-call/zero-selection/zero-Gold conditions as the original audit.

## Reporting boundary

A PASS after this amendment authorizes only responsible-author review of availability. It does not authorize fresh-ID selection, candidate-pool construction, retrieval, generation, V2/HGB/GbV scoring, action sealing, Gold mapping, or evaluation.
