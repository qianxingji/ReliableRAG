# Client Lead review: published GbV component and local paired adaptation

CAS Q2 STATUS: NOT READY. Checked 2026-09-11 before fresh scoring/outcomes.
This is a source-fidelity assessment, not manuscript prose or a new experiment.

The primary paper defines Answering with Faithfulness separately from ordinary
answer correctness. Its Appendix A.1 uses a question/answer hypothesis, individual
passage premises, 20-word overlap for overlength passages and maximum NLI score.
Appendix A.2 selects MoritzLaurer/deberta-v3-large-zeroshot-v2.0 with the natural
sentence format; larger-reader experiments use a different prompted verifier.
These details support the local dedicated-verifier component. They do not
establish author-code or token-level numerical reproduction.
[Primary paper, sections 3–4 and Appendix A, pp. 1019–1020, 1027–1028](https://aclanthology.org/2025.ijcnlp-long.56.pdf).

The linked author repository distributes adapted NQ, BioASQ and NoMIRACL
datasets. Its visible root contains dataset files, README and license; it does
not supply a scoring implementation there. This bounded inspection is not a
claim that author implementation code exists nowhere.
[Author repository](https://github.com/alexshtf/awf_datasets).

Local implementation evidence is the authenticated src/verification/gbv_nli.py
in both checkouts: SHA256
a9ca2f6391b91fec2b56c309bdfb2543ff0a6ae9c5f8cfe89ff7e14358c11503.
The original scoring inventory pins it and the model config; that source remains
unchanged. The template is `The answer to the question "{question}" is: "{answer}"`.
The historical label-resolver correction selects the unique positive entailment
label exactly; both earlier blocked attempts remain preserved.

| Local decision | Claim boundary |
|---|---|
| Model revision 5a4338ab2151dc8db04ad53b42b6153382bf4f99; FP32, batch 8, slow tokenizer | Reproducible project settings; do not attribute the exact revision/runtime settings to the paper |
| Fit-checked chunks using the effective 512-token limit and 20-word overlap | Local deterministic implementation of the described recipe; no author-tokenization equality claim |
| Own-evidence scores F0(a0,E0), F1(a1,E1), then F1−F0 | Project-specific paired adaptation, not a published paired-policy formula |
| Global K=900 with a common forced-Keep mask | Project's fixed action-budget experiment, not reproduction of a published threshold-selection protocol |
| Qwen-2.5-3B and three multi-hop datasets with fixed candidate pools | Bounded empirical transport; no original-paper benchmark/model replication claim |
| EM/F1 Recovery/Damage outcomes and supervised GBV_ONLY_R/HGB_GBV_R | Correctness-based local controls; these outcomes do not measure faithfulness directly |

Lead decision: retain the frozen comparator and all nine policies unchanged.
Use the reporting label “paired adaptation of GbV Post-Answering NLI”; keep the
internal ledger identifier GbV. The frozen protocol's phrase “exact published
paired adaptation” means preserve the existing local implementation, not that
the paper publishes our paired margin. This clarification changes no byte-frozen
protocol, model, prompt, budget, score, eligibility rule or planned analysis.

The web tool could not retrieve the exact revision's Hugging Face config URL.
Its local 1,019-byte config remains authenticated by SHA256
3b0a2a3fb311037ba72670d87cbd16f920581985178547a76936dfdb292e5271;
remote re-verification is not claimed. Do not substitute an unpinned revision.

P0: complete the already frozen empirical experiment and review its actual
contribution; no evidence supports a novel-method promotion yet. P1: report
the component/adaptation boundaries above and complete cost/release evidence.
P2: no extra verifier, model search or post-outcome threshold changes. General
SOTA coverage and broad external transfer remain unestablished.
