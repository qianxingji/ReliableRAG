# Official neural wheels: resolution correction and acquisition

Research Lead decision, 2026-09-11, before the corrected resolution/acquisition.
CAS Q2 STATUS: NOT READY.

The metadata-only v1 report resolved 34 exact distributions and preserved one
Torch assertion failure, manifest
`0fe71dfab921bad5946e6694570db21c3d99209c69f423d31076c23aaacafff2`.
Its retained official index response from
`https://download.pytorch.org/whl/cu128/torch/` has SHA-256
`f4d53b238bf7390cc0f9dacbca3d20b4e01e0ab2ba66874b3b410c3774e0d854`.
The exact compatible wheel is present: the parser rejected its official
`download-r2.pytorch.org` subdomain rather than finding an absent release.

Authenticate the original report and raw index, then resolve only this remaining
entry in a new v2 namespace. Do not request or replace the 34 successful PyPI
responses. Accept the exact indexed HTTPS URL
`https://download-r2.pytorch.org/whl/cu128/torch-2.7.1%2Bcu128-cp310-cp310-win_amd64.whl`
with the unchanged index digest
`5174f02de8ca14df87c8e333c4c39cf3ce93a323c9d470d690301d110a053b3c`.
Verify exact version and target wheel tags. Keep the first failure and script;
the correction does not retroactively change that run's result.

After all 35 exact selections are sealed, acquire their binary wheels into a
new private output namespace. Use only those URLs and digests; allow payload
hosts `files.pythonhosted.org`, `download.pytorch.org` and
`download-r2.pytorch.org`, always HTTPS. Authenticate published size where
available and SHA-256 for every complete payload before reading ZIP metadata.
No substituted versions, source builds or changed expected hashes. Preserve
failed/partial downloads under distinct names; retries, if needed, retain prior
attempts and use the same published digest. Existing authenticated CPU wheels
may be copied only if filename, size and selected digest agree exactly.

Read only package METADATA, WHEEL and license/notice files from authenticated
archives; verify names, versions and compatible tags without executing package
code. Save role-specific hash locks for the 33-package environment and separate
SentencePiece/PyArrow targets, plus a combined availability inventory. Hash the
acquisition script, this decision and predecessor manifests before downloading;
seal all result files and recheck inputs at completion. This is binary acquisition
only: no installation, repair of the running environment, model loads, GPU work,
scientific fit or fresh Gold/answer access. The previously inventoried RECORD
discrepancy, absolute-path constraints and historical provenance limits remain.
