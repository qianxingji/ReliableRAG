# Phi/BGE joint preflight independent-validation contract

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

Before the joint-memory result can be used for a development-runtime admission
decision, a single-use validator must authenticate both sealed producer
namespaces without importing either producer. It must bind the V1 failure and
the prospectively corrected V2 source commits and manifests, verify exact
namespace coverage, and recheck every non-weight producer input. Model-weight
records must match the previously accepted Phi availability audit and BGE
pretrained-asset lock; the validator must not read model-weight bytes.

The validator independently reconstructs the invented short repair prompt and
the 16,000-character long answer prompt with the pinned local Phi tokenizer. It
must reproduce the complete prompt token IDs, masks, prompt hashes, generated
token decoding and parsers. The two V2 generation captures must also be exactly
equal to the corresponding observations in the already independently accepted
Phi-only preflight. Admissions, revisions, forward/load counts, BGE vector
shape and finite norm, and all zero benchmark/Gold/existing-answer/fit counters
must be checked.

The validator may read the two joint-preflight namespaces, the accepted
Phi-only witness namespace, committed source and controls, non-weight snapshot
files, and the active Python environment. Network/process access, model-weight
reads, benchmark/raw-data reads and writes outside the new validation namespace
are forbidden. It performs no model load, model forward, generation or fit.

A pass authenticates the saved source and witnesses only. The anomalous peak-
reserved counter remains a separate Astra xhigh capacity decision, and no test
benchmark is authorized by this validation.
