# Offline restoration of the declared static graph

Scope: authenticate and restore exact bytes on Windows with isolated CPython
3.10. The original runtime remains active elsewhere. This runbook never invokes
a scientific entry point, imports a saved estimator or decodes scientific data.
CAS Q2 STATUS: NOT READY. Use STATIC_DELIVERY_RESULTS.json for actual acceptance
and the evidence-companion digest, rather than inferring success from this guide.

## Three private transport parts

Keep these local/private; none is committed or uploaded to GitHub:

1. `STATIC_DEPENDENCIES_V1_PRIVATE.zip`, 4,376,282,512 bytes,
   SHA-256 `b80bbe91fee02dbdc9b360cebf29385948f9fa81c62fc1564bb4c0bc0214efe5`.
   It contains 17,595 static payload files plus 15 audit/control members.
2. The existing `PRETRAINED_RUNTIME_ASSETS_V1_PRIVATE.zip`, 7,495,085,322 bytes,
   SHA-256 `741b30828503c481cbdc712295c9ab12f52a1c3de183c17bc572a11436762fa9`.
   The validator restores only its 22 graph-bound asset members; this archive is
   reused as an external dependency, not duplicated inside the static package.
3. `STATIC_DELIVERY_V1_EVIDENCE_PRIVATE.zip`. Obtain its exact digest from
   STATIC_DELIVERY_RESULTS.json. It supplies the delivery freeze, independent
   receipt, sealed graph audit, exact source controllers and contracts.

Before extraction, verify all three SHA-256 digests against the separately
published results. Extract the small evidence companion into a new directory.
It contains exact validator bytes under `control/validator.py` and the original
freeze under `records/DELIVERY_FREEZE.json`. The freeze digest is
`c80258e345b23300f1f5830f64aac7d3c33913146e30f3aaa599f518d6c362f1`.
Verify the validator's digest and size against that freeze before execution.
Do not substitute a Git checkout affected by line-ending conversion.

## Independent restoration

Use an absolute path to a trusted Windows CPython 3.10 interpreter with
`-I -S -B -X utf8`, followed by the extracted exact validator. Supply these
arguments, replacing only physical locations:

```text
--archive <absolute-path-to-STATIC_DEPENDENCIES_V1_PRIVATE.zip>
--archive-sha256 b80bbe91fee02dbdc9b360cebf29385948f9fa81c62fc1564bb4c0bc0214efe5
--asset-archive <absolute-path-to-PRETRAINED_RUNTIME_ASSETS_V1_PRIVATE.zip>
--freeze <absolute-path-to-records/DELIVERY_FREEZE.json>
--freeze-sha256 c80258e345b23300f1f5830f64aac7d3c33913146e30f3aaa599f518d6c362f1
--destination <absolute-path-to-new-nonexistent-directory>
--receipt <absolute-path-to-new-json-file-in-existing-directory>
```

Allow at least 14 GB free space on the restoration drive. The destination must
not exist and should be short enough for Windows paths. A successful run creates
three separate subdirectories: `original`, `engineering`, `task`. It reconstructs
all 17,617 graph files, totaling 11,840,356,271 bytes, and checks every restored
digest and the exact file set. No existing files or original metadata paths are
overwritten. A failed run/partial destination must be retained; use another
explicitly versioned namespace only after reviewing the failure.

Required receipt status:
`PASS_INDEPENDENT_STATIC_THREE_ROOT_RESTORATION_ONLY`, with zero blocked events,
21,118 checked dependency edges, all 17,617 nodes reachable from 21 frozen seeds,
17,595 internal and 22 external files, and zero original-project content reads.
The graph authority is the accepted manifest
`aa5c3da7ed764405e92602b64303984931a798abf2aee3e64c5d56ae34e892ea`.
Original and restored bytes were also rechecked separately by the delivery writer
when its own acceptance status is PASS; the standalone validator receipt has its
own narrower scope and does not read unavailable original paths.

## Scientific boundaries

These restored roots preserve historical absolute paths in manifests and source
definitions. They are not a ready-to-run replacement for the original controllers.
Use the separately accepted neural runtime and native path adapter only under a
new reviewed binding/execution contract. Never rewrite old hashes or patch live
C3 to point here. The active C3 launch freeze is included only as static launch
metadata. Its live ledgers and future C4/D outputs are deliberately absent.

No package installation, pretrained deserialization, CUDA forward, fresh Gold
read, metric replay or whole-pipeline replay is performed by this validator.
Same-host file relocation does not establish another-host/OS reproduction.
Historical fit-time provenance gaps, missing empirical outcomes and unestablished
contribution remain unchanged.
