# Phi reader development runtime independent-validation contract

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

This contract defines the result-blind validator for the canonical 13,500-trace
Phi development runtime and its fixed 180-trace replay.  It authorizes validation
only.  It does not authorize a reader, BGE or NLI model load, a model forward,
development or test Gold access, fitting, scoring, outcome analysis, or a test
runtime.

The validator is a separate implementation.  It must not import the development
executor, `phi_reader_development_runtime_common.py`, or
`phi_reader_development_runtime_guard.py`.  Its only neural asset operation is
loading the pinned Phi tokenizer from the accepted local snapshot.  An audit
boundary denies model-weight reads, network access, subprocess creation after
startup, and writes outside the explicit new validation namespace.
Third-party tokenizer import probes use a private temporary directory inside
that namespace.
Namespace seals and source records are authenticated before the audit is
installed.  The `transformers.AutoTokenizer` module is then imported because
its transitive torch import performs a Windows platform subprocess probe.  The
boundary starts before `from_pretrained`, before any tokenizer snapshot access,
and before semantic decoding of trace, prompt, input-freeze and runtime-ledger
records; the freeze and report record this boundary point explicitly.

The launch names the sealed canonical and replay namespaces and their expected
manifest SHA-256 pins, an expected runtime source commit, and a new one-component
validation output name.  All three names
are containment checked.  The validator requires both runtime namespaces to be
complete, exactly sealed, immutable, from the same expected commit, and bound to
the same runtime configuration.  It rehashes every non-weight executable-freeze
input record.  Model-weight records are not opened: their path, size and digest
records must instead equal the already accepted joint-preflight records, which
preserves the zero-weight-byte-read boundary.

Both the runtime executable freeze and its success receipt must contain the
same exact audit-boundary string: `after authenticated source records, framework
imports/configuration, authenticated native assembly, and cached platform probe;
before CUDA device query, model loads, and runtime trace/dataset semantic reads`.  The independent
validator pins that text and rejects a missing, divergent or edited copy.
It also requires the successful receipt to report exactly one BGE model load,
one Phi reader model load and zero NLI model loads.

The validator independently checks the old 13,500-row development order and
the fixed 180-row, 20-per-cell replay selection against the accepted input
freeze.  It validates all four ledgers and every call-event intent/completion
pair, including operation inputs and the completed ledger-row digest.  It
reconstructs every evidence rendering and prompt.  The accepted input-freeze
witnesses bind `a0` and repair-query prompt hashes, token IDs, lengths and render
flags; tokenizer-only reconstruction additionally binds the dynamic `a1`
prompt, IDs and admission.  Generated token IDs are tokenizer-decoded and the
saved answer/query parsers are independently repeated.

The canonical ledgers and call-event journal are consumed as six synchronized
streams in trace order.  Their parsed rows are discarded after each trace.  A
single pass retains only the actual raw bytes for the fixed 180 replay traces;
the replay streams are then compared directly with those bytes.  The validator
does not recreate JSON bytes from parsed values for this identity claim.  At
most one dataset's retrieval assets are loaded at a time.

Repair validation restores the serialized BM25 index and dense document matrix
without constructors or encoders.  BM25 scores are recomputed from the saved
query text.  Dense scores are recomputed from the saved 768-value query vector.
Hybrid rank fusion is independently repeated at component depth 100, RRF k=60
and result depth 50.  The validator checks same-retriever routing, rank order,
scores, the first candidate outside E0, rank-5 replacement, pool document
identity/content, provenance hashes and canonical branch hashes.  It cannot
independently prove that a saved dense query vector is the output of the pinned
BGE for the saved query without violating the no-model-forward boundary; that
remaining claim is limited to the runtime call journal, frozen model identity,
vector shape/finiteness, and exact downstream ranking recomputation.

Replay rows must be byte-identical to the canonical rows selected by fixed trace
position in each of the four ledgers.  Receipts must truthfully report canonical
and replay row counts, guard admissions, reference decoding, zero Gold reads,
zero fit calls, and zero historical Qwen answer reads.  The validator reports
its own tokenizer loads separately and requires reader/BGE/NLI model loads and
all model forwards to remain zero.

The validation output is single use.  A pass writes an executable validation
freeze, an independent report and an exact SHA-256 manifest.  Any mismatch is a
hard failure; no runtime artifact is modified and no scientific call is retried.
