# Restore the fixed pretrained assets from the private delivery

This restores files only. It does not run C3/C4, load a model or evaluate answers.
Do not redirect the current C3 process or rerun accepted restoration routinely.

Use both private components listed in PRETRAINED_ASSET_DELIVERY_RESULTS.json:
the large `PRETRAINED_RUNTIME_ASSETS_V1_PRIVATE.zip` and the small
`PRETRAINED_ASSET_DELIVERY_V1_EVIDENCE_PRIVATE.zip`. Verify both SHA-256 values
against that record before extracting or executing a control script. No download
or model replacement is needed. The evidence ZIP contains exact control-source
bytes; use its `control/validator.py` rather than a checkout whose Git line-ending
conversion may change the frozen source hash.

Extract only the small evidence ZIP to an empty audit directory. Its `records/`
directory contains EXECUTION_FREEZE.json, the asset lock and original acceptance
receipts. Keep the large asset ZIP intact for the independent validator.
Use a separate, non-existing absolute project destination. The new receipt's
parent directory must already exist and its filename must not already exist.

The tested interpreter is the existing Windows CPython 3.10.6 base, with isolated
mode, site packages disabled and bytecode writing disabled. No neural packages
are needed for this validator. The following paths are examples to adjust to
the actual private files; this is not a command to repeat the current accepted run:

```powershell
& 'C:\Users\qianx\AppData\Local\Programs\Python\Python310\python.exe' -I -S -B -X utf8 `
  'E:\restoration-audit\control\validator.py' `
  --archive 'E:\private-delivery\PRETRAINED_RUNTIME_ASSETS_V1_PRIVATE.zip' `
  --archive-sha256 741b30828503c481cbdc712295c9ab12f52a1c3de183c17bc572a11436762fa9 `
  --freeze 'E:\restoration-audit\records\EXECUTION_FREEZE.json' `
  --freeze-sha256 d5941e8b5bfeed2bd3c1ad272349d7cfdc50d4ac7a7da85b23558a6282f561a2 `
  --destination 'E:\restored-project-fresh' `
  --receipt 'E:\restoration-audit\NEW_RESTORATION.json'
```

Require exit zero and `PASS_EXACT_PRETRAINED_ASSET_ARCHIVE_AND_RESTORATION_ONLY`.
The validator verifies the two original audit pins, exact 30-member archive,
22 original payload digests, restored exact file set and Qwen's two-shard index
closure. Its recorded old-project content reads and blocked events must be zero.
It rejects existing destinations/receipts, traversal, aliases, symlinks and
unexpected members; it does not overwrite files or repair a failed archive.
Keep every failure and partial restoration, and diagnose before a new attempt.

BGE serves retrieval/repair and answer embedding, Qwen serves generation and
likelihood scoring, and DeBERTa serves the GbV NLI component. Their exact
revisions are in PRETRAINED_ASSET_LOCK.json. Learned ROA/HGB/V2 policy artifacts,
datasets, generation ledgers, package wheels, Python and Windows are separate
dependencies. The accepted neural wheel kit supplies package files, but no full
pipeline relocation or CUDA replay has yet been accepted. Continue those gates
through CURRENT_TASK.md and retain CAS Q2 STATUS: NOT READY.
