# Mistral development acquisition and replay protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_FORMAL_EXECUTOR_VALIDATION`. This document fixes the
formal 13,500-trace development acquisition, component order, durable recovery,
storage and sampled replay. It does not start the run, expose Gold or authorize
a scientific claim.

## Inputs and isolation

The executor binds directly to the accepted Qwen development trace manifest,
questions, original Top-5 evidence, retrieval pool/indexes and the accepted
Mistral value-blind input freeze. Phi outputs, answers, vectors, validators and
failure artifacts are not scientific inputs. Only the 4,500 development
questions / 13,500 retriever traces are in scope: 3,600 fit questions and 900
calibration questions. Test inputs and every Gold value remain unopened.

Every tracked/external input is SHA-256 authenticated before a model load and
rehashed at stage completion. Offline mode is mandatory. Each output stage uses
a new namespace and append-only canonical JSONL ledgers.

## Component-sequential stages

1. **`a0_query`**: load Mistral alone. For every trace, generate `a0` and the
   repair query from the original evidence. Close Mistral. Expected calls:
   27,000 generation operations.
2. **`repair`**: with Mistral absent, load BGE alone. Reuse the sealed document
   embeddings and BM25 structures, issue exactly one same-retriever depth-50
   repair per trace, and replace rank 5. Dense/hybrid query embeddings total
   9,000. Close BGE. Expected repair operations: 13,500.
3. **`a1_likelihood`**: load Mistral alone. Generate `a1`, then calculate
   L00/L01/L10/L11 by answer-token teacher forcing. Close Mistral before any
   future NLI/GbV work. Expected operations: 13,500 generation plus 54,000
   likelihood calls.
4. **`witness_replay`**: after all canonical stages and their no-model
   validation, replay exactly the first and last development trace in each of
   the nine dataset × retriever cells under distinct replay operation keys.
   Save the complete first-token FP32 vocabulary vector for three generations
   and four likelihood cells: 126 model operations and 126 fixed vectors. The
   canonical compact rows are immutable; replay cannot replace them.

Canonical totals are 40,500 generation calls, 54,000 likelihood calls, 13,500
repair operations, 94,500 model operations and 108,000 operations including
repair. No original-question retrieval, document embedding, NLI, fit, Gold or
test operation is permitted.

## Journals, recovery and failures

Each operation fsyncs a stable key and complete input hash before execution,
then fsyncs its scientific row and journal result. Completed keys are skipped
and never regenerated. If a durable row exists after a crash but the journal
result does not, recovery closes the journal from that row without inference.
If only an intent exists, the deterministic operation may be reissued only with
the exact key/type/input hash; `resume_pending` is fsynced first and the extra
physical call is disclosed. Mismatches, gaps, partial lines, duplicate rows and
out-of-order stages fail closed. Every process failure remains in a separate
receipt; no namespace is overwritten.

## Compact receipts and validation

All generation rows retain prompt/input hashes, token counts, generated IDs,
all selected-token log probabilities, raw/parsed text hashes, parser status,
render metadata, input identity and forward counts. Reconstructable prompt ID
and all-one mask arrays are omitted from canonical rows to control storage.

All likelihood rows retain prompt/target hashes and counts, every target-token
log probability, mean/minimum, truncation/render metadata, cell identity and
forward count. Reconstructable prompt/target arrays are omitted. The validator
independently rebuilds them from the bound question/evidence/answer and checks
the hashes, counts and target-preserving right-prompt truncation.

The 18-position replay saves 16,515,072 raw FP32 logit bytes before container
metadata. Each first-token softmax is recomputed independently. Full-vocabulary
arrays are not stored for all 94,500 canonical model operations.

## Limits and stopping

- Batch size one; CPU admission before CUDA; generation input at most 8,192
  tokens; likelihood total at most 8,192 with complete target retention.
- Mistral peak reserved at most 14 GiB; BGE uses its already accepted BF16
  route; Mistral and BGE/NLI never coexist.
- At least 30 GiB free on E: before each stage; output plus a second immutable
  archive budget at most 50 GiB.
- Maximum elapsed time per stage process: seven days. Progress is reported every
  ten completed traces. A resource exception, overlength row, empty likelihood
  target, nonfinite value, input mutation or validator rejection fails the
  stage and is not converted into an eligible success.

The formal stage cannot start until its executor, independent validator and
invented recovery/compaction tests pass from a committed tree. After accepted
development acquisition, reader-matched scoring and the already frozen
development-only tuner may run. Primary recipe and multiplicity family must be
frozen before any Mistral test outcome is opened.
