# P0-G third-party terms recheck

Decision: **PASS_THIRD_PARTY_TERMS_RECHECK_RELEASE_SOURCE_CORRECTED_CURRENT_ARCHIVE_WITHHELD.**

**CAS Q3 STATUS: NOT READY.** This is a release-boundary audit, not legal
advice or authorization to distribute any project, benchmark, model or output
artifact.

The principal upstream records were rechecked on 2026-09-14. The records
support the existing decision to exclude all benchmark payloads, model weights,
tokenizers and third-party packages from the aggregate reviewer artifact:

| Material | Upstream record checked | Verified boundary |
|---|---|---|
| HotpotQA | <https://github.com/hotpotqa/hotpot> | Dataset CC BY-SA 4.0; repository code Apache-2.0. |
| 2WikiMultiHopQA | <https://github.com/Alab-NII/2wikimultihop> | Repository carries Apache-2.0; the project continues to exclude the externally downloaded dataset payload rather than infer a broader redistribution right. |
| MuSiQue | <https://github.com/stonybrooknlp/musique> | Dataset CC BY 4.0, with an upstream warning about overlap with seed single-hop datasets. |
| Qwen2.5-3B-Instruct at `aa8e72537993ba99e69dfaafa59ed015b17504d1` | <https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/aa8e72537993ba99e69dfaafa59ed015b17504d1/LICENSE> | Qwen Research License Agreement; non-commercial research/evaluation grant and separate redistribution conditions. |
| BGE base English v1.5 at `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` | <https://huggingface.co/BAAI/bge-base-en-v1.5/tree/a5beb1e3e68b9ab74eb54cfd186867f64f240e1a> | Upstream model card declares MIT and says the released model can be used commercially. |
| DeBERTa zero-shot v2.0 at `5a4338ab2151dc8db04ad53b42b6153382bf4f99` | <https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0/tree/5a4338ab2151dc8db04ad53b42b6153382bf4f99> | Model card labels the foundation model MIT but warns that the non-`-c` checkpoint used training data with varying licenses, including non-commercial licenses, and that legal views differ on downstream effect. |

The last item corrects an over-broad line in the previous
`THIRD_PARTY_NOTICES.md`, which stated only `MIT`. The tracked release source
now retains both the foundation-model label and the training-data caveat. It
does not infer the license of generated answers or aggregate metrics.

The preserved aggregate archives with SHA-256
`b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d`
contain the earlier notice member with SHA-256
`20d6198a76b35d050c95b51423b1c6f6729e7ae1074b28c48fb32a80539e5180`.
Those archives remain valid as immutable, withheld arithmetic-verification
witnesses. They are not release-ready and must not be published. The next
owner-authorized, license-bearing archive must be rebuilt from the corrected
source and pass the deterministic, anonymity, round-trip and policy checks
again.

No benchmark text, answer, model payload, generated answer, per-question
outcome or private scientific evidence was opened for this audit. No model
forward or scientific fit was executed.
