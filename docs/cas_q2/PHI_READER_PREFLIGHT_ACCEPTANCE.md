# Phi reader compatibility preflight: client acceptance

Date: 2026-09-12. Client Research Lead review: Sol High.

CAS Q2 STATUS: **NOT READY**.

Decision: **ACCEPTED_PHI_READER_PREFLIGHT_WITH_MEMORY_LIMIT**. The single
invented-only GPU producer, the separate tokenizer-only validator and the
external client audit all pass. This establishes that the authenticated Phi
reader adapter and answer-likelihood scorer execute deterministically at the
frozen interfaces. It supplies no benchmark outcome, model-fit, fairness,
reader-robustness, contribution or deployment evidence.

The unique producer used source commit
`b9680dba8845d7ad077acd884ff8b5166536b009` and the pinned
`microsoft/Phi-3.5-mini-instruct@2fe192450127e6a83f7441aef6e3ca586c338b77`
snapshot. Its sealed namespace is
`outputs/cas_q2/phi_reader_gpu_preflight_v1`, with manifest SHA-256
`cfebd83ce688479af922e884ea0df6034af6e32fc2175c3fd3b5e69266e58d30`.
It completed two sequential model loads, four logical greedy generations, 55
internal generation forwards, two likelihood forwards and one exact likelihood
cache hit. Repeated short generation was byte-identical. The 9,472-token long
generation input exercised context truncation; the 8,192-token long likelihood
input exercised the frozen scoring truncation. No benchmark row, Gold value or
scientific fit was read or produced.

The first independent validator is preserved at
`outputs/cas_q2/phi_reader_gpu_preflight_validation_v1`. It failed before
tokenizer load because importing `transformers` after the IO hook caused a
Windows `NUL` platform probe to be rejected. It contains zero model loads,
forwards, benchmark rows, fits and Gold reads; its manifest is
`35cf75ee5a8d0ef1efb00b9d560fa8e455a1873d20d202cad93f1752acf15269`.
The prospective V2 import-order correction is documented separately and did
not rerun the GPU producer.

The V2 tokenizer-only validator used source commit
`fe50810e5b7b85d32245a846d5045f757cf3d249` and passed 111 independent
checks. It reconstructed prompts, token IDs, generation parsing, answer-query
parsing, chosen-logit minus log-normalizer reductions and the exact cache
identity without loading model weights. Its namespace manifest is
`ef11925bb631e47c22fd47ba0579edf138e708b4a1ee78bbe4527cb1f7fe291a`.
There were no weight-read or outside-output-write denials.

The external client audit rehashed every producer, failed-validator and V2
validator file plus all bound source and model inputs. Its accepted task
namespace is `outputs/phi_reader_preflight_client_audit_v1`; manifest SHA-256 is
`dc5d0a25bcac891552ac2ab4cc333c4a7e39e25f1faa655d0575550f4358afba`
and audit SHA-256 is
`37b50e125fb8709342a5352768696f73f0019798d3a7ba5ae8752128092d4a62`.
The audit performed no model forward, fit, benchmark-row read or Gold read.

## Binding memory limit and next gate

The long invented generation reached 15,987,338,240 allocated CUDA bytes. The
reported 16,311 MiB device total is 17,103,323,136 bytes, leaving only
1,115,984,896 nominal unallocated bytes; the observed allocation is
93.4750405689% of nominal capacity. This is an interface witness, not a batch
capacity guarantee, and allocated bytes omit reserved allocator state and other
GPU processes.

No Phi benchmark call is authorized by this acceptance. Before any development
or test generation, commit and independently accept a value-blind input freeze
that tokenizes every planned prompt, proves no input exceeds the accepted
9,472-token generation witness, freezes batching/concurrency to one and binds
the exact 6,000-question cohort, 18,000 retrieval assets, prompts, split roles,
source/model hashes and output namespaces. Gold and existing answer strings must
remain closed during this gate. Any overlength input or memory-contract mismatch
stops the stage and is preserved; it does not authorize prompt shortening after
outcome inspection.

P0 is that input/implementation freeze, followed by the single frozen Phi
development and test study and independent fairness/claim audits. P1 remains
complete Phi cost/runtime packaging, another-host reproduction and the seven
missing historical fit-time receipts. P2 remains manuscript construction and
target-journal qualification after the empirical claim boundary is known. The
principal rejection risk is still that the fusion is an ordinary supervised
combination with no established method novelty; reader dependence and the tight
GPU margin may further narrow the evidence.
