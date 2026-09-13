# Client Lead acceptance: original-retrieval GPU preflight

CAS Q2 STATUS: NOT READY. Accept only the original-retrieval execution scope in
EMPIRICAL_C2_RETRIEVAL_CONTRACT.md, before canonical benchmark retrieval starts.

At implementation commit c3260ad7bfeb571c1abe9856f9b0345e1b1946a1, the guarded
preflight loaded the pinned BGE BertModel once on RTX 5060 Ti / CUDA. Exactly two
invented-query forwards returned identical float32 embeddings. Actual model
parameters were BF16, deterministic algorithms enabled, CUDA/cuDNN TF32 disabled,
cuDNN deterministic enabled and benchmark disabled; attention backend was sdpa.
The revision was a5beb1e3e68b9ab74eb54cfd186867f64f240e1a. No benchmark forward,
fit, reader generation or Gold access occurred. Python audit denials: zero.

Accepted preflight manifest SHA-256:
3861f34c6add005baa1889d36679b740c90677d0fbbbc04ea85ab8b5cc6a2b3d.
The frozen input/source records must still match before canonical execution.
The combined engineering suite ran 41 tests: 39 passed, 2 Windows filesystem
capability skips. An earlier synthetic fixture incorrectly expected empty-query
retrieval; it was corrected before source freeze to assert the original rejection
behavior. No scientific execution was retried or altered for that fixture.

Proceed once into outputs/cas_q2/empirical_retrieval_v1 using this accepted
manifest hash. Preserve all output if any check fails. Only after the independent
complete arithmetic/trace audit passes may original retrieval be accepted.
This document grants no reader/repair/scoring/Gold execution outside their
subsequently completed native adapters and executable freezes.
