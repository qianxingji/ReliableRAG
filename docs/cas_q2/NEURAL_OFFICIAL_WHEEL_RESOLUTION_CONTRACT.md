# Exact neural-environment wheel availability

Research Lead decision, 2026-09-11, before querying the package indexes.
CAS Q2 STATUS: NOT READY.

Resolve official wheel availability for every distribution in the completed
current-runtime inventory: 33 original-environment distributions plus the
separate SentencePiece and PyArrow targets. This includes installed utilities;
do not present the list as a proven minimal scientific dependency set. The
inventory's preserved NumPy RECORD discrepancy is not waived by this stage.

Query exact name/version metadata from official PyPI. For the installed
`torch==2.7.1+cu128`, use the official PyTorch CUDA 12.8 wheel index. Retain the
raw index responses, selected filenames, official SHA-256 fragments/digests,
sizes where published, compatibility tags, timestamps and all HTTP failures.
Use the existing trusted HTTPS proxy; no credentials or private scientific
content is sent. Do not follow payload links outside the official package hosts.

Choose only wheels compatible with this Windows amd64 CPython 3.10 target,
ranked by the interpreter's packaging tags. Exclude yanked releases, source
distributions and a release whose Requires-Python excludes this interpreter.
Select exact versions only. Missing versions, missing compatible wheels or
unavailable published hashes are explicit reconstruction gaps: no version
substitution, source build or environment repair is authorized by this contract.

This first stage downloads metadata only. It does not install packages,
deserialize wheel code, use the GPU or read fresh answers/Gold. Freeze the
inventory input, resolver script and this contract before requests; use a new
exclusive output namespace and retain all partial/failure results. A completed
resolution report means official availability was checked at the recorded time,
not that binaries have been acquired, historical wheel identity has been proven
or a clean neural environment has passed. Subsequent acquisition/installation
must bind these selections and preserve unresolved discrepancies explicitly.

The running C3 environment, frozen path bindings and pipeline sources stay
unchanged. No new scientific fit or neural execution is part of this work.
