# Phi/BGE joint-memory preflight: Astra xhigh acceptance

Date: 2026-09-12. Client Research Lead review: Astra xhigh.

**CAS Q2 STATUS: NOT READY.**

Decision: **ACCEPTED_FOR_SINGLE_PROCESS_PHI_DEVELOPMENT_RUNTIME_ONLY**. The
sealed V2 invented-only producer, independent saved-source/witness validator
and external client audit pass. This closes the joint Phi/BGE engineering-
capacity prerequisite for development-runtime execution. It does not authorize
the test benchmark, reader-specific scientific fits, test Gold, scientific
claims or manuscript drafting.

## Authenticated execution

The preserved V1 producer manifest is
`692c75ac0a625bc3c5aec37562b0be5e73832d7b315df399b044a1b9600464c1`.
It loaded both models and completed two logical Phi generations plus one BGE
forward, then failed because the invented question omitted the frozen word
`toy`. Its zero benchmark, Gold, existing-answer and fit counters remain
unchanged.

The prospectively corrected V2 used source commit
`4f9eb32b73d73675e2dec3eedabd3d7728d8ee6a` and manifest
`ecf17a8af6c21fe2887700993bafe53c4aa8ae3c5419112737049db5c91ef2bf`.
With the pinned Phi and BGE revisions resident in BF16/eval mode, it completed
exactly two logical Phi generations, 49 internal Phi forwards and one BGE
forward. The pre-CUDA guard admitted a 353-token repair-query prompt and the
exact 9,472-token long-answer witness. It loaded two models and read zero
benchmark rows, Gold values or existing answers, and performed zero scientific
fits.

The committed tokenizer-only validator used source commit
`4a8cb721d55c063d56d43aa1f868b32e4d5b17fb`. Its manifest is
`931391743a6ce4c64164973801eeffde0476545552c79d6b150458cd1b7d417d`.
It passed 89 checks without reading weight bytes or executing a model. It bound
both producer commits/manifests, rehashed all non-weight inputs, matched all
three weight records to previously accepted asset pins, independently rebuilt
both prompts/tokens/masks/renders/parsers, and established exact equality with
the corresponding already validated Phi-only captures.

The external client audit is sealed at client task namespace
`outputs/phi_bge_joint_preflight_client_audit_v1`. Its manifest SHA-256 is
`b82298a9f1a6df5c49305be12c5fff23fb2064ef1922fd78dd66d7dc51116163`
and audit SHA-256 is
`d08541acf0d92eca99839ac9cee156c05fe73ff36ee6e81c2ed5c758b627011d`.

## Capacity interpretation

The process used PyTorch 2.7.1+cu128's `native` caching allocator on an NVIDIA
GeForce RTX 5060 Ti under WDDM. Peak tensor-allocated CUDA memory was
16,213,824,000 bytes against a 17,102,864,384-byte nominal device total:
94.8018%, leaving 889,040,384 bytes (about 848 MiB) by that counter. Peak
reserved was 19,203,620,864 bytes, above nominal physical capacity.

PyTorch documents `max_memory_allocated` as the peak memory occupied by tensors
and `max_memory_reserved` as the total managed by its caching allocator; these
are different accounting domains. Microsoft documents that WDDM assigns stable
per-process GPU virtual addresses while the underlying resources can be over-
committed and relocated. The observed reserved value is therefore consistent
with allocator/virtual-memory accounting and is not evidence of simultaneous
physical residency or additional headroom. Sources checked 2026-09-12:

- https://docs.pytorch.org/docs/stable/generated/torch.cuda.max_memory_allocated.html
- https://docs.pytorch.org/docs/main/notes/cuda.html#memory-management
- https://learn.microsoft.com/en-us/windows-hardware/drivers/display/gpu-virtual-memory-in-wddm-2-0

The acceptance rests on the successful exact 9,472-token stress execution with
both models resident, not on the anomalous reserved counter. The value-blind
input freeze found a 3,682-token maximum across 63,000 deterministic original-
evidence prompts; repaired-answer prompts remain dynamic and must stay below the
same 9,472-token pre-CUDA ceiling.

## Binding runtime controls

Development execution must use one process, one Phi instance, one BGE instance,
BF16/eval/inference mode and batch size one. The committed exact tokenizer guard
must run before every CUDA generation and reject an unknown stage, malformed
mask, non-unit batch or more than 9,472 input tokens. The runtime must durably
flush per-stage receipts and resume only from an exact validated prefix.

Record allocator backend, WDDM/device identity, start free/total memory and
allocated/reserved peaks. A CUDA OOM, guard failure, boundary violation or
receipt-prefix conflict must be sealed as a failure and stop the run. Do not
change prompts, evidence, dtype, model revision, token limits or allocator
configuration in response. No concurrent GPU workload is permitted for the
authorized process.

P0 is now the development-only Phi generator/retriever/scorer implementation,
its single execution, bounded replay and independent validation. Test execution
and the ten reader-specific fits remain gated on development acceptance. P1 is
another-host reproduction plus the seven missing historical fit-time receipts.
P2 is manuscript and target-journal qualification after the reader result fixes
the claim boundary. The leading rejection risks remain ordinary fusion without
method novelty, possible reader dependence and incomplete end-to-end Phi
evidence.
