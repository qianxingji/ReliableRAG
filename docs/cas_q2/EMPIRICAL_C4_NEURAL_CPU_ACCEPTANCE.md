# Client Lead acceptance: independent neural-witness CPU engineering

CAS Q2 STATUS: NOT READY. Effective 2026-09-11.

The prospective validation contract was committed at 1158b84 before its
implementation and before any C4 scoring GPU preflight or fresh neural scores.
Accept the CPU engineering regression at source commit
b754f657b5f70448b5837364cdb0bd233f7b3f01 for the stated synthetic scope only.
Namespace: empirical_neural_engineering_tests_v1. Immutable manifest:
cc322f1456cfe6c3c3190c98c5b03f305c2d4846cd6062bb68417bae47efcfbf.
The full raw test logs and executable/input freeze are retained; all 226 bound
input files remained unchanged. This is an engineering test run, not a new
process-wide scientific input boundary or real-model neural execution acceptance.

The full repository suite ran 101 distinct discovered tests: 99 passed and the
two existing Windows filesystem-capability cases were skipped. Ten new tests
exercise independent witness validators against the unchanged native scoring
functions with explicit CPU fake logits. They check:

- Likelihood rendering, character/token truncation, prefix alignment, all four
  cells, token positions, exact reductions and initially empty cache chronology;
  imported cache hits, missing/altered observations and invalid timings fail.
- NLI hypothesis, complete original chunk boundaries and word coverage, token
  batches, positive class resolution, saved FP32 softmax, exact branch maxima
  and pair margin; corruptions of each binding fail.
- Both documented deterministic NLI preparation failures are independently
  reproduced; completed first-branch work is retained when the second fails.
- Native document-mode answer embeddings include empty/equal answers and a
  partial final batch; saved-vector order, tokens and dot products are checked
  independently without another encoder forward.

Three additional CPU tests cover fixed model configurations and exclusive new
NLI cache staging. Scientific configuration values must exactly match the
historical records; only IO paths are adapted. Snapshot copying preserves the
original model ID/revision and bytes in a new HF_HOME. Tests use explicitly
invented file bytes, reject missing/changed/foreign/duplicate inputs before
copying, and refuse reuse of the destination. The real pinned model constructors
are implemented but have not been executed by these tests; slow-tokenizer
package setup, protected executors and actual GPU compatibility remain pending.

No neural forward replay claim is made. Likelihood witnesses contain target-token
log probabilities, not full-vocabulary logits. Semantic validation recomputes
saved-vector dot products, not BGE's internal CLS normalization. NLI validation
uses shared authenticated tokenizers and saved logits, not an independent model
forward. HGB downstream validation still shares saved sklearn probabilities.

The new NLI GPU/CPU softmax gate was fixed prospectively at absolute 8*float32
epsilon (9.5367431640625e-7), with probability-sum bound 2*epsilon. It applies only
to independently recomputed probabilities from saved FP32 logits. The existing
1e-10 head replay threshold remains unchanged. Actual saved probabilities,
maxima, margins, masks and actions are never replaced by approximate values and
still require their stated exact checks. Exceedances must fail and be preserved;
the bound cannot be increased after inspecting a GPU result.

C3 continues in its original process and namespace. P0 remains completing that
canonical pass, fixed 180-trace replay and full independent acceptance, then
protected C4 executors, pinned-model GPU preflights and complete file-level
independent validation before any prelabel seal or Gold mapping. This stage did
not score fresh answers, load real neural models or add scientific fits; the
takeover fit total remains 178. It provides no fresh quality evidence.

Principal rejection risks remain the unestablished contribution, incomplete
fresh empirical results and historical per-estimator fit-time receipt gaps.
P1 covers baseline fidelity, complete cost accounting, contamination boundaries
and release reproducibility. P2 introduces no model/feature/seed/budget search.
CAS partition year, institutional category rule and target journal remain
undecided by the user. Both historical advancement failures remain unchanged.
