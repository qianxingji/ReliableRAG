# Full historical reference/outcome replay in the restored roots

Research Lead design, 2026-09-11. CAS Q2 STATUS: NOT READY.
Freeze before implementation, raw-reference decoding or execution.

## Scope and closed fresh evaluation

Recompute all 13,500 historical branch outcomes for the original 4,500 question
groups, using original selected-reference readers, original answer metrics and
the accepted new PyArrow 20.0.0 target. This historical evaluation was already
opened on 2026-09-10. It is not current empirical D execution or permission to
open the current 6,000-question cohort's answers, scores, outcomes or Gold.

Before any reference/answer decoding, authenticate the accepted static graph,
restoration and original final-evaluation manifest
6a13d70133669c56d2a0c03829ea55267f4bc87108f767e6f80c4b6c1170512a.
Freeze exactly named inputs and controls. Authenticate original selected IDs
a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff
and the current selected-ID file
be87edeb12ab435a487ad0f7cf3bd1c4a2f0022c1c426bbd0f47f5fa9cfe8886,
bound by the accepted current cohort seal
6070c63b9cbf3277ef328d059dcaabc98480ba2bb60503b66ad2faa5e816b62a.
Read IDs only and require 4,500 old / 6,000 current unique (dataset,sample_id)
groups, 1,500 / 2,000 per dataset and zero intersection. Fail without decoding
references on any overlap or mismatch; do not select replacements.

Original canonical branches:
ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09.
Original numeric outcome ledger:
2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576.
Original selected-reference binding:
f31bc4f39f37ebbcb05eff0d15fa568c0c352d3bf8da0c7579397192eb99ebd1.
Use the existing MAPPING_INPUT_SPEC, source counts and reference semantics:
2Wiki dev JSON 12,576 rows, Hotpot distractor validation Parquet 7,405 rows,
MuSiQue train JSONL 19,938 rows. Only MuSiQue includes original answer_aliases.
All three raw sources and all used old source files must match prior static and
mapping-spec pins. No current empirical payload is otherwise in the read list.

## Actual original reading and reconstruction

Select unchanged read_object, json_references, parquet_references and
load_references from original selected_gold.py (SHA-256
b0d3e6003884909a74caf8a48f1e5d634d3244bc9f047ed0aa4c7dbfabfb16a7).
Keep the original _JSONByteCursor (source
4ecb9dad8bf88a80b99dfb97df4bc36de4bfa95feb3a9d5645e850fa08362472),
including ID-only first passes and selected-span second passes. Explicitly bind
only ROOT to the restored original root and necessary IO/hash helpers. Preserve
load_references' original 1,500-per-dataset rule and original calling bodies.

Use original metric definitions from src/evaluation/answers.py
d6de10b0d44bf32c5aa3727c4d2b4b3dc2556b3e4f791cc1fc4f08ad957dd182,
verifying all five AST hashes against the original mapping specification.
Use original canonical/jsha serialization for exact reference binding and row
bytes. Project historical canonical answers with the already frozen
empirical_outcome_native.canonical_answer_rows function; its cursor skips
question/evidence strings. Preserve all rows, order, retrievers and aliases.

The producer independently obtains all old references, matches their archived
binding hash, computes every a0/a1 EM/F1 and writes a new numeric ledger.
Do not read archived numeric values to generate outputs. Only after completing
the new ledger, compare its complete bytes to the unchanged original hash.
Save all new numeric rows and reference-binding/count receipts, not raw reference
strings. No action, policy, model or contribution analysis is in this gate.

In a separate process, reread the same raw sources with the unchanged original
reader, independently reconstruct all selected references and verify the same
binding hash. Recompute metrics using the previously frozen independent
normalize/metrics definitions in empirical_outcome_independent.py
404f51538788580c4da2e1ff713edcd98a74d55793f9dac2384ce1920f9c98cc.
Validate the exact seven-field schema and complete 13,500-row/nine-stratum
universe. Compare all 54,000 metric values to both new and archived ledgers:
EM exact and F1 absolute error <= 1e-15, reporting actual maxima. Require exact
new/original ledger bytes as a separate check. This uses shared original
reference reading but independent metric formulas; disclose that limitation.

## PyArrow binding and selected-cell boundary

Use the accepted new environment plus exactly its separate new PyArrow target,
not the original tmp package. Record actual module paths/version and mapped
native Arrow binaries, each bound to the accepted installed-file receipt.
Never import pandas, datasets, neural packages or estimator models in this gate.

Supply an explicitly disclosed observation wrapper through the original reader's
pq argument. It delegates to real PyArrow ParquetFile over Python-opened file
handles, preserving every requested option. Permit only id/answer column reads,
use_threads=False and use_pandas_metadata=False. Record row-group/column calls.
Permit ID to_pylist, determine selected indices from those IDs, and allow answer
scalar as_py only at those selected indices. Reject whole-answer-column Python
conversion, unselected indices and question/context/support columns. This is
an IO observation wrapper, not a substitute Parquet decoder. The original
reader function bodies and real native library remain unchanged.

Physical Arrow page decompression may include unselected rows. Do not claim
otherwise. Fresh/unselected reference values must not be converted to Python,
retained, logged or emitted. JSON unselected values remain cursor-skipped;
historical selected answer strings exist only in each mapper's memory. No raw
reference string is written to disk or tool output.

Before real sources, run invented JSON/JSONL and Parquet selection fixtures,
including unselected malformed/null answers and forbidden extra columns.
Require correct selected aliases/metrics and rejection of an invalid selected
answer, missing selected ID, unselected scalar access, forbidden column access
and a corrupted numeric row. These fixtures cause no scientific fits and do
not replace the full historical replay. Preserve expected rejections separately
from unexpected failures. Do not patch the original parser or metric functions.

## Execution and acceptance

Use one CPU thread, offline settings and no CUDA initialization. Freeze each
command/output namespace before execution. Use exact read/write allowlists;
no score/action/model inputs, current canonical payloads, network or process
actions after the accepted narrow OS bootstrap. All unexpected warnings,
exceptions or audit events fail the gate and retain partial outputs. Hash every
used original/restored file, all 21,267 environment/target files and controls
before/after. Preserve earlier accepted gates and all HGB failures unchanged.

Acceptance covers complete historical source-to-outcome numerical replay and
actual new Arrow target binding, not the current D pipeline, full arbitrary-root
CLI execution, BGE/Qwen/NLI forward replay or another-host reproduction. There
are zero new fits; the actual total stays 185. Original fit-time provenance
limits and both rejected historical contribution gates remain unchanged.
P0: original C3 completion/replay/acceptance, C4/full prelabel, then actual cost/D
and contribution review. P1: this remaining execution binding plus BGE and
complete stage/pipeline delivery. P2 adds no search; CAS scope remains undecided.
