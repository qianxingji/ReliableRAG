# Phi input-freeze V2 environment-read amendment

2026-09-12. **CAS Q2 STATUS: NOT READY.**

The unique V1 tokenizer-only producer stopped before tokenizer construction or
prompt tokenization. `AutoTokenizer.from_pretrained` entered Transformers'
lazy model registry and attempted to read
`transformers/models/arcee/__pycache__/__init__.cpython-310.pyc`. The V1
allowlist covered the pinned snapshot and scientific inputs but excluded the
already imported Python environment. The boundary rejected that read. V1 is
preserved at `outputs/cas_q2/phi_reader_input_freeze_v1`, manifest SHA-256
`c244000cb83b33d08f8a37419ee5c7aa6617f80311610d69706b3975e75dd2a9`.
It performed zero prompt tokenizations, model loads, forwards, generations,
scientific fits, existing-answer reads and Gold reads.

V2 changes only the read boundary and output namespace. Read-only files beneath
the exact active virtual-environment and base-Python roots may be opened during
tokenizer construction and use. Every actually opened environment file is
recorded and hashed in the final executable freeze. Weight-like files with
`.safetensors`, `.bin`, `.pt`, `.pth` or `.ckpt` suffix remain forbidden
regardless of location. Scientific data remain limited to the same explicit
label-free allowlist; output writes remain limited to the new V2 namespace;
network and subprocess events remain forbidden after boundary installation.

All cohorts, roles, templates, hashes, renderer, 9,472-token ceiling, batch and
concurrency limits, expected 63,000 tokenizations and acceptance rules in
`PHI_READER_INPUT_FREEZE_CONTRACT.md` remain unchanged. V2 does not reuse or
alter any V1 file.
