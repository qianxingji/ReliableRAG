# HGB diagnostic state-observer refinement

Research Lead decision, 2026-09-11. Before implementing diagnostic v2.
The original seven-fit byte gate remains failed and unchanged.

Diagnostic v1 stopped on original SymmetricSelector before completing state
observation. This Python 3.10 dataclass uses slots and exposes neither the
dictionary nor __getstate__ assumed by the observer. Preserve the entire failed
diagnostic; no model, score or training change follows from this tool failure.

For v2, observe object serialization through its standard __reduce_ex__(4)
description. Record the complete returned tuple/string, constructor identity,
all constructor arguments, state and optional list/dict iteration members.
Record globally referenced types/functions by module and qualified name without
calling them. Explicitly support bytes as hexadecimal. Existing complete NumPy
array/dtype/scalar and dictionary/sequence handling remains unchanged, including
separate raw-buffer hashes and named structured fields. Standard reduction
also covers slots and native loss objects without inventing empty state.

This is an observation of the existing object's pickle description, not execution
of its constructor or a replacement model dump. Preserve complete differences
and fail on unsupported state, recursion or undeclared side effects. Do not
mutate either object, fit, predict, score, open labels or relax exact comparison.
The original v1 observer, output and failure remain frozen; use a new namespace
and new implementation file. Reuse the unchanged no-fit/no-score guard and
accepted package environment. All prior byte pins and preservation checks apply.
CAS Q2 STATUS: NOT READY. Scientific fit total stays 185.
