# C4 full GbV scoring acceptance

**Decision: ACCEPTED for the frozen C4 prelabel chain.** The single full GbV
stage and a separate CPU client audit completed over all 18,000 frozen traces.
This acceptance authorizes only the fixed policies stage. It does not read fresh
Gold outcomes, establish answer quality, support a contribution claim, or make
the project submission ready.

## Bound execution

- Scientific namespace: `outputs/cas_q2/empirical_gbv_scoring_v1`
- Source commit: `efe595a25060b83e30b1d36413d6e2de3e11893a`
- Scientific manifest: `0316b48996435da3f6e9ea20ffa329780c5bf0181af7706e113fd0b4a4de085c`
- External run manifest: `3cc31eeeab0837ca95d2f1fd077034980c6964a20f011d9ecdf6790200aea0ef`
- Binding config: `a0f5c80d89ed9bdd014f90664d4d038e07ae3d8d8d7fdfb422535716eb08249f`
- Accepted predecessors: runtime `dc2905224798b07302db8950f68db228de1faff9042c44dbaee7111ba107878f`, V2 GPU preflight `1aabac381c8a5e5381f46729f49e9afcaae915c1fa84cd375141486e513b530a`, and base `6cbc051be274617e26f548f4b51b5a6ec3cddeb5e1caf6761f00fa8301913cab`.

The producer completed 18,000 traces. Native and common eligibility both equal
4,267. It attempted and completed 8,534 branches, recording 8,534 NLI forward
calls, 42,946 pairs and 10,132,344 padded input tokens. The model revision is
`5a4338ab2151dc8db04ad53b42b6153382bf4f99`, inference dtype is FP32, the
effective maximum length is 512, and the observed forward device is `cuda:0`.
There were no new deterministic unscorable pairs, model fits, generation calls,
retrieval calls, or fresh Gold values.

## Independent saved-witness audit

The client audit manifest is
`549bfcc82a78d9b75aa18fb2c297310c8d1e257f8310b456b1eaa060372cbfd3`.
It independently reconstructed all 18,000 bound traces with the original slow
DeBERTa tokenizer, checked every saved token/chunk binding, recomputed FP32
softmax probabilities from every saved logit, and closed the complete forward
and branch journals. The maximum probability error was
`9.04739765328344e-08`, below the frozen absolute bound
`9.5367431640625e-07`. All emitted saved batches satisfy the 512-token bound;
the one 519-token warning occurs before the frozen chunking step and matches the
producer log.

The audit also rehashed all 17,435 executable inputs and 30,912 environment
files. The seven copied NLI snapshot files match their sources byte for byte.
Large ledgers and weights remain in the sealed scientific namespace; the audit
archive contains metadata only. The audit performs no second neural forward.

The first client-audit invocation used the system Python and failed before the
numeric loop because `transformers` was unavailable. It is preserved under
`outputs/c4_gbv_scoring_v1_client_audit_controller_failure_v1` with manifest
`a9acbeda5ab52ba48ec2f6819a6f393c1cf303a63fb6a5371e816cd1364eb5dd`.
The accepted invocation used the already authenticated original project virtual
environment; the scientific stage was not restarted or modified.

## Scope and next gate

This establishes complete saved-logit, softmax, tokenizer/chunk, branch and
margin arithmetic for the one frozen GbV run. It does not independently repeat
the NLI neural forward or inspect answer outcomes. The next permitted action is
one commit-bound CPU policies run using the exact accepted runtime, preflight,
base and GbV manifests, followed by a separate policies audit and the full C4
independent validator.

**CAS Q2 STATUS: NOT READY.** The main rejection risks remain absent fresh
quality results, no cleared novel contribution, missing historical fit-time
receipts, and unfinished C4/D/cost/confirmation evidence. P0 is policies plus
complete C4 validation; P1 is the authorized cost and D execution after C4; P2
remains the final research/claim and reproducibility closure without new search.
