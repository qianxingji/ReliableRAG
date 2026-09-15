# Transport the accepted static graph without rewriting it

Research Lead execution specification, 2026-09-11. CAS Q2 STATUS: NOT READY.
This implements STATIC_DELIVERY_CLOSURE_CONTRACT.md after the graph audit passed.
It does not broaden the scientific decode boundary or authorize inference.

The accepted graph manifest is
`aa5c3da7ed764405e92602b64303984931a798abf2aee3e64c5d56ae34e892ea`:
17,617 nodes, 21,118 edges, 11,840,356,271 bytes, no reported issue and 36 exact
namespace checks. Its metadata remains byte-for-byte evidence, including original
absolute paths. Do not rewrite those paths to make a scientific loader pass.

Create one new, private ZIP64 archive using stored members to limit CPU contention
with the original running C3 process. Include all 17,595 remaining graph files
(4,345,359,738 bytes), under `roots/{original,engineering,task}/...`. Include the
complete sealed graph audit and the exact audit controller, seeds, two contracts,
asset lock, writer and independent validator. Freeze all these input/control
digests and the destination before writing the archive. The freeze and resulting
archive digest are outside the archive to avoid a circular digest definition.

The other 22 graph nodes are external members in the already accepted private
PRETRAINED_RUNTIME_ASSETS_V1_PRIVATE.zip, SHA-256
`741b30828503c481cbdc712295c9ab12f52a1c3de183c17bc572a11436762fa9`.
Their original member names are `assets/{original-relative-path}`; exact lock
SHA-256 is `53fc72dd7e85dfd6dab703531cdf2599b029e2adec8430610c688ab8a4a1a12c`.
Read this existing archive, without downloading or repackaging it, to restore
those 22 files into the new logical original root alongside the static package.
Leave the previously accepted pretrained restoration unchanged.

The separate validator runs in a fresh isolated, no-site, no-bytecode standard
library Python process. Authenticate the sealed audit, every support member and
the two archives against independently supplied pins. Reconstruct expected
payload members from the authenticated graph, check node/edge digest consistency,
seed reachability, exact unique archive member sets and routes against the pinned
asset lock. Do not import the writer/auditor or read original project content.
Reject path traversal, reserved/alias names, links, reparse points and overwrites.
Actually extract all 17,617 nodes into three fresh roots; rehash the exact restored
file set. The writer independently rehashes all originals and restored files
after validation. Preserve every failed archive, partial restoration and receipt.

Payload files remain opaque, including source code, saved models and scientific
JSON/JSONL/Arrow contents. Decode only delivery/audit graph metadata and the asset
lock. No model loads, fits, neural forwards, new cohort choices or fresh Gold
values. Only the single predeclared validator subprocess is allowed by the writer;
the validator permits no network or subprocesses. Record access guard violations.

Acceptance is `PASS_DECLARED_STATIC_TRANSPORT_AND_RESTORATION_ONLY`. It neither
supplies the excluded C3 live ledgers / future stages nor proves complete source
IO closure, portable scientific predecessor bindings, CUDA or pipeline replay.
Include the exact controls and freeze in a small evidence companion for offline
validation; reuse of a Git checkout with different line endings is insufficient.

P0 remains original C3 completion/replay/acceptance, actual C4/prelabel, cost/D,
and contribution review. P1 remains prospective scientific delivery bindings,
completed-stage dependencies and complete relocated execution. Seven historical
fit-time receipts and another-host evidence remain missing. P2 adds no searches.
