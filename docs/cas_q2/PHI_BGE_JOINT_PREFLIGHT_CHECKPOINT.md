# Phi/BGE joint preflight execution checkpoint

2026-09-12. **CAS Q2 STATUS: NOT READY.**

The V1 producer is preserved under manifest
`692c75ac0a625bc3c5aec37562b0be5e73832d7b315df399b044a1b9600464c1`.
It loaded both models and completed two invented Phi generations and one BGE
forward, then failed because its question text differed from the frozen
9,472-token witness while the assertion expected that exact length. It read no
benchmark, Gold or existing answer and performed no fit.

The prospectively corrected V2 producer passed under source commit
`4f9eb32b73d73675e2dec3eedabd3d7728d8ee6a`; manifest SHA-256 is
`ecf17a8af6c21fe2887700993bafe53c4aa8ae3c5419112737049db5c91ef2bf`.
With Phi and BGE resident it completed exactly two logical Phi generations, 49
Phi internal forwards and one BGE forward. The guard admitted the 353-token
repair-query prompt and exact 9,472-token long answer prompt. Model loads were
two; benchmark rows, Gold reads, existing-answer reads and fits were zero.

Peak allocated CUDA memory was 16,213,824,000 bytes against a reported
17,102,864,384-byte device total, or about 94.80%, leaving about 848 MiB by this
accounting. Peak reserved was reported as 19,203,620,864 bytes, above nominal
device total. That counter cannot be treated as physical headroom without an
independent allocator/driver interpretation. Because this is an anomalous
resource-accounting result, final capacity acceptance is pending Astra xhigh
review after an independent saved-witness/source audit. Development benchmark
execution remains unauthorized.
