# Phi preflight validator V2 import-boundary amendment

2026-09-12. **CAS Q2 STATUS: NOT READY.**

The first independent validator stopped before loading the tokenizer. Its audit
hook was installed before importing `transformers`; that import lazily imports
PyTorch, whose Windows platform probe opens the `NUL` device through a subprocess.
The hook rejected that operating-system capability as an output-directory write.
The preserved namespace is
`outputs/cas_q2/phi_reader_gpu_preflight_validation_v1`. It contains no model
load, model forward, benchmark row, fit or Gold read.

V2 changes only lifecycle order: import `AutoTokenizer` before installing the
tokenizer IO boundary. The call to `AutoTokenizer.from_pretrained`, every model
snapshot read, all reconstruction and all output writes remain inside the
boundary. Safetensors and `.bin` reads remain forbidden. V2 binds the unchanged
producer commit `b9680dba8845d7ad077acd884ff8b5166536b009` and does not rerun the
GPU producer. All schemas, hashes, arithmetic tolerances and acceptance rules in
`PHI_READER_PREFLIGHT_EXECUTION_CONTRACT.md` remain unchanged.

