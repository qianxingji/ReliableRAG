# Phi reader full-input freeze: client acceptance

Date: 2026-09-12. Client Research Lead review: Sol High.

CAS Q2 STATUS: **NOT READY**.

Decision: **ACCEPTED_VALUE_BLIND_PHI_INPUT_FREEZE**. The V2 tokenizer-only
producer, non-importing independent reconstruction and external client audit all
pass. This accepts the fixed development/test membership, deterministic `a0`
and repair-query prompt lengths, and the mandatory dynamic `a1` admission
boundary. It authorizes development-runtime implementation and validation only;
it does not authorize test benchmark execution, test Gold, result analysis,
fairness claims or manuscript drafting.

The unique V1 producer is preserved at
`outputs/cas_q2/phi_reader_input_freeze_v1`, manifest SHA-256
`c244000cb83b33d08f8a37419ee5c7aa6617f80311610d69706b3975e75dd2a9`.
It stopped before tokenizer construction because Transformers' lazy registry
read an installed Python bytecode file outside the overly narrow allowlist. Its
receipt records zero prompt tokenizations, model loads, forwards, generations,
fits, existing-answer reads and Gold reads.

The prospective V2 boundary admits read-only access beneath the exact active
virtual-environment and base-Python roots, records every file actually opened,
and continues to forbid all weight-like files, network/process events and
non-allowlisted scientific data. The unique V2 producer used source commit
`baf84189d0cc101fee14e0af660570be29187da8`. Its manifest SHA-256 is
`17cb0c29e4d4a5b98991bbebf1368bdff0ebece6221ca163c73327bcf4bcedd9`.

V2 tokenized the unchanged answer and repair-query prompts for all 31,500 fixed
original-evidence traces: 13,500 development traces over 4,500 questions and
18,000 test traces over 6,000 questions. The resulting 63,000 prompt
tokenizations contain 10,800 fit-role, 2,700 calibration-role and 18,000
test-role trace rows. No rendered context reached the 16,000-character budget.
The maximum was 3,682 tokens for a development 2Wiki dense repair-query prompt,
leaving 5,790 tokens below the accepted 9,472-token compatibility ceiling.

The separate validator used source commit
`553eb6f1047c6af2acb248407397ddd82986e5c9` and did not import the producer.
It reconstructed all 63,000 prompts and all 31,500 scalar-ledger rows, reproduced
every aggregate and maximum, rechecked the 9,472/9,473 admission boundary for
`a0`, `repair_query` and `a1`, and observed no boundary denial. Its manifest is
`3d0488e18ff5433abc721230763aa82d57452a13a66322040904392a1ff0ccd0`.

The external client audit reparsed every private scalar row, recomputed roles,
strata, maxima and truncation counts, rehashed all producer inputs plus 114
actually read environment files, and verified the absence of answer/outcome/
Gold/weight paths. Its task namespace is
`outputs/phi_reader_input_freeze_client_audit_v1`; manifest SHA-256 is
`74f3c9026d340d4582a78348d9448a618742c8bf59128558234601bbc9b4e312`
and audit SHA-256 is
`d97aaa3b9bf0c69318ff3e04693b13f380a3096bd2727f60264697ca3042796c`.

The repaired-answer prompt remains dynamic because it depends on Phi's newly
generated repair query. The committed runtime guard must tokenize each `a1`
prompt before CUDA transfer/model access and reject more than 9,472 tokens,
non-unit batch size, a malformed mask or an unknown stage. A failure must remain
sealed; it cannot justify changing prompts or evidence.

P0 is now the single-use Phi development generator/retriever/scorer
implementation, its bounded replay and independent validation, followed by the
five reader-matched heads. Test execution remains gated on those accepted
development artifacts. P1 remains complete cost/runtime packaging, another-host
reproduction and the seven missing historical fit-time receipts. P2 remains
the manuscript and target-journal qualification after the reader result fixes
the claim boundary. Main rejection risks remain ordinary fusion without method
novelty, possible reader dependence and missing end-to-end Phi evidence.
