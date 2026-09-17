# Mistral development GbV input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before paired-GbV execution. It
changes no NLI model or revision, branch order, batch size, premise splitting,
entailment rule, context-failure policy, label, endpoint or tuning rule. It
strengthens only the provenance boundary of the not-yet-run stage.

## Gap

The initial implementation authenticated the historical runtime and
predecessor manifests before use, but its executable freeze recorded only those
manifest files rather than every payload member. Its independent validator
verified the HGB acceptance and model/package assets, but did not reconstruct
the complete direct path set. This stage restores original evidence and reads
three acquisition outputs directly, so a manifest-only final rehash was not
sufficient.

## Prospective correction

Before loading the NLI model, the producer must now:

1. verify and record all 220 historical runtime, pool and retrieval payload
   members plus their three manifests, allowing only generated
   `__pycache__/*.pyc` extras in those legacy namespaces;
2. verify and record every member of the accepted Mistral input freeze, HGB
   stage, `a0_query`, repair and `a1_likelihood`, plus the independent HGB
   validation receipt;
3. verify and record 27 GbV provenance paths: the historical preflight, pinned
   GbV source, 17 exact SentencePiece package files, one package provenance
   record and seven exact NLI snapshot files;
4. record the producer and independent validator, acquisition/scoring helpers,
   independent eligibility formula, package initializers, frozen scoring
   protocol, this amendment and required native runtime files; and
5. rehash every recorded input after NLI unload and before the PASS receipt.

The independent tokenizer/logit validator reconstructs the identical path set,
requires exact equality with the executable freeze, validates exact recursive
manifest coverage, reauthenticates all 27 GbV provenance paths, and retains its
existing exact binding of branch receipts, result rows, call journal and all raw
logit files.

Ten focused GbV tests cover model/batch identity, branch ordering and recovery,
independent softmax/logit reconstruction, deterministic unscorable handling,
validator independence, exact input-graph requirements and rejection of an
unexpected manifest file. The complete Mistral suite passes 164 tests.

No paired-GbV model load or forward, Gold access, test access or scientific fit
occurred while making or testing this amendment. The active `a0_query`
executable, source commit and all 31 frozen inputs remain unchanged.
