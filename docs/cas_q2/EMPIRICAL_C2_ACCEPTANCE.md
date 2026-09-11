# Client Research Lead acceptance: all original-query retrieval

CAS Q2 STATUS: NOT READY. Accept only original retrieval for the fixed 6,000
questions / 18,000 traces under EMPIRICAL_C2_RETRIEVAL_CONTRACT.md.

The canonical run at commit 3345456348d6841c8e837fc8b4a83ee0c786b75b completed
in 1,096.5623014 seconds including its recorded setup/check boundaries. It made
18,000 logical original retrieval calls, 54,716 document-embedding rows,
3,422 document forward batches and 12,000 separate single-query forwards:
15,422 canonical BGE forwards total. The earlier two invented GPU preflight
forwards are separate overhead. No reader, repair, scoring, action or Gold
evaluation was run. Scientific fitting remains 178 takeover fits.

Independent validation passed 18,173 explicit checks covering all 18,000 traces,
12,000 recomputed BM25/dense score vectors and 6,000 RRF fusions. Every saved
numeric ranking and top5 binding matched exactly. All 6,000 dense/hybrid paired
query vectors were exactly equal. Original ASTs, saved inputs and source bytes
were unchanged; canonical Python execution guard denials were zero.

Accepted manifest SHA-256:
81b9c7163adf669a828bd2ef772e14fecbda727cf596bced45856a1e699a354d.

This is complete saved-array retrieval arithmetic validation, not a second full
encoder replay or answer-quality evidence. The 47-test repository suite passed
45 tests with the same two Windows filesystem-capability skips. Separately,
22 authenticated original reader/repair CPU fixtures passed with no pretrained
model load/forward; their original cross-line parser behavior remains unchanged.

Proceed with C3 trace/replay preparation and its joint-model compatibility
preflight after source/input freezes. The 18,000-trace reader generation pass
still needs its own client acceptance of complete executable bindings and GPU
preflight. Label mapping remains closed until all later frozen scores/actions
pass independent prelabel acceptance.

P0: actual candidate-pair generation, score/action seals and fresh outcome
analysis; evidenced contribution; disclosed historical training-receipt gaps;
and official CAS journal/institution qualification (user scope still undecided).
P1: comparison fidelity, real whole-pipeline costs, contamination boundaries and
reproducible release. P2 adds no model/feature/seed/budget search. Both failed
method-advancement criteria remain unchanged; no novel candidate is cleared.
