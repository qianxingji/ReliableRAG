# Deliver the exact pretrained runtime assets

Research Lead contract, 2026-09-11, before packaging or extraction.
CAS Q2 STATUS: NOT READY.

The offline package kit and two-root native definition assembly are accepted.
Neither kit contains the complete pretrained model payloads needed for actual
pipeline reproduction. Close that concrete delivery gap using the existing
authenticated files only; do not download, convert, quantize or load a model.

## Authority and complete scope

The accepted acquisition audit manifest is
`6e441f8f9fef2b000ba2b39dcfd7b40f74dd4f779568d885584bb7da10b7d518`;
the accepted scoring audit manifest is
`1027d9e0c062c11bca3c6427d2c2db6403b42e25880d34777d5e32b6adae8ebc`.
Their original checked_files records remain the authority for every payload.

| Role | Model and fixed revision | Files | Bytes |
|---|---|---:|---:|
| Retrieval, repair retrieval and answer embedding | BAAI/bge-base-en-v1.5 @ a5beb1e3e68b9ab74eb54cfd186867f64f240e1a | 6 | 438,899,684 |
| Generation, repair query and reader likelihood | Qwen/Qwen2.5-3B-Instruct @ aa8e72537993ba99e69dfaafa59ed015b17504d1 | 9 | 6,183,451,098 |
| GbV NLI component | MoritzLaurer/deberta-v3-large-zeroshot-v2.0 @ 5a4338ab2151dc8db04ad53b42b6153382bf4f99 | 7 | 872,645,751 |

Include all 22 files / 7,494,996,533 bytes, including tokenizer/configuration,
Qwen shard index and the existing NLI README. Preserve exact relative locations
under the logical original project root. Keep original manifests unchanged;
a separate transport lock must match their model IDs, revisions, file sets,
sizes and hashes. The learned ROA/HGB/V2 policy artifacts, datasets, runtime
outputs and package wheels are separate dependencies, not part of these
pretrained snapshots or a claim of full pipeline closure.

## Execution and independent acceptance

1. Use a fresh private namespace. Authenticate both audit manifests and their
   complete saved audit reports, select the exact three snapshot directories,
   and require equality of declared and physical file sets before copying.
2. Freeze the contract, writer, independent validator and payload records.
   Write a private ZIP64 archive with all assets and provenance/control files.
   Stream bytes without tensor deserialization; preserve original content and
   use no model or dataset library. No private upload is authorized here.
3. In a separate isolated base-Python process, independently reauthenticate the
   embedded original audits against their existing pins, reconstruct all 22
   expected payload identities, compare the transport lock, and check the exact
   archive membership. Reject path traversal, case collisions, symlinks,
   duplicate or unknown members and changed hashes/sizes before accepting.
4. Actually extract to a new project root, preserving relative paths, without
   overwriting an existing directory. Stream-compare every archive payload and
   every restored file against the original audit digest. Independently verify
   that Qwen's index references exactly the two included shard basenames. Do not
   decode tensor payloads or claim model execution from header/index checks.
5. Rehash all original inputs and copies, confirm exact file sets, record both
   commands and all outcomes, and seal the namespace. Retain incomplete or
   failed archives/extractions; use a new version for any correction. The
   ongoing original C3 process and its inputs must stay untouched.

The scripts may read only the named snapshots/audit/control files, archive,
base-Python/Windows runtime and new output directories. Deny network, scientific
imports, model/estimator loads, inference, fits, data/Gold reads and mutations to
original files. The writer may start only its one declared independent Python
validator. OS inventory must not introduce hidden platform probing or subprocess
exceptions; this stage needs no platform.uname or neural-package imports.

A PASS closes only exact pretrained-asset delivery and extraction. It does not
accept CUDA execution, a relocated neural pipeline, any fresh result, complete
data/output closure, another host/OS reproduction or Submission Ready status.
P0 remains C3 completion/fixed replay/acceptance, then C4/full prelabel, cost/D
and contribution review. No P2 model/feature/seed/budget search is permitted.
