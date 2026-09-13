# Authenticated original ROA source

These five Python files are byte-for-byte copies of the sealed original namespace
`outputs/daa_v3_development/recovery_only_isolation_v1`, authenticated by
`docs/cas_q2/ROA_MANIFEST_SPEC.json`. They are preserved without algorithm edits.
The original scripts use sibling imports and fixed artifact paths. Load them only
through `scripts.replay_roa_original`, which binds paths in memory, redirects the
report writer, denies writes outside a new output directory, and prohibits fits.

`learning.fit_bundle` is retained for source review; replay never invokes it.
`independent.py` is the original separate numerical reconstruction, not a new
implementation described as the historical one. It does not import design,
learning, metrics, or the experiment executor. Its `scientific_fit_calls=112`
field describes historical calls; the wrapper separately reports zero new calls.
